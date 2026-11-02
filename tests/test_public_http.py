"""End-to-end local HTTP smoke test: real streamable transport and security.

Never downloads or reads health data. Uses ephemeral loopback port and a
fictional allowed public Host header.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest


@pytest.mark.parametrize("protocol", ["2025-11-25"])
def test_public_http_end_to_end_and_host_origin_rejection(protocol):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    env = os.environ.copy()
    env.update({
        "SINAN_PUBLIC_HOST": "sinan-public.example.org",
        "SINAN_DB_PATH": "/no/patient/data.sqlite3",
        "SINAN_PUBLIC_REAL_DATA": "1",  # must have no effect on public mode
        "PORT": str(port),
        "PYTHONUNBUFFERED": "1",
    })
    child = subprocess.Popen(
        [sys.executable, "-m", "sinan_mcp.public_server"],
        env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True
    )
    address = "http://127.0.0.1:" + str(port)

    def get(path, *, host="sinan-public.example.org", origin=None):
        headers = {"Host": host}
        if origin is not None:
            headers["Origin"] = origin
        with urlopen(Request(address + path, headers=headers), timeout=3) as r:
            return r.status, json.load(r)

    def call(method, params, *, host="sinan-public.example.org", origin=None):
        headers = {
            "Host": host,
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": protocol,
        }
        if origin is not None:
            headers["Origin"] = origin
        request = Request(address + "/mcp",
                          headers=headers, method="POST",
                          data=json.dumps({
                              "jsonrpc": "2.0", "id": 1,
                              "method": method, "params": params,
                          }).encode())
        with urlopen(request, timeout=4) as r:
            return r.status, json.load(r)

    try:
        for attempt in range(60):
            if child.poll() is not None:
                raise AssertionError("Public MCP process exited on startup: " +
                                     (child.stderr.read() or "")[-2500:])
            try:
                status, health = get("/health")
                if status == 200:
                    break
            except (URLError, TimeoutError):
                time.sleep(0.15)
        else:
            raise AssertionError("Public MCP did not become healthy")

        assert health["deployment"] == "synthetic-only"

        code, response = call("initialize", {
            "protocolVersion": protocol,
            "capabilities": {},
            "clientInfo": {"name": "test-public", "version": "1.0"},
        })
        assert code == 200
        assert response["result"]["serverInfo"]["name"]

        code, response = call("tools/list", {})
        assert code == 200
        tools = {x["name"] for x in response["result"]["tools"]}
        assert tools == {
            "sobre_o_servidor", "listar_bases", "listar_agravos",
            "descrever_campos", "metodologia_abandono_tuberculose",
            "contar_notificacoes", "proporcao_abandono_tuberculose",
            "listar_fontes_oficiais", "pesquisar_agravos", "descrever_agravo",
        }

        code, response = call("tools/call", {
            "name": "listar_bases", "arguments": {},
        })
        assert code == 200
        assert "synthetic" in json.dumps(response)
        assert "SINAN_PUBLIC_REAL_DATA" not in json.dumps(response)

        # The same MCP route must reject unexpected hosts and browser origins.
        with pytest.raises(HTTPError) as wrong_host:
            call("tools/list", {}, host="evil.example.org")
        assert wrong_host.value.code == 421

        with pytest.raises(HTTPError) as wrong_origin:
            call("tools/list", {}, origin="https://evil.example.org")
        assert wrong_origin.value.code == 403
    finally:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)
        if child.stderr is not None:
            child.stderr.close()
