from apitally_serverless.starlette import ApitallyMiddleware as _ApitallyMiddlewareForStarlette
from apitally_serverless.starlette import set_consumer


__all__ = ["ApitallyMiddleware", "set_consumer"]


class ApitallyMiddleware(_ApitallyMiddlewareForStarlette):
    """
    Apitally middleware for FastAPI applications in serverless environments.

    For more information, see:
    - Setup guide: https://docs.apitally.io/frameworks/fastapi-serverless
    - Reference: https://docs.apitally.io/reference/python-serverless
    """

    pass
