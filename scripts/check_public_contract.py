"""Fail-closed, offline check of the synthetic-only public contract.

This guard checks only static code/deployment invariants and tool inventory;
it is defense-in-depth, not a penetration test, scientific validation or
proof of privacy/anonymization.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "public-mcp-contract-v1.json"
PUBLIC = ROOT / "sinan_mcp" / "public_server.py"
ADMISSION = ROOT / "sinan_mcp" / "public_admission.py"
PUBLIC_LOCK = ROOT / "requirements-public.lock"
DEPLOYMENT = ROOT / "render.yaml"
DOC = ROOT / "docs" / "PUBLIC_LAUNCH.md"


def check() -> list[str]:
    problems: list[str] = []
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = PUBLIC.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(PUBLIC))
    if contract.get("schema_version") != "sinan-public-mcp-contract-v1":
        problems.append("Versao de contrato nao reconhecida")
    if contract.get("nature") != "synthetic-only":
        problems.append("Contrato publico nao e exclusivamente sintetico")
    for flag in ("live_data_available", "patient_records_available",
                 "supports_arbitrary_sql"):
        if contract.get(flag) is not False:
            problems.append("Contrato permite recurso real/perigoso: " + flag)
    if contract.get("health_path") != "/health" or contract.get("mcp_path") != "/mcp":
        problems.append("Rotas MCP e health alteradas fora do contrato")

    names = []
    health = False
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if isinstance(dec.func.value, ast.Name) and dec.func.value.id == "mcp":
                    if dec.func.attr == "tool":
                        names.append(node.name)
                    elif dec.func.attr == "custom_route" and node.name == "health":
                        health = True
    declared = contract.get("public_tools")
    if not isinstance(declared, list) or not all(isinstance(x, str) for x in declared):
        problems.append("Ferramentas do contrato invalidas")
    elif len(declared) != len(set(declared)) or set(declared) != set(names):
        problems.append("Inventario do MCP publico diverge do contrato")
    if not health:
        problems.append("Endpoint de health publico ausente")

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports = ([n.name for n in node.names]
                       if isinstance(node, ast.Import) else [node.module or ""])
            for module in imports:
                if module.split(".")[0] in {
                    "sqlite3", "pysus", "duckdb", "pandas", "subprocess",
                    "requests", "httpx", "pickle",
                }:
                    problems.append("Import perigoso no entrypoint publico: " + module)
            if isinstance(node, ast.ImportFrom) and node.level >= 1:
                if (node.module or "").split(".")[0] in {
                    "server", "core", "tool_api", "cli", "rest",
                    "demo", "approved_server",
                }:
                    problems.append("Import privado no entrypoint publico: " + str(node.module))

    if not ADMISSION.is_file():
        problems.append("Controle de admissao do MCP publico ausente")
    else:
        guard = ADMISSION.read_text(encoding="utf-8")
        if "class PublicAdmissionGuard:" not in guard or "status_code=429" not in guard:
            problems.append("Limites de taxa/concorrencia do MCP publico ausentes")
    if "mcp.streamable_http_app(" not in source or "PublicAdmissionGuard(" not in source:
        problems.append("Servidor publico sem o middleware de admissao ASGI")
    if "mcp.run(" in source or "proxy_headers=False" not in source:
        problems.append("Servidor publico iniciou sem limitador ou confiou em headers proxy")
    if not PUBLIC_LOCK.is_file():
        problems.append("Lockfile de dependencias publicas ausente")
    else:
        lock = PUBLIC_LOCK.read_text(encoding="utf-8")
        if "mcp==2.3.0" not in lock or "--hash=sha256:" not in lock:
            problems.append("Lockfile publico sem versao e hashes obrigatorios")

    deploy = DEPLOYMENT.read_text(encoding="utf-8")
    if "startCommand: python -m sinan_mcp.public_server" not in deploy:
        problems.append("Manifesto Render nao inicia o entrypoint sintetico")
    if "autoDeploy: false" not in deploy:
        problems.append("Manifesto Render habilitou deploy automatico")
    if "--require-hashes --no-deps -r requirements-public.lock" not in deploy:
        problems.append("Manifesto Render nao utiliza dependencias imutaveis")
    if 'value: "0"' not in deploy or "SINAN_PUBLIC_REAL_DATA" not in deploy:
        problems.append("Manifesto Render nao bloqueia dados reais explicitamente")
    guide = DOC.read_text(encoding="utf-8")
    if "ten public, read-only tools" not in guide:
        problems.append("Guia de lancamento nao documenta as dez ferramentas")
    if "seven public, read-only tools" in guide:
        problems.append("Guia de lancamento ainda menciona sete ferramentas")
    return problems


def main() -> int:
    failures = check()
    if failures:
        for item in failures:
            print("PUBLIC CONTRACT FAIL:", item, file=sys.stderr)
        return 1
    print("PUBLIC CONTRACT PASS: 10 MCP tools, synthetic-only; no deployment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
