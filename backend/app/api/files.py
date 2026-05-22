"""
File upload, listing, deletion, and streaming API routes.
POST   /api/files/upload
GET    /api/files
GET    /api/files/{id}
DELETE /api/files/{id}
GET    /api/media/stream/{id}
"""
import os
import uuid
import mimetypes
import logging
import asyncio
from pathlib import Path

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile,
    File as FastAPIFile, status, BackgroundTasks, Request
)
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.db.database import get_db
from app.core.config import settings
from app.core.security import get_current_user_id
from app.models.models import File, FileType, ProcessingStatus, ActivityLog
from app.schemas.files import FileUploadResponse, FileListResponse, FileDetailResponse
from app.services.pdf_service import process_pdf
from app.services.media_service import process_media

router = APIRouter(tags=["Files"])
logger = logging.getLogger(__name__)

# Mime type to FileType mapping
MIME_TO_FILETYPE = {
    "application/pdf": FileType.PDF,
    "audio/mpeg": FileType.AUDIO,
    "audio/mp3": FileType.AUDIO,
    "audio/wav": FileType.AUDIO,
    "audio/x-wav": FileType.AUDIO,
    "audio/ogg": FileType.AUDIO,
    "video/mp4": FileType.VIDEO,
    "video/quicktime": FileType.VIDEO,
    "video/x-msvideo": FileType.VIDEO,
    "video/webm": FileType.VIDEO,
    "video/avi": FileType.VIDEO,
}


def _detect_file_type(filename: str, content_type: str) -> FileType:
    ext = Path(filename).suffix.lower().lstrip(".")
    pdf_exts = {"pdf"}
    audio_exts = {"mp3", "wav", "ogg", "m4a", "flac", "aac"}
    video_exts = {"mp4", "mov", "avi", "webm", "mkv", "wmv"}

    if ext in pdf_exts or content_type == "application/pdf":
        return FileType.PDF
    if ext in audio_exts or content_type.startswith("audio/"):
        return FileType.AUDIO
    if ext in video_exts or content_type.startswith("video/"):
        return FileType.VIDEO

    raise HTTPException(
        status_code=415,
        detail=f"Unsupported file type: .{ext}. Allowed: PDF, MP3, WAV, MP4, MOV",
    )


async def _run_processing(file_id: int, file_path: str, file_type: FileType):
    """Background task: run appropriate processing pipeline."""
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            if file_type == FileType.PDF:
                await process_pdf(file_id, file_path, db)
            else:
                await process_media(file_id, file_path, db)
        except Exception as e:
            logger.error(f"Background processing error for file {file_id}: {e}")


@router.post("/api/files/upload", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = FastAPIFile(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF, audio, or video file and queue it for processing."""
    content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or ""
    file_type = _detect_file_type(file.filename, content_type)

    # Generate unique stored filename
    file_uuid = str(uuid.uuid4())
    ext = Path(file.filename).suffix
    stored_name = f"{file_uuid}{ext}"
    upload_path = os.path.join(settings.UPLOAD_DIR, stored_name)

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    size_bytes = 0
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    # Write file to disk in chunks to avoid loading large files (up to 500MB) in memory
    try:
        with open(upload_path, "wb") as f_out:
            while chunk := await file.read(65536):
                size_bytes += len(chunk)
                if size_bytes > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB",
                    )
                f_out.write(chunk)
    except HTTPException:
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise
    except Exception as e:
        if os.path.exists(upload_path):
            os.remove(upload_path)
        logger.error(f"Error saving uploaded file: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error writing file to disk"
        )

    # Save metadata to DB
    db_file = File(
        uuid=file_uuid,
        original_name=file.filename,
        stored_name=stored_name,
        file_type=file_type,
        mime_type=content_type,
        size_bytes=size_bytes,
        status=ProcessingStatus.PENDING,
        owner_id=user_id,
    )
    db.add(db_file)
    db.add(ActivityLog(
        user_id=user_id,
        action="file_upload",
        resource_type="file",
        extra_data={"filename": file.filename, "size_bytes": size_bytes},
    ))
    await db.commit()
    await db.refresh(db_file)

    # Queue background processing
    background_tasks.add_task(_run_processing, db_file.id, upload_path, file_type)

    return db_file


@router.get("/api/files", response_model=FileListResponse)
async def list_files(
    page: int = 1,
    page_size: int = 20,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all files owned by the authenticated user."""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(File)
        .where(File.owner_id == user_id)
        .order_by(File.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    files = result.scalars().all()

    count_result = await db.execute(
        select(func.count(File.id)).where(File.owner_id == user_id)
    )
    total = count_result.scalar_one()

    return FileListResponse(files=list(files), total=total, page=page, page_size=page_size)


@router.get("/api/files/{file_id}", response_model=FileDetailResponse)
async def get_file(
    file_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed metadata for a specific file."""
    result = await db.execute(
        select(File).where(and_(File.id == file_id, File.owner_id == user_id))
    )
    file_obj = result.scalar_one_or_none()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    return file_obj


@router.delete("/api/files/{file_id}", status_code=204)
async def delete_file(
    file_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a file and its associated data."""
    result = await db.execute(
        select(File).where(and_(File.id == file_id, File.owner_id == user_id))
    )
    file_obj = result.scalar_one_or_none()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    # Remove physical file
    upload_path = os.path.join(settings.UPLOAD_DIR, file_obj.stored_name)
    if os.path.exists(upload_path):
        os.remove(upload_path)

    # Remove FAISS index directory
    if file_obj.faiss_index_path and os.path.exists(file_obj.faiss_index_path):
        import shutil
        shutil.rmtree(file_obj.faiss_index_path, ignore_errors=True)

    db.add(ActivityLog(
        user_id=user_id,
        action="file_delete",
        resource_type="file",
        resource_id=str(file_id),
    ))
    await db.delete(file_obj)
    await db.commit()


@router.get("/api/media/stream/{file_id}")
async def stream_media(
    file_id: int,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Stream audio/video file with HTTP Range support."""
    result = await db.execute(
        select(File).where(and_(File.id == file_id, File.owner_id == user_id))
    )
    file_obj = result.scalar_one_or_none()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = os.path.join(settings.UPLOAD_DIR, file_obj.stored_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Physical file not found")

    file_size = os.path.getsize(file_path)
    media_type = file_obj.mime_type or "application/octet-stream"

    # Support HTTP Range requests for seeking
    range_header = request.headers.get("Range")
    if range_header:
        range_val = range_header.strip().replace("bytes=", "")
        start_str, _, end_str = range_val.partition("-")
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
        end = min(end, file_size - 1)
        chunk_size = end - start + 1

        def iter_file():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    data = f.read(min(65536, remaining))
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": media_type,
        }
        return StreamingResponse(iter_file(), status_code=206, headers=headers)

    return FileResponse(file_path, media_type=media_type, filename=file_obj.original_name)
