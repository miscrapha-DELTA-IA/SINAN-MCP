"""Curation-only, zero-network evidence registry for official SINAN documentation.

This is a catalogue of *located Ministry of Health documents*, not a
certificate of an annual file's availability, completeness, dictionary
compatibility, legal status or epidemiological validity. Official-hosted PDF
!= dictionary *verified for the requested data year*.

The public module is immutable, metadata-only and imports NO patient data,
SQLite, PySUS or private admin tools. Future validated annual editions must
be separately attested by a reviewed workflow, not by toggling JSON flags.
"""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from importlib.resources import files
from urllib.parse import urlsplit
from typing import Any

from .official_sources import CONDITIONS

SCHEMA = "sinan-official-year-evidence-v1"
REFERENCE_CODES = frozenset(x[0] for x in CONDITIONS)
PORTAL = "portalsinan.saude.gov.br"
DATA_PORTAL = "www.gov.br"
PDF_PREFIX = "/images/documentos/Agravos/"
# Exact historical directories with URL-encoded spaces on Portal SINAN.
# Other percent escapes, nested paths and unreviewed names are rejected.
ALLOWED_ENCODED_PDF_DIRECTORIES = frozenset({
    "Hepatites%20Virais",
    "Leishmaniose%20Visceral",
    "Leishmaniose%20Tegumentar%20Americana",
})
DATA_PATH = (
    "/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/"
    "svsa/agravos-de-notificacoes/agravos-de-notificacoes"
)
DOCUMENT_KEYS = frozenset({
    "titulo", "instituicao_publicadora", "edicao_documental", "pagina_oficial",
    "url_documento", "tipo", "integridade_binaria_publicada_por_autoridade",
})
DATA_KEYS = frozenset({
    "pagina_oficial", "arquivo_exato_2024", "codigo_download_confirmado",
    "checksum_arquivo_publicado_por_autoridade", "status_consolidacao_2024",
    "sistema_origem_no_ano_confirmado",
})
VALIDATION_KEYS = frozenset({
    "link_de_dicionario_oficial_localizado",
    "arquivo_anual_identificado_independentemente",
    "dicionario_aplicavel_ao_ano_confirmado",
    "esquema_comparado_ao_arquivo_2024",
    "aprovacao_epidemiologica_independente",
    "aprovacao_para_publicar",
})
YEAR_KEYS = frozenset({
    "agravo_alias_interno", "ano_do_arquivo_pretendido",
    "sistema_documentado", "documento", "acesso_dados",
    "validacoes", "limitacoes",
})
NOTICE = (
    "Fonte oficial de DOCUMENTAÇÃO identificada; NÃO foi validada a "
    "correspondência do dicionário com o arquivo do ano, nem o sistema "
    "de origem, checksum oficial do dataset, situação de consolidação, "
    "coorte, indicadores ou autorização para publicar. Sem dados reais."
)


def _pairs_strict(pairs: list[tuple[str, object]]) -> dict:
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ValueError("Chave duplicada no índice de evidências")
        obj[k] = v
    return obj


def _text(value: object, max_size: int = 800) -> str:
    if (not isinstance(value, str) or not 1 <= len(value.strip()) <= max_size
            or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise ValueError("Texto inválido no índice documental")
    return value


def _official_url(url: object, host: str, prefix: str) -> str:
    raw = _text(url, 1024)
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("URL documental inválida") from exc
    encoded_path_ok = False
    if host == PORTAL and prefix == PDF_PREFIX and "%" in parsed.path:
        suffix = (
            parsed.path[len(PDF_PREFIX):]
            if parsed.path.startswith(PDF_PREFIX) else ""
        )
        parts = suffix.split("/")
        encoded_path_ok = (
            len(parts) == 2
            and parts[0] in ALLOWED_ENCODED_PDF_DIRECTORIES
            and re.fullmatch(r"[A-Za-z0-9_.-]+[.]pdf", parts[1]) is not None
        )
    if (parsed.scheme != "https" or parsed.hostname != host
            or parsed.username is not None or parsed.password is not None
            or port not in (None, 443) or parsed.query or parsed.fragment
            or not parsed.path.startswith(prefix)
            or "\\" in raw or ("%" in parsed.path and not encoded_path_ok) or "//" in parsed.path
            or any(ord(c) < 33 for c in raw)):
        raise ValueError("Referência fora do domínio/caminho HTTPS oficial")
    return raw


def validate_registry(payload: object) -> dict:
    """Validate all package-curated metadata; refuse fake approval flags."""
    if (not isinstance(payload, dict) or set(payload) != {
        "schema_version", "catalog_revision", "verified_portal_links_on",
        "scope", "entries",
    } or payload["schema_version"] != SCHEMA):
        raise ValueError("Formato do catálogo de evidência incompatível")
    if (not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}-r[0-9]{1,3}",
                         _text(payload["catalog_revision"], 32))
            or not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}",
                                _text(payload["verified_portal_links_on"], 10))
            or payload["scope"] != (
                "evidencia_documental_de_fontes_oficiais_sem_atestado_de_compatibilidade_ano"
            )):
        raise ValueError("Revisão ou escopo documental não autorizado")
    entries = payload["entries"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= 100:
        raise ValueError("Entradas documentais ausentes ou excessivas")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != YEAR_KEYS:
            raise ValueError("Entrada por agravo/ano malformada")
        code, year = entry["agravo_alias_interno"], entry["ano_do_arquivo_pretendido"]
        if (not isinstance(code, str) or code not in REFERENCE_CODES
                or type(year) is not int or not 1980 <= year <= 2100
                or (code, year) in seen):
            raise ValueError("Alias, ano ou combinação duplicada inválidos")
        seen.add((code, year))
        _text(entry["sistema_documentado"], 120)
        _text(entry["limitacoes"], 1200)
        doc = entry["documento"]
        if not isinstance(doc, dict) or set(doc) != DOCUMENT_KEYS:
            raise ValueError("Metadados de dicionário incompletos")
        for key in ("titulo", "instituicao_publicadora", "edicao_documental"):
            _text(doc[key], 250)
        if doc["tipo"] != "pdf_dicionario":
            raise ValueError("Tipo de documento fora da allowlist")
        if doc["integridade_binaria_publicada_por_autoridade"] is not None:
            raise ValueError("Checksum oficial não verificado: não pode ser declarado")
        _official_url(doc["pagina_oficial"], PORTAL, "/")
        _official_url(doc["url_documento"], PORTAL, PDF_PREFIX)
        if not doc["url_documento"].endswith(".pdf"):
            raise ValueError("Documento oficial esperado deve ser PDF")
        data = entry["acesso_dados"]
        if not isinstance(data, dict) or set(data) != DATA_KEYS:
            raise ValueError("Metadados de arquivo anual incompletos")
        _official_url(data["pagina_oficial"], DATA_PORTAL, DATA_PATH)
        for key in (DATA_KEYS - {"pagina_oficial", "sistema_origem_no_ano_confirmado"}):
            if data[key] is not None:
                raise ValueError("Arquivo, checksum ou status anual ainda não verificado")
        if data["sistema_origem_no_ano_confirmado"] is not False:
            raise ValueError("Sistema de origem anual não pode ser atestado neste índice")
        flags = entry["validacoes"]
        if not isinstance(flags, dict) or set(flags) != VALIDATION_KEYS:
            raise ValueError("Flags de evidência documental inválidas")
        if flags["link_de_dicionario_oficial_localizado"] is not True:
            raise ValueError("Este registro exige link documental identificado")
        if any(flags[k] is not False
               for k in VALIDATION_KEYS - {"link_de_dicionario_oficial_localizado"}):
            raise ValueError(
                "Validação anual e autorização não podem ser promovidas por catálogo"
            )
    return payload


@lru_cache(maxsize=1)
def _index() -> tuple[dict, tuple[dict, ...]]:
    """Packaged, fixed source; no user-defined JSON path or HTTP fetch."""
    src = files("sinan_mcp").joinpath("registry", "official_documentary_evidence.json")
    text = src.read_text(encoding="utf-8")
    if len(text.encode("utf-8")) > 100_000:
        raise ValueError("Registro excede limite de tamanho")
    data = validate_registry(json.loads(text, object_pairs_hook=_pairs_strict))
    # Fingerprint of *reviewable metadata*, NOT of official source bytes.
    meta = {
        "catalog_revision": data["catalog_revision"],
        "verified_portal_links_on": data["verified_portal_links_on"],
        "catalog_metadata_sha256": hashlib.sha256(
            json.dumps(data, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }
    return meta, tuple(data["entries"])


def listar_evidencias_documentais() -> dict[str, Any]:
    meta, entries = _index()
    return {
        "schema_version": SCHEMA, **meta,
        "entradas": [
            {"agravo": x["agravo_alias_interno"],
             "ano_do_arquivo_pretendido": x["ano_do_arquivo_pretendido"],
             "edicao_documental": x["documento"]["edicao_documental"],
             "estado": "documento_oficial_localizado_ano_nao_verificado"}
            for x in entries
        ],
        "total_entradas_documentadas": len(entries),
        "quantidade_anos_de_arquivo_cientificamente_verificados": 0,
        "base_real_disponibilizada": False,
        "aviso": NOTICE,
    }


def consultar_evidencia_agravo_ano(agravo: str, ano: int) -> dict[str, Any]:
    """Exact single year, no guess or fallback to another dictionary edition."""
    if not isinstance(agravo, str) or not re.fullmatch(r"[A-Za-z]{4}", agravo):
        raise ValueError("Informe alias interno do agravo com quatro letras")
    if type(ano) is not int or not 1980 <= ano <= 2100:
        raise ValueError("Informe ano de arquivo inteiro entre 1980 e 2100")
    code = agravo.upper()
    meta, entries = _index()
    match = next(
        (x for x in entries if x["agravo_alias_interno"] == code
         and x["ano_do_arquivo_pretendido"] == ano), None
    )
    return {
        "schema_version": SCHEMA, **meta,
        "agravo_alias_interno": code, "ano_do_arquivo_pretendido": ano,
        "estado": (
            "documento_oficial_localizado_ano_nao_verificado" if match else
            "sem_documentacao_anual_curada"
        ),
        "indice_de_alias_contem_agravo": code in REFERENCE_CODES,
        "evidencia_documental": (
            {
                "titulo": match["documento"]["titulo"],
                "pagina_oficial": match["documento"]["pagina_oficial"],
                "documento_url": match["documento"]["url_documento"],
                "edicao_documental": match["documento"]["edicao_documental"],
                "sistema_descrito_no_documento": match["sistema_documentado"],
                "orientacao_dados": match["acesso_dados"]["pagina_oficial"],
                "limitacoes": match["limitacoes"],
            }
            if match else None
        ),
        "link_dicionario_oficial_localizado": match is not None,
        "arquivo_anual_independentemente_verificado": False,
        "codigo_download_anual_verificado": False,
        "compatibilidade_dicionario_ano_verificada": False,
        "sha256_oficial_do_arquivo_disponivel": False,
        "consolidacao_anual_confirmada": False,
        "indicador_cientifico_ano_validado": False,
        "acesso_publico_a_dados_reais": False,
        "autorizacao_de_publicacao": False,
        "consulta_de_dados_executada": False,
        "aviso": NOTICE,
    }
