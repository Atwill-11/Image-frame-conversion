from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SessionCreateRequest(BaseModel):
    name: str = Field(default="新会话", max_length=100)


class SessionUpdateRequest(BaseModel):
    name: str = Field(..., max_length=100)


class SessionResponse(BaseModel):
    id: int
    user_id: int
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
