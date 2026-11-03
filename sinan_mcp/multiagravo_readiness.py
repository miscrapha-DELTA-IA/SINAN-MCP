"""Safe, OFFLINE, multi-disease roadmap coverage snapshot for one file-year.

References and proposed methods != usable patient data or valid indicators.
This reads only version-controlled, public metadata registries; never reads
SQLite, ZIP, CSV, private checklists or network resources. No approval API.
"""
from __future__ import annotations

from typing import Any

from .official_sources import CONDITIONS
from .official_annual_resources import (
    consultar_recursos_oficiais_ano,
    listar_recursos_oficiais_anuais,
)
from .year_evidence_registry import consultar_evidencia_agravo_ano
from .indicator_protocols import plan_indicator

SCHEMA = "sinan-multiagravo-year-coverage-diagnostic-v1"
NOTICE = (
    "CATALOGO DOCUMENTAL, NAO INVENTARIO CLINICO. Recurso oficial identificado "
    "ou dicionario localizado NAO prova download, compatibilidade, "
    "integridade de dados, consolidacao, indicador validado, licenca de "
    "tratamento ou aprovacao para publicacao."
)
ALIASES = {code: (name, stage) for code, name, stage in CONDITIONS}
BLOCKED = frozenset({
    "arquivo_anual_autenticado",
    "dicionario_aplicavel_ao_ano_validado",
    "coorte_ano_validada",
    "indicador_real_homologado",
    "dados_reais_disponiveis_no_mcp_publico",
    "publicacao_autorizada",
})


def diagnosticar_cobertura_multiagravo(
    ano: int, agravo: str | None = None,
) -> dict[str, Any]:
    """Cross-reference exact disease-year metadata, never infer approval."""
    if type(ano) is not int or not 1980 <= ano <= 2100:
        raise ValueError("Ano de arquivo invalido")
    if agravo is None:
        selected = list(ALIASES)
    else:
        if not isinstance(agravo, str) or agravo != agravo.strip().upper():
            raise ValueError("Use alias interno de quatro letras em maiusculas")
        if agravo not in ALIASES:
            raise ValueError("Agravo nao consta no catalogo de referencia")
        selected = [agravo]
    distributions = listar_recursos_oficiais_anuais()
    records = []
    for code in selected:
        name, stage = ALIASES[code]
        doc = consultar_evidencia_agravo_ano(code, ano)
        sources = consultar_recursos_oficiais_ano(code, ano)
        indicator = plan_indicator(code, ano)
        n = sources["quantidade_recursos_catalogados"]
        if not isinstance(n, int) or n < 0 or n != len(sources["recursos"]):
            raise ValueError("Catalogo anual inconsistente")
        if any((
            sources["analise_epidemiologica_autorizada"],
            sources["publicacao_autorizada"],
            doc["autorizacao_de_publicacao"],
            indicator["indicadores_oficiais_disponiveis"],
        )):
            raise ValueError("Indice documental contem autorizacao nao validada")
        row = {
            "agravo": code,
            "nome_referencia": name,
            "estado_referencia": stage,
            "ano_do_arquivo": ano,
            "documento_oficial_localizado": doc[
                "link_dicionario_oficial_localizado"
            ],
            "distribuicoes_anuais_catalogadas": n,
            "formatos_catalogados": sorted(
                set(x["formato"] for x in sources["recursos"])
            ),
            "propostas_metodologicas_nao_validadas": len(indicator["metodos"]),
            "arquivo_anual_autenticado": False,
            "dicionario_aplicavel_ao_ano_validado": False,
            "coorte_ano_validada": False,
            "indicador_real_homologado": False,
            "dados_reais_disponiveis_no_mcp_publico": False,
            "publicacao_autorizada": False,
        }
        if any(row[key] is not False for key in BLOCKED):
            raise ValueError("Flag de autorizacao indevida no diagnostico")
        records.append(row)
    return {
        "schema_version": SCHEMA,
        "ano_do_arquivo": ano,
        "filtro_agravo": agravo,
        "agravos_referenciados": len(records),
        "agravos_com_documentacao_localizada": sum(
            x["documento_oficial_localizado"] for x in records
        ),
        "distribuicoes_catalogadas": sum(
            x["distribuicoes_anuais_catalogadas"] for x in records
        ),
        "sha256_catalogo_distribuicoes": distributions["catalog_metadata_sha256"],
        "registros": records,
        "dados_clinicos_consultados": False,
        "publicacao_automatica": False,
        "status": "DIAGNOSTICO_DOCUMENTAL_SEM_VALIDACAO_EPIDEMIOLOGICA",
        "aviso": NOTICE,
    }
