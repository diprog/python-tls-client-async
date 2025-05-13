from http.cookiejar import CookieJar

import pytest
from nocasedict import NocaseDict

from async_tls_client.cookies import cookiejar_from_dict, extract_cookies_to_jar, merge_cookies


@pytest.mark.asyncio
async def test_basic_cookie_persistence(session):
    """Test cookie persistence across requests."""
    # Set a cookie
    await session.get("https://httpbin.org/cookies/set?test_cookie=12345")
    # Verify persistence
    response = await session.get("https://httpbin.org/cookies")
    assert response.json()["cookies"]["test_cookie"] == "12345"


@pytest.mark.asyncio
async def test_multiple_cookies_in_one_response(session):
    """Test multiple cookies set in one response."""
    # Set multiple cookies
    await session.get("https://httpbin.org/cookies/set?cookie1=value1&cookie2=value2")
    # Verify both cookies are stored
    response = await session.get("https://httpbin.org/cookies")
    cookies = response.json()["cookies"]
    assert "cookie1" in cookies and cookies["cookie1"] == "value1"
    assert "cookie2" in cookies and cookies["cookie2"] == "value2"


@pytest.mark.asyncio
async def test_cookie_expiration(session):
    """Test that expired cookies are not sent."""
    # Set a cookie with an expired max-age
    await session.get("https://httpbin.org/cookies/set?expired_cookie=deadbeef ;max-age=-1")
    # Ensure the cookie is not present
    response = await session.get("https://httpbin.org/cookies")
    assert "expired_cookie" not in response.json()["cookies"]


# Golang response object only returns name=value pairs
@pytest.mark.asyncio
async def test_cookie_domain_path_attributes(session):
    """Test cookies with domain/path attributes."""
    # Set a cookie for a specific path
    await session.get(
        "https://google.com"
    )
    await session.get(
        "https://httpbin.org/response-headers",
        params={"Set-Cookie": "path_cookie=value; Path=/get"}
    )
    # Should be sent to /get
    response = await session.get("https://httpbin.org/get")
    assert "path_cookie" in response.json()["headers"].get("Cookie", "")
    # Should not be sent to /post
    response = await session.post("https://httpbin.org/post")
    assert "path_cookie" not in response.json()["headers"].get("Cookie", "")


@pytest.mark.asyncio
async def test_secure_http_only_flags(session):
    """Test Secure and httpOnly flags."""
    # Set a Secure and httpOnly cookie
    await session.get(
        "https://httpbin.org/response-headers",
        params={"Set-Cookie": "secure_cookie=value; Secure; HttpOnly; Path=/"}
    )
    # Verify cookie is stored with correct attributes
    for cookie in session.cookies:
        if cookie.name == "secure_cookie":
            assert cookie.secure
            assert "httpOnly" in cookie._rest
            break
    else:
        pytest.fail("secure_cookie not found in session")


@pytest.mark.asyncio
async def test_merge_cookies(session):
    """Test merging session and request cookies."""
    # Initial session cookies
    session.cookies = cookiejar_from_dict({"session_cookie": "123"})
    # Merge with request cookies
    merged = merge_cookies(session.cookies, {"session_cookie": "456", "new_cookie": "789"})
    merged_dict = {c.name: c.value for c in merged}
    assert merged_dict == {"session_cookie": "456", "new_cookie": "789"}


@pytest.mark.asyncio
async def test_multiple_set_cookie_headers(session):
    """Test multiple Set-Cookie headers in a single response."""
    # Set multiple cookies via multiple Set-Cookie headers
    response = await session.get("https://httpbin.org/response-headers", params={
        "Set-Cookie": [
            "cookie1=value1",
            "cookie2=value2",
            "cookie3=value3"
        ]
    })
    # Extract cookies manually from headers
    cookie_jar = CookieJar()
    extract_cookies_to_jar(
        request_url="https://httpbin.org/response-headers",
        request_headers=response.headers,
        cookie_jar=cookie_jar,
        response_headers=response.headers
    )
    cookie_names = [c.name for c in cookie_jar]
    assert set(cookie_names) == {"cookie1", "cookie2", "cookie3"}


@pytest.mark.asyncio
async def test_cookie_persistence_after_redirect(session):
    """Test cookies set during redirects are preserved."""
    # 302 redirect to /get with a Set-Cookie
    response = await session.get("https://httpbin.org/redirect-to?url=https%3A%2F%2Fhttpbin.org%2Fget",
                                 allow_redirects=True)
    # Set a cookie during the redirect
    await session.get("https://httpbin.org/cookies/set?redirect_cookie=value")
    # Verify cookie is stored
    response = await session.get("https://httpbin.org/cookies")
    assert "redirect_cookie" in response.json()["cookies"]


@pytest.mark.asyncio
async def test_cookiejar_merging_logic(session):
    # Merge with dict
    jar1 = cookiejar_from_dict({"a": "1"})
    jar1_copy = cookiejar_from_dict({})
    for c in jar1:
        jar1_copy.set_cookie(c)
    merged = merge_cookies(jar1_copy, {"a": "2", "b": "3"})
    assert {c.name: c.value for c in merged} == {"a": "2", "b": "3"}

    # Merge with CookieJar
    jar1_copy2 = cookiejar_from_dict({})
    for c in jar1:
        jar1_copy2.set_cookie(c)
    jar2 = cookiejar_from_dict({"c": "4", "d": "5"})
    merged = merge_cookies(jar1_copy2, jar2)
    assert {c.name: c.value for c in merged} == {"a": "1", "c": "4", "d": "5"}


@pytest.mark.asyncio
async def test_extract_cookies_to_jar(session):
    """Test manual cookie extraction from headers into CookieJar."""
    mock_headers = {
        "Set-Cookie": [
            "test1=value1; Path=/",
            "test2=value2; Domain=httpbin.org; Secure",
        ]
    }
    cookie_jar = CookieJar()
    extract_cookies_to_jar(
        request_url="https://httpbin.org/get",
        request_headers=session.headers,
        cookie_jar=cookie_jar,
        response_headers=NocaseDict(mock_headers)
    )
    cookie_names = [c.name for c in cookie_jar]
    assert set(cookie_names) == {"test1", "test2"}

@pytest.mark.asyncio
async def test_get_add_cookies(session):
    await session.add_cookies({"bruh": "moment"}, "https://example.com")
    await session.get_cookies("https://example.com")