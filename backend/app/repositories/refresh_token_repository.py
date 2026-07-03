from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.refresh_token import RefreshToken
from backend.app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, RefreshToken)

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def revoke_all_for_user(self, user_id: str) -> None:
        """Revoke every active token for a user (logout all sessions)."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
            )
        )
        for token in result.scalars().all():
            token.revoked = True

    async def revoke(self, token: RefreshToken) -> None:
        token.revoked = True
