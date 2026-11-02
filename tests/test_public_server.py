"""Public launch gate: no patient data or local research databases, only fiction."""
from __future__ import annotations

import asyncio
import inspect
import os

import pytest

from sinan_mcp import public_server as public


def test_public_does_not_import_private_data_pipeline(monkeypatch, tmp_path):
    # ENVIRONMENT POISONING: a public daemon must ignore private DB permissions.
    monkeypatch.setenv("SINAN_DB_PATH", str(tmp_path / "clinical.sqlite3"))
    monkeypatch.setenv("SINAN_PUBLIC_REAL_DATA", "1")
    assert public.sobre_o_servidor if hasattr(public, "sobre_o_servidor") else public.mcp
    assert not (tmp_path / "clinical.sqlite3").exists()
    src = inspect.getsource(public)
    for forbidden in ["from .server import", "from .core import",
                      "from .tool_api import", "sqlite3.connect",
                      "ingest_pysus(", "ingest_csv(", "urllib.request"]:
        assert forbidden not in src


def test_public_values_are_labelled_fictional():
    base = public.listar_bases()
    assert base["dados_reais_disponiveis"] is False
    assert base["bases"][0]["tipo_de_fonte"] == "synthetic"
    r = public.contar_notificacoes(
        "TUBE", 2024, 2024, "PI", None, "raca_cor"
    )
    assert sum(g["notificacoes_ficticias"] for g in r["resultado"]["dados"]) == 120
    assert "SINTÉTICO" in r["aviso"]
    assert r["proveniencia"]["fonte"] == "synthetic-in-code/v1"
    loss = public.proporcao_abandono_tuberculose(
        2024, 2024, "PI", None, "sexo"
    )
    assert "SINTÉTICO" in loss["aviso"]
    assert len(loss["resultado"]["dados"]) == 2
    assert public.listar_agravos()["aviso"] == r["aviso"]
    assert public.metodologia_abandono_tuberculose()["situacao"] == "NAO_OFICIAL"


@pytest.mark.parametrize("bad", [
    ("DENG", 2024, 2024, "PI", None, "raca_cor"),
    ("TUBE", 2023, 2023, "PI", None, "raca_cor"),
    ("TUBE", 2024, 2024, "RJ", None, "raca_cor"),
    ("TUBE", 2024, 2024, "PI", "221100", "raca_cor"),
    ("TUBE", 2024, 2024, "PI", None, "municipio"),
    ("TUBE", True, True, "PI", None, "sexo"),
])
def test_no_real_or_arbitrary_query(bad):
    with pytest.raises(ValueError, match="Exemplo público restrito"):
        public.contar_notificacoes(*bad)


def test_public_host_configuration_fail_closed(monkeypatch):
    monkeypatch.delenv("SINAN_PUBLIC_HOST", raising=False)
    monkeypatch.delenv("RENDER_EXTERNAL_HOSTNAME", raising=False)
    with pytest.raises(RuntimeError, match="SINAN_PUBLIC_HOST"):
        public._hostname()
    for bad in ["", "http://example.org", "*.example.org",
                "127.0.0.1", "localhost", "example.org/path",
                "EXAMPLE.ORG:443", "host name"]:
        monkeypatch.setenv("SINAN_PUBLIC_HOST", bad)
        with pytest.raises(RuntimeError):
            public._hostname()
    monkeypatch.setenv("SINAN_PUBLIC_HOST", "sinan-public.example.org")
    assert public._hostname() == "sinan-public.example.org"


def test_public_starts_only_with_host_allowlist(monkeypatch):
    monkeypatch.setenv("SINAN_PUBLIC_HOST", "sinan-public.example.org")
    monkeypatch.setenv("PORT", "10000")
    captured = {}

    def fake_run(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(public.mcp, "run", fake_run)
    public.start()
    assert captured["transport"] == "streamable-http"
    assert captured["stateless_http"] is True
    assert captured["json_response"] is True
    assert captured["max_request_body_size"] <= 16384
    assert captured["streamable_http_path"] == "/mcp"
    assert captured["host"] == "0.0.0.0"
    security = captured["transport_security"]
    assert security.enable_dns_rebinding_protection is True
    assert "sinan-public.example.org" in security.allowed_hosts
    assert "https://chatgpt.com" in security.allowed_origins


def test_public_mcp_tools_no_private_admin_routes():
    from mcp import Client

    async def probe():
        async with Client(public.mcp, raise_exceptions=True) as client:
            tools = (await client.list_tools()).tools
            names = {t.name for t in tools}
            assert names == {
                "sobre_o_servidor", "listar_bases", "listar_agravos",
                "descrever_campos", "metodologia_abandono_tuberculose",
                "contar_notificacoes", "proporcao_abandono_tuberculose",
                "listar_fontes_oficiais", "pesquisar_agravos", "descrever_agravo",
            "matriz_capacidades", "planejar_consulta_agravo",
            }
            assert all(not n.startswith(("importar", "diagnosticar",
                                        "auditar", "query_sql")) for n in names)
            r = await client.call_tool("contar_notificacoes", {
                "agravo": "TUBE", "ano_inicio": 2024, "ano_fim": 2024,
                "uf": "PI", "por": "raca_cor",
            })
            assert not r.is_error
            assert r.structured_content["proveniencia"]["fonte"] == "synthetic-in-code/v1"
            r2 = await client.call_tool("listar_bases", {})
            assert not r2.is_error
            assert r2.structured_content["dados_reais_disponiveis"] is False

    asyncio.run(probe())
