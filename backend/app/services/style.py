import os
import base64
import time
import logging
import httpx
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.models.history import HistoryRecord
from app.models.session import ConversationSession
from app.schemas.style import StyleConvertResponse, HistoryRecordResponse, HistoryListResponse
from fastapi import HTTPException, status, UploadFile

logger = logging.getLogger(__name__)
settings = get_settings()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_mime_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    return mime_map.get(ext, "image/jpeg")


def validate_image_file(filename: str) -> None:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片格式: {ext}，支持格式: {', '.join(ALLOWED_EXTENSIONS)}",
        )


async def save_upload_file(file: UploadFile, upload_dir: str, prefix: str = "") -> str:
    validate_image_file(file.filename)

    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower()
    timestamp = int(time.time() * 1000)
    filename = f"{prefix}{timestamp}{ext}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    return filepath


async def download_result_image(image_url: str, upload_dir: str) -> str:
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = int(time.time() * 1000)
    filename = f"result_{timestamp}.png"
    filepath = os.path.join(upload_dir, filename)

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(image_url)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            logger.info(f"Result image downloaded: {filepath}")
            return filepath
        else:
            logger.error(f"Failed to download result image: {response.status_code}")
            return None


async def call_style_transfer_api(
    content_image_path: str,
    style_image_path: str,
    prompt: str,
) -> dict:
    content_base64 = encode_image(content_image_path)
    style_base64 = encode_image(style_image_path)

    content_mime = get_mime_type(content_image_path)
    style_mime = get_mime_type(style_image_path)

    base_prompt = "以第一张图片为内容参考，第二张图片为风格参考，进行艺术风格迁移。请保持原图的人物、构图、场景等主要内容不变，仅转换艺术风格。"
    full_prompt = base_prompt
    if prompt and prompt.strip():
        full_prompt = f"{base_prompt} {prompt.strip()}"

    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"data:{content_mime};base64,{content_base64}"},
                {"image": f"data:{style_mime};base64,{style_base64}"},
                {"text": full_prompt},
            ],
        }
    ]

    payload = {
        "model": settings.DASHSCOPE_MODEL,
        "input": {
            "messages": messages,
        },
        "parameters": {
            "result_format": "message",
            "n": 1,
        },
    }

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    headers = {
        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }

    start_time = time.time()
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload, headers=headers)
    duration = round(time.time() - start_time, 2)

    if response.status_code != 200:
        logger.error(f"DashScope API error: {response.status_code} - {response.text}")
        return {
            "success": False,
            "status_code": response.status_code,
            "message": response.text[:500],
            "duration": duration,
            "image_url": None,
        }

    data = response.json()

    try:
        output = data["output"]
        choices = output.get("choices", [])
        if choices:
            content_list = choices[0].get("message", {}).get("content", [])
            image_url = None
            for item in content_list:
                if "image" in item:
                    image_url = item["image"]
                    break
        else:
            image_url = None
    except (KeyError, IndexError) as e:
        logger.error(f"Parse response error: {e}, data: {data}")
        return {
            "success": False,
            "status_code": response.status_code,
            "message": f"解析响应失败: {str(e)}",
            "duration": duration,
            "image_url": None,
        }

    return {
        "success": True,
        "status_code": response.status_code,
        "message": "success",
        "duration": duration,
        "image_url": image_url,
    }


async def create_style_conversion(
    db: AsyncSession,
    session_id: int,
    content_image_path: str,
    style_image_path: str,
    prompt: str,
    upload_dir: str = None,
) -> StyleConvertResponse:
    result = await db.execute(
        select(ConversationSession).where(ConversationSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    api_result = await call_style_transfer_api(
        content_image_path, style_image_path, prompt
    )

    result_image_url = api_result.get("image_url")
    result_image_path = None

    if api_result["success"] and result_image_url and upload_dir:
        result_image_path = await download_result_image(result_image_url, upload_dir)

    record = HistoryRecord(
        session_id=session_id,
        original_image_path=content_image_path,
        style_image_path=style_image_path,
        result_image_url=result_image_url,
        result_image_path=result_image_path,
        prompt=prompt,
        api_duration=api_result.get("duration"),
        api_status=api_result.get("status_code"),
        api_message=api_result.get("message"),
    )

    if not api_result["success"]:
        record.result_image_url = None
        record.result_image_path = None

    db.add(record)
    await db.commit()
    await db.refresh(record)

    return StyleConvertResponse(
        record=HistoryRecordResponse.model_validate(record)
    )


async def get_history_by_session(
    db: AsyncSession, session_id: int
) -> HistoryListResponse:
    result = await db.execute(
        select(HistoryRecord)
        .where(HistoryRecord.session_id == session_id)
        .order_by(HistoryRecord.created_at.desc())
    )
    records = result.scalars().all()

    return HistoryListResponse(
        records=[HistoryRecordResponse.model_validate(r) for r in records],
        total=len(records),
    )


async def delete_history_record(db: AsyncSession, record_id: int) -> None:
    result = await db.execute(
        select(HistoryRecord).where(HistoryRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="历史记录不存在",
        )

    delete_image_file(record.original_image_path)
    delete_image_file(record.style_image_path)
    delete_image_file(record.result_image_path)

    await db.delete(record)
    await db.commit()


def delete_image_file(image_path: str) -> None:
    if not image_path:
        return
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            logger.info(f"Deleted image file: {image_path}")
    except Exception as e:
        logger.error(f"Failed to delete image file {image_path}: {e}")
