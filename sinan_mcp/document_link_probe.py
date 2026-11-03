"""Explicit local metadata-only link check for curated official PDF references.

Uses HEAD, not GET. No downloading, scraping, user-supplied URLs, redirects,
clinical files or public MCP endpoints. A 200 / PDF Content-Type does NOT
certify publisher authenticity, edition, integrity or year applicability.
"""
from __future__ import annotations

import urllib.error
import urllib.request

from .year_evidence_registry import consultar_evidencia_agravo_ano

TIMEOUT_SECONDS = 8


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Documento redirecionado: destino não acessado")


def _head(url: str):
    request = urllib.request.Request(
        url, method="HEAD",
        headers={"User-Agent": "SINAN-MCP-Document-Curation/1.0"},
    )
    return urllib.request.build_opener(_NoRedirect).open(
        request, timeout=TIMEOUT_SECONDS
    )


def monitorar_link_documental(agravo: str, ano: int) -> dict:
    """Check only the exact immutable registry URL, never claim year verification."""
    evidence = consultar_evidencia_agravo_ano(agravo, ano)
    row = evidence["evidencia_documental"]
    if row is None:
        raise ValueError("Nenhum documento curado para agravo/ano solicitado")
    url = row["documento_url"]
    status = "nao_verificado"
    method = "HEAD"
    observed_http_status = None
    mime_reported_pdf = False
    try:
        with _head(url) as response:
            if response.geturl() != url:
                raise RuntimeError("URL mudou durante a requisição")
            observed_http_status = int(response.status)
            mime = (response.headers.get("Content-Type") or "").split(";", 1)[0]
            mime_reported_pdf = mime.strip().lower() == "application/pdf"
            if observed_http_status == 200 and mime_reported_pdf:
                status = "head_pdf_respondeu"
            else:
                status = "resposta_nao_conclusiva"
    except urllib.error.HTTPError as exc:
        observed_http_status = int(exc.code)
        status = "http_restrito_ou_indisponivel"
    except (urllib.error.URLError, OSError, TimeoutError, RuntimeError):
        status = "rede_ou_redirecionamento_nao_conclusivo"

    return {
        "schema_version": "sinan-document-link-probe-v1",
        "agravo": evidence["agravo_alias_interno"],
        "ano_do_arquivo_pretendido": evidence["ano_do_arquivo_pretendido"],
        "url_documento_no_catalogo": url,
        "metodo": method,
        "estado_disponibilidade": status,
        "http_status_observado": observed_http_status,
        "content_type_pdf_reportado": mime_reported_pdf,
        "documento_transferido": False,
        "redirecionamentos_seguidos": False,
        "download_microdados": False,
        "conteudo_documento_comparado": False,
        "arquivo_anual_verificado": False,
        "aplicabilidade_ao_ano_verificada": False,
        "autoriza_publicacao": False,
        "aviso": (
            "HEAD é indício de disponibilidade da URL, não autenticação do "
            "conteúdo, código da doença, versão do arquivo ou validade anual. "
            "Falhas de rede/405/403 não provam remoção do documento. "
            "Nenhum dado clínico foi consultado."
        ),
    }
