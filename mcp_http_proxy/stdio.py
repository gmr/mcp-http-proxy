import asyncio
import io
import logging
import os
import sys
import typing
from asyncio import streams

import orjson

from mcp_http_proxy.models import jsonrpc

LOGGER = logging.getLogger(__name__)


class Server:
    def __init__(self, on_request: typing.Callable) -> None:
        self.buffer: bytes = b''
        self.loop: asyncio.BaseEventLoop | None = None
        self.on_request = on_request
        self.reader: asyncio.StreamReader | None = None
        self.stdout: io.TextIOWrapper | None = None
        self.stop: asyncio.Event | None = None
        self.writer: asyncio.StreamWriter | None = None

    async def run(self) -> None:
        await self._setup()
        while not self.stop.is_set():
            chunk = await self.reader.read(4096)
            LOGGER.debug('Chunk: %r', chunk)
            if not chunk:
                LOGGER.error('Remote disconnect')
                return
            self.buffer += chunk
            await self._parse_buffer()
        self.writer.close()

    async def _parse_buffer(self) -> None:
        arrays, brackets, offset = 0, 0, 0
        escape_next = False
        in_string = False
        while offset < len(self.buffer):
            if self.buffer[offset] == 34 and not escape_next:
                in_string = not in_string
            if not in_string:
                match self.buffer[offset]:
                    case 123:
                        brackets += 1
                    case 125:
                        brackets -= 1
                    case 91:
                        arrays += 1
                    case 93:
                        arrays -= 1
            if offset and not brackets and not arrays:
                try:
                    value = orjson.loads(self.buffer[:offset + 1])
                except orjson.JSONDecodeError:
                    LOGGER.debug(
                        'Invalid JSON (%r, %r, %r, %r): %r',
                        brackets,
                        arrays,
                        in_string,
                        escape_next,
                        self.buffer[:offset],
                    )
                else:
                    self.buffer = self.buffer[offset + 1:].strip()
                    offset = 0
                    await self._send_request(value)
                    continue

            escape_next = (
                self.buffer[offset] == 92 and not escape_next and in_string
            )
            offset += 1

    async def _send_request(self, value: dict) -> None:
        if value.get('method', '').startswith('notifications'):
            await self.on_request(jsonrpc.Notification.model_validate(value))
        else:
            await self.on_request(jsonrpc.Request.model_validate(value))

    def shutdown(self) -> None:
        self.stop.set()

    async def write(
        self, value: jsonrpc.Response | jsonrpc.Notification
    ) -> bool:
        data = value.model_dump_json(
            exclude_none=True, exclude_unset=True
        ).encode('utf-8')
        LOGGER.debug('Writing %r', data)
        self.writer.write(data)
        self.writer.write(b'\n')
        await self.writer.drain()
        return True

    async def _setup(self):
        self.loop = asyncio.get_running_loop()
        self.stop = asyncio.Event()
        self.reader = asyncio.StreamReader(loop=self.loop)
        await self.loop.connect_read_pipe(self.reader_protocol, sys.stdin)
        self.stdout = os.fdopen(sys.stdout.fileno(), 'wb')
        transport, protocol = await self.loop.connect_write_pipe(
            self.flow_control_mixin, self.stdout
        )
        self.writer = asyncio.StreamWriter(
            transport, protocol, None, self.loop
        )

    def flow_control_mixin(self) -> streams.FlowControlMixin:
        return streams.FlowControlMixin(loop=self.loop)

    def reader_protocol(self) -> asyncio.StreamReaderProtocol:
        return asyncio.StreamReaderProtocol(self.reader, loop=self.loop)
