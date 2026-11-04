"""Synthetic-only admission tests. No sockets, data, credentials or downloads."""
from __future__ import annotations

import asyncio
import json
from starlette.responses import JSONResponse
import pytest

from sinan_mcp.public_admission import PublicAdmissionGuard, bounded_int_env


async def _request(app, *, path="/mcp", headers=None):
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await app(
        {"type": "http", "path": path, "method": "POST", "headers": headers or []},
        receive, send,
    )
    head = next(m for m in messages if m["type"] == "http.response.start")
    body = b"".join(
        m.get("body", b"") for m in messages if m["type"] == "http.response.body"
    )
    return head["status"], dict(head["headers"]), body


async def _ok(scope, receive, send):
    await JSONResponse({"ok": True})(scope, receive, send)


def test_global_token_bucket_and_retry_after():
    now = [100.0]
    guard = PublicAdmissionGuard(_ok, requests_per_minute=2,
                                 max_in_flight=2, clock=lambda: now[0])

    async def scenario():
        assert (await _request(guard))[0] == 200
        assert (await _request(guard))[0] == 200
        status, headers, body = await _request(guard)
        assert status == 429
        assert headers[b"retry-after"] == b"30"
        assert headers[b"cache-control"] == b"no-store"
        assert json.loads(body)["error"] == "too_many_requests"
        now[0] += 30
        assert (await _request(guard))[0] == 200

    asyncio.run(scenario())


def test_headers_cannot_bypass_shared_budget():
    guard = PublicAdmissionGuard(_ok, requests_per_minute=1)
    async def scenario():
        assert (await _request(guard, headers=[(b"x-forwarded-for", b"1.2.3.4")]))[0] == 200
        assert (await _request(guard, headers=[(b"x-forwarded-for", b"9.8.7.6")]))[0] == 429
    asyncio.run(scenario())


def test_concurrency_limit_releases_slot_on_completion():
    entered = asyncio.Event()
    release = asyncio.Event()

    async def slow(scope, receive, send):
        entered.set()
        await release.wait()
        await _ok(scope, receive, send)

    guard = PublicAdmissionGuard(slow, requests_per_minute=10, max_in_flight=1)

    async def scenario():
        first = asyncio.create_task(_request(guard))
        await entered.wait()
        code, headers, _ = await _request(guard)
        assert code == 429
        assert headers[b"retry-after"] == b"1"
        release.set()
        assert (await first)[0] == 200
        assert (await _request(guard))[0] == 200
    asyncio.run(scenario())


def test_health_and_lifespan_forward_without_affecting_mcp_quota():
    scopes = []
    async def capture(scope, receive, send):
        scopes.append(scope["type"] + ":" + scope.get("path", ""))
        if scope["type"] == "http":
            await _ok(scope, receive, send)

    guard = PublicAdmissionGuard(capture, requests_per_minute=1)
    async def scenario():
        for _ in range(5):
            assert (await _request(guard, path="/health"))[0] == 200
        assert (await _request(guard, path="/mcp"))[0] == 200
        assert (await _request(guard, path="/mcp/"))[0] == 429
        # The wrapper must not swallow the SDK's lifespan startup/shutdown.
        async def receive():
            return {"type": "lifespan.shutdown"}
        async def send(_message):
            pass
        await guard({"type": "lifespan"}, receive, send)
    asyncio.run(scenario())
    assert "lifespan:" in scopes


@pytest.mark.parametrize("value", ["0", "-1", "abc", "12001"])
def test_invalid_environment_never_disables_guard(monkeypatch, value):
    monkeypatch.setenv("SINAN_PUBLIC_RATE_PER_MINUTE", value)
    with pytest.raises(ValueError):
        bounded_int_env("SINAN_PUBLIC_RATE_PER_MINUTE", 300, 12000)



def test_periodic_counters_never_include_client_metadata(caplog):
    import logging
    now = [0.0]
    guard = PublicAdmissionGuard(_ok, requests_per_minute=1, clock=lambda: now[0])

    async def scenario():
        client = [(b"x-forwarded-for", b"SECRET_PRIVATE_CLIENT_IDENTIFIER")]
        assert (await _request(guard, headers=client))[0] == 200
        assert (await _request(guard, headers=client))[0] == 429
        now[0] = 60.0
        assert (await _request(guard, headers=client))[0] == 200

    with caplog.at_level(logging.WARNING, logger="sinan_mcp.public_admission"):
        asyncio.run(scenario())
    assert "rate_rejected=1" in caplog.text
    assert "accepted=2" in caplog.text
    assert "SECRET_PRIVATE_CLIENT_IDENTIFIER" not in caplog.text
