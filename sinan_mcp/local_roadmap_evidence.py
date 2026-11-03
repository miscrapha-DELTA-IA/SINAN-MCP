"""Bind an existing DENG/2024 header-only crosswalk to the local roadmap.

Only attaches local evidence, not approval. Opens a private JSON audit report,
NEVER a ZIP, CSV, patient row, SQLite database, network resource or MCP tool.
The original roadmap and evidence reports remain untouched.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .local_dengue_dictionary_crosswalk import RESOURCE_ID as DENG_RESOURCE
from .roadmap_readiness import (
    MAX_BYTES, SHA, _strict_json_pairs, avaliar_checklist, load_checklist,
    validate_checklist,
)

MAX_EVIDENCE_BYTES = 128_000
REPORT_SCHEMA = "sinan-private-dengue-crosswalk-candidate-v1"
GATE = "dicionario_esquema"


def _private_crosswalk_digest(path: str | Path) -> str:
    """Only parse the expected unapproved crosswalk; never trust arbitrary JSON."""
    p = Path(path).expanduser()
    if (p.is_symlink() or not p.is_file()
            or p.suffix.lower() != ".json"
            or not 2 <= p.stat().st_size <= MAX_EVIDENCE_BYTES):
        raise ValueError("Parecer local de esquema ausente ou fora do limite")
    raw = p.read_bytes()
    if len(raw) > MAX_EVIDENCE_BYTES:
        raise ValueError("Parecer local de esquema excessivo")
    try:
        report = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_json_pairs)
    except (UnicodeError, ValueError):
        raise ValueError("Parecer local de esquema malformado") from None
    if not isinstance(report, dict):
        raise ValueError("Parecer de esquema deve ser objeto JSON")
    required = {
        "schema_version": REPORT_SCHEMA,
        "resource_id": DENG_RESOURCE,
        "agravo": "DENG",
        "ano_rotulado_no_portal": 2024,
        "status_revisao": "PENDENTE",
        "publicacao_autorizada": False,
        "autorizacao_analise_real": False,
        "dicionario_aplicavel_a_exportacao_2024_validado": False,
        "dominios_categoricos_verificados": False,
        "linhas_de_pacientes_lidas": 0,
        "campos_csv_desconhecidos_incluidos_no_parecer": False,
    }
    if any(
        k not in report or type(report[k]) is not type(expected)
        or report[k] != expected
        for k, expected in required.items()
    ):
        raise ValueError("Parecer nao e evidencia pendente do recurso DENG/2024")
    for k in ("pdf_atual_sha256_local", "zip_sha256_local", "pdf2015_sha256_local"):
        value = report.get(k)
        if not isinstance(value, str) or not SHA.fullmatch(value):
            raise ValueError("Parecer sem hashes locais coerentes")
    fields = ("n_campos_csv", "n_nomes_unicos_pdf_atual", "nome_comum_pdf_atual_csv",
              "quantidade_csv_fora_pdf_atual")
    if any(type(report.get(k)) is not int or report[k] < 0 or report[k] > 2000 for k in fields):
        raise ValueError("Contagens do parecer invalidas")
    if report["nome_comum_pdf_atual_csv"] + report["quantidade_csv_fora_pdf_atual"] != report["n_campos_csv"]:
        raise ValueError("Campos CSV do parecer nao reconciliam")
    missing = report.get("nomes_pdf_atual_ausentes_csv")
    if (not isinstance(missing, list)
            or any(not isinstance(n, str) for n in missing)
            or len(missing) + report["nome_comum_pdf_atual_csv"] != report["n_nomes_unicos_pdf_atual"]):
        raise ValueError("Campos documentais do parecer nao reconciliam")
    return hashlib.sha256(raw).hexdigest()


def vincular_parecer_dengue_checklist_local(
    checklist_path: str | Path, parecer_path: str | Path, destino: str | Path,
) -> dict:
    """Produce a NEW pending-readiness JSON with only a SHA-256 evidence pointer."""
    checklist = load_checklist(checklist_path)
    scope = checklist["scope"]
    if (scope["agravo"] != "DENG" or scope["ano_do_arquivo"] != 2024
            or scope["resource_id"] != DENG_RESOURCE):
        raise ValueError("Checklist nao corresponde ao recurso DENG/2024")
    if checklist["gates"][GATE] != {
        "situacao": "PENDENTE", "evidencia_sha256_local": None,
    }:
        raise ValueError("Gate documental ja possui evidencia; revisar antes de alterar")
    digest = _private_crosswalk_digest(parecer_path)
    checklist["gates"][GATE] = {
        "situacao": "EVIDENCIA_LOCAL_NAO_VALIDADA",
        "evidencia_sha256_local": digest,
    }
    validate_checklist(checklist)
    out = Path(destino).expanduser()
    if (out.is_symlink() or out.suffix.lower() != ".json"
            or not out.parent.is_dir() or out.parent.is_symlink()):
        raise ValueError("Destino privado inadequado")
    # Prevent accidental cross-directory export or replacement of source.
    origin = Path(checklist_path).expanduser()
    evidence = Path(parecer_path).expanduser()
    if (out.parent.resolve() != origin.parent.resolve()
            or evidence.parent.resolve() != origin.parent.resolve()):
        raise ValueError("Checklists e evidencias devem permanecer na mesma pasta privada")
    fd = os.open(str(out), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(checklist, file, ensure_ascii=False, indent=2)
            file.write("\n")
    except BaseException:
        try:
            out.unlink()
        except OSError:
            pass
        raise
    summary = avaliar_checklist(checklist)
    return {
        "agravo": summary["agravo"],
        "ano_do_arquivo": summary["ano_do_arquivo"],
        "n_frentes_pendentes": summary["n_frentes_pendentes"],
        "n_frentes_com_evidencia_local_nao_validada": summary[
            "n_frentes_com_evidencia_local_nao_validada"
        ],
        "gate_com_evidencia_local": GATE,
        "parecer_epidemiologico_aprovado": False,
        "acesso_remoto_com_dados_reais_autorizado": False,
        "publicacao_autorizada": False,
        "status": summary["status"],
    }
