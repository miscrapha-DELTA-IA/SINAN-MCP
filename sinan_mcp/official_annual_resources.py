"""Curated pointers to annual file distributions in the official SUS open-data portal.

The Ministry's resource detail pages identify a named distribution for a year,
which is stronger than a general directory listing, but is NOT proof of which
dictionary version applies, source file byte identity, completeness, clinical
validity, consolidation status or permission to publish. Public, read-only
metadata; no network clients or local data readers live in this module.
"""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from importlib.resources import files
from urllib.parse import urlsplit

from .year_evidence_registry import consultar_evidencia_agravo_ano

SCHEMA = "sinan-public-resource-pointers-v1"
SCOPE = "metadados_de_recursos_anualizados_identificados_no_portal_oficial_sem_verificar_bytes"
DATASET_SLUGS = {
    "DENG": ("arboviroses-dengue", "Dengue", "DENG"),
    "CHIK": ("arboviroses-febre-de-chikungunya", "Chikungunya", "CHIK"),
}
PUBLICATION = "Ministério da Saúde — Portal de Dados Abertos do SUS"
RESOURCE_ID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
REQUIRED = frozenset({
    "agravo_alias_interno", "ano_rotulado_no_portal", "titulo_recurso",
    "resource_id", "dataset_url", "resource_url", "distribution_url",
    "distribution_format", "archive_filename", "archive_internal_extension",
    "publisher", "link_documental_do_dicionario_identificado",
    "arquivo_binario_baixado_ou_verificado",
    "checksum_sha256_publicado_pela_autoridade",
    "esquema_do_recurso_comparado_com_dicionario",
    "status_preliminar_final_verificado", "uso_epidemiologico_validado",
    "publicacao_de_resultados_autorizada",
})
NEGATIVE = frozenset({
    "arquivo_binario_baixado_ou_verificado",
    "esquema_do_recurso_comparado_com_dicionario",
    "status_preliminar_final_verificado", "uso_epidemiologico_validado",
    "publicacao_de_resultados_autorizada",
})
NOTICE = (
    "Recurso individual identificado em catálogo governamental; não comprova "
    "download, integridade dos bytes, aplicação do dicionário ao arquivo, "
    "estado final ou qualidade clínica. Não houve processamento de dados."
)


def _obj(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("JSON do catálogo com campo duplicado")
        out[k] = v
    return out


def _url(actual, *, host, exact_path):
    if not isinstance(actual, str) or len(actual) > 512:
        raise ValueError("URL de distribuição inválida")
    try:
        u = urlsplit(actual)
        port = u.port
    except ValueError as exc:
        raise ValueError("URL de distribuição inválida") from exc
    if (u.scheme != "https" or u.hostname != host
            or u.username is not None or u.password is not None
            or port not in (None, 443) or u.path != exact_path
            or u.query or u.fragment or "\\" in actual
            or "%" in actual or "//" in u.path
            or any(ord(ch) < 33 for ch in actual)):
        raise ValueError("URL fora do domínio e caminho específico oficial")


def validate_resource_catalog(doc: object) -> dict:
    if (not isinstance(doc, dict)
            or set(doc) != {"schema_version", "catalog_revision", "scope", "records"}
            or doc["schema_version"] != SCHEMA or doc["scope"] != SCOPE
            or not isinstance(doc["catalog_revision"], str)
            or not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}-r[0-9]{1,2}",
                                doc["catalog_revision"])):
        raise ValueError("Cabeçalho do registro anual inválido")
    rows = doc["records"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 50:
        raise ValueError("Lista anual inválida")
    ids = set()
    files_seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != REQUIRED:
            raise ValueError("Recurso com campos inesperados ou ausentes")
        code, year = row["agravo_alias_interno"], row["ano_rotulado_no_portal"]
        if (not isinstance(code, str) or code not in DATASET_SLUGS
                or type(year) is not int or year != 2024):
            raise ValueError("Este catálogo piloto só possui anos/agravos checados")
        slug, folder, prefix = DATASET_SLUGS[code]
        resource_id = row["resource_id"]
        if not isinstance(resource_id, str) or not RESOURCE_ID.fullmatch(resource_id):
            raise ValueError("ID do recurso oficial inválido")
        if resource_id in ids:
            raise ValueError("ID de distribuição duplicado")
        ids.add(resource_id)
        if row["publisher"] != PUBLICATION:
            raise ValueError("Editor declarado não corresponde ao catálogo")
        expected_title = ("Dengue - 2024" if code == "DENG"
                          else "Febre de Chikungunya - 2024")
        if row["titulo_recurso"] != expected_title:
            raise ValueError("Título anual inesperado")
        fmt = row["distribution_format"]
        if not isinstance(fmt, str) or fmt not in {"CSV", "JSON"}:
            raise ValueError("Formato ainda não curado")
        lower = fmt.lower()
        filename = f"{prefix}BR24.{lower}.zip"
        if (row["archive_filename"] != filename
                or row["archive_internal_extension"] != "." + lower):
            raise ValueError("Nome do pacote anual diverge da distribuição")
        if (code, year, fmt) in files_seen:
            raise ValueError("Mesmo formato anual publicado duas vezes no índice")
        files_seen.add((code, year, fmt))
        dataset_path = "/dataset/" + slug
        resource_path = dataset_path + "/resource/" + resource_id
        distribution_path = (
            "/ckan.saude.gov.br/SINAN/" + folder + "/" + lower + "/" + filename
        )
        _url(row["dataset_url"], host="dadosabertos.saude.gov.br",
             exact_path=dataset_path)
        _url(row["resource_url"], host="dadosabertos.saude.gov.br",
             exact_path=resource_path)
        _url(row["distribution_url"], host="s3.sa-east-1.amazonaws.com",
             exact_path=distribution_path)
        if row["checksum_sha256_publicado_pela_autoridade"] is not None:
            raise ValueError("Checksum governamental não foi identificado")
        if row["link_documental_do_dicionario_identificado"] is not True:
            raise ValueError("Índice de referência documental ausente")
        if any(row[k] is not False for k in NEGATIVE):
            raise ValueError("Edição anual NÃO pode ser auto-aprovada pelo JSON")
    return doc


@lru_cache(maxsize=1)
def _index():
    source = files("sinan_mcp").joinpath("registry", "official_annual_resources.json")
    contents = source.read_text(encoding="utf-8")
    if len(contents.encode("utf-8")) > 80000:
        raise ValueError("Recurso anual excede limite")
    parsed = validate_resource_catalog(json.loads(contents, object_pairs_hook=_obj))
    fingerprint = hashlib.sha256(json.dumps(
        parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()
    return fingerprint, tuple(parsed["records"])


def consultar_recursos_oficiais_ano(agravo: str, ano: int) -> dict:
    """Metadata-only lookup: a catalogued distribution is not a validated dataset."""
    evidence = consultar_evidencia_agravo_ano(agravo, ano)
    digest, all_records = _index()
    code = evidence["agravo_alias_interno"]
    rows = [
        row for row in all_records
        if row["agravo_alias_interno"] == code and row["ano_rotulado_no_portal"] == ano
    ]
    return {
        "schema_version": SCHEMA,
        "agravo_alias_interno": code,
        "ano_rotulado_no_portal": ano,
        "estado": ("recurso_anual_identificado_no_catalogo"
                   if rows else "sem_recurso_anual_curado"),
        "recursos": [
            {
                "resource_id": row["resource_id"],
                "formato": row["distribution_format"],
                "nome_arquivo": row["archive_filename"],
                "pagina_recurso_oficial": row["resource_url"],
                "pagina_conjunto_oficial": row["dataset_url"],
                "url_distribuicao_publicada": row["distribution_url"],
                "checksum_oficial_publicado": False,
                "arquivo_local_verificado": False,
            }
            for row in rows
        ],
        "quantidade_recursos_catalogados": len(rows),
        "catalog_metadata_sha256": digest,
        "documento_de_dicionario_localizado": evidence[
            "link_dicionario_oficial_localizado"
        ],
        "compatibilidade_dicionario_ano_verificada": False,
        "arquivo_binario_verificado": False,
        "sistema_de_origem_anual_verificado": False,
        "situacao_preliminar_final_confirmada": False,
        "analise_epidemiologica_autorizada": False,
        "publicacao_autorizada": False,
        "microdados_acessados": False,
        "aviso": NOTICE,
    }


def listar_recursos_oficiais_anuais() -> dict:
    digest, all_records = _index()
    unique = sorted({(r["agravo_alias_interno"], r["ano_rotulado_no_portal"])
                     for r in all_records})
    return {
        "schema_version": SCHEMA,
        "catalog_metadata_sha256": digest,
        "pares_com_recursos_identificados": [
            {"agravo": code, "ano": year,
             "estado": "recurso_anual_identificado_no_catalogo"}
            for code, year in unique
        ],
        "quantidade_distribuicoes_identificadas": len(all_records),
        "arquivos_binarios_verificados": 0,
        "anos_com_dicionario_aplicavel_verificado": 0,
        "analises_reais_publicadas": 0,
        "aviso": NOTICE,
    }
