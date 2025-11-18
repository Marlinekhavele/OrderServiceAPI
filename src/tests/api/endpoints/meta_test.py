import pytest

from conftest import TEST_BASE_URL


@pytest.mark.asyncio
async def test_endpoint_meta(async_client):
    """
    Test the meta endpoint.
    """
    response = await async_client.get(
        f"{TEST_BASE_URL}/api/meta/", follow_redirects=False
    )
    assert 200 == response.status_code
    assert {"app_version": "0.1.1"} == response.json()
