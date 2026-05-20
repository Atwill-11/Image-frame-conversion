from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func
from app.models.session import ConversationSession
from app.models.history import HistoryRecord
from app.schemas.session import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    SessionListResponse,
)
from fastapi import HTTPException, status
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


def delete_image_file(image_path: str) -> None:
    if not image_path:
        return
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            logger.info(f"Deleted image file: {image_path}")
    except Exception as e:
        logger.error(f"Failed to delete image file {image_path}: {e}")


async def create_session(
    db: AsyncSession, user_id: int, req: SessionCreateRequest
) -> SessionResponse:
    session = ConversationSession(
        user_id=user_id,
        name=req.name,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionResponse.model_validate(session)


async def get_sessions_by_user(
    db: AsyncSession, user_id: int
) -> SessionListResponse:
    count_result = await db.execute(
        select(func.count()).select_from(ConversationSession).where(
            ConversationSession.user_id == user_id
        )
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(ConversationSession)
        .where(ConversationSession.user_id == user_id)
        .order_by(ConversationSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s) for s in sessions],
        total=total,
    )


async def get_session_by_id(
    db: AsyncSession, session_id: int, user_id: int
) -> SessionResponse:
    result = await db.execute(
        select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    return SessionResponse.model_validate(session)


async def update_session(
    db: AsyncSession, session_id: int, user_id: int, req: SessionUpdateRequest
) -> SessionResponse:
    result = await db.execute(
        select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    session.name = req.name
    session.updated_at = datetime.now()
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionResponse.model_validate(session)


async def delete_session(db: AsyncSession, session_id: int, user_id: int) -> None:
    result = await db.execute(
        select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    history_result = await db.execute(
        select(HistoryRecord).where(HistoryRecord.session_id == session_id)
    )
    history_records = history_result.scalars().all()
    for record in history_records:
        delete_image_file(record.original_image_path)
        delete_image_file(record.style_image_path)
        delete_image_file(record.result_image_path)
        await db.delete(record)

    await db.delete(session)
    await db.commit()
