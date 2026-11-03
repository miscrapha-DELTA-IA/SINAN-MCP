"""No-network tests for explicit official document availability probes."""
from __future__ import annotations

from urllib.error import HTTPError, URLError

import pytest

from sinan_mcp import document_link_probe as probe


class _HeadResponse:
    def __init__(self, url, status=200, mime="application/pdf"):
        self._url = url
        self.status = status
        self.headers = {"Content-Type": mime}
    def geturl(self):
        return self._url
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False


def test_fixed_official_pdf_head_only_and_no_promotion(monkeypatch):
    seen = []
    def fake_head(url):
        seen.append(url)
        return _HeadResponse(url, 200, "application/pdf; charset=binary")
    monkeypatch.setattr(probe, "_head", fake_head)
    result = probe.monitorar_link_documental("TUBE", 2024)
    assert len(seen) == 1
    assert seen[0].startswith("https://portalsinan.saude.gov.br/")
    assert result["estado_disponibilidade"] == "head_pdf_respondeu"
    assert result["metodo"] == "HEAD"
    assert result["documento_transferido"] is False
    assert result["redirecionamentos_seguidos"] is False
    assert not result["arquivo_anual_verificado"]
    assert not result["aplicabilidade_ao_ano_verificada"]
    assert not result["autoriza_publicacao"]


def test_http_errors_and_bad_content_type_are_not_false_file_absence(monkeypatch):
    url = "https://portalsinan.saude.gov.br/some.pdf"
    monkeypatch.setattr(probe, "_head",
                        lambda official_url: _HeadResponse(official_url, 200, "text/html"))
    invalid = probe.monitorar_link_documental("DENG", 2024)
    assert invalid["estado_disponibilidade"] == "resposta_nao_conclusiva"
    assert not invalid["content_type_pdf_reportado"]
    def denied(_):
        raise HTTPError(url, 405, "method unavailable", {}, None)
    monkeypatch.setattr(probe, "_head", denied)
    denied_result = probe.monitorar_link_documental("CHIK", 2024)
    assert denied_result["estado_disponibilidade"] == "http_restrito_ou_indisponivel"
    assert denied_result["http_status_observado"] == 405
    assert denied_result["autoriza_publicacao"] is False


def test_redirect_handler_will_not_follow():
    blocker = probe._NoRedirect()
    with pytest.raises(RuntimeError, match="redirecionado"):
        blocker.redirect_request(None, None, 301, "Moved", {},
                                 "http://127.0.0.1/private")


def test_probe_handles_redirect_and_tls_failure_without_leaking(monkeypatch):
    def redirected(_):
        raise RuntimeError("blocked redirect to internal")
    monkeypatch.setattr(probe, "_head", redirected)
    result = probe.monitorar_link_documental("TUBE", 2024)
    assert result["estado_disponibilidade"] == "rede_ou_redirecionamento_nao_conclusivo"
    assert "internal" not in str(result)
    monkeypatch.setattr(probe, "_head",
                        lambda _: (_ for _ in ()).throw(URLError("secret token")))
    failed = probe.monitorar_link_documental("TUBE", 2024)
    assert "secret token" not in str(failed)
    assert failed["http_status_observado"] is None


def test_unregistered_year_refused_before_network(monkeypatch):
    monkeypatch.setattr(probe, "_head",
                        lambda *_: pytest.fail("No network for unregistered year"))
    with pytest.raises(ValueError, match="Nenhum documento"):
        probe.monitorar_link_documental("TUBE", 2023)


def test_actual_request_constructor_enforces_head_and_timeout(monkeypatch):
    requests = []
    class FakeOpener:
        def open(self, request, *, timeout):
            requests.append((request, timeout))
            return _HeadResponse(request.full_url)
    monkeypatch.setattr(probe.urllib.request, "build_opener",
                        lambda *handlers: FakeOpener())
    with probe._head("https://portalsinan.saude.gov.br/fake.pdf"):
        pass
    assert len(requests) == 1
    assert requests[0][0].get_method() == "HEAD"
    assert requests[0][1] <= 8
