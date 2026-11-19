"""Synthetic-only tests for local TUBE/2019 source-code preservation audit."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path

import pytest

from sinan_mcp import tb2019_source_audit as audit
from sinan_mcp.core import db_connect, project_record
from sinan_mcp.tb2019_private_import import PARQUET_SHA256, SOURCE_TYPE


def _setup(tmp_path, monkeypatch, records, *, alter_sqlite=False):
    root = tmp_path / "data" / "private" / "tb2019"
    root.mkdir(parents=True)
    monkeypatch.setattr(audit, "PRIVATE_ROOT", root)
    dbc = root / "TUBEBR19.dbc"
    dbc.write_bytes(b"ONLY_ARTIFICIAL_TEST_CONTENT")
    monkeypatch.setattr(audit, "verify_local_dbc", lambda _root: dbc)
    dbfile = root / audit.DB_NAME
    with db_connect(dbfile) as connection:
        connection.execute(
            "INSERT INTO fontes VALUES (?,?,?,?,?,?,?,?,?)",
            ("sha", "TUBE", 2019, SOURCE_TYPE, "pysus.fake", "desconhecido",
             PARQUET_SHA256, "SYNTHETIC", len(records))
        )
        for i, r in enumerate(records):
            row = list(project_record(r, "TUBE", 2019))
            if alter_sqlite and i == 0:
                row[4] = "F" if row[4] == "M" else "M"
            connection.execute(
                "INSERT INTO registros VALUES (?,?,?,?,?,?,?,?)",
                ("sha", *row)
            )

    def converter(_source, destination):
        Path(destination).write_bytes(b"SIMULATED_DBF_BYTES")

    class FakeReader:
        field_names = ["ID_MN_RESI", "CS_SEXO", "CS_RACA", "SITUA_ENCE"]
        def __init__(self, path, *, load, **kwargs):
            assert load is False
        def __iter__(self):
            return iter(records)

    return root, dbfile, converter, FakeReader


def test_source_projection_equality_without_exposing_raw_categories(tmp_path, monkeypatch):
    records = [
        {"ID_MN_RESI": "221100", "CS_SEXO": "M", "CS_RACA": "4", "SITUA_ENCE": "10"},
        {"ID_MN_RESI": "221100", "CS_SEXO": "F", "CS_RACA": "1", "SITUA_ENCE": "1"},
        {"ID_MN_RESI": "221100", "CS_SEXO": "I", "CS_RACA": "9", "SITUA_ENCE": ""},
    ]
    root, db, convert, reader = _setup(tmp_path, monkeypatch, records)
    before = db.read_bytes()
    stages = []
    output = audit.audit_original_projection(
        root, converter=convert, reader_factory=reader,
        stage=lambda stage: stages.append(stage)
    )
    assert output["dominios_brutos_sem_alertas"] is True
    assert output["projecao_sem_perda_de_codigos_preenchidos"] is True
    assert output["multiconjunto_original_projetado_igual_sqlite"] is True
    assert output["publicacao_autorizada"] is False
    assert "10" not in json.dumps(output)
    assert "221100" not in json.dumps(output)
    assert db.read_bytes() == before
    assert len(stages) == 4
    assert not list(root.rglob("*.dbf"))
    report = list(root.glob("TUBE2019-source-audit-*.json"))
    assert len(report) == 1
    assert json.loads(report[0].read_text())["raw_domain_checks"]["situacao_encerramento"] is True


def test_source_code_rejected_by_dictionary_is_not_silently_approved(tmp_path, monkeypatch):
    records = [
        {"ID_MN_RESI": "221100", "CS_SEXO": "M", "CS_RACA": "7", "SITUA_ENCE": "2"},
        {"ID_MN_RESI": "221100", "CS_SEXO": "F", "CS_RACA": "4", "SITUA_ENCE": "1"},
    ]
    root, db, convert, reader = _setup(tmp_path, monkeypatch, records)
    result = audit.audit_original_projection(root, converter=convert, reader_factory=reader)
    assert result["dominios_brutos_sem_alertas"] is False
    assert result["projecao_sem_perda_de_codigos_preenchidos"] is False
    # SQLite matches its own projected source, but that does not fix lost codes.
    assert result["multiconjunto_original_projetado_igual_sqlite"] is True


def test_sqlite_multiset_discrepancy_caught_without_details(tmp_path, monkeypatch):
    records = [
        {"ID_MN_RESI": "221100", "CS_SEXO": "M", "CS_RACA": "1", "SITUA_ENCE": "10"},
        {"ID_MN_RESI": "221100", "CS_SEXO": "M", "CS_RACA": "1", "SITUA_ENCE": "10"},
    ]
    root, _db, convert, reader = _setup(
        tmp_path, monkeypatch, records, alter_sqlite=True
    )
    result = audit.audit_original_projection(root, converter=convert, reader_factory=reader)
    assert result["multiconjunto_original_projetado_igual_sqlite"] is False
    assert result["publicacao_autorizada"] is False


def test_outside_private_directory_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "PRIVATE_ROOT", tmp_path / "expected")
    with pytest.raises(ValueError, match="Somente a pasta"):
        audit.audit_original_projection(tmp_path / "other")
