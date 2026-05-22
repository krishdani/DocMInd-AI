"""Tests for file upload and management endpoints."""
import io
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_files_empty(client: AsyncClient, test_user, auth_headers):
    resp = await client.get("/api/files", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["files"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_files_with_data(client: AsyncClient, test_user, test_file, auth_headers):
    resp = await client.get("/api/files", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["files"][0]["original_name"] == "test.pdf"


@pytest.mark.asyncio
@patch("app.api.files._run_processing", new_callable=AsyncMock)
async def test_upload_pdf(mock_proc, client: AsyncClient, test_user, auth_headers, tmp_path):
    # Create a minimal PDF-like file content
    fake_pdf = b"%PDF-1.4 fake content for testing"
    resp = await client.post(
        "/api/files/upload",
        headers=auth_headers,
        files={"file": ("document.pdf", io.BytesIO(fake_pdf), "application/pdf")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["original_name"] == "document.pdf"
    assert data["file_type"] == "pdf"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_upload_unsupported_type(client: AsyncClient, test_user, auth_headers):
    resp = await client.post(
        "/api/files/upload",
        headers=auth_headers,
        files={"file": ("doc.docx", io.BytesIO(b"fake docx"), "application/msword")},
    )
    assert resp.status_code == 415


@pytest.mark.asyncio
async def test_get_file_detail(client: AsyncClient, test_user, test_file, auth_headers):
    resp = await client.get(f"/api/files/{test_file.id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == test_file.id


@pytest.mark.asyncio
async def test_get_file_not_found(client: AsyncClient, test_user, auth_headers):
    resp = await client.get("/api/files/99999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_file(client: AsyncClient, test_user, test_file, auth_headers):
    with patch("os.path.exists", return_value=False):
        resp = await client.delete(f"/api/files/{test_file.id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_files_require_auth(client: AsyncClient):
    resp = await client.get("/api/files")
    assert resp.status_code == 403
