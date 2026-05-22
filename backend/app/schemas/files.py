"""
Pydantic schemas for File upload, listing, and metadata.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FileUploadResponse(BaseModel):
    id: int
    uuid: str
    original_name: str
    file_type: str
    mime_type: Optional[str]
    size_bytes: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    files: list[FileUploadResponse]
    total: int
    page: int
    page_size: int


class FileDetailResponse(FileUploadResponse):
    duration_seconds: Optional[float]
    error_message: Optional[str]
    faiss_index_path: Optional[str]
    updated_at: datetime
