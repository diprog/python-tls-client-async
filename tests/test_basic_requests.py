import pytest

@pytest.mark.asyncio
async def test_get_request(session):
    response = await session.get("https://httpbin.org/get")
    assert response.status_code == 200
    assert response.url == "https://httpbin.org/get"
    assert "headers" in response.json()

@pytest.mark.asyncio
async def test_post_with_data(session):
    response = await session.post(
        "https://httpbin.org/post",
        data={"key": "value"}
    )
    assert response.status_code == 200
    assert response.json()["form"] == {"key": "value"}

@pytest.mark.asyncio
async def test_post_with_json(session):
    response = await session.post(
        "https://httpbin.org/post",
        json={"key": "value"}
    )
    assert response.status_code == 200
    assert response.json()["json"] == {"key": "value"}