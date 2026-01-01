<p align="center">
  <a href="https://apitally.io" target="_blank">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://assets.apitally.io/logos/logo-horizontal-new-dark.png">
      <source media="(prefers-color-scheme: light)" srcset="https://assets.apitally.io/logos/logo-horizontal-new-light.png">
      <img alt="Apitally logo" src="https://assets.apitally.io/logos/logo-horizontal-new-light.png" width="220">
    </picture>
  </a>
</p>
<p align="center"><b>API monitoring & analytics made simple</b></p>
<p align="center" style="color: #ccc;">Real-time metrics, request logs, and alerts for your APIs — with just a few lines of code.</p>
<br>
<img alt="Apitally screenshots" src="https://assets.apitally.io/screenshots/overview.png">
<br>

# Apitally SDK for serverless Python runtimes

[![Tests](https://github.com/apitally/apitally-py-serverless/actions/workflows/tests.yaml/badge.svg?event=push)](https://github.com/apitally/apitally-py-serverless/actions)
[![Codecov](https://codecov.io/gh/apitally/apitally-py-serverless/graph/badge.svg?token=q76jRwq7Hi)](https://codecov.io/gh/apitally/apitally-py-serverless)
[![PyPI](https://img.shields.io/pypi/v/apitally-serverless?logo=pypi&logoColor=white&color=%23006dad)](https://pypi.org/project/apitally-serverless/)

This SDK for Apitally currently supports the following web frameworks:

- [FastAPI](https://docs.apitally.io/setup-guides/fastapi-serverless)

The following serverless platforms are supported:

- [Cloudflare Workers](https://docs.apitally.io/setup-guides/cloudflare-workers) (via Logpush)

Learn more about Apitally on our 🌎 [website](https://apitally.io) or check out
the 📚 [documentation](https://docs.apitally.io).

## Key features

### API analytics

Track traffic, error and performance metrics for your API, each endpoint and individual API consumers, allowing you to make informed, data-driven engineering and product decisions.

### Error tracking

Understand which validation rules in your endpoints cause client errors. Capture error details and stack traces for 500 error responses, and have them linked to Sentry issues automatically.

### Request logging

Drill down from insights to individual requests or use powerful filtering to understand how consumers have interacted with your API. Configure exactly what is included in the logs to meet your requirements.

### API monitoring & alerting

Get notified immediately if something isn't right using custom alerts, synthetic uptime checks and heartbeat monitoring. Notifications can be delivered via email, Slack or Microsoft Teams.

## Install

Use `pip` to install and provide your framework of choice as an extra, for
example:

```bash
pip install apitally-serverless[fastapi]
```

The available extras are: `fastapi` and `starlette`.

## Usage

Our comprehensive [setup guides](https://docs.apitally.io/setup-guides) include
all the details you need to get started.

### FastAPI

This is an example of how to add the Apitally middleware to a FastAPI
application. For further instructions, see our
[setup guide for FastAPI](https://docs.apitally.io/frameworks/fastapi-serverless).

```python
from fastapi import FastAPI
from apitally_serverless.fastapi import ApitallyMiddleware

app = FastAPI()
app.add_middleware(
    ApitallyMiddleware,
    log_request_headers=True,
    log_request_body=True,
    log_response_body=True,
)
```

## Getting help

If you need help please [create a new discussion](https://github.com/orgs/apitally/discussions/categories/q-a) on GitHub
or [join our Slack workspace](https://join.slack.com/t/apitally-community/shared_invite/zt-2b3xxqhdu-9RMq2HyZbR79wtzNLoGHrg).

## License

This library is licensed under the terms of the MIT license.
