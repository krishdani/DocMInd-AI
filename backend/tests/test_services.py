"""Tests for services: security, PDF chunking, media processing."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from app.services.pdf_service import chunk_text
from app.services.media_service import build_timed_chunks


# ── Security Tests ────────────────────────────────────────────────────────────

class TestSecurity:
    def test_hash_and_verify_password(self):
        plain = "SecurePass123"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("CorrectPass1")
        assert not verify_password("WrongPass1", hashed)

    def test_create_and_decode_access_token(self):
        token = create_access_token({"sub": "42"})
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        token = create_refresh_token({"sub": "42"})
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_invalid_token_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token("totally.invalid.token")
        assert exc_info.value.status_code == 401


# ── PDF Chunking Tests ────────────────────────────────────────────────────────

class TestPDFChunking:
    def test_chunk_short_text(self):
        text = "This is a short document."
        chunks = chunk_text(text)
        assert len(chunks) >= 1
        assert chunks[0][0] == text

    def test_chunk_long_text(self):
        # Generate text longer than CHUNK_SIZE
        text = ("This is sentence number X. " * 100)
        chunks = chunk_text(text)
        assert len(chunks) > 1

    def test_chunk_content_preserved(self):
        text = "Alpha beta gamma. " * 200
        chunks = chunk_text(text)
        combined = " ".join(c[0] for c in chunks)
        # All original words should appear somewhere in chunks
        assert "Alpha" in combined
        assert "gamma" in combined


# ── Media Timed Chunk Tests ───────────────────────────────────────────────────

class TestTimedChunks:
    SAMPLE_SEGMENTS = [
        {"text": "Hello world this is segment one.", "start": 0.0, "end": 3.5},
        {"text": "Segment two continues here.", "start": 3.5, "end": 6.0},
        {"text": "Segment three is more content.", "start": 6.0, "end": 9.5},
    ]

    def test_builds_at_least_one_chunk(self):
        chunks = build_timed_chunks(self.SAMPLE_SEGMENTS)
        assert len(chunks) >= 1

    def test_chunk_has_required_keys(self):
        chunks = build_timed_chunks(self.SAMPLE_SEGMENTS)
        for chunk in chunks:
            assert "text" in chunk
            assert "start_time" in chunk
            assert "end_time" in chunk

    def test_timestamps_are_numeric(self):
        chunks = build_timed_chunks(self.SAMPLE_SEGMENTS)
        for chunk in chunks:
            assert isinstance(chunk["start_time"], float)
            assert isinstance(chunk["end_time"], float)

    def test_empty_segments_returns_empty(self):
        chunks = build_timed_chunks([])
        assert chunks == []

    def test_skips_empty_text_segments(self):
        segments = [
            {"text": "", "start": 0.0, "end": 1.0},
            {"text": "Real content here.", "start": 1.0, "end": 2.0},
        ]
        chunks = build_timed_chunks(segments)
        assert all(c["text"].strip() for c in chunks)
