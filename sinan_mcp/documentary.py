"""Fixed, auditable public document pointers; NO external I/O or case datasets.

A URL discovered on an official institution website is NOT a reviewed SINAN
dictionary, authenticated download, cohort, real dataset or epidemiological
statistic. The metadata records only a dated institutional-page identification.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from importlib.resources import files
from urllib.parse import urlsplit

SCHEMA_VERSION = "sinan-documentary-registry-v1"
ALLOWED_HOSTS = {
    "www.gov.br", "portalsinan.saude.gov.br", "dadosabertos.saude.gov.br",
}
EXPECTED_CODES = {
    "TUBE", "DENG", "CHIK", "ZIKA", "HANS", "SIFA", "SIFC",
    "HEPA", "MENI", "VIOL", "LEIV", "LTAN", "ANIM", "COQU",
}


@lru_cache(maxsize=1)
def _load_registry() -> dict:
    """Read a single package resource, never remote URLs or private files."""
    import json

    registry = json.loads(
        files("sinan_mcp").joinpath("documentary_registry.json")
        .read_text(encoding="utf-8")
    )
    if registry.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Versão de registro documental não suportada")
    items = registry.get("registros", [])
    codes = [item.get("codigo_interno") for item in items]
    if len(codes) != 14 or set(codes) != EXPECTED_CODES:
        raise ValueError("O registro documental não cobre exatamente os 14 aliases conhecidos")
    ids: set[str] = set()
    for item in items:
        if (item.get("arquivos_reais_importados") is not False
                or item.get("indicadores_reais_homologados") is not False
                or item.get("dicionario_ano_versao_confrontado") is not False):
            raise ValueError("Metadado científico público não pode afirmar homologação real")
        if not item.get("referencias"):
            raise ValueError("Agravo sem página institucional documentada")
        for ref in item["referencias"]:
            parsed = urlsplit(ref.get("url", ""))
            if (parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS
                    or parsed.username or parsed.password or parsed.query or parsed.fragment):
                raise ValueError("Referência institucional não está na lista de domínios permitidos")
            if ref["id"] in ids:
                raise ValueError("Identificador documental duplicado")
            ids.add(ref["id"])
            if (ref.get("arquivo_baixado_e_validado") is not False
                    or ref.get("conteudo_integral_auditado") is not False
                    or ref.get("verificacao") != "pagina_publica_identificada_titulo_escopo"):
                raise ValueError("O registro não pode declarar documento validado")
    return registry


def obter_evidencias(codigo_interno: str) -> dict:
    """Return disconnected public metadata for a known code, never live data."""
    for item in _load_registry()["registros"]:
        if item["codigo_interno"] == codigo_interno:
            return deepcopy(item)
    raise ValueError("Alias interno não localizado no registro documental")


def termos_relacionados(codigo_interno: str) -> tuple[str, ...]:
    return tuple(obter_evidencias(codigo_interno)["termos_relacionados"])


def resumo_documental() -> dict:
    registry = _load_registry()
    return {
        "schema_version": registry["schema_version"],
        "data_da_curadoria": registry["data_da_curadoria"],
        "metodo": registry["metodo"],
        "limites": registry["limites"],
        "agravos_com_pagina_institucional": len(registry["registros"]),
        "referencias_de_paginas_institucionais": sum(
            len(item["referencias"]) for item in registry["registros"]
        ),
        "dicionarios_anuais_confrontados": 0,
        "arquivos_de_microdados_importados": 0,
        "indicadores_epidemiologicos_homologados": 0,
        "verificacao_ao_vivo_em_requisicoes_mcp": False,
        "data_do_ultimo_teste_online": None,
    }


@lru_cache(maxsize=1)
def _load_instruments_2024() -> dict:
    """Validate a frozen public snapshot made ONLY from official PDF metadata.

    The embedded field labels are descriptions of blank instruments, not row
    values from notifications or proof of a 2024 data-release schema.
    """
    import json
    import re

    data = json.loads(
        files("sinan_mcp").joinpath("public_instruments_2024.json")
        .read_text(encoding="utf-8")
    )
    if (data.get("schema_version") != "sinan-public-instruments-2024-v1"
            or data.get("scope") != "SOMENTE_METADADOS_DOCUMENTAIS_PUBLICOS_SEM_MICRODADOS"
            or data.get("actual_2024_dataset_schema_validated") is not False
            or data.get("independent_scientific_review_approved") is not False
            or data.get("real_data_access") is not False
            or set(data.get("diseases", {})) != {"ZIKA", "TUBE"}):
        raise ValueError("Publicação documental 2024 fora do escopo aprovado")

    doc_codes = {
        "ZIKA": {"ZIKA-DIC", "ZIKA-FICHA", "ZIKA-INSTR", "COMMON-NINDIV"},
        "TUBE": {"TUBE-DIC", "TUBE-FICHA", "TUBE-ACOMP", "COMMON-NINDIV"},
    }
    all_document_hashes: dict[str, str] = {}
    for disease, required in doc_codes.items():
        item = data["diseases"][disease]
        codes = [doc.get("id") for doc in item["documentos"]]
        if (item["ano_alvo"] != 2024 or set(codes) != required
                or len(codes) != 4
                or item["total_documentos"] != 4
                or item["correspondencia_arquivo_sinan_2024_validada"] is not False
                or item["revisao_independente_aprovada"] is not False
                or item["campos_do_agravo"] != (37 if disease == "ZIKA" else 15)
                or item["campos_de_notificacao_comum"] != 5
                or item["total_campos_documentais"] != (42 if disease == "ZIKA" else 20)
                or len(item["campos_documentais"]) != item["total_campos_documentais"]):
            raise ValueError("Inventário documental público inconsistente")
        for doc in item["documentos"]:
            pdf = urlsplit(doc["url_pdf"])
            origin = urlsplit(doc["url_origem"])
            if (pdf.scheme != "https"
                    or (pdf.hostname != "portalsinan.saude.gov.br" and
                        (pdf.hostname != "s3.sa-east-1.amazonaws.com"
                         or not pdf.path.startswith("/ckan.saude.gov.br/SINAN/Zikavirus/")))
                    or origin.scheme != "https"
                    or origin.hostname not in {"portalsinan.saude.gov.br", "dadosabertos.saude.gov.br"}
                    or doc["integridade_bytes_verificada"] is not True
                    or doc["assinatura_digital_da_fonte_verificada"] is not False
                    or doc["correspondencia_com_arquivo_2024_validada"] is not False
                    or doc["parecer_independente_aprovado"] is not False
                    or not re.fullmatch(r"[a-f0-9]{64}", doc["sha256_pdf"])):
                raise ValueError("Proveniência de PDF não satisfaz o gate público")
            previous = all_document_hashes.setdefault(doc["id"], doc["sha256_pdf"])
            if previous != doc["sha256_pdf"]:
                raise ValueError("Hash duplicado divergente para documento compartilhado")
        for field in item["campos_documentais"]:
            if (field["correspondencia_arquivo_2024"] != "NAO_VERIFICADA"
                    or field["revisao_humana"] != "PENDENTE"
                    or field["documento_id"] not in required
                    or not isinstance(field["pagina_pdf"], int)
                    or field["pagina_pdf"] < 1):
                raise ValueError("Alegação indevida na matriz de campos pública")
    if len(all_document_hashes) != 7:
        raise ValueError("A auditoria não contém sete documentos únicos")
    return data


def obter_instrumentos_2024(codigo_interno: str) -> dict | None:
    """Non-Zika/TB codes return no instrument; never fabricate a 2024 layout."""
    if codigo_interno not in {"ZIKA", "TUBE"}:
        return None
    return deepcopy(_load_instruments_2024()["diseases"][codigo_interno])


def resumo_instrumentos_2024(codigo_interno: str) -> dict | None:
    item = obter_instrumentos_2024(codigo_interno)
    if item is None:
        return None
    return {
        "ano_alvo": 2024,
        "documentos_pdf_com_hash_verificado": item["total_documentos"],
        "codigos_de_campo_localizados_na_pagina": item["total_campos_documentais"],
        "correspondencia_com_exportacao_2024_validada": False,
        "parecer_independente_aprovado": False,
        "fonte_metodologica": "https://github.com/miscrapha-DELTA-IA/SINAN-MCP/blob/main/docs/instruments-2024/REVIEW_PROTOCOL.md",
    }
