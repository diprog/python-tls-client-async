# Python-TLS-Client-Async

[![PyPI version](https://img.shields.io/pypi/v/async_tls_client.svg)](https://pypi.org/project/async_tls_client/)
[![Python versions](https://img.shields.io/pypi/pyversions/async_tls_client.svg)](https://pypi.org/project/async_tls_client/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Asyncio-first TLS client for Python with advanced fingerprinting capabilities. Modern fork of [Python-TLS-Client](https://github.com/FlorianREGAZ/Python-Tls-Client) with enhanced features and active maintenance.

```python
from async_tls_client import AsyncClient
import asyncio

async def main():
    async with AsyncClient(
        client_identifier="chrome120",
        random_tls_extension_order=True
    ) as client:
        response = await client.get("https://tls.peet.ws/api/all")
        print(f"Detected TLS fingerprint: {response.json()['tls']['ja3_hash']}")

asyncio.run(main())
```

## Features ✨

- **Full Async Support**: Built with asyncio for high-performance concurrent requests
- **Modern TLS Fingerprinting**: JA3, JA4, HTTP/2 fingerprints and TLS 1.3 support
- **Client Profiles**: 50+ preconfigured clients (Chrome, Firefox, Safari, iOS, Android)
- **Advanced Configuration**:
  - Custom TLS cipher suites & extensions
  - HTTP/2 and QUIC protocol support
  - Certificate pinning and compression
  - Proxy support (HTTP/S, SOCKS4/5)
- **Auto-Cookie Management**: Session persistence with configurable cookie jars
- **Request Manipulation**: Header ordering, pseudo-header customization, and priority control

## Why This Fork? 🚀

This project was created to address the lack of updates in the original Python-TLS-Client while incorporating:
- Modern Python 3.9+ features and async/await syntax
- Active updates from the underlying [tls-client](https://github.com/bogdanfinn/tls-client) Go library
- Improved error handling and debugging capabilities
- Better documentation and developer experience
- Enhanced security features for enterprise use cases

## Installation 📦

```bash
pip install async_tls_client
```

## Quickstart 🚀

### Basic Usage

```python
from async_tls_client import AsyncClient
import asyncio

async def main():
    async with AsyncClient("chrome120") as client:
        response = await client.get(
            "https://httpbin.org/json",
            headers={"X-API-Key": "secret"},
            proxy="http://user:pass@proxy:port"
        )
        print(f"Status: {response.status_code}")
        print(f"Headers: {response.headers}")
        print(f"JSON: {response.json()}")

asyncio.run(main())
```

### Advanced Configuration

```python
from async_tls_client import AsyncClient

client = AsyncClient(
    ja3_string="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
    h2_settings={
        "HEADER_TABLE_SIZE": 65536,
        "MAX_CONCURRENT_STREAMS": 1000,
        "INITIAL_WINDOW_SIZE": 6291456,
        "MAX_HEADER_LIST_SIZE": 262144
    },
    supported_signature_algorithms=[
        "ECDSAWithP256AndSHA256",
        "PSSWithSHA256",
        "PKCS1WithSHA256",
        "ECDSAWithP384AndSHA384",
        "PSSWithSHA384",
        "PKCS1WithSHA512",
    ],
    certificate_pinning={
        "example.com": [
            "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        ]
    }
)
```

## Client Profiles 🕶️

Preconfigured client identifiers (https://github.com/bogdanfinn/tls-client/blob/master/profiles/profiles.go):

| Browser/Framework       | Available Profiles                                                                 |
|-------------------------|------------------------------------------------------------------------------------|
| Chrome                  | chrome_103 - chrome_133 (including PSK variants: 116_PSK, 116_PSK_PQ, 131_PSK, 133_PSK) |
| Firefox                 | firefox_102 - firefox_135                                                          |
| Safari (Desktop)        | safari_15_6_1, safari_16_0, safari_ipad_15_6                                       |
| Safari (iOS)            | safari_ios_15_5 - safari_ios_18_0                                                  |
| Opera                   | opera_89 - opera_91                                                                |
| Android (OkHttp)        | okhttp4_android_7 - okhttp4_android_13                                             |
| iOS (Custom)            | mms_ios (v1, v2, v3), mesh_ios (v1, v2), confirmed_ios, zalando_ios_mobile, nike_ios_mobile |
| Android (Custom)        | mesh_android (v1, v2), confirmed_android, zalando_android_mobile, nike_android_mobile |
| Cloudflare              | cloudscraper                                                                       |

## Advanced Features 🔧

### Custom Fingerprint Configuration

```python
client = AsyncClient(
    ja3_string="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
    h2_settings_order=["HEADER_TABLE_SIZE", "MAX_CONCURRENT_STREAMS"],
    pseudo_header_order=[":method", ":authority", ":scheme", ":path"],
    header_order=["accept", "user-agent", "accept-encoding"],
    force_http1=False,
    cert_compression_algo="brotli"
)
```

### Certificate Pinning

```python
client = AsyncClient(
    certificate_pinning={
        "api.bank.com": [
            "sha256/7HIpactkIAq2Y49orFOOQKurWxmmSFZhBCoQYcRhJ3Y=",
            "sha256/YLh1dUR9y6Kja30RrAn7JKnbQG/uEtLMkBgFF2Fuihg="
        ]
    }
)
```

### Proxy Support

```python
response = await client.get(
    "https://api.example.com",
    proxy="socks5://user:pass@proxy:1080"
)
```

## Asynchronous Design 🚧

The client leverages Python's asyncio through three key strategies:

1. **Non-blocking I/O**
   - Network operations run in separate threads using `asyncio.to_thread`
   - Go TLS client handles remain managed in background executors

2. **Session Management**
   - `AsyncClient` context manager handles automatic cleanup
   - Connection pooling with automatic keep-alives
   - Cookie persistence across requests

3. **Resource Optimization**
   - Zero-copy body handling for large responses
   - Lazy initialization of heavy resources
   - Automatic memory cleanup of Go pointers

## Packaging 📦

When using PyInstaller/PyArmor, include the shared library:

### Windows
```bash
--add-binary 'async_tls_client/dependencies/tls-client-64.dll;async_tls_client/dependencies'
```

### Linux
```bash
--add-binary 'async_tls_client/dependencies/tls-client-x86.so:async_tls_client/dependencies'
```

### macOS
```bash
--add-binary 'async_tls_client/dependencies/tls-client-arm64.dylib:async_tls_client/dependencies'
```

## Acknowledgements 🙏

- Original Python implementation: [FlorianREGAZ/Python-Tls-Client](https://github.com/FlorianREGAZ/Python-Tls-Client)
- Core TLS implementation: [bogdanfinn/tls-client](https://github.com/bogdanfinn/tls-client)
- Inspiration: [psf/requests](https://github.com/psf/requests)

## License 📄

MIT License - See [LICENSE](LICENSE) for details