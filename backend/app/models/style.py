from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class CustomStyle(SQLModel, table=True):
    __tablename__ = "custom_styles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100)
    image_path: str = Field(max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)
