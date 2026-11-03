"""Reviewed public *documentary* reference for the ZIKA dictionary PDF.

The official Ministry resource page directly links a public 8-page PDF
identified as "Sinan Net — Dicionário de Dados — ZIKA". It numbers 37
fields. This module does not download/parse a PDF during CLI execution,
does not read cases or private files, and DOES NOT assert that the
2024 JSON/Parquet release has exactly those columns.

The pages were visually inspected during documentary curation.
There is no verified official SHA256 or validated 2024 dataset schema.
"""
from __future__ import annotations

from .zika_resource_identity import confrontar_snapshot_portal_zika_2024

SCHEMA = "sinan-zika-dictionary-documentary-reference-v1"
RESOURCE_ID = "58038262-c745-46ea-979b-8727eb08ec5c"
PACKAGE_ID = "4557ba96-7d52-4a56-bd6f-f99a5af09f77"
RESOURCE_URL = (
    "https://dadosabertos.saude.gov.br/dataset/"
    "arboviroses-zika-virus/resource/" + RESOURCE_ID
)
PDF_URL = (
    "https://s3.sa-east-1.amazonaws.com/"
    "ckan.saude.gov.br/SINAN/Zikavirus/dic_dados_zika.pdf"
)
# Page numbers are 1-based human-readable page indices.
# Selected examples, not a generated/validated schema or a full mapping.
VISIBLE_FIELD_EXAMPLES = (
    ("tp_not", 1, "char(1)"),
    ("id_agravo", 1, "char(5)"),
    ("dt_notific", 1, "date(8)"),
    ("cs_sexo", 3, "char(1)"),
    ("cs_raca", 4, "char(1)"),
    ("classi_fin", 6, "char(2)"),
    ("criterio", 6, "char(2)"),
    ("dt_encerra", 8, "date(8)"),
    ("tp_sistema", 8, "char(1)"),
)


def diagnosticar_pdf_oficial_zika() -> dict:
    """Curated source evidence, fully offline. Never promote scientific gates."""
    metadata = confrontar_snapshot_portal_zika_2024()
    if (metadata["registros_documentais_concordantes"] != 2
            or metadata["publicacao_autorizada"]
            or metadata["arquivo_anual_autenticado"]):
        raise ValueError("Fonte anual de Zika divergiu dos estados não homologados")
    return {
        "schema_version": SCHEMA,
        "agravo": "ZIKA",
        "ano_do_arquivo_pretendido": 2024,
        "titulo_pdf": "Sinan Net — Dicionário de Dados — ZIKA",
        "id_recurso_dicionario": RESOURCE_ID,
        "id_conjunto_portal": PACKAGE_ID,
        "url_recurso_governamental": RESOURCE_URL,
        "url_pdf_governamental": PDF_URL,
        "formato": "PDF",
        "numero_de_paginas_visualizado": 8,
        "numero_de_campos_numerados_no_documento": 37,
        "exemplos_de_campos_visualmente_conferidos": [
            {"campo": name, "pagina_documental": page, "tipo_documentado": ftype}
            for name, page, ftype in VISIBLE_FIELD_EXAMPLES
        ],
        "documento_especifico_zika_localizado": True,
        "ligacao_resource_id_pdf_conferida_no_portal": True,
        "documento_inspecionado_visualmente": True,
        "conteudo_completo_transcrito_ou_homologado": False,
        "checksum_pdf_oficial_publicado": False,
        "sha256_bytes_pdf_efetivamente_calculado": False,
        "dicionario_comparado_a_cabecalho_2024": False,
        "campos_da_distribuicao_2024_lidos": 0,
        "integridade_zip_2024_verificada": False,
        "data_corte_do_arquivo_2024_verificada": False,
        "situacao_final_preliminar_2024_verificada": False,
        "indicadores_reais_homologados": 0,
        "publicacao_autorizada": False,
        "status": "DICIONARIO_ZIKA_PDF_LOCALIZADO_SEM_CONFRONTO_COM_2024",
        "aviso": (
            "Página e PDF governamentais específicos de Zika localizados. "
            "Os 37 campos numerados descrevem o documento, não a exportação "
            "ZIKABR24. Sem checksum oficial, confronto real de esquema, "
            "data de corte, homologação epidemiológica ou publicação."
        ),
    }
