import base64
import gzip
import json
from typing import Any, TypedDict

from typing_extensions import NotRequired


class ConsumerDict(TypedDict):
    identifier: str
    name: str | None
    group: str | None


class StartupDataDict(TypedDict):
    paths: list[dict[str, str]]
    versions: dict[str, str]
    client: str


class RequestDataDict(TypedDict):
    path: str | None
    headers: list[tuple[str, str]] | None
    size: int | None
    consumer: str | None
    body: bytes | None


class ResponseDataDict(TypedDict):
    response_time: float
    status_code: int
    headers: list[tuple[str, str]] | None
    size: int | None
    body: bytes | None


class ValidationErrorDict(TypedDict):
    loc: list[str]
    msg: str
    type: str


class OutputDataDict(TypedDict):
    instance_uuid: str
    request_uuid: str
    startup: StartupDataDict | None
    consumer: ConsumerDict | None
    request: RequestDataDict
    response: ResponseDataDict
    validation_errors: list[ValidationErrorDict] | None
    exclude: NotRequired[bool]


def _json_default(obj: Any) -> Any:
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("ascii")
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _skip_empty_values(data: dict[str, Any]) -> dict[str, Any]:
    return {
        k: _skip_empty_values(v) if isinstance(v, dict) else v
        for k, v in data.items()
        if v is not None and v != [] and v != {} and v != "" and v is not False
    }


def _create_log_message(data: OutputDataDict) -> str:
    cleaned = _skip_empty_values(dict(data))
    serialized = json.dumps(cleaned, separators=(",", ":"), default=_json_default)
    compressed = gzip.compress(serialized.encode("utf-8"))
    encoded = base64.b64encode(compressed).decode("ascii")
    return f"apitally:{encoded}"


def log_data(data: OutputDataDict) -> None:
    msg = _create_log_message(data)

    if len(msg) > 15_000:
        # Cloudflare Workers Logpush limits the total length of all exception and log messages to 16,384 characters,
        # so we need to keep the logged message well below that limit.
        data["request"]["body"] = None
        data["response"]["body"] = None
        msg = _create_log_message(data)

    print(msg)
