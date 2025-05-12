import pytest

@pytest.mark.asyncio
async def test_cookie_handling(session):
    # Set cookie
    await session.get("https://httpbin.org/cookies/set/sessioncookie/12345")
    # Verify persistence
    response = await session.get("https://httpbin.org/cookies")
    assert response.json()["cookies"] == {"sessioncookie": "12345"}

@pytest.mark.asyncio
async def test_custom_headers(session):
    response = await session.get(
        "https://httpbin.org/headers",
        headers={"X-Test-Header": "value"}
    )
    assert response.json()["headers"]["X-Test-Header"] == "value"

@pytest.mark.asyncio
async def test_tls_fingerprinting(session):
    response = await session.get("https://tls.peet.ws/api/all")
    data = response.json()
    assert "tls" in data
    assert "ja3_hash" in data["tls"]
    assert len(data["tls"]["ja3_hash"]) == 32  # MD5 hash length