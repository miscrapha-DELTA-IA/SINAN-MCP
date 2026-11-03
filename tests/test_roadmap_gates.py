"""Synthetic fixtures only: test offline roadmap gates without any SINAN records."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys

import pytest

from sinan_mcp.core import ingest_csv
from sinan_mcp.provenance import validate_manifest, verify_local_file, load_manifest
from sinan_mcp.quality_gate import audit_projected_snapshot
from sinan_mcp.aggregate_contract import candidate_digest
from sinan_mcp.release_pipeline import prepare_candidate
from sinan_mcp.release_composition import assess_release_set


def fake_evidence(tmp_path):
    file = tmp_path / "fake.csv"
    file.write_text("CS_SEXO,CS_RACA\nF,4\n", encoding="utf-8")
    digest = hashlib.sha256(file.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "sinan-source-evidence-v1",
        "agravo": "TUBE", "ano_arquivo": 2024, "tipo_ano": "ano_arquivo",
        "codigo_download_declarado": "TUBE",
        "metodo": "csv-local",
        "url_fonte": "https://www.gov.br/saude/pt-br/",
        "url_dicionario": "https://portalsinan.saude.gov.br/tuberculose",
        "versao_dicionario": "versao de exemplo 2024",
        "situacao_declarada": "desconhecido",
        "extraido_em_utc": "2026-11-02T18:00:00Z",
        "arquivo_nome": "fake.csv", "arquivo_bytes": file.stat().st_size,
        "arquivo_sha256": digest,
        "observacao_metodologica": "EXEMPLO SINTETICO; NENHUM DADO SINAN REAL",
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return file, path, manifest


def test_checksum_only_proves_local_integrity(tmp_path):
    file, evidence, manifest = fake_evidence(tmp_path)
    assert validate_manifest(manifest) is manifest
    result = verify_local_file(evidence, file)
    assert result["integridade_local_verificada"]
    assert not result["identidade_fonte_oficial_verificada"]
    assert not result["status_final_documental_verificado"]
    assert not result["codigo_download_oficial_verificado"]
    assert not result["aprovacao_para_publicacao"]
    assert "CS_SEXO" not in json.dumps(result)
    assert not any(x.suffix == ".sqlite3" for x in tmp_path.iterdir())


@pytest.mark.parametrize("change", [
    lambda x: x.update(agravo="UNKNOWN"),
    lambda x: x.update(agravo=[]),
    lambda x: x.update(tipo_ano=[]),
    lambda x: x.update(metodo={}),
    lambda x: x.update(situacao_declarada=[]),
    lambda x: x.update(ano_arquivo=True),
    lambda x: x.update(tipo_ano="ano_indeterminado"),
    lambda x: x.update(metodo="http-arbitrary"),
    lambda x: x.update(situacao_declarada="certificada"),
    lambda x: x.update(url_fonte="https://evil.gov.br.attacker.invalid/"),
    lambda x: x.update(url_dicionario="http://portalsinan.saude.gov.br/"),
    lambda x: x.update(arquivo_nome="../patient.csv"),
    lambda x: x.update(arquivo_bytes=False),
    lambda x: x.update(arquivo_sha256="not_a_hash"),
    lambda x: x.update(extraido_em_utc="2026-11-02"),
    lambda x: x.update(pacientes=[{"nome": "NAO_ENVIAR"}]),
])
def test_reject_unsafe_manifest_fields(tmp_path, change):
    _, _, manifest = fake_evidence(tmp_path)
    change(manifest)
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_changed_file_and_duplicate_json_keys_are_rejected(tmp_path):
    file, path, manifest = fake_evidence(tmp_path)
    file.write_text("alterado sem atualizar checksum", encoding="utf-8")
    with pytest.raises(ValueError):
        verify_local_file(path, file)
    contents = json.dumps(manifest)
    path.write_text(contents.replace('"schema_version":', '"schema_version": "sinan-source-evidence-v1", "schema_version":', 1))
    with pytest.raises(ValueError, match="JSON"):
        load_manifest(path)


def test_manifest_symlink_not_accepted(tmp_path):
    file, path, _ = fake_evidence(tmp_path)
    link = tmp_path / "link.json"
    try:
        link.symlink_to(path)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks unavailable")
    with pytest.raises(ValueError, match="simbólico"):
        verify_local_file(link, file)


def fake_snapshot(tmp_path, *, ano=2024, uf="PI"):
    code = "221100" if uf == "PI" else "355030"
    dataset = tmp_path / f"{ano}-{uf}.csv"
    with dataset.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "ID_MN_RESI", "CS_SEXO", "CS_RACA", "SITUA_ENCE", "NM_PACIENT"
        ])
        writer.writeheader()
        for i in range(220):
            writer.writerow({
                "ID_MN_RESI": code, "CS_SEXO": "M" if i % 2 else "F",
                "CS_RACA": "1" if i % 2 else "4", "SITUA_ENCE": "1",
                "NM_PACIENT": f"FAKE{i}"
            })
    db = tmp_path / f"{ano}-{uf}.sqlite3"
    ingest_csv(db, dataset, agravo="TUBE", ano=ano, status="final")
    return db


def test_quality_admin_report_readonly_and_no_individual_data(tmp_path):
    db = fake_snapshot(tmp_path)
    before = db.read_bytes()
    result = audit_projected_snapshot(db, agravo="TUBE", ano=2024)
    assert result["registros_snapshot"] == 220
    assert result["registros_metadado"] == 220
    assert result["integridade_metadado"]["contagem_igual_metadado"]
    assert result["linhas_com_projecao_identica_alem_da_primeira"] == 218
    assert result["equivalencia_projecao_nao_indica_pessoa_duplicada"]
    assert not result["reconciliado_com_tabnet"]
    assert not result["dicionario_ano_validado"]
    assert not result["aprovado_publicacao"]
    assert "FAKE0" not in json.dumps(result)
    assert db.read_bytes() == before


def test_quality_fails_without_existing_database(tmp_path):
    bad = tmp_path / "nonexistent.sqlite3"
    with pytest.raises(ValueError):
        audit_projected_snapshot(bad, agravo="TUBE", ano=2024)
    assert not bad.exists()


def fake_approved(tmp_path, *, ano=2024, uf="PI"):
    folder = tmp_path / f"package-{ano}-{uf}"
    folder.mkdir()
    db = fake_snapshot(folder, ano=ano, uf=uf)
    candidate = prepare_candidate(db, agravo="TUBE", ano=ano, uf=uf, por="sexo")
    obj = {
        "stage": "APPROVED_PUBLIC_AGGREGATE",
        "candidate": candidate,
        "candidate_sha256": candidate_digest(candidate),
        "review": {
            "privacy_reviewer": "Independent Test Privacy Reviewer",
            "scientific_reviewer": "Independent Test Epidemiology Reviewer",
            "review_reference": "FAKE NON-PUBLIC TEST DECISION",
            "publication_authorized": True,
            "cross_release_comparison_reviewed": True,
        },
    }
    path = folder / "fake-approved.json"
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return str(path), hashlib.sha256(path.read_bytes()).hexdigest()


def test_release_gate_fails_closed_across_file_year_and_dimension(tmp_path):
    a = fake_approved(tmp_path, ano=2024, uf="PI")
    b = fake_approved(tmp_path, ano=2023, uf="PI")
    with pytest.raises(ValueError, match="COMPOSIÇÃO"):
        assess_release_set([a, b])
    with pytest.raises(ValueError, match="repetido"):
        assess_release_set([a, a])


def test_nonoverlap_still_never_authorizes_publication(tmp_path):
    a = fake_approved(tmp_path, ano=2024, uf="PI")
    b = fake_approved(tmp_path, ano=2024, uf="SP")
    out = assess_release_set([a, b])
    assert out["pacotes_validados_estruturalmente"] == 2
    assert out["sobreposicao_direta_detectada"] is False
    assert out["revisao_de_composicao_externa_concluida"] is False
    assert out["publicacao_autorizada"] is False
    assert not out["garantia_de_anonimizacao"]


def test_invalid_package_checksum_blocks_release(tmp_path):
    a = fake_approved(tmp_path)
    with pytest.raises(ValueError):
        assess_release_set([(a[0], "a" * 64)])


def test_cli_local_gates(tmp_path):
    file, manifest, _ = fake_evidence(tmp_path)
    q = subprocess.run(
        [sys.executable, "-m", "sinan_mcp", "verificar-proveniencia",
         str(manifest), str(file)],
        cwd=tmp_path, text=True, capture_output=True, timeout=20
    )
    assert q.returncode == 0, q.stderr
    assert '"aprovacao_para_publicacao": false' in q.stdout
    assert "CS_SEXO" not in q.stdout

    bad = subprocess.run(
        [sys.executable, "-m", "sinan_mcp", "verificar-proveniencia",
         str(manifest), str(tmp_path / "missing.csv")],
        cwd=tmp_path, text=True, capture_output=True, timeout=20
    )
    assert bad.returncode == 2
    assert "PROVENIÊNCIA NÃO VERIFICADA" in bad.stderr
    assert "Traceback" not in bad.stderr



def fake_declared_tabnet(tmp_path, *, year_type="ano_arquivo", second=110):
    obj = {
        "schema_version": "sinan-official-tabulation-candidate-v1",
        "stage": "UNAPPROVED_OFFICIAL_TABULATION",
        "source": {
            "url": "https://datasus.saude.gov.br/informacoes-de-saude-tabnet/",
            "titulo_tabela": "TABELA INTEIRAMENTE INVENTADA PARA TESTE",
            "extracao_utc": "2026-11-02T18:00:00Z",
            "sha256_arquivo_origem": "f" * 64,
            "filtros_tabulacao": "teste fake TUBE; ano 2024, uf PI, sexo",
            "estado_consolidacao": "desconhecido",
        },
        "scope": {
            "agravo_codigo_interno": "TUBE",
            "agravo_nome": "Tuberculose",
            "uf": "PI",
            "ano_inicio": 2024, "ano_fim": 2024,
            "tipo_ano": year_type,
            "indicador": "registros_tabnet", "dimensao": "sexo",
        },
        "cells": [
            {"categoria": "F", "registros": 110},
            {"categoria": "M", "registros": second},
        ],
        "limitations": "TABELA ARTIFICIAL DE TESTE. NUNCA USAR PARA ESTATISTICAS REAIS.",
    }
    file = tmp_path / "tabnet-fake.json"
    file.write_text(json.dumps(obj), encoding="utf-8")
    return file


def test_offline_reconciliation_equal_but_never_certified(tmp_path):
    from sinan_mcp.reconciliation import reconcile_declared_table
    db = fake_snapshot(tmp_path)
    file = fake_declared_tabnet(tmp_path)
    report = reconcile_declared_table(db, file)
    assert report["categorias_iguais"] is True
    assert report["contagens_iguais"] is True
    assert report["numero_de_categorias_com_diferenca"] == 0
    assert not report["arquivo_fonte_oficial_autenticado"]
    assert not report["coorte_epidemiologica_validada"]
    assert not report["publicacao_autorizada"]
    assert '"registros"' not in json.dumps(report)
    assert "FAKE0" not in json.dumps(report)


def test_offline_reconciliation_detects_fake_mismatch_and_wrong_year(tmp_path):
    from sinan_mcp.reconciliation import reconcile_declared_table
    db = fake_snapshot(tmp_path)
    file = fake_declared_tabnet(tmp_path, second=120)
    report = reconcile_declared_table(db, file)
    assert not report["contagens_iguais"]
    assert report["numero_de_categorias_com_diferenca"] == 1
    file = fake_declared_tabnet(tmp_path, year_type="ano_diagnostico")
    with pytest.raises(ValueError, match="ano_arquivo"):
        reconcile_declared_table(db, file)


def test_offline_reconciliation_blocks_small_cells(tmp_path):
    from sinan_mcp.reconciliation import reconcile_declared_table
    db = fake_snapshot(tmp_path)
    import sqlite3
    # Mutate the disposable synthetic fixture only.
    with sqlite3.connect(db) as con:
        con.execute(
            "DELETE FROM registros WHERE rowid IN "
            "(SELECT rowid FROM registros WHERE sexo='M' LIMIT 95)"
        )
    file = fake_declared_tabnet(tmp_path)
    with pytest.raises(ValueError, match="pequena"):
        reconcile_declared_table(db, file)
