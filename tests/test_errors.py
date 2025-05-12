import pytest
from async_tls_client.exceptions import TLSClientException

@pytest.mark.asyncio
async def test_invalid_url(session):
    with pytest.raises(TLSClientException):
        await session.get("invalid://invalid-url")

@pytest.mark.asyncio
async def test_timeout(session):
    with pytest.raises(TLSClientException):
        await session.get(
            "https://httpbin.org/delay/5",
            timeout_seconds=1
        )

@pytest.mark.asyncio
async def test_nonexistent_domain(session):
    with pytest.raises(TLSClientException):
        await session.get("https://nonexistent-domain-12345.com")