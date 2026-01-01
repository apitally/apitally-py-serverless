from dataclasses import dataclass, field
from typing import Any, TypedDict


class ApitallyConfigKwargs(TypedDict, total=False):
    enabled: bool
    log_request_headers: bool
    log_request_body: bool
    log_response_headers: bool
    log_response_body: bool
    mask_headers: list[str]
    mask_body_fields: list[str]
    exclude_paths: list[str]


@dataclass
class ApitallyConfig:
    enabled: bool = True
    log_request_headers: bool = False
    log_request_body: bool = False
    log_response_headers: bool = True
    log_response_body: bool = False
    mask_headers: list[str] = field(default_factory=list)
    mask_body_fields: list[str] = field(default_factory=list)
    exclude_paths: list[str] = field(default_factory=list)

    @classmethod
    def from_kwargs(cls, kwargs: ApitallyConfigKwargs) -> "ApitallyConfig":
        config_kwargs: dict[str, Any] = {k: v for k, v in kwargs.items() if k in cls.__dataclass_fields__}
        return ApitallyConfig(**config_kwargs)
