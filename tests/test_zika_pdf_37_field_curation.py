"""Entirely offline checks for candidate 37-field Zika PDF transcription.

No ZIKABR24 JSON/Parquet ZIP, no patients, and no public MCP extension.
The expected sample and types are static documentary evidence, NOT a
validated annual import layout.
"""
from __future__ import annotations

import copy
import inspect
import subprocess
import sys

import pytest

from sinan_mcp import zika_pdf_37_field_curation as catalog
from sinan_mcp.zika_official_dictionary_reference import (
    PDF_URL, RESOURCE_ID, RESOURCE_URL, VISIBLE_FIELD_EXAMPLES,
)


def test_all_37_fields_present_numbered_pages_and_official_document():
    result = catalog.carregar_transcricao_zika_pdf()
    assert result["status"] == "TRANSCRICAO_PDF_COMPLETA_CANDIDATA_NAO_HOMOLOGADA"
    assert result["documentary_fields_transcribed"] == 37
    assert result["source_pdf_page_count"] == 8
    assert result["source_pdf"] == PDF_URL
    assert result["source_resource_page"] == RESOURCE_URL
    assert result["documentary_page_counts"] == {
        "1": 5, "2": 7, "3": 3, "4": 3,
        "5": 7, "6": 4, "7": 3, "8": 5,
    }
    assert len(result["local_catalog_sha256_not_official_pdf_hash"]) == 64
    rows = result["documentary_field_rows"]
    assert [r["seq"] for r in rows] == list(range(1, 38))
    assert len({r["campo"] for r in rows}) == 37
    for field in rows:
        assert field["validado_no_arquivo_2024"] is False


def test_existing_visually_checked_nine_fields_are_not_mutated():
    result = catalog.carregar_transcricao_zika_pdf()
    by_name = {r["campo"]: r for r in result["documentary_field_rows"]}
    assert set(by_name) == set(catalog.EXPECTED_FIELD_IDS)
    for name, page, kind in VISIBLE_FIELD_EXAMPLES:
        assert by_name[name]["pagina_pdf"] == page
        assert by_name[name]["tipo_documental"] == kind


def test_sensitive_semantics_require_review_not_auto_homologation():
    report = catalog.carregar_transcricao_zika_pdf()
    fields = {r["campo"]: r for r in report["documentary_field_rows"]}
    assert fields["nu_idade_n"]["tipo_documental"] == "num(4)"
    assert fields["nu_idade_n"]["dominio_descritor"] == (
        "idade_codificada_unidade_primeiro_digito"
    )
    assert fields["nduplic_n"]["codigos_citados"] == []
    assert fields["nduplic_n"]["dominio_descritor"] == "codigos_ambiguidade_pagina"
    assert fields["in_vincula"]["tipo_documental"] == "char(6)"
    assert fields["cs_escol_n"]["dominio_descritor"] == "codigos_heterogeneos_revisao"
    assert fields["classi_fin"]["codigos_citados"] == ["1", "2", "9"]
    assert fields["tp_sistema"]["codigos_citados"] == ["1", "2"]
    flagged = {x["campo"] for x in report["issues_requiring_independent_review"]}
    assert {"nu_idade_n", "nduplic_n", "cs_escol_n",
            "in_vincula", "tp_sistema"} <= flagged
    assert report["fields_in_actual_2024_file_read"] == 0
    assert report["annual_schema_2024_validated"] is False
    assert report["case_definitions_validated"] is False
    assert report["duplication_rules_approved"] is False
    assert report["documentary_second_reviewer_authenticated"] is False
    assert report["official_pdf_sha256_verified"] is False
    assert report["indicators_approved"] == 0
    assert report["publication_authorized"] is False


@pytest.mark.parametrize("change", [
    lambda x: x.update(year_2024_schema_compared=True),
    lambda x: x.update(publication_authorized=True),
    lambda x: x.update(documentary_second_reviewer_authenticated=True),
    lambda x: x.update(source_bytes_official_sha256_verified=True),
    lambda x: x.update(year_2024_data_accessed=True),
    lambda x: x.update(indicators_approved=1),
    lambda x: x.update(source_resource_id="264978ca-f795-4940-b5d3-ebc21e7d1c7c"),
    lambda x: x.update(source_pdf="https://bad.example.net/a.pdf"),
    lambda x: x["fields"].pop(),
    lambda x: x["fields"].append(copy.deepcopy(x["fields"][-1])),
    lambda x: x["fields"][0].update(seq=2),
    lambda x: x["fields"][0].update(campo="fake"),
    lambda x: x["fields"][0].update(tipo_documental="char(9)"),
    lambda x: x["fields"][0].update(pagina_pdf=3),
    lambda x: x["fields"][0].update(validado_no_arquivo_2024=True),
    lambda x: x["fields"][12].update(tipo_documental="char(4)"),
    lambda x: x["fields"][12].update(dominio_descritor="categorias_listadas"),
    lambda x: x["fields"][21].update(codigos_citados=["1", "2"]),
    lambda x: x["fields"][22].update(tipo_documental="char(1)"),
    lambda x: x["transcription_issues"].clear(),
    lambda x: x.update(unvalidated_public_data="patient"),
])
def test_catalogue_refuses_documentary_tampering_and_fake_validations(change):
    from sinan_mcp.zika_pdf_37_field_curation import validar_transcricao_zika_documental
    source = catalog.carregar_transcricao_zika_pdf()
    # Obtain source from packaged JSON, never external data or private files.
    from importlib.resources import files
    import json
    obj = json.loads(files("sinan_mcp").joinpath(
        "registry", catalog.FILE_NAME
    ).read_text(encoding="utf-8"))
    change(obj)
    with pytest.raises(ValueError):
        validar_transcricao_zika_documental(obj)
    assert source["publication_authorized"] is False


def test_duplicate_json_keys_fail_closed():
    with pytest.raises(ValueError, match="duplicada"):
        catalog._pairs_no_duplicates([
            ("campo", "cs_raca"), ("campo", "not_reliable")
        ])


def test_report_fields_are_copied_not_shared_mutable_state():
    a = catalog.carregar_transcricao_zika_pdf()
    a["documentary_field_rows"][0]["campo"] = "CORRUPTED"
    b = catalog.carregar_transcricao_zika_pdf()
    assert b["documentary_field_rows"][0]["campo"] == "tp_not"


def test_cli_summary_and_verbose_metadata_never_open_patients(tmp_path):
    command = [sys.executable, "-m", "sinan_mcp",
               "conferir-transcricao-zika-pdf"]
    summary = subprocess.run(command, cwd=tmp_path, text=True,
                             capture_output=True, timeout=30)
    assert summary.returncode == 0, summary.stderr
    assert "Campos documentais transcritos: 37" in summary.stdout
    assert "Paginas conferidas: 8" in summary.stdout
    assert "Campos reais ZIKABR24 lidos: 0" in summary.stdout
    assert "Compatibilidade com esquema 2024: NAO" in summary.stdout
    assert "Regras de duplicidade homologadas: NAO" in summary.stdout
    assert "Indicadores homologados: 0; publicacao autorizada: NAO" in summary.stdout
    verbose = subprocess.run(command + ["--detalhar"], cwd=tmp_path,
                             text=True, capture_output=True, timeout=30)
    assert verbose.returncode == 0, verbose.stderr
    assert "01 pagina 1: tp_not [char(1)]" in verbose.stdout
    assert "13 pagina 3: nu_idade_n [num(4)]" in verbose.stdout
    assert "22 pagina 5: nduplic_n [char(1)]" in verbose.stdout
    assert "37 pagina 8: tp_sistema [char(1)]" in verbose.stdout
    assert not (tmp_path / "sinan.sqlite3").exists()
    assert not (tmp_path / "ZIKABR24.json.zip").exists()
    assert not (tmp_path / "ZIKABR24.parquet.zip").exists()


def test_no_private_imports_or_public_server_changes():
    from sinan_mcp import public_server, local_schema_review
    module = inspect.getsource(catalog)
    for forbidden in ("import requests", "import sqlite3",
                      "import pysus", "urlopen(", "import subprocess",
                      "ZIKABR24.json.zip", "ZIKABR24.parquet.zip"):
        assert forbidden not in module
    assert "zika_pdf_37_field_curation" not in inspect.getsource(public_server)
    private = inspect.getsource(local_schema_review.comparar_esquema_local)
    assert "Comparacao ZIKABR24 bloqueada" in private
