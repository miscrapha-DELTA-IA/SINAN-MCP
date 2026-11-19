"""Synthetic-only quality preflight tests; never access health data or network."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from sinan_mcp import tb2019_quality as quality
from sinan_mcp import tb2019_private_import as private
from sinan_mcp import tb2019_parity as parity


def fixture(tmp_path, monkeypatch, *, status="desconhecido", registered=3):
    root = tmp_path / "data" / "private" / "tb2019"
    root.mkdir(parents=True)
    db = root / quality.DATABASE
    monkeypatch.setattr(quality, "PRIVATE_ROOT", root)
    monkeypatch.setattr(parity, "verify_local_dbc", lambda _root: root / "TUBEBR19.dbc")
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE fontes (chave TEXT, agravo TEXT, ano INT, tipo_fonte TEXT, "
            "status TEXT, sha256 TEXT, n_registros INT)"
        )
        conn.execute(
            "CREATE TABLE registros (chave TEXT, agravo TEXT, ano INT, uf TEXT, "
            "municipio TEXT, sexo TEXT, raca_cor TEXT, situacao_encerramento TEXT)"
        )
        conn.execute(
            "INSERT INTO fontes VALUES (?,?,?,?,?,?,?)",
            ("a", "TUBE", 2019, private.SOURCE_TYPE, status,
             private.PARQUET_SHA256, registered)
        )
        conn.executemany(
            "INSERT INTO registros VALUES (?,?,?,?,?,?,?,?)",
            [
                ("a", "TUBE", 2019, "PI", "221100", "F", "4", "1"),
                ("a", "TUBE", 2019, "PI", "221100", "M", "1", "2"),
                ("a", "TUBE", 2019, "PI", "221100", None, "9", None),
            ]
        )
    return root, db


def test_quality_preflight_is_local_and_no_counts(tmp_path, monkeypatch):
    root, db = fixture(tmp_path, monkeypatch)
    before = db.read_bytes()
    outcome = quality.audit_private_tb2019(db)
    assert outcome["verificacao_tecnica"] == "concluida"
    assert outcome["status_final_homologado"] is False
    assert outcome["publicacao_autorizada"] is False
    assert outcome["contagens_ou_registros_exibidos"] is False
    assert "221100" not in str(outcome)
    assert "n_registros" not in json.dumps(outcome)
    reports = list(root.glob("TUBE2019-quality-*.json"))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text(encoding="utf-8"))
    assert report["completude_bandas"]["sexo"] != "zero"
    assert report["verificacoes"]["codigos_projetados_no_dominio"]
    assert report["verificacoes"]["uf_municipio_projetados_consistentes"]
    assert "n_registros" not in report
    assert db.read_bytes() == before


def test_status_final_alone_is_rejected(tmp_path, monkeypatch):
    _root, db = fixture(tmp_path, monkeypatch, status="final")
    with pytest.raises(ValueError, match="Fonte fora"):
        quality.audit_private_tb2019(db)


def test_inconsistent_row_metadata_rejected(tmp_path, monkeypatch):
    _root, db = fixture(tmp_path, monkeypatch, registered=4)
    with pytest.raises(ValueError, match="Integridade de escopo"):
        quality.audit_private_tb2019(db)


def test_outside_private_dir_is_rejected(tmp_path, monkeypatch):
    root, db = fixture(tmp_path, monkeypatch)
    other = tmp_path / "outside.sqlite3"
    other.write_bytes(db.read_bytes())
    with pytest.raises(ValueError, match="Banco restrito"):
        quality.audit_private_tb2019(other)


def test_bucket_categories_do_not_disclose_numerator():
    assert quality._bucket(0, 100) == "zero"
    assert quality._bucket(1, 100) == "ate_1_porcento"
    assert quality._bucket(2, 100) == "mais_1_ate_5_porcento"
    assert quality._bucket(100, 100) == "mais_20_porcento"
