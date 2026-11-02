"""Read-only HTTPS smoke test for the intentionally fictional public MCP.

Runs from CI, never requests real surveillance data.
"""
from __future__ import annotations

import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = os.environ.get("SINAN_PUBLIC_SMOKE_URL", "").rstrip("/")
if not BASE.startswith("https://") or not BASE.endswith(".onrender.com"):
    raise SystemExit("SINAN_PUBLIC_SMOKE_URL must be an explicit approved HTTPS Render hostname")


def request(path: str, payload=None, *, origin=None):
    headers = {"Accept": "application/json, text/event-stream"}
    if payload is not None:
        headers.update({
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2025-11-25",
        })
    if origin is not None:
        headers["Origin"] = origin
    req = Request(
        BASE + path, headers=headers, method="POST" if payload else "GET",
        data=json.dumps(payload).encode("utf-8") if payload else None,
    )
    with urlopen(req, timeout=30) as response:
        if response.status != 200:
            raise AssertionError(f"Expected 200, got {response.status}")
        raw = response.read(100_000)
        return json.loads(raw)


def rpc(method: str, params: dict, *, origin=None):
    return request("/mcp", {
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params,
    }, origin=origin)


def tool(name: str, arguments: dict):
    result = rpc("tools/call", {"name": name, "arguments": arguments})
    if "error" in result:
        raise AssertionError(f"MCP error on tool {name}: {result['error'].get('code')}")
    obj = result["result"].get("structuredContent")
    if obj is None:
        blocks = result["result"].get("content", [])
        obj = json.loads(next(v["text"] for v in blocks if v.get("type") == "text"))
    return obj


def main():
    last = None
    for _ in range(50):
        try:
            health = request("/health")
            assert health["status"] == "ok"
            assert health["deployment"] == "synthetic-only"
            print("PASS HTTPS /health: synthetic-only")
            break
        except (AssertionError, URLError, TimeoutError, ValueError) as exc:
            last = type(exc).__name__
            time.sleep(5)
    else:
        raise AssertionError("Public endpoint did not become healthy: " + str(last))

    init = rpc("initialize", {
        "protocolVersion": "2025-11-25",
        "capabilities": {},
        "clientInfo": {"name": "public-smoke", "version": "1"},
    })
    assert init["result"]["serverInfo"]["name"].startswith("SINAN MCP")
    print("PASS MCP initialize")

    tools = rpc("tools/list", {})["result"]["tools"]
    names = {t["name"] for t in tools}
    assert names == {
        "sobre_o_servidor", "listar_bases", "listar_agravos", "descrever_campos",
        "metodologia_abandono_tuberculose", "contar_notificacoes",
        "proporcao_abandono_tuberculose",
    }
    print("PASS MCP tools/list: seven read-only demonstration tools")

    bases = tool("listar_bases", {})
    assert bases["dados_reais_disponiveis"] is False
    assert all(b["tipo_de_fonte"] == "synthetic" for b in bases["bases"])
    print("PASS MCP listar_bases: no real datasets")

    counts = tool("contar_notificacoes", {
        "agravo": "TUBE", "ano_inicio": 2024, "ano_fim": 2024,
        "uf": "PI", "por": "raca_cor",
    })
    assert counts["proveniencia"]["fonte"] == "synthetic-in-code/v1"
    assert "SINTÉTICO" in counts["aviso"]
    assert sum(x["notificacoes_ficticias"] for x in counts["resultado"]["dados"]) == 120
    print("PASS MCP contar_notificacoes: 120 explicitly fictional records")

    try:
        rpc("tools/list", {}, origin="https://evil.example.org")
    except HTTPError as exc:
        assert exc.code == 403, f"Unexpected Origin response: {exc.code}"
        print("PASS MCP rejects unapproved Origin")
    else:
        raise AssertionError("Unapproved Origin was accepted")

    print("PUBLIC HTTPS MCP SMOKE SUCCESS")


if __name__ == "__main__":
    main()
