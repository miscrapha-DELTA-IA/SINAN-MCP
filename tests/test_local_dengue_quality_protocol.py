"""Synthetic metadata-only tests for DENG/2024 cohort-quality planning."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

import pytest

from sinan_mcp import local_dengue_quality_protocol as protocol
from sinan_mcp.roadmap_readiness import (
    preparar_checklist_local, diagnosticar_checklist_local,
)

RESOURCE = "4cf2f7b8-9920-41b5-817a-1ffc13e0690c"


def _synthetic(tmp_path, monkeypatch):
    roadmap = tmp_path / "roadmap-DENG-2024-com-fonte-local.json"
    preparar_checklist_local("DENG", 2024, roadmap, RESOURCE)
    dict_sha = "a" * 64
    source_bytes = b"PRIVATE_SYNTHETIC_DOSSIER_METADATA_NOT_PATIENTS"
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    obj = json.loads(roadmap.read_text(encoding="utf-8"))
    for key, sha in (("dicionario_esquema", dict_sha),
                     ("fonte_agravo_ano", source_sha)):
        obj["gates"][key] = {
            "situacao": "EVIDENCIA_LOCAL_NAO_VALIDADA",
            "evidencia_sha256_local": sha,
        }
    roadmap.write_text(json.dumps(obj), encoding="utf-8")
    dictionary = tmp_path / "parecer-pendente-dengue-crosswalk-2024.json"
    dictionary.write_text("{}", encoding="utf-8")
    dossier = tmp_path / "dossie-fonte-DENG-2024-local.json"
    dossier.write_bytes(source_bytes)
    old = {
        "zip_sha256_local": "b" * 64,
        "pdf_atual_sha256_local": "c" * 64,
    }
    source = {
        "crosswalk_pending_sha256_local": dict_sha,
        "zip_sha256_local": "b" * 64,
        "pdf_documental_sha256_local": "c" * 64,
    }
    monkeypatch.setattr(protocol, "_crosswalk", lambda _: (old, dict_sha))
    monkeypatch.setattr(protocol, "_safe_json_file",
                        lambda *args: (source, source_bytes))
    monkeypatch.setattr(protocol, "_validate_dossier", lambda _: None)
    return roadmap, dictionary, dossier, source


def test_plan_is_bound_to_evidence_but_does_not_promote_quality(tmp_path, monkeypatch):
    checklist, dictionary, dossier, _ = _synthetic(tmp_path, monkeypatch)
    out = tmp_path / "plan.json"
    result = protocol.preparar_plano_qualidade_dengue_local(
        checklist, dictionary, dossier, out
    )
    assert result["checkpoints_pendentes"] == len(protocol.CHECKPOINTS) == 9
    assert result["frentes_roadmap_ainda_pendentes"] == 5
    assert result["qualidade_coorte_concluida"] is False
    assert result["dados_clinicos_lidos"] is False
    assert result["publicacao_autorizada"] is False
    assert diagnosticar_checklist_local(checklist)["n_frentes_pendentes"] == 5
    obj = json.loads(out.read_text(encoding="utf-8"))
    assert obj["n_linhas_clinicas_lidas"] == 0
    assert obj["indicadores_reais_calculados"] is False
    assert obj["quality_checkpoints"]["escopo_unidade_observacional"]["status"] == "PENDENTE"
    assert obj["coorte_definida_independentemente"] is False
    assert obj["apto_analise_ou_publicacao"] is False
    assert obj["roadmap_quality_gate_alterado"] is False
    assert "PRIVATE_SYNTHETIC_DOSSIER" not in out.read_text(encoding="utf-8")
    if os.name != "nt":
        assert out.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        protocol.preparar_plano_qualidade_dengue_local(
            checklist, dictionary, dossier, out
        )


def test_wrong_dossier_digest_fails_closed(tmp_path, monkeypatch):
    checklist, dictionary, dossier, source = _synthetic(tmp_path, monkeypatch)
    source["zip_sha256_local"] = "d" * 64
    out = tmp_path / "plan.json"
    with pytest.raises(ValueError, match="conciliados"):
        protocol.preparar_plano_qualidade_dengue_local(
            checklist, dictionary, dossier, out
        )
    assert not out.exists()


def test_unlinked_source_or_nonpending_quality_fails(tmp_path, monkeypatch):
    checklist, dictionary, dossier, source = _synthetic(tmp_path, monkeypatch)
    obj = json.loads(checklist.read_text(encoding="utf-8"))
    obj["gates"]["fonte_agravo_ano"]["evidencia_sha256_local"] = "f" * 64
    checklist.write_text(json.dumps(obj), encoding="utf-8")
    with pytest.raises(ValueError, match="dois pareceres"):
        protocol.preparar_plano_qualidade_dengue_local(
            checklist, dictionary, dossier, tmp_path / "plan.json"
        )
    obj["gates"]["fonte_agravo_ano"]["evidencia_sha256_local"] = hashlib.sha256(
        b"PRIVATE_SYNTHETIC_DOSSIER_METADATA_NOT_PATIENTS"
    ).hexdigest()
    obj["gates"]["qualidade_coorte"] = {
        "situacao": "EVIDENCIA_LOCAL_NAO_VALIDADA",
        "evidencia_sha256_local": "d" * 64,
    }
    checklist.write_text(json.dumps(obj), encoding="utf-8")
    with pytest.raises(ValueError, match="nao esta pendente"):
        protocol.preparar_plano_qualidade_dengue_local(
            checklist, dictionary, dossier, tmp_path / "plan.json"
        )


def test_wrong_directory_fails(tmp_path, monkeypatch):
    checklist, dictionary, dossier, _ = _synthetic(tmp_path, monkeypatch)
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(ValueError, match="mesma pasta privada"):
        protocol.preparar_plano_qualidade_dengue_local(
            checklist, dictionary, dossier, outside / "plan.json"
        )


def test_help_exposes_metadata_only_quality_plan():
    call = subprocess.run(
        [sys.executable, "-m", "sinan_mcp",
         "preparar-plano-qualidade-dengue", "--help"],
        capture_output=True, text=True, timeout=20,
    )
    assert call.returncode == 0, call.stderr
    assert "--checklist" in call.stdout
    assert "--parecer-esquema" in call.stdout
    assert "--dossie-fonte" in call.stdout
    assert "--saida" in call.stdout
