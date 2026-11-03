"""Frozen, human-curated official portal metadata for ZIKA 2024.

This module does not access the website at runtime, fetch datasets, parse
patient files, or authenticate a binary. It compares TWO versioned public
metadata records with the existing allowlisted annual pointer catalogue.
"""
from __future__ import annotations

import hashlib
import json

from .official_annual_resources import consultar_recursos_oficiais_ano

SCHEMA = "sinan-zika-official-page-metadata-snapshot-v1"
CAPTURE_DATE = "2026-11-03"
PACKAGE_ID = "4557ba96-7d52-4a56-bd6f-f99a5af09f77"

# Literal human-reviewed observations on the two original CKAN resource pages.
# Date of LAST MODIFICATION is intentionally excluded: the portal updates
# dynamically, and it does not identify the biological file's cut-off date.
SNAPSHOT = (
    {
        "resource_id": "264978ca-f795-4940-b5d3-ebc21e7d1c7c",
        "portal_title": "Zika Vírus - 2024",
        "portal_format": "JSON",
        "portal_status": "active",
        "portal_package_id": PACKAGE_ID,
        "portal_page": (
            "https://dadosabertos.saude.gov.br/dataset/"
            "arboviroses-zika-virus/resource/"
            "264978ca-f795-4940-b5d3-ebc21e7d1c7c"
        ),
        "portal_distribution": (
            "https://s3.sa-east-1.amazonaws.com/"
            "ckan.saude.gov.br/SINAN/Zikavirus/json/ZIKABR24.json.zip"
        ),
    },
    {
        "resource_id": "41bfda2a-5826-4ef9-8913-497247e6c9ce",
        "portal_title": "Zika Vírus - 2024",
        "portal_format": "PARQUET",
        "portal_status": "active",
        "portal_package_id": PACKAGE_ID,
        "portal_page": (
            "https://dadosabertos.saude.gov.br/dataset/"
            "arboviroses-zika-virus/resource/"
            "41bfda2a-5826-4ef9-8913-497247e6c9ce"
        ),
        "portal_distribution": (
            "https://s3.sa-east-1.amazonaws.com/"
            "ckan.saude.gov.br/SINAN/Zikavirus/parquet/ZIKABR24.parquet.zip"
        ),
    },
)
REQUIRED = frozenset({
    "resource_id", "portal_title", "portal_format", "portal_status",
    "portal_package_id", "portal_page", "portal_distribution",
})


def confrontar_snapshot_portal_zika_2024(
    snapshot: tuple[dict, ...] = SNAPSHOT,
) -> dict:
    """Reject drift or injected approval claims against the curated catalogue."""
    if not isinstance(snapshot, tuple) or len(snapshot) != 2:
        raise ValueError("Snapshot documental exige exatamente dois recursos")
    annual = consultar_recursos_oficiais_ano("ZIKA", 2024)
    if (annual["quantidade_recursos_catalogados"] != 2
            or annual["documento_de_dicionario_localizado"]
            or annual["arquivo_binario_verificado"]
            or annual["publicacao_autorizada"]
            or annual["microdados_acessados"]):
        raise ValueError("Estado do catálogo ZIKA/2024 não documental")
    expected = {r["resource_id"]: r for r in annual["recursos"]}
    ids = set()
    verified = []
    for record in snapshot:
        if not isinstance(record, dict) or set(record) != REQUIRED:
            raise ValueError("Metadados oficiais fora do esquema estrito")
        rid = record["resource_id"]
        if not isinstance(rid, str) or rid not in expected or rid in ids:
            raise ValueError("UUID externo inválido ou duplicado")
        ids.add(rid)
        annual_record = expected[rid]
        if (record["portal_title"] != "Zika Vírus - 2024"
                or record["portal_status"] != "active"
                or record["portal_package_id"] != PACKAGE_ID
                or record["portal_format"] != annual_record["formato"]
                or record["portal_page"] != annual_record["pagina_recurso_oficial"]
                or record["portal_distribution"] != annual_record[
                    "url_distribuicao_publicada"
                ]):
            raise ValueError("Página e registro documental apresentam divergência")
        verified.append({
            "resource_id": rid,
            "formato_documentado": record["portal_format"],
            "estado_observado_na_pagina": "active",
            "id_conjunto_documentado": PACKAGE_ID,
            "pagina_oficial": record["portal_page"],
            "concorda_com_catalogo_local": True,
            "site_reconsultado_nesta_execucao": False,
            "arquivo_binario_verificado": False,
            "checksum_oficial_verificado": False,
            "layout_2024_validado": False,
            "situacao_preliminar_final_confirmada": False,
            "publicacao_autorizada": False,
        })
    if ids != set(expected):
        raise ValueError("Amostra de IDs está incompleta")
    fingerprint = hashlib.sha256(json.dumps(
        snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    return {
        "schema_version": SCHEMA,
        "agravo": "ZIKA",
        "ano_rotulado": 2024,
        "data_curadoria_documental": CAPTURE_DATE,
        "registros_documentais_concordantes": len(verified),
        "registros": verified,
        "sha256_snapshot_metadados": fingerprint,
        "fonte_primaria": "Ministério da Saúde — Portal de Dados Abertos do SUS",
        "consulta_web_nesta_execucao": False,
        "arquivos_binarios_acessados": 0,
        "campos_clinicos_lidos": 0,
        "arquivo_anual_autenticado": False,
        "dicionario_aplicavel_2024_validado": False,
        "indicador_real_homologado": False,
        "publicacao_autorizada": False,
        "status": "IDENTIDADE_DOCUMENTAL_CONFERIDA_SEM_VALIDACAO_DO_ARQUIVO",
        "aviso": (
            "A identidade UUID/formato/conjunto nas páginas oficiais foi "
            "anotada em snapshot histórico. Isto não é uma nova consulta "
            "online, não autentica o arquivo binário, não atesta sua "
            "consolidação ou o esquema de 2024 e não autoriza publicar."
        ),
    }
