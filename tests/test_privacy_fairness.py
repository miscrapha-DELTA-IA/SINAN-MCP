"""Security regression tests for ChatGPT tunnel and local fairness workflow.

All rows are deliberately fabricated. Never commit real SINAN data.
"""
from __future__ import annotations

import csv
import json
import sqlite3

import pytest

from sinan_mcp.core import db_connect_readonly, ingest_csv
from sinan_mcp.fairness import _auc, _average_precision, audit_predictions
from sinan_mcp.tool_api import abandono_publico, contagens_publicas, listar_bases_publicas


def _db(tmp_path, rows):
    source = tmp_path / "fictional.csv"
    with source.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["CS_RACA", "CS_SEXO", "ID_MN_RESI", "SITUA_ENCE"])
        writer.writeheader()
        writer.writerows(rows)
    database = tmp_path / "synthetic_projection.sqlite3"
    ingest_csv(database, source, agravo="TUBE", ano=2024)
    return database


def _row(i, *, race="4", outcome="1"):
    return {"CS_RACA": race, "CS_SEXO": "F" if i % 2 else "M",
            "ID_MN_RESI": "221100", "SITUA_ENCE": outcome}


def test_public_real_data_requires_explicit_local_admin_approval(tmp_path, monkeypatch):
    db = _db(tmp_path, [_row(i, race="4" if i < 100 else "1",
                         outcome="2" if i % 4 == 0 else "1") for i in range(200)])
    monkeypatch.delenv("SINAN_PUBLIC_REAL_DATA", raising=False)
    with pytest.raises(ValueError, match="Dados reais bloqueados"):
        contagens_publicas(db, agravo="TUBE", ano_inicio=2024, ano_fim=2024, uf="PI")
    assert listar_bases_publicas(db)["bases"][0]["tipo_de_fonte"] == "csv-local"
    monkeypatch.setenv("SINAN_PUBLIC_REAL_DATA", "1")
    output = contagens_publicas(db, agravo="TUBE", ano_inicio=2024,
                               ano_fim=2024, uf="PI", por="raca_cor")
    assert output["resultado"]["dados"]
    assert output["resultado"].get("status") != "nao_divulgavel"


def test_small_cell_blocks_other_dimension_and_tb_metric(tmp_path, monkeypatch):
    db = _db(tmp_path, [_row(i, race="4" if i < 196 else "1",
                         outcome="2" if i % 3 == 0 else "1") for i in range(200)])
    monkeypatch.setenv("SINAN_PUBLIC_REAL_DATA", "1")
    for dimension in ["sexo", "raca_cor"]:
        result = contagens_publicas(db, agravo="TUBE",
                                   ano_inicio=2024, ano_fim=2024, uf="PI", por=dimension)
        assert result["resultado"]["status"] == "nao_divulgavel"
        assert result["resultado"]["dados"] == []
    loss = abandono_publico(db, ano_inicio=2024, ano_fim=2024, uf="PI", por="sexo")
    assert loss["resultado"]["dados"] == []
    assert loss["resultado"]["status"] == "nao_divulgavel"


def test_small_outcome_subcell_blocks_simple_count_too(tmp_path, monkeypatch):
    rows = []
    for i in range(240):
        race = "4" if i < 120 else "1"
        # Deliberately rare lost outcomes in race=4 (5 of 120).
        lost = (i < 5) or (i >= 120 and i % 3 == 0)
        rows.append(_row(i, race=race, outcome="2" if lost else "1"))
    db = _db(tmp_path, rows)
    monkeypatch.setenv("SINAN_PUBLIC_REAL_DATA", "1")
    for dimension in ["sexo", "raca_cor"]:
        r = contagens_publicas(db, agravo="TUBE",
                              ano_inicio=2024, ano_fim=2024, uf="PI", por=dimension)
        assert r["resultado"]["dados"] == []


def test_query_only_never_creates_or_modifies_local_database(tmp_path):
    missing = tmp_path / "missing.db"
    with pytest.raises(ValueError, match="não inicializado"):
        db_connect_readonly(missing)
    assert not missing.exists()
    db = _db(tmp_path, [_row(i) for i in range(110)])
    con = db_connect_readonly(db)
    try:
        with pytest.raises(sqlite3.OperationalError):
            con.execute("DELETE FROM registros")
        assert con.execute("SELECT COUNT(*) FROM registros").fetchone()[0] == 110
    finally:
        con.close()


def _predictions(tmp_path, *, bad=False):
    path = tmp_path / "predictions.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["y_true", "y_score", "raca_cor", "identificador"])
        writer.writeheader()
        for i in range(120):
            y = 1 if i % 2 else 0
            score = 0.9 if y else 0.1
            if bad and i == 4:
                score = "NaN"
            writer.writerow({"y_true": y, "y_score": score,
                             "raca_cor": "4" if i < 60 else "1",
                             "identificador": "SEGREDO_FICTICIO_" + str(i)})
    return path


def test_fairness_binary_metrics_perfect_model_and_no_identifiers(tmp_path):
    source = _predictions(tmp_path)
    result = audit_predictions(source, group="raca_cor", cohort="2022-2023",
                               bootstrap=20, seed=7)
    assert result["n_registros_avaliados"] == 120
    assert result["coorte_de_teste_informada"] == "2022-2023"
    assert set(result["grupos_elegiveis"]) == {"1", "4"}
    assert result["disparidades"] == {"spd": 0.0, "eod": 0.0, "aaod": 0.0}
    for group in result["grupos_elegiveis"].values():
        assert group["auroc"] == pytest.approx(1.0)
        assert group["average_precision"] == pytest.approx(1.0)
        assert group["sensibilidade_tpr"] == pytest.approx(1.0)
        assert group["fpr"] == pytest.approx(0.0)
    assert result["bootstrap_iid_percentil"]["eod"]["inferior_2_5pct"] == 0
    assert "SEGREDO_FICTICIO" not in json.dumps(result)


def test_fairness_auc_average_precision_ties():
    pairs = [(0.2, 0), (0.2, 1)]
    assert _auc(pairs) == pytest.approx(0.5)
    assert _average_precision(pairs) == pytest.approx(0.5)
    assert _auc([(0.1, 0), (0.9, 1)]) == 1.0
    assert _average_precision([(0.1, 0), (0.9, 1)]) == 1.0


def test_fairness_rejects_nan_and_unknown_groups(tmp_path):
    with pytest.raises(ValueError, match="Pontuação"):
        audit_predictions(_predictions(tmp_path, bad=True), group="raca_cor")
    with pytest.raises(ValueError, match="Grupo permitido"):
        audit_predictions(_predictions(tmp_path), group="id_paciente")
    with pytest.raises(ValueError, match="Limiar"):
        audit_predictions(_predictions(tmp_path), group="raca_cor", threshold=1.0)


def test_fairness_too_small_group_not_reported(tmp_path):
    source = tmp_path / "small.csv"
    with source.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["y_true", "y_score", "sexo"])
        writer.writeheader()
        for i in range(102):
            writer.writerow({"y_true": i % 2, "y_score": 0.8 if i % 2 else 0.2,
                             "sexo": "M" if i < 100 else "I"})
    result = audit_predictions(source, group="sexo")
    assert set(result["grupos_elegiveis"]) == {"M"}
    assert result["n_grupos_insuficientes"] == 1
    assert all(value is None for value in result["disparidades"].values())
