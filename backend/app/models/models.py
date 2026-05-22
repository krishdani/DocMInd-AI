"""
SQLAlchemy ORM Models for all database tables.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, JSON, Enum as SAEnum, BigInteger
)
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class FileType(str, enum.Enum):
    PDF = "pdf"
    AUDIO = "audio"
    VIDEO = "video"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── User ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200))
    role = Column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")


# ─── File ────────────────────────────────────────────────────────────────────

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    original_name = Column(String(500), nullable=False)
    stored_name = Column(String(500), nullable=False)
    file_type = Column(SAEnum(FileType), nullable=False)
    mime_type = Column(String(100))
    size_bytes = Column(BigInteger, nullable=False)
    duration_seconds = Column(Float)  # for audio/video
    status = Column(SAEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    error_message = Column(Text)
    faiss_index_path = Column(String(500))
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    owner = relationship("User", back_populates="files")
    transcript = relationship("Transcript", back_populates="file", uselist=False, cascade="all, delete-orphan")
    summary = relationship("Summary", back_populates="file", uselist=False, cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="file", cascade="all, delete-orphan")


# ─── Transcript ──────────────────────────────────────────────────────────────

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_text = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    segments = Column(JSON)  # list of {start, end, text} dicts
    created_at = Column(DateTime(timezone=True), default=utcnow)

    file = relationship("File", back_populates="transcript")


# ─── Document Chunk (for FAISS) ───────────────────────────────────────────────

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)
    # For audio/video: timestamp references
    start_time = Column(Float)
    end_time = Column(Float)
    token_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    file = relationship("File", back_populates="chunks")


# ─── Summary ─────────────────────────────────────────────────────────────────

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), unique=True, nullable=False)
    short_summary = Column(Text)
    detailed_summary = Column(Text)
    bullet_points = Column(JSON)  # list of strings
    key_topics = Column(JSON)    # list of {topic, timestamps?, confidence}
    word_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    file = relationship("File", back_populates="summary")


# ─── Chat ────────────────────────────────────────────────────────────────────

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500))
    file_ids = Column(JSON, default=list)  # list of file IDs used in context
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="chats")
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    sources = Column(JSON)  # list of {file_id, chunk_index, score, snippet}
    tokens_used = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    chat = relationship("Chat", back_populates="messages")


# ─── Activity Log ─────────────────────────────────────────────────────────────

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    extra_data = Column(JSON)
    ip_address = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="activity_logs")
