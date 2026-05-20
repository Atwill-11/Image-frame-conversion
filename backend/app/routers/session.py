from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from app.schemas.session import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
)
from app.schemas.common import ApiResponse
from app.services.session import (
    create_session,
    get_sessions_by_user,
    get_session_by_id,
    update_session,
    delete_session,
)
from app.utils.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/sessions", tags=["会话管理"])


@router.post("/", response_model=ApiResponse, summary="创建会话")
async def create_new_session(
    req: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    session = await create_session(db, current_user.id, req)
    return ApiResponse(
        code=0,
        message="创建成功",
        data=session.model_dump(),
    )


@router.get("/", response_model=ApiResponse, summary="获取用户所有会话")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await get_sessions_by_user(db, current_user.id)
    return ApiResponse(
        code=0,
        message="success",
        data=result.model_dump(),
    )


@router.get("/{session_id}", response_model=ApiResponse, summary="获取会话详情")
async def get_session_detail(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    session = await get_session_by_id(db, session_id, current_user.id)
    return ApiResponse(
        code=0,
        message="success",
        data=session.model_dump(),
    )


@router.put("/{session_id}", response_model=ApiResponse, summary="更新会话")
async def update_session_detail(
    session_id: int,
    req: SessionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    session = await update_session(db, session_id, current_user.id, req)
    return ApiResponse(
        code=0,
        message="更新成功",
        data=session.model_dump(),
    )


@router.delete("/{session_id}", response_model=ApiResponse, summary="删除会话")
async def delete_session_by_id(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    await delete_session(db, session_id, current_user.id)
    return ApiResponse(
        code=0,
        message="删除成功",
    )
