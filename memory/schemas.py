from datetime import datetime

from pydantic import BaseModel, Field


class MemoryCandidate(BaseModel):
    memory_type: str = Field(pattern=r"^[a-z_]+$")
    content: str = Field(min_length=3, max_length=240)
    canonical_key: str = Field(min_length=3, max_length=120)
    confidence: float = Field(default=0.8, ge=0, le=1)
    importance: float = Field(default=0.6, ge=0, le=1)


class MemoryRecord(BaseModel):
    id: int
    user_id: str
    memory_type: str
    content: str
    canonical_key: str
    confidence: float
    importance: float
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None = None
    usage_count: int = 0
    active: bool = True

