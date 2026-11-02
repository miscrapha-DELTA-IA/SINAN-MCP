"""Release gates: fabricated records only, no real health data or cloud upload."""
from __future__ import annotations

import asyncio
import csv
import hashlib
import inspect
import json
import os
import subprocess
import sys

import pytest

from sinan_mcp.core import ingest_csv
from sinan_mcp.release_pipeline import prepare_candidate, write_private_candidate
from sinan_mcp.aggregate_contract import (
    candidate_digest, validate_candidate, load_approved_release,
)


def fake_db(tmp_path, *, races=(110, 110), status="final"):
    source = tmp_path / "fabricated.csv"
    with source.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "ID_MN_RESI", "CS_RACA", "CS_SEXO", "SITUA_ENCE",
            "NM_PACIENT", "NU_NOTIFIC",
        ])
        writer.writeheader()
        n = 0
        for race, quantity in zip(("4", "1"), races):
            for i in range(quantity):
                writer.writerow({
                    "ID_MN_RESI": "221100", "CS_RACA": race,
                    "CS_SEXO": "F" if i % 2 else "M", "SITUA_ENCE": "1",
                    "NM_PACIENT": f"FICTICIO_PRIVADO_{n}",
                    "NU_NOTIFIC": f"FAKE_IDENT_{n}",
                })
                n += 1
    db = tmp_path / "research.sqlite3"
    ingest_csv(db, source, agravo="TUBE", ano=2024, status=status)
    return db


def package(candidate):
    return {
        "stage": "APPROVED_PUBLIC_AGGREGATE",
        "candidate": candidate,
        "candidate_sha256": candidate_digest(candidate),
        "review": {
            "privacy_reviewer": "Independent Privacy Reviewer",
            "scientific_reviewer": "Independent Scientific Reviewer",
            "review_reference": "Private institutional decision no. 999",
            "publication_authorized": True,
            "cross_release_comparison_reviewed": True,
        },
    }


def save_package(tmp_path, obj):
    path = tmp_path / "approved.json"
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
    path.write_bytes(raw)
    return path, hashlib.sha256(raw).hexdigest()


def test_candidate_build_from_local_projection_is_not_public(tmp_path, monkeypatch):
    db = fake_db(tmp_path)
    before = db.read_bytes()
    out = prepare_candidate(db, agravo="TUBE", ano=2024, uf="PI", por="raca_cor")
    validate_candidate(out)
    assert out["stage"] == "UNAPPROVED_RESEARCH_CANDIDATE"
    assert out["source"]["tipo"] == "csv-local"
    assert out["scope"]["ano_nao_e_diagnostico"] is True
    assert [x["registros"] for x in out["cells"]] == [110, 110]
    assert out["policy"]["not_formal_anonymization"] is True
    assert "FICTICIO_PRIVADO" not in json.dumps(out)
    assert "NU_NOTIFIC" not in json.dumps(out)
    assert db.read_bytes() == before
    monkeypatch.chdir(tmp_path)
    path = write_private_candidate(out)
    assert path.is_file()
    assert str(path.resolve()).startswith(str((tmp_path/"data").resolve()))
    assert path.name.endswith(".candidate.json")
    with pytest.raises(FileExistsError):
        write_private_candidate(out)
    with pytest.raises(ValueError, match="data/"):
        write_private_candidate(out, root=tmp_path / "repository" / "assets")


def test_reject_entire_partition_if_one_subgroup_below_k(tmp_path):
    db = fake_db(tmp_path, races=(201, 19))
    with pytest.raises(ValueError, match="Célula pequena"):
        prepare_candidate(db, agravo="TUBE", ano=2024, uf="PI", por="raca_cor")
    assert not list(tmp_path.rglob("candidate.json"))


def test_reject_small_or_disallowed_partition(tmp_path):
    db = fake_db(tmp_path, races=(30, 30))
    with pytest.raises(ValueError, match="Partição insuficiente"):
        prepare_candidate(db, agravo="TUBE", ano=2024, uf="PI", por="sexo")
    for kwargs in [
        {"por": "municipio", "uf": "PI"},
        {"por": "raca_cor", "uf": "invalid"},
        {"por": "raca_cor", "uf": "PI", "ano": 2023},
    ]:
        params = {"agravo": "TUBE", "ano": 2024, "uf": "PI", "por": "raca_cor"}
        params.update(kwargs)
        with pytest.raises(ValueError):
            prepare_candidate(db, **params)


def test_approved_static_package_is_pinned_and_reviewer_attested(tmp_path):
    candidate = prepare_candidate(fake_db(tmp_path), agravo="TUBE", ano=2024,
                                  uf="PI", por="raca_cor")
    path, digest = save_package(tmp_path, package(candidate))
    loaded = load_approved_release(path, digest)
    assert loaded["candidate"]["cells"] == candidate["cells"]
    with pytest.raises(ValueError, match="Checksum"):
        load_approved_release(path, "a" * 64)
    changed = package(candidate)
    changed["candidate"]["cells"][0]["registros"] += 1
    tamper_path, tamper_digest = save_package(tmp_path, changed)
    with pytest.raises(ValueError, match="modificado"):
        load_approved_release(tamper_path, tamper_digest)
    wrong = package(candidate)
    wrong["review"]["cross_release_comparison_reviewed"] = False
    path, digest = save_package(tmp_path, wrong)
    with pytest.raises(ValueError, match="aprovação"):
        load_approved_release(path, digest)


def test_preliminary_source_must_not_be_approved(tmp_path):
    db = fake_db(tmp_path, status="desconhecido")
    candidate = prepare_candidate(db, agravo="TUBE", ano=2024, uf="PI", por="sexo")
    path, digest = save_package(tmp_path, package(candidate))
    with pytest.raises(ValueError, match="status final"):
        load_approved_release(path, digest)


def test_unknown_extra_columns_and_lower_k_rejected(tmp_path):
    candidate = prepare_candidate(fake_db(tmp_path), agravo="TUBE",
                                  ano=2024, uf="PI", por="raca_cor")
    with pytest.raises(ValueError, match="célula"):
        candidate["cells"][0]["registros"] = 1
        validate_candidate(candidate)
    candidate["cells"][0]["registros"] = 110
    candidate["cells"][0]["patient_name"] = "FICTICIO"
    with pytest.raises(ValueError, match="Campo de célula"):
        validate_candidate(candidate)


def test_public_approved_server_fails_closed_without_explicit_package(monkeypatch):
    from sinan_mcp import approved_server
    monkeypatch.delenv("SINAN_APPROVED_RELEASE_FILE", raising=False)
    monkeypatch.delenv("SINAN_APPROVED_RELEASE_SHA256", raising=False)
    approved_server._release.cache_clear()
    with pytest.raises(RuntimeError, match="desativada"):
        approved_server.sobre_o_servidor()
    src = inspect.getsource(approved_server)
    for forbidden in [
        "from .core import", "from .release_pipeline import",
        "from .server import", "sqlite3.connect", "ingest_pysus(",
        "from .tool_api import", "SINAN_PUBLIC_REAL_DATA",
    ]:
        assert forbidden not in src


def test_approved_server_returns_only_exact_approved_aggregation(tmp_path, monkeypatch):
    from sinan_mcp import approved_server
    candidate = prepare_candidate(fake_db(tmp_path), agravo="TUBE",
                                  ano=2024, uf="PI", por="sexo")
    path, digest = save_package(tmp_path, package(candidate))
    monkeypatch.setenv("SINAN_APPROVED_RELEASE_FILE", str(path))
    monkeypatch.setenv("SINAN_APPROVED_RELEASE_SHA256", digest)
    monkeypatch.setenv("SINAN_DB_PATH", str(tmp_path / "nonexistent-patient.db"))
    monkeypatch.setenv("SINAN_PUBLIC_REAL_DATA", "1")
    approved_server._release.cache_clear()
    try:
        out = approved_server.consultar_agregado("TUBE", 2024, "PI", "sexo")
        assert out["escopo"]["ano_nao_e_diagnostico"]
        assert out["tipo"] == "contagem_registros_ano_do_arquivo_nao_oficial"
        assert len(out["categorias"]) == 2
        assert "FICTICIO_PRIVADO" not in json.dumps(out)
        assert not (tmp_path / "nonexistent-patient.db").exists()
        for args in [
            ("TUBE", 2024, "PI", "raca_cor"),
            ("TUBE", 2023, "PI", "sexo"),
            ("DENG", 2024, "PI", "sexo"),
            ("TUBE", 2024, "RJ", "sexo"),
        ]:
            with pytest.raises(ValueError, match="não aprovada"):
                approved_server.consultar_agregado(*args)

        from mcp import Client
        async def probe():
            async with Client(approved_server.mcp, raise_exceptions=True) as client:
                names = {t.name for t in (await client.list_tools()).tools}
                assert names == {"sobre_o_servidor", "listar_agregados", "consultar_agregado"}
                response = await client.call_tool("consultar_agregado", {
                    "agravo": "TUBE", "ano_do_arquivo": 2024,
                    "uf": "PI", "por": "sexo",
                })
                assert not response.is_error
                assert response.structured_content["escopo"]["uf"] == "PI"
        asyncio.run(probe())
    finally:
        approved_server._release.cache_clear()


def test_cli_does_not_send_or_publish_private_rows(tmp_path):
    db = fake_db(tmp_path)
    proc = subprocess.run([
        sys.executable, "-m", "sinan_mcp", "--db", str(db), "preparar-agregado",
        "--agravo", "TUBE", "--ano", "2024", "--uf", "PI", "--por", "sexo",
    ], cwd=tmp_path, capture_output=True, text=True, timeout=20)
    assert proc.returncode == 0, proc.stderr
    assert "NÃO APROVADO" in proc.stdout
    assert "FICTICIO_PRIVADO" not in proc.stdout
    assert len(list((tmp_path / "data" / "review-packages").glob("*.candidate.json"))) == 1
