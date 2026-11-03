"""Explicit ADMINISTRATIVE discovery of the Zika dictionary CKAN resource.

Network is used only by the operator-invoked CLI command, never by the public
MCP, regular coverage/roadmap queries or imports. GETs ONE fixed official
CKAN package metadata endpoint, with size/time bounds, HTTPS verification
and redirects disabled. Does not GET PDF, ZIP, datasets or patient records.

The CKAN endpoint is a discovery candidate: availability has not been
confirmed from this environment. Fail closed if unavailable or inconsistent.
"""
from __future__ import annotations

import json
import re
import socket
import ssl
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler, Request, build_opener,
)

PACKAGE = "arboviroses-zika-virus"
PACKAGE_ID = "4557ba96-7d52-4a56-bd6f-f99a5af09f77"
CKAN_ENDPOINT = (
    "https://ckan-dadosabertos.saude.gov.br/api/3/action/"
    "package_show?id=arboviroses-zika-virus"
)
RESOURCE_PAGE_BASE = (
    "https://dadosabertos.saude.gov.br/dataset/"
    "arboviroses-zika-virus/resource/"
)
DOWNLOAD_HOST = "s3.sa-east-1.amazonaws.com"
DOWNLOAD_PREFIX = "/ckan.saude.gov.br/SINAN/Zikavirus/pdf/"
UUID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
PDF_NAME = re.compile(r"[A-Za-z0-9_.-]{1,160}\.pdf\Z", re.IGNORECASE)
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_RESOURCES = 80
TIMEOUT = 8


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _no_dupes(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("Campo JSON duplicado no catálogo remoto")
        out[key] = value
    return out


def _normalize_title(value):
    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(
        character for character in normalized
        if not unicodedata.combining(character)
    ).strip().casefold()


def _download_pdf_url(value):
    """Return an exact allowed URL or None; never return a rejected input."""
    if not isinstance(value, str) or len(value) > 512:
        return None
    try:
        url = urlsplit(value)
        if (
            url.scheme != "https"
            or url.hostname != DOWNLOAD_HOST
            or url.username is not None
            or url.password is not None
            or url.port not in (None, 443)
            or url.query
            or url.fragment
            or "\\" in value
            or "%" in value
            or url.path.count("//")
            or not url.path.startswith(DOWNLOAD_PREFIX)
        ):
            return None
        tail = url.path[len(DOWNLOAD_PREFIX):]
        if not PDF_NAME.fullmatch(tail) or ".." in tail:
            return None
        return value
    except ValueError:
        return None


def _read_ckan_json():
    """Bounded request to ONE fixed public metadata endpoint."""
    request = Request(
        CKAN_ENDPOINT, headers={"Accept": "application/json",
                                "User-Agent": "SINAN-MCP-documental-audit/0.4"},
        method="GET",
    )
    opener = build_opener(_NoRedirect())
    with opener.open(request, timeout=TIMEOUT) as response:
        if response.geturl() != CKAN_ENDPOINT:
            raise ValueError("Redirecionamento de recurso de metadados proibido")
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type.lower():
            raise ValueError("Resposta remota não é JSON CKAN")
        size_header = response.headers.get("Content-Length")
        if size_header:
            if not size_header.isdigit() or int(size_header) > MAX_JSON_BYTES:
                raise ValueError("Tamanho de metadados fora do limite")
        raw = response.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("Metadados remotos excedem limite")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_no_dupes)


def identificar_dicionario_zika_no_ckan(payload=None):
    """Validate an official CKAN package metadata envelope; zero PDF reads.

    An external payload may be supplied by tests. Without one, ONLY a
    deliberate invocation contacts the predetermined metadata API.
    """
    if payload is None:
        payload = _read_ckan_json()
    if (
        not isinstance(payload, dict)
        or payload.get("success") is not True
        or not isinstance(payload.get("result"), dict)
    ):
        raise ValueError("Envelope de catálogo CKAN inválido")
    package = payload["result"]
    if (package.get("id") != PACKAGE_ID or package.get("name") != PACKAGE):
        raise ValueError("Conjunto CKAN diferente do Sinan/Vírus Zika")
    resources = package.get("resources")
    if not isinstance(resources, list) or not 1 <= len(resources) <= MAX_RESOURCES:
        raise ValueError("Lista de recursos CKAN inválida")
    matches = [
        x for x in resources
        if isinstance(x, dict)
        and _normalize_title(x.get("name")) == "dicionario de dados - zika virus"
    ]
    if len(matches) != 1:
        raise ValueError("Dicionário Zika ausente ou ambíguo no catálogo")
    record = matches[0]
    resource_id = record.get("id")
    if not isinstance(resource_id, str) or not UUID.fullmatch(resource_id):
        raise ValueError("UUID do dicionário Zika inválido")
    if _normalize_title(record.get("format")) != "pdf":
        raise ValueError("Formato de dicionário não é PDF")
    safe_pdf = _download_pdf_url(record.get("url"))
    return {
        "schema_version": "sinan-zika-ckan-dictionary-discovery-v1",
        "agravo": "ZIKA",
        "ano_do_arquivo_pretendido": 2024,
        "fonte": "Metadados de recurso no CKAN do Portal SUS",
        "recurso_uuid_documentado": resource_id,
        "pagina_recurso_oficial": RESOURCE_PAGE_BASE + resource_id,
        "titulo": "Dicionário de dados - Zika Vírus",
        "formato": "PDF",
        "pdf_url_apenas_se_host_e_caminho_permitidos": safe_pdf,
        "url_pdf_validada_estruturalmente": safe_pdf is not None,
        "pdf_baixado": False,
        "pdf_conteudo_lido": False,
        "ano_do_dicionario_confirmado": False,
        "compatibilidade_layout_2024_verificada": False,
        "arquivo_anual_2024_autenticado": False,
        "data_corte_2024_confirmada": False,
        "indicador_homologado": False,
        "publicacao_autorizada": False,
        "status": "RECURSO_DICIONARIO_IDENTIFICADO_POR_METADADOS_NAO_AUDITADO",
        "aviso": (
            "UUID e formato foram encontrados em metadados do conjunto oficial, "
            "não em uma auditoria do PDF. URL rejeitada não é exibida. "
            "Não houve download de dicionário, ZIP ou dados clínicos. "
            "Nenhuma aplicabilidade a 2024 foi estabelecida."
        ),
    }


def classificar_falha_descoberta(exc: Exception) -> str:
    """Operator-safe failure category, without server body, URLs or credentials.

    Never claim a particular root cause unless the exception establishes it.
    No additional network requests, logs or local file reads occur here.
    """
    if isinstance(exc, HTTPError):
        status = exc.code
        if type(status) is not int or not 100 <= status <= 599:
            return "STATUS_HTTP_INVALIDO"
        if 300 <= status <= 399:
            return "REDIRECIONAMENTO_HTTP_BLOQUEADO"
        return f"HTTP_{status}"
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return "TIMEOUT"
    if isinstance(exc, ssl.SSLError):
        return "TLS_CERTIFICADO_OU_CONEXAO"
    if isinstance(exc, URLError):
        reason = exc.reason
        if isinstance(reason, socket.gaierror):
            return "DNS_NAO_RESOLVE"
        if isinstance(reason, (socket.timeout, TimeoutError)):
            return "TIMEOUT"
        if isinstance(reason, ssl.SSLError):
            return "TLS_CERTIFICADO_OU_CONEXAO"
        if isinstance(reason, ConnectionRefusedError):
            return "CONEXAO_RECUSADA"
        reason_class = str(reason).lower()
        if any(token in reason_class for token in (
            "getaddrinfo", "name or service not known", "name resolution",
            "nodename nor servname", "no such host",
        )):
            return "DNS_NAO_RESOLVE"
        if "timed out" in reason_class or "timeout" in reason_class:
            return "TIMEOUT"
        if "certificate" in reason_class or "tls" in reason_class:
            return "TLS_CERTIFICADO_OU_CONEXAO"
        return "CONEXAO_FALHOU_SEM_CAUSA_CONFIRMADA"
    if isinstance(exc, json.JSONDecodeError):
        return "RESPOSTA_JSON_INVALIDA"
    if isinstance(exc, UnicodeError):
        return "RESPOSTA_CODIFICACAO_INVALIDA"
    if isinstance(exc, ValueError):
        msg = str(exc)
        if msg in frozenset({
            "HTML_SEM_UUID_DOCUMENTAL_VERIFICAVEL",
            "HTML_OFICIAL_INVALIDO",
            "HTML_EXCEDE_LIMITE",
            "HTML_JSON_ESTRUTURA_EXCEDE_LIMITE",
            "HTML_METADADOS_AMBIGUOS",
            "SCRIPT_HTML_EXCEDE_LIMITE",
            "RECURSO_DOCUMENTAL_AMBIGUO",
            "UUID_DOCUMENTAL_INVALIDO",
            "FORMATO_DOCUMENTAL_DIVERGENTE",
            "PAGINA_OFICIAL_NAO_HTML",
            "REDIRECIONAMENTO_PAGINA_OFICIAL",
        }):
            return msg
        if "Dicionário Zika ausente ou ambíguo" in msg:
            return "RECURSO_AUSENTE_OU_AMBIGUO"
        if "Conjunto CKAN diferente" in msg:
            return "PACOTE_CKAN_DIVERGENTE"
        if "não é JSON CKAN" in msg:
            return "RESPOSTA_NAO_JSON"
        if "Redirecionamento" in msg:
            return "REDIRECIONAMENTO_BLOQUEADO"
        if "excedem limite" in msg or "fora do limite" in msg:
            return "RESPOSTA_EXCEDE_LIMITE"
        return "METADADOS_CKAN_REJEITADOS"
    if isinstance(exc, OSError):
        if isinstance(exc, socket.gaierror):
            return "DNS_NAO_RESOLVE"
        if isinstance(exc, ConnectionRefusedError):
            return "CONEXAO_RECUSADA"
        return "ERRO_SISTEMA_OU_REDE_INDETERMINADO"
    return "FALHA_INDETERMINADA"
