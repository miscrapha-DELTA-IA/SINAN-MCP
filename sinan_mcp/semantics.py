"""Read-only epidemiological semantics for research *planning*, never inference.

Controlled vocabularies distinguish source records, people, cases and rates;
no clinical datasets, SQL, denominator lookups, code execution or network.
Every request fails closed if its disease, reference year, axes or denominator
have not been independently validated for the intended study.
"""
from __future__ import annotations

from typing import Any

from .official_sources import CONDITIONS

SCHEMA_VERSION = "sinan-epidemiological-semantics-v1"
UNITS = frozenset({
    "registro_de_notificacao", "caso_confirmado", "episodio",
    "individuo", "obito", "internacao", "agregado_territorial",
})
TIME_AXES = frozenset({
    "ano_do_arquivo", "ano_notificacao", "ano_diagnostico",
    "ano_encerramento", "ano_primeiros_sintomas",
})
MEASURES = frozenset({"contagem_registros", "proporcao", "incidencia",
                      "prevalencia", "letalidade"})
DENOMINATORS = frozenset({
    "populacao_residente", "pessoas_em_risco", "registros_elegiveis",
    "casos_confirmados", "episodios_elegiveis",
})
DENOMINATOR_REFERENCES = frozenset({
    "ibge_a_verificar", "coorte_local_a_validar",
    "fonte_oficial_a_verificar",
})
CODES = frozenset(code for code, _, _ in CONDITIONS)
NOTICE = (
    "Estrutura de PLANEJAMENTO. Não estabelece disponibilidade de bases, "
    "validade de dicionário, casos únicos, coorte, denominador, incidência "
    "nem permissão de publicação. Não houve consulta de dados reais."
)


def _enum(value: object, options: frozenset[str], name: str) -> str:
    if not isinstance(value, str) or value not in options:
        raise ValueError(f"{name} fora do vocabulário controlado")
    return value


def vocabulario_semantico() -> dict[str, Any]:
    """Expose controlled terms for research design, not actual indicator values."""
    return {
        "schema_version": SCHEMA_VERSION,
        "unidades_observacionais": sorted(UNITS),
        "eixos_temporais": sorted(TIME_AXES),
        "tipos_medida": sorted(MEASURES),
        "denominadores_declaraveis_nao_validados": sorted(DENOMINATORS),
        "referencias_de_denominador_pendentes": sorted(DENOMINATOR_REFERENCES),
        "indicadores_reais_validados": [],
        "consulta_executada": False,
        "aviso": NOTICE,
    }


def planejar_medida_epidemiologica(
    agravo: str, ano_do_arquivo: int, unidade_observacional: str,
    eixo_temporal: str, tipo_medida: str, denominador: str | None = None,
    fonte_denominador: str | None = None,
) -> dict[str, Any]:
    """Plan a controlled measurement request; never produce a statistic.

    Semantics are intentionally conservative: an unverified disease/year
    always needs human scientific review, even if all enum values are valid.
    A rate or proportion with no denominator is refused structurally.
    """
    if not isinstance(agravo, str) or len(agravo) > 4:
        raise ValueError("Use um alias interno de agravo de quatro letras")
    code = agravo.strip().upper()
    if code not in CODES:
        state = "fora_do_indice_curado"
    else:
        state = "sem_fonte_e_metodo_validados_para_ano"
    if type(ano_do_arquivo) is not int or not 1980 <= ano_do_arquivo <= 2100:
        raise ValueError("Ano do arquivo fora do intervalo")
    unit = _enum(unidade_observacional, UNITS, "unidade_observacional")
    time_axis = _enum(eixo_temporal, TIME_AXES, "eixo_temporal")
    measure = _enum(tipo_medida, MEASURES, "tipo_medida")
    if denominador is not None:
        _enum(denominador, DENOMINATORS, "denominador")
    if fonte_denominador is not None:
        _enum(fonte_denominador, DENOMINATOR_REFERENCES, "fonte_denominador")
    required = measure != "contagem_registros"
    if not required and (denominador is not None or fonte_denominador is not None):
        state = "recusado_denominador_indevido_para_contagem"
    elif required and (denominador is None or fonte_denominador is None):
        state = "recusado_sem_denominador_e_fonte"
    elif measure == "contagem_registros" and unit != "registro_de_notificacao":
        state = "recusado_contagem_nao_e_registro_de_notificacao"
    elif measure == "incidencia" and (
        unit != "caso_confirmado" or denominador != "pessoas_em_risco"
    ):
        state = "recusado_incidencia_sem_caso_e_populacao_em_risco"
    elif measure == "prevalencia" and (
        unit != "individuo" or denominador != "populacao_residente"
    ):
        state = "recusado_prevalencia_sem_pessoas_e_populacao"
    elif measure == "letalidade" and (
        unit != "obito" or denominador != "casos_confirmados"
    ):
        state = "recusado_letalidade_sem_obitos_e_casos"
    return {
        "schema_version": SCHEMA_VERSION,
        "agravo_alias_interno": code,
        "ano_do_arquivo_pretendido": ano_do_arquivo,
        "unidade_observacional": unit,
        "eixo_temporal_pretendido": time_axis,
        "tipo_de_medida": measure,
        "denominador": denominador if required else "nao_se_aplica",
        "fonte_denominador_pendente": fonte_denominador,
        "estado": state,
        "aceito_para_calculo_real": False,
        "valor": None,
        "consulta_executada": False,
        "requisitos_pendentes": [
            "Confirmar código de download, arquivo exato, ano e sistema de origem",
            "Verificar dicionário do agravo/ano e definição da unidade observacional",
            "Definir coorte, caso e critérios de inclusão sem confundir registros com indivíduos",
            "Comprovar fonte, território e período do denominador quando aplicável",
            "Revisar indicador cientificamente e autorização de acesso/divulgação",
        ],
        "aviso": NOTICE,
    }


def semantica_demo(*, proporcao: bool) -> dict[str, Any]:
    """Annotations for the wholly fictional in-code TUBE fixture only."""
    return {
        "schema_version": SCHEMA_VERSION,
        "unidade_observacional": "registro_ficticio_nao_caso",
        "eixo_temporal": "ano_do_arquivo_ficticio",
        "tipo_de_medida": ("proporcao_de_registros_ficticios"
                          if proporcao else "contagem_de_registros_ficticios"),
        "numerador": ("registros_ficticios_com_desfecho_2"
                      if proporcao else "registros_ficticios_por_categoria"),
        "denominador": ("total_registros_ficticios_da_categoria"
                        if proporcao else "nao_se_aplica"),
        "nao_e_incidencia": True,
        "nao_e_estimativa_de_risco": True,
        "avaliacao_epidemiologica_real": False,
    }
