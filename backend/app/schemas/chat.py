"""
Pydantic schemas for Chat and Q&A.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class Source(BaseModel):
    file_id: int
    file_name: str
    chunk_index: int
    score: float
    snippet: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class ChatQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    file_ids: List[int] = Field(default_factory=list, description="Scope to specific files; empty = all user files")
    chat_id: Optional[int] = None  # continue existing session
    stream: bool = True


class ChatMessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    sources: Optional[List[Source]]
    tokens_used: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionResponse(BaseModel):
    id: int
    title: Optional[str]
    file_ids: List[int]
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    sessions: List[ChatSessionResponse]
    total: int
