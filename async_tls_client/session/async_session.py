import asyncio
import base64
import ctypes
import urllib.parse
import uuid
from json import dumps, loads
from typing import Any, Optional, Union

from requests.structures import CaseInsensitiveDict

from async_tls_client.cffi import destroySession, freeMemory, request
from async_tls_client.cookies import cookiejar_from_dict, extract_cookies_to_jar, merge_cookies
from async_tls_client.exceptions import TLSClientException
from async_tls_client.response import Response, build_response
from async_tls_client.types import ClientIdentifiers, Curves, DelegatedSignatureAlgorithms, H2Settings, \
    SignatureAlgorithms, \
    TLSVersions


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
            cert_compression_algo: str = None,
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

        :param cert_compression_algo: Certificate compression algorithm.
            Examples: "zlib", "brotli", "zstd"

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
        self.headers = CaseInsensitiveDict()
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
        self.cert_compression_algo = cert_compression_algo
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
        destroy_session_payload = {
            "sessionId": self._session_id
        }

        destroy_session_response = await asyncio.to_thread(
            destroySession, dumps(destroy_session_payload).encode('utf-8')
        )
        destroy_session_response_bytes = ctypes.string_at(destroy_session_response)
        destroy_session_response_string = destroy_session_response_bytes.decode('utf-8')
        destroy_session_response_object = loads(destroy_session_response_string)

        await asyncio.to_thread(
            freeMemory, destroy_session_response_object['id'].encode('utf-8')
        )

        return destroy_session_response_string

    async def execute_request(
            self,
            method: str,
            url: str,
            params: Optional[dict] = None,
            data: Optional[Union[str, dict]] = None,
            headers: Optional[dict] = None,
            cookies: Optional[dict] = None,
            json: Optional[dict] = None,
            allow_redirects: Optional[bool] = False,
            insecure_skip_verify: Optional[bool] = False,
            timeout_seconds: Optional[int] = None,
            proxy: Optional[dict] = None
    ) -> Response:
        """
        Executes an HTTP request using the Go-based TLS client in a separate thread.

        :param method: HTTP method (GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD)
        :param url: Request URL
        :param params: Querystring parameters
        :param data: Request body (form data or raw bytes)
        :param headers: Additional headers
        :param cookies: Additional cookies
        :param json: JSON body (alternative to data)
        :param allow_redirects: Follow redirects
        :param insecure_skip_verify: Skip TLS verification
        :param timeout_seconds: Request timeout
        :param proxy: Proxy configuration
            Example:

            .. code-block:: python

                {
                    "http": "http://user:pass@ip:port",
                    "https": "http://user:pass@ip:port"
                }

        :return: Response object
        :raises TLSClientException: If Go client returns status code 0 (error)
        """

        def build_payload():
            # Prepare URL - add params to url
            final_url = url
            if params is not None:
                final_url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"

            # Prepare request body
            if data is None and json is not None:
                if isinstance(json, (dict, list)):
                    json_data = dumps(json)
                else:
                    json_data = json
                request_body = json_data
                content_type = "application/json"
            elif data is not None and not isinstance(data, (str, bytes)):
                request_body = urllib.parse.urlencode(data, doseq=True)
                content_type = "application/x-www-form-urlencoded"
            else:
                request_body = data
                content_type = None

            # Create a copy of the session headers to avoid modifying the original
            merged_headers = CaseInsensitiveDict(self.headers.copy())

            # Set Content-Type header if applicable
            if content_type is not None and "content-type" not in merged_headers:
                merged_headers["Content-Type"] = content_type

            # Merge headers from the session and the request
            if headers is not None:
                merged_headers.update(headers)
                # Remove keys with None values
                none_keys = [k for (k, v) in merged_headers.items() if v is None or k is None]
                for key in none_keys:
                    del merged_headers[key]

            # Merge cookies from the session and the request
            merged_cookies = merge_cookies(self.cookies, cookies or {})
            request_cookies = [
                {
                    "domain": c.domain,
                    "expires": c.expires,
                    "name": c.name,
                    "path": c.path,
                    "value": c.value.replace('"', "")
                }
                for c in merged_cookies
            ]

            final_proxy = ""
            if isinstance(proxy, dict) and "http" in proxy:
                final_proxy = proxy["http"]
            elif isinstance(proxy, str):
                final_proxy = proxy

            final_timeout_seconds = timeout_seconds or self.timeout_seconds
            final_certificate_pinning = self.certificate_pinning

            is_byte_request = isinstance(request_body, (bytes, bytearray))
            payload = {
                "sessionId": self._session_id,
                "followRedirects": allow_redirects,
                "forceHttp1": self.force_http1,
                "withDebug": self.debug,
                "catchPanics": self.catch_panics,
                "headers": dict(merged_headers),
                "headerOrder": self.header_order,
                "insecureSkipVerify": insecure_skip_verify,
                "isByteRequest": is_byte_request,
                "isByteResponse": True,
                "additionalDecode": self.additional_decode,
                "proxyUrl": final_proxy,
                "requestUrl": final_url,
                "requestMethod": method,
                "requestBody": base64.b64encode(request_body).decode() if is_byte_request else request_body,
                "requestCookies": request_cookies,
                "timeoutSeconds": final_timeout_seconds,
            }
            if final_certificate_pinning:
                payload["certificatePinningHosts"] = final_certificate_pinning

            # If no predefined client_identifier, we use custom TLS settings
            if self.client_identifier is None:
                payload["customTlsClient"] = {
                    "ja3String": self.ja3_string,
                    "h2Settings": self.h2_settings,
                    "h2SettingsOrder": self.h2_settings_order,
                    "pseudoHeaderOrder": self.pseudo_header_order,
                    "connectionFlow": self.connection_flow,
                    "priorityFrames": self.priority_frames,
                    "headerPriority": self.header_priority,
                    "certCompressionAlgo": self.cert_compression_algo,
                    "supportedVersions": self.supported_versions,
                    "supportedSignatureAlgorithms": self.supported_signature_algorithms,
                    "supportedDelegatedCredentialsAlgorithms": self.supported_delegated_credentials_algorithms,
                    "keyShareCurves": self.key_share_curves,
                }
            else:
                payload["tlsClientIdentifier"] = self.client_identifier
                payload["withRandomTLSExtensionOrder"] = self.random_tls_extension_order

            return payload

        payload = build_payload()

        def make_request():
            # This is a pointer to the response
            return request(dumps(payload).encode('utf-8'))

        response = await asyncio.to_thread(make_request)

        response_bytes = ctypes.string_at(response)
        response_string = response_bytes.decode('utf-8')
        response_object = loads(response_string)
        await asyncio.to_thread(freeMemory, response_object['id'].encode('utf-8'))

        if response_object["status"] == 0:
            raise TLSClientException(response_object["body"])

        response_cookie_jar = extract_cookies_to_jar(
            request_url=url,
            request_headers=payload["headers"],
            cookie_jar=self.cookies,
            response_headers=response_object["headers"]
        )
        return build_response(response_object, response_cookie_jar)

    async def get(self, url: str, **kwargs: Any) -> Response:
        """
        Sends an asynchronous GET request.

        :param url: Request URL
        :param kwargs: Additional arguments for execute_request
        :return: Response object
        """
        return await self.execute_request(method="GET", url=url, **kwargs)

    async def options(self, url: str, **kwargs: Any) -> Response:
        """
        Sends an asynchronous OPTIONS request.

        :param url: Request URL
        :param kwargs: Additional arguments for execute_request
        :return: Response object
        """
        return await self.execute_request(method="OPTIONS", url=url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> Response:
        """
        Sends an asynchronous HEAD request.

        :param url: Request URL
        :param kwargs: Additional arguments for execute_request
        :return: Response object
        """
        return await self.execute_request(method="HEAD", url=url, **kwargs)

    async def post(
            self,
            url: str,
            data: Optional[Union[str, dict]] = None,
            json: Optional[dict] = None,
            **kwargs: Any
    ) -> Response:
        """
        Sends an asynchronous POST request.

        :param url: Request URL
        :param data: Request body (form data or raw bytes)
        :param json: JSON body (alternative to data)
        :param kwargs: Additional arguments for execute_request
        :return: Response object
        """
        return await self.execute_request(method="POST", url=url, data=data, json=json, **kwargs)

    async def put(
            self,
            url: str,
            data: Optional[Union[str, dict]] = None,
            json: Optional[dict] = None,
            **kwargs: Any
    ) -> Response:
        """
        Sends an asynchronous PUT request.

        :param url: Request URL
        :param data: Request body (form data or raw bytes)
        :param json: JSON body (alternative to data)
        :param kwargs: Additional arguments for execute_request
        :return: Response object
        """
        return await self.execute_request(method="PUT", url=url, data=data, json=json, **kwargs)

    async def patch(
            self,
            url: str,
            data: Optional[Union[str, dict]] = None,
            json: Optional[dict] = None,
            **kwargs: Any
    ) -> Response:
        """
        Sends an asynchronous PATCH request.

        :param url: Request URL
        :param data: Request body (form data or raw bytes)
        :param json: JSON body (alternative to data)
        :param kwargs: Additional arguments for execute_request
        :return: Response object
        """
        return await self.execute_request(method="PATCH", url=url, data=data, json=json, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> Response:
        """
        Sends an asynchronous DELETE request.

        :param url: Request URL
        :param kwargs: Additional arguments for execute_request
        :return: Response object
        """
        return await self.execute_request(method="DELETE", url=url, **kwargs)