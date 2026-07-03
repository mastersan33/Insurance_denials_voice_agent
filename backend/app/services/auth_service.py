from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config.settings import settings
from backend.app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from backend.app.core.security import (
    create_access_token,
    generate_refresh_token,
    generate_reset_token,
    hash_password,
    hash_token,
    refresh_token_expiry,
    reset_token_expiry,
    verify_password,
)
from backend.app.models.password_reset_token import PasswordResetToken
from backend.app.models.refresh_token import RefreshToken
from backend.app.models.user import User
from backend.app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from backend.app.repositories.refresh_token_repository import RefreshTokenRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.user import (
    MessageResponse,
    PasswordChange,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdateProfile,
)
from backend.app.services.email_service import send_password_reset_email


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.reset_tokens = PasswordResetTokenRepository(db)

    def _make_token_response(self, user: User, raw_refresh: str) -> TokenResponse:
        access_token = create_access_token({"sub": user.id, "role": user.role})
        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user),
        )

    async def register(self, data: UserCreate) -> UserResponse:
        existing = await self.users.get_by_email(data.email)
        if existing:
            raise ConflictException(f"User with email '{data.email}' already exists")
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
        )
        user = await self.users.create(user)
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str, ip_address: str | None = None) -> TokenResponse:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedException("Account is disabled")

        # Issue refresh token
        raw_refresh = generate_refresh_token()
        rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            expires_at=refresh_token_expiry(),
            ip_address=ip_address,
        )
        await self.refresh_tokens.create(rt)
        await self.users.touch_last_login(user.id)
        await self.db.commit()

        return self._make_token_response(user, raw_refresh)

    async def refresh(self, raw_refresh_token: str) -> TokenResponse:
        token_hash = hash_token(raw_refresh_token)
        rt = await self.refresh_tokens.get_by_hash(token_hash)
        if not rt:
            raise UnauthorizedException("Invalid or expired refresh token")

        user = await self.users.get_by_id(rt.user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or disabled")

        # Rotate: revoke old, issue new
        await self.refresh_tokens.revoke(rt)
        new_raw = generate_refresh_token()
        new_rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(new_raw),
            expires_at=refresh_token_expiry(),
        )
        await self.refresh_tokens.create(new_rt)
        await self.db.commit()

        return self._make_token_response(user, new_raw)

    async def logout(self, user_id: str, raw_refresh_token: str | None) -> MessageResponse:
        if raw_refresh_token:
            rt = await self.refresh_tokens.get_by_hash(hash_token(raw_refresh_token))
            if rt:
                await self.refresh_tokens.revoke(rt)
        await self.db.commit()
        return MessageResponse(message="Logged out successfully")

    async def logout_all(self, user_id: str) -> MessageResponse:
        await self.refresh_tokens.revoke_all_for_user(user_id)
        await self.db.commit()
        return MessageResponse(message="All sessions revoked")

    async def forgot_password(self, email: str) -> MessageResponse:
        user = await self.users.get_by_email(email)
        # Always return success — never leak whether email exists
        if user and user.is_active:
            raw_token = generate_reset_token()
            prt = PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=reset_token_expiry(),
            )
            await self.reset_tokens.create(prt)
            await self.db.commit()
            await send_password_reset_email(email, raw_token)
        return MessageResponse(
            message="If that email is registered, a reset link has been sent."
        )

    async def reset_password(self, data: ResetPasswordRequest) -> MessageResponse:
        token_hash = hash_token(data.token)
        prt = await self.reset_tokens.get_valid_by_hash(token_hash)
        if not prt:
            raise BadRequestException("Invalid or expired reset token")

        user = await self.users.get_by_id(prt.user_id)
        if not user:
            raise NotFoundException("User", prt.user_id)

        await self.users.update(user, {"hashed_password": hash_password(data.new_password)})
        await self.reset_tokens.mark_used(prt)
        # Revoke all refresh tokens on password reset (force re-login everywhere)
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.db.commit()
        return MessageResponse(message="Password reset successfully")

    async def change_password(self, user: User, data: PasswordChange) -> MessageResponse:
        if not verify_password(data.current_password, user.hashed_password):
            raise BadRequestException("Current password is incorrect")
        await self.users.update(user, {"hashed_password": hash_password(data.new_password)})
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.db.commit()
        return MessageResponse(message="Password changed successfully")

    async def update_profile(self, user: User, data: UserUpdateProfile) -> UserResponse:
        updates = data.model_dump(exclude_none=True)
        if updates:
            user = await self.users.update(user, updates)
        await self.db.commit()
        return UserResponse.model_validate(user)

    async def get_me(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)
