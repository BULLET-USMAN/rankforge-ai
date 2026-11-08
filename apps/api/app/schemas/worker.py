from typing import Any, Optional

from pydantic import BaseModel, Field


class SmokeTaskRequest(BaseModel):
    x: int = Field(default=21, description="First integer operand")
    y: int = Field(default=21, description="Second integer operand")


class SmokeTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    result: Optional[Any] = None
