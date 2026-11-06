"""Curated scope: supported ingest/export != epidemiologically validated indicator."""
from __future__ import annotations
from .official_sources import listar_fontes_oficiais as _official_sources, pesquisar_agravos as _reference_conditions

CATALOGUE = {
    "TUBE": {
        "nome": "Tuberculose", "name_en": "Tuberculosis", "suporte": "piloto",
        "operacoes": ["agregacoes_demograficas", "abandono_exploratorio"],
        "metodologia_indicador": "exploratorio_nao_oficial",
        "referencia_dicionario": "https://portalsinan.saude.gov.br/tuberculose",
    },
    "DENG": {
        "nome": "Dengue", "name_en": "Dengue", "suporte": "piloto",
        "operacoes": ["agregacoes_demograficas"],
        "metodologia_indicador": "nenhum_indicador_clinico_validado",
        "referencia_dicionario": "https://pysus.readthedocs.io/en/latest/guides/columns.html",
    },
}


def listar_agravos() -> dict:
    return {"schema_version": "0.3", "agravos_piloto": CATALOGUE, "indice_de_referencia": _reference_conditions(), "fontes_navegacao": _official_sources(),
            "aviso": "Lista de módulos testados com dados sintéticos; não implica validação para todos os anos e layouts de SINAN.",
            "outros_agravos": "Podem ser importados experimentalmente pela CLI, mas não têm modelo científico curado."}


def metodologia_tuberculose() -> dict:
    return {"codigo": "TB_ABANDONO_EXPLORATORIO",
            "situacao": "RASCUNHO_METODOLOGICO_BLOQUEADO",
            "validado_cientificamente": False,
            "utilizavel_em_dados_reais": False,
            "numerador": "NÃO DEFINIDO: códigos SITUA_ENCE 2/10 exigem coorte e regras oficiais",
            "denominador": "NÃO DEFINIDO: não usar somente códigos 1/2/10 como população elegível",
            "tempo": "NÃO DEFINIDO: ano do arquivo não equivale a ano do diagnóstico",
            "faltam": ["Coorte definida por tipo de entrada e data de diagnóstico",
                       "Critérios oficiais da modalidade de TB e registro de desfechos",
                       "Vinculação e desduplicação dos registros",
                       "Verificação de dicionário específico de ano/versão"],
            "fonte_oficial": "https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/svsa/tuberculose/caderno-de-indicadores-da-tuberculose",
            "aviso": "Definição epidemiológica não operacional. Não calcular a partir de dados reais, comparar com metas oficiais ou usar em decisões clínicas."}
