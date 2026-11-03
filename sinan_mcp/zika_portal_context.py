"""Curated official Zika publication context; no patient or file processing.

The national catalogue's description concerns how Zika cases are reported
and historical releases are disseminated. It is NOT an attestation of the
individual 2024 JSON/Parquet file, data-cutoff date, or applicable schema.
"""
from __future__ import annotations

from .official_annual_resources import consultar_recursos_oficiais_ano
from .zika_official_dictionary_reference import PDF_URL, RESOURCE_URL

SCHEMA = "sinan-zika-2024-portal-context-v1"
SOURCE_URL = "https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus"
SOURCE_TITLE = "Sinan/Vírus Zika"
DICT_LISTING_TITLE = "Dicionário de dados - Zika Vírus"
DICT_LISTING_DATE = "2025-07-14"
# The official resource page and 8-page public PDF are now located.
# No clinical 2024 data, checksum or whole-export scheme has been validated.


def consultar_contexto_portal_zika_2024() -> dict:
    """Describe separately official catalogue statements vs unverified file."""
    annual = consultar_recursos_oficiais_ano("ZIKA", 2024)
    if (annual["quantidade_recursos_catalogados"] != 2
            or annual["documento_de_dicionario_localizado"]
            or annual["arquivo_binario_verificado"]
            or annual["publicacao_autorizada"]):
        raise ValueError("Catálogo ZIKA/2024 não satisfaz invariantes documentais")
    return {
        "schema_version": SCHEMA,
        "agravo": "ZIKA",
        "ano_rotulado_no_arquivo": 2024,
        "url_conjunto_oficial": SOURCE_URL,
        "titulo_conjunto_oficial": SOURCE_TITLE,
        "sistema_de_notificacao_descrito_no_conjunto": "SINAN Net",
        "sistema_de_notificacao_mencionado_pelo_portal": True,
        "sistema_de_origem_dos_bytes_2024_autenticado": False,
        "notificacao_compulsoria_descrita": True,
        "prazo_de_encerramento_documentado_dias": 60,
        "definicao_textual_caso_provavel": (
            "Suspeitos notificados, excluindo os casos descartados"
        ),
        "definicao_de_caso_validada_em_registros_2024": False,
        "series_historicas_congeladas_em_datas_especificas_por_ano": True,
        "data_de_corte_exata_do_zip_2024": None,
        "data_atualizacao_portal_equivale_a_corte_epidemiologico": False,
        "nota_geografica_espirito_santo": (
            "Desde 2020 ES utiliza e-SUS Vigilancia; segundo o portal, "
            "arboviroses urbanas incluem Zika proveniente de SINAN Net"
        ),
        "cobertura_geografica_do_arquivo_2024_validada": False,
        "recurso_de_dicionario_zika_listado_no_portal": True,
        "titulo_recurso_dicionario": DICT_LISTING_TITLE,
        "data_de_atualizacao_listada_do_dicionario": DICT_LISTING_DATE,
        "url_exata_pdf_dicionario_zika_recuperada": PDF_URL,
        "pagina_exata_recurso_dicionario_zika": RESOURCE_URL,
        "pdf_inspecionado_visual_documentalmente": True,
        "conteudo_pdf_dicionario_zika_auditado": False,
        "dicionario_de_zika_aplicavel_ao_ano_2024_validado": False,
        "distribuicoes_anuais_catalogadas": 2,
        "arquivos_binarios_2024_verificados": 0,
        "campos_clinicos_lidos": 0,
        "dados_reais_disponiveis_no_mcp_publico": False,
        "indicadores_reais_homologados": 0,
        "publicacao_autorizada": False,
        "status": "CONTEXTO_OFICIAL_DO_CONJUNTO_SEM_VALIDACAO_DO_ARQUIVO",
        "aviso": (
            "O portal descreve SINAN Net, atualização das séries e lista "
            "um dicionário específico de Zika cujo PDF foi localizado "
            "e visualizado. Não foi estabelecida a data de corte nem a "
            "compatibilidade com a exportação 2024. Versão, esquema, "
            "autenticidade dos ZIPs, coorte e "
            "consolidação seguem pendentes. Nenhum dado clínico foi lido."
        ),
    }
