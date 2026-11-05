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
