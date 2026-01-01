# Apitally Serverless Python SDK

Simple API monitoring & analytics for REST APIs running on serverless platforms (e.g. AWS Lambda).

## Installation

```bash
pip install apitally-serverless[fastapi]
```

## Usage with FastAPI

```python
from fastapi import FastAPI
from apitally_serverless.fastapi import ApitallyMiddleware, ApitallyConfig

app = FastAPI()

config = ApitallyConfig(
    enabled=True,
    log_request_headers=True,
    log_request_body=True,
    log_response_headers=True,
    log_response_body=True,
)

app.add_middleware(ApitallyMiddleware, config=config)
```

## Documentation

For more information, see the [Apitally documentation](https://docs.apitally.io).
