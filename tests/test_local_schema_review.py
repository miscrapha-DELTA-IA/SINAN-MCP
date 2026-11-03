"""Regression tests: local-only field comparisons, no real SINAN records."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import zipfile

import pytest

from sinan_mcp.local_schema_review import (
    _prepare_template_dict, comparar_esquema_local, load_candidate,
    preparar_modelo_local, salvar_parecer_pendente_local, validate_candidate,
)
from sinan_mcp.official_annual_resources import _index
from sinan_mcp.year_evidence_registry import consultar_evidencia_agravo_ano

CSV_ID = "4cf2f7b8-9920-41b5-817a-1ffc13e0690c"
JSON_ID = "28975ef7-da35-498e-b179-cfbde2150f90"


def fixture_pdf(tmp_path, code="DENG"):
    link = consultar_evidencia_agravo_ano(code, 2024)[
        "evidencia_documental"]["documento_url"]
    file = tmp_path / link.rsplit("/", 1)[-1]
    # A deliberately fake PDF is sufficient for LOCAL hash binding.
    # The test checks that no PDF-byte comparison gets called "official".
    file.write_bytes(b"%PDF-1.4\n%SYNTHETIC-UNTRUSTED-PDF\n%%EOF\n")
    return file


def fixture_zip(tmp_path, resource_id=CSV_ID, *, content=None):
    row = next(x for x in _index()[1] if x["resource_id"] == resource_id)
    z = tmp_path / row["archive_filename"]
    if content is None:
        content = b"ID_AGRAVO,DT_INVEST,ID_OCUPA_N,EXTRA_FIELD\n2,20240101,X,SECRET-PATIENT\n"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as fh:
        fh.writestr(row["archive_filename"][:-4], content)
    return z


def fixture_candidate(tmp_path, *, resource_id=CSV_ID, pdf=None, changes=None):
    pdf = pdf or fixture_pdf(tmp_path)
    doc = _prepare_template_dict(resource_id, pdf)
    if changes:
        changes(doc)
    path = tmp_path / "contrato.json"
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return path, pdf


def test_historical_excerpt_three_fields_only_and_unreviewed(tmp_path):
    pdf = fixture_pdf(tmp_path)
    dest = tmp_path / "candidato.json"
    done = preparar_modelo_local(CSV_ID, pdf, dest)
    assert dest.exists()
    assert not done["aprovado"]
    doc = load_candidate(dest)
    assert doc["cobertura"] == "excerto_parcial"
    assert doc["situacao_transcricao"] == "manual_nao_revisada"
    assert {x["name"] for x in doc["campos_dbf"]} == {
        "ID_AGRAVO", "DT_INVEST", "ID_OCUPA_N"
    }
    assert {x["pdf_page_1_based"] for x in doc["campos_dbf"]} == {2}
    if os.name != "nt":
        assert dest.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        preparar_modelo_local(CSV_ID, pdf, dest)


def test_csv_header_only_partial_match_no_false_certification(tmp_path):
    contract, pdf = fixture_candidate(tmp_path)
    z = fixture_zip(tmp_path)
    report = comparar_esquema_local(CSV_ID, z, pdf, contract)
    assert report["estado"] == "correspondencia_parcial_sem_validacao_anual"
    assert report["n_campos_documentados"] == 3
    assert report["n_campos_observados"] == 4
    assert report["n_campos_nao_documentados"] == 1
    assert report["campos_documentados_ausentes"] == []
    assert report["campos_documentados_presentes"] == [
        "DT_INVEST", "ID_AGRAVO", "ID_OCUPA_N"
    ]
    assert report["json_registros_amostrados_localmente"] == 0
    assert not report["json_valores_examinados_transitoriamente"]
    assert not report["dicionario_aplicavel_ao_ano_verificado"]
    assert not report["revisao_epidemiologica_independente"]
    assert not report["publicacao_autorizada"]
    assert "SECRET-PATIENT" not in json.dumps(report)
    assert "EXTRA_FIELD" not in json.dumps(report)
    assert str(z) not in json.dumps(report)


def test_missing_dictionary_column_is_structural_discrepancy(tmp_path):
    contract, pdf = fixture_candidate(tmp_path)
    z = fixture_zip(tmp_path, content=b"ID_AGRAVO,ID_OCUPA_N\n2,secret\n")
    report = comparar_esquema_local(CSV_ID, z, pdf, contract)
    assert report["estado"] == "divergencia_estrutural_para_revisao"
    assert report["campos_documentados_ausentes"] == ["DT_INVEST"]


def test_full_transcription_candidate_flags_unknown_columns(tmp_path):
    contract, pdf = fixture_candidate(
        tmp_path, changes=lambda x: x.update(cobertura="transcricao_pretendida_completa")
    )
    z = fixture_zip(tmp_path)
    report = comparar_esquema_local(CSV_ID, z, pdf, contract)
    assert report["divergencia_na_cobertura_declarada"]
    assert report["n_campos_nao_documentados"] == 1
    assert not report["dicionario_aplicavel_ao_ano_verificado"]


@pytest.mark.parametrize("changes", [
    lambda x: x.update(situacao_transcricao="aprovado"),
    lambda x: x.update(cobertura=[]),
    lambda x: x.update(resource_id="not-listed"),
    lambda x: x.update(dictionary_url="https://evil.test/dictionary.pdf"),
    lambda x: x.update(pdf_sha256_local_observado="not-sha"),
    lambda x: x.update(ano_rotulado_no_portal=True),
    lambda x: x.update(campos_dbf=[]),
    lambda x: x["campos_dbf"].append(dict(x["campos_dbf"][0])),
    lambda x: x["campos_dbf"][0].update(pdf_page_1_based=0),
    lambda x: x["campos_dbf"][0].update(name="../../NM_PACIENTE"),
    lambda x: x.update(autorizacao_publicacao=True),
    lambda x: x.update(json_layout="array_of_objects"),
])
def test_untrusted_contract_cannot_approve_release(tmp_path, changes):
    pdf = fixture_pdf(tmp_path)
    contract = _prepare_template_dict(CSV_ID, pdf)
    changes(contract)
    with pytest.raises(ValueError):
        validate_candidate(contract)


def test_duplicate_json_key_contract_is_rejected(tmp_path):
    contract, _ = fixture_candidate(tmp_path)
    original = contract.read_text(encoding="utf-8")
    original = original.replace(
        '"schema_version": ', '"schema_version": "duplicate", "schema_version": ', 1
    )
    contract.write_text(original, encoding="utf-8")
    with pytest.raises(ValueError, match="chave"):
        load_candidate(contract)


def test_changed_pdf_local_checksum_blocks_comparison(tmp_path):
    contract, pdf = fixture_candidate(tmp_path)
    z = fixture_zip(tmp_path)
    pdf.write_bytes(b"%PDF-1.4\nALTERED\n%%EOF\n")
    with pytest.raises(ValueError, match="PDF local mudou"):
        comparar_esquema_local(CSV_ID, z, pdf, contract)


def test_invalid_or_oversized_header_never_echoes_data(tmp_path):
    contract, pdf = fixture_candidate(tmp_path)
    z = fixture_zip(tmp_path, content=b"ID_AGRAVO,DT_INVEST,DT_INVEST\nsecret,secret,secret\n")
    with pytest.raises(ValueError, match="Cabeçalho CSV"):
        comparar_esquema_local(CSV_ID, z, pdf, contract)
    z = fixture_zip(tmp_path, content=b"ID_AGRAVO,secret_name\n1,2\n")
    with pytest.raises(ValueError):
        comparar_esquema_local(CSV_ID, z, pdf, contract)


def test_review_packet_is_all_pending_and_exclusive(tmp_path):
    contract, pdf = fixture_candidate(tmp_path)
    z = fixture_zip(tmp_path)
    report = comparar_esquema_local(CSV_ID, z, pdf, contract)
    dest = tmp_path / "revisao-pendente.json"
    result = salvar_parecer_pendente_local(report, dest)
    doc = json.loads(dest.read_text(encoding="utf-8"))
    assert result["total_etapas_pendentes"] >= 8
    assert all(s == "pendente" for s in doc["verificacoes_pendentes"].values())
    assert doc["resultado_revisao"] == "NAO_AVALIADO"
    assert not doc["autorizacao_publicacao"]
    assert "SECRET-PATIENT" not in dest.read_text(encoding="utf-8")
    if os.name != "nt":
        assert dest.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        salvar_parecer_pendente_local(report, dest)


def test_json_array_streaming_is_bounded_and_no_values_echoed(tmp_path):
    pytest.importorskip("ijson")
    contract, pdf = fixture_candidate(tmp_path, resource_id=JSON_ID)
    z = fixture_zip(
        tmp_path, resource_id=JSON_ID,
        content=json.dumps([
            {"ID_AGRAVO": "2", "DT_INVEST": "2024-01-01",
             "ID_OCUPA_N": "SECRET-PRIVATE-DATA"},
            {"ID_AGRAVO": "2", "DT_INVEST": "2024-01-02",
             "ID_OCUPA_N": "SECRET-PRIVATE-DATA"},
        ]).encode("utf-8"),
    )
    report = comparar_esquema_local(JSON_ID, z, pdf, contract)
    assert report["json_registros_amostrados_localmente"] == 2
    assert report["json_valores_examinados_transitoriamente"]
    assert not report["divergencia_na_cobertura_declarada"]
    assert "SECRET-PRIVATE-DATA" not in json.dumps(report)


def test_json_ndjson_and_nested_structures_flagged(tmp_path):
    pytest.importorskip("ijson")
    contract, pdf = fixture_candidate(
        tmp_path, resource_id=JSON_ID,
        changes=lambda x: x.update(json_layout="ndjson"),
    )
    rows = b'{"ID_AGRAVO":"2","DT_INVEST":{"a":"private"},"ID_OCUPA_N":"x"}\n'
    z = fixture_zip(tmp_path, resource_id=JSON_ID, content=rows)
    report = comparar_esquema_local(JSON_ID, z, pdf, contract)
    assert report["json_objetos_aninhados_detectados"]
    assert report["divergencia_na_cobertura_declarada"]


def test_json_sample_limit_disclosed(tmp_path):
    pytest.importorskip("ijson")
    contract, pdf = fixture_candidate(tmp_path, resource_id=JSON_ID)
    data = [{"ID_AGRAVO": "2", "DT_INVEST": "1", "ID_OCUPA_N": "x"}
            for _ in range(90)]
    z = fixture_zip(tmp_path, resource_id=JSON_ID, content=json.dumps(data).encode())
    report = comparar_esquema_local(JSON_ID, z, pdf, contract)
    assert report["json_registros_amostrados_localmente"] == 64
    assert report["json_limite_registros_amostrados"] == 64


def test_cli_review_workflow_is_local_and_cannot_overwrite(tmp_path):
    pdf = fixture_pdf(tmp_path)
    z = fixture_zip(tmp_path)
    src = [sys.executable, "-m", "sinan_mcp"]
    contract = tmp_path / "private-contract.json"
    output = tmp_path / "private-review.json"
    cmd1 = src + [
        "preparar-modelo-esquema", "--resource-id", CSV_ID,
        "--pdf", str(pdf), "--saida", str(contract),
    ]
    proc = subprocess.run(cmd1, capture_output=True, text=True, timeout=20,
                          cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr
    cmd2 = src + [
        "comparar-esquema-privado", "--resource-id", CSV_ID,
        "--zip", str(z), "--pdf", str(pdf), "--contrato", str(contract),
        "--parecer-pendente", str(output),
    ]
    checked = subprocess.run(cmd2, capture_output=True, text=True,
                             timeout=20, cwd=tmp_path)
    assert checked.returncode == 0, checked.stderr
    assert output.is_file()
    assert "SECRET-PATIENT" not in checked.stdout
    assert "SEM" not in checked.stdout or "NENHUM INDICADOR REAL" in checked.stdout
    assert not (tmp_path / "data").exists()
    second = subprocess.run(cmd2, capture_output=True, text=True,
                            timeout=20, cwd=tmp_path)
    assert second.returncode == 2
    assert "SECRET-PATIENT" not in second.stderr
