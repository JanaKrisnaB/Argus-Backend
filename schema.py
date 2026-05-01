from pydantic import BaseModel
from typing import Literal, List, Optional


class ReviewComment(BaseModel):
    line: int
    comment: str
    severity: Literal["low", "medium", "high"]
    confidence: float


class ReviewRequest(BaseModel):
    code: str
    config: Literal["A", "B", "C"] = "C"


class ReviewResponse(BaseModel):
    comments: List[ReviewComment]
    critic_log: str
    memory_count: int


class MemoryRecord(BaseModel):
    id: str
    comment: str
    severity: str
    confidence: float


class MemorySearchRequest(BaseModel):
    query: str
    top_k: int = 5
