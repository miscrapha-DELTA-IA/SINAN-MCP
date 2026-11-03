"""Only synthetic PDF fixtures; no download or clinical records."""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

fitz = pytest.importorskip("fitz")
pytest.importorskip("reportlab")
from reportlab.pdfgen import canvas

from sinan_mcp.local_pdf_dictionary_candidate import (
    _scan_official_pdf_draft, gerar_rascunho_pdf_dbf_local,
)
from sinan_mcp.local_schema_review import load_candidate
from sinan_mcp.year_evidence_registry import consultar_evidencia_agravo_ano

DENG = "4cf2f7b8-9920-41b5-817a-1ffc13e0690c"
CHIK = "74c005e0-e1b8-4db0-997d-8c80b2d37f8a"


def _fake_pdf(tmp_path, *, anchored=True, extra_pages=0, corrupt=False):
    name = consultar_evidencia_agravo_ano(
        "DENG", 2024
    )["evidencia_documental"]["documento_url"].rsplit("/", 1)[-1]
    path = tmp_path / name
    if corrupt:
        path.write_bytes(b"%PDF-NOT-A-VALID-DOCUMENT")
        return path
    c = canvas.Canvas(str(path), pagesize=(842, 595))
    c.drawString(180, 500, "Synthetic test. No real ministry document.")
    c.showPage()
    words = ["ID_AGRAVO", "DT_INVEST", "ID_OCUPA_N", "FEBRE", "DOR_COSTAS",
             "PETÉQUIA_N"] if anchored else ["VALOR_DESCONHECIDO", "FEBRE"]
    for idx, field in enumerate(words):
        c.drawString(720, 490 - idx * 48, field)
    # Unrelated capitalized text in the left-hand narrative column must not
    # be mistaken for a DBF field.
    c.drawString(100, 455, "PII_SECRET_FIELD")
    c.showPage()
    for _ in range(extra_pages):
        c.drawString(720, 400, "LEUCOPENIA")
        c.showPage()
    c.save()
    return path


def test_offline_candidate_from_pdf_geometry(tmp_path):
    pdf = _fake_pdf(tmp_path)
    fields, stats = _scan_official_pdf_draft(pdf)
    names = {x["name"] for x in fields}
    assert names == {"ID_AGRAVO", "DT_INVEST", "ID_OCUPA_N", "FEBRE", "DOR_COSTAS"}
    assert stats["quantidade_palavras_ambiguidade_ou_acento"] == 1
    assert "PII_SECRET_FIELD" not in names
    assert set(x["pdf_page_1_based"] for x in fields) == {2}


def test_generated_candidate_is_local_unreviewed_and_never_overwrites(tmp_path):
    pdf = _fake_pdf(tmp_path)
    dest = tmp_path / "candidate-private.json"
    result = gerar_rascunho_pdf_dbf_local(DENG, pdf, dest)
    assert result["campos_candidatos_extraidos"] == 5
    assert result["campos_ancora_localizados"] == 3
    assert result["nomes_ambiguos_nao_normalizados"] == 1
    assert result["dicionario_aplicavel_2024_confirmado"] is False
    assert result["dados_reais_lidos"] is False
    assert result["publicacao_autorizada"] is False
    assert result["transcricao_verificada_independentemente"] is False
    obj = load_candidate(dest)
    assert obj["cobertura"] == "excerto_parcial"
    assert obj["situacao_transcricao"] == "manual_nao_revisada"
    assert obj["ano_rotulado_no_portal"] == 2024
    assert len(obj["campos_dbf"]) == 5
    if os.name != "nt":
        assert dest.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        gerar_rascunho_pdf_dbf_local(DENG, pdf, dest)
    assert "PII_SECRET_FIELD" not in dest.read_text(encoding="utf-8")


def test_chik_uses_same_document_profile_with_different_resource(tmp_path):
    pdf = _fake_pdf(tmp_path)
    dest = tmp_path / "chik-private.json"
    result = gerar_rascunho_pdf_dbf_local(CHIK, pdf, dest)
    assert result["agravo"] == "CHIK"
    assert load_candidate(dest)["format"] == "JSON"
    assert load_candidate(dest)["json_layout"] == "array_of_objects"
    assert not result["publicacao_autorizada"]


def test_pdf_missing_anchors_fails_closed_without_creating_file(tmp_path):
    pdf = _fake_pdf(tmp_path, anchored=False)
    out = tmp_path / "invalid.json"
    with pytest.raises(ValueError, match="Ancoragem"):
        gerar_rascunho_pdf_dbf_local(DENG, pdf, out)
    assert not out.exists()


def test_corrupt_pdf_is_rejected_without_echoing_bytes(tmp_path):
    pdf = _fake_pdf(tmp_path, corrupt=True)
    out = tmp_path / "invalid.json"
    with pytest.raises(ValueError):
        gerar_rascunho_pdf_dbf_local(DENG, pdf, out)
    assert not out.exists()


def test_missing_resource_and_path_safety(tmp_path):
    pdf = _fake_pdf(tmp_path)
    with pytest.raises(ValueError):
        gerar_rascunho_pdf_dbf_local("00000000-0000-0000-0000-000000000000",
                                    pdf, tmp_path / "invalid.json")
    if hasattr(os, "symlink"):
        link = tmp_path / "link.pdf"
        try:
            link.symlink_to(pdf)
        except (NotImplementedError, OSError):
            pass
        else:
            with pytest.raises(ValueError):
                _scan_official_pdf_draft(link)


def test_cli_runs_without_data_and_keeps_private_names_off_stdout(tmp_path):
    pdf = _fake_pdf(tmp_path)
    dest = tmp_path / "candidate.json"
    p = subprocess.run(
        [sys.executable, "-m", "sinan_mcp", "rascunhar-campos-dbf-pdf",
         "--resource-id", DENG, "--pdf", str(pdf), "--saida", str(dest)],
        capture_output=True, text=True, timeout=20, cwd=tmp_path,
    )
    assert p.returncode == 0, p.stderr
    assert dest.exists()
    assert "CANDIDATO DBF" in p.stdout
    assert "DICIONÁRIO 2024 NÃO VALIDADO" in p.stdout
    assert "ID_AGRAVO" not in p.stdout
    assert "PII_SECRET_FIELD" not in p.stdout
    assert not (tmp_path / "data").exists()


def test_inappropriate_extra_pages_rejected(tmp_path):
    pdf = _fake_pdf(tmp_path, extra_pages=45)
    with pytest.raises(ValueError, match="número de páginas"):
        _scan_official_pdf_draft(pdf)
