from http.client import HTTPMessage, HTTPResponse
from http.cookiejar import Cookie, CookieJar
from typing import Optional, Union
from urllib.parse import urlparse
from urllib.request import Request

from nocasedict import NocaseDict


class MockRequest(Request):
    """
    Minimal request-like object to interface with `CookieJar.extract_cookies`.

    This class constructs a minimal request interface compatible with
    `http.cookiejar.CookieJar.extract_cookies()` by converting TLS client inputs
    into the format expected by the standard library's cookie handling. It avoids
    reimplementing cookie parsing logic by leveraging Python's built-in cookiejar
    implementation.

    :param request_url: Full URL for the request (used for domain/path validation)
    :param request_headers: NocaseDict of request headers (for Host header validation)
    """

    def __init__(self, request_url: str, request_headers: NocaseDict, method: str):
        """
        Initialize a mock request with URL and headers.

        Creates a minimal request object that implements only the necessary interface
        for cookie extraction from responses. The object structure follows what
        `http.cookiejar.CookieJar` expects when processing Set-Cookie headers.
        """
        headers_dict = dict(request_headers.items())
        super().__init__(request_url, headers=headers_dict, unverifiable=True, method=method)
        self.headers = request_headers
        parsed_url = urlparse(request_url)
        self.type = parsed_url.scheme
        self.host = parsed_url.netloc
        self.path = parsed_url.path


class MockResponse(HTTPResponse):
    """
    Minimal response-like object to interface with `CookieJar.extract_cookies`.

    Wraps TLS client response headers into an HTTPResponse-compatible format
    required by `http.cookiejar.CookieJar.extract_cookies()`. This ensures we
    can use Python's standard cookie parsing without reimplementing header
    processing or cookie validation logic.

    :param headers: NocaseDict of raw response headers containing Set-Cookie fields
    """

    # noinspection PyMissingConstructor
    def __init__(self, headers: NocaseDict):
        """
        Initialize response with headers for cookie processing.

        Converts TLS client response headers into an HTTPMessage format that
        matches what `http.cookiejar.CookieJar` expects during cookie extraction.
        This avoids reimplementing cookie header parsing and domain/path validation.
        """
        # noinspection PyMissingConstructor
        self.headers = HTTPMessage()
        for name, values in headers.items():
            for value in values:
                self.headers.add_header(name.lower(), value)

    def close(self, *args, **kwargs):
        return

    def flush(self, *args, **kwargs):
        return

def create_cookie_from_dict(cookie: dict):
    return Cookie(
        version=None,
        name=cookie["name"],
        value=cookie["value"],
        port=None,
        port_specified=False,
        domain=cookie["domain"],
        domain_specified=False,
        domain_initial_dot=False,
        path=cookie.get("path", "/"),
        path_specified=cookie.get("path") is not None,
        secure=cookie["secure"],
        expires=cookie["expires"],
        discard=cookie.get("discard", True),
        comment=None,
        comment_url=None,
        rest={'httpOnly': cookie.get("httpOnly"), "maxAge": cookie.get("maxAge")},
        rfc2109=False
    )

def create_cookie(
        name: str,
        value: str,
        *,
        domain: str = '',
        path: str = '/',
        secure: bool = False,
        expires: Optional[int] = None,
        discard: bool = True,
        httponly: bool = False,
        comment: Optional[str] = None,
        comment_url: Optional[str] = None
) -> Cookie:
    """
    Create a Cookie object with basic attributes for TLS client sessions.

    :param name: Cookie name (required)
    :param value: Cookie value (required)
    :param domain: Cookie domain (default: '')
    :param path: Cookie path (default: '/')
    :param secure: Whether cookie requires HTTPS (default: False)
    :param expires: Expiration time in seconds since epoch (default: None)
    :param discard: Whether to discard session cookie (default: True)
    :param httponly: Whether cookie is HTTP-only (default: False)
    :param comment: Cookie comment metadata (default: None)
    :param comment_url: Cookie comment URL (default: None)
    :return: Constructed Cookie object with specified attributes
    """
    return Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=domain,
        domain_specified=False,
        domain_initial_dot=False,
        path=path,
        path_specified=bool(path),
        secure=secure,
        expires=expires,
        discard=discard,
        comment=comment,
        comment_url=comment_url,
        rest={'HttpOnly': None} if httponly else {},
        rfc2109=False
    )


def cookiejar_from_dict(cookie_dict: dict) -> CookieJar:
    """
    Create CookieJar from dictionary of cookie name-value pairs.

    Converts a simple dictionary mapping cookie names to values into a fully-featured
    CookieJar object. This is useful for initializing cookie storage from simple cookie
    specifications.

    :param cookie_dict: Dictionary mapping cookie names to values. If empty, returns empty jar.
    :return: CookieJar containing cookies created from the dictionary entries
    """
    jar = CookieJar()
    if cookie_dict:
        for name, value in cookie_dict.items():
            cookie = create_cookie(name, value)
            jar.set_cookie(cookie)
    return jar


def merge_cookies(target_jar: CookieJar, source: Union[dict, CookieJar]) -> CookieJar:
    """
    Merge cookies from source into target jar for session persistence.

    Combines cookies from either a dictionary or another CookieJar into the target jar.
    This maintains cookie state across multiple requests in a TLS client session.

    :param target_jar: Destination CookieJar to update with new cookies
    :param source: Source cookies to merge, either as a dictionary or CookieJar
    :return: Updated CookieJar containing both original and new cookies
    """
    if isinstance(source, dict):
        source = cookiejar_from_dict(source)
    for cookie in source:
        target_jar.set_cookie(cookie)
    return target_jar


def extract_cookies_to_jar(
        request_url: str,
        request_headers: NocaseDict,
        cookie_jar: CookieJar,
        response_headers: NocaseDict,
        request_method: Optional[str] = None
) -> CookieJar:
    """
    Extract cookies from response and add to jar for persistent session management.

    Processes Set-Cookie headers from TLS client responses and stores them in the
    provided cookie jar. This maintains cookie state across requests in a session.

    :param request_url: Original request URL for cookie domain/path validation
    :param request_headers: Headers sent with the request (for Host header)
    :param cookie_jar: Target CookieJar to store extracted cookies
    :param response_headers: Response headers containing Set-Cookie fields
    :return: CookieJar with newly extracted cookies added to existing entries
    """
    req = MockRequest(request_url, request_headers, request_method)
    res = MockResponse(response_headers)
    cookie_jar.extract_cookies(res, req)
    return cookie_jar
