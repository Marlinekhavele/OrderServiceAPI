import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database.base import Base
from app.deps import get_db_session
from app.main import app
from app.settings import Settings

TEST_BASE_URL = "http://test"


def get_test_settings() -> Settings:
    """
    Get settings configured for testing.
    """
    return Settings(
        ENV_NAME="test",
        DB_NAME="order_service_test",
        DB_PORT=5433,
    )


# Initialize test settings
test_settings = get_test_settings()


# Event Loop Fixtures
@pytest.fixture(scope="session")
def event_loop_policy():
    """
    Set event loop policy for the entire test session.
    """
    return asyncio.get_event_loop_policy()


@pytest.fixture(scope="function")
def event_loop(event_loop_policy):
    """
    Create a new event loop for each test function.
    """
    loop = event_loop_policy.new_event_loop()
    yield loop
    loop.close()


# Database Fixtures
@pytest_asyncio.fixture(scope="function")
async def db_engine(event_loop):
    """
    Create a test database engine using test settings.
    Drops and recreates all tables for test isolation.
    """
    engine = create_async_engine(
        test_settings.DB_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Setup: Create fresh tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with proper isolation."""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


# HTTP Client Fixtures
@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client with test database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=TEST_BASE_URL) as client:
        yield client

    app.dependency_overrides.clear()


# Settings Fixture


@pytest.fixture
def test_settings_fixture():
    """
    Provide test settings to tests that need it.
    """
    return test_settings


# Sample Data Fixtures


@pytest.fixture
def sample_order_data():
    """
    Sample order data for testing.
    """
    return {
        "instrument": "DE000A0Q4RZ3",
        "type": "limit",
        "quantity": 5,
        "side": "sell",
        "limit_price": 125.50,
    }
