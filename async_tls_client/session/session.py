import uuid
from http.cookiejar import CookieJar
from typing import Optional, Union, Unpack

from nocasedict import NocaseDict

from async_tls_client.cffi import (
    add_cookies_to_session, destroy_session, get_cookies_from_session, request
)
from async_tls_client.cookies import (
    cookiejar_from_dict, create_cookie_from_dict,
    merge_cookies
)
from async_tls_client.response import Response, build_response
from async_tls_client.session.request_payload_builder import build_payload
from async_tls_client.types import (
    ClientIdentifiers, Curves, DelegatedSignatureAlgorithms, H2Settings,
    RequestOptions, SignatureAlgorithms,
    TLSVersions
)


class AsyncSession:
    """
    Asynchronous session to perform HTTP requests with special TLS settings and session management.

    This class provides an asynchronous session that uses a Go-based TLS client under the hood.
    It supports setting client identifiers, custom JA3 strings, HTTP/2 settings, certificate pinning,
    custom proxy usage, and more. Each session is tracked by a unique session ID, so destroying or closing
    the session frees its underlying resources.

    The session includes:
    - Standard HTTP settings (headers, proxies, cookies, etc.)
    - Advanced TLS settings (client identifiers, JA3, HTTP/2 h2_settings, supported signature algorithms, etc.)
    - HTTP/2 custom frames and priorities
    - Custom extension order and forced HTTP/1 usage if necessary
    - Debugging and panic catching (Go-based)

    Examples:
        Example usage::

            async with AsyncSession(client_identifier="chrome_120") as session:
                response = await session.get("https://example.com")
                print(response.status_code, response.text)

    """

    def __init__(
            self,
            client_identifier: ClientIdentifiers = "chrome_133",
            ja3_string: Optional[str] = None,
            h2_settings: Optional[dict[H2Settings, int]] = None,
            h2_settings_order: Optional[list[str]] = None,
            supported_signature_algorithms: Optional[list[SignatureAlgorithms]] = None,
            supported_delegated_credentials_algorithms: Optional[list[DelegatedSignatureAlgorithms]] = None,
            supported_versions: Optional[list[TLSVersions]] = None,
            key_share_curves: Optional[list[Curves]] = None,
            cert_compression_algos: list[str] = None,
            additional_decode: str = None,
            pseudo_header_order: Optional[list[str]] = None,
            connection_flow: Optional[int] = None,
            priority_frames: Optional[list] = None,
            header_order: Optional[list[str]] = None,
            header_priority: Optional[list[str]] = None,
            random_tls_extension_order: Optional[bool] = False,
            force_http1: Optional[bool] = False,
            catch_panics: Optional[bool] = False,
            debug: Optional[bool] = False,
            certificate_pinning: Optional[dict[str, list[str]]] = None,
    ) -> None:
        """
        Initializes the AsyncSession with various HTTP and TLS parameters.

        :param client_identifier: Identifies the client configuration to use.
            Possible values: "chrome_103", "firefox_102", "opera_89" etc.
            Default: "chrome_133"

        :param ja3_string: JA3 string specifying TLS fingerprint details including:
            - TLSVersion
            - Ciphers
            - Extensions
            - EllipticCurves
            - EllipticCurvePointFormats
            Example:

            .. code-block:: python

                "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"

        :param h2_settings: Dictionary representing HTTP/2 header frame settings.
            Possible keys:
            - HEADER_TABLE_SIZE
            - ENABLE_PUSH
            - MAX_CONCURRENT_STREAMS
            - INITIAL_WINDOW_SIZE
            - MAX_FRAME_SIZE
            - MAX_HEADER_LIST_SIZE
            Example:

            .. code-block:: python

                {
                    "HEADER_TABLE_SIZE": 65536,
                    "MAX_CONCURRENT_STREAMS": 1000,
                    "INITIAL_WINDOW_SIZE": 6291456,
                    "MAX_HEADER_LIST_SIZE": 262144
                }

        :param h2_settings_order: List specifying the order of HTTP/2 settings.
            Example:

            .. code-block:: python

                [
                    "HEADER_TABLE_SIZE",
                    "MAX_CONCURRENT_STREAMS",
                    "INITIAL_WINDOW_SIZE",
                    "MAX_HEADER_LIST_SIZE"
                ]

        :param supported_signature_algorithms: List of supported signature algorithms.
            Possible values:
            - PKCS1WithSHA256
            - PKCS1WithSHA384
            - PKCS1WithSHA512
            - PSSWithSHA256
            - PSSWithSHA384
            - PSSWithSHA512
            - ECDSAWithP256AndSHA256
            - ECDSAWithP384AndSHA384
            - ECDSAWithP521AndSHA512
            - PKCS1WithSHA1
            - ECDSAWithSHA1
            Example:

            .. code-block:: python

                [
                    "ECDSAWithP256AndSHA256",
                    "PSSWithSHA256",
                    "PKCS1WithSHA256",
                    "ECDSAWithP384AndSHA384",
                    "PSSWithSHA384",
                    "PKCS1WithSHA384",
                    "PSSWithSHA512",
                    "PKCS1WithSHA512",
                ]

        :param supported_delegated_credentials_algorithms: List of supported delegated credentials algorithms.
            Same possible values as supported_signature_algorithms.

        :param supported_versions: List of supported TLS versions.
            Possible values: "GREASE", "1.3", "1.2", "1.1", "1.0"
            Example:

            .. code-block:: python

                ["GREASE", "1.3", "1.2"]

        :param key_share_curves: List of key share curves.
            Possible values: "GREASE", "P256", "P384", "P521", "X25519", "P256Kyber768", "X25519Kyber512D",
            "X25519Kyber768", "X25519Kyber768Old", "X25519MLKEM768"
            Example:

            .. code-block:: python

                ["GREASE", "X25519"]

        :param cert_compression_algos: Certificate compression algorithms.
            Example: ["zlib", "brotli", "zstd"]

        :param additional_decode: Explicit response decoding algorithm.
            Examples: "gzip", "br", "deflate"

        :param pseudo_header_order: List specifying pseudo-header order.
            Possible values: ":authority", ":method", ":path", ":scheme"
            Example:

            .. code-block:: python

                [
                    ":method",
                    ":authority",
                    ":scheme",
                    ":path"
                ]

        :param connection_flow: Connection flow/window size increment.
            Example: 15663105

        :param priority_frames: List specifying HTTP/2 priority frames.
            Example:

            .. code-block:: python

                [
                    {
                        "streamID": 3,
                        "priorityParam": {
                            "weight": 201,
                            "streamDep": 0,
                            "exclusive": false
                        }
                    },
                    {
                        "streamID": 5,
                        "priorityParam": {
                            "weight": 101,
                            "streamDep": false,
                            "exclusive": 0
                        }
                    }
                ]

        :param header_order: List specifying header order.
            Example:

            .. code-block:: python

                ["key1", "key2"]

        :param header_priority: Dictionary specifying header priority.
            Example:

            .. code-block:: python

                {
                    "streamDep": 1,
                    "exclusive": true,
                    "weight": 1
                }

        :param random_tls_extension_order: Whether to randomize TLS extension order.
            Default: False

        :param force_http1: Whether to force HTTP/1 usage.
            Default: False

        :param catch_panics: Whether to catch Go panics.
            Default: False

        :param debug: Enable debug mode.
            Default: False

        :param certificate_pinning: Dictionary for certificate pinning.
            Example:

            .. code-block:: python

                {
                    "example.com": [
                        "sha256/AAAAAAAAAAAAAAAAAAAAAA=="
                    ]
                }
        """
        self._session_id = str(uuid.uuid4())
        # Standard Settings
        self.headers = NocaseDict()  # Defaults to o-http-client/2.0
        self.proxies = {}
        self.params = {}
        self.cookies = cookiejar_from_dict({})
        self.timeout_seconds = 30
        self.certificate_pinning = certificate_pinning

        # Advanced Settings
        self.client_identifier = client_identifier
        self.ja3_string = ja3_string
        self.h2_settings = h2_settings
        self.h2_settings_order = h2_settings_order
        self.supported_signature_algorithms = supported_signature_algorithms
        self.supported_delegated_credentials_algorithms = supported_delegated_credentials_algorithms
        self.supported_versions = supported_versions
        self.key_share_curves = key_share_curves
        self.cert_compression_algos = cert_compression_algos
        self.additional_decode = additional_decode
        self.pseudo_header_order = pseudo_header_order
        self.connection_flow = connection_flow
        self.priority_frames = priority_frames
        self.header_order = header_order
        self.header_priority = header_priority
        self.random_tls_extension_order = random_tls_extension_order
        self.force_http1 = force_http1
        self.catch_panics = catch_panics
        self.debug = debug

    async def __aenter__(self):
        """
        Enters the session in an asynchronous context manager.

        :return: Current session instance
        """
        return self

    async def __aexit__(self, *args):
        """
        Exits the session in an asynchronous context manager.
        Frees resources by calling the `close()` method asynchronously.
        """
        await self.close()

    async def close(self) -> str:
        """
        Closes the session and frees allocated Go memory resources.

        :return: JSON response string from the destroy session call
        """
        return await destroy_session(self._session_id)

    async def get_cookies(self, url: str) -> Optional[list[dict]]:
        return (await get_cookies_from_session(self._session_id, url))["cookies"]

    async def add_cookies(self, cookies: Union[dict[str, str], list[dict]], url: str):
        if isinstance(cookies, dict):
            cookies = [{"name": name, "value": value} for name, value in cookies.items()]

        await add_cookies_to_session(self._session_id, cookies, url)

    async def execute_request(
            self,
            method: str,
            url: str,
            **kwargs: Unpack[RequestOptions]
    ) -> Response:
        """Execute an HTTP request with configured options.

        :param method: HTTP verb to use (GET/POST/etc.)
        :param url: Target URL for request
        :param kwargs: Additional request configuration options
        :return: Response object with request results
        :raises TLSClientException: For request errors
        """
        # Extract parameters from kwargs
        params = kwargs.get('params')
        data = kwargs.get('data')
        headers = kwargs.get('headers')
        cookies = kwargs.get('cookies')
        json_body = kwargs.get('json')
        allow_redirects = kwargs.get('allow_redirects', False)
        insecure_skip_verify = kwargs.get('insecure_skip_verify', False)
        timeout_seconds = kwargs.get('timeout_seconds')
        proxy = kwargs.get('proxy')

        # Rest of the method remains unchanged
        payload = build_payload(
            session=self,
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            cookies=cookies,
            json=json_body,
            allow_redirects=allow_redirects,
            insecure_skip_verify=insecure_skip_verify,
            timeout_seconds=timeout_seconds,
            proxy=proxy
        )

        response_object = await request(payload)

        session_cookies = await self.get_cookies(url)
        response_cookies: list[dict] = []
        if session_cookies:
            for cookie in session_cookies:
                if cookie["name"] in response_object["cookies"].keys():
                    response_cookies.append(cookie)

        response_cookie_jar = CookieJar()
        for cookie in response_cookies:
            response_cookie_jar.set_cookie(create_cookie_from_dict(cookie))

        merge_cookies(self.cookies, response_cookie_jar)
        return build_response(response_object, response_cookie_jar)

    async def get(self, url: str, **kwargs: Unpack[RequestOptions]) -> Response:
        """Send GET request to specified URL.

        :param url: Target URL for request
        :param kwargs: Additional request options
        """
        return await self.execute_request("GET", url, **kwargs)

    async def options(self, url: str, **kwargs: Unpack[RequestOptions]) -> Response:
        """Send OPTIONS request to specified URL.

        :param url: Target URL for request
        :param kwargs: Additional request options including data/json
        """
        return await self.execute_request("OPTIONS", url, **kwargs)

    async def head(self, url: str, **kwargs: Unpack[RequestOptions]) -> Response:
        """Send HEAD request to specified URL.

        :param url: Target URL for request
        :param kwargs: Additional request options including data/json
        """
        return await self.execute_request("HEAD", url, **kwargs)

    async def post(self, url: str, **kwargs: Unpack[RequestOptions]) -> Response:
        """Send POST request to specified URL.

        :param url: Target URL for request
        :param kwargs: Additional request options including data/json
        """
        return await self.execute_request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Unpack[RequestOptions]) -> Response:
        """Send PUT request to specified URL.

        :param url: Target URL for request
        :param kwargs: Additional request options including data/json
        """
        return await self.execute_request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Unpack[RequestOptions]) -> Response:
        """Send PATCH request to specified URL.

        :param url: Target URL for request
        :param kwargs: Additional request options including data/json
        """
        return await self.execute_request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Unpack[RequestOptions]) -> Response:
        """Send DELETE request to specified URL.

        :param url: Target URL for request
        :param kwargs: Additional request options including data/json
        """
        return await self.execute_request("DELETE", url, **kwargs)
