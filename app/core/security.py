from __future__ import annotations

import structlog
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = structlog.get_logger(__name__)

_OPEN_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Validates X-API-Key header on all API routes.

    Skips validation for health check and docs endpoints.
    Returns 401 for missing key; 403 for invalid key.
    """

    async def dispatch(  # type: ignore[override]
        self, request: Request, call_next: object
    ) -> object:
        path = request.url.path

        if path in _OPEN_PATHS or not path.startswith("/api/"):
            return await call_next(request)  # type: ignore[misc]

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            logger.warning("api_key.missing", path=path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing X-API-Key header"},
            )

        valid_keys: list[str] = list(settings.api.api_keys) + [
            settings.api.admin_api_key
        ]
        if api_key not in valid_keys:
            logger.warning("api_key.invalid", path=path)
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid API key"},
            )

        logger.debug("api_key.valid", path=path)
        return await call_next(request)  # type: ignore[misc]


def require_admin_key(request: Request) -> None:
    """FastAPI dependency: asserts the request carries the admin API key.

    Args:
        request: The incoming FastAPI request.

    Raises:
        HTTPException: 403 if the key is not the admin key.
    """
    api_key = request.headers.get("X-API-Key", "")
    if api_key != settings.api.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin API key required",
        )
