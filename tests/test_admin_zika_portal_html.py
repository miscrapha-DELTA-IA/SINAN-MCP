"""Official HTML metadata-only Zika document discovery, fully offline synthetic tests."""
from __future__ import annotations

import json
import inspect
import subprocess
import sys

import pytest

from sinan_mcp import admin_zika_portal_html as portal
from sinan_mcp.admin_zika_dictionary_discovery import classificar_falha_descoberta

DICT_ID = "a89df117-8b2f-4eb3-8bdc-93aa645e97ab"  # synthetic, not an actual Ministry UUID
KNOWN_ID = "264978ca-f795-4940-b5d3-ebc21e7d1c7c"  # verified 2024 metadata identifier
PDF = (
    "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/"
    "SINAN/Zikavirus/pdf/ZIKA_TEST_ONLY.pdf"
)


def fake_html(dictionary_id=DICT_ID, pdf_url=PDF, fmt="PDF"):
    obj = {"props": {"pageProps": {"dataset": {
        "id": portal.PACKAGE_ID,
        "name": portal.PACKAGE,
        "resources": [
            {"id": KNOWN_ID, "name": "Zika Vírus - 2024", "format": "JSON"},
            {"id": dictionary_id, "name": "Dicionário de dados - Zika Vírus",
             "format": fmt, "url": pdf_url},
        ]
    }}}}
    return (
        '<!doctype html><html><head><script id="__NEXT_DATA__" '
        'type="application/json">' + json.dumps(obj, ensure_ascii=False) +
        '</script></head><body>Sinan/Vírus Zika</body></html>'
    )


def test_script_metadata_identity_and_restriction_states():
    result = portal.descobrir_dicionario_zika_pagina(fake_html())
    assert result["recurso_uuid_documentado"] == DICT_ID
    assert result["pagina_recurso_oficial"] == portal.RESOURCE_PAGE_BASE + DICT_ID
    assert result["metodo_de_evidencia"] == "json_embutido_no_html_oficial"
    assert result["formato_declarado_no_html"] == "PDF"
    assert result["url_pdf_aprovada_estruturalmente"] == PDF
    assert result["arquivo_pdf_baixado"] is False
    assert result["conteudo_pdf_auditado"] is False
    assert result["dicionario_aplicavel_a_2024_validado"] is False
    assert result["dados_clinicos_acessados"] is False
    assert result["indicador_real_homologado"] is False
    assert result["publicacao_autorizada"] is False


def test_official_anchor_fallback_cannot_claim_pdf_format():
    html = (
        '<html><body>'
        f'<a href="/dataset/arboviroses-zika-virus/resource/{KNOWN_ID}">'
        'Zika Vírus - 2024</a>'
        f'<a href="/dataset/arboviroses-zika-virus/resource/{DICT_ID}">'
        'Dicionário de dados - Zika Vírus</a></body></html>'
    )
    result = portal.descobrir_dicionario_zika_pagina(html)
    assert result["metodo_de_evidencia"] == "link_publico_no_html_oficial"
    assert result["formato_declarado_no_html"] == "INDETERMINADO"
    assert result["url_pdf_aprovada_estruturalmente"] is None
    assert result["conteudo_pdf_auditado"] is False


@pytest.mark.parametrize("html", [
    "<html><body>Dicionário de dados - Zika Vírus</body></html>",
    '<html><a href="/dataset/arboviroses-zika-virus/resource/'
    + DICT_ID + '">Dicionário de dados - Zika Vírus</a></html>',
    fake_html().replace(KNOWN_ID, "00000000-0000-0000-0000-000000000000"),
    fake_html().replace(portal.PACKAGE_ID, "00000000-0000-0000-0000-000000000000"),
    fake_html(dictionary_id="not-real"),
    fake_html(fmt="CSV"),
    fake_html().replace('"Dicionário de dados - Zika Vírus"',
                        '"Dicionário de dados - Dengue"'),
])
def test_html_missing_or_mismatched_evidence_fails_closed(html):
    with pytest.raises(ValueError):
        portal.descobrir_dicionario_zika_pagina(html)


def test_invalid_pdf_url_not_exposed_even_if_dictionary_uuid_found():
    html = fake_html(pdf_url="https://evil.example.invalid/malware.pdf")
    result = portal.descobrir_dicionario_zika_pagina(html)
    assert result["recurso_uuid_documentado"] == DICT_ID
    assert result["url_pdf_aprovada_estruturalmente"] is None
    assert result["conteudo_pdf_auditado"] is False


def test_single_official_html_request_fixed_host_no_redirects(monkeypatch):
    html = fake_html()
    data = html.encode("utf-8")
    class Response:
        headers = {"Content-Type": "text/html; charset=utf-8",
                   "Content-Length": str(len(data))}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def geturl(self):
            return portal.PAGE
        def read(self, n):
            assert n == portal.MAX_BYTES + 1
            return data
    class Opener:
        def open(self, req, timeout):
            assert req.full_url == portal.PAGE
            assert req.get_method() == "GET"
            assert timeout == portal.TIMEOUT_SECONDS
            return Response()
    def mock_opener(handler):
        assert isinstance(handler, portal._NoRedirect)
        return Opener()
    monkeypatch.setattr(portal, "build_opener", mock_opener)
    assert portal.descobrir_dicionario_zika_pagina()[
        "recurso_uuid_documentado"] == DICT_ID


def test_admin_command_aliases_exist_without_network_on_help(tmp_path):
    for command in ("identificar-dicionario-zika-portal",
                    "identificar-dicionario-zika-ckan"):
        result = subprocess.run(
            [sys.executable, "-m", "sinan_mcp", command, "--help"],
            cwd=tmp_path, capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr
    assert not (tmp_path / "sinan.sqlite3").exists()


def test_fail_closed_categories_for_missing_html_identity():
    assert classificar_falha_descoberta(
        ValueError("HTML_SEM_UUID_DOCUMENTAL_VERIFICAVEL")
    ) == "HTML_SEM_UUID_DOCUMENTAL_VERIFICAVEL"


def test_existing_public_diagnostics_remain_unchanged():
    from sinan_mcp.multiagravo_readiness import diagnosticar_cobertura_multiagravo
    from sinan_mcp import public_server
    cov = diagnosticar_cobertura_multiagravo(2024)
    assert cov["agravos_referenciados"] == 14
    assert cov["agravos_com_documentacao_localizada"] == 12
    assert cov["distribuicoes_catalogadas"] == 5
    assert cov["publicacao_automatica"] is False
    assert "admin_zika_portal_html" not in inspect.getsource(public_server)


def test_known_nextjs_build_id_is_validated_without_extra_network():
    import json
    html = (
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps({"buildId": "HJKl1234_ABCD"})
        + '</script>'
    )
    assert portal._extract_build_id(html) == "HJKl1234_ABCD"
    with pytest.raises(ValueError):
        portal._extract_build_id(
            '<script type="application/json">{"buildId":"../evil"}</script>'
        )


def test_nextjs_hydration_returns_metadata_only(monkeypatch):
    import json
    build_id = "HJKl1234_ABCD"
    html = (
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps({"buildId": build_id})
        + '</script>'
    )
    page_props = {
        "id": portal.PACKAGE_ID,
        "name": portal.PACKAGE,
        "resources": [
            {"id": KNOWN_ID, "name": "Zika Vírus - 2024", "format": "JSON"},
            {"id": DICT_ID, "name": "Dicionário de dados - Zika Vírus",
             "format": "PDF", "url": PDF},
        ],
    }
    monkeypatch.setattr(portal, "_read_public_html", lambda: html)
    def mock_nextjs(actual_id):
        assert actual_id == build_id
        return {"pageProps": page_props}
    monkeypatch.setattr(portal, "_read_nextjs_dataset_json", mock_nextjs)
    report = portal.descobrir_dicionario_zika_portal()
    assert report["metodo_de_evidencia"] == "nextjs_hidratacao_json_oficial"
    assert report["recurso_uuid_documentado"] == DICT_ID
    assert report["url_pdf_aprovada_estruturalmente"] == PDF
    assert report["arquivo_pdf_baixado"] is False
    assert report["conteudo_pdf_auditado"] is False
    assert report["dicionario_aplicavel_a_2024_validado"] is False
    assert report["indicador_real_homologado"] is False
    assert report["publicacao_autorizada"] is False


def test_nextjs_response_only_uses_official_same_origin(monkeypatch):
    import json
    raw = json.dumps({"pageProps": {"id": portal.PACKAGE_ID}}).encode("utf-8")
    class Response:
        headers = {"Content-Type": "application/json", "Content-Length": str(len(raw))}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def geturl(self):
            return (
                portal.PAGE.replace("/dataset/arboviroses-zika-virus", "")
                + "/_next/data/HJKl1234_ABCD/dataset/"
                "arboviroses-zika-virus.json?slug=arboviroses-zika-virus"
            )
        def read(self, n):
            assert n == portal.MAX_BYTES + 1
            return raw
    class Opener:
        def open(self, req, timeout):
            assert req.full_url == Response().geturl()
            assert req.get_method() == "GET"
            assert timeout == portal.TIMEOUT_SECONDS
            return Response()
    def safe_build_opener(handler):
        assert isinstance(handler, portal._NoRedirect)
        return Opener()
    monkeypatch.setattr(portal, "build_opener", safe_build_opener)
    assert portal._read_nextjs_dataset_json("HJKl1234_ABCD") == {
        "pageProps": {"id": portal.PACKAGE_ID}
    }
    with pytest.raises(ValueError):
        portal._read_nextjs_dataset_json("../traverse")


def test_nextjs_failure_uses_html_fallback_without_claiming_pdf(monkeypatch):
    html = (
        '<script id="__NEXT_DATA__" type="application/json">'
        '{"buildId":"HJKl1234_ABCD"}</script>'
        f'<a href="/dataset/arboviroses-zika-virus/resource/{KNOWN_ID}">'
        'Zika Vírus - 2024</a>'
        f'<a href="/dataset/arboviroses-zika-virus/resource/{DICT_ID}">'
        'Dicionário de dados - Zika Vírus</a>'
    )
    monkeypatch.setattr(portal, "_read_public_html", lambda: html)
    def unavailable(_):
        raise ValueError("NEXTJS_METADADOS_INVALIDOS")
    monkeypatch.setattr(portal, "_read_nextjs_dataset_json", unavailable)
    result = portal.descobrir_dicionario_zika_portal()
    assert result["metodo_de_evidencia"] == "link_publico_no_html_oficial"
    assert result["formato_declarado_no_html"] == "INDETERMINADO"
    assert result["conteudo_pdf_auditado"] is False


def test_both_portal_discovery_methods_fail_closed_when_unknown(monkeypatch):
    monkeypatch.setattr(portal, "_read_public_html", lambda: "<html>No links</html>")
    with pytest.raises(ValueError, match="NEXTJS_E_HTML_SEM_UUID_DOCUMENTAL_VALIDADO"):
        portal.descobrir_dicionario_zika_portal()
