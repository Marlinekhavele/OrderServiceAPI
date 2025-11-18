import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

TEST_BASE_URL = "http://test"


@pytest.fixture
async def async_client():
    """
    Fixture to provide an AsyncClient for testing FastAPI app.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=TEST_BASE_URL) as ac:
        yield ac


@pytest.fixture(scope="function")
def event_loop():
    """
    Create an instance of the default event loop for each test case.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
