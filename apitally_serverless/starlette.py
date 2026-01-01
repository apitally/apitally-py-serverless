import json
import sys
import time
from contextlib import suppress
from importlib.metadata import PackageNotFoundError, version
from uuid import uuid4

from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.routing import BaseRoute, Match, Router
from starlette.schemas import SchemaGenerator
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from typing_extensions import Unpack

from apitally_serverless.common.config import ApitallyConfig, ApitallyConfigKwargs
from apitally_serverless.common.consumers import ApitallyConsumer
from apitally_serverless.common.headers import convert_headers, is_supported_content_type, parse_content_length
from apitally_serverless.common.masking import DataMasker
from apitally_serverless.common.output import (
    OutputDataDict,
    StartupDataDict,
    ValidationErrorDict,
    log_data,
)


__all__ = ["ApitallyMiddleware", "set_consumer"]

MAX_BODY_SIZE = 10_000
BODY_TOO_LARGE = b"<body too large>"


class ApitallyMiddleware:
    """
    Apitally middleware for Starlette applications in serverless environments.

    For more information, see:
    - Setup guide: https://docs.apitally.io/frameworks/starlette-serverless
    - Reference: https://docs.apitally.io/reference/python-serverless
    """

    def __init__(
        self,
        app: ASGIApp,
        **kwargs: Unpack[ApitallyConfigKwargs],
    ) -> None:
        self.app = app
        self.config = ApitallyConfig.from_kwargs(kwargs)
        self.masker = DataMasker(self.config)
        self.instance_uuid = str(uuid4())
        self.is_first_request = True

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self.config.enabled or scope["type"] != "http" or scope["method"] == "OPTIONS":  # pragma: no cover
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        request = Request(scope, receive, send)
        request_size = parse_content_length(request.headers.get("Content-Length"))
        request_content_type = request.headers.get("Content-Type")
        request_body = b""
        request_body_too_large = request_size is not None and request_size > MAX_BODY_SIZE

        response_status = 0
        response_time: float | None = None
        response_headers = Headers()
        response_body = b""
        response_body_too_large = False
        response_size: int | None = None
        response_chunked = False
        response_content_type: str | None = None

        async def receive_wrapper() -> Message:
            nonlocal request_body, request_body_too_large

            message = await receive()
            if message["type"] == "http.request":
                if (
                    self.config.log_request_body
                    and not request_body_too_large
                    and is_supported_content_type(request_content_type)
                ):
                    request_body += message.get("body", b"")
                    if len(request_body) > MAX_BODY_SIZE:
                        request_body_too_large = True
                        request_body = b""
            return message

        async def send_wrapper(message: Message) -> None:
            nonlocal response_time, response_status, response_headers, response_body
            nonlocal response_body_too_large, response_chunked, response_content_type, response_size

            if message["type"] == "http.response.start":
                response_time = time.perf_counter() - start_time
                response_status = message["status"]
                response_headers = Headers(scope=message)
                response_chunked = (
                    response_headers.get("Transfer-Encoding") == "chunked" or "Content-Length" not in response_headers
                )
                response_content_type = response_headers.get("Content-Type")
                response_size = (
                    parse_content_length(response_headers.get("Content-Length")) if not response_chunked else 0
                )
                response_body_too_large = response_size is not None and response_size > MAX_BODY_SIZE

            elif message["type"] == "http.response.body":
                if response_chunked and response_size is not None:
                    response_size += len(message.get("body", b""))

                should_capture = (
                    (self.config.log_response_body or response_status == 422)
                    and is_supported_content_type(response_content_type)
                    and not response_body_too_large
                )
                if should_capture:
                    response_body += message.get("body", b"")
                    if len(response_body) > MAX_BODY_SIZE:
                        response_body_too_large = True
                        response_body = b""

            await send(message)

        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        finally:
            if response_time is None:
                response_time = time.perf_counter() - start_time

            if request_body_too_large:
                request_body = BODY_TOO_LARGE
            if response_body_too_large:
                response_body = BODY_TOO_LARGE

            # Build startup data on first request
            startup_data: StartupDataDict | None = None
            if self.is_first_request:
                self.is_first_request = False
                startup_data = {
                    "paths": _get_endpoints(self.app),
                    "versions": _get_versions(),
                    "client": "python-serverless:starlette",
                }

            consumer = _get_consumer(request)
            validation_errors = (
                _extract_validation_errors(response_body) if response_status == 422 and response_body else None
            )

            data: OutputDataDict = {
                "instance_uuid": self.instance_uuid,
                "request_uuid": str(uuid4()),
                "startup": startup_data,
                "consumer": {
                    "identifier": consumer.identifier,
                    "name": consumer.name,
                    "group": consumer.group,
                }
                if consumer and (consumer.name or consumer.group)
                else None,
                "request": {
                    "path": _get_path(request),
                    "headers": convert_headers(request.headers.items()),
                    "size": request_size,
                    "consumer": consumer.identifier if consumer else None,
                    "body": request_body or None,
                },
                "response": {
                    "response_time": response_time,
                    "status_code": response_status,
                    "headers": convert_headers(response_headers.items()),
                    "size": response_size,
                    "body": response_body or None,
                },
                "validation_errors": validation_errors,
            }

            self.masker.apply_masking(data)
            log_data(data)


def set_consumer(request: Request, identifier: str, name: str | None = None, group: str | None = None) -> None:
    """Set the consumer for the current request."""
    request.state.apitally_consumer = ApitallyConsumer(identifier, name=name, group=group)


def _get_consumer(request: Request) -> ApitallyConsumer | None:
    if hasattr(request.state, "apitally_consumer") and isinstance(request.state.apitally_consumer, ApitallyConsumer):
        return request.state.apitally_consumer
    return None


def _get_path(request: Request, routes: list[BaseRoute] | None = None) -> str | None:
    if routes is None:
        routes = request.app.routes
    for route in routes:
        if hasattr(route, "routes"):
            path = _get_path(request, routes=route.routes)
            if path is not None:
                return path
        elif hasattr(route, "path"):
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return request.scope.get("root_path", "") + route.path
    return None


def _get_endpoints(app: ASGIApp) -> list[dict[str, str]]:
    routes = _get_routes(app)
    schemas = SchemaGenerator({})
    endpoints = schemas.get_endpoints(routes)
    return [{"method": e.http_method, "path": e.path} for e in endpoints]


def _get_routes(app: ASGIApp | Router) -> list[BaseRoute]:
    if isinstance(app, Router):
        return app.routes
    elif hasattr(app, "app"):
        return _get_routes(app.app)
    return []  # pragma: no cover


def _get_versions() -> dict[str, str]:
    versions = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    for package in ["apitally-serverless", "fastapi", "starlette"]:
        with suppress(PackageNotFoundError):
            versions[package] = version(package)
    return versions


def _extract_validation_errors(response_body: bytes) -> list[ValidationErrorDict] | None:
    """Extract Pydantic validation errors from a 422 response body."""
    try:
        body = json.loads(response_body.decode("utf-8"))
        if isinstance(body, dict) and "detail" in body and isinstance(body["detail"], list):
            errors: list[ValidationErrorDict] = []
            for detail in body["detail"]:
                if isinstance(detail, dict):
                    loc = detail.get("loc", [])
                    msg = detail.get("msg", "")
                    error_type = detail.get("type", "")
                    errors.append(
                        {
                            "loc": [str(item) for item in loc],
                            "msg": str(msg),
                            "type": str(error_type),
                        }
                    )
            return errors
    except (json.JSONDecodeError, UnicodeDecodeError):  # pragma: no cover
        pass

    return None
