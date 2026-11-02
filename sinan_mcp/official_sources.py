"""Verified-entrypoint registry for SINAN-notifiable diseases and events.

Contains only navigation metadata and illustrative internal four-letter aliases.
NO live retrieval, individual records, health measurements or epidemiologic
totals. A disease's presence here never establishes a verified dataset.
"""
from __future__ import annotations

import re
import unicodedata

SCHEMA_VERSION = "sinan-sources-v1"
NOTICE = (
    "Catálogo de referência para descoberta, NÃO inventário de bases carregadas. "
    "Nenhuma estatística real foi disponibilizada ou validada por este catálogo."
)

# Verified official landing pages (not links to specific validated table exports).
OFFICIAL_SOURCES = (
    {
        "id": "ms-sinan-agravos",
        "nome": "Ministério da Saúde — Dados sobre agravos de notificação",
        "url": "https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/svsa/agravos-de-notificacoes/agravos-de-notificacoes",
        "tipo": "guia_oficial_acesso_microdados_e_tabnet",
        "possui_valores_importados_neste_mcp": False,
    },
    {
        "id": "datasus-tabnet",
        "nome": "DATASUS — Informações de Saúde (TABNET)",
        "url": "https://datasus.saude.gov.br/informacoes-de-saude-tabnet/",
        "tipo": "indice_oficial_tabelas_agravos",
        "possui_valores_importados_neste_mcp": False,
    },
    {
        "id": "ms-sinan",
        "nome": "Ministério da Saúde — Sistema de Informações de Agravos de Notificação",
        "url": "https://www.gov.br/saude/pt-br/composicao/svsa/sistemas-de-informacao/sinan/sinan",
        "tipo": "documentacao_oficial",
        "possui_valores_importados_neste_mcp": False,
    },
    {
        "id": "sinan-portal",
        "nome": "Portal SINAN — fichas e dicionários",
        "url": "https://portalsinan.saude.gov.br/",
        "tipo": "indice_documentacao_agravos",
        "possui_valores_importados_neste_mcp": False,
    },
)

# Internal aliases derived from the current codebase; NOT asserted to be
# canonical download codes in DATASUS, PySUS or all annual dictionaries.
# Pilot import coverage is different from availability of approved statistics.
CONDITIONS = (
    ("TUBE", "Tuberculose", "piloto_em_validacao"),
    ("DENG", "Dengue", "piloto_em_validacao"),
    ("CHIK", "Chikungunya", "referencia_sem_validacao_especifica"),
    ("ZIKA", "Zika", "referencia_sem_validacao_especifica"),
    ("HANS", "Hanseníase", "referencia_sem_validacao_especifica"),
    ("SIFA", "Sífilis adquirida", "referencia_sem_validacao_especifica"),
    ("SIFC", "Sífilis congênita", "referencia_sem_validacao_especifica"),
    ("HEPA", "Hepatites virais", "referencia_sem_validacao_especifica"),
    ("MENI", "Meningite", "referencia_sem_validacao_especifica"),
    ("VIOL", "Violência interpessoal/autoprovocada", "referencia_sem_validacao_especifica"),
    ("LEIV", "Leishmaniose visceral", "referencia_sem_validacao_especifica"),
    ("LTAN", "Leishmaniose tegumentar", "referencia_sem_validacao_especifica"),
    ("ANIM", "Acidentes por animais peçonhentos", "referencia_sem_validacao_especifica"),
    ("COQU", "Coqueluche", "referencia_sem_validacao_especifica"),
)


def _normalize(s: str) -> str:
    lowered = unicodedata.normalize("NFKD", s.casefold())
    return "".join(ch for ch in lowered if not unicodedata.combining(ch))


def _condition_record(alias: str, name: str, stage: str) -> dict:
    return {
        "codigo_interno": alias,
        "nome": name,
        "estado_de_implementacao": stage,
        "dados_reais_disponiveis_no_mcp_publico": False,
        "indicadores_reais_validados_no_mcp_publico": False,
        "codigo_oficial_de_download_confirmado": False,
        "fonte_referencia_id": "ms-sinan-agravos",
    }


def listar_fontes_oficiais() -> dict:
    """Describe navigational references; does NOT fetch or proxy data."""
    return {
        "schema_version": SCHEMA_VERSION,
        "fontes": [dict(x) for x in OFFICIAL_SOURCES],
        "natureza": "somente_metadados_de_navegacao",
        "aviso": NOTICE,
    }


def pesquisar_agravos(termo: str = "", limite: int = 20) -> dict:
    """Search the *curated example index* only, never a full mandatory list."""
    if not isinstance(termo, str) or len(termo) > 80 or "\x00" in termo:
        raise ValueError("Termo inválido; máximo de 80 caracteres")
    if type(limite) is not int or not 1 <= limite <= 20:
        raise ValueError("Limite deve estar entre 1 e 20")
    cleaned = _normalize(termo.strip())
    if not cleaned:
        matches = CONDITIONS
    else:
        matches = tuple(
            cond for cond in CONDITIONS
            if cleaned in _normalize(cond[0]) or cleaned in _normalize(cond[1])
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "termo": termo.strip(),
        "resultados": [_condition_record(*c) for c in matches[:limite]],
        "total_no_indice_curado": len(matches),
        "indice_exemplificativo_nao_exaustivo": True,
        "codigo_de_agravo": "alias_interno_nao_codificacao_oficial",
        "aviso": NOTICE,
    }


def descrever_agravo(codigo_interno: str) -> dict:
    """Distinguish indexed, ingested, reviewed and published states."""
    if not isinstance(codigo_interno, str) or not re.fullmatch(r"[A-Za-z]{4}", codigo_interno):
        raise ValueError("Use um alias interno de quatro letras (ex.: TUBE, DENG)")
    key = codigo_interno.upper()
    for code, name, stage in CONDITIONS:
        if code == key:
            return {
                "schema_version": SCHEMA_VERSION,
                "agravo": _condition_record(code, name, stage),
                "fonte_de_consulta": dict(OFFICIAL_SOURCES[0]),
                "tabulacao_oficial": dict(OFFICIAL_SOURCES[1]),
                "proxima_etapa": (
                    "Confirmar código real de download, ano, dicionário e fonte; "
                    "validar versão, agregados e política de publicação."
                ),
                "aviso": NOTICE,
            }
    raise ValueError(
        "Agravo não consta do índice exemplificativo. Isso NÃO indica "
        "ausência de notificação no SINAN; consulte as fontes oficiais."
    )
