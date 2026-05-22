"""
ASGI entrypoint for uvicorn.
Run with: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""
from app.main import app  # noqa: F401
