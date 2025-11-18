import pytest

from conftest import TEST_BASE_URL


@pytest.mark.asyncio
async def test_health_check(async_client):
    """
    Test the health check endpoint.
    """
    response = await async_client.get(
        f"{TEST_BASE_URL}/api/health", follow_redirects=True
    )
    assert response.status_code == 200
    assert response.json() == {"status": "I'm alive"}


@pytest.mark.asyncio
async def test_health_check_trailingslash(async_client):
    """
    Test the health check endpoint with trailing slash.
    """
    response = await async_client.get(f"{TEST_BASE_URL}/api/health/")
    assert 200 == response.status_code
    assert {"status": "I'm alive"} == response.json()
