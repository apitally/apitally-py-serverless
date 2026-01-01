import json
import re
from typing import Any

from apitally_serverless.common.config import ApitallyConfig
from apitally_serverless.common.output import OutputDataDict


MASKED = "******"

EXCLUDE_PATH_PATTERNS = [
    r"/_?healthz?$",
    r"/_?health[_-]?checks?$",
    r"/_?heart[_-]?beats?$",
    r"/ping$",
    r"/ready$",
    r"/live$",
]
MASK_HEADER_PATTERNS = [
    r"auth",
    r"api-?key",
    r"secret",
    r"token",
    r"cookie",
]
MASK_BODY_FIELD_PATTERNS = [
    r"password",
    r"pwd",
    r"token",
    r"secret",
    r"auth",
    r"card[-_ ]?number",
    r"ccv",
    r"ssn",
]


class DataMasker:
    def __init__(self, config: ApitallyConfig) -> None:
        self.config = config
        self.exclude_path_patterns = [
            re.compile(p, re.I) for p in dict.fromkeys(config.exclude_paths + EXCLUDE_PATH_PATTERNS)
        ]
        self.mask_header_patterns = [
            re.compile(p, re.I) for p in dict.fromkeys(config.mask_headers + MASK_HEADER_PATTERNS)
        ]
        self.mask_body_field_patterns = [
            re.compile(p, re.I) for p in dict.fromkeys(config.mask_body_fields + MASK_BODY_FIELD_PATTERNS)
        ]

    def apply_masking(self, data: OutputDataDict) -> None:
        request = data["request"]
        response = data["response"]

        # Check if path is excluded
        if self._should_exclude_path(request["path"]):
            request["headers"] = None
            request["body"] = None
            response["headers"] = None
            response["body"] = None
            data["exclude"] = True
            return

        # Drop request and response bodies if logging is disabled
        if not self.config.log_request_body and request["body"] is not None:
            request["body"] = None
        if not self.config.log_response_body and response["body"] is not None:
            response["body"] = None

        # Mask request and response body fields
        if request["body"] is not None:
            request["body"] = self._mask_body_bytes(request["body"], request["headers"])
        if response["body"] is not None:
            response["body"] = self._mask_body_bytes(response["body"], response["headers"])

        # Mask request and response headers
        if self.config.log_request_headers and request["headers"] is not None:
            request["headers"] = self._mask_headers(request["headers"])
        else:
            request["headers"] = None

        if self.config.log_response_headers and response["headers"] is not None:
            response["headers"] = self._mask_headers(response["headers"])
        else:
            response["headers"] = None

    def _should_exclude_path(self, path: str | None) -> bool:
        return path is not None and any(p.search(path) for p in self.exclude_path_patterns)

    def _should_mask_header(self, name: str) -> bool:
        return any(p.search(name) for p in self.mask_header_patterns)

    def _should_mask_body_field(self, name: str) -> bool:
        return any(p.search(name) for p in self.mask_body_field_patterns)

    def _mask_headers(self, headers: list[tuple[str, str]]) -> list[tuple[str, str]]:
        return [(k, MASKED if self._should_mask_header(k) else v) for k, v in headers]

    def _mask_body_bytes(self, body: bytes, headers: list[tuple[str, str]] | None) -> bytes:
        content_type = self._get_content_type(headers)

        try:
            if content_type is None or "json" in content_type.lower():
                parsed = json.loads(body.decode("utf-8"))
                masked = self._mask_body(parsed)
                return json.dumps(masked, separators=(",", ":")).encode("utf-8")
            elif "ndjson" in content_type.lower():
                lines = body.decode("utf-8").split("\n")
                masked_lines = []
                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            parsed = json.loads(line)
                            masked = self._mask_body(parsed)
                            masked_lines.append(json.dumps(masked, separators=(",", ":")))
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            masked_lines.append(line)
                return "\n".join(masked_lines).encode("utf-8")
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        return body

    def _mask_body(self, data: Any) -> Any:
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, str) and self._should_mask_body_field(key):
                    result[key] = MASKED
                else:
                    result[key] = self._mask_body(value)
            return result
        if isinstance(data, list):
            return [self._mask_body(item) for item in data]
        return data

    def _get_content_type(self, headers: list[tuple[str, str]] | None) -> str | None:
        if not headers:
            return None
        for k, v in headers:
            if k.lower() == "content-type":
                return v
        return None
