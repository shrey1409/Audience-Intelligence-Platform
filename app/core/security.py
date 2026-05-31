"""API key middleware — validates X-API-Key header on every incoming request."""

from __future__ import annotations

import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that enforces X-API-Key authentication.

    Requests to /api/v1/health pass through without a key so monitoring systems
    can check liveness without credentials.

    Returns HTTP 401 with a JSON body for missing or invalid keys.
    """

    _EXEMPT_PATHS: frozenset[str] = frozenset({"/api/v1/health"})

    async def dispatch(self, request: Request, call_next: object) -> Response:
        """Validate the X-API-Key header before forwarding the request.

        Args:
            request: The incoming Starlette request.
            call_next: The next middleware or endpoint handler.

        Returns:
            The endpoint response if the key is valid, or a 401 JSON response.
        """
        if request.url.path in self._EXEMPT_PATHS:
            return await call_next(request)  # type: ignore[misc]

        api_key = request.headers.get("X-API-Key", "")
        if api_key not in settings.api.api_keys:
            body = json.dumps({"detail": "Invalid or missing API key"}).encode()
            return Response(
                content=body,
                status_code=401,
                media_type="application/json",
            )

        return await call_next(request)  # type: ignore[misc]
