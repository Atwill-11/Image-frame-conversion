from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from app.schemas.style import (
    PresetStyleResponse,
    CustomStyleResponse,
    CustomStyleListResponse,
)
from app.schemas.common import ApiResponse
from app.services.style_service import (
    get_preset_styles,
    get_custom_styles,
    create_custom_style,
    delete_custom_style,
)
from app.utils.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/styles", tags=["风格管理"])


@router.get("/presets", response_model=ApiResponse, summary="获取预设风格列表")
async def list_preset_styles():
    presets = await get_preset_styles()
    return ApiResponse(
        code=0,
        message="success",
        data=[p.model_dump() for p in presets],
    )


@router.get("/custom", response_model=ApiResponse, summary="获取用户自定义风格列表")
async def list_custom_styles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await get_custom_styles(db, current_user.id)
    return ApiResponse(
        code=0,
        message="success",
        data=result.model_dump(),
    )


@router.post("/custom", response_model=ApiResponse, summary="创建自定义风格")
async def create_custom_style_api(
    name: str = Form(...),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    image_content = await image.read()
    result = await create_custom_style(
        db=db,
        user_id=current_user.id,
        name=name,
        image_content=image_content,
        filename=image.filename or "style.jpg",
    )
    return ApiResponse(
        code=0,
        message="创建成功",
        data=result.model_dump(),
    )


@router.delete("/custom/{style_id}", response_model=ApiResponse, summary="删除自定义风格")
async def delete_custom_style_api(
    style_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    await delete_custom_style(db, style_id, current_user.id)
    return ApiResponse(
        code=0,
        message="删除成功",
    )
