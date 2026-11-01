"""Curated scope: supported ingest/export != epidemiologically validated indicator."""
from __future__ import annotations

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
    return {"schema_version": "0.3", "agravos_piloto": CATALOGUE,
            "aviso": "Lista de módulos testados com dados sintéticos; não implica validação para todos os anos e layouts de SINAN.",
            "outros_agravos": "Podem ser importados experimentalmente pela CLI, mas não têm modelo científico curado."}


def metodologia_tuberculose() -> dict:
    return {"codigo": "TB_ABANDONO_EXPLORATORIO", "situacao": "NAO_OFICIAL",
            "numerador": "SITUA_ENCE em 2 ou 10",
            "denominador": "SITUA_ENCE em 1, 2 ou 10",
            "tempo": "Ano do arquivo importado, NÃO ano de diagnóstico",
            "faltam": ["Coorte definida por tipo de entrada e data de diagnóstico",
                       "Critérios oficiais da modalidade de TB e registro de desfechos",
                       "Vinculação e desduplicação dos registros",
                       "Verificação de dicionário específico de ano/versão"],
            "fonte_oficial": "https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/svsa/tuberculose/caderno-de-indicadores-da-tuberculose",
            "aviso": "Não comparar esta medida com metas oficiais, nem utilizá-la em decisões clínicas."}
