"""Public launch gate: no patient data or local research databases, only fiction."""
from __future__ import annotations

import asyncio
import inspect
import logging
import os

import pytest
from mcp.server.mcpserver.exceptions import ToolError

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


def test_public_privacy_document_is_packaged_and_servable():
    """The privacy notice is a static bundled asset, not a database or remote fetch."""
    from importlib.resources import files

    html = files("sinan_mcp").joinpath("public_privacy.html").read_text(encoding="utf-8")
    assert '<html lang="pt-BR">' in html
    assert "Política de Privacidade" in html
    assert "SINAN" in html and "sintética" in html
    assert "Render" in html and "7 dias" in html
    assert "LGPD" in html and "ANPD" in html
    assert "Raphael Múcio Teixeira Cabral de Pina Bulhões Di Giorgio" in html
    assert "miscrapha@gmail.com" in html
    assert "[PENDENTE" not in html
    assert "Minuta em validação" not in html
    assert "a confirmar após revisão" not in html
    assert "dados técnicos" in html or "Metadados técnicos" in html
    assert "direitos" in html.lower()
    assert "transferência internacional" in html.lower()
    assert "<script" not in html.lower()
    assert "<form" not in html.lower()

    async def read_policy():
        response = await public.public_privacy(None)
        assert response.status_code == 200
        assert response.body.decode("utf-8") == html
        assert response.headers["content-type"].startswith("text/html")
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "default-src 'none'" in response.headers["content-security-policy"]

    asyncio.run(read_policy())


@pytest.mark.parametrize("name,route,required", [
    ("public_about.html", public.public_about, "Catálogo documental e simulações epidemiológicas"),
    ("public_support.html", public.public_support, "Suporte e contato"),
    ("public_terms.html", public.public_terms, "Termos de Uso"),
])
def test_public_listing_pages_packaged_and_readonly(name, route, required):
    """Site, support and terms must work without DB, network or client state."""
    from importlib.resources import files

    html = files("sinan_mcp").joinpath(name).read_text(encoding="utf-8")
    assert '<html lang="pt-BR">' in html
    assert required in html
    assert "miscrapha@gmail.com" in html
    assert "Raphael Múcio Teixeira Cabral de Pina Bulhões Di Giorgio" in html
    assert "/privacidade" in html and "/suporte" in html and "/termos" in html
    assert "/sobre" in html
    assert "SINAN MCP" in html
    assert "<script" not in html.lower()
    assert "<form" not in html.lower()
    assert "[PENDENTE" not in html
    async def fetch_static():
        response = await route(None)
        assert response.status_code == 200
        assert response.body.decode("utf-8") == html
        assert response.headers["content-type"].startswith("text/html")
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "default-src 'none'" in response.headers["content-security-policy"]
    asyncio.run(fetch_static())


def test_public_static_page_allowlist_no_traversal():
    with pytest.raises(ValueError, match="não permitida"):
        public._static_public_page("../.env")
    with pytest.raises(ValueError, match="não permitida"):
        public._static_public_page("public_privacy.html")


def test_public_values_are_labelled_fictional():
    base = public.listar_bases()
    assert base["dados_reais_disponiveis"] is False
    assert base["bases"][0]["tipo_de_fonte"] == "synthetic"
    r = public.contar_notificacoes(
        "TUBE", 2024, 2024, "PI", None, "raca_cor"
    )
    assert sum(g["notificacoes_ficticias"] for g in r["resultado"]["dados"]) == 120
    assert "SINTÉTICO" in r["aviso"]
    assert r["proveniencia"]["fonte"] == "synthetic-in-code/v2"
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
    with pytest.raises(ToolError, match="Exemplo público restrito"):
        public.contar_notificacoes(*bad)



def test_public_mcp_rejected_queries_are_tool_errors_not_unexpected_crashes(caplog):
    """Denied fictional-query variants must not generate exception tracebacks."""
    from mcp import Client

    async def probe():
        async with Client(public.mcp, raise_exceptions=True) as client:
            for args in (
                {"agravo": "DENG", "ano_inicio": 2024, "ano_fim": 2024, "uf": "PI"},
                {"agravo": "TUBE", "ano_inicio": 2024, "ano_fim": 2024,
                 "uf": "PI", "municipio": "221100"},
            ):
                response = await client.call_tool("contar_notificacoes", args)
                assert response.is_error is True
                text = " ".join(
                    getattr(block, "text", "") for block in response.content
                )
                assert "Exemplo público restrito" in text
                assert "Error executing tool contar_notificacoes:" in text
                # Rejected client parameters must never be echoed to a model.
                assert "221100" not in text
                assert "DENG" not in text

    with caplog.at_level(logging.INFO):
        asyncio.run(probe())

    assert "raised an unexpected exception" not in caplog.text
    assert "Traceback (most recent call last)" not in caplog.text
    assert "221100" not in caplog.text


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
    import uvicorn
    from sinan_mcp.public_admission import PublicAdmissionGuard

    monkeypatch.setenv("SINAN_PUBLIC_HOST", "sinan-public.example.org")
    monkeypatch.setenv("PORT", "10000")
    captured = {}
    def fake_app(**kwargs):
        captured["mcp_settings"] = kwargs
        return object()
    def fake_run(app, **kwargs):
        captured["guard"] = app
        captured["uvicorn_settings"] = kwargs

    monkeypatch.setattr(public.mcp, "streamable_http_app", fake_app)
    monkeypatch.setattr(uvicorn, "run", fake_run)
    public.start()
    assert isinstance(captured["guard"], PublicAdmissionGuard)
    assert captured["guard"].requests_per_minute == 300
    assert captured["guard"].max_in_flight == 16
    mcp = captured["mcp_settings"]
    assert mcp["stateless_http"] is True
    assert mcp["json_response"] is True
    assert mcp["max_request_body_size"] <= 16384
    assert mcp["streamable_http_path"] == "/mcp"
    assert mcp["host"] == "0.0.0.0"
    security = mcp["transport_security"]
    assert security.enable_dns_rebinding_protection is True
    assert "sinan-public.example.org" in security.allowed_hosts
    assert "https://chatgpt.com" in security.allowed_origins
    assert captured["uvicorn_settings"]["workers"] == 1
    assert captured["uvicorn_settings"]["proxy_headers"] is False
    assert captured["uvicorn_settings"]["access_log"] is False


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
            }
            assert all(not n.startswith(("importar", "diagnosticar",
                                        "auditar", "query_sql")) for n in names)
            # The public plugin directory requires explicit safety hints on
            # every advertised tool; default/omitted annotations are unsafe.
            for t in tools:
                assert t.annotations is not None, t.name
                assert t.annotations.read_only_hint is True, t.name
                assert t.annotations.destructive_hint is False, t.name
                assert t.annotations.open_world_hint is False, t.name
                serialized = t.annotations.model_dump(by_alias=True, exclude_none=True)
                assert serialized["readOnlyHint"] is True, t.name
                assert serialized["destructiveHint"] is False, t.name
                assert serialized["openWorldHint"] is False, t.name
            r = await client.call_tool("contar_notificacoes", {
                "agravo": "TUBE", "ano_inicio": 2024, "ano_fim": 2024,
                "uf": "PI", "por": "raca_cor",
            })
            assert not r.is_error
            assert r.structured_content["proveniencia"]["fonte"] == "synthetic-in-code/v2"
            r2 = await client.call_tool("listar_bases", {})
            assert not r2.is_error
            assert r2.structured_content["dados_reais_disponiveis"] is False

    asyncio.run(probe())


@pytest.mark.parametrize("key,value", [
    ("SINAN_PUBLIC_RATE_PER_MINUTE", "301"),
    ("SINAN_PUBLIC_RATE_PER_MINUTE", "12000"),
    ("SINAN_PUBLIC_MAX_IN_FLIGHT", "17"),
    ("SINAN_PUBLIC_MAX_IN_FLIGHT", "128"),
])
def test_public_daemon_fails_closed_on_relaxed_env_caps(monkeypatch, key, value):
    monkeypatch.setenv("SINAN_PUBLIC_HOST", "sinan-public.example.org")
    monkeypatch.setenv("PORT", "10000")
    monkeypatch.setenv(key, value)
    # No network socket is opened. Reject before uvicorn.run.
    with pytest.raises(ValueError, match="fora do intervalo seguro"):
        public.start()
