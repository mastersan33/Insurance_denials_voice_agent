from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.billing_case import BillingCase
from backend.app.repositories.base import BaseRepository


class BillingCaseRepository(BaseRepository[BillingCase]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, BillingCase)

    async def get_by_claim_number(self, claim_number: str) -> BillingCase | None:
        result = await self.db.execute(
            select(BillingCase).where(BillingCase.claim_number == claim_number)
        )
        return result.scalar_one_or_none()

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> list[BillingCase]:
        result = await self.db.execute(
            select(BillingCase).where(BillingCase.status == status).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_payer(self, payer_name: str, skip: int = 0, limit: int = 100) -> list[BillingCase]:
        result = await self.db.execute(
            select(BillingCase).where(BillingCase.payer_name == payer_name).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
