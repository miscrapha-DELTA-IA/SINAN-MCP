"""Synthetic private spelling audit: no SINAN records, real PDF or live CSV."""
from __future__ import annotations
import json
import os
import subprocess
import sys
import pytest

from sinan_mcp import local_dengue_spelling_review as module

A = "a" * 64
B = "b" * 64


def _metadata(monkeypatch):
    monkeypatch.setattr(module, "examinar_pdf_dengue_local", lambda _: {
        "pdf_sha256_local": A,
        "nomes_documentais": {"CLINIC_CHIK", "SG_UF"},
    })
    monkeypatch.setattr(module, "_load_previous_crosswalk", lambda _: {
        "pdf_atual_sha256_local": A,
        "zip_sha256_local": B,
        "nomes_pdf_atual_ausentes_csv": ["CLINIC_CHIK"],
        "quantidade_csv_fora_pdf_atual": 2,
    })
    monkeypatch.setattr(module, "_load_sidecar", lambda _: {
        "pdf_sha256_local": A,
        "zip_sha256_local": B,
        "nomes_adicionais_csv_nao_documentados_no_pdf": ["CLINC_CHIK", "UF"],
    })


def test_name_only_reconciliation_requires_human_review(tmp_path, monkeypatch):
    _metadata(monkeypatch)
    out = tmp_path / "private.json"
    summary = module.gerar_hipoteses_grafia_dengue_local(
        "pdf", "prior", "extras", out,
    )
    assert summary["extras_avaliados"] == 2
    assert summary["hipoteses_grafia"] == 1
    assert summary["sem_correspondencia"] == 1
    assert summary["nomes_no_terminal"] is False
    assert "CLINC_CHIK" not in str(summary)
    obj = json.loads(out.read_text(encoding="utf-8"))
    assert obj["hipoteses_de_grafia"][0]["nome_observado_csv"] == "CLINC_CHIK"
    assert obj["hipoteses_de_grafia"][0]["candidatos_nomes_pdf_publico"] == [
        "CLINIC_CHIK"
    ]
    assert obj["nomes_csv_sem_correspondencia_de_um_caractere"] == ["UF"]
    assert obj["equivalencia_semantica_verificada"] is False
    assert obj["alias_automatico_habilitado"] is False
    assert obj["publicacao_autorizada"] is False
    if os.name != "nt":
        assert out.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        module.gerar_hipoteses_grafia_dengue_local(
            "pdf", "prior", "extras", out,
        )


def test_file_hash_mismatch_blocks_sidecar(tmp_path, monkeypatch):
    _metadata(monkeypatch)
    monkeypatch.setattr(module, "_load_previous_crosswalk", lambda _: {
        "pdf_atual_sha256_local": A,
        "zip_sha256_local": "c" * 64,
        "nomes_pdf_atual_ausentes_csv": ["CLINIC_CHIK"],
        "quantidade_csv_fora_pdf_atual": 2,
    })
    out = tmp_path / "private.json"
    with pytest.raises(ValueError, match="correspondem"):
        module.gerar_hipoteses_grafia_dengue_local(
            "pdf", "prior", "extras", out,
        )
    assert not out.exists()


@pytest.mark.parametrize("left,right,expected", [
    ("CLINC_CHIK", "CLINIC_CHIK", True),
    ("UF", "SG_UF", False),
    ("CS_RACA", "CS_RACA", False),
    ("CS_RACA", "CS_SEXO", False),
    ("XYZ", "XYZA", False),
])
def test_bounded_typographic_hypothesis(left, right, expected):
    assert module._exactly_one_insert_or_delete(left, right) is expected


def test_private_sidecar_rejects_duplicate_and_unsafe_names(tmp_path):
    p = tmp_path / "s.json"
    fields = {
        "schema_version": module.PRIVATE_SCHEMA,
        "resource_id": module.RESOURCE_ID,
        "publicacao_autorizada": False,
        "nomes_publicaveis": False,
        "revisao_independente": "PENDENTE",
        "n_linhas_clinicas_lidas": 0,
        "nomes_adicionais_csv_nao_documentados_no_pdf": ["CLINC_CHIK", "UF"],
        "quantidade": 2,
        "pdf_sha256_local": A,
        "zip_sha256_local": B,
    }
    p.write_text(json.dumps(fields), encoding="utf-8")
    assert module._load_sidecar(p)["quantidade"] == 2
    fields["nomes_adicionais_csv_nao_documentados_no_pdf"] = ["UF", "UF"]
    p.write_text(json.dumps(fields), encoding="utf-8")
    with pytest.raises(ValueError):
        module._load_sidecar(p)
    p.write_text(json.dumps(fields)[:-1] + ',"quantidade":2}', encoding="utf-8")
    with pytest.raises(ValueError):
        module._load_sidecar(p)


def test_cli_help_available_without_any_real_data():
    process = subprocess.run(
        [sys.executable, "-m", "sinan_mcp",
         "conferir-hipoteses-grafia-dengue", "--help"],
        capture_output=True, text=True, timeout=20,
    )
    assert process.returncode == 0, process.stderr
    assert "--extras-privados" in process.stdout
    assert "--saida-privada" in process.stdout
