from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from app.schemas.user import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from app.schemas.common import ApiResponse
from app.services.auth import register_user, login_user
from app.utils.deps import get_current_user, delete_token
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=ApiResponse, summary="用户注册")
async def register(
    req: UserRegisterRequest,
    db: AsyncSession = Depends(get_session),
):
    user = await register_user(db, req)
    return ApiResponse(
        code=0,
        message="注册成功",
        data=user.model_dump(),
    )


@router.post("/login", response_model=ApiResponse, summary="用户登录")
async def login(
    req: UserLoginRequest,
    db: AsyncSession = Depends(get_session),
):
    token_resp = await login_user(db, req)
    return ApiResponse(
        code=0,
        message="登录成功",
        data=token_resp.model_dump(),
    )


@router.post("/logout", response_model=ApiResponse, summary="用户登出")
async def logout(current_user: User = Depends(get_current_user)):
    await delete_token(current_user.id)
    return ApiResponse(
        code=0,
        message="登出成功",
    )


@router.get("/me", response_model=ApiResponse, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    return ApiResponse(
        code=0,
        message="success",
        data=UserResponse.model_validate(current_user).model_dump(),
    )
