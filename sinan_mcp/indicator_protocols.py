"""Registry of explicitly unvalidated epidemiologic method proposals.

A protocol is documentation, NOT a validated epidemiologic indicator.
No source I/O, no SQL, no disease outcomes are computed by this module.
"""
from __future__ import annotations

from .official_sources import CONDITIONS

KNOWN = frozenset(code for code, _, _ in CONDITIONS)
SCHEMA = "sinan-method-proposals-v1"

PROPOSALS = {
    "TUBE": {
        "TB_ABANDONO_EXPLORATORIO": {
            "rotulo": "Proporção exploratória por situação de encerramento",
            "classificacao": "EXPLORATORIO_NAO_OFICIAL",
            "ano_referencia": "ano_arquivo",
            "campos_necessarios": ["SITUA_ENCE"],
            "numerador_de_referencia": "SITUA_ENCE em {2,10}",
            "denominador_de_referencia": "SITUA_ENCE em {1,2,10}",
            "pendencias_cientificas": [
                "dicionario do ano/agravo validado",
                "elegibilidade e tipo de entrada",
                "definicao de coorte por diagnostico",
                "vinculacao e deduplicacao longitudinal",
                "reconciliacao com indicador oficial",
                "revisao de risco de divulgacao entre subgrupos",
            ],
        },
    },
    "DENG": {
        "DENG_REGISTROS_DESCRITIVOS": {
            "rotulo": "Contagem descritiva de registros importados",
            "classificacao": "CONTAGEM_DESCRITIVA_NAO_INCIDENCIA",
            "ano_referencia": "ano_arquivo",
            "campos_necessarios": ["identificacao_do_arquivo"],
            "numerador_de_referencia": "numero de registros no arquivo",
            "denominador_de_referencia": "nao se aplica a contagem de registros",
            "pendencias_cientificas": [
                "dicionario da versao do ano",
                "classificacao final e confirmacao de caso",
                "deduplicacao e tipo de sistema",
                "populacao sob risco se futuro objetivo for incidencia",
                "confronto com tabulacao oficial",
                "revisao de risco de divulgacao",
            ],
        },
    },
}


def plan_indicator(agravo: str, ano: int, protocolo: str | None = None) -> dict:
    """Fail closed on unsupported disease-year methods, no real calculations."""
    if not isinstance(agravo, str) or agravo not in KNOWN:
        raise ValueError("Use alias interno existente no catálogo de referência")
    if type(ano) is not int or not 1980 <= ano <= 2100:
        raise ValueError("Ano de arquivo inválido")
    options = PROPOSALS.get(agravo, {})
    if protocolo is not None:
        if not isinstance(protocolo, str) or protocolo not in options:
            raise ValueError("Protocolo não definido para este agravo")
        methods = {protocolo: options[protocolo]}
    else:
        methods = options
    return {
        "schema_version": SCHEMA,
        "agravo": agravo,
        "ano_do_arquivo": ano,
        "estado": "proposta_sem_validacao_para_ano" if methods else "sem_protocolo_especifico",
        "metodos": methods,
        "codigo_download_confirmado_para_ano": False,
        "dicionario_validado_para_ano": False,
        "definicao_de_coorte_validada": False,
        "indicadores_oficiais_disponiveis": False,
        "resultado_numerico": None,
        "consulta_de_dados_executada": False,
        "aviso": (
            "Metodologia exploratória; NÃO é certificado para o ano informado "
            "e não autoriza cálculos clínicos, divulgação, inferência individual, "
            "incidência ou comparação com metas oficiais."
        ),
    }
