"""Admin-only ZIKA dictionary discovery from the official SUS dataset HTML.

The current public portal is a Next.js frontend; its internal CKAN host
cannot be assumed to resolve and traditional /api/3/action routes are not
a reliable public interface. Read ONE fixed public dataset PAGE, never
download PDF, ZIP, case data, API keys or binary datasets.

Discovery is best-effort and MUST fail closed if the actual HTML does not
contain enough trustworthy identity information.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .admin_zika_dictionary_discovery import (
    _download_pdf_url, _normalize_title, classificar_falha_descoberta,
    UUID, PACKAGE, PACKAGE_ID, RESOURCE_PAGE_BASE,
    _no_dupes, identificar_dicionario_zika_no_ckan,
)

PAGE = "https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus"
TARGET = "dicionario de dados - zika virus"
KNOWN_ANNUAL_IDS = frozenset({
    "264978ca-f795-4940-b5d3-ebc21e7d1c7c",  # JSON 2024
    "41bfda2a-5826-4ef9-8913-497247e6c9ce",  # PARQUET 2024
})
MAX_BYTES = 3 * 1024 * 1024
MAX_SCRIPT_COUNT = 128
TIMEOUT_SECONDS = 10
RESOURCE_LINK = re.compile(
    r"^(?:https://dadosabertos\.saude\.gov\.br)?"
    r"/dataset/arboviroses-zika-virus/resource/"
    r"([0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})$"
)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class _PublicPage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scripts = []
        self.anchors = []
        self._script = False
        self._anchor_href = None
        self._anchor_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script":
            self._script = True
            self.scripts.append("")
        elif tag == "a":
            self._anchor_href = attrs.get("href")
            self._anchor_text = []

    def handle_data(self, data):
        if self._script and self.scripts:
            self.scripts[-1] += data
        if self._anchor_href is not None:
            self._anchor_text.append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self._script = False
        elif tag == "a":
            if self._anchor_href is not None:
                self.anchors.append((self._anchor_href, "".join(self._anchor_text)))
            self._anchor_href = None
            self._anchor_text = []


def _read_public_html():
    opener = build_opener(_NoRedirect())
    request = Request(
        PAGE,
        method="GET",
        headers={"Accept": "text/html",
                 "User-Agent": "SINAN-MCP-documental-audit/0.4"},
    )
    with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
        if response.geturl() != PAGE:
            raise ValueError("REDIRECIONAMENTO_PAGINA_OFICIAL")
        mime = response.headers.get("Content-Type", "")
        if "text/html" not in mime.lower():
            raise ValueError("PAGINA_OFICIAL_NAO_HTML")
        length = response.headers.get("Content-Length")
        if length and (not length.isdigit() or int(length) > MAX_BYTES):
            raise ValueError("HTML_EXCEDE_LIMITE")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("HTML_EXCEDE_LIMITE")
    return raw.decode("utf-8", errors="strict")


def _bounded_json_tree(text):
    """Parse a complete JSON script, never orphan resource fragments.

    Earlier fragment extraction could discard the parent package UUID and
    accidentally attach an unrelated resources[] list to ZIKA. Only full
    JSON documents with an explicit validated package parent may qualify.
    """
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        return
    if isinstance(parsed, dict):
        yield parsed


def _resource_collections(node):
    """Bounded traversal over parsed inline JSON dictionaries only."""
    stack = [(node, 0)]
    visited = 0
    while stack:
        current, depth = stack.pop()
        visited += 1
        if visited > 5000 or depth > 25:
            raise ValueError("HTML_JSON_ESTRUTURA_EXCEDE_LIMITE")
        if isinstance(current, dict):
            listed = current.get("resources")
            if isinstance(listed, list) and len(listed) <= 200:
                package_id = current.get("id")
                package_name = current.get("name")
                if package_id != PACKAGE_ID or package_name != PACKAGE:
                    continue
                yield listed
            for k, v in current.items():
                if isinstance(v, (dict, list)) and len(str(k)) <= 128:
                    stack.append((v, depth + 1))
        elif isinstance(current, list):
            for item in current[:200]:
                if isinstance(item, (dict, list)):
                    stack.append((item, depth + 1))


def descobrir_dicionario_zika_pagina(html=None):
    """Find a ZIKA dictionary resource in *only* the official page HTML.

    If HTML has no reliably tied resource UUID (a common Next.js issue),
    return an explicit error and do NOT fabricate an ID.
    """
    if html is None:
        html = _read_public_html()
    if not isinstance(html, str) or len(html.encode("utf-8")) > MAX_BYTES:
        raise ValueError("HTML_OFICIAL_INVALIDO")
    parser = _PublicPage()
    parser.feed(html)
    if len(parser.scripts) > MAX_SCRIPT_COUNT:
        raise ValueError("HTML_EXCEDE_LIMITE")
    collections = []
    for script in parser.scripts:
        if len(script) > MAX_BYTES:
            raise ValueError("SCRIPT_HTML_EXCEDE_LIMITE")
        if "resources" not in script:
            continue
        for parsed in _bounded_json_tree(script):
            collections.extend(_resource_collections(parsed))
            if len(collections) > 20:
                raise ValueError("HTML_METADADOS_AMBIGUOS")
    matches = []
    for coll in collections:
        known_ids = {
            item.get("id") for item in coll if isinstance(item, dict)
            and isinstance(item.get("id"), str)
        }
        # At least one known 2024 resource anchors the collection to ZIKA.
        if not (known_ids & KNOWN_ANNUAL_IDS):
            continue
        for item in coll:
            if not isinstance(item, dict):
                continue
            if _normalize_title(item.get("name", item.get("title"))) == TARGET:
                matches.append(item)
    # When Next.js emits identical pageProps twice, identical UUID is fine.
    unique = {item.get("id"): item for item in matches
              if isinstance(item.get("id"), str)}
    if len(unique) == 1:
        record = next(iter(unique.values()))
        rid = record["id"]
        if not UUID.fullmatch(rid):
            raise ValueError("UUID_DOCUMENTAL_INVALIDO")
        fmt = _normalize_title(record.get("format"))
        if fmt not in ("pdf", ""):
            raise ValueError("FORMATO_DOCUMENTAL_DIVERGENTE")
        direct_url = _download_pdf_url(record.get("url")) if fmt == "pdf" else None
        source = "json_embutido_no_html_oficial"
    elif len(unique) > 1:
        raise ValueError("RECURSO_DOCUMENTAL_AMBIGUO")
    else:
        # Anchor links are also official HTML. To avoid associating an
        # unrelated page, they must be accompanied by a known ZIKA/2024 link.
        ids = set()
        target_links = set()
        for href, label in parser.anchors:
            m = RESOURCE_LINK.fullmatch(href) if isinstance(href, str) else None
            if m:
                ids.add(m.group(1))
                if _normalize_title(label) == TARGET:
                    target_links.add(m.group(1))
        if len(target_links) != 1 or not (ids & KNOWN_ANNUAL_IDS):
            raise ValueError("HTML_SEM_UUID_DOCUMENTAL_VERIFICAVEL")
        rid = next(iter(target_links))
        fmt = ""
        direct_url = None
        source = "link_publico_no_html_oficial"
    return {
        "schema_version": "sinan-zika-portal-html-dictionary-discovery-v1",
        "fonte_html_oficial": PAGE,
        "metodo_de_evidencia": source,
        "agravo": "ZIKA",
        "recurso_uuid_documentado": rid,
        "pagina_recurso_oficial": RESOURCE_PAGE_BASE + rid,
        "formato_declarado_no_html": "PDF" if fmt == "pdf" else "INDETERMINADO",
        "url_pdf_aprovada_estruturalmente": direct_url,
        "arquivo_pdf_baixado": False,
        "conteudo_pdf_auditado": False,
        "dicionario_aplicavel_a_2024_validado": False,
        "data_de_corte_2024_confirmada": False,
        "dados_clinicos_acessados": False,
        "indicador_real_homologado": False,
        "publicacao_autorizada": False,
        "status": "REFERENCIA_DOCUMENTAL_IDENTIFICADA_EM_HTML_SEM_AUDITORIA",
    }


# The public Next.js hydration data layer has been documented by PySUS:
# https://github.com/AlertaDengue/PySUS/blob/main/pysus/api/saude/next_data.py
# https://github.com/AlertaDengue/PySUS/blob/main/pysus/api/saude/catalog.py
# No internal hostname, redirect or arbitrary URL is trusted.
BUILD_ID = re.compile(r"[A-Za-z0-9_-]{8,128}\Z")


def _extract_build_id(html):
    parser = _PublicPage()
    parser.feed(html)
    for script in parser.scripts[:MAX_SCRIPT_COUNT]:
        if '"buildId"' not in script:
            continue
        try:
            obj = json.loads(script, object_pairs_hook=_no_dupes)
        except (ValueError, TypeError):
            continue
        if not isinstance(obj, dict):
            continue
        key = obj.get("buildId")
        if isinstance(key, str) and BUILD_ID.fullmatch(key):
            return key
    raise ValueError("BUILD_ID_NAO_LOCALIZADO_NA_PAGINA")


def _read_nextjs_dataset_json(build_id):
    if not isinstance(build_id, str) or not BUILD_ID.fullmatch(build_id):
        raise ValueError("BUILD_ID_INVALIDO")
    url = (
        "https://dadosabertos.saude.gov.br/_next/data/" + build_id
        + "/dataset/arboviroses-zika-virus.json?slug=arboviroses-zika-virus"
    )
    request = Request(
        url, method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "SINAN-MCP-documental-audit/0.4",
        },
    )
    opener = build_opener(_NoRedirect())
    with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
        if response.geturl() != url:
            raise ValueError("REDIRECIONAMENTO_NEXTJS_BLOQUEADO")
        mime = response.headers.get("Content-Type", "")
        if "application/json" not in mime.lower():
            raise ValueError("NEXTJS_RESPONDEU_NAO_JSON")
        length = response.headers.get("Content-Length")
        if length and (not length.isdigit() or int(length) > MAX_BYTES):
            raise ValueError("NEXTJS_JSON_EXCEDE_LIMITE")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("NEXTJS_JSON_EXCEDE_LIMITE")
    parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_dupes)
    if not isinstance(parsed, dict):
        raise ValueError("NEXTJS_METADADOS_INVALIDOS")
    return parsed


def descobrir_dicionario_zika_portal():
    """Two bounded same-origin requests: HTML -> Next.js dataset metadata.

    If the Next.js hydration endpoint has changed or is temporarily
    unavailable, allow only the strict HTML identity fallback. Never use
    the broken CKAN hostname, third-party proxies or data download URLs.
    """
    html = _read_public_html()
    next_data_problem = None
    try:
        build_id = _extract_build_id(html)
        data = _read_nextjs_dataset_json(build_id)
        page_props = data.get("pageProps")
        report = identificar_dicionario_zika_no_ckan(
            {"success": True, "result": page_props}
        )
        return {
            "schema_version": "sinan-zika-nextjs-dictionary-discovery-v1",
            "fonte_html_oficial": PAGE,
            "metodo_de_evidencia": "nextjs_hidratacao_json_oficial",
            "agravo": "ZIKA",
            "recurso_uuid_documentado": report["recurso_uuid_documentado"],
            "pagina_recurso_oficial": report["pagina_recurso_oficial"],
            "formato_declarado_no_html": "PDF",
            "url_pdf_aprovada_estruturalmente": report[
                "pdf_url_apenas_se_host_e_caminho_permitidos"
            ],
            "arquivo_pdf_baixado": False,
            "conteudo_pdf_auditado": False,
            "dicionario_aplicavel_a_2024_validado": False,
            "data_de_corte_2024_confirmada": False,
            "dados_clinicos_acessados": False,
            "indicador_real_homologado": False,
            "publicacao_autorizada": False,
            "status": "REFERENCIA_DOCUMENTAL_NEXTJS_NAO_AUDITADA",
        }
    except (ValueError, OSError, UnicodeError, HTTPError, URLError) as exc:
        next_data_problem = exc

    try:
        return descobrir_dicionario_zika_pagina(html)
    except ValueError as exc:
        if next_data_problem is not None:
            raise ValueError(
                "NEXTJS_E_HTML_SEM_UUID_DOCUMENTAL_VALIDADO"
            ) from next_data_problem
        raise exc
