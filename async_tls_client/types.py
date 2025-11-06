from typing import Any, Literal, Optional, TypeAlias, TypedDict, Union

ClientIdentifiers: TypeAlias = Literal[
    # Chrome
    "chrome_103", "chrome_104", "chrome_105", "chrome_106", "chrome_107",
    "chrome_108", "chrome_109", "chrome_110", "chrome_111", "chrome_112",
    "chrome_116_PSK", "chrome_116_PSK_PQ", "chrome_117", "chrome_120",
    "chrome_124", "chrome_130_PSK", "chrome_131", "chrome_131_PSK",
    "chrome_133", "chrome_133_PSK",
    # Safari
    "safari_15_6_1", "safari_16_0",
    # iPadOS (Safari)
    "safari_ipad_15_6",
    # iOS (Safari)
    "safari_ios_15_5", "safari_ios_15_6", "safari_ios_16_0",
    "safari_ios_17_0", "safari_ios_18_0", "safari_ios_18_5",
    # Firefox
    "firefox_102", "firefox_104", "firefox_105", "firefox_106", "firefox_108",
    "firefox_110", "firefox_117", "firefox_120", "firefox_123", "firefox_132",
    "firefox_133", "firefox_135",
    # Opera
    "opera_89", "opera_90", "opera_91",
    # OkHttp4
    "okhttp4_android_7", "okhttp4_android_8", "okhttp4_android_9",
    "okhttp4_android_10", "okhttp4_android_11", "okhttp4_android_12",
    "okhttp4_android_13",
    # Custom
    "zalando_android_mobile", "zalando_ios_mobile",
    "nike_ios_mobile", "nike_android_mobile",
    "cloudscraper",
    "mms_ios", "mms_ios_1", "mms_ios_2", "mms_ios_3",
    "mesh_ios", "mesh_ios_1", "mesh_ios_2",
    "mesh_android", "mesh_android_1", "mesh_android_2",
    "confirmed_ios", "confirmed_android"
]

# https://github.com/bogdanfinn/tls-client/blob/7a71edbf6e05acd4ade8e910e4c29c968003e27b/mapper.go#L29
SignatureAlgorithms: TypeAlias = Literal[
    "PKCS1WithSHA256", "PKCS1WithSHA384", "PKCS1WithSHA512", "PSSWithSHA256", "PSSWithSHA384",
    "PSSWithSHA512", "ECDSAWithP256AndSHA256", "ECDSAWithP384AndSHA384", "ECDSAWithP521AndSHA512",
    "PKCS1WithSHA1", "ECDSAWithSHA1", "Ed25519", "SHA224_RSA", "SHA224_ECDSA"
]

DelegatedSignatureAlgorithms: TypeAlias = SignatureAlgorithms

# https://github.com/bogdanfinn/tls-client/blob/7a71edbf6e05acd4ade8e910e4c29c968003e27b/mapper.go#L21
TLSVersions: TypeAlias = Literal["GREASE", "1.3", "1.2", "1.1", "1.0"]

# https://github.com/bogdanfinn/tls-client/blob/7a71edbf6e05acd4ade8e910e4c29c968003e27b/mapper.go#L75
Curves: TypeAlias = Literal[
    "GREASE", "P256", "P384", "P521", "X25519", "P256Kyber768", "X25519Kyber512D",
    "X25519Kyber768", "X25519Kyber768Old", "X25519MLKEM768"
]

# https://github.com/bogdanfinn/tls-client/blob/7a71edbf6e05acd4ade8e910e4c29c968003e27b/mapper.go#L9
H2Settings: TypeAlias = Literal[
    "HEADER_TABLE_SIZE", "ENABLE_PUSH", "MAX_CONCURRENT_STREAMS", "INITIAL_WINDOW_SIZE", "MAX_FRAME_SIZE",
    "MAX_HEADER_LIST_SIZE", "UNKNOWN_SETTING_7", "UNKNOWN_SETTING_8", "UNKNOWN_SETTING_9"
]


class RequestOptions(TypedDict, total=False):
    """Dictionary of available request configuration options.

    :param params: Query parameters to append to URL
    :param data: Request body data (form-encoded or binary)
    :param headers: Additional headers to send
    :param cookies: Cookies to include in request
    :param json: JSON data to send as body
    :param allow_redirects: Follow redirects automatically
    :param insecure_skip_verify: Disable TLS verification
    :param timeout_seconds: Request timeout duration
    :param timeout_milliseconds: Request timeout in milliseconds
    :param proxy: Proxy configuration for request
    :param request_host_override: Override request Host header
    :param stream_output_path: Path to write streaming output
    :param stream_output_block_size: Block size for streamed chunks
    :param stream_output_eof_symbol: Symbol to signal end of stream
    """
    params: Optional[dict[str, Any]]
    data: Optional[Union[str, bytes, dict[str, Any]]]
    headers: Optional[dict[str, str]]
    cookies: Optional[dict[str, str]]
    json: Optional[Union[dict[str, Any], list[Any], str]]
    allow_redirects: Optional[bool]
    insecure_skip_verify: Optional[bool]
    timeout_seconds: Optional[int]
    timeout_milliseconds: Optional[int]
    proxy: Optional[Union[dict[str, str], str]]
    request_host_override: Optional[str]
    stream_output_path: Optional[str]
    stream_output_block_size: Optional[int]
    stream_output_eof_symbol: Optional[str]

