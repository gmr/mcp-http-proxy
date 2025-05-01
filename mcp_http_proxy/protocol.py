import enum
import logging
import typing

from mcp_http_proxy import version
from mcp_http_proxy.models import jsonrpc, mcp

LOGGER = logging.getLogger(__name__)


class State(enum.Enum):
    IDLE = 0
    INITIALIZE_RECEIVED = 1
    INITIALIZE_RESPONDED = 2


class MCP:
    def __init__(self, writer: typing.Callable) -> None:
        self.state = State.IDLE
        self.write_response = writer

    async def rpc_received(
        self, value: jsonrpc.Notification | jsonrpc.Request
    ) -> None:
        rpc = mcp.jsonrpc_to_mcp(value)
        if value.method == mcp.INITIALIZE:
            response = jsonrpc.Response(
                jsonrpc='2.0',
                id=value.id,
                result=mcp.InitializeResult(
                    protocolVersion=rpc.protocolVersion,
                    capabilities=mcp.ServerCapabilities(
                        completions=None,
                        experimental=None,
                        logging=None,
                        pagination=None,
                        prompts={'listChanged': True},
                        resources={'listChanged': True, 'subscribe': True},
                        tools={'listChanged': True},
                    ),
                    serverInfo=mcp.Implementation(
                        name='MCP-HTTP-PROXY', version=version
                    ),
                ),
            )
            await self.write_response(response)
        elif value.method == mcp.INITIALIZED:
            LOGGER.info('Client initialized')
        else:
            LOGGER.debug('Fail')
