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
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

PRESETS_DIR = Path(__file__).parent.parent.parent / "presets"


def get_presets_config_path() -> Path:
    return PRESETS_DIR / "presets.json"


def get_preset_image_path(filename: str) -> Path:
    return PRESETS_DIR / filename


def get_user_custom_style_dir(user_id: int) -> str:
    base_dir = Path(__file__).parent.parent.parent / "uploads" / str(user_id) / "custom_styles"
    base_dir.mkdir(parents=True, exist_ok=True)
    return str(base_dir)


def get_image_url_from_path(image_path: str) -> str:
    parts = re.split(r"[/\\]", image_path)
    uploads_index = -1
    for i, p in enumerate(parts):
        if p == "uploads":
            uploads_index = i
            break
    if uploads_index != -1 and uploads_index < len(parts) - 1:
        return "/" + "/".join(parts[uploads_index:])
    return "/uploads/" + parts[-1]


async def get_preset_styles() -> list[PresetStyleResponse]:
    config_path = get_presets_config_path()
    if not config_path.exists():
        return []

    with open(config_path, "r", encoding="utf-8") as f:
        presets = json.load(f)

    result = []
    for preset in presets:
        image_path = get_preset_image_path(preset["filename"])
        image_url = f"/presets/{preset['filename']}" if image_path.exists() else ""
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
    style_dir = get_user_custom_style_dir(user_id)

    timestamp = int(time.time() * 1000)
    ext = os.path.splitext(filename)[1] or ".jpg"
    new_filename = f"style_{timestamp}{ext}"
    filepath = os.path.join(style_dir, new_filename)

    with open(filepath, "wb") as f:
        f.write(image_content)

    logger.info(f"Custom style image saved: {filepath}")

    custom_style = CustomStyle(
        user_id=user_id,
        name=name,
        image_path=filepath,
    )
    db.add(custom_style)
    await db.commit()
    await db.refresh(custom_style)

    image_url = get_image_url_from_path(filepath)
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

    if style.image_path and os.path.exists(style.image_path):
        try:
            os.remove(style.image_path)
            logger.info(f"Deleted custom style image: {style.image_path}")
        except Exception as e:
            logger.error(f"Failed to delete custom style image: {e}")

    await db.delete(style)
    await db.commit()
