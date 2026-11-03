"""Synthetic-only tests for 2024-era PDF structural crosswalk.

Never download real SINAN data or include any real patient samples.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pymupdf = pytest.importorskip("pymupdf")
pytest.importorskip("reportlab")
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import Table
from reportlab.pdfgen import canvas

from sinan_mcp.local_dengue_dictionary_crosswalk import (
    _table_rows, _only_documented_crosswalk, _pdf_local_hash,
    examinar_pdf_dengue_local, _hipoteses_documentais_de_escopo,
)


def _pdf_with_table(path: Path):
    width, height = landscape(A4)
    c = canvas.Canvas(str(path), pagesize=(width, height))
    content = [
        ["Seq.", "Nome do Campo", "Campo", "Tipo", "Categoria", "Descrição", "Características"],
        ["1", "Tipo de notificação", "tp_not", "char(1)", "1-Sim", "Tipo", "Obrigatório"],
        ["2", "Raça/Cor", "cs_raca", "char(1)", "1-Branca", "Raça", "Essencial"],
        ["3", "Hospitalização", "hospitaliz", "char(1)", "1-Sim", "Hospitalização", "Essencial"],
    ]
    tab = Table(content, colWidths=[45, 140, 105, 70, 105, 150, 150], rowHeights=[35, 50, 60, 50])
    tab.setStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ])
    w, h = tab.wrap(width, height)
    tab.drawOn(c, 40, height - h - 40)
    c.save()
    return path


def test_extract_synthetic_seven_column_document(tmp_path):
    path = _pdf_with_table(tmp_path / "synthetic.pdf")
    with pymupdf.open(str(path)) as doc:
        result = _table_rows(doc)
    assert [r["seq"] for r in result] == [1, 2, 3]
    assert [r["name"] for r in result] == ["tp_not", "cs_raca", "hospitaliz"]
    assert all(r["pdf_page_1_based"] == 1 for r in result)
    assert result[1]["type_as_printed"] == "char(1)"


def test_header_names_are_never_listed_if_not_in_public_documents():
    out = _only_documented_crosswalk(
        {"TP_NOT", "ID_AGRAVO", "CS_RACA"},
        {"ID_AGRAVO", "DT_INVEST", "CLINIC_CHIK"},
        {"TP_NOT", "CS_RACA", "EVIL_SECRET_HEADER", "OTHER_UNKNOWN"},
    )
    assert out["nome_comum_pdf_atual_csv"] == 2
    assert out["quantidade_csv_fora_pdf_atual"] == 2
    assert out["nomes_pdf_atual_ausentes_csv"] == ["ID_AGRAVO"]
    assert out["nomes_pdf2015_ausentes_pdf_atual"] == [
        "CLINIC_CHIK", "DT_INVEST",
    ]
    assert "EVIL_SECRET_HEADER" not in str(out)
    assert "OTHER_UNKNOWN" not in str(out)


def test_rejects_unpinned_pdf_even_with_right_name(tmp_path):
    pdf = _pdf_with_table(tmp_path / "dic_dados_dengue.pdf")
    with pytest.raises(ValueError, match="Hash"):
        examinar_pdf_dengue_local(pdf)


def test_pdf_symlink_rejected(tmp_path):
    pdf = _pdf_with_table(tmp_path / "dic_dados_dengue.pdf")
    link = tmp_path / "alias.pdf"
    try:
        link.symlink_to(pdf)
    except (OSError, NotImplementedError):
        pytest.skip("OS não permite link simbólico")
    with pytest.raises(ValueError):
        _pdf_local_hash(link)


def test_cli_help_available_without_pdf_dependency():
    # The global CLI lazy-loads its PDF dependencies so normal MCP queries
    # are not affected by the optional PDF audit feature.
    import subprocess
    import sys
    p = subprocess.run(
        [sys.executable, "-m", "sinan_mcp",
         "confrontar-dicionario-dengue-2024", "--help"],
        text=True, capture_output=True, timeout=20,
    )
    assert p.returncode == 0, p.stderr
    assert "--contrato-2015" in p.stdout
    assert "--parecer-pendente" in p.stdout


def test_clinic_chik_absence_is_only_a_hypothesis_not_an_exemption():
    result = _hipoteses_documentais_de_escopo(
        {"CLINIC_CHIK", "CS_RACA"}, {"CS_RACA"}
    )
    assert len(result) == 1
    assert result[0]["campo_documentado"] == "CLINIC_CHIK"
    assert result[0]["pagina_pdf"] == 13
    assert result[0]["sequencia_documental"] == 73
    assert result[0]["escopo_condicional_documentado"] == "Chikungunya"
    assert result[0]["motivo_da_ausencia_no_csv"] == "NAO_DETERMINADO"
    assert result[0]["dispensa_justificada"] is False
    assert result[0]["validacao_independente"] == "PENDENTE"


def test_no_scope_assumption_when_clinic_chik_is_present():
    assert _hipoteses_documentais_de_escopo(
        {"CLINIC_CHIK", "CS_RACA"}, {"CLINIC_CHIK", "CS_RACA"}
    ) == []


def test_no_scope_assumption_for_other_missing_and_never_echo_unknown_csv_names():
    result = _hipoteses_documentais_de_escopo(
        {"CS_RACA", "HOSPITAL"}, {"CS_RACA", "UNKNOWN_HEADER_99"}
    )
    assert result == []
    # The same unknown header must never be included in the public-document
    # hypothesis, and the existing private crosswalk still only counts extras.
    crosswalk = _only_documented_crosswalk(
        {"CS_RACA", "HOSPITAL"}, {"HOSPITAL"},
        {"CS_RACA", "UNKNOWN_HEADER_99"},
    )
    assert crosswalk["quantidade_csv_fora_pdf_atual"] == 1
    assert "UNKNOWN_HEADER_99" not in str(crosswalk)
