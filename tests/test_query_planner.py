"""Multi-agravo planner tests: no real-data claims and no storage access."""
from __future__ import annotations

import asyncio
import inspect
import json

import pytest

from sinan_mcp import query_planner
from sinan_mcp import public_server


def test_matrix_is_curated_and_never_implies_real_dataset():
    result = query_planner.matriz_capacidades()
    assert result["quantidade_referencias"] >= 14
    assert result["escopo"] == "indice_curado_exemplificativo_nao_exaustivo"
    assert result["operacoes_reais_neste_servidor"] == []
    assert result["publicacao_de_agregados_reais_automatica"] is False
    assert all(not item["consulta_real_disponivel_no_mcp_publico"]
               for item in result["agravos_referenciados"])
    assert sum(item["demo_sintetica"]
               for item in result["agravos_referenciados"]) == 1


@pytest.mark.parametrize("term, expected", [
    ("Tuberculose", "TUBE"),
    ("TUBE", "TUBE"),
    ("tuberculose", "TUBE"),
    ("Hanseníase", "HANS"),
    ("hanseniase", "HANS"),
    ("hepatites", "HEPA"),
    ("meningite", "MENI"),
    ("ANIM", "ANIM"),
])
def test_planner_resolves_supported_reference_terms(term, expected):
    data = query_planner.planejar_consulta_agravo(term, ano=2023, uf="pi", por="sexo")
    assert data["estado"] == "referencia_identificada_sem_dados_reais"
    assert data["correspondencias"][0]["codigo_interno"] == expected
    assert data["entrada"] == {"agravo": term, "ano": 2023, "uf": "PI",
                               "dimensao": "sexo"}
    assert data["consulta_executada"] is False
    assert data["resultado_epidemiologico"] is None
    assert data["dados_reais_disponiveis_no_servidor_publico"] is False
    assert len(data["fontes_oficiais_para_verificacao"]) >= 2


def test_ambiguous_and_unknown_not_falsely_resolved():
    ambiguous = query_planner.planejar_consulta_agravo("sífilis")
    assert ambiguous["estado"] == "ambiguo_escolha_agravo"
    assert {x["codigo_interno"] for x in ambiguous["correspondencias"]} == {
        "SIFA", "SIFC"
    }
    unknown = query_planner.planejar_consulta_agravo("enfermidade desconhecida")
    assert unknown["estado"] == "fora_do_indice_exemplificativo"
    assert unknown["correspondencias"] == []
    assert unknown["fontes_oficiais_para_verificacao"]


@pytest.mark.parametrize("kwargs", [
    {"agravo": ""}, {"agravo": None}, {"agravo": "\x00TUBE"},
    {"agravo": "TUBE", "ano": True},
    {"agravo": "TUBE", "ano": 1900},
    {"agravo": "TUBE", "ano": 2020.5},
    {"agravo": "TUBE", "uf": "Piauí"},
    {"agravo": "TUBE", "uf": "XX"},
    {"agravo": "TUBE", "por": "municipio"},
    {"agravo": "TUBE", "por": "sexo,raca_cor"},
    {"agravo": "TUBE", "por": None},
])
def test_bad_inputs_are_rejected(kwargs):
    with pytest.raises(ValueError):
        query_planner.planejar_consulta_agravo(**kwargs)


def test_planner_has_no_database_network_or_private_imports():
    code = inspect.getsource(query_planner)
    for forbidden in [
        "import sqlite3", "from .core import", "from .tool_api import",
        "from .release_pipeline import", "requests.get", "urllib.request",
        "subprocess", "SINAN_DB_PATH", "SINAN_PUBLIC_REAL_DATA"
    ]:
        assert forbidden not in code


def test_public_mcp_exposes_planner_tools():
    from mcp import Client

    async def exercise():
        async with Client(public_server.mcp, raise_exceptions=True) as client:
            tools = {item.name for item in (await client.list_tools()).tools}
            assert {"matriz_capacidades", "planejar_consulta_agravo"} <= tools
            response = await client.call_tool(
                "planejar_consulta_agravo",
                {"agravo": "DENG", "ano": 2024, "uf": "PI"}
            )
            assert not response.is_error
            assert response.structured_content["estado"] == (
                "referencia_identificada_sem_dados_reais"
            )
            assert not response.structured_content["consulta_executada"]
            assert "DENG" in json.dumps(response.structured_content)
            matrix = await client.call_tool("matriz_capacidades", {})
            assert not matrix.is_error
            assert not matrix.structured_content["operacoes_reais_neste_servidor"]

    asyncio.run(exercise())
