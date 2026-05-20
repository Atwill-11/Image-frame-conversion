from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class ConversationSession(SQLModel, table=True):
    __tablename__ = "conversation_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(default="新会话", max_length=100)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
