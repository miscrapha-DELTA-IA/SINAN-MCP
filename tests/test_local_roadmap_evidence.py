"""Synthetic-only tests for binding private DENG/2024 audit evidence to checklist."""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from sinan_mcp.roadmap_readiness import preparar_checklist_local, diagnosticar_checklist_local
from sinan_mcp.local_roadmap_evidence import (
    _private_crosswalk_digest, vincular_parecer_dengue_checklist_local,
)

RESOURCE = "4cf2f7b8-9920-41b5-817a-1ffc13e0690c"


def _fake(tmp_path):
    old = tmp_path / "roadmap-DENG-2024.json"
    preparar_checklist_local("DENG", 2024, old, RESOURCE)
    audit = tmp_path / "parecer-pendente-dengue-crosswalk-2024.json"
    report = {
        "schema_version": "sinan-private-dengue-crosswalk-candidate-v1",
        "resource_id": RESOURCE,
        "agravo": "DENG",
        "ano_rotulado_no_portal": 2024,
        "status_revisao": "PENDENTE",
        "publicacao_autorizada": False,
        "autorizacao_analise_real": False,
        "dicionario_aplicavel_a_exportacao_2024_validado": False,
        "dominios_categoricos_verificados": False,
        "linhas_de_pacientes_lidas": 0,
        "campos_csv_desconhecidos_incluidos_no_parecer": False,
        "pdf_atual_sha256_local": "a" * 64,
        "zip_sha256_local": "b" * 64,
        "pdf2015_sha256_local": "c" * 64,
        "n_campos_csv": 121,
        "n_nomes_unicos_pdf_atual": 120,
        "nome_comum_pdf_atual_csv": 119,
        "quantidade_csv_fora_pdf_atual": 2,
        "nomes_pdf_atual_ausentes_csv": ["CLINIC_CHIK"],
    }
    audit.write_text(json.dumps(report), encoding="utf-8")
    return old, audit


def test_attach_only_pending_document_evidence(tmp_path):
    old, audit = _fake(tmp_path)
    new = tmp_path / "roadmap-DENG-2024-evidencia-local.json"
    summary = vincular_parecer_dengue_checklist_local(old, audit, new)
    assert summary["n_frentes_pendentes"] == 6
    assert summary["n_frentes_com_evidencia_local_nao_validada"] == 1
    assert summary["publicacao_autorizada"] is False
    assert summary["acesso_remoto_com_dados_reais_autorizado"] is False
    original = diagnosticar_checklist_local(old)
    assert original["n_frentes_pendentes"] == 7
    updated = diagnosticar_checklist_local(new)
    assert updated["status"] == "BLOQUEADO_PARA_USO_REAL_E_PUBLICACAO"
    assert updated["n_frentes_com_evidencia_local_nao_validada"] == 1
    doc = json.loads(new.read_text(encoding="utf-8"))
    assert doc["gates"]["dicionario_esquema"]["evidencia_sha256_local"] == _private_crosswalk_digest(audit)
    assert doc["gates"]["dicionario_esquema"]["situacao"] == "EVIDENCIA_LOCAL_NAO_VALIDADA"
    assert doc["publicacao_autorizada"] is False
    assert "CLINIC_CHIK" not in new.read_text(encoding="utf-8")
    assert "CLINC_CHIK" not in new.read_text(encoding="utf-8")
    if os.name != "nt":
        assert new.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        vincular_parecer_dengue_checklist_local(old, audit, new)


@pytest.mark.parametrize("changes", [
    {"publicacao_autorizada": True},
    {"status_revisao": "APROVADO"},
    {"autorizacao_analise_real": True},
    {"dicionario_aplicavel_a_exportacao_2024_validado": True},
    {"dominios_categoricos_verificados": True},
    {"linhas_de_pacientes_lidas": 2},
    {"campos_csv_desconhecidos_incluidos_no_parecer": True},
    {"agravo": "TUBE"},
    {"ano_rotulado_no_portal": 2023},
    {"zip_sha256_local": "INVALID"},
    {"nome_comum_pdf_atual_csv": 118},
    {"quantidade_csv_fora_pdf_atual": 3},
])
def test_fails_closed_on_bad_crosswalk(tmp_path, changes):
    old, audit = _fake(tmp_path)
    doc = json.loads(audit.read_text(encoding="utf-8"))
    doc.update(changes)
    audit.write_text(json.dumps(doc), encoding="utf-8")
    out = tmp_path / "new.json"
    with pytest.raises(ValueError):
        vincular_parecer_dengue_checklist_local(old, audit, out)
    assert not out.exists()


def test_duplicate_keys_are_rejected(tmp_path):
    old, audit = _fake(tmp_path)
    raw = audit.read_text(encoding="utf-8")
    audit.write_text(raw[:-1] + ',"publicacao_autorizada":false}', encoding="utf-8")
    with pytest.raises(ValueError):
        vincular_parecer_dengue_checklist_local(old, audit, tmp_path / "new.json")


def test_wrong_scope_or_directories_rejected(tmp_path):
    old, audit = _fake(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(ValueError, match="mesma pasta"):
        vincular_parecer_dengue_checklist_local(old, audit, other / "new.json")
    original = json.loads(old.read_text(encoding="utf-8"))
    original["scope"]["agravo"] = "TUBE"
    original["scope"]["resource_id"] = None
    old.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises(ValueError, match="recurso DENG"):
        vincular_parecer_dengue_checklist_local(old, audit, tmp_path / "not-created.json")


def test_cli_stays_metadata_only(tmp_path):
    old, audit = _fake(tmp_path)
    out = tmp_path / "new.json"
    process = subprocess.run([
        sys.executable, "-m", "sinan_mcp",
        "vincular-evidencia-dengue-roadmap",
        "--checklist", str(old),
        "--parecer-esquema", str(audit),
        "--saida", str(out),
    ], capture_output=True, text=True, timeout=20)
    assert process.returncode == 0, process.stderr
    assert "Frentes sem evidencia: 6" in process.stdout
    assert "Frentes com evidencia nao validada: 1" in process.stdout
    assert "Publicacao autorizada: NAO" in process.stdout
    assert "CLINIC_CHIK" not in (process.stdout + process.stderr)
    assert out.exists()
