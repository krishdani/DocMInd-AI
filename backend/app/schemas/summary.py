"""
Pydantic schemas for Summaries and Timestamp search.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class KeyTopic(BaseModel):
    topic: str
    confidence: float
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    snippet: Optional[str] = None


class SummaryResponse(BaseModel):
    id: int
    file_id: int
    short_summary: Optional[str]
    detailed_summary: Optional[str]
    bullet_points: Optional[List[str]]
    key_topics: Optional[List[KeyTopic]]
    word_count: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class TimestampSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    file_id: int
    top_k: int = Field(default=5, ge=1, le=20)


class TimestampResult(BaseModel):
    start_time: float
    end_time: float
    snippet: str
    confidence: float
    chunk_index: int


class TimestampSearchResponse(BaseModel):
    query: str
    file_id: int
    results: List[TimestampResult]
