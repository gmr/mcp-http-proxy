import logging
import typing

import pydantic

from mcp_http_proxy.models import jsonrpc

LOGGER = logging.getLogger(__name__)

INITIALIZE = 'initialize'
INITIALIZED = 'notifications/initialized'


class MCPModel(pydantic.BaseModel):
    def model_dump(self, *args, **kwargs) -> dict[str, typing.Any]:
        """Dump the model, stripping None values"""
        kwargs['exclude_none'] = True
        kwargs['exclude_unset'] = True
        return super().model_dump(*args, **kwargs)


class Annotations(MCPModel):
    """Optional annotations for the client.

    The client can use annotations to inform how objects are used or displayed.
    """

    audience: list['Role'] | None = None
    priority: float | None = None

    model_config = {'extra': 'allow'}


class AudioContent(MCPModel):
    """Audio provided to or from an LLM."""

    data: str
    mimeType: str
    type: typing.Literal['audio']
    annotations: Annotations | None = None

    model_config = {'extra': 'allow'}


class BlobResourceContents(MCPModel):
    """Binary resource contents."""

    blob: str
    uri: str
    mimeType: str | None = None

    model_config = {'extra': 'allow'}


class TextContent(MCPModel):
    """Text provided to or from an LLM."""

    text: str
    type: typing.Literal['text']
    annotations: Annotations | None = None

    model_config = {'extra': 'allow'}


class ImageContent(MCPModel):
    """An image provided to or from an LLM."""

    data: str
    mimeType: str
    type: typing.Literal['image']
    annotations: Annotations | None = None

    model_config = {'extra': 'allow'}


class TextResourceContents(MCPModel):
    """Text resource contents."""

    text: str
    uri: str
    mimeType: str | None = None

    model_config = {'extra': 'allow'}


ResourceContentsType = TextResourceContents | BlobResourceContents


class EmbeddedResource(MCPModel):
    """The contents of a resource, embedded into a prompt or
    a tool call result.
    """

    resource: ResourceContentsType
    type: typing.Literal['resource']
    annotations: Annotations | None = None

    model_config = {'extra': 'allow'}


class CallToolResult(MCPModel):
    """The server's response to a tool call."""

    content: list[TextContent | ImageContent | AudioContent | EmbeddedResource]
    isError: bool | None = None
    _meta: dict[str, typing.Any] | None = None

    model_config = {'extra': 'allow'}


# Define Role enum
Role = typing.Literal['assistant', 'user']


class PromptMessage(MCPModel):
    """Describes a message returned as part of a prompt."""

    content: TextContent | ImageContent | AudioContent | EmbeddedResource
    role: Role

    model_config = {'extra': 'allow'}


class SamplingMessage(MCPModel):
    """Describes a message issued to or received from an LLM API."""

    content: TextContent | ImageContent | AudioContent
    role: Role

    model_config = {'extra': 'allow'}


class ModelHint(MCPModel):
    """Hints to use for model selection."""

    name: str | None = None

    model_config = {'extra': 'allow'}


class ModelPreferences(MCPModel):
    """The server's preferences for model selection during sampling."""

    costPriority: float | None = None
    intelligencePriority: float | None = None
    speedPriority: float | None = None
    hints: list[ModelHint] | None = None

    model_config = {'extra': 'allow'}


class CreateMessageRequest(MCPModel):
    """A request from the server to sample an LLM via the client."""

    method: typing.Literal['sampling/createMessage']
    params: dict[str, typing.Any]

    model_config = {'extra': 'allow'}


class CreateMessageResult(MCPModel):
    """The client's response to a sampling/create_message request."""

    content: TextContent | ImageContent | AudioContent
    model: str
    role: Role
    stopReason: str | None = None
    _meta: dict[str, typing.Any] | None = None

    model_config = {'extra': 'allow'}


class Implementation(MCPModel):
    """Describes the name and version of an MCP implementation."""

    name: str
    version: str

    model_config = {'extra': 'allow'}


class ClientCapabilities(MCPModel):
    """Capabilities a client may support."""

    roots: dict[str, typing.Any] | None = None
    sampling: dict[str, typing.Any] | None = None
    experimental: dict[str, dict[str, typing.Any]] | None = None

    model_config = {'extra': 'allow'}


class ServerCapabilities(MCPModel):
    """Capabilities that a server may support."""

    completions: dict | None
    experimental: dict | None
    logging: dict | None
    pagination: dict | None
    prompts: dict[str, bool] | None
    resources: dict[str, bool] | None
    tools: dict[str, bool] | None


class InitializeRequest(MCPModel):
    """Request sent from the client to the server when it first connects."""

    protocolVersion: str
    capabilities: ClientCapabilities
    clientInfo: Implementation
    model_config = {'extra': 'allow'}


class InitializeResult(MCPModel):
    """Server's response to the initialize request."""

    protocolVersion: str = '2025-03-26'
    capabilities: ServerCapabilities
    serverInfo: Implementation
    instructions: str | None = None
    _meta: dict[str, typing.Any] | None = None


class PromptReference(MCPModel):
    """Identifies a prompt."""

    name: str
    type: typing.Literal['ref/prompt']

    model_config = {'extra': 'allow'}


class ResourceReference(MCPModel):
    """A reference to a resource or resource template definition."""

    uri: str
    type: typing.Literal['ref/resource']

    model_config = {'extra': 'allow'}


class CompleteRequest(MCPModel):
    """A request from the client to the server for completion options."""

    method: typing.Literal['completion/complete']
    params: dict[str, typing.Any]

    model_config = {'extra': 'allow'}


class CompleteResult(MCPModel):
    """The server's response to a completion/complete request."""

    completion: dict[str, typing.Any]
    _meta: dict[str, typing.Any] | None = None

    model_config = {'extra': 'allow'}


class Resource(MCPModel):
    """A known resource that the server is capable of reading."""

    name: str
    uri: str
    description: str | None = None
    mimeType: str | None = None
    size: int | None = None
    annotations: Annotations | None = None

    model_config = {'extra': 'allow'}


class ResourceTemplate(MCPModel):
    """A template description for resources available on the server."""

    name: str
    uriTemplate: str
    description: str | None = None
    mimeType: str | None = None
    annotations: Annotations | None = None

    model_config = {'extra': 'allow'}


class PromptArgument(MCPModel):
    """Describes an argument that a prompt can accept."""

    name: str
    description: str | None = None
    required: bool | None = None

    model_config = {'extra': 'allow'}


class Prompt(MCPModel):
    """A prompt or prompt template that the server offers."""

    name: str
    description: str | None = None
    arguments: list[PromptArgument] | None = None

    model_config = {'extra': 'allow'}


class ToolAnnotations(MCPModel):
    """Additional properties describing a Tool to clients."""

    title: str | None = None
    readOnlyHint: bool | None = None
    idempotentHint: bool | None = None
    destructiveHint: bool | None = None
    openWorldHint: bool | None = None

    model_config = {'extra': 'allow'}


class Tool(MCPModel):
    """Definition for a tool the client can call."""

    name: str
    inputSchema: dict[str, typing.Any]
    description: str | None = None
    annotations: ToolAnnotations | None = None

    model_config = {'extra': 'allow'}


class Root(MCPModel):
    """Represents a root directory or file that the server can operate on."""

    uri: str
    name: str | None = None

    model_config = {'extra': 'allow'}


# Recursive relationship handling
Annotations.model_rebuild()
Tool.model_rebuild()


def jsonrpc_to_mcp(request: jsonrpc.Request) -> InitializeRequest | None:
    LOGGER.debug('Converting %r', request)
    if request.method == INITIALIZE:
        LOGGER.info(request.params)
        return InitializeRequest(**request.params)
    LOGGER.warning('Unknown method: %s', request.method)
    return None
