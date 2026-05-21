import os
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from app.schemas.style import StyleConvertResponse, HistoryListResponse, HistoryRecordResponse
from app.schemas.common import ApiResponse
from app.services.style import (
    create_style_conversion,
    get_history_by_session,
    delete_history_record,
    save_upload_file,
)
from app.utils.deps import get_current_user
from app.models.user import User
from app.config import get_settings

router = APIRouter(prefix="/api/style", tags=["风格转换"])
settings = get_settings()

PRESETS_DIR = Path(__file__).resolve().parent.parent.parent / "presets"


@router.post("/convert", response_model=ApiResponse, summary="执行风格转换")
async def style_convert(
    session_id: int = Form(..., description="会话ID"),
    content_image: UploadFile = File(..., description="内容图片"),
    style_image: UploadFile = File(default=None, description="风格图片(仅当style_type为upload时需要)"),
    style_type: str = Form(default="upload", description="风格类型: preset/custom/upload"),
    style_image_path: str = Form(default="", description="风格图片路径(仅当style_type为preset或custom时需要)"),
    prompt: str = Form(
        default="",
        description="转换提示词",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))

    content_path = await save_upload_file(content_image, upload_dir, prefix="content_")

    if style_type == "upload":
        if not style_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="style_type为upload时，style_image不能为空",
            )
        style_path = await save_upload_file(style_image, upload_dir, prefix="style_")
    elif style_type == "preset":
        if not style_image_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="style_type为preset时，style_image_path不能为空",
            )
        style_path = str(PRESETS_DIR / style_image_path)
    else:
        if not style_image_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="style_type为custom时，style_image_path不能为空",
            )
        style_path = style_image_path

    result = await create_style_conversion(
        db=db,
        session_id=session_id,
        content_image_path=content_path,
        style_image_path=style_path,
        prompt=prompt,
        upload_dir=upload_dir,
        style_type=style_type,
    )

    return ApiResponse(
        code=0,
        message="风格转换完成",
        data=result.record.model_dump(),
    )


@router.get(
    "/history/{session_id}", response_model=ApiResponse, summary="获取会话历史记录"
)
async def get_history(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await get_history_by_session(db, session_id)
    return ApiResponse(
        code=0,
        message="success",
        data=result.model_dump(),
    )


@router.delete(
    "/history/{record_id}", response_model=ApiResponse, summary="删除单条历史记录"
)
async def delete_history(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    await delete_history_record(db, record_id)
    return ApiResponse(
        code=0,
        message="删除成功",
    )
