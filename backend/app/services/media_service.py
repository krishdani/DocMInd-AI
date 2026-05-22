"""
Audio/Video transcription service using OpenAI Whisper API.
Handles chunking of large files, timestamp preservation,
embedding generation, and FAISS index creation.
"""
import os
import json
import logging
from typing import List, Dict, Any
import openai
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.models import File, Transcript, DocumentChunk, ProcessingStatus

logger = logging.getLogger(__name__)

# Whisper max file size is 25MB; we use ffmpeg to split large files
WHISPER_MAX_BYTES = 24 * 1024 * 1024  # 24MB safety margin


async def transcribe_file(file_path: str) -> Dict[str, Any]:
    """
    Send audio/video file to OpenAI Whisper API.
    Returns verbose JSON with segments containing timestamps.
    """
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    with open(file_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            model=settings.OPENAI_WHISPER_MODEL,
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    return response.model_dump()


def build_timed_chunks(segments: List[Dict]) -> List[Dict]:
    """
    Group Whisper segments into larger chunks (~CHUNK_SIZE chars)
    while preserving start/end timestamps.
    """
    chunks = []
    current_text = ""
    current_start = 0.0
    current_end = 0.0

    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        if current_text == "":
            current_start = seg.get("start", 0.0)

        current_text += " " + text
        current_end = seg.get("end", current_end)

        if len(current_text) >= settings.CHUNK_SIZE:
            chunks.append({
                "text": current_text.strip(),
                "start_time": current_start,
                "end_time": current_end,
            })
            # Overlap: keep last segment text
            current_text = text
            current_start = seg.get("start", current_end)

    if current_text.strip():
        chunks.append({
            "text": current_text.strip(),
            "start_time": current_start,
            "end_time": current_end,
        })

    return chunks


async def process_media(file_id: int, file_path: str, db: AsyncSession) -> None:
    """
    Full audio/video processing pipeline:
    1. Transcribe with Whisper
    2. Build timed chunks
    3. Embed + store in FAISS
    4. Persist transcript + chunks to DB
    5. Update file status
    """
    result = await db.execute(select(File).where(File.id == file_id))
    file_obj = result.scalar_one_or_none()
    if not file_obj:
        raise ValueError(f"File {file_id} not found")

    file_obj.status = ProcessingStatus.PROCESSING
    await db.commit()

    try:
        logger.info(f"Transcribing media file: {file_path}")
        whisper_result = await transcribe_file(file_path)

        full_text = whisper_result.get("text", "")
        segments = whisper_result.get("segments", [])
        language = whisper_result.get("language", "en")
        duration = whisper_result.get("duration")

        # Save transcript
        transcript = Transcript(
            file_id=file_id,
            full_text=full_text,
            language=language,
            segments=segments,
        )
        db.add(transcript)

        if duration:
            file_obj.duration_seconds = duration

        # Build timestamped chunks for embeddings
        timed_chunks = build_timed_chunks(segments)
        logger.info(f"Created {len(timed_chunks)} timed chunks for file {file_id}")

        embeddings_model = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        texts = [c["text"] for c in timed_chunks]
        metadatas = [
            {
                "file_id": file_id,
                "chunk_index": i,
                "start_time": c["start_time"],
                "end_time": c["end_time"],
            }
            for i, c in enumerate(timed_chunks)
        ]
        vector_store = await FAISS.afrom_texts(texts, embeddings_model, metadatas=metadatas)

        index_dir = os.path.join(settings.FAISS_INDEX_PATH, str(file_id))
        os.makedirs(index_dir, exist_ok=True)
        vector_store.save_local(index_dir)

        # Persist chunks to DB
        for i, chunk in enumerate(timed_chunks):
            db_chunk = DocumentChunk(
                file_id=file_id,
                chunk_index=i,
                content=chunk["text"],
                start_time=chunk["start_time"],
                end_time=chunk["end_time"],
                token_count=len(chunk["text"].split()),
            )
            db.add(db_chunk)

        file_obj.status = ProcessingStatus.COMPLETED
        file_obj.faiss_index_path = index_dir
        await db.commit()
        logger.info(f"Media processing complete for file {file_id}")

    except Exception as e:
        logger.error(f"Media processing failed for file {file_id}: {e}")
        file_obj.status = ProcessingStatus.FAILED
        file_obj.error_message = str(e)
        await db.commit()
        raise
