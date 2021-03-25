"""
Simple FreeSWITCH inbound event socket implementation based on asyncio
"""

import asyncio
import logging
from typing import Dict, Tuple


class ESLError(Exception):
    """
    Base class for all ESL errors.
    """


class ESLHeaderError(ESLError):
    """
    Error thrown while parsing ESL response headers.
    """


class ESLProtocolError(ESLError):
    """
    Error thrown if event socket returns unexpected response.
    """


class ESL():
    """
    Simple FreeSWITCH inbound event socket implementation based on asyncio
    """

    def __init__(self,
                 reader: asyncio.StreamReader,
                 writer: asyncio.StreamWriter):
        self._in = reader
        self._out = writer
        self._log = logging.getLogger('esl')

    async def initialize(self):
        """
        Initialize an ESL connection, wait for auth/request.
        """
        self._log.debug("Expect auth/request")
        headers = await self._read_all_headers()
        _ = await self._read_body(headers)
        if headers["Content-Type"] == 'auth/request':
            self._log.debug("Received auth/request")
        else:
            raise ESLProtocolError(f"Expected auth request, "
                                   f"but got {headers!r}")

    async def login(self, password: str) -> bool:
        """
        Send password to FreeSWITCH. Returns True if login was successfull.
        """
        result = False

        self._log.info("Login: Send password")
        await self._write(f'auth {password}')

        self._log.debug("Expect command/reply")
        headers = await self._read_all_headers()
        body = await self._read_body(headers)
        if headers["Content-Type"] == 'command/reply' \
                and headers["Reply-Text"] == "+OK accepted":
            self._log.debug("Received command/reply")
            result = True
        elif headers["Content-Type"] == "text/rude-rejection":
            self._log.error("Received text/rude-rejection: %s", body)
        else:
            raise ESLProtocolError(f"Expected auth response, "
                                   f"but got {headers!r}")

        self._log.info("Login: %s", "success" if result else "failure")
        return result

    async def send(self, command: str) -> Tuple[Dict[str, str], str]:
        """
        Send command to FreeSWITCH. Returns a tuple (headers, body).
        """
        body = ""
        headers = {}

        self._log.debug("Send %s", command)
        await self._write(command)

        self._log.debug("Expect api/response")
        headers = await self._read_all_headers()
        body = await self._read_body(headers)

        if headers["Content-Type"] != 'api/response':
            raise ESLProtocolError(f"Expected api response, "
                                   f"but got {headers!r}")

        return headers, body

    async def _write(self, command: str):
        self._out.write(f'{command}\n\n'.encode())
        await self._out.drain()

    async def _read_headers(self):
        while True:
            line = await self._in.readline()
            if len(line) == 0 or line[-1:] != b"\n":
                raise ESLHeaderError("Encountered EOF "
                                     "while reading response headers")
            if line == b"\n":
                return

            name, value = line.decode().split(":", 1)
            yield name.strip(), value.strip()

    async def _read_all_headers(self) -> Dict[str, str]:
        return {key: value async for key, value in self._read_headers()}

    async def _read_body(self, headers: Dict[str, str]) -> str:
        result = ""

        if "Content-Length" in headers:
            size = int(headers["Content-Length"])
            result = (await self._in.readexactly(size)).decode()

        return result
