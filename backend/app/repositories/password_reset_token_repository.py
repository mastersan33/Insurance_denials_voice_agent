from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.password_reset_token import PasswordResetToken
from backend.app.repositories.base import BaseRepository


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, PasswordResetToken)

    async def get_valid_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used.is_(False),
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def mark_used(self, token: PasswordResetToken) -> None:
        token.used = True
