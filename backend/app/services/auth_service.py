from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import ConflictException, UnauthorizedException
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.models.user import User
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.user import TokenResponse, UserCreate, UserResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def register(self, data: UserCreate) -> UserResponse:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ConflictException(f"User with email '{data.email}' already exists")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
        )
        user = await self.repo.create(user)
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedException("Account is disabled")

        token = create_access_token(data={"sub": user.id, "role": user.role})
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )
