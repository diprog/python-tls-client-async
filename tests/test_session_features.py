from pprint import pprint

import pytest

@pytest.mark.asyncio
async def test_custom_headers(session):
    response = await session.get(
        "https://httpbin.org/headers",
        headers={"X-Test-Header": "value"}
    )
    assert response.json()["headers"]["X-Test-Header"] == "value"

# ja3-strings w
# @pytest.mark.asyncio
# async def test_tls_fingerprinting(session):
#     response = await session.get("https://tls.browserleaks.com")
#     data = response.json()
#     pprint(data)