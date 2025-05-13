import base64
import urllib.parse
from json import dumps
from typing import Any, Optional, TYPE_CHECKING, Union

from nocasedict import NocaseDict

from async_tls_client.cookies import create_cookie

if TYPE_CHECKING:
    from async_tls_client.session.session import AsyncSession


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
        proxy: Optional[Union[dict, str]] = None
) -> dict:
    """Build payload dictionary for TLS client request."""
    # Prepare URL with query parameters
    final_url = url
    if params:
        final_url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"

    # Prepare request body and content type
    request_body, content_type = _prepare_request_body(data, json)

    # Merge and clean headers
    merged_headers = _merge_headers(session.headers, headers, content_type)

    # Prepare cookies
    request_cookies = _prepare_cookies(cookies)

    # Prepare proxy URL
    final_proxy = _prepare_proxy(proxy)

    # Build base payload
    payload = {
        "sessionId": session._session_id,
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
        "withoutCookieJar": False,
        "withDefaultCookieJar": True,
        "requestCookies": request_cookies,
        "timeoutSeconds": timeout_seconds or session.timeout_seconds,
    }

    # Handle request body encoding
    if request_body is not None:
        if payload["isByteRequest"]:
            payload["requestBody"] = base64.b64encode(request_body).decode()
        else:
            payload["requestBody"] = request_body

    # Add certificate pinning if configured
    if session.certificate_pinning:
        payload["certificatePinningHosts"] = session.certificate_pinning

    # Configure TLS client parameters
    _configure_tls_client(session, payload)

    return payload


def _prepare_request_body(data, json):
    """Prepare request body and determine content type."""
    if data is None and json is not None:
        request_body = json if isinstance(json, (str, bytes)) else dumps(json)
        content_type = "application/json"
    elif data is not None and not isinstance(data, (str, bytes)):
        request_body = urllib.parse.urlencode(data, doseq=True)
        content_type = "application/x-www-form-urlencoded"
    else:
        request_body = data
        content_type = None
    return request_body, content_type


def _merge_headers(base_headers: NocaseDict, extra_headers: Optional[dict], content_type: Optional[str]) -> NocaseDict:
    """Merge and clean headers."""
    merged = NocaseDict(base_headers.copy())
    if extra_headers:
        merged.update(extra_headers)
        # Remove keys with None values
        none_keys = [k for k, v in merged.items() if v is None or k is None]
        for key in none_keys:
            del merged[key]
    if content_type and "content-type" not in merged:
        merged["Content-Type"] = content_type
    return merged


def _prepare_cookies(cookies: Optional[dict[str, str]]) -> list[dict]:
    """Convert cookies dictionary to request format."""
    if not cookies:
        return []

    request_cookies = []
    for name, value in cookies.items():
        cookie = create_cookie(name, value)
        request_cookies.append({
            "domain": cookie.domain,
            "expires": cookie.expires,
            "name": cookie.name,
            "path": cookie.path,
            "value": cookie.value.replace('"', "")
        })
    return request_cookies


def _prepare_proxy(proxy: Optional[Union[dict, str]]) -> str:
    """Extract proxy URL from proxy configuration."""
    if isinstance(proxy, dict) and "http" in proxy:
        return proxy["http"]
    if isinstance(proxy, str):
        return proxy
    return ""


def _configure_tls_client(session: "AsyncSession", payload: dict):
    """Configure TLS client parameters in payload."""
    if session.client_identifier is None:
        payload["customTlsClient"] = {
            "ja3String": session.ja3_string,
            "h2Settings": session.h2_settings,
            "h2SettingsOrder": session.h2_settings_order,
            "pseudoHeaderOrder": session.pseudo_header_order,
            "connectionFlow": session.connection_flow,
            "priorityFrames": session.priority_frames,
            "headerPriority": session.header_priority,
            "certCompressionAlgo": session.cert_compression_algo,
            "supportedVersions": session.supported_versions,
            "supportedSignatureAlgorithms": session.supported_signature_algorithms,
            "supportedDelegatedCredentialsAlgorithms": session.supported_delegated_credentials_algorithms,
            "keyShareCurves": session.key_share_curves,
        }
    else:
        payload["tlsClientIdentifier"] = session.client_identifier
        payload["withRandomTLSExtensionOrder"] = session.random_tls_extension_order
