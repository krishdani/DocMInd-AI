"""
PDF processing service.
Extracts text, splits into chunks, generates OpenAI embeddings,
stores in FAISS, and persists chunk metadata to PostgreSQL.
"""
import os
import logging
from typing import List, Tuple
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.models import File, DocumentChunk, ProcessingStatus

logger = logging.getLogger(__name__)


def extract_pdf_text(file_path: str) -> str:
    """Extract full text from a PDF using pdfplumber."""
    pages_text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
    return "\n\n".join(pages_text)


def chunk_text(text: str) -> List[Tuple[str, int, int]]:
    """
    Split text into overlapping chunks.
    Returns list of (chunk_text, start_char, end_char).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.create_documents([text])
    results = []
    pos = 0
    for doc in chunks:
        start = text.find(doc.page_content, pos)
        end = start + len(doc.page_content)
        results.append((doc.page_content, start, end))
        pos = max(0, end - settings.CHUNK_OVERLAP)
    return results


async def process_pdf(file_id: int, file_path: str, db: AsyncSession) -> None:
    """
    Full PDF processing pipeline:
    1. Extract text
    2. Chunk it
    3. Embed + store in FAISS
    4. Save chunks to DB
    5. Update file status
    """
    # Mark as processing
    result = await db.execute(select(File).where(File.id == file_id))
    file_obj = result.scalar_one_or_none()
    if not file_obj:
        raise ValueError(f"File {file_id} not found")

    file_obj.status = ProcessingStatus.PROCESSING
    await db.commit()

    try:
        logger.info(f"Extracting text from PDF: {file_path}")
        text = extract_pdf_text(file_path)

        if not text.strip():
            raise ValueError("PDF contains no extractable text")

        chunks = chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks for file {file_id}")

        # Build FAISS index from chunks
        embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        texts = [c[0] for c in chunks]
        metadatas = [
            {"file_id": file_id, "chunk_index": i, "start_char": c[1], "end_char": c[2]}
            for i, c in enumerate(chunks)
        ]
        vector_store = await FAISS.afrom_texts(texts, embeddings, metadatas=metadatas)

        # Persist FAISS index to disk
        index_dir = os.path.join(settings.FAISS_INDEX_PATH, str(file_id))
        os.makedirs(index_dir, exist_ok=True)
        vector_store.save_local(index_dir)

        # Save chunks to DB
        for i, (chunk_text_content, start_char, end_char) in enumerate(chunks):
            chunk = DocumentChunk(
                file_id=file_id,
                chunk_index=i,
                content=chunk_text_content,
                start_char=start_char,
                end_char=end_char,
                token_count=len(chunk_text_content.split()),
            )
            db.add(chunk)

        file_obj.status = ProcessingStatus.COMPLETED
        file_obj.faiss_index_path = index_dir
        await db.commit()
        logger.info(f"PDF processing complete for file {file_id}")

    except Exception as e:
        logger.error(f"PDF processing failed for file {file_id}: {e}")
        file_obj.status = ProcessingStatus.FAILED
        file_obj.error_message = str(e)
        await db.commit()
        raise
