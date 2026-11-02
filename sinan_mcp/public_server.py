"""Independent public MCP preview with only deterministic, fictional data.

SECURITY BOUNDARY:
- No SQLite/database access, downloads, file input, PySUS or research data.
- No import of sinan_mcp.server, tool_api, ingestion or admin functions.
- No ambient SINAN_DB_PATH or SINAN_PUBLIC_REAL_DATA bypass.
- No write tools or arbitrary SQL. Published numbers are FAKE demonstration
  fixtures and MUST NEVER be portrayed as official epidemiological data.
"""
from __future__ import annotations

import os
import re
from collections import Counter
from typing import Any

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse

from .catalogue import listar_agravos as _catalogue, metodologia_tuberculose as _method
from .official_sources import (
    listar_fontes_oficiais as _official_sources,
    pesquisar_agravos as _search_conditions,
    descrever_agravo as _describe_condition,
)
from .query_planner import (
    matriz_capacidades as _capabilities,
    planejar_consulta_agravo as _plan_query,
)

PUBLIC_VERSION = "0.4.0a4"
WARNING = (
    "EXEMPLO INTEGRALMENTE SINTÉTICO. Os números NÃO são do SINAN real, "
    "não representam pacientes, notificações oficiais, incidência ou risco."
)
mcp = MCPServer(
    "SINAN MCP — public demonstration",
    instructions=(
        "Este servidor público oferece catálogo de REFERÊNCIAS a múltiplos agravos e um exemplo 100% FICTÍCIO apenas de tuberculose. "
        "Listar um agravo ou uma fonte NÃO equivale a ter dados reais disponíveis. Não há bases reais importadas nem acesso a microdados. "
        "Em TODAS as respostas com valores numéricos, identifique explicitamente "
        "os números como sintéticos e nunca os utilize para inferências epidemiológicas. "
        "Nunca afirme que dados do SINAN real foram consultados."
    ),
)


def _fake_rows():
    """Stable, fixed fictional fixture (120 made-up records, never from SINAN)."""
    for i in range(120):
        race = "4" if i < 70 else "1"
        sex = "F" if i % 2 else "M"
        loss = ((i < 70 and i % 3 == 0) or
                (i >= 70 and i % 4 == 0))
        yield race, sex, "2" if loss else "1"


def _check(agravo: str, ano_inicio: int | None, ano_fim: int | None,
           uf: str | None, municipio: str | None, por: str) -> None:
    if (agravo != "TUBE" or type(ano_inicio) is not int or ano_inicio != 2024
            or type(ano_fim) is not int or ano_fim != 2024
            or uf != "PI" or municipio is not None
            or por not in {"raca_cor", "sexo"}):
        raise ValueError(
            "Exemplo público restrito a TUBE, ano_inicio=ano_fim=2024, "
            "uf=PI, municipio omitido e por=sexo ou raca_cor. "
            "Não há datasets reais disponíveis."
        )


def _result_meta():
    return {
        "fonte": "synthetic-in-code/v1",
        "natureza": "100% sintético",
        "agravo": "TUBE",
        "ano_do_arquivo_ficticio": 2024,
        "territorio_ficticio": "PI",
        "status": "nao_se_aplica",
        "aviso": WARNING,
    }


@mcp.tool()
def sobre_o_servidor() -> dict[str, Any]:
    """Identificação, licença, limitações e segurança da instância pública."""
    return {
        "produto": "SINAN MCP — Demonstração pública",
        "versao": PUBLIC_VERSION,
        "modalidade": "publica_somente_leitura_sintetica",
        "dados_reais_disponiveis": False,
        "acesso_microdados": False,
        "ferramentas_de_escrita": False,
        "caracter": "Software independente, não oficial do Ministério da Saúde ou DATASUS",
        "codigo_fonte": "https://github.com/miscrapha-DELTA-IA/SINAN-MCP",
        "aviso": WARNING,
    }


@mcp.tool()
def listar_bases() -> dict[str, Any]:
    """Lista exclusivamente a base FICTÍCIA de demonstração; nenhuma base SINAN real."""
    return {
        "schema_version": "0.4",
        "bases": [
            {"agravo": "TUBE", "ano_do_arquivo": 2024,
             "tipo_de_fonte": "synthetic", "status": "nao_se_aplica"}
        ],
        "dados_reais_disponiveis": False,
        "aviso": WARNING,
    }


@mcp.tool()
def listar_agravos() -> dict[str, Any]:
    """Lista agravos documentados; não implica disponibilização de bases reais."""
    data = _catalogue()
    data["disponibilidade_neste_servidor"] = (
        "Apenas um cenário inteiramente fictício TUBE 2024/PI; "
        "DENG e demais agravos sem dados consultáveis nesta instância."
    )
    data["aviso"] = WARNING
    return data


@mcp.tool()
def listar_fontes_oficiais() -> dict[str, Any]:
    """Fontes oficiais de consulta: somente links e documentação, SEM números reais."""
    return _official_sources()


@mcp.tool()
def pesquisar_agravos(termo: str = "", limite: int = 20) -> dict[str, Any]:
    """Encontra agravos em índice EXEMPLIFICATIVO; sem download nem dados individuais."""
    return _search_conditions(termo, limite)


@mcp.tool()
def descrever_agravo(codigo_interno: str) -> dict[str, Any]:
    """Distingue código interno, documentação, validação e disponibilidade."""
    return _describe_condition(codigo_interno)


@mcp.tool()
def matriz_capacidades() -> dict[str, Any]:
    """Matriz dos agravos REFERENCIADOS, deixando explícita a ausência de dados reais."""
    return _capabilities()


@mcp.tool()
def planejar_consulta_agravo(
    agravo: str, ano: int | None = None, uf: str | None = None,
    por: str = "sexo",
) -> dict[str, Any]:
    """Orienta pesquisa de qualquer agravo sem inventar dados nem acessar microdados."""
    return _plan_query(agravo, ano, uf, por)


@mcp.tool()
def descrever_campos() -> dict[str, Any]:
    """Explica variáveis do protótipo e a necessidade de validação científica."""
    return {
        "variaveis_da_demo": {
            "raca_cor": "CS_RACA: 1 branca, 4 parda na demonstração; categorias reais dependem do dicionário oficial.",
            "sexo": "CS_SEXO: F ou M na demonstração, não infere identidade de gênero.",
            "situacao_encerramento": "Códigos fictícios 1 cura e 2 abandono; não são coorte oficial.",
        },
        "referencia": "https://portalsinan.saude.gov.br/tuberculose",
        "aviso": WARNING,
    }


@mcp.tool()
def metodologia_abandono_tuberculose() -> dict[str, Any]:
    """Documenta uma proporção exploratória, NÃO o indicador oficial do MS."""
    data = _method()
    data["aviso_publico"] = WARNING
    return data


@mcp.tool()
def contar_notificacoes(agravo: str, ano_inicio: int | None = None,
                        ano_fim: int | None = None, uf: str | None = None,
                        municipio: str | None = None, por: str = "raca_cor") -> dict[str, Any]:
    """Retorna SOMENTE contagens FICTÍCIAS para testar a ferramenta, nunca notificações reais."""
    _check(agravo, ano_inicio, ano_fim, uf, municipio, por)
    pos = 0 if por == "raca_cor" else 1
    counts = Counter(row[pos] for row in _fake_rows())
    return {
        "schema_version": "0.4",
        "tipo": "demonstracao_de_contagem_nao_epidemiologica",
        "resultado": {
            "agravo": agravo, "agrupar_por": por,
            "filtros": {"ano_inicio": 2024, "ano_fim": 2024, "uf": "PI"},
            "dados": [
                {"categoria": key, "notificacoes_ficticias": n, "suprimido": False}
                for key, n in sorted(counts.items())
            ],
        },
        "proveniencia": _result_meta(),
        "aviso": WARNING,
    }


@mcp.tool()
def proporcao_abandono_tuberculose(ano_inicio: int | None = None,
                                 ano_fim: int | None = None,
                                 uf: str | None = None,
                                 municipio: str | None = None,
                                 por: str = "raca_cor") -> dict[str, Any]:
    """Exemplo FICTÍCIO de proporção de abandono; NÃO é indicador epidemiológico oficial."""
    _check("TUBE", ano_inicio, ano_fim, uf, municipio, por)
    pos = 0 if por == "raca_cor" else 1
    groups: dict[str, list[str]] = {}
    for row in _fake_rows():
        groups.setdefault(row[pos], []).append(row[2])
    data = [
        {"categoria": k, "proporcao_ficticia_percentual": round(
            100 * sum(v == "2" for v in values) / len(values), 2
        ), "suprimido": False}
        for k, values in sorted(groups.items())
    ]
    return {
        "schema_version": "0.4",
        "tipo": "simulacao_nao_oficial_de_abandono",
        "resultado": {"dados": data, "agrupar_por": por},
        "proveniencia": _result_meta(),
        "aviso": WARNING,
    }


@mcp.custom_route("/health", methods=["GET"])
async def health(_request):
    """Non-sensitive public liveness check."""
    return JSONResponse(
        {"status": "ok", "deployment": "synthetic-only", "version": PUBLIC_VERSION},
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


def _hostname() -> str:
    """Fail closed: a public listener needs an explicit hosting hostname."""
    raw = os.getenv("SINAN_PUBLIC_HOST") or os.getenv("RENDER_EXTERNAL_HOSTNAME", "")
    host = raw.strip().lower()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?", host):
        raise RuntimeError(
            "Defina SINAN_PUBLIC_HOST com o hostname HTTPS autorizado "
            "(sem esquema, porta ou caminho); a instância pública não iniciou."
        )
    if host in {"localhost", "127.0.0.1"}:
        raise RuntimeError("Host público não pode ser localhost")
    return host


def start() -> None:
    host = _hostname()
    port = int(os.getenv("PORT", "10000"))
    if not 1024 <= port <= 65535:
        raise ValueError("PORT inválida")
    # The MCP SDK itself enforces Host and Origin allowlists.
    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[host, host + ":*"],
        allowed_origins=["https://chatgpt.com", "https://chat.openai.com"],
    )
    mcp.run(
        transport="streamable-http", host="0.0.0.0", port=port,
        streamable_http_path="/mcp", stateless_http=True, json_response=True,
        max_request_body_size=16384, transport_security=transport_security,
    )


if __name__ == "__main__":
    start()
