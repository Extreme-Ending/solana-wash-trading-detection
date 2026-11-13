"""ASGI boundary controls for authentication, rate and body size."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import Callable

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from solana_risk.api.auth import authenticate_authorization_header
from solana_risk.api.errors import ApiError, api_error_response


PROTECTED_PATHS = frozenset({"/v1/features/preview", "/v1/score"})


class PerInstanceRateLimiter:
    """Bound an authorized UID within one process; not a distributed quota."""

    def __init__(
        self,
        *,
        requests: int,
        window_seconds: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.requests = requests
        self.window_seconds = window_seconds
        self._clock = clock
        self._entries: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, uid: str) -> int | None:
        """Return a Retry-After delay when the current request exceeds the limit."""

        now = self._clock()
        cutoff = now - self.window_seconds
        async with self._lock:
            entries = self._entries[uid]
            while entries and entries[0] <= cutoff:
                entries.popleft()
            if len(entries) >= self.requests:
                return max(1, int(entries[0] + self.window_seconds - now) + 1)
            entries.append(now)
        return None


class ProtectedRouteMiddleware:
    """Reject unauthenticated protected requests before route/body processing."""

    def __init__(self, app: ASGIApp, *, rate_limiter: PerInstanceRateLimiter) -> None:
        self.app = app
        self.rate_limiter = rate_limiter

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope.get("path") not in PROTECTED_PATHS
            or scope.get("method") == "OPTIONS"
        ):
            await self.app(scope, receive, send)
            return

        authorization_values = [
            value.decode("latin-1")
            for key, value in scope.get("headers", [])
            if key.lower() == b"authorization"
        ]
        authorization = authorization_values[0] if len(authorization_values) == 1 else None
        request = Request(scope)
        try:
            if len(authorization_values) > 1:
                raise ApiError(
                    status_code=401,
                    code="INVALID_TOKEN",
                    message="The authentication token is invalid.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            claims = await authenticate_authorization_header(request, authorization)
            uid = claims.get("uid")
            if not isinstance(uid, str):
                raise ApiError(
                    status_code=401,
                    code="INVALID_TOKEN",
                    message="The authentication token is invalid.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            retry_after = await self.rate_limiter.check(uid)
            if retry_after is not None:
                raise ApiError(
                    status_code=429,
                    code="RATE_LIMIT_EXCEEDED",
                    message="The per-instance request limit has been exceeded.",
                    details={"retry_after_seconds": retry_after},
                    headers={"Retry-After": str(retry_after)},
                )
            state = scope.setdefault("state", {})
            if not isinstance(state, dict):
                raise ApiError(
                    status_code=503,
                    code="AUTH_MIDDLEWARE_UNAVAILABLE",
                    message="Protected-route authentication is unavailable.",
                )
            state["authorized_user"] = claims
        except ApiError as exc:
            response = api_error_response(exc)
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


class RequestSizeLimitMiddleware:
    """Reject oversized request bodies before JSON/Pydantic processing."""

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return

        content_length = next(
            (
                value
                for key, value in scope.get("headers", [])
                if key.lower() == b"content-length"
            ),
            None,
        )
        if content_length is not None:
            try:
                if int(content_length) > self.max_bytes:
                    await self._reject(scope, receive, send)
                    return
            except ValueError:
                pass

        messages: list[Message] = []
        total = 0
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] == "http.request":
                total += len(message.get("body", b""))
                if total > self.max_bytes:
                    await self._reject(scope, receive, send)
                    return
                if not message.get("more_body", False):
                    break
            elif message["type"] == "http.disconnect":
                break

        index = 0

        async def replay_receive() -> Message:
            nonlocal index
            if index < len(messages):
                message = messages[index]
                index += 1
                return message
            return {"type": "http.disconnect"}

        await self.app(scope, replay_receive, send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            status_code=413,
            content={
                "error": {
                    "code": "REQUEST_TOO_LARGE",
                    "message": "Request body exceeds the configured byte limit.",
                    "details": {"max_request_bytes": self.max_bytes},
                }
            },
        )
        await response(scope, receive, send)
