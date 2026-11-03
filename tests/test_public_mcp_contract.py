"""Explicit public MCP tool name/description/input-field contract snapshot.

Any change requires a conscious test review: protects against accidental tool
rug-pulls, unexpected new inputs and private-administrator tool exposure.
This is not by itself a complete MCP security conformance certification.
"""
from __future__ import annotations

import asyncio

from sinan_mcp import public_server

# Exact snapshot of *public* names, developer-controlled descriptions, and
# input properties; committed as reviewable source, not auto-regenerated.
EXPECTED = {
    "sobre_o_servidor": (
        "Identificação, licença, limitações e segurança da instância pública.", (),
    ),
    "listar_bases": (
        "Lista exclusivamente a base FICTÍCIA de demonstração; nenhuma base SINAN real.", (),
    ),
    "listar_agravos": (
        "Lista agravos documentados; não implica disponibilização de bases reais.", (),
    ),
    "listar_fontes_oficiais": (
        "Fontes oficiais de consulta: somente links e documentação, SEM números reais.", (),
    ),
    "pesquisar_agravos": (
        "Encontra agravos em índice EXEMPLIFICATIVO; sem download nem dados individuais.",
        ("termo", "limite"),
    ),
    "descrever_agravo": (
        "Distingue código interno, documentação, validação e disponibilidade.",
        ("codigo_interno",),
    ),
    "matriz_capacidades": (
        "Matriz dos agravos REFERENCIADOS, deixando explícita a ausência de dados reais.", (),
    ),
    "planejar_consulta_agravo": (
        "Orienta pesquisa de qualquer agravo sem inventar dados nem acessar microdados.",
        ("agravo", "ano", "uf", "por"),
    ),
    "vocabulario_semantico": (
        "Define unidades, eixos temporais, medidas e denominadores sem consultar dados.", (),
    ),
    "planejar_medida_epidemiologica": (
        "Planeja uma medida com semântica controlada; nunca executa cálculo real.",
        ("agravo", "ano_do_arquivo", "unidade_observacional",
         "eixo_temporal", "tipo_medida", "denominador", "fonte_denominador"),
    ),
    "descrever_campos": (
        "Explica variáveis do protótipo e a necessidade de validação científica.", (),
    ),
    "metodologia_abandono_tuberculose": (
        "Documenta uma proporção exploratória, NÃO o indicador oficial do MS.", (),
    ),
    "contar_notificacoes": (
        "Retorna SOMENTE contagens FICTÍCIAS para testar a ferramenta, nunca notificações reais.",
        ("agravo", "ano_inicio", "ano_fim", "uf", "municipio", "por"),
    ),
    "proporcao_abandono_tuberculose": (
        "Exemplo FICTÍCIO de proporção de abandono; NÃO é indicador epidemiológico oficial.",
        ("ano_inicio", "ano_fim", "uf", "municipio", "por"),
    ),
}


def test_snapshot_of_public_descriptions_and_input_field_names():
    from mcp import Client

    async def check():
        async with Client(public_server.mcp, mode="auto", raise_exceptions=True) as client:
            tools = (await client.list_tools()).tools
            by_name = {tool.name: tool for tool in tools}
            assert set(by_name) == set(EXPECTED)
            for name, (description, fields) in EXPECTED.items():
                tool = by_name[name]
                assert tool.description == description, f"Description changed: {name}"
                assert set(tool.inputSchema.get("properties", {})) == set(fields), (
                    f"Input schema changed: {name}"
                )
                assert not name.startswith(
                    ("importar", "auditar", "validar", "confrontar", "verificar")
                )
            assert str(client.protocol_version) == "2026-07-28"

    asyncio.run(check())


def test_no_admin_tool_aliases_in_snapshot():
    for forbidden in (
        "importar-pysus", "importar-csv", "auditar-qualidade",
        "validar-csv-demo", "confrontar-tabnet", "verificar-composicao",
        "verificar-proveniencia", "verificar-linhagem",
    ):
        assert forbidden not in EXPECTED
