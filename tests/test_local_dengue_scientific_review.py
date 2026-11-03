"""Private DENG/2024 scientific review requests; no clinical data, no release."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from sinan_mcp import local_dengue_scientific_review as review
from sinan_mcp import synthetic_dengue_csv_audit as synth


def _synthetic_plan(p: Path) -> None:
    content = {
        "schema_version": synth.PLAN_SCHEMA,
        "scope": {
            "agravo": "DENG", "ano_do_arquivo": 2024,
            "resource_id": review.RESOURCE_ID,
        },
        "parecer_esquema_sha256_local": "a" * 64,
        "dossie_fonte_sha256_local": "b" * 64,
        "zip_sha256_local": "c" * 64,
        "quality_checkpoints": {
            key: {"status": "PENDENTE", "definicao_de_aceite": desc}
            for key, desc in synth.CHECKPOINTS.items()
        },
        "unidade_observacional": "NAO_DEFINIDA",
        "coorte_definida_independentemente": False,
        "revisao_clinica_independente": "PENDENTE",
        "data_cutoff_confirmada": False,
        "qualidade_dados_clinicos_auditada": False,
        "n_linhas_clinicas_lidas": 0,
        "indicadores_reais_calculados": False,
        "apto_analise_ou_publicacao": False,
        "roadmap_quality_gate_alterado": False,
        "status": "PLANO_PRIVADO_NAO_VALIDADO",
    }
    p.write_text(json.dumps(content), encoding="utf-8")


def _artifacts(tmp_path: Path) -> tuple[Path, Path, Path]:
    plan = tmp_path / "plano-qualidade-DENG-2024-privado.json"
    _synthetic_plan(plan)
    synthetic_report = tmp_path / "simulacao-qualidade-DENG-2024.json"
    synth.auditar_fixture_dengue_local(plan, synthetic_report)
    output = tmp_path / "pacote-revisao-cientifica-DENG-2024.json"
    return plan, synthetic_report, output


def test_packet_has_seven_pending_decisions_and_no_autoapproval(tmp_path):
    plan, simulation, out = _artifacts(tmp_path)
    got = review.preparar_pacote_revisao_dengue_local(plan, simulation, out)
    assert got == {
        "agravo": "DENG",
        "ano": 2024,
        "questoes_cientificas_pendentes": 7,
        "checkpoints_qualidade_pendentes": 9,
        "revisores_autenticados": 0,
        "dados_reais_lidos": 0,
        "uso_real_autorizado": False,
        "publicacao_autorizada": False,
        "status": "PEDIDO_DE_REVISAO_NAO_HOMOLOGADO",
    }
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["plano_qualidade_sha256_local"] == hashlib.sha256(
        plan.read_bytes()
    ).hexdigest()
    assert doc["simulacao_sintetica_sha256_local"] == hashlib.sha256(
        simulation.read_bytes()
    ).hexdigest()
    assert doc["zip_sha256_local"] == "c" * 64
    assert doc["revisores_autenticados"] == 0
    assert doc["qualidade_coorte_homologada"] is False
    assert doc["aliases_de_campos_aprovados"] is False
    assert doc["dominios_clinicos_validados"] is False
    assert all(item["situacao"] == "PENDENTE"
               for item in doc["questoes_para_revisao_independente"].values())
    assert "CLASSI_FIN" in doc["questoes_para_revisao_independente"]["classi_fin"]["questao"]
    assert review.diagnosticar_pacote_cientifico_local(out) == got
    assert "2024-01-15" not in out.read_text(encoding="utf-8")
    if os.name != "nt":
        assert out.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        review.preparar_pacote_revisao_dengue_local(plan, simulation, out)


def test_plan_changed_after_simulation_blocks_creation(tmp_path):
    plan, sim, out = _artifacts(tmp_path)
    plan.write_text(plan.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        review.preparar_pacote_revisao_dengue_local(plan, sim, out)
    assert not out.exists()


@pytest.mark.parametrize("tamper", [
    lambda d: d.update({"publicacao_autorizada": True}),
    lambda d: d.update({"qualidade_coorte_homologada": True}),
    lambda d: d.update({"registros_reais_lidos": 10}),
    lambda d: d.update({"checkpoints_cientificos_validados": 1}),
    lambda d: d.update({"origem_dados": "CSV_OFICIAL"}),
    lambda d: d["verificacoes_sinteticas"].update({"linhas_sinteticas": 100}),
    lambda d: d.update({"plano_privado_sha256_local": "f" * 64}),
])
def test_forged_simulation_is_rejected(tmp_path, tamper):
    plan, sim, out = _artifacts(tmp_path)
    doc = json.loads(sim.read_text(encoding="utf-8"))
    tamper(doc)
    sim.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ValueError):
        review.preparar_pacote_revisao_dengue_local(plan, sim, out)
    assert not out.exists()


@pytest.mark.parametrize("tamper", [
    lambda d: d.update({"publicacao_autorizada": True}),
    lambda d: d.update({"autorizacao_uso_real": True}),
    lambda d: d.update({"dominios_clinicos_validados": True}),
    lambda d: d.update({"aliases_de_campos_aprovados": True}),
    lambda d: d.update({"revisores_autenticados": 1}),
    lambda d: d.update({"qualidade_coorte_homologada": True}),
    lambda d: d.update({"checkpoints_qualidade_pendentes": 0}),
    lambda d: d.update({"status": "APROVADO"}),
    lambda d: d["scope"].update({"agravo": "TUBE"}),
    lambda d: d["questoes_para_revisao_independente"]["classi_fin"].update(
        {"situacao": "APROVADO"}
    ),
    lambda d: d["questoes_para_revisao_independente"].pop("uf"),
    lambda d: d.update({"field": "unexpected"}),
])
def test_attempted_scientific_approval_or_scope_escalation_is_refused(tmp_path, tamper):
    plan, sim, out = _artifacts(tmp_path)
    review.preparar_pacote_revisao_dengue_local(plan, sim, out)
    obj = json.loads(out.read_text(encoding="utf-8"))
    tamper(obj)
    out.write_text(json.dumps(obj), encoding="utf-8")
    with pytest.raises(ValueError):
        review.diagnosticar_pacote_cientifico_local(out)


def test_duplicate_keys_are_rejected_without_clinical_output(tmp_path):
    plan, sim, out = _artifacts(tmp_path)
    report = sim.read_text(encoding="utf-8")
    sim.write_text(
        report.rstrip()[:-1] + ',"publicacao_autorizada":false}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        review.preparar_pacote_revisao_dengue_local(plan, sim, out)
    assert not out.exists()


def test_cross_directory_and_symlink_to_simulation_denied(tmp_path):
    plan, sim, out = _artifacts(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    with pytest.raises(ValueError, match="mesma pasta"):
        review.preparar_pacote_revisao_dengue_local(plan, sim, elsewhere / "out.json")
    symlink = tmp_path / "symlink.json"
    try:
        symlink.symlink_to(sim)
    except (NotImplementedError, OSError):
        pytest.skip("Permissao para symlink indisponivel no Windows")
    with pytest.raises(ValueError):
        review.preparar_pacote_revisao_dengue_local(plan, symlink, out)


def test_cli_end_to_end_on_private_synthetic_metadata(tmp_path):
    plan, sim, out = _artifacts(tmp_path)
    cmd = [sys.executable, "-m", "sinan_mcp"]
    create = subprocess.run(
        cmd + [
            "preparar-pacote-revisao-cientifica-dengue",
            "--plano", str(plan),
            "--simulacao", str(sim),
            "--saida", str(out),
        ],
        capture_output=True, text=True, timeout=25,
    )
    assert create.returncode == 0, create.stderr
    assert "Questoes pendentes: 7" in create.stdout
    assert "Dados reais lidos: 0" in create.stdout
    assert out.exists()
    diagnostic = subprocess.run(
        cmd + [
            "diagnosticar-pacote-revisao-cientifica-dengue",
            "--arquivo", str(out),
        ],
        capture_output=True, text=True, timeout=25,
    )
    assert diagnostic.returncode == 0, diagnostic.stderr
    assert "Checkpoints de qualidade pendentes: 9" in diagnostic.stdout
    assert "Publicacao autorizada: NAO" in diagnostic.stdout
    assert "CLINC_CHIK" not in create.stdout + diagnostic.stdout
    assert "CLASSI_FIN" not in create.stdout + diagnostic.stdout
