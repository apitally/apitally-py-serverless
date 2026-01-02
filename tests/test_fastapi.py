import base64
import gzip
import json
from typing import Any

import pytest
from fastapi import FastAPI, Query, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel

from apitally_serverless.fastapi import ApitallyMiddleware, set_consumer


def get_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        ApitallyMiddleware,
        enabled=True,
        log_request_headers=True,
        log_request_body=True,
        log_response_headers=True,
        log_response_body=True,
    )

    @app.get("/hello")
    def get_hello(request: Request, name: str = Query(min_length=2), age: int = Query(ge=18)):
        set_consumer(request, "test", name="Test", group="Test")
        return {"message": f"Hello {name}! You are {age} years old!"}

    @app.get("/hello/{id}")
    def get_hello_with_id(id: str):
        return {"message": f"Hello {id}!"}

    class HelloBody(BaseModel):
        name: str
        age: int

    @app.post("/hello")
    def post_hello(body: HelloBody):
        return {"message": f"Hello {body.name}! You are {body.age} years old!"}

    @app.get("/error")
    def get_error():
        raise ValueError("test error")

    return app


def get_logged_data(capsys: pytest.CaptureFixture[str]) -> dict[str, Any] | None:
    captured = capsys.readouterr()
    for line in captured.out.split("\n"):
        if line.startswith("apitally:"):
            encoded = line.replace("apitally:", "")
            compressed = base64.b64decode(encoded)
            decompressed = gzip.decompress(compressed)
            return json.loads(decompressed.decode("utf-8"))
    return None


@pytest.fixture
def client() -> TestClient:
    return TestClient(get_app(), raise_server_exceptions=False)


def test_logs_get_request(client: TestClient, capsys: pytest.CaptureFixture[str]):
    response = client.get("/hello?name=John&age=20")
    assert response.status_code == 200

    data = get_logged_data(capsys)
    assert data is not None
    assert data["instance_uuid"] is not None
    assert data["request_uuid"] is not None
    assert data["consumer"] is not None
    assert data["consumer"]["name"] == "Test"
    assert data["consumer"]["group"] == "Test"
    assert data["request"]["path"] == "/hello"
    assert data["request"]["consumer"] == "test"
    assert any(h[0] == "content-type" for h in data["response"]["headers"])
    assert data["response"]["size"] is not None
    assert data["response"]["size"] > 0
    assert data["response"]["body"] is not None

    body = base64.b64decode(data["response"]["body"]).decode("utf-8")
    assert "Hello John" in body


def test_logs_get_request_with_path_param(client: TestClient, capsys: pytest.CaptureFixture[str]):
    response = client.get("/hello/123")
    assert response.status_code == 200

    data = get_logged_data(capsys)
    assert data is not None
    assert data["request"]["path"] == "/hello/{id}"


def test_logs_post_request_with_json_body(client: TestClient, capsys: pytest.CaptureFixture[str]):
    body = {"name": "John", "age": 20}
    response = client.post("/hello", json=body)
    assert response.status_code == 200

    data = get_logged_data(capsys)
    assert data is not None
    assert data["request"]["path"] == "/hello"
    assert any(h == ["content-type", "application/json"] for h in data["request"]["headers"])
    assert data["request"]["size"] is not None
    assert data["request"]["size"] > 0
    assert data["request"]["body"] is not None

    request_body = base64.b64decode(data["request"]["body"]).decode("utf-8")
    assert "John" in request_body


def test_logs_error_response(client: TestClient, capsys: pytest.CaptureFixture[str]):
    response = client.get("/error")
    assert response.status_code == 500

    data = get_logged_data(capsys)
    assert data is not None
    assert data["request"]["path"] == "/error"
    assert data["exception"] is not None
    assert data["exception"]["type"] == "builtins.ValueError"
    assert data["exception"]["msg"] == "test error"
    assert data["exception"]["traceback"] is not None
    assert "test_fastapi.py" in data["exception"]["traceback"]


def test_logs_unhandled_request(client: TestClient, capsys: pytest.CaptureFixture[str]):
    response = client.get("/unhandled")
    assert response.status_code == 404

    data = get_logged_data(capsys)
    assert data is not None
    assert "path" not in data["request"]
    assert data["response"]["status_code"] == 404


def test_captures_validation_errors(client: TestClient, capsys: pytest.CaptureFixture[str]):
    response = client.get("/hello?name=X&age=17")
    assert response.status_code == 422

    data = get_logged_data(capsys)
    assert data is not None
    assert data["validation_errors"] is not None
    assert len(data["validation_errors"]) == 2

    locs = [e["loc"] for e in data["validation_errors"]]
    assert ["query", "name"] in locs
    assert ["query", "age"] in locs
