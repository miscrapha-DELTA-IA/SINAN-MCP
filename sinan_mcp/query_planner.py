"""Read-only multi-agravo research planning; no numeric data or network access.

A reference catalogue is NOT a registry of imported SINAN databases. This
module only helps MCP clients distinguish navigation, demo, local research and
independently approved publication. It never imports clinical data.
"""
from __future__ import annotations

import unicodedata
from typing import Any

from .official_sources import CONDITIONS, OFFICIAL_SOURCES
from .year_evidence_registry import consultar_evidencia_agravo_ano
from .official_annual_resources import consultar_recursos_oficiais_ano

SCHEMA = "sinan-research-plan-v1"
UF = frozenset(
    "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS "
    "RO RR SC SP SE TO BR".split()
)
GROUPS = frozenset({"sexo", "raca_cor"})
NOTICE = (
    "Planejamento informativo: nenhuma consulta real, download, ingestão, "
    "acesso individual ou publicação foi executada. Referência de agravo "
    "não comprova disponibilidade de dados, qualidade ou indicador validado."
)


def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.casefold())
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


def _check_query(agravo: str) -> str:
    if (not isinstance(agravo, str) or not 1 <= len(agravo.strip()) <= 80
            or any(ord(c) < 32 or ord(c) == 127 for c in agravo)):
        raise ValueError("Informe nome ou alias de agravo (1 a 80 caracteres).")
    return agravo.strip()


def _record(item: tuple[str, str, str]) -> dict[str, Any]:
    code, name, state = item
    return {
        "codigo_interno": code,
        "nome": name,
        "estado_referencia": state,
        "consulta_real_disponivel_no_mcp_publico": False,
        "indicador_real_validado": False,
        "codigo_download_oficial_verificado": False,
        "demo_sintetica": code == "TUBE",
    }


def matriz_capacidades() -> dict[str, Any]:
    """List known reference entries, never real-data availability."""
    return {
        "schema_version": SCHEMA,
        "agravos_referenciados": [_record(x) for x in CONDITIONS],
        "quantidade_referencias": len(CONDITIONS),
        "escopo": "indice_curado_exemplificativo_nao_exaustivo",
        "operacoes_servidor_publico": [
            "referencias_oficiais", "pesquisa_catalogo",
            "planejamento_de_consulta", "demonstracao_sintetica_TUBE"
        ],
        "operacoes_reais_neste_servidor": [],
        "publicacao_de_agregados_reais_automatica": False,
        "aviso": NOTICE,
    }


def planejar_consulta_agravo(
    agravo: str, ano: int | None = None, uf: str | None = None,
    por: str = "sexo"
) -> dict[str, Any]:
    """Plan where and how an agravo might be researched; never fetch records.

    Unknown/ambiguous names are returned as explicit states, not fabricated
    availability. Inputs cannot select arbitrary SQL, municipality or outcomes.
    """
    term = _check_query(agravo)
    if ano is not None and (type(ano) is not int or not 2000 <= ano <= 2100):
        raise ValueError("Ano deve ser inteiro entre 2000 e 2100.")
    if uf is not None:
        if not isinstance(uf, str) or uf.strip().upper() not in UF:
            raise ValueError("UF inválida; use sigla brasileira ou BR.")
        uf = uf.strip().upper()
    if not isinstance(por, str) or por not in GROUPS:
        raise ValueError("Apenas sexo ou raca_cor; nenhum cruzamento é planejado.")

    normalized = _normalize(term)
    exact = [
        x for x in CONDITIONS
        if _normalize(x[0]) == normalized or _normalize(x[1]) == normalized
    ]
    matches = exact or [
        x for x in CONDITIONS
        if normalized in _normalize(x[0]) or normalized in _normalize(x[1])
    ]
    if not matches:
        status = "fora_do_indice_exemplificativo"
    elif len(matches) > 1:
        status = "ambiguo_escolha_agravo"
    else:
        status = "referencia_identificada_sem_dados_reais"

    return {
        "schema_version": SCHEMA,
        "entrada": {"agravo": term, "ano": ano, "uf": uf, "dimensao": por},
        "estado": status,
        "correspondencias": [_record(x) for x in matches],
        "evidencia_documental_agravo_ano": (
            consultar_evidencia_agravo_ano(matches[0][0], ano)
            if ano is not None and len(matches) == 1 else None
        ),
        "recursos_de_distribuicao_ano": (
            consultar_recursos_oficiais_ano(matches[0][0], ano)
            if ano is not None and len(matches) == 1 else None
        ),
        "consulta_executada": False,
        "dados_reais_disponiveis_no_servidor_publico": False,
        "resultado_epidemiologico": None,
        "proximas_etapas": [
            "Confirmar a ficha, definicao de caso, codigo de arquivo e dicionario "
            "do agravo/ano em fontes oficiais.",
            "Verificar disponibilidade e status preliminar/final do arquivo; "
            "nao interpretar ano de arquivo como ano de diagnostico.",
            "Se autorizado, importar e auditar registros exclusivamente em ambiente "
            "local protegido; a instancia publica nao permite importacao.",
            "Confrontar agregados com tabulacoes oficiais e executar revisao "
            "epidemiologica, de privacidade e de diferenca entre publicacoes.",
            "Somente uma aprovacao independente permite avaliar publicacao "
            "em servidor SEPARADO; nenhuma aprovacao ocorre automaticamente.",
        ],
        "fontes_oficiais_para_verificacao": [
            {"nome": x["nome"], "url": x["url"]} for x in OFFICIAL_SOURCES
        ],
        "aviso": NOTICE,
    }
