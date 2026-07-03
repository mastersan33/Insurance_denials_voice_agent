from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.billing_case import BillingCase
from backend.app.repositories.base import BaseRepository


def _escape_like(value: str) -> str:
    """Escape LIKE wildcards to prevent injection via search queries."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


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

    async def search(
        self,
        q: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[BillingCase], int]:
        stmt = select(BillingCase)
        count_stmt = select(func.count()).select_from(BillingCase)

        if q:
            # Escape LIKE wildcards before wrapping — prevents wildcard injection
            safe_q = _escape_like(q.strip())
            like = f"%{safe_q}%"
            filter_clause = or_(
                BillingCase.patient_name.ilike(like),
                BillingCase.claim_number.ilike(like),
                BillingCase.payer_name.ilike(like),
            )
            stmt = stmt.where(filter_clause)
            count_stmt = count_stmt.where(filter_clause)

        if status:
            stmt = stmt.where(BillingCase.status == status)
            count_stmt = count_stmt.where(BillingCase.status == status)

        if priority:
            stmt = stmt.where(BillingCase.priority == priority)
            count_stmt = count_stmt.where(BillingCase.priority == priority)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(BillingCase.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def delete(self, case: BillingCase) -> None:
        await self.db.delete(case)
        await self.db.flush()

