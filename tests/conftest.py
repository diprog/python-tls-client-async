import pytest
from async_tls_client import AsyncSession

@pytest.fixture
async def session():
    async with AsyncSession(client_identifier="chrome120") as sess:
        yield sess