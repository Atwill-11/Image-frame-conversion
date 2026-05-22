import os
import base64
import tempfile
import time
import logging
import httpx
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.models.history import HistoryRecord
from app.models.session import ConversationSession
from app.schemas.style import StyleConvertResponse, HistoryRecordResponse, HistoryListResponse
from app.utils.oss import upload_bytes, delete_object, extract_key_from_url, get_object_bytes
from app.services.style_service import get_image_url_from_path
from fastapi import HTTPException, status, UploadFile

logger = logging.getLogger(__name__)
settings = get_settings()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_mime_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return MIME_MAP.get(ext, "image/jpeg")


def validate_image_file(filename: str) -> None:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片格式: {ext}，支持格式: {', '.join(ALLOWED_EXTENSIONS)}",
        )


async def save_upload_file(file: UploadFile, user_id: int, prefix: str = "") -> str:
    validate_image_file(file.filename)

    ext = os.path.splitext(file.filename)[1].lower()
    timestamp = int(time.time() * 1000)
    filename = f"{prefix}{timestamp}{ext}"
    content_type = MIME_MAP.get(ext, "image/jpeg")

    content = await file.read()

    if settings.OSS_ENABLED:
        key = f"uploads/{user_id}/{filename}"
        url = await upload_bytes(key, content, content_type)
        return url

    upload_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content)
    return filepath


async def download_result_image(image_url: str, user_id: int) -> str:
    timestamp = int(time.time() * 1000)
    filename = f"result_{timestamp}.png"

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(image_url)
        if response.status_code != 200:
            logger.error(f"Failed to download result image: {response.status_code}")
            return None

        if settings.OSS_ENABLED:
            key = f"uploads/{user_id}/{filename}"
            url = await upload_bytes(key, response.content, "image/png")
            return url

        upload_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)
        logger.info(f"Result image downloaded: {filepath}")
        return filepath


async def get_image_base64(image_path: str) -> tuple[str, str]:
    if image_path.startswith("http"):
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(image_path)
            content_bytes = resp.content
        content_base64 = base64.b64encode(content_bytes).decode("utf-8")
        return content_base64, "image/jpeg"

    if image_path.startswith("/api/oss/image/"):
        key = image_path[len("/api/oss/image/"):]
        content_bytes, content_type = await get_object_bytes(key)
        content_base64 = base64.b64encode(content_bytes).decode("utf-8")
        return content_base64, content_type

    if settings.OSS_ENABLED and not os.path.exists(image_path):
        content_bytes, content_type = await get_object_bytes(image_path)
        content_base64 = base64.b64encode(content_bytes).decode("utf-8")
        return content_base64, content_type

    content_base64 = encode_image(image_path)
    content_mime = get_mime_type(image_path)
    return content_base64, content_mime


async def call_style_transfer_api(
    content_image_path: str,
    style_image_path: str,
    prompt: str,
) -> dict:
    content_base64, content_mime = await get_image_base64(content_image_path)
    style_base64, style_mime = await get_image_base64(style_image_path)

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
            "full_prompt": full_prompt,
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
            "full_prompt": full_prompt,
        }

    return {
        "success": True,
        "status_code": response.status_code,
        "message": "success",
        "duration": duration,
        "image_url": image_url,
        "full_prompt": full_prompt,
    }


async def create_style_conversion(
    db: AsyncSession,
    session_id: int,
    content_image_path: str,
    style_image_path: str,
    prompt: str,
    user_id: int = None,
    style_type: str = "upload",
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

    if api_result["success"] and result_image_url and user_id:
        result_image_path = await download_result_image(result_image_url, user_id)

    full_prompt = api_result.get("full_prompt", prompt)

    record = HistoryRecord(
        session_id=session_id,
        original_image_path=content_image_path,
        style_image_path=style_image_path,
        style_type=style_type,
        result_image_url=result_image_url,
        result_image_path=result_image_path,
        prompt=full_prompt,
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

    record_dict = {
        "id": record.id,
        "session_id": record.session_id,
        "original_image_path": record.original_image_path,
        "original_image_url": get_image_url_from_path(record.original_image_path),
        "style_image_path": record.style_image_path,
        "style_image_url": get_image_url_from_path(record.style_image_path),
        "style_type": record.style_type,
        "result_image_url": record.result_image_url,
        "result_image_path": record.result_image_path,
        "prompt": record.prompt,
        "api_duration": record.api_duration,
        "api_status": record.api_status,
        "api_message": record.api_message,
        "created_at": record.created_at,
    }

    return StyleConvertResponse(
        record=HistoryRecordResponse(**record_dict)
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

    record_responses = []
    for r in records:
        record_dict = {
            "id": r.id,
            "session_id": r.session_id,
            "original_image_path": r.original_image_path,
            "original_image_url": get_image_url_from_path(r.original_image_path),
            "style_image_path": r.style_image_path,
            "style_image_url": get_image_url_from_path(r.style_image_path),
            "style_type": r.style_type,
            "result_image_url": r.result_image_url,
            "result_image_path": r.result_image_path,
            "prompt": r.prompt,
            "api_duration": r.api_duration,
            "api_status": r.api_status,
            "api_message": r.api_message,
            "created_at": r.created_at,
        }
        record_responses.append(HistoryRecordResponse(**record_dict))

    return HistoryListResponse(
        records=record_responses,
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

    if settings.OSS_ENABLED:
        content_key = extract_key_from_url(record.original_image_path)
        if content_key:
            await delete_object(content_key)
        if record.style_type == "upload":
            style_key = extract_key_from_url(record.style_image_path)
            if style_key:
                await delete_object(style_key)
        if record.result_image_path:
            result_key = extract_key_from_url(record.result_image_path)
            if result_key:
                await delete_object(result_key)
    else:
        delete_image_file(record.original_image_path)
        if record.style_type == "upload":
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
