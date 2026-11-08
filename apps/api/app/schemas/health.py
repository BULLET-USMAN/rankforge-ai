from datetime import datetime, timezone
from typing import Dict, Optional

from pydantic import BaseModel, Field


class LivenessResponse(BaseModel):
    status: str = Field(default="alive", description="Process liveness state")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DependencyHealth(BaseModel):
    status: str = Field(..., description="ok, degraded, or unreachable")
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class ReadinessResponse(BaseModel):
    status: str = Field(..., description="ready or not_ready")
    environment: str
    dependencies: Dict[str, DependencyHealth]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
