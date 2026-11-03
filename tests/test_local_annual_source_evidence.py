"""Synthetic, local-only tests for DENG/2024 annual source evidence.

No official ZIP, PDF or clinical sample is committed or used. Only metadata.
"""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

import sinan_mcp.local_annual_source_evidence as source
from sinan_mcp.local_roadmap_evidence import vincular_parecer_dengue_checklist_local
from sinan_mcp.roadmap_readiness import (
    diagnosticar_checklist_local, preparar_checklist_local,
)

RESOURCE = "4cf2f7b8-9920-41b5-817a-1ffc13e0690c"


def _inputs(tmp_path, monkeypatch):
    original = tmp_path / "roadmap-DENG-2024.json"
    preparar_checklist_local("DENG", 2024, original, RESOURCE)
    report = tmp_path / "parecer-pendente-dengue-crosswalk-2024.json"
    payload = {
        "schema_version": "sinan-private-dengue-crosswalk-candidate-v1",
        "resource_id": RESOURCE, "agravo": "DENG",
        "ano_rotulado_no_portal": 2024, "status_revisao": "PENDENTE",
        "publicacao_autorizada": False, "autorizacao_analise_real": False,
        "dicionario_aplicavel_a_exportacao_2024_validado": False,
        "dominios_categoricos_verificados": False,
        "linhas_de_pacientes_lidas": 0,
        "campos_csv_desconhecidos_incluidos_no_parecer": False,
        "pdf_atual_sha256_local": "a" * 64,
        "zip_sha256_local": "b" * 64,
        "pdf2015_sha256_local": "c" * 64,
        "n_campos_csv": 121, "n_nomes_unicos_pdf_atual": 120,
        "nome_comum_pdf_atual_csv": 119,
        "quantidade_csv_fora_pdf_atual": 2,
        "nomes_pdf_atual_ausentes_csv": ["CLINIC_CHIK"],
    }
    report.write_text(json.dumps(payload), encoding="utf-8")
    linked = tmp_path / "roadmap-DENG-2024-com-evidencia.json"
    vincular_parecer_dengue_checklist_local(original, report, linked)
    source_row = {
        "agravo_alias_interno": "DENG",
        "ano_rotulado_no_portal": 2024,
        "distribution_format": "CSV",
        "archive_filename": "DENGBR24.csv.zip",
        "distribution_url": "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Dengue/csv/DENGBR24.csv.zip",
        "resource_url": "https://dadosabertos.saude.gov.br/dataset/arboviroses-dengue/resource/" + RESOURCE,
    }
    monkeypatch.setattr(source, "_resource", lambda _: source_row)
    evidence = {
        "schema_version": "sinan-local-official-resource-zip-inspection-v1",
        "resource_id": RESOURCE, "formato_declarado": "CSV",
        "arquivo_zip_estrutura_compativel_com_nome_registrado": True,
        "arquivos_extraidos": 0, "conteudo_clinico_lido": False,
        "origem_dos_bytes_autenticada": False, "publicacao_autorizada": False,
        "arquivo_pacote_sha256_local": "b" * 64,
        "arquivo_pacote_bytes_local": 187264443,
    }
    monkeypatch.setattr(
        source, "conferir_zip_recurso_local", lambda resource, path: evidence
    )
    return original, report, linked, source_row, evidence


def test_source_dossier_and_checkpoint_remain_unapproved(tmp_path, monkeypatch):
    original, report, linked, row, inspection = _inputs(tmp_path, monkeypatch)
    dossier = tmp_path / "fonte.json"
    summary = source.preparar_dossie_fonte_dengue_local(
        "DENGBR24.csv.zip", report, dossier,
    )
    assert summary["zip_local_conciliado_com_parecer"] is True
    assert summary["status_consolidacao"] == "DESCONHECIDO"
    assert summary["origem_oficial_autenticada"] is False
    obj = json.loads(dossier.read_text(encoding="utf-8"))
    assert obj["zip_sha256_local"] == "b" * 64
    assert obj["registros_clinicos_lidos"] == 0
    assert obj["origem_autenticada_por_autoridade"] is False
    assert obj["data_corte_verificada"] is False
    assert "CLINC_CHIK" not in dossier.read_text(encoding="utf-8")
    assert "CLINIC_CHIK" not in dossier.read_text(encoding="utf-8")
    output = tmp_path / "roadmap-DENG-2024-com-fonte.json"
    result = source.vincular_dossie_fonte_dengue_roadmap_local(
        linked, report, dossier, output
    )
    assert result["n_frentes_pendentes"] == 5
    assert result["n_frentes_com_evidencia_local_nao_validada"] == 2
    assert result["autenticidade_oficial_confirmada"] is False
    assert result["consolidacao_confirmada"] is False
    assert result["publicacao_autorizada"] is False
    assert diagnosticar_checklist_local(original)["n_frentes_pendentes"] == 7
    assert diagnosticar_checklist_local(linked)["n_frentes_pendentes"] == 6
    assert diagnosticar_checklist_local(output)["n_frentes_pendentes"] == 5
    assert not any(
        x in output.read_text(encoding="utf-8")
        for x in ("CLINC_CHIK", "CLINIC_CHIK")
    )
    with pytest.raises(FileExistsError):
        source.vincular_dossie_fonte_dengue_roadmap_local(
            linked, report, dossier, output
        )


@pytest.mark.parametrize("tamper", [
    {"origem_autenticada_por_autoridade": True},
    {"checksum_oficial_verificado": True},
    {"data_corte_verificada": True},
    {"status_consolidacao": "FINAL"},
    {"revisao_institucional_independente": "APROVADO"},
    {"publicacao_autorizada": True},
    {"registros_clinicos_lidos": 1},
    {"resource_id": "fake-id"},
    {"zip_sha256_local": "0" * 64},
    {"pdf_documental_sha256_local": "0" * 64},
    {"crosswalk_pending_sha256_local": "0" * 64},
    {"ano_rotulado_no_portal": 2025},
])
def test_dossier_tampering_cannot_promote_status(tmp_path, monkeypatch, tamper):
    _, report, linked, _, _ = _inputs(tmp_path, monkeypatch)
    dossier = tmp_path / "fonte.json"
    source.preparar_dossie_fonte_dengue_local("fake.zip", report, dossier)
    value = json.loads(dossier.read_text(encoding="utf-8"))
    value.update(tamper)
    dossier.write_text(json.dumps(value), encoding="utf-8")
    out = tmp_path / "out.json"
    with pytest.raises(ValueError):
        source.vincular_dossie_fonte_dengue_roadmap_local(
            linked, report, dossier, out
        )
    assert not out.exists()


def test_zip_hash_mismatch_blocks_source_and_writes_nothing(tmp_path, monkeypatch):
    _, report, _, _, inspection = _inputs(tmp_path, monkeypatch)
    inspection["arquivo_pacote_sha256_local"] = "d" * 64
    output = tmp_path / "fonte.json"
    with pytest.raises(ValueError, match="nao conciliados"):
        source.preparar_dossie_fonte_dengue_local("fake.zip", report, output)
    assert not output.exists()


def test_existing_dossier_is_not_overwritten(tmp_path, monkeypatch):
    _, report, _, _, _ = _inputs(tmp_path, monkeypatch)
    target = tmp_path / "fonte.json"
    source.preparar_dossie_fonte_dengue_local("fake.zip", report, target)
    with pytest.raises(FileExistsError):
        source.preparar_dossie_fonte_dengue_local("fake.zip", report, target)


def test_duplicate_json_and_crosswalk_changed_fail_closed(tmp_path, monkeypatch):
    _, report, linked, _, _ = _inputs(tmp_path, monkeypatch)
    dossier = tmp_path / "fonte.json"
    source.preparar_dossie_fonte_dengue_local("fake.zip", report, dossier)
    raw = dossier.read_text(encoding="utf-8")
    dossier.write_text(raw[:-1] + ',"publicacao_autorizada":false}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicadas"):
        source.vincular_dossie_fonte_dengue_roadmap_local(
            linked, report, dossier, tmp_path / "out.json"
        )
    dossier.write_text(raw, encoding="utf-8")
    prior = json.loads(report.read_text(encoding="utf-8"))
    prior["zip_sha256_local"] = "e" * 64
    report.write_text(json.dumps(prior), encoding="utf-8")
    with pytest.raises(ValueError):
        source.vincular_dossie_fonte_dengue_roadmap_local(
            linked, report, dossier, tmp_path / "out.json"
        )


def test_cli_help_documents_2_private_actions():
    for command in (
        "preparar-dossie-fonte-dengue",
        "vincular-fonte-dengue-roadmap",
    ):
        x = subprocess.run(
            [sys.executable, "-m", "sinan_mcp", command, "--help"],
            capture_output=True, text=True, timeout=20,
        )
        assert x.returncode == 0, x.stderr
        assert "--saida" in x.stdout
