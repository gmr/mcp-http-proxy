"""Opinionated JSON-RPC models used by the proxy.

Always requires an ID

"""

import typing

import pydantic


class Request(pydantic.BaseModel):
    jsonrpc: str = '2.0'
    method: str
    params: dict[str, typing.Any] | None = None
    id: str | int


class Notification(pydantic.BaseModel):
    jsonrpc: str = '2.0'
    method: str
    params: None = None


class Error(pydantic.BaseModel):
    code: int
    message: str
    data: typing.Any | None = None


class Response(pydantic.BaseModel):

    jsonrpc: str = '2.0'
    result: typing.Any | None = None
    error: Error | None = None
    id: str | int

    def model_dump(self, *args, **kwargs) -> dict[str, typing.Any]:
        """Dump the model, stripping None values"""
        kwargs['exclude_none'] = True
        return super().model_dump(*args, **kwargs)


Batch = list[Request | Notification | Response]
