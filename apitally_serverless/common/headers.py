from typing import Iterable


SUPPORTED_CONTENT_TYPES = [
    "application/json",
    "application/ld+json",
    "application/problem+json",
    "application/vnd.api+json",
    "application/x-ndjson",
    "text/plain",
    "text/html",
]


def convert_headers(
    headers: Iterable[tuple[str, str]] | None,
) -> list[tuple[str, str]]:
    if headers is None:
        return []
    return [(k.lower(), v) for k, v in headers]


def parse_content_length(
    content_length: str | bytes | int | None,
) -> int | None:
    if content_length is None:
        return None
    if isinstance(content_length, int):
        return content_length
    if isinstance(content_length, bytes):
        content_length = content_length.decode()
    try:
        return int(content_length)
    except ValueError:
        return None


def is_supported_content_type(content_type: str | None) -> bool:
    if not content_type:
        return False
    return any(content_type.startswith(t) for t in SUPPORTED_CONTENT_TYPES)
