"""
Summary and Timestamp search API routes.
GET  /api/summary/{file_id}
POST /api/timestamps/search
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.database import get_db
from app.core.security import get_current_user_id
from app.models.models import File, Summary as SummaryModel, ProcessingStatus
from app.schemas.summary import (
    SummaryResponse, TimestampSearchRequest, TimestampSearchResponse, TimestampResult
)
from app.services.summary_service import generate_summary
from app.services.chat_service import get_relevant_chunks

router = APIRouter(tags=["Summary & Timestamps"])
logger = logging.getLogger(__name__)


@router.get("/api/summary/{file_id}", response_model=SummaryResponse)
async def get_summary(
    file_id: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get (or generate) a summary for a file.
    If summary exists in DB, returns it. Otherwise generates async.
    """
    # Verify ownership
    result = await db.execute(
        select(File).where(and_(File.id == file_id, File.owner_id == user_id))
    )
    file_obj = result.scalar_one_or_none()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    if file_obj.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"File is not yet processed. Status: {file_obj.status.value}"
        )

    # Check if summary already exists
    sum_result = await db.execute(
        select(SummaryModel).where(SummaryModel.file_id == file_id)
    )
    existing = sum_result.scalar_one_or_none()
    if existing:
        return existing

    # Generate summary (blocking for first request)
    try:
        await generate_summary(file_id, db)
        sum_result = await db.execute(
            select(SummaryModel).where(SummaryModel.file_id == file_id)
        )
        return sum_result.scalar_one()
    except Exception as e:
        logger.error(f"Summary generation failed for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.post("/api/timestamps/search", response_model=TimestampSearchResponse)
async def search_timestamps(
    body: TimestampSearchRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Semantic timestamp search: find where a topic was discussed in audio/video.
    Returns ranked segments with timestamps and confidence scores.
    """
    # Verify ownership
    result = await db.execute(
        select(File).where(and_(File.id == body.file_id, File.owner_id == user_id))
    )
    file_obj = result.scalar_one_or_none()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    if file_obj.status != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="File not yet processed")

    # Get relevant chunks with timestamps via semantic search
    chunks = await get_relevant_chunks(
        query=body.query,
        file_ids=[body.file_id],
        top_k=body.top_k,
        db=db,
    )

    # Filter to only chunks that have timestamps (audio/video)
    results = []
    for chunk in chunks:
        if chunk.get("start_time") is not None:
            results.append(TimestampResult(
                start_time=chunk["start_time"],
                end_time=chunk["end_time"],
                snippet=chunk["content"][:300],
                confidence=min(chunk["score"], 1.0),
                chunk_index=chunk["chunk_index"],
            ))
        else:
            # PDF chunk - return with position info
            results.append(TimestampResult(
                start_time=0.0,
                end_time=0.0,
                snippet=chunk["content"][:300],
                confidence=min(chunk["score"], 1.0),
                chunk_index=chunk["chunk_index"],
            ))

    return TimestampSearchResponse(
        query=body.query,
        file_id=body.file_id,
        results=results,
    )
