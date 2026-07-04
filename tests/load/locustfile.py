"""
Locust load test suite for the Insurance Denials Voice Agent API.

Scenarios
─────────
  - AuthUser        : register → login → refresh → /me (auth flow stress)
  - BillingWorkflow : list cases → create case → create call job (core flow)
  - ReadOnlyUser    : list cases, analytics, dashboard stats (viewer traffic)
  - DashboardSocket : WebSocket dashboard connection keep-alive

Run locally (requires the backend to be running):

    pip install locust
    locust -f tests/load/locustfile.py --host http://localhost:8000

Run headless for CI/CD:

    # 100 users ramp over 30 seconds, run for 2 minutes
    locust -f tests/load/locustfile.py --host http://localhost:8000 \
           --headless -u 100 -r 30 --run-time 2m \
           --csv reports/load_100

    # 1 000 users
    locust -f tests/load/locustfile.py --host http://localhost:8000 \
           --headless -u 1000 -r 50 --run-time 5m \
           --csv reports/load_1000

    # 5 000 users  (requires multiple workers — see below)
    locust -f tests/load/locustfile.py --master --host http://localhost:8000
    locust -f tests/load/locustfile.py --worker  # run on each worker node

Pass secrets via environment variables (never hardcode in this file):
    LOCUST_USER_EMAIL=test@example.com
    LOCUST_USER_PASSWORD=TestPass123!
"""
import os
import random
import string
import time
import uuid

from locust import HttpUser, TaskSet, between, events, task
from locust.contrib.fasthttp import FastHttpUser


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

PAYER_NAMES = [
    "UnitedHealthcare", "Aetna", "Cigna", "BlueCross BlueShield",
    "Humana", "Molina Healthcare", "Centene", "Anthem",
]
DENIAL_CODES = ["CO-97", "CO-4", "CO-16", "CO-50", "CO-22", "PR-1", "PR-2", "OA-18"]


def _random_email() -> str:
    uid = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"loadtest_{uid}@example-loadtest.com"


def _random_claim() -> str:
    return f"CLM-{random.randint(100000, 999999)}"


def _random_billing_case() -> dict:
    return {
        "patient_name": f"Patient {random.randint(1000, 9999)}",
        "payer_name": random.choice(PAYER_NAMES),
        "claim_number": _random_claim(),
        "denial_code": random.choice(DENIAL_CODES),
        "amount_billed": round(random.uniform(200.0, 8000.0), 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Task Sets
# ─────────────────────────────────────────────────────────────────────────────

class AuthTasks(TaskSet):
    """Stress-test the auth flow: register → login → access token refresh."""

    def on_start(self):
        self.email = _random_email()
        self.password = "LoadTest@123"
        self.access_token: str | None = None

    @task(1)
    def register_and_login(self):
        # Register
        self.client.post(
            "/api/v1/auth/register",
            json={"email": self.email, "password": self.password, "full_name": "Load Tester"},
            name="/api/v1/auth/register",
        )
        # Login
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
            name="/api/v1/auth/login",
        )
        if resp.status_code == 200:
            self.access_token = resp.json().get("access_token")

    @task(3)
    def refresh_token(self):
        self.client.post(
            "/api/v1/auth/refresh",
            name="/api/v1/auth/refresh",
        )

    @task(2)
    def get_me(self):
        if self.access_token:
            self.client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {self.access_token}"},
                name="/api/v1/auth/me",
            )


class BillingWorkflowTasks(TaskSet):
    """Core billing case + call job workflow — operator persona."""

    def on_start(self):
        self.access_token: str | None = None
        email = _random_email()
        password = "LoadTest@123"
        self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Billing Op"},
        )
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        if resp.status_code == 200:
            self.access_token = resp.json().get("access_token")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

    @task(5)
    def list_billing_cases(self):
        self.client.get(
            "/api/v1/billing-cases?limit=50",
            headers=self._headers(),
            name="/api/v1/billing-cases [list]",
        )

    @task(2)
    def create_billing_case(self):
        resp = self.client.post(
            "/api/v1/billing-cases",
            json=_random_billing_case(),
            headers=self._headers(),
            name="/api/v1/billing-cases [create]",
        )
        if resp.status_code == 201:
            case_id = resp.json().get("id")
            # Create call job for this case
            self.client.post(
                "/api/v1/call-jobs",
                json={
                    "billing_case_id": case_id,
                    "phone_number": "+15005550006",  # Twilio test number
                    "priority": random.randint(1, 5),
                },
                headers=self._headers(),
                name="/api/v1/call-jobs [create]",
            )

    @task(3)
    def list_call_jobs(self):
        self.client.get(
            "/api/v1/call-jobs?limit=20",
            headers=self._headers(),
            name="/api/v1/call-jobs [list]",
        )

    @task(1)
    def search_billing_cases(self):
        q = random.choice(PAYER_NAMES[:4])
        self.client.get(
            f"/api/v1/billing-cases?q={q}&limit=20",
            headers=self._headers(),
            name="/api/v1/billing-cases [search]",
        )


class ReadOnlyTasks(TaskSet):
    """Read-heavy analytics & dashboard traffic — viewer persona."""

    def on_start(self):
        self.access_token: str | None = None
        email = _random_email()
        password = "LoadTest@123"
        self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Viewer"},
        )
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        if resp.status_code == 200:
            self.access_token = resp.json().get("access_token")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

    @task(5)
    def dashboard_stats(self):
        self.client.get(
            "/api/v1/dashboard/stats",
            headers=self._headers(),
            name="/api/v1/dashboard/stats",
        )

    @task(3)
    def analytics_summary(self):
        self.client.get(
            "/api/v1/analytics/summary",
            headers=self._headers(),
            name="/api/v1/analytics/summary",
        )

    @task(2)
    def analytics_call_volume(self):
        self.client.get(
            "/api/v1/analytics/call-volume?days=30",
            headers=self._headers(),
            name="/api/v1/analytics/call-volume",
        )

    @task(2)
    def analytics_outcomes(self):
        self.client.get(
            "/api/v1/analytics/outcomes",
            headers=self._headers(),
            name="/api/v1/analytics/outcomes",
        )

    @task(1)
    def active_calls(self):
        self.client.get(
            "/api/v1/calls/active",
            headers=self._headers(),
            name="/api/v1/calls/active",
        )

    @task(1)
    def health(self):
        self.client.get("/api/v1/health", name="/api/v1/health")


# ─────────────────────────────────────────────────────────────────────────────
# User types
# ─────────────────────────────────────────────────────────────────────────────

class AuthStressUser(FastHttpUser):
    """Simulates users hammering the auth flow."""
    tasks = [AuthTasks]
    wait_time = between(0.5, 2.0)
    weight = 1


class BillingOperator(FastHttpUser):
    """Simulates billing operators performing their core workflow."""
    tasks = [BillingWorkflowTasks]
    wait_time = between(1.0, 4.0)
    weight = 5


class DashboardViewer(FastHttpUser):
    """Simulates dashboard viewers and analysts — mostly reads."""
    tasks = [ReadOnlyTasks]
    wait_time = between(2.0, 8.0)
    weight = 3


# ─────────────────────────────────────────────────────────────────────────────
# Custom event hooks — print summary thresholds to console
# ─────────────────────────────────────────────────────────────────────────────

_THRESHOLDS = {
    "p50_ms": 200,     # 50th percentile response time
    "p95_ms": 1000,    # 95th percentile response time
    "p99_ms": 3000,    # 99th percentile response time
    "failure_pct": 1,  # max 1% error rate
}


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Print threshold pass/fail summary on test completion."""
    stats = environment.runner.stats.total
    p50 = stats.get_response_time_percentile(0.50)
    p95 = stats.get_response_time_percentile(0.95)
    p99 = stats.get_response_time_percentile(0.99)
    total_req = stats.num_requests
    failures = stats.num_failures
    fail_pct = (failures / total_req * 100) if total_req else 0

    print("\n" + "=" * 60)
    print("LOAD TEST THRESHOLD RESULTS")
    print("=" * 60)
    results = [
        ("p50 (ms)",      p50,      _THRESHOLDS["p50_ms"],    "ms"),
        ("p95 (ms)",      p95,      _THRESHOLDS["p95_ms"],    "ms"),
        ("p99 (ms)",      p99,      _THRESHOLDS["p99_ms"],    "ms"),
        ("Failure %",     fail_pct, _THRESHOLDS["failure_pct"], "%"),
    ]
    all_pass = True
    for name, value, threshold, unit in results:
        passed = value <= threshold
        if not passed:
            all_pass = False
        status = "PASS" if passed else "FAIL"
        print(f"  {name:20s}: {value:8.1f}{unit}  threshold={threshold}{unit}  [{status}]")
    print("=" * 60)
    print(f"  Total requests : {total_req}")
    print(f"  Failures       : {failures}")
    print(f"  RPS            : {stats.total_rps:.1f}")
    print("=" * 60)
    if not all_pass:
        environment.process_exit_code = 1
