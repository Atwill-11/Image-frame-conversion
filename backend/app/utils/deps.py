import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.database import get_session
from app.models.user import User
from app.utils.redis import get_redis

settings = get_settings()
security = HTTPBearer()


def create_access_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


async def store_token(token: str, user_id: int):
    r = await get_redis()
    key = f"token:{user_id}"
    await r.set(key, token, ex=settings.TOKEN_EXPIRE_MINUTES * 60)


async def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效Token",
        )


async def check_token_in_redis(user_id: int, token: str) -> bool:
    r = await get_redis()
    key = f"token:{user_id}"
    stored_token = await r.get(key)
    return stored_token == token


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session),
) -> User:
    token = credentials.credentials
    payload = await verify_token(token)

    user_id = int(payload.get("sub"))
    username = payload.get("username")

    valid = await check_token_in_redis(user_id, token)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已失效，请重新登录",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    return user


async def delete_token(user_id: int):
    r = await get_redis()
    key = f"token:{user_id}"
    await r.delete(key)
