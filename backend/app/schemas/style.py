from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class StyleConvertRequest(BaseModel):
    session_id: int
    prompt: str = Field(
        default="请将第一张图片的风格转换为第二张图片的艺术风格，保持人物和构图等内容主体不变。",
        max_length=1000,
    )


class HistoryRecordResponse(BaseModel):
    id: int
    session_id: int
    original_image_path: str
    original_image_url: str = ""
    style_image_path: str
    style_image_url: str = ""
    style_type: str = "upload"
    result_image_url: Optional[str] = None
    result_image_path: Optional[str] = None
    prompt: str
    api_duration: Optional[float] = None
    api_status: Optional[int] = None
    api_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HistoryListResponse(BaseModel):
    records: list[HistoryRecordResponse]
    total: int


class StyleConvertResponse(BaseModel):
    record: HistoryRecordResponse


class PresetStyleResponse(BaseModel):
    id: str
    name: str
    filename: str
    description: str
    image_url: str


class CustomStyleCreate(BaseModel):
    name: str = Field(max_length=100)


class CustomStyleResponse(BaseModel):
    id: int
    user_id: int
    name: str
    image_path: str
    image_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomStyleListResponse(BaseModel):
    styles: list[CustomStyleResponse]
    total: int
