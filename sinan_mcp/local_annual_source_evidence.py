"""Offline source-evidence dossier for the DENG/2024 ZIP and readiness checklist.

This code compares exact local ZIP bytes, official-portal resource metadata
curated in the repo and a previous PENDING private header-only crosswalk.
It DOES NOT authenticate Ministry of Health bytes, certify their consolidation,
interpret patient data, publish results or access MCP/SQLite/network.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from .local_distribution_review import conferir_zip_recurso_local
from .local_roadmap_evidence import (
    DENG_RESOURCE, GATE as DICTIONARY_GATE, _private_crosswalk_digest,
)
from .local_schema_review import _resource
from .roadmap_readiness import (
    _strict_json_pairs, avaliar_checklist, load_checklist, SHA, validate_checklist,
)

SCHEMA = "sinan-private-annual-source-evidence-dossier-v1"
GATE = "fonte_agravo_ano"
MAX_REPORT = 128_000
MAX_DOSSIER = 32_768


def _safe_json_file(path: str | Path, max_bytes: int) -> tuple[dict, bytes]:
    p = Path(path).expanduser()
    if (p.is_symlink() or not p.is_file() or p.suffix.lower() != ".json"
            or not 2 <= p.stat().st_size <= max_bytes):
        raise ValueError("Arquivo JSON privado ausente ou fora dos limites")
    raw = p.read_bytes()
    if len(raw) > max_bytes:
        raise ValueError("Arquivo JSON privado excede limite")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_json_pairs)
    except (UnicodeError, ValueError):
        raise ValueError("JSON privado malformado") from None
    if not isinstance(obj, dict):
        raise ValueError("JSON privado deve ser objeto")
    return obj, raw


def _crosswalk(path: str | Path) -> tuple[dict, str]:
    digest = _private_crosswalk_digest(path)
    obj, raw = _safe_json_file(path, MAX_REPORT)
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("Parecer de esquema alterado durante leitura")
    return obj, digest


def _curated_source() -> dict:
    item = _resource(DENG_RESOURCE)
    if (item["agravo_alias_interno"] != "DENG"
            or item["ano_rotulado_no_portal"] != 2024
            or item["distribution_format"] != "CSV"
            or item["archive_filename"] != "DENGBR24.csv.zip"):
        raise ValueError("Registro de fonte anual nao corresponde a DENG/2024 CSV")
    return item


def _write_exclusive(path: str | Path, data: dict) -> None:
    target = Path(path).expanduser()
    if (target.is_symlink() or target.suffix.lower() != ".json"
            or not target.parent.is_dir() or target.parent.is_symlink()):
        raise ValueError("Destino JSON privado invalido")
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except BaseException:
        try:
            target.unlink()
        except OSError:
            pass
        raise


def preparar_dossie_fonte_dengue_local(
    zip_path: str | Path, parecer_path: str | Path, destino: str | Path,
) -> dict:
    """Inspect ZIP central-directory + local SHA, never decompress records."""
    source = _curated_source()
    prior, digest = _crosswalk(parecer_path)
    result = conferir_zip_recurso_local(DENG_RESOURCE, zip_path)
    if (result.get("schema_version")
            != "sinan-local-official-resource-zip-inspection-v1"
            or result.get("resource_id") != DENG_RESOURCE
            or result.get("formato_declarado") != "CSV"
            or result.get("arquivo_zip_estrutura_compativel_com_nome_registrado") is not True
            or result.get("arquivos_extraidos") != 0
            or result.get("conteudo_clinico_lido") is not False
            or result.get("origem_dos_bytes_autenticada") is not False
            or result.get("publicacao_autorizada") is not False
            or result.get("arquivo_pacote_sha256_local") != prior["zip_sha256_local"]):
        raise ValueError("ZIP e parecer anterior nao conciliados ou aprovados")
    zip_sha = result["arquivo_pacote_sha256_local"]
    zip_size = result["arquivo_pacote_bytes_local"]
    if (not isinstance(zip_sha, str) or not SHA.fullmatch(zip_sha)
            or type(zip_size) is not int or zip_size < 22):
        raise ValueError("Hash ou tamanho ZIP local invalido")
    # Keep all private artifacts together, in a gitignored location chosen by the operator.
    if Path(destino).expanduser().parent.resolve() != Path(parecer_path).expanduser().parent.resolve():
        raise ValueError("Parecer e dossie devem ficar na mesma pasta privada")
    dossier = {
        "schema_version": SCHEMA,
        "resource_id": DENG_RESOURCE,
        "agravo": "DENG",
        "ano_rotulado_no_portal": 2024,
        "distribution_url_curated": source["distribution_url"],
        "resource_url_curated": source["resource_url"],
        "archive_filename": source["archive_filename"],
        "format": "CSV",
        "crosswalk_pending_sha256_local": digest,
        "zip_sha256_local": zip_sha,
        "zip_tamanho_bytes_local": zip_size,
        "pdf_documental_sha256_local": prior["pdf_atual_sha256_local"],
        "observado_localmente_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "inspecao_integridade_local": True,
        "arquivo_estruturalmente_compativel": True,
        "registros_clinicos_lidos": 0,
        "origem_autenticada_por_autoridade": False,
        "checksum_oficial_verificado": False,
        "data_corte_verificada": False,
        "status_consolidacao": "DESCONHECIDO",
        "dicionario_ano_homologado": False,
        "revisao_institucional_independente": "PENDENTE",
        "publicacao_autorizada": False,
    }
    _validate_dossier(dossier)
    _write_exclusive(destino, dossier)
    return {
        "recurso_reconhecido": True,
        "zip_local_conciliado_com_parecer": True,
        "status_consolidacao": "DESCONHECIDO",
        "origem_oficial_autenticada": False,
        "uso_real_autorizado": False,
        "publicacao_autorizada": False,
    }


def _validate_dossier(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "resource_id", "agravo", "ano_rotulado_no_portal",
        "distribution_url_curated", "resource_url_curated", "archive_filename",
        "format", "crosswalk_pending_sha256_local", "zip_sha256_local",
        "zip_tamanho_bytes_local", "pdf_documental_sha256_local",
        "observado_localmente_utc", "inspecao_integridade_local",
        "arquivo_estruturalmente_compativel", "registros_clinicos_lidos",
        "origem_autenticada_por_autoridade", "checksum_oficial_verificado",
        "data_corte_verificada", "status_consolidacao",
        "dicionario_ano_homologado", "revisao_institucional_independente",
        "publicacao_autorizada",
    }:
        raise ValueError("Dossie de fonte fora do contrato controlado")
    src = _curated_source()
    expected = {
        "schema_version": SCHEMA, "resource_id": DENG_RESOURCE,
        "agravo": "DENG", "ano_rotulado_no_portal": 2024,
        "distribution_url_curated": src["distribution_url"],
        "resource_url_curated": src["resource_url"],
        "archive_filename": src["archive_filename"], "format": "CSV",
        "inspecao_integridade_local": True,
        "arquivo_estruturalmente_compativel": True,
        "registros_clinicos_lidos": 0,
        "origem_autenticada_por_autoridade": False,
        "checksum_oficial_verificado": False,
        "data_corte_verificada": False, "status_consolidacao": "DESCONHECIDO",
        "dicionario_ano_homologado": False,
        "revisao_institucional_independente": "PENDENTE",
        "publicacao_autorizada": False,
    }
    if any(
        key not in value or type(value[key]) is not type(want) or value[key] != want
        for key, want in expected.items()
    ):
        raise ValueError("Dossie com origem, autorizacao ou status declarados indevidamente")
    for name in (
        "crosswalk_pending_sha256_local", "zip_sha256_local",
        "pdf_documental_sha256_local",
    ):
        if not isinstance(value[name], str) or not SHA.fullmatch(value[name]):
            raise ValueError("Dossie com SHA-256 invalido")
    if (type(value["zip_tamanho_bytes_local"]) is not int
            or not 22 <= value["zip_tamanho_bytes_local"] <= 3 * 1024**3):
        raise ValueError("Tamanho ZIP fora do limite")
    stamp = value["observado_localmente_utc"]
    if not isinstance(stamp, str) or len(stamp) != 20 or not stamp.endswith("Z"):
        raise ValueError("Horario local de auditoria invalido")
    try:
        datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError("Horario UTC invalido") from None
    return value


def vincular_dossie_fonte_dengue_roadmap_local(
    checklist_path: str | Path, parecer_path: str | Path,
    dossie_path: str | Path, destino: str | Path,
) -> dict:
    """Attach a source *evidence pointer* to a NEW private roadmap JSON."""
    checklist = load_checklist(checklist_path)
    scope = checklist["scope"]
    if (scope["agravo"] != "DENG" or scope["ano_do_arquivo"] != 2024
            or scope["resource_id"] != DENG_RESOURCE):
        raise ValueError("Checklist nao corresponde a DENG/2024 CSV")
    if checklist["gates"][GATE] != {
        "situacao": "PENDENTE", "evidencia_sha256_local": None,
    }:
        raise ValueError("Gate de fonte ja alterado; requer revisao")
    old, digest = _crosswalk(parecer_path)
    if checklist["gates"][DICTIONARY_GATE] != {
        "situacao": "EVIDENCIA_LOCAL_NAO_VALIDADA",
        "evidencia_sha256_local": digest,
    }:
        raise ValueError("O parecer de dicionario nao esta vinculado a este checklist")
    dossier, raw = _safe_json_file(dossie_path, MAX_DOSSIER)
    _validate_dossier(dossier)
    if (dossier["crosswalk_pending_sha256_local"] != digest
            or dossier["zip_sha256_local"] != old["zip_sha256_local"]
            or dossier["pdf_documental_sha256_local"] != old["pdf_atual_sha256_local"]):
        raise ValueError("Dossie e parecer nao representam a mesma evidencia")
    if len({
        Path(p).expanduser().parent.resolve()
        for p in (checklist_path, parecer_path, dossie_path, destino)
    }) != 1:
        raise ValueError("Artefatos devem permanecer na mesma pasta privada")
    checklist["gates"][GATE] = {
        "situacao": "EVIDENCIA_LOCAL_NAO_VALIDADA",
        "evidencia_sha256_local": hashlib.sha256(raw).hexdigest(),
    }
    validate_checklist(checklist)
    _write_exclusive(destino, checklist)
    summary = avaliar_checklist(checklist)
    return {
        "n_frentes_pendentes": summary["n_frentes_pendentes"],
        "n_frentes_com_evidencia_local_nao_validada":
            summary["n_frentes_com_evidencia_local_nao_validada"],
        "autenticidade_oficial_confirmada": False,
        "consolidacao_confirmada": False,
        "publicacao_autorizada": False,
        "status": summary["status"],
    }
