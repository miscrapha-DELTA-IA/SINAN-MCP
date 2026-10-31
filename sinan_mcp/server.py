"""Camada de ferramentas MCP, desacoplada do código de ingestão/administração."""
from __future__ import annotations

import os
from pathlib import Path
from mcp.server import MCPServer
from .core import catalogo, contar, abandono_tb, dicionario

mcp = MCPServer("SINAN MCP", instructions=(
    "Ferramentas de epidemiologia sobre bases públicas do SINAN importadas localmente. "
    "NÃO invente números quando a resposta vier vazia ou suprimida. "
    "Diferencie ano de arquivo e ano de notificação. "
    "Cite fonte, status e período do catálogo e não trate contagem de registros como incidência. "
    "As proporções são exploratórias, não indicadores oficiais."
))


def db_path() -> Path:
    return Path(os.getenv("SINAN_DB_PATH", "./data/sinan.sqlite3"))


@mcp.tool()
def listar_bases() -> dict:
    """Lista datasets SINAN importados, anos, status final/preliminar, proveniência e data de carga."""
    return catalogo(db_path())


@mcp.tool()
def descrever_campos() -> dict:
    """Explica campos e exemplos de agravos para interpretar os resultados corretamente."""
    return dicionario()


@mcp.tool()
def contar_notificacoes(agravo: str, ano_inicio: int | None = None,
                         ano_fim: int | None = None, uf: str | None = None,
                         municipio: str | None = None, por: str = "ano") -> dict:
    """Conta registros por ano, UF, município, sexo ou raça/cor. Aplica limiar de supressão 10."""
    return contar(db_path(), agravo=agravo, ano_inicio=ano_inicio, ano_fim=ano_fim,
                  uf=uf, municipio=municipio, por=por)


@mcp.tool()
def proporcao_abandono_tuberculose(ano_inicio: int | None = None,
                                  ano_fim: int | None = None, uf: str | None = None,
                                  municipio: str | None = None, por: str = "raca_cor") -> dict:
    """Proporção exploratória TB de SITUA_ENCE 2 ou 10 entre encerramentos 1, 2 ou 10, por grupo. NÃO é taxa oficial."""
    return abandono_tb(db_path(), ano_inicio=ano_inicio, ano_fim=ano_fim,
                       uf=uf, municipio=municipio, por=por)


if __name__ == "__main__":
    mcp.run()
