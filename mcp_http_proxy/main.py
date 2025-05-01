""" """

import asyncio
import logging

from mcp_http_proxy import protocol, stdio
from mcp_http_proxy.models import jsonrpc

LOGGER = logging.getLogger(__name__)


class MCPHTTPProxy:
    def __init__(self) -> None:
        self.mcp = protocol.MCP(self.write_rpc_response)
        self.stdio = stdio.Server(self.mcp.rpc_received)

    async def run(self) -> None:
        await self.stdio.run()

    async def shutdown(self) -> None:
        self.stdio.shutdown()

    async def write_rpc_response(
        self, response: jsonrpc.Response | jsonrpc.Notification
    ) -> bool:
        return await self.stdio.write(response)


def main() -> None:
    logging.basicConfig(level=logging.DEBUG, filename='mcp-http-proxy.log')
    proxy = MCPHTTPProxy()
    try:
        asyncio.run(proxy.run())
    except KeyboardInterrupt:
        asyncio.run(proxy.shutdown())
