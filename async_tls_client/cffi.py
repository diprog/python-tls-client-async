import asyncio
import ctypes
import json
import os
from platform import machine
from sys import platform

from .exceptions import TLSClientException

if platform == 'darwin':
    file_ext = '-arm64.dylib' if machine() == "arm64" else '-x86.dylib'
elif platform in ('win32', 'cygwin'):
    file_ext = '-64.dll' if 8 == ctypes.sizeof(ctypes.c_voidp) else '-32.dll'
else:
    if machine() == "aarch64":
        file_ext = '-arm64.so'
    elif "x86" in machine():
        file_ext = '-x86.so'
    else:
        file_ext = '-amd64.so'

root_dir = os.path.abspath(os.path.dirname(__file__))
binary_filepath = os.path.join(root_dir, 'dependencies', f'tls-client{file_ext}')
library = ctypes.cdll.LoadLibrary(binary_filepath)

# Extract methods from the shared library
_freeMemory = library.freeMemory
_freeMemory.argtypes = [ctypes.c_char_p]
_freeMemory.restype = ctypes.c_char_p

_request = library.request
_request.argtypes = [ctypes.c_char_p]
_request.restype = ctypes.c_char_p

_destroySession = library.destroySession
_destroySession.argtypes = [ctypes.c_char_p]
_destroySession.restype = ctypes.c_char_p

_getCookiesFromSession = library.getCookiesFromSession
_getCookiesFromSession.argtypes = [ctypes.c_char_p]
_getCookiesFromSession.restype = ctypes.c_char_p

_addCookiesToSession = library.addCookiesToSession
_addCookiesToSession.argtypes = [ctypes.c_char_p]
_addCookiesToSession.restype = ctypes.c_char_p


async def free_memory(response_id: str):
    await asyncio.to_thread(_freeMemory, response_id.encode('utf-8'))


async def request(payload: dict) -> dict:
    response = await asyncio.to_thread(
        _request,
        json.dumps(payload).encode('utf-8')
    )
    response_bytes = ctypes.string_at(response)
    response_string = response_bytes.decode('utf-8')
    response_object = json.loads(response_string)

    await free_memory(response_object["id"])

    if response_object["status"] == 0:
        raise TLSClientException(response_object["body"])

    return response_object


async def destroy_session(session_id: str) -> dict:
    destroy_session_response = await asyncio.to_thread(
        _destroySession,
        json.dumps({"sessionId": session_id}).encode('utf-8')
    )
    destroy_session_response_bytes = ctypes.string_at(destroy_session_response)
    destroy_session_response_string = destroy_session_response_bytes.decode('utf-8')
    destroy_session_response_object = json.loads(destroy_session_response_string)
    await free_memory(destroy_session_response_object['id'])
    return destroy_session_response_object


async def get_cookies_from_session(session_id: str, url: str) -> dict:
    cookies_response = await asyncio.to_thread(
        _getCookiesFromSession,
        json.dumps({"sessionId": session_id, "url": url}).encode('utf-8')
    )
    # we dereference the pointer to a byte array
    cookies_response_bytes = ctypes.string_at(cookies_response)
    # convert our byte array to a string (tls client returns json)
    cookies_response_string = cookies_response_bytes.decode('utf-8')
    # convert response string to json
    cookies_response_object = json.loads(cookies_response_string)
    return cookies_response_object


async def add_cookies_to_session(session_id, cookies: list[dict], url: str) -> dict:
    add_cookies_to_session_response = await asyncio.to_thread(
        _addCookiesToSession,
        json.dumps({"cookies": cookies, "sessionId": session_id, "url": url}).encode('utf-8')
    )
    add_cookies_bytes = ctypes.string_at(add_cookies_to_session_response)
    add_cookies_string = add_cookies_bytes.decode('utf-8')
    add_cookies_object = json.loads(add_cookies_string)
    return add_cookies_object
