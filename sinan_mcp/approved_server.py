"""Independent *optional* MCP service for human-reviewed aggregate releases.

NOT used by the already deployed synthetic public preview.
No SQLite, raw data, PySUS, private server, research pipelines or arbitrary SQL.
This process MUST fail to start without a versioned approved release and pinned
SHA-256. A review record is not a guarantee of anonymization or compliance.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Any

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse

from .aggregate_contract import load_approved_release

mcp = MCPServer(
    "SINAN MCP — aggregates (reviewed)",
    instructions=(
        "Somente agregados estáticos previamente avaliados e identificados. "
        "Nunca afirmar que os números correspondem a incidência, pacientes únicos "
        "ou coortes de diagnóstico sem documentação específica. "
        "Informar ano de ARQUIVO, UF, grupo, proveniência e limitações. "
        "Não há acesso a microdados; nenhuma consulta individual ou SQL é permitida."
    ),
)


@lru_cache(maxsize=1)
def _release() -> dict:
    path = os.getenv("SINAN_APPROVED_RELEASE_FILE", "")
    digest = os.getenv("SINAN_APPROVED_RELEASE_SHA256", "")
    if not path or not digest:
        raise RuntimeError(
            "Instância de agregados desativada: informe caminho e SHA-256 "
            "de um pacote com revisão humana independente."
        )
    return load_approved_release(path, digest)


def _source() -> dict:
    candidate = _release()["candidate"]
    return {
        "tipo": candidate["source"]["tipo"],
        "status_informado": candidate["source"]["status_informado"],
        "fingerprint_sha256": candidate["source"]["fingerprint_sha256"],
        "fonte_oficial": candidate["source"]["referencia_oficial"],
        "ano_do_arquivo_nao_equivale_a_ano_diagnostico": True,
    }


@mcp.tool()
def sobre_o_servidor() -> dict[str, Any]:
    """Descreve o caráter independente e as limitações do pacote aprovado."""
    package = _release()
    return {
        "modalidade": "apenas_agregados_estaticos_revisados",
        "source_record_level_data": False,
        "possui_microdados": False,
        "numero_de_pacotes": 1,
        "arquivo_de_ano": package["candidate"]["scope"]["ano_do_arquivo"],
        "fonte": _source(),
        "aviso": ("Revisão registrada; isso NÃO certifica anonimização formal, "
                  "equivalência com indicador oficial ou ausência de risco residual."),
    }


@mcp.tool()
def listar_agregados() -> dict[str, Any]:
    """Lista a ÚNICA combinação exata aprovada de ano do arquivo, UF e dimensão."""
    scope = _release()["candidate"]["scope"]
    return {
        "schema_version": "sinan-aggregates-v1",
        "disponiveis": [{
            "agravo": scope["agravo"],
            "ano_do_arquivo": scope["ano_do_arquivo"],
            "uf": scope["uf"],
            "dimensao": scope["dimensao"],
        }],
        "fonte": _source(),
        "aviso": "Somente tabelas pré-computadas; sem consulta livre nem microdados.",
    }


@mcp.tool()
def consultar_agregado(agravo: str, ano_do_arquivo: int, uf: str,
                       por: str) -> dict[str, Any]:
    """Consulta contagens aprovadas por parâmetros EXATOS; não é incidência."""
    candidate = _release()["candidate"]
    scope = candidate["scope"]
    if (agravo, ano_do_arquivo, uf, por) != (
        scope["agravo"], scope["ano_do_arquivo"], scope["uf"], scope["dimensao"]
    ) or type(ano_do_arquivo) is not int:
        raise ValueError(
            "Combinação não aprovada. Consulte listar_agregados; "
            "não há filtros adicionais, cruzamentos, totais alternativos ou SQL."
        )
    return {
        "schema_version": "sinan-aggregates-v1",
        "tipo": "contagem_registros_ano_do_arquivo_nao_oficial",
        "escopo": scope,
        "categorias": [dict(c) for c in candidate["cells"]],
        "fonte": _source(),
        "limitacoes": candidate["limitations"],
        "aviso_privacidade": (
            "Dados agregados sob política restritiva, não garantidamente "
            "anonimizados; risco residual de vínculo exige acompanhamento."
        ),
    }


@mcp.custom_route("/health", methods=["GET"])
async def health(_request):
    # Must not report healthy without the required verified release.
    _release()
    return JSONResponse(
        {"status": "ok", "deployment": "human-reviewed-aggregates-only"},
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


def _hostname() -> str:
    host = (os.getenv("SINAN_PUBLIC_HOST") or
            os.getenv("RENDER_EXTERNAL_HOSTNAME") or "").strip().lower()
    if (not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?", host)
            or host in {"localhost", "127.0.0.1"}):
        raise RuntimeError("Hostname público HTTPS autorizado ausente/inválido")
    return host


def start() -> None:
    _release()  # Refuse startup if review, policy, hash or file is missing.
    host = _hostname()
    port = int(os.getenv("PORT", "10000"))
    if not 1024 <= port <= 65535:
        raise ValueError("PORT inválida")
    mcp.run(
        transport="streamable-http", host="0.0.0.0", port=port,
        streamable_http_path="/mcp", stateless_http=True, json_response=True,
        max_request_body_size=16384,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[host, host + ":*"],
            allowed_origins=["https://chatgpt.com", "https://chat.openai.com"],
        ),
    )


if __name__ == "__main__":
    start()
