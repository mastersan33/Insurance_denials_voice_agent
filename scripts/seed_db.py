"""Seed the development database with synthetic billing cases and a default admin user.

Day 2 requirement: "run the seed script twice — must not crash or duplicate rows"

Usage:
    python -m scripts.seed_db                   # seed with defaults
    python -m scripts.seed_db --reset           # drop+recreate seed data
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure project root is on the path so backend imports work
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config.settings import settings
from backend.app.core.security import hash_password
from backend.app.db.session import async_session_factory, engine
from backend.app.db.base import Base
import backend.app.models  # noqa: F401 — importing the package registers all models with SQLAlchemy Base
from backend.app.models.billing_case import BillingCase
from backend.app.models.user import User


# ---------------------------------------------------------------------------
# Synthetic billing cases — use ONLY synthetic data, never real patient data
# ---------------------------------------------------------------------------
SEED_BILLING_CASES = [
    {
        "patient_name": "John Smith",
        "payer_name": "Blue Cross Blue Shield",
        "payer_phone": "+15551234567",
        "claim_number": "CLM-SEED-001",
        "denial_code": "CO-97",
        "denial_reason": "Procedure not paid separately — bundled with primary procedure.",
        "amount_billed": 1800.00,
        "provider_name": "City Medical Center",
        "provider_npi": "1234567890",
        "service_date": "2026-06-01",
        "status": "open",
    },
    {
        "patient_name": "Jane Doe",
        "payer_name": "Aetna",
        "payer_phone": "+15559876543",
        "claim_number": "CLM-SEED-002",
        "denial_code": "CO-50",
        "denial_reason": "Service not deemed medically necessary by the payer.",
        "amount_billed": 3200.00,
        "provider_name": "Regional Health Clinic",
        "provider_npi": "0987654321",
        "service_date": "2026-06-05",
        "status": "open",
    },
    {
        "patient_name": "Robert Johnson",
        "payer_name": "UnitedHealthcare",
        "payer_phone": "+15554441111",
        "claim_number": "CLM-SEED-003",
        "denial_code": "CO-16",
        "denial_reason": "Claim missing required NPI information.",
        "amount_billed": 950.00,
        "provider_name": "Downtown Specialists",
        "provider_npi": "1122334455",
        "service_date": "2026-06-10",
        "status": "open",
    },
    {
        "patient_name": "Mary Williams",
        "payer_name": "Cigna",
        "payer_phone": "+15552223333",
        "claim_number": "CLM-SEED-004",
        "denial_code": "CO-22",
        "denial_reason": "Coordination of benefits — another payer may be primary.",
        "amount_billed": 2100.00,
        "provider_name": "Westside Medical Group",
        "provider_npi": "5566778899",
        "service_date": "2026-06-15",
        "status": "open",
    },
    {
        "patient_name": "David Brown",
        "payer_name": "Humana",
        "payer_phone": "+15556667777",
        "claim_number": "CLM-SEED-005",
        "denial_code": "CO-4",
        "denial_reason": "Service inconsistent with modifier used.",
        "amount_billed": 740.00,
        "provider_name": "Northside Physicians",
        "provider_npi": "9988776655",
        "service_date": "2026-06-18",
        "status": "open",
    },
]

# Default admin user — change password before any real usage
SEED_ADMIN_USER = {
    "email": "admin@billing.com",
    "full_name": "Admin User",
    "password": "Admin@1234",
    "role": "admin",
}


async def _ensure_schema() -> None:
    """Create all tables if they don't exist (handles fresh DB without Alembic)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _seed_admin(db: AsyncSession, reset: bool) -> None:
    result = await db.execute(select(User).where(User.email == SEED_ADMIN_USER["email"]))
    existing = result.scalar_one_or_none()

    if existing and reset:
        await db.delete(existing)
        await db.flush()
        existing = None

    if not existing:
        user = User(
            email=SEED_ADMIN_USER["email"],
            hashed_password=hash_password(SEED_ADMIN_USER["password"]),
            full_name=SEED_ADMIN_USER["full_name"],
            role=SEED_ADMIN_USER["role"],
            is_active=True,
        )
        db.add(user)
        print(f"  + Admin user created: {SEED_ADMIN_USER['email']}")
    else:
        print(f"  ~ Admin user already exists: {SEED_ADMIN_USER['email']}")


async def _seed_billing_cases(db: AsyncSession, reset: bool) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    for data in SEED_BILLING_CASES:
        result = await db.execute(
            select(BillingCase).where(BillingCase.claim_number == data["claim_number"])
        )
        existing = result.scalar_one_or_none()

        if existing and reset:
            await db.delete(existing)
            await db.flush()
            existing = None

        if not existing:
            case = BillingCase(**data)
            db.add(case)
            inserted += 1
        else:
            skipped += 1

    return inserted, skipped


async def seed(reset: bool = False) -> None:
    await _ensure_schema()

    async with async_session_factory() as db:
        print("\nSeeding admin user...")
        await _seed_admin(db, reset)

        print("\nSeeding billing cases...")
        inserted, skipped = await _seed_billing_cases(db, reset)
        print(f"  + Inserted: {inserted}")
        print(f"  ~ Skipped (already exist): {skipped}")

        await db.commit()

    print("\nSeed complete.\n")
    print(f"  API:      http://localhost:{settings.port}/docs")
    print(f"  Login:    {SEED_ADMIN_USER['email']} / {SEED_ADMIN_USER['password']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed development database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and re-insert seed data (idempotent reset)",
    )
    args = parser.parse_args()
    asyncio.run(seed(reset=args.reset))


if __name__ == "__main__":
    main()
