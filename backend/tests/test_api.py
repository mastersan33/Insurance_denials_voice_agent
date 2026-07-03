import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "outbound-billing-voice-agent"


@pytest.mark.asyncio
async def test_health_ready(client: AsyncClient):
    response = await client.get("/health/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "checks" in data


@pytest.mark.asyncio
async def test_health_system(client: AsyncClient):
    response = await client.get("/health/system")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "securepass123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "pass123", "full_name": "Dup"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "mypassword", "full_name": "Login User"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "mypassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login@example.com"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/stats")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_stats(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/dashboard/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_calls" in data
    assert "active_calls" in data
    assert "resolution_rate" in data


@pytest.mark.asyncio
async def test_billing_cases_crud(client: AsyncClient, auth_headers: dict):
    # Create
    create_response = await client.post(
        "/api/v1/billing-cases",
        json={
            "patient_name": "Jane Doe",
            "payer_name": "Blue Cross",
            "claim_number": "CLM-TEST-001",
            "denial_code": "CO-97",
            "priority": "high",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    case = create_response.json()
    case_id = case["id"]
    assert case["patient_name"] == "Jane Doe"

    # Retrieve
    get_response = await client.get(f"/api/v1/billing-cases/{case_id}", headers=auth_headers)
    assert get_response.status_code == 200

    # Update
    update_response = await client.patch(
        f"/api/v1/billing-cases/{case_id}",
        json={"status": "in_progress"},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "in_progress"

    # List
    list_response = await client.get("/api/v1/billing-cases", headers=auth_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1


@pytest.mark.asyncio
async def test_billing_cases_search(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/v1/billing-cases",
        json={"patient_name": "Search Target", "payer_name": "Aetna", "claim_number": "SRCH-001"},
        headers=auth_headers,
    )
    response = await client.get("/api/v1/billing-cases?q=Search+Target", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(c["patient_name"] == "Search Target" for c in data["items"])


@pytest.mark.asyncio
async def test_analytics_summary(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/analytics/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_calls" in data
    assert "resolution_rate" in data


@pytest.mark.asyncio
async def test_analytics_call_volume(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/analytics/call-volume?days=7", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 7
    assert "date" in data[0]
    assert "total" in data[0]


@pytest.mark.asyncio
async def test_analytics_outcomes(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/analytics/outcomes", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_analytics_payers(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/analytics/payers", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_reports_billing_cases_csv(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/reports/billing-cases?fmt=csv", headers=auth_headers)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_reports_calls_csv(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/reports/calls?fmt=csv", headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_audit_log_requires_supervisor(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/audit", headers=auth_headers)
    # Default test user has 'operator' role — should be 403
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tickets_crud(client: AsyncClient, auth_headers: dict):
    create = await client.post(
        "/api/v1/tickets",
        json={"title": "Test Ticket", "description": "needs attention", "priority": "high"},
        headers=auth_headers,
    )
    assert create.status_code == 201
    ticket = create.json()
    assert ticket["title"] == "Test Ticket"

    update = await client.patch(
        f"/api/v1/tickets/{ticket['id']}",
        json={"status": "in_progress"},
        headers=auth_headers,
    )
    assert update.status_code == 200
    assert update.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_queue_pause_resume(client: AsyncClient, auth_headers: dict):
    pause = await client.post("/api/v1/call-jobs/queue/pause", headers=auth_headers)
    assert pause.status_code == 200
    assert "paused" in pause.json()

    resume = await client.post("/api/v1/call-jobs/queue/resume", headers=auth_headers)
    assert resume.status_code == 200
    assert "resumed" in resume.json()


@pytest.mark.asyncio
async def test_queue_retry_failed(client: AsyncClient, auth_headers: dict):
    response = await client.post("/api/v1/call-jobs/queue/retry-failed", headers=auth_headers)
    assert response.status_code == 200
    assert "retried" in response.json()

