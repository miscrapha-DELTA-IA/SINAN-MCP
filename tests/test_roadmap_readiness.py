"""Synthetic, fail-closed readiness gates for referenced SINAN diseases."""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from sinan_mcp import roadmap_readiness as rd

DENG = "4cf2f7b8-9920-41b5-817a-1ffc13e0690c"


def test_template_is_private_pending_and_never_authorizes(tmp_path):
    out = tmp_path / "readiness.json"
    report = rd.preparar_checklist_local("DENG", 2024, out, resource_id=DENG)
    assert report["n_frentes_pendentes"] == len(rd.GATES) == 7
    assert report["publicacao_autorizada"] is False
    assert report["acesso_remoto_com_dados_reais_autorizado"] is False
    assert report["status"] == "BLOQUEADO_PARA_USO_REAL_E_PUBLICACAO"
    assert rd.diagnosticar_checklist_local(out) == report
    assert len(rd.load_checklist(out)["gates"]) == 7
    if os.name != "nt":
        assert out.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        rd.preparar_checklist_local("DENG", 2024, out, resource_id=DENG)


@pytest.mark.parametrize("agravo", sorted(rd.ALIASES))
def test_templates_allow_all_referenced_diseases_but_grant_none(agravo, tmp_path):
    result = rd.preparar_checklist_local(
        agravo, 2024, tmp_path / f"{agravo}.json"
    )
    assert result["agravo"] == agravo
    assert result["n_frentes_pendentes"] == len(rd.GATES)
    assert result["publicacao_autorizada"] is False


def test_unlisted_disease_and_forged_annual_resource_are_rejected(tmp_path):
    with pytest.raises(ValueError):
        rd.preparar_checklist_local("FAKE", 2024, tmp_path / "bad.json")
    with pytest.raises(ValueError):
        rd.preparar_checklist_local(
            "TUBE", 2024, tmp_path / "bad.json", resource_id=DENG
        )
    assert not (tmp_path / "bad.json").exists()


def test_local_evidence_only_requires_fingerprint_but_does_not_authenticate(tmp_path):
    p = tmp_path / "r.json"
    rd.preparar_checklist_local("DENG", 2024, p)
    d = rd.load_checklist(p)
    d["gates"]["dicionario_esquema"] = {
        "situacao": "EVIDENCIA_LOCAL_NAO_VALIDADA",
        "evidencia_sha256_local": "a" * 64,
    }
    d["gates"]["fonte_agravo_ano"] = {
        "situacao": "PARECER_EXTERNO_DECLARADO_NAO_AUTENTICADO",
        "evidencia_sha256_local": "b" * 64,
    }
    result = rd.avaliar_checklist(d)
    assert result["n_frentes_pendentes"] == 5
    assert result["n_frentes_com_evidencia_local_nao_validada"] == 1
    assert result["n_frentes_com_parecer_declarado_nao_autenticado"] == 1
    assert result["revisor_externo_autenticado_pelo_sistema"] is False
    assert result["conformidade_lgpd_certificada"] is False
    assert result["publicacao_autorizada"] is False


def test_even_all_fake_claimed_review_signatures_never_authorize(tmp_path):
    p = tmp_path / "r.json"
    rd.preparar_checklist_local("DENG", 2024, p)
    d = rd.load_checklist(p)
    for field in rd.GATES:
        d["gates"][field] = {
            "situacao": "PARECER_EXTERNO_DECLARADO_NAO_AUTENTICADO",
            "evidencia_sha256_local": "c" * 64,
        }
    result = rd.avaliar_checklist(d)
    assert result["n_frentes_pendentes"] == 0
    assert result["publicacao_autorizada"] is False
    assert result["status"] == "BLOQUEADO_PARA_USO_REAL_E_PUBLICACAO"


@pytest.mark.parametrize("tamper", [
    lambda obj: obj.update({"publicacao_autorizada": True}),
    lambda obj: obj.update({"revisao_institucional_independente": "APROVADO"}),
    lambda obj: obj.update({"pseudonym": "name"}),
    lambda obj: obj["gates"].pop("privacidade_composicao"),
    lambda obj: obj["gates"]["dicionario_esquema"].update({
        "situacao": "PARECER_EXTERNO_DECLARADO_NAO_AUTENTICADO",
        "evidencia_sha256_local": None,
    }),
    lambda obj: obj["gates"]["fonte_agravo_ano"].update({
        "situacao": "APROVADO"
    }),
    lambda obj: obj["gates"]["fonte_agravo_ano"].update({
        "situacao": ["PENDENTE"]
    }),
    lambda obj: obj["scope"].update({"ano_do_arquivo": 0}),
])
def test_rejects_approval_escalation_and_schema_tampering(tmp_path, tamper):
    p = tmp_path / "r.json"
    rd.preparar_checklist_local("DENG", 2024, p)
    value = rd.load_checklist(p)
    tamper(value)
    with pytest.raises(ValueError):
        rd.avaliar_checklist(value)


def test_duplicate_json_keys_are_rejected(tmp_path):
    p = tmp_path / "r.json"
    rd.preparar_checklist_local("DENG", 2024, p)
    text = p.read_text(encoding="utf-8")
    p.write_text(text[:-2] + ', "publicacao_autorizada": false}', encoding="utf-8")
    with pytest.raises(ValueError):
        rd.load_checklist(p)


def test_cli_commands_do_not_read_data_or_expose_sensitive_results(tmp_path):
    path = tmp_path / "manifest.json"
    cmd = [sys.executable, "-m", "sinan_mcp"]
    created = subprocess.run(
        cmd + ["preparar-checklist-roadmap",
               "--agravo", "TUBE", "--ano", "2024", "--saida", str(path)],
        capture_output=True, text=True, timeout=20,
    )
    assert created.returncode == 0, created.stderr
    assert path.exists()
    assert "BLOQUEADO" in created.stdout
    diag = subprocess.run(
        cmd + ["diagnosticar-checklist-roadmap", "--arquivo", str(path)],
        capture_output=True, text=True, timeout=20,
    )
    assert diag.returncode == 0, diag.stderr
    assert "BLOQUEADO_PARA_USO_REAL_E_PUBLICACAO" in diag.stdout
    assert "Frentes pendentes: 7 de 7" in diag.stdout
    assert "paciente" not in (created.stdout + diag.stdout).lower()
