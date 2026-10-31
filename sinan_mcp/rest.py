"""Adaptador REST local para clientes sem MCP; NÃO é pronto para Internet.

Reusa o mesmo núcleo de consulta e os mesmos filtros, sem permitir SQL livre.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .core import catalogo, contar, abandono_tb, dicionario


class Handler(BaseHTTPRequestHandler):
    server_version = "SINAN-MCP-REST/0.1"

    def _answer(self, status: int, payload: dict):
        content = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def _host_allowed(self):
        return self.headers.get("Host", "").split(":")[0].lower() in {"127.0.0.1", "localhost"}

    def do_GET(self):
        if not self._host_allowed():
            return self._answer(403, {"erro": "Host não autorizado"})
        path = urlparse(self.path).path
        if path == "/health":
            return self._answer(200, {"status": "ok", "tipo": "adaptador-local"})
        if path == "/v1/bases":
            return self._answer(200, catalogo(os.getenv("SINAN_DB_PATH", "./data/sinan.sqlite3")))
        if path == "/v1/campos":
            return self._answer(200, dicionario())
        return self._answer(404, {"erro": "Endpoint não encontrado"})

    def do_POST(self):
        if not self._host_allowed():
            return self._answer(403, {"erro": "Host não autorizado"})
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            return self._answer(415, {"erro": "Content-Type deve ser application/json"})
        try:
            size = int(self.headers.get("Content-Length", "-1"))
            if not 0 <= size <= 8192:
                return self._answer(413, {"erro": "Corpo muito grande ou inválido (máx. 8 KB)"})
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                return self._answer(400, {"erro": "Corpo deve ser um objeto JSON"})
            db = os.getenv("SINAN_DB_PATH", "./data/sinan.sqlite3")
            path = urlparse(self.path).path
            if path == "/v1/contagens":
                if any(k not in {"agravo", "ano_inicio", "ano_fim", "uf", "municipio", "por"} for k in body):
                    raise ValueError("Argumento desconhecido")
                return self._answer(200, contar(db, **body))
            if path == "/v1/tb/abandono":
                if any(k not in {"ano_inicio", "ano_fim", "uf", "municipio", "por"} for k in body):
                    raise ValueError("Argumento desconhecido")
                return self._answer(200, abandono_tb(db, **body))
            return self._answer(404, {"erro": "Endpoint não encontrado"})
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            return self._answer(400, {"erro": str(e)})


def run_rest(port: int):
    if not 1024 <= port <= 65535:
        raise ValueError("Porta REST inválida")
    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        server.serve_forever(poll_interval=0.2)
