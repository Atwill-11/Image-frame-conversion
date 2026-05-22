import logging
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response, FileResponse
from app.config import get_settings
from app.utils.oss import get_object_bytes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/oss", tags=["OSS代理"])
settings = get_settings()

PRESETS_DIR = Path(__file__).resolve().parent.parent.parent / "presets"


@router.get("/image/{key:path}", summary="OSS图片代理")
async def proxy_oss_image(key: str):
    logger.info(f"OSS proxy request: key={key}")

    if not settings.OSS_ENABLED:
        logger.warning(f"OSS not enabled, cannot fetch: {key}")
        if key.startswith("presets/"):
            filename = key[len("presets/"):]
            local_path = PRESETS_DIR / filename
            if local_path.exists():
                logger.info(f"Serving preset from local file: {local_path}")
                return FileResponse(str(local_path))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OSS not enabled",
        )

    try:
        body, content_type = await get_object_bytes(key)
        logger.info(f"OSS fetch success: key={key}, content_type={content_type}, size={len(body)}")
        return Response(content=body, media_type=content_type)
    except Exception as e:
        logger.error(f"OSS fetch failed: key={key}, error={str(e)}")
        if key.startswith("presets/"):
            filename = key[len("presets/"):]
            local_path = PRESETS_DIR / filename
            if local_path.exists():
                logger.info(f"Falling back to local preset file: {local_path}")
                return FileResponse(str(local_path))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to fetch OSS object: {key}, error: {str(e)}",
        )
