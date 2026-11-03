"""Offline administrative map of generic SINAN notification documentation.

A shared notification dictionary is not a disease-specific dictionary,
a validated 2024 layout, proof of an annual release, or an authorization.
This module never downloads records, runs network requests, or reads DBs.
"""
from __future__ import annotations

from typing import Any

from .official_sources import CONDITIONS

SCHEMA = "sinan-shared-notification-documentation-v1"
PORTAL = "https://portalsinan.saude.gov.br"
SHARED_PDF = (
    PORTAL
    + "/images/documentos/Agravos/NINDIV/DIC_DADOS_NET_Not_Individual_rev.pdf"
)
EDITION = "SINAN NET 5.0 — dicionário de Notificação Individual, novembro/2018"
# Deliberately scoped to research planning for the 2024 file year.
# ZIKA links to the shared dictionary on its official disease page.
# SIFA is only a CANDIDATE: the generic notification page does not
# establish a direct link between the SIFA 2024 file and this PDF.
CANDIDATES = {
    "ZIKA": (PORTAL + "/zika", "link_direto_na_pagina_zika"),
    "SIFA": (PORTAL + "/notificacoes", "candidato_generico_sem_vinculo_anual"),
}
ALIASES = frozenset(code for code, _, _ in CONDITIONS)


def diagnosticar_documentacao_transversal(
    ano: int, agravo: str | None = None,
) -> dict[str, Any]:
    """Return historical documentary candidates, never epidemiological approval."""
    if type(ano) is not int or not 1980 <= ano <= 2100:
        raise ValueError("Ano de arquivo inválido")
    if agravo is None:
        selected = ("ZIKA", "SIFA")
    elif type(agravo) is not str or agravo not in ALIASES:
        raise ValueError("Informe alias interno do agravo em maiúsculas")
    else:
        selected = (agravo,)

    rows = []
    for code in selected:
        candidate = CANDIDATES.get(code) if ano == 2024 else None
        direct = candidate is not None and code == "ZIKA"
        rows.append({
            "agravo": code,
            "ano_do_arquivo_pretendido": ano,
            "referencia_transversal_candidata": candidate is not None,
            "vinculo_direto_na_pagina_do_agravo": direct,
            "tipo_vinculo": candidate[1] if candidate else "sem_referencia_curada",
            "pagina_oficial": candidate[0] if candidate else None,
            "url_dicionario_compartilhado": SHARED_PDF if candidate else None,
            "edicao_documental": EDITION if candidate else None,
            "dicionario_especifico_neste_registro": False,
            "compatibilidade_com_arquivo_anual_demonstrada": False,
            "sistema_origem_2024_verificado": False,
            "indicador_real_homologado": False,
            "acesso_clinico_executado": False,
            "publicacao_autorizada": False,
        })
    return {
        "schema_version": SCHEMA,
        "ano_do_arquivo_pretendido": ano,
        "agravos_consultados": len(rows),
        "referencias_transversais_candidatas": sum(
            x["referencia_transversal_candidata"] for x in rows
        ),
        "vinculos_diretos_na_pagina_do_agravo": sum(
            x["vinculo_direto_na_pagina_do_agravo"] for x in rows
        ),
        "registros": rows,
        "dados_clinicos_consultados": False,
        "autorizacao_de_publicacao": False,
        "status": "REFERENCIA_DOCUMENTAL_TRANSVERSAL_SEM_VALIDACAO_ANUAL",
        "aviso": (
            "Dicionário geral de Notificação Individual SINAN NET 5.0 (2018). "
            "O vínculo direto existe na página de Zika; para sífilis adquirida "
            "é apenas hipótese documental genérica. Nenhum dos dois prova "
            "layout, arquivo, sistema, coorte ou indicador de 2024."
        ),
    }
