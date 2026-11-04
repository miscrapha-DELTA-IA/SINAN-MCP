"""Small, bounded admission-control layer for the *synthetic-only* public MCP.

This is a per-PROCESS global token bucket and concurrency guard. It does not
claim per-user quotas behind a TLS reverse proxy, protect across replicas, or
replace provider/edge protection. Deliberately ignores all X-Forwarded-* headers.
No user identifiers, IP addresses, request bodies or health data are stored.
"""
from __future__ import annotations

import math
import os
import threading
import time
from collections.abc import Callable

from starlette.responses import JSONResponse

DEFAULT_RATE_PER_MINUTE = 300
DEFAULT_MAX_IN_FLIGHT = 16


def bounded_int_env(name: str, default: int, upper: int) -> int:
    """Reject invalid or disabled protective configuration at startup."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} deve ser inteiro positivo") from exc
    if not 1 <= value <= upper:
        raise ValueError(f"{name} fora do intervalo seguro: 1..{upper}")
    return value


class PublicAdmissionGuard:
    """Global in-memory throttling for /mcp; never parse forwarded client IPs."""

    def __init__(
        self,
        app,
        *,
        requests_per_minute: int = DEFAULT_RATE_PER_MINUTE,
        max_in_flight: int = DEFAULT_MAX_IN_FLIGHT,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not 1 <= requests_per_minute <= 12000:
            raise ValueError("requests_per_minute deve estar entre 1 e 12000")
        if not 1 <= max_in_flight <= 128:
            raise ValueError("max_in_flight deve estar entre 1 e 128")
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.max_in_flight = max_in_flight
        self._clock = clock
        self._lock = threading.Lock()
        self._tokens = float(requests_per_minute)
        self._updated = clock()
        self._in_flight = 0

    async def __call__(self, scope, receive, send) -> None:
        # Lifespan must always be forwarded: the MCP session manager lives there.
        if scope.get("type") != "http" or scope.get("path") not in {"/mcp", "/mcp/"}:
            await self.app(scope, receive, send)
            return

        admitted = False
        retry_after = 1
        with self._lock:
            now = self._clock()
            elapsed = max(0.0, now - self._updated)
            self._updated = now
            self._tokens = min(
                float(self.requests_per_minute),
                self._tokens + elapsed * (self.requests_per_minute / 60.0),
            )
            if self._in_flight >= self.max_in_flight:
                retry_after = 1
            elif self._tokens < 1.0:
                retry_after = max(
                    1, math.ceil((1.0 - self._tokens) * 60.0 / self.requests_per_minute)
                )
            else:
                self._tokens -= 1.0
                self._in_flight += 1
                admitted = True

        if not admitted:
            response = JSONResponse(
                {"error": "too_many_requests", "retry_after_seconds": retry_after},
                status_code=429,
                headers={
                    "Retry-After": str(retry_after),
                    "Cache-Control": "no-store",
                    "X-Content-Type-Options": "nosniff",
                },
            )
            await response(scope, receive, send)
            return
        try:
            await self.app(scope, receive, send)
        finally:
            with self._lock:
                self._in_flight -= 1
