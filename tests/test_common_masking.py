import json
from typing import Any, cast

from apitally_serverless.common.config import ApitallyConfig
from apitally_serverless.common.masking import MASKED, DataMasker
from apitally_serverless.common.output import OutputDataDict


def create_config(**kwargs: Any) -> ApitallyConfig:
    defaults: dict[str, Any] = {
        "enabled": True,
        "log_request_headers": True,
        "log_request_body": True,
        "log_response_headers": True,
        "log_response_body": True,
    }
    return ApitallyConfig(**{**defaults, **kwargs})


def create_output_data(
    request: dict[str, Any] | None = None,
    response: dict[str, Any] | None = None,
) -> OutputDataDict:
    request_dict = {
        "path": "/test",
        "headers": [("content-type", "application/json")],
        "size": None,
        "consumer": None,
        "body": b'{"username":"john"}',
    }
    if request:
        request_dict.update(request)
    response_dict = {
        "response_time": 0.1,
        "status_code": 200,
        "headers": [("content-type", "application/json")],
        "size": None,
        "body": b'{"status":"ok"}',
    }
    if response:
        response_dict.update(response)
    return cast(
        OutputDataDict,
        {
            "instance_uuid": "00000000-0000-0000-0000-000000000000",
            "request_uuid": "00000000-0000-0000-0000-000000000000",
            "request": request_dict,
            "response": response_dict,
            "startup": None,
            "consumer": None,
            "validation_errors": None,
            "exception": None,
            "exclude": False,
        },
    )


def test_exclude_paths():
    masker = DataMasker(create_config(exclude_paths=[r"/custom-excluded$"]))

    # Builtin pattern match
    data = create_output_data(request={"path": "/healthz"})
    masker.apply_masking(data)
    assert data["exclude"] is True
    assert data["request"]["headers"] is None
    assert data["request"]["body"] is None

    # Custom pattern match
    data = create_output_data(request={"path": "/api/custom-excluded"})
    masker.apply_masking(data)
    assert data["exclude"] is True

    # Non-excluded path
    data = create_output_data(request={"path": "/api/other"})
    masker.apply_masking(data)
    assert data["exclude"] is False


def test_headers_not_logged_when_disabled():
    masker = DataMasker(create_config(log_request_headers=False, log_response_headers=False))
    data = create_output_data()

    masker.apply_masking(data)

    assert data["request"]["headers"] is None
    assert data["response"]["headers"] is None


def test_bodies_not_logged_when_disabled():
    masker = DataMasker(create_config(log_request_body=False, log_response_body=False))
    data = create_output_data()

    masker.apply_masking(data)

    assert data["request"]["body"] is None
    assert data["response"]["body"] is None


def test_mask_headers():
    masker = DataMasker(create_config(mask_headers=[r"x-custom"]))
    data = create_output_data(
        request={
            "headers": [
                ("accept", "application/json"),
                ("authorization", "Bearer token"),  # builtin pattern
                ("x-custom-header", "secret"),  # custom pattern
            ],
        }
    )

    masker.apply_masking(data)

    headers = data["request"]["headers"]
    assert headers is not None
    assert ("accept", "application/json") in headers
    assert ("authorization", MASKED) in headers
    assert ("x-custom-header", MASKED) in headers


def test_mask_body_fields():
    masker = DataMasker(create_config(mask_body_fields=[r"custom"]))
    request_body = {
        "username": "john",
        "password": "secret",  # builtin pattern
        "custom": "value",  # custom pattern
        "nested": {"token": "nested"},  # builtin pattern, nested
        "array": [{"auth": "array"}],  # builtin pattern, in array
    }
    data = create_output_data(
        request={
            "headers": [("content-type", "application/json")],
            "body": json.dumps(request_body).encode(),
        }
    )

    masker.apply_masking(data)

    body = data["request"]["body"]
    assert body is not None
    masked = json.loads(body.decode())
    assert masked["username"] == "john"
    assert masked["password"] == MASKED
    assert masked["custom"] == MASKED
    assert masked["nested"]["token"] == MASKED
    assert masked["array"][0]["auth"] == MASKED


def test_mask_body_fields_ndjson():
    masker = DataMasker(create_config())
    lines = [
        {"username": "john", "password": "secret1"},
        {"username": "jane", "token": "abc123"},
    ]
    data = create_output_data(
        request={
            "headers": [("content-type", "application/x-ndjson")],
            "body": "\n".join(json.dumps(line) for line in lines).encode(),
        }
    )

    masker.apply_masking(data)

    body = data["request"]["body"]
    assert body is not None
    masked_lines = [json.loads(line) for line in body.decode().split("\n")]
    assert masked_lines[0]["username"] == "john"
    assert masked_lines[0]["password"] == MASKED
    assert masked_lines[1]["token"] == MASKED
