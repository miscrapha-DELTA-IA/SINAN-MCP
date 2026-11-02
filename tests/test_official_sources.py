"""Multi-agravo reference catalogue, independent of the clinical SQL pipeline."""
from __future__ import annotations

import asyncio
import inspect
import json
from urllib.parse import urlparse

import pytest

from sinan_mcp import official_sources as registry
from sinan_mcp import public_server


def test_registry_is_explicitly_non_exhaustive_and_no_real_datasets():
    all_items = registry.pesquisar_agravos("")
    assert all_items["indice_exemplificativo_nao_exaustivo"] is True
    assert len(all_items["resultados"]) >= 12
    assert all(not x["dados_reais_disponiveis_no_mcp_publico"] for x in all_items["resultados"])
    assert all(not x["codigo_oficial_de_download_confirmado"] for x in all_items["resultados"])
    assert {"TUBE", "DENG", "HANS", "HEPA", "SIFA", "VIOL", "ANIM", "MENI"} <= {
        d["codigo_interno"] for d in all_items["resultados"]
    }
    assert "NAO" not in json.dumps(all_items)


@pytest.mark.parametrize("input_text, expected", [
    ("hanseníase", "HANS"),
    ("hanseniase", "HANS"),
    ("TUBE", "TUBE"),
    ("dengue", "DENG"),
    ("sífilis", "SIFA"),
    ("peçonhentos", "ANIM"),
    ("leishmaniose", "LEIV"),
    ("meningite", "MENI"),
])
def test_search_normalization(input_text, expected):
    found = registry.pesquisar_agravos(input_text)
    assert expected in {x["codigo_interno"] for x in found["resultados"]}


@pytest.mark.parametrize("bad,limit", [
    (None, 5), ("a" * 81, 5), ("abc\x00", 5), ("", -1), ("", True), ("", 100)
])
def test_search_rejects_invalid_filters(bad, limit):
    with pytest.raises(ValueError):
        registry.pesquisar_agravos(bad, limit)


def test_unknown_disease_does_not_mean_not_in_sinan():
    with pytest.raises(ValueError, match="NÃO indica"):
        registry.descrever_agravo("AAAA")
    with pytest.raises(ValueError):
        registry.descrever_agravo("../../root")


def test_sources_are_real_official_landing_pages_not_direct_values():
    sources = registry.listar_fontes_oficiais()
    assert sources["natureza"] == "somente_metadados_de_navegacao"
    assert sources["fontes"]
    for source in sources["fontes"]:
        u = urlparse(source["url"])
        assert u.scheme == "https"
        assert u.hostname in {"www.gov.br", "datasus.saude.gov.br", "portalsinan.saude.gov.br"}
        assert source["possui_valores_importados_neste_mcp"] is False


def test_tool_references_do_not_import_private_or_accept_microdata():
    code = inspect.getsource(registry)
    for forbidden in ["import sqlite3", "from .core import", "from .tool_api import",
                      "urllib.request", "requests.get", "ingest_pysus", "sinan.sqlite3"]:
        assert forbidden not in code

    assert public_server.listar_bases()["dados_reais_disponiveis"] is False
    assert public_server.pesquisar_agravos("DENG")["resultados"][0]["codigo_interno"] == "DENG"
    assert public_server.descrever_agravo("DENG")["agravo"]["dados_reais_disponiveis_no_mcp_publico"] is False


def test_public_mcp_exposes_only_static_reference_functions():
    from mcp import Client
    async def probe():
        async with Client(public_server.mcp, raise_exceptions=True) as client:
            names = {t.name for t in (await client.list_tools()).tools}
            assert {"listar_fontes_oficiais", "pesquisar_agravos", "descrever_agravo"} <= names
            out = await client.call_tool("pesquisar_agravos", {"termo": "hepatites"})
            assert not out.is_error
            assert out.structured_content["resultados"][0]["codigo_interno"] == "HEPA"
            source = await client.call_tool("listar_fontes_oficiais", {})
            assert not source.is_error
            assert source.structured_content["natureza"] == "somente_metadados_de_navegacao"
    asyncio.run(probe())
