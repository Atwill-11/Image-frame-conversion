from pydantic import BaseModel
from typing import Optional


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[dict | list | str | int | float | bool] = None
