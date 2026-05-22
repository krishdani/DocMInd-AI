"""
Pytest configuration and shared fixtures.
"""
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.db.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models.models import User, File, FileType, ProcessingStatus


# ── Use in-memory SQLite for tests ───────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provide a clean DB session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Provide an async test client with DB override."""
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the DB."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("TestPass1"),
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Return Authorization headers for the test user."""
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_file(db_session: AsyncSession, test_user: User) -> File:
    """Create a test PDF file record."""
    f = File(
        uuid="test-uuid-1234",
        original_name="test.pdf",
        stored_name="test-uuid-1234.pdf",
        file_type=FileType.PDF,
        mime_type="application/pdf",
        size_bytes=12345,
        status=ProcessingStatus.COMPLETED,
        owner_id=test_user.id,
    )
    db_session.add(f)
    await db_session.commit()
    await db_session.refresh(f)
    return f
