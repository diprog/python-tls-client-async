from base64 import b64encode
from typing import Any, Dict, Optional, TYPE_CHECKING, Tuple, Union
from urllib.parse import urlencode
from json import dumps as json_dumps

if TYPE_CHECKING:
    from .session import AsyncSession


def _prepare_request_body(
        data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        json_data: Optional[Union[Dict, list, str]] = None
) -> Tuple[Optional[Union[str, bytes]], Optional[str]]:
    """
    Prepares the request body and determines the appropriate Content-Type.

    Priority:
    1. If json_data is provided, it takes precedence over data
    2. For dict data, uses urlencode
    3. Strings/bytes are used as-is
    """
    if json_data is not None:
        if isinstance(json_data, (dict, list)):
            return json_dumps(json_data), 'application/json'
        return str(json_data), 'application/json'

    if data is not None:
        if isinstance(data, dict):
            return urlencode(data, doseq=True), 'application/x-www-form-urlencoded'
        return data, None

    return None, None


def _merge_headers(
        session_headers: Optional[Dict[str, str]],
        request_headers: Optional[Dict[str, str]],
        content_type: Optional[str]
) -> Dict[str, str]:
    """
    Merges session headers with request headers, considering Content-Type.

    Priority:
    1. Headers from current request
    2. Headers from session
    3. Auto-detected Content-Type
    """
    merged = {}
    if session_headers:
        merged.update(session_headers)
    if request_headers:
        merged.update(request_headers)
    if content_type and 'Content-Type' not in merged:
        merged['Content-Type'] = content_type
    return merged


def _prepare_cookies(cookies: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Formats cookies into the expected backend format (name=value dict)."""
    return cookies or {}


def _prepare_proxy(proxy: Optional[Union[Dict[str, Any], str]]) -> Optional[str]:
    """Formats proxy into connection string."""
    if proxy is None:
        return None

    if isinstance(proxy, str):
        return proxy

    if isinstance(proxy, dict):
        # Proxy with authentication
        if 'url' in proxy:
            return proxy['url']

        scheme = proxy.get('scheme', 'http')
        host = proxy.get('host', '')
        port = proxy.get('port', '')
        username = proxy.get('username')
        password = proxy.get('password')

        if not host:
            return None

        # Format with port
        host_port = f"{host}:{port}" if port else host

        # Add authentication
        if username and password:
            auth = f"{username}:{password}@"
        else:
            auth = ""

        return f"{scheme}://{auth}{host_port}"

    raise TypeError(f"Unsupported proxy type: {type(proxy)}")


def build_payload(
    session: "AsyncSession",
    method: str,
    url: str,
    params: Optional[dict[str, Any]] = None,
    data: Optional[Union[str, bytes, dict]] = None,
    headers: Optional[dict[str, str]] = None,
    cookies: Optional[dict[str, str]] = None,
    json: Optional[Union[dict, list, str]] = None,
    allow_redirects: bool = False,
    insecure_skip_verify: bool = False,
    timeout_seconds: Optional[int] = None,
    timeout_milliseconds: Optional[int] = None,
    proxy: Optional[Union[dict, str]] = None,
    request_host_override: Optional[str] = None,
    stream_output_path: Optional[str] = None,
    stream_output_block_size: Optional[int] = None,
    stream_output_eof_symbol: Optional[str] = None
) -> dict:
    final_url = url
    if params:
        final_url = f"{url}?{urlencode(params, doseq=True)}"

    request_body, content_type = _prepare_request_body(data, json)

    merged_headers = _merge_headers(session.headers, headers, content_type)

    request_cookies = _prepare_cookies(cookies)

    final_proxy = _prepare_proxy(proxy)

    # Таймаут
    timeout_sec = timeout_seconds or session.timeout_seconds
    timeout_ms = timeout_milliseconds or session.timeout_milliseconds

    if timeout_sec and timeout_ms:
        raise ValueError("Cannot specify both timeout_seconds and timeout_milliseconds")

    # Транспортные опции
    transport_options = {}
    if session.idle_conn_timeout is not None:
        transport_options["idleConnTimeout"] = int(session.idle_conn_timeout * 1e9)
    if session.max_idle_conns is not None:
        transport_options["maxIdleConns"] = session.max_idle_conns
    if session.max_idle_conns_per_host is not None:
        transport_options["maxIdleConnsPerHost"] = session.max_idle_conns_per_host
    if session.max_conns_per_host is not None:
        transport_options["maxConnsPerHost"] = session.max_conns_per_host
    if session.max_response_header_bytes is not None:
        transport_options["maxResponseHeaderBytes"] = session.max_response_header_bytes
    if session.write_buffer_size is not None:
        transport_options["writeBufferSize"] = session.write_buffer_size
    if session.read_buffer_size is not None:
        transport_options["readBufferSize"] = session.read_buffer_size
    if session.disable_keep_alives is not None:
        transport_options["disableKeepAlives"] = session.disable_keep_alives
    if session.disable_compression is not None:
        transport_options["disableCompression"] = session.disable_compression

    # Потоковая запись
    stream_path = stream_output_path or session.stream_output_path
    stream_block = stream_output_block_size or session.stream_output_block_size
    stream_eof = stream_output_eof_symbol or session.stream_output_eof_symbol

    payload = {
        "sessionId": session.session_id,
        "followRedirects": allow_redirects,
        "forceHttp1": session.force_http1,
        "withDebug": session.debug,
        "catchPanics": session.catch_panics,
        "headers": dict(merged_headers),
        "headerOrder": session.header_order,
        "insecureSkipVerify": insecure_skip_verify,
        "isByteRequest": isinstance(request_body, (bytes, bytearray)),
        "isByteResponse": True,
        "additionalDecode": session.additional_decode,
        "proxyUrl": final_proxy,
        "requestUrl": final_url,
        "requestMethod": method,
        "withoutCookieJar": session.without_cookie_jar,
        "withDefaultCookieJar": session.with_default_cookie_jar,
        "requestCookies": request_cookies,
        "disableIPV4": session.disable_ipv4,
        "disableIPV6": session.disable_ipv6,
        "isRotatingProxy": session.is_rotating_proxy,
        "serverNameOverwrite": session.server_name_overwrite,
        "localAddress": session.local_address,
        "defaultHeaders": session.default_headers,
        "connectHeaders": session.connect_headers,
        "streamOutputPath": stream_path,
        "streamOutputBlockSize": stream_block,
        "streamOutputEOFSymbol": stream_eof,
        "requestHostOverride": request_host_override,
        "transportOptions": transport_options if transport_options else None
    }

    # Таймауты
    if timeout_ms:
        payload["timeoutMilliseconds"] = timeout_ms
    elif timeout_sec:
        payload["timeoutSeconds"] = timeout_sec

    # Тело запроса
    if request_body is not None:
        if payload["isByteRequest"]:
            payload["requestBody"] = b64encode(request_body).decode()
        else:
            payload["requestBody"] = request_body

    # Сертификаты
    if session.certificate_pinning:
        payload["certificatePinningHosts"] = session.certificate_pinning

    # TLS клиент
    if session.client_identifier is None:
        payload["tlsClientIdentifier"] = ""
        custom_client = {
            "ja3String": session.ja3_string,
            "h2Settings": session.h2_settings,
            "h2SettingsOrder": session.h2_settings_order,
            "pseudoHeaderOrder": session.pseudo_header_order,
            "connectionFlow": session.connection_flow,
            "priorityFrames": session.priority_frames,
            "headerPriority": session.header_priority,
            "certCompressionAlgos": session.cert_compression_algos,
            "supportedVersions": session.supported_versions,
            "supportedSignatureAlgorithms": session.supported_signature_algorithms,
            "supportedDelegatedCredentialsAlgorithms": session.supported_delegated_credentials_algorithms,
            "keyShareCurves": session.key_share_curves,
            "alpnProtocols": session.alpn_protocols,
            "alpsProtocols": session.alps_protocols,
            "echCandidatePayloads": session.ech_candidate_payloads,
            "echCandidateCipherSuites": session.ech_candidate_cipher_suites,
            "recordSizeLimit": session.record_size_limit
        }
        payload["customTlsClient"] = {k: v for k, v in custom_client.items() if v is not None}
    else:
        payload["tlsClientIdentifier"] = session.client_identifier
        payload["withRandomTLSExtensionOrder"] = session.random_tls_extension_order

    return payload