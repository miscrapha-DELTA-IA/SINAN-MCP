"""Offline, strict candidate transcription of the 37 numbered Zika PDF fields.

These are DOCUMENTARY facts from an eight-page public Ministry PDF,
not a verified schema for ZIKABR24, no sampled clinical data, no
epidemiological approval. Code/domain mappings are deliberately partial
and must not drive patient-level algorithms.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
from importlib.resources import files
import json
import re

from .zika_official_dictionary_reference import PDF_URL, RESOURCE_ID, RESOURCE_URL

SCHEMA = "sinan-zika-pdf-37-fields-documentary-candidate-v1"
FILE_NAME = "zika_pdf_37_fields_candidate.json"
EXPECTED_FIELD_IDS = (
    "tp_not", "id_agravo", "dt_notific", "sem_not", "nu_ano",
    "sg_uf_not", "id_municip", "id_regiona", "id_unidade", "dt_sin_pri",
    "sem_pri", "ano_nasc", "nu_idade_n", "cs_sexo", "cs_gestant",
    "cs_raca", "cs_escol_n", "sg_uf", "id_mn_resi", "id_rg_resi",
    "id_pais", "nduplic_n", "in_vincula", "dt_invest", "id_ocupa_n",
    "classi_fin", "criterio", "tpautocto", "coufinf", "copaisinf",
    "comuninf", "doenca_tra", "evolucao", "dt_obito", "dt_encerra",
    "dt_digita", "tp_sistema",
)
# Every type is from the visible Tipo column. Note 'num(4)' for age
# and 'char(6)' for linkage despite its 0/1 documented categories.
EXPECTED_TYPES = (
    "char(1)", "char(5)", "date(8)", "char(6)", "char(4)",
    "char(2)", "char(6)", "char(8)", "char(7)", "date(8)",
    "char(6)", "char(4)", "num(4)", "char(1)", "char(1)",
    "char(1)", "char(2)", "char(2)", "char(6)", "char(8)",
    "char(4)", "char(1)", "char(6)", "date(8)", "char(6)",
    "char(2)", "char(2)", "char(1)", "char(2)", "char(4)",
    "char(6)", "char(1)", "char(1)", "date(8)", "date(8)",
    "date(8)", "char(1)",
)
EXPECTED_PAGES = (
    (1,) * 5 + (2,) * 7 + (3,) * 3 + (4,) * 3
    + (5,) * 7 + (6,) * 4 + (7,) * 3 + (8,) * 5
)
DOMAINS = frozenset({
    "categorias_listadas", "tabela_agravos_cid10", "data_dd_mm_aaaa",
    "semana_epidemiologica_aaaass", "ano_aaaa", "tabela_ibge",
    "tabela_regional_sistema", "tabela_cnes",
    "idade_codificada_unidade_primeiro_digito",
    "codigos_heterogeneos_revisao", "tabela_paises",
    "codigos_ambiguidade_pagina", "tabela_ocupacoes",
})
GROUPS = frozenset({
    "notificacao", "pessoa", "residencia", "controle_notificacoes",
    "investigacao", "desfecho_investigacao", "autoctonia",
    "encerramento", "sistema_origem",
})
EXPECTED_KNOWN_CODES = {
    "tp_not": ("1", "2", "3", "4"),
    "nu_idade_n": ("1", "2", "3", "4"),
    "cs_sexo": ("M", "F", "I"),
    "cs_gestant": ("0", "1", "2", "3", "4", "5", "6", "9"),
    "cs_raca": ("1", "2", "3", "4", "5", "9"),
    "in_vincula": ("0", "1"),
    "classi_fin": ("1", "2", "9"),
    "criterio": ("1", "2", "3"),
    "tpautocto": ("1", "2", "3"),
    "doenca_tra": ("1", "2", "9"),
    "evolucao": ("0", "1", "2", "3", "9"),
    "tp_sistema": ("1", "2"),
}
REQUIRED_FIELDS = frozenset({
    "seq", "campo", "tipo_documental", "pagina_pdf", "grupo_proposto",
    "significado_resumido", "dominio_descritor", "codigos_citados",
    "validado_no_arquivo_2024",
})
REQUIRED_TOP = frozenset({
    "schema_version", "source_title", "source_resource_id",
    "source_package_id", "source_page", "source_pdf", "source_pages",
    "fields_numbered_in_pdf", "field_count_transcribed_from_visible_pdf",
    "transcription_status", "domain_status", "source_bytes_official_sha256_verified",
    "documentary_second_reviewer_authenticated", "year_2024_schema_compared",
    "year_2024_data_accessed", "year_2024_cutoff_confirmed",
    "indicators_approved", "publication_authorized",
    "transcription_issues", "fields",
})


def _pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Chave duplicada no catalogo documental")
        result[key] = value
    return result


def validar_transcricao_zika_documental(doc: object) -> dict:
    """Fail closed: not a schema, dictionary-domain or release approval."""
    if not isinstance(doc, dict) or set(doc) != REQUIRED_TOP:
        raise ValueError("Catalogo Zika com estrutura inesperada")
    required_identity = {
        "schema_version": SCHEMA,
        "source_resource_id": RESOURCE_ID,
        "source_page": RESOURCE_URL,
        "source_pdf": PDF_URL,
        "source_package_id": "4557ba96-7d52-4a56-bd6f-f99a5af09f77",
        "source_pages": 8,
        "fields_numbered_in_pdf": 37,
        "field_count_transcribed_from_visible_pdf": 37,
        "transcription_status": "transcricao_documental_candidata_sem_revisao_independente",
        "domain_status": "dominios_documentais_parcialmente_resumidos_nao_homologados",
        "indicators_approved": 0,
    }
    for key, val in required_identity.items():
        if doc[key] != val or type(doc[key]) is not type(val):
            raise ValueError("Identidade, estado ou contagem documental divergente")
    for name in (
        "source_bytes_official_sha256_verified",
        "documentary_second_reviewer_authenticated",
        "year_2024_schema_compared", "year_2024_data_accessed",
        "year_2024_cutoff_confirmed", "publication_authorized",
    ):
        if doc[name] is not False:
            raise ValueError("Transcricao nao pode conceder validacao ou acesso")
    if (not isinstance(doc["source_title"], str)
            or doc["source_title"] != "Sinan Net — Dicionário de Dados — ZIKA"):
        raise ValueError("Titulo documental nao reconhecido")
    items = doc["fields"]
    if not isinstance(items, list) or len(items) != 37:
        raise ValueError("Transcricao deve ter exatamente 37 campos")
    for index, row in enumerate(items):
        if not isinstance(row, dict) or set(row) != REQUIRED_FIELDS:
            raise ValueError("Campo documental com formato invalido")
        if (type(row["seq"]) is not int or row["seq"] != index + 1
                or row["campo"] != EXPECTED_FIELD_IDS[index]
                or row["tipo_documental"] != EXPECTED_TYPES[index]
                or type(row["pagina_pdf"]) is not int
                or row["pagina_pdf"] != EXPECTED_PAGES[index]):
            raise ValueError("Campo, tipo ou pagina nao conferem com PDF revisado")
        if (row["grupo_proposto"] not in GROUPS
                or row["dominio_descritor"] not in DOMAINS
                or not isinstance(row["significado_resumido"], str)
                or not 3 <= len(row["significado_resumido"]) <= 110
                or any(ord(c) < 32 for c in row["significado_resumido"])
                or row["validado_no_arquivo_2024"] is not False):
            raise ValueError("Descricao nao curada ou validacao indevida")
        codes = row["codigos_citados"]
        if (not isinstance(codes, list)
                or tuple(codes) != EXPECTED_KNOWN_CODES.get(row["campo"], ())
                or any(type(code) is not str for code in codes)):
            raise ValueError("Dominio de categorias nao corresponde ao PDF curado")
        if row["campo"] == "nduplic_n" and (
                row["dominio_descritor"] != "codigos_ambiguidade_pagina"
                or codes):
            raise ValueError("Nunca inferir automaticamente codigos de duplicidade")
        if row["campo"] == "nu_idade_n" and (
                row["dominio_descritor"] != "idade_codificada_unidade_primeiro_digito"):
            raise ValueError("Idade nao pode ser interpretada como anos")
    issues = doc["transcription_issues"]
    if (not isinstance(issues, list) or len(issues) < 6
            or len(issues) > 20
            or "nduplic_n" not in [x.get("campo") for x in issues if isinstance(x, dict)]
            or "nu_idade_n" not in [x.get("campo") for x in issues if isinstance(x, dict)]):
        raise ValueError("Ressalvas obrigatorias ausentes")
    for issue in issues:
        if (not isinstance(issue, dict) or set(issue) != {"campo", "motivo"}
                or issue["campo"] not in EXPECTED_FIELD_IDS
                or not isinstance(issue["motivo"], str)
                or not 15 <= len(issue["motivo"]) <= 300):
            raise ValueError("Ressalva documental malformada")
    return doc


def carregar_transcricao_zika_pdf() -> dict:
    """Read a *packaged* public-document JSON only, with no network/DB."""
    source = files("sinan_mcp").joinpath("registry", FILE_NAME)
    raw = source.read_bytes()
    if not 1000 <= len(raw) <= 65000:
        raise ValueError("Tamanho inesperado da transcricao documental")
    candidate = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs_no_duplicates)
    doc = validar_transcricao_zika_documental(candidate)
    # This fingerprint is local version-control identity, NOT SHA of MS PDF.
    fingerprint = hashlib.sha256(raw).hexdigest()
    summary = {
        "schema_version": "sinan-zika-pdf-37-fields-documentary-report-v1",
        "agravo": "ZIKA",
        "documentary_fields_transcribed": len(doc["fields"]),
        "source_pdf_page_count": doc["source_pages"],
        "source_pdf": doc["source_pdf"],
        "source_resource_page": doc["source_page"],
        "documentary_page_counts": {
            str(k): v for k, v in sorted(
                Counter(x["pagina_pdf"] for x in doc["fields"]).items()
            )
        },
        "local_catalog_sha256_not_official_pdf_hash": fingerprint,
        "issues_requiring_independent_review": deepcopy(doc["transcription_issues"]),
        "documentary_field_rows": deepcopy(doc["fields"]),
        "fields_in_actual_2024_file_read": 0,
        "documentary_second_reviewer_authenticated": False,
        "annual_schema_2024_validated": False,
        "case_definitions_validated": False,
        "duplication_rules_approved": False,
        "official_pdf_sha256_verified": False,
        "indicators_approved": 0,
        "publication_authorized": False,
        "status": "TRANSCRICAO_PDF_COMPLETA_CANDIDATA_NAO_HOMOLOGADA",
    }
    return summary
