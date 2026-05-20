from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.utils.security import hash_password, verify_password
from app.utils.deps import create_access_token, store_token
from app.schemas.user import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from fastapi import HTTPException, status


async def register_user(db: AsyncSession, req: UserRegisterRequest) -> UserResponse:
    result = await db.execute(select(User).where(User.username == req.username))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    user = User(
        username=req.username,
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


async def login_user(db: AsyncSession, req: UserLoginRequest) -> TokenResponse:
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    token = create_access_token(user.id, user.username)
    await store_token(token, user.id)

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )
