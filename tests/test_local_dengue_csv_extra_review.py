"""Purely synthetic test of opt-in private review for unknown CSV HEADER names."""
from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

import sinan_mcp.local_dengue_csv_extra_review as private
from sinan_mcp.local_dengue_dictionary_crosswalk import RESOURCE_ID

A = "a" * 64
B = "b" * 64
C = "c" * 64


def _synthetic(tmp_path, monkeypatch):
    pdf = tmp_path / "dic_dados_dengue.pdf"
    pdf.write_bytes(b"%PDF-local-synthetic")
    old = tmp_path / "old.json"
    old.write_text("{}", encoding="utf-8")
    zip_path = tmp_path / "DENGBR24.csv.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as arc:
        arc.writestr(
            "DENGBR24.csv",
            "A_FIELD,EXTRA_ONE,EXTRA_TWO\n"
            "fake_patient_value,NEVER_READ_THESE_RECORDS,NEVER_READ\n",
        )
    prior = tmp_path / "prior.json"
    prior.write_text(json.dumps({
        "schema_version": "sinan-private-dengue-crosswalk-candidate-v1",
        "resource_id": RESOURCE_ID,
        "status_revisao": "PENDENTE",
        "autorizacao_analise_real": False,
        "publicacao_autorizada": False,
        "pdf_atual_sha256_local": A,
        "pdf2015_sha256_local": B,
        "zip_sha256_local": C,
        "n_campos_csv": 3,
        "nome_comum_pdf_atual_csv": 1,
        "quantidade_csv_fora_pdf_atual": 2,
        "nomes_pdf_atual_ausentes_csv": ["CLINIC_CHIK"],
    }), encoding="utf-8")
    monkeypatch.setattr(private, "examinar_pdf_dengue_local",
                        lambda path: {
                            "nomes_documentais": {"A_FIELD", "CLINIC_CHIK"},
                            "pdf_sha256_local": A,
                        })
    monkeypatch.setattr(private, "load_candidate",
                        lambda path: {
                            "resource_id": RESOURCE_ID, "format": "CSV",
                            "pdf_sha256_local_observado": B,
                            "csv_encoding": "utf-8-sig", "csv_delimiter": ",",
                        })
    monkeypatch.setattr(private, "conferir_zip_recurso_local",
                        lambda resource, path: {
                            "arquivo_pacote_sha256_local": C,
                        })
    monkeypatch.setattr(private, "_resource",
                        lambda resource: {
                            "archive_filename": "DENGBR24.csv.zip",
                        })
    return pdf, old, zip_path, prior


def test_private_sidecar_contains_names_but_summary_never_does(
    tmp_path, monkeypatch,
):
    pdf, old, zip_path, prior = _synthetic(tmp_path, monkeypatch)
    dst = tmp_path / "private-headers.json"
    output = private.gerar_revisao_privada_cabecalhos_dengue(
        pdf, old, zip_path, prior, dst
    )
    assert output["quantidade"] == 2
    assert output["revisao"] == "PENDENTE"
    assert output["dados_clinicos_lidos"] is False
    assert output["nomes_exibidos_no_terminal"] is False
    assert "EXTRA_ONE" not in str(output)
    assert "EXTRA_TWO" not in str(output)
    text = dst.read_text(encoding="utf-8")
    obj = json.loads(text)
    assert obj["nomes_adicionais_csv_nao_documentados_no_pdf"] == [
        "EXTRA_ONE", "EXTRA_TWO",
    ]
    assert obj["publicacao_autorizada"] is False
    assert obj["n_linhas_clinicas_lidas"] == 0
    assert "fake_patient_value" not in text
    assert "NEVER_READ_THESE_RECORDS" not in text
    if __import__("os").name != "nt":
        assert dst.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        private.gerar_revisao_privada_cabecalhos_dengue(
            pdf, old, zip_path, prior, dst,
        )


def test_prior_report_tied_to_both_documents_and_zip(tmp_path, monkeypatch):
    pdf, old, zip_path, prior = _synthetic(tmp_path, monkeypatch)
    obj = json.loads(prior.read_text(encoding="utf-8"))
    obj["zip_sha256_local"] = "bad"
    prior.write_text(json.dumps(obj), encoding="utf-8")
    with pytest.raises(ValueError, match="outro ZIP"):
        private.gerar_revisao_privada_cabecalhos_dengue(
            pdf, old, zip_path, prior, tmp_path / "no.json"
        )
    assert not (tmp_path / "no.json").exists()


def test_reject_report_with_unapproved_release_and_duplicate_keys(
    tmp_path, monkeypatch,
):
    pdf, old, zip_path, prior = _synthetic(tmp_path, monkeypatch)
    txt = prior.read_text(encoding="utf-8")
    obj = json.loads(txt)
    obj["publicacao_autorizada"] = True
    prior.write_text(json.dumps(obj), encoding="utf-8")
    with pytest.raises(ValueError, match="escopo local"):
        private.gerar_revisao_privada_cabecalhos_dengue(
            pdf, old, zip_path, prior, tmp_path / "no.json"
        )
    prior.write_text(txt[:-1] + ',"n_campos_csv":3}', encoding="utf-8")
    with pytest.raises(ValueError, match="repetida"):
        private._load_previous_crosswalk(prior)


def test_new_cli_help_is_available_without_live_data():
    import subprocess
    import sys
    p = subprocess.run(
        [sys.executable, "-m", "sinan_mcp",
         "preparar-revisao-local-extras-dengue", "--help"],
        capture_output=True, text=True, timeout=20,
    )
    assert p.returncode == 0, p.stderr
    assert "--parecer-anterior" in p.stdout
    assert "--saida-privada" in p.stdout
