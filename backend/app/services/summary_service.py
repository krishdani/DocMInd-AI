"""
Summarization service using OpenAI GPT.
Generates short, detailed, bullet-point summaries + key topics.
Results cached in Redis to avoid redundant API calls.
"""
import json
import logging
from typing import Dict, Any
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.redis_client import cache_get, cache_set
from app.models.models import File, Transcript, Summary, DocumentChunk, FileType

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def _get_document_text(file_id: int, db: AsyncSession) -> str:
    """Retrieve full text for a file (transcript or PDF chunks)."""
    # Try transcript first (audio/video)
    result = await db.execute(
        select(Transcript.full_text).where(Transcript.file_id == file_id)
    )
    row = result.scalar_one_or_none()
    if row:
        return row

    # Fall back to concatenated PDF chunks
    result = await db.execute(
        select(DocumentChunk.content)
        .where(DocumentChunk.file_id == file_id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = result.scalars().all()
    return "\n\n".join(chunks) if chunks else ""


async def generate_summary(file_id: int, db: AsyncSession) -> Dict[str, Any]:
    """
    Generate all summary types for a file.
    Returns dict with short, detailed, bullets, topics.
    Caches result in Redis.
    """
    cache_key = f"summary:{file_id}"
    cached = await cache_get(cache_key)
    if cached:
        logger.info(f"Cache hit for summary of file {file_id}")
        return cached

    text = await _get_document_text(file_id, db)
    if not text:
        raise ValueError(f"No text content found for file {file_id}")

    # Truncate to avoid token limits (~16k chars ≈ 4k tokens)
    truncated = text[:16000] if len(text) > 16000 else text

    # Fetch segments for timestamp-aware topic extraction
    seg_result = await db.execute(
        select(Transcript.segments).where(Transcript.file_id == file_id)
    )
    segments = seg_result.scalar_one_or_none() or []

    prompt = f"""Analyze the following document content and provide a comprehensive summary.

Document Content:
{truncated}

Return a JSON object with EXACTLY these keys:
{{
  "short_summary": "2-3 sentence executive summary",
  "detailed_summary": "Comprehensive 3-5 paragraph detailed summary covering all major points",
  "bullet_points": ["Key point 1", "Key point 2", "Key point 3", ...],
  "key_topics": [
    {{"topic": "Topic name", "confidence": 0.95, "snippet": "Brief quote or description"}},
    ...
  ],
  "word_count": <integer word count of original text>
}}

Provide 5-10 bullet points and 5-8 key topics. Return only valid JSON."""

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    data["word_count"] = data.get("word_count", len(text.split()))

    # If we have segments, try to match topics to timestamps
    if segments and data.get("key_topics"):
        data["key_topics"] = _attach_timestamps_to_topics(
            data["key_topics"], segments
        )

    # Persist to DB
    existing = await db.execute(select(Summary).where(Summary.file_id == file_id))
    summary_obj = existing.scalar_one_or_none()

    if summary_obj:
        summary_obj.short_summary = data.get("short_summary")
        summary_obj.detailed_summary = data.get("detailed_summary")
        summary_obj.bullet_points = data.get("bullet_points", [])
        summary_obj.key_topics = data.get("key_topics", [])
        summary_obj.word_count = data.get("word_count")
    else:
        summary_obj = Summary(
            file_id=file_id,
            short_summary=data.get("short_summary"),
            detailed_summary=data.get("detailed_summary"),
            bullet_points=data.get("bullet_points", []),
            key_topics=data.get("key_topics", []),
            word_count=data.get("word_count"),
        )
        db.add(summary_obj)

    await db.commit()

    # Cache result
    await cache_set(cache_key, data)
    return data


def _attach_timestamps_to_topics(topics: list, segments: list) -> list:
    """
    Try to find the first occurrence of each topic keyword in segments
    and attach a timestamp.
    """
    for topic in topics:
        topic_name = topic.get("topic", "").lower()
        for seg in segments:
            seg_text = seg.get("text", "").lower()
            if any(word in seg_text for word in topic_name.split()[:3]):
                topic["start_time"] = seg.get("start")
                topic["end_time"] = seg.get("end")
                break
    return topics
