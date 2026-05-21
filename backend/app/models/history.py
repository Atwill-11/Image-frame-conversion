from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class HistoryRecord(SQLModel, table=True):
    __tablename__ = "history_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="conversation_sessions.id", index=True)
    original_image_path: str = Field(max_length=500)
    style_image_path: str = Field(max_length=500)
    style_type: str = Field(default="upload", max_length=20, description="风格类型: preset/custom")
    result_image_url: Optional[str] = Field(default=None, max_length=1000)
    result_image_path: Optional[str] = Field(default=None, max_length=500)
    prompt: str = Field(default="请将第一张图片的风格转换为第二张图片的艺术风格，保持人物和构图等内容主体不变。", max_length=1000)
    api_duration: Optional[float] = Field(default=None, description="API调用耗时(秒)")
    api_status: Optional[int] = Field(default=None, description="API响应状态码")
    api_message: Optional[str] = Field(default=None, max_length=500, description="API响应消息")
    created_at: datetime = Field(default_factory=datetime.now)
