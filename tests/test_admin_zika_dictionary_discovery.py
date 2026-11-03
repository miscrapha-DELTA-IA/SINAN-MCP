"""CKAN Zika dictionary resource lookup: synthetic metadata only, never PDF."""
from __future__ import annotations

import copy
import inspect
import json
import subprocess
import sys

import pytest

from sinan_mcp import admin_zika_dictionary_discovery as discovery

RESOURCE_ID = "8b0a4c29-b39a-4700-b531-01d71a7fb06a"
# This mock URL is intentionally NOT claimed as an existing Ministry file.
MOCK_PDF = (
    "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/"
    "SINAN/Zikavirus/pdf/DICIONARIO_EXEMPLO_ZIKA.pdf"
)


def fixture_metadata():
    return {
        "success": True,
        "result": {
            "id": discovery.PACKAGE_ID,
            "name": discovery.PACKAGE,
            "resources": [
                {"id": "264978ca-f795-4940-b5d3-ebc21e7d1c7c",
                 "name": "Zika Vírus - 2024", "format": "JSON",
                 "url": "https://example.invalid/never-requested"},
                {"id": RESOURCE_ID, "name": "Dicionário de dados - Zika Vírus",
                 "format": "PDF", "url": MOCK_PDF},
            ],
        },
    }


def test_only_exact_official_package_and_dictionary_title_accepted():
    result = discovery.identificar_dicionario_zika_no_ckan(fixture_metadata())
    assert result["agravo"] == "ZIKA"
    assert result["recurso_uuid_documentado"] == RESOURCE_ID
    assert result["pagina_recurso_oficial"] == (
        discovery.RESOURCE_PAGE_BASE + RESOURCE_ID
    )
    assert result["url_pdf_validada_estruturalmente"] is True
    assert result["pdf_url_apenas_se_host_e_caminho_permitidos"] == MOCK_PDF
    assert result["pdf_baixado"] is False
    assert result["pdf_conteudo_lido"] is False
    assert result["ano_do_dicionario_confirmado"] is False
    assert result["compatibilidade_layout_2024_verificada"] is False
    assert result["data_corte_2024_confirmada"] is False
    assert result["indicador_homologado"] is False
    assert result["publicacao_autorizada"] is False


@pytest.mark.parametrize("mutation", [
    lambda doc: doc.update(success=False),
    lambda doc: doc["result"].update(id="e" * 36),
    lambda doc: doc["result"].update(name="arboviroses-dengue"),
    lambda doc: doc["result"].update(resources=[]),
    lambda doc: doc["result"].update(resources=[1] * 81),
    lambda doc: doc["result"]["resources"].append(
        copy.deepcopy(doc["result"]["resources"][1])
    ),
    lambda doc: doc["result"]["resources"][1].update(
        name="Dicionário de dados - Dengue"
    ),
    lambda doc: doc["result"]["resources"][1].update(format="XLSX"),
    lambda doc: doc["result"]["resources"][1].update(id="not-uuid"),
    lambda doc: doc["result"]["resources"][1].update(id=True),
    lambda doc: doc["result"]["resources"][1].update(format=True),
])
def test_ambiguous_or_inconsistent_resources_fail_closed(mutation):
    doc = fixture_metadata()
    mutation(doc)
    with pytest.raises(ValueError):
        discovery.identificar_dicionario_zika_no_ckan(doc)


@pytest.mark.parametrize("badurl", [
    "http://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/pdf/f.pdf",
    "https://s3.sa-east-1.amazonaws.com.evil/ckan.saude.gov.br/SINAN/Zikavirus/pdf/f.pdf",
    "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Dengue/pdf/f.pdf",
    "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/pdf/../f.pdf",
    "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/pdf/%2e%2e/f.pdf",
    "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/pdf/f.pdf?x=1",
    "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/pdf/f.exe",
    "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/pdf/f.pdf#fragment",
    None,
    True,
])
def test_unapproved_download_url_never_leaks_to_operator_output(badurl):
    doc = fixture_metadata()
    doc["result"]["resources"][1]["url"] = badurl
    result = discovery.identificar_dicionario_zika_no_ckan(doc)
    assert result["url_pdf_validada_estruturalmente"] is False
    assert result["pdf_url_apenas_se_host_e_caminho_permitidos"] is None
    assert result["pagina_recurso_oficial"].startswith(
        "https://dadosabertos.saude.gov.br/dataset/"
    )
    assert result["publicacao_autorizada"] is False


def test_reader_only_requests_fixed_ckan_json_with_limit_and_no_redirect(monkeypatch):
    raw = json.dumps(fixture_metadata()).encode("utf-8")
    class Response:
        headers = {"Content-Type": "application/json", "Content-Length": str(len(raw))}
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return None
        def geturl(self):
            return discovery.CKAN_ENDPOINT
        def read(self, n):
            assert n == discovery.MAX_JSON_BYTES + 1
            return raw
    class Opener:
        def open(self, request, timeout):
            assert request.full_url == discovery.CKAN_ENDPOINT
            assert request.get_method() == "GET"
            assert timeout == discovery.TIMEOUT
            return Response()
    def fake_builder(handler):
        assert isinstance(handler, discovery._NoRedirect)
        return Opener()
    monkeypatch.setattr(discovery, "build_opener", fake_builder)
    assert discovery._read_ckan_json() == fixture_metadata()
    assert discovery.identificar_dicionario_zika_no_ckan()[
        "recurso_uuid_documentado"] == RESOURCE_ID


def test_bounded_reader_rejects_wrong_media_and_redirects(monkeypatch):
    class Response:
        headers = {"Content-Type": "text/html"}
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return None
        def geturl(self):
            return "https://wrong.example.invalid/other"
    class Opener:
        def open(self, request, timeout):
            return Response()
    monkeypatch.setattr(discovery, "build_opener", lambda _: Opener())
    with pytest.raises(ValueError):
        discovery._read_ckan_json()


def test_cli_is_explicit_admin_command_without_network_when_help_requested(tmp_path):
    p = subprocess.run(
        [sys.executable, "-m", "sinan_mcp",
         "identificar-dicionario-zika-ckan", "--help"],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert p.returncode == 0, p.stderr
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "sinan.sqlite3").exists()


def test_existing_offline_readiness_is_unmodified():
    from sinan_mcp.multiagravo_readiness import diagnosticar_cobertura_multiagravo
    from sinan_mcp.zika_portal_context import consultar_contexto_portal_zika_2024
    snapshot = diagnosticar_cobertura_multiagravo(2024)
    assert snapshot["agravos_referenciados"] == 14
    assert snapshot["agravos_com_documentacao_localizada"] == 12
    assert snapshot["distribuicoes_catalogadas"] == 5
    assert snapshot["publicacao_automatica"] is False
    ctx = consultar_contexto_portal_zika_2024()
    assert ctx["url_exata_pdf_dicionario_zika_recuperada"] is None
    assert ctx["conteudo_pdf_dicionario_zika_auditado"] is False


def test_discovery_is_not_imported_by_public_mcp_or_offline_diagnostic():
    from sinan_mcp import public_server, multiagravo_readiness
    assert "admin_zika_dictionary_discovery" not in inspect.getsource(public_server)
    assert "admin_zika_dictionary_discovery" not in inspect.getsource(multiagravo_readiness)
