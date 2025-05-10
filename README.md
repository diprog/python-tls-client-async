# Python-TLS-Client-Async

[![PyPI version](https://img.shields.io/pypi/v/async_tls_client.svg)](https://pypi.org/project/async_tls_client/)

> Asyncio fork of [Florian Zager's Python-TLS-Client](https://github.com/FlorianREGAZ/Python-Tls-Client) 
> with updated dependencies and modern Python support.

Python-TLS-Client-Async is a fork of [Python-TLS-Client](https://github.com/FlorianREGAZ/Python-Tls-Client) with added
support for asyncio. This library allows you to perform advanced HTTP requests while maintaining compatibility with
asynchronous programming patterns in Python.

The fork was created due to the lack of updates in the original repository, while the underlying GoLang
library [tls-client](https://github.com/bogdanfinn/tls-client) continues to evolve actively. This project aims to keep
up with the latest developments in the GoLang library and provide a modern, asynchronous interface for Python users.

# Installation

```bash
pip install async_tls_client
```

# Features

- Asyncio-based API for making HTTP requests.
- Inspired by the syntax of [requests](https://github.com/psf/requests), making it familiar and easy to use.
- Supports advanced TLS configurations like JA3, HTTP/2 settings, and more.

# Asynchronous Design

The project achieves asynchronicity by leveraging Python's `asyncio` framework. Here’s how it works:

1. **Thread Offloading for Blocking Operations:**
   Since the underlying `tls-client` library is implemented in Go and provides a blocking API, the project uses
   `asyncio.to_thread` to offload these blocking operations to separate threads. This allows the Python event loop to
   remain non-blocking while interacting with the synchronous Go library.

2. **Custom Async Session Class:**
   The `AsyncSession` class wraps synchronous operations in asynchronous methods. For example, requests are executed in
   threads to ensure compatibility with asyncio, while responses are processed asynchronously.

3. **Async Context Management:**
   The session supports asynchronous context management using `async with`, ensuring proper cleanup of resources like
   sessions and memory allocations when the session is closed.

4. **Seamless Integration with Asyncio:**
   By providing async versions of common HTTP methods (`get`, `post`, `put`, etc.), the library integrates smoothly into
   existing asyncio-based workflows.

# Examples

The syntax is similar to the original Python-TLS-Client library but adapted for asynchronous workflows.

## Example 1 - Preset

```python
import async_tls_client
import asyncio


# Example of client identifiers:
# Chrome --> chrome_103, chrome_104, chrome_105, chrome_106, chrome_107, chrome_108, chrome109, chrome110,
#            chrome111, chrome112, chrome_116_PSK, chrome_116_PSK_PQ, chrome_117, chrome_120
# Firefox --> firefox_102, firefox_104, firefox108, Firefox110, firefox_117, firefox_120
# Opera --> opera_89, opera_90
# Safari --> safari_15_3, safari_15_6_1, safari_16_0
# iOS --> safari_ios_15_5, safari_ios_15_6, safari_ios_16_0
# iPadOS --> safari_ios_15_6
# Android --> okhttp4_android_7, okhttp4_android_8, okhttp4_android_9, okhttp4_android_10, okhttp4_android_11,
#             okhttp4_android_12, okhttp4_android_13

async def main():
    session = async_tls_client.AsyncSession(
        client_identifier="chrome112",
        random_tls_extension_order=True
    )

    response = await session.get(
        "https://www.example.com/",
        headers={"key1": "value1"},
        proxy="http://user:password@host:port"
    )

    print(response.text)
    await session.close()


asyncio.run(main())
```

## Example 2 - Custom

```python
import async_tls_client
import asyncio


async def main():
    session = async_tls_client.AsyncSession(
        ja3_string="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
        h2_settings={
            "HEADER_TABLE_SIZE": 65536,
            "MAX_CONCURRENT_STREAMS": 1000,
            "INITIAL_WINDOW_SIZE": 6291456,
            "MAX_HEADER_LIST_SIZE": 262144
        },
        h2_settings_order=[
            "HEADER_TABLE_SIZE",
            "MAX_CONCURRENT_STREAMS",
            "INITIAL_WINDOW_SIZE",
            "MAX_HEADER_LIST_SIZE"
        ],
        supported_signature_algorithms=[
            "ECDSAWithP256AndSHA256",
            "PSSWithSHA256",
            "PKCS1WithSHA256",
            "ECDSAWithP384AndSHA384",
            "PSSWithSHA384",
            "PKCS1WithSHA384",
            "PSSWithSHA512",
            "PKCS1WithSHA512",
        ],
        supported_versions=["GREASE", "1.3", "1.2"],
        key_share_curves=["GREASE", "X25519"],
        cert_compression_algo="brotli",
        pseudo_header_order=[
            ":method",
            ":authority",
            ":scheme",
            ":path"
        ],
        connection_flow=15663105,
        header_order=[
            "accept",
            "user-agent",
            "accept-encoding",
            "accept-language"
        ]
    )

    response = await session.post(
        "https://www.example.com/",
        headers={"key1": "value1"},
        json={"key1": "key2"}
    )

    print(response.text)
    await session.close()


asyncio.run(main())
```

# PyInstaller / PyArmor

If you want to package the library with PyInstaller or PyArmor, make sure to include the necessary dependencies:

## Linux - Ubuntu / x86

```bash
--add-binary '{path_to_library}/async_tls_client/dependencies/tls-client-x86.so:async_tls_client/dependencies'
```

## Linux Alpine / AMD64

```bash
--add-binary '{path_to_library}/async_tls_client/dependencies/tls-client-amd64.so:async_tls_client/dependencies'
```

## MacOS M1 and older

```bash
--add-binary '{path_to_library}/async_tls_client/dependencies/tls-client-x86.dylib:async_tls_client/dependencies'
```

## MacOS M2

```bash
--add-binary '{path_to_library}/async_tls_client/dependencies/tls-client-arm64.dylib:async_tls_client/dependencies'
```

## Windows

```bash
--add-binary '{path_to_library}/async_tls_client/dependencies/tls-client-64.dll;async_tls_client/dependencies'
```

# Acknowledgements

This project is a fork of [Python-TLS-Client](https://github.com/FlorianREGAZ/Python-Tls-Client), with significant
contributions to support asyncio. The original library is based
on [tls-client](https://github.com/bogdanfinn/tls-client) by [Bogdanfinn](https://github.com/bogdanfinn).

The syntax aims to remain close to [requests](https://github.com/psf/requests) to ensure ease of use and familiarity for
Python developers.

