import json
import os
import re
import time
from pathlib import Path
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func
from app.models.style import CustomStyle
from app.schemas.style import (
    PresetStyleResponse,
    CustomStyleResponse,
    CustomStyleListResponse,
)
from app.config import get_settings
from app.utils.oss import upload_bytes, delete_object, extract_key_from_url, get_oss_url
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

PRESETS_DIR = Path(__file__).resolve().parent.parent.parent / "presets"


def get_presets_config_path() -> Path:
    return PRESETS_DIR / "presets.json"


def get_preset_image_path(filename: str) -> Path:
    return PRESETS_DIR / filename


def get_image_url_from_path(image_path: str) -> str:
    if image_path.startswith("http"):
        return image_path
    if image_path.startswith("/api/"):
        return image_path

    parts = re.split(r"[/\\]", image_path)
    uploads_index = -1
    for i, p in enumerate(parts):
        if p == "uploads":
            uploads_index = i
            break
    if uploads_index != -1 and uploads_index < len(parts) - 1:
        return "/" + "/".join(parts[uploads_index:])

    presets_index = -1
    for i, p in enumerate(parts):
        if p == "presets":
            presets_index = i
            break
    if presets_index != -1 and presets_index < len(parts) - 1:
        return "/" + "/".join(parts[presets_index:])

    return "/uploads/" + parts[-1]


async def get_preset_styles() -> list[PresetStyleResponse]:
    config_path = get_presets_config_path()
    if not config_path.exists():
        return []

    with open(config_path, "r", encoding="utf-8") as f:
        presets = json.load(f)

    result = []
    for preset in presets:
        if settings.OSS_ENABLED:
            image_url = get_oss_url(f"presets/{preset['filename']}")
        else:
            image_url = f"/presets/{preset['filename']}"
        result.append(
            PresetStyleResponse(
                id=preset["id"],
                name=preset["name"],
                filename=preset["filename"],
                description=preset["description"],
                image_url=image_url,
            )
        )

    return result


async def get_custom_styles(
    db: AsyncSession, user_id: int
) -> CustomStyleListResponse:
    count_result = await db.execute(
        select(func.count()).select_from(CustomStyle).where(
            CustomStyle.user_id == user_id
        )
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(CustomStyle)
        .where(CustomStyle.user_id == user_id)
        .order_by(CustomStyle.created_at.desc())
    )
    styles = result.scalars().all()

    style_responses = []
    for style in styles:
        image_url = get_image_url_from_path(style.image_path)
        style_responses.append(
            CustomStyleResponse(
                id=style.id,
                user_id=style.user_id,
                name=style.name,
                image_path=style.image_path,
                image_url=image_url,
                created_at=style.created_at,
            )
        )

    return CustomStyleListResponse(styles=style_responses, total=total)


async def create_custom_style(
    db: AsyncSession,
    user_id: int,
    name: str,
    image_content: bytes,
    filename: str,
) -> CustomStyleResponse:
    timestamp = int(time.time() * 1000)
    ext = os.path.splitext(filename)[1] or ".jpg"
    new_filename = f"style_{timestamp}{ext}"

    if settings.OSS_ENABLED:
        key = f"uploads/{user_id}/custom_styles/{new_filename}"
        content_type_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp", ".bmp": "image/bmp",
        }
        content_type = content_type_map.get(ext, "image/jpeg")
        image_path = await upload_bytes(key, image_content, content_type)
    else:
        style_dir = Path(__file__).parent.parent.parent / "uploads" / str(user_id) / "custom_styles"
        style_dir.mkdir(parents=True, exist_ok=True)
        filepath = str(style_dir / new_filename)
        with open(filepath, "wb") as f:
            f.write(image_content)
        image_path = filepath

    logger.info(f"Custom style image saved: {image_path}")

    custom_style = CustomStyle(
        user_id=user_id,
        name=name,
        image_path=image_path,
    )
    db.add(custom_style)
    await db.commit()
    await db.refresh(custom_style)

    image_url = get_image_url_from_path(image_path)
    return CustomStyleResponse(
        id=custom_style.id,
        user_id=custom_style.user_id,
        name=custom_style.name,
        image_path=custom_style.image_path,
        image_url=image_url,
        created_at=custom_style.created_at,
    )


async def delete_custom_style(
    db: AsyncSession, style_id: int, user_id: int
) -> None:
    result = await db.execute(
        select(CustomStyle).where(
            CustomStyle.id == style_id,
            CustomStyle.user_id == user_id,
        )
    )
    style = result.scalar_one_or_none()

    if style is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风格不存在",
        )

    if settings.OSS_ENABLED:
        key = extract_key_from_url(style.image_path)
        if key:
            await delete_object(key)
            logger.info(f"Deleted OSS custom style image: {key}")
    elif style.image_path and os.path.exists(style.image_path):
        try:
            os.remove(style.image_path)
            logger.info(f"Deleted custom style image: {style.image_path}")
        except Exception as e:
            logger.error(f"Failed to delete custom style image: {e}")

    await db.delete(style)
    await db.commit()
