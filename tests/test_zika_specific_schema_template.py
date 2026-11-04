"""Zika 2024: strictly synthetic, Zika-specific candidate template tests.

Never use actual ZIKABR24 data. No network, clinical records or official
checksum verification is performed; PDF fixtures are intentionally fake.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys

import pytest

from sinan_mcp.local_schema_review import (
    _prepare_template_dict, comparar_esquema_local, preparar_modelo_local,
    validate_candidate,
)
from sinan_mcp.zika_official_dictionary_reference import (
    VISIBLE_FIELD_EXAMPLES, PDF_URL,
)

ZIKA_JSON_ID = "264978ca-f795-4940-b5d3-ebc21e7d1c7c"
ZIKA_PARQUET_ID = "41bfda2a-5826-4ef9-8913-497247e6c9ce"
DENG_JSON_ID = "28975ef7-da35-498e-b179-cfbde2150f90"


def fake_pdf(tmp_path, name="dic_dados_zika.pdf"):
    file = tmp_path / name
    file.write_bytes(b"%PDF-1.4\n%FAKE-DOCUMENT-NO-SINAN-DATA\n%%EOF\n")
    return file


def test_zika_json_template_references_only_selected_zika_pdf_fields(tmp_path):
    pdf = fake_pdf(tmp_path)
    result = _prepare_template_dict(ZIKA_JSON_ID, pdf)
    expected = [
        {"name": name.upper(), "pdf_page_1_based": page}
        for name, page, _kind in VISIBLE_FIELD_EXAMPLES
    ]
    assert result["agravo"] == "ZIKA"
    assert result["ano_rotulado_no_portal"] == 2024
    assert result["format"] == "JSON"
    assert result["dictionary_url"] == PDF_URL
    assert result["campos_dbf"] == expected
    assert len(expected) == 9
    assert len(expected) < 37
    assert result["json_layout"] == "nao_determinado"
    assert result["cobertura"] == "excerto_parcial"
    assert result["situacao_transcricao"] == "manual_nao_revisada"
    assert {x["name"] for x in expected} >= {
        "TP_NOT", "ID_AGRAVO", "DT_NOTIFIC", "CS_RACA", "CLASSI_FIN",
        "DT_ENCERRA", "TP_SISTEMA"
    }
    assert "DT_INVEST" not in {x["name"] for x in expected}
    assert "ID_OCUPA_N" not in {x["name"] for x in expected}


def test_zika_template_created_exclusively_without_2024_archive(tmp_path):
    pdf = fake_pdf(tmp_path)
    dest = tmp_path / "zika-candidato-privado.json"
    report = preparar_modelo_local(ZIKA_JSON_ID, pdf, dest)
    candidate = json.loads(dest.read_text(encoding="utf-8"))
    assert report["arquivo_modelo_criado_localmente"] is True
    assert report["campos_exemplo_documentados"] == 9
    assert report["aprovado"] is False
    assert candidate["json_layout"] == "nao_determinado"
    assert candidate["pdf_sha256_local_observado"]
    assert len(candidate["pdf_sha256_local_observado"]) == 64
    assert not (tmp_path / "ZIKABR24.json.zip").exists()
    with pytest.raises(FileExistsError):
        preparar_modelo_local(ZIKA_JSON_ID, pdf, dest)


def test_unknown_zika_json_layout_blocks_zip_access_even_in_private_tool(tmp_path):
    pdf = fake_pdf(tmp_path)
    dest = tmp_path / "candidate.json"
    preparar_modelo_local(ZIKA_JSON_ID, pdf, dest)
    fake_zip = tmp_path / "ZIKABR24.json.zip"
    assert not fake_zip.exists()
    with pytest.raises(ValueError, match="Layout JSON ZIKA/2024 nao identificado"):
        comparar_esquema_local(ZIKA_JSON_ID, fake_zip, pdf, dest)
    assert not fake_zip.exists()


def test_operator_can_declare_json_topology_but_no_approval_is_granted(tmp_path):
    pdf = fake_pdf(tmp_path)
    candidate = _prepare_template_dict(ZIKA_JSON_ID, pdf)
    candidate["json_layout"] = "ndjson"
    assert validate_candidate(candidate)["situacao_transcricao"] == "manual_nao_revisada"
    candidate["json_layout"] = "array_of_objects"
    assert validate_candidate(candidate)["cobertura"] == "excerto_parcial"
    # Even with a manually selected topology, the comparison must reject
    # ZIKABR24 before reading any ZIP or clinical record.
    for chosen_layout in ("ndjson", "array_of_objects"):
        candidate["json_layout"] = chosen_layout
        contract = tmp_path / ("manual-" + chosen_layout + ".json")
        contract.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(ValueError, match="Comparacao ZIKABR24 bloqueada"):
            comparar_esquema_local(
                ZIKA_JSON_ID, tmp_path / "NO_CLINICAL_FILE.zip", pdf, contract
            )
        assert not (tmp_path / "NO_CLINICAL_FILE.zip").exists()
    candidate["situacao_transcricao"] = "aprovada"
    with pytest.raises(ValueError):
        validate_candidate(candidate)


def test_zika_parquet_not_mistaken_for_json_or_transcribed_schema(tmp_path):
    pdf = fake_pdf(tmp_path)
    with pytest.raises(ValueError, match="PARQUET"):
        _prepare_template_dict(ZIKA_PARQUET_ID, pdf)
    data = _prepare_template_dict(ZIKA_JSON_ID, pdf)
    altered = copy.deepcopy(data)
    altered["resource_id"] = ZIKA_PARQUET_ID
    altered["format"] = "PARQUET"
    with pytest.raises(ValueError, match="PARQUET"):
        validate_candidate(altered)


def test_unknown_layout_never_accepted_for_dengue_json(tmp_path):
    # Legacy document-specific examples for DENG remain unchanged.
    doc = fake_pdf(tmp_path, "DIC_DADOS_ONLINE.pdf")
    candidate = _prepare_template_dict(DENG_JSON_ID, doc)
    assert {field["name"] for field in candidate["campos_dbf"]} == {
        "ID_AGRAVO", "DT_INVEST", "ID_OCUPA_N"
    }
    candidate["json_layout"] = "nao_determinado"
    with pytest.raises(ValueError):
        validate_candidate(candidate)


def test_cli_template_zika_does_not_create_data_or_approve_research(tmp_path):
    pdf = fake_pdf(tmp_path)
    dest = tmp_path / "zika-private-candidate.json"
    run = subprocess.run([
        sys.executable, "-m", "sinan_mcp", "preparar-modelo-esquema",
        "--resource-id", ZIKA_JSON_ID,
        "--pdf", str(pdf), "--saida", str(dest),
    ], cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stderr
    assert "NAO" in run.stdout or "NÃO" in run.stdout
    doc = json.loads(dest.read_text(encoding="utf-8"))
    assert doc["agravo"] == "ZIKA"
    assert doc["json_layout"] == "nao_determinado"
    assert doc["situacao_transcricao"] == "manual_nao_revisada"
    assert len(doc["campos_dbf"]) == 9
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "sinan.sqlite3").exists()
