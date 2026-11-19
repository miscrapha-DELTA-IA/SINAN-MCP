"""Isolated synthetic tests: no real SINAN data, no external downloads."""
from pathlib import Path
import shutil

import pytest

from sinan_mcp import tb2019_private_import as private


def fake_evidence(*, equal=True):
    return {
        "multiconjunto_4_campos_igual": equal,
        "dbc_sha256_recebido": "7a00e29a5a309b794e21f1a650d3b04b9d3cb05fcc6ef8c9feefab3a961c9144",
        "parquet_sha256_verificado": private.PARQUET_SHA256,
        "parquet_key": private.PARQUET_KEY,
        "equivalencia_integral_verificada": False,
        "publicacao_autorizada": False,
    }


def test_refuses_nonprivate_path_without_reading_source(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="SQLite privado"):
        private.import_verified_research_2019(tmp_path / "outside.sqlite3")


def test_refuses_unmatched_projection_before_network_or_sqlite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    base = tmp_path / "data/private/tb2019"
    base.mkdir(parents=True)
    monkeypatch.setattr(private, "verify_local_dbc", lambda root: base / "TUBEBR19.dbc")
    monkeypatch.setattr(private, "compare_local_2019",
                        lambda root: fake_evidence(equal=False))
    monkeypatch.setattr(private, "download_mirror_entry",
                        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network forbidden")))
    with pytest.raises(ValueError, match="Concordancia"):
        private.import_verified_research_2019()
    assert not list(base.glob("*.sqlite3"))


def test_refuses_changed_parquet_hash_before_ingest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    base = tmp_path / "data/private/tb2019"
    base.mkdir(parents=True)
    monkeypatch.setattr(private, "verify_local_dbc", lambda root: base / "TUBEBR19.dbc")
    monkeypatch.setattr(private, "compare_local_2019", lambda root: fake_evidence())
    # Install test's tiny optional PyArrow dependency only if available.
    pytest.importorskip("pyarrow.parquet")
    monkeypatch.setattr(private, "download_mirror_entry",
                        lambda *_args, **_kwargs: ("0" * 64, private.PARQUET_BYTES))
    with pytest.raises(ValueError, match="Parquet diverge"):
        private.import_verified_research_2019()
    assert not list(base.glob("*.sqlite3"))


def test_private_research_import_stays_unknown(tmp_path, monkeypatch):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    from sinan_mcp.core import catalogo, db_connect_readonly

    monkeypatch.chdir(tmp_path)
    root = tmp_path / "data/private/tb2019"
    root.mkdir(parents=True)
    monkeypatch.setattr(private, "verify_local_dbc", lambda _root: root / "TUBEBR19.dbc")
    monkeypatch.setattr(private, "compare_local_2019", lambda _root: fake_evidence())

    fixture = tmp_path / "ficticio.parquet"
    pq.write_table(pa.table({
        "ID_MN_RESI": ["221100", "221100", "221100"],
        "CS_SEXO": ["F", "M", "F"],
        "CS_RACA": ["4", "1", "4"],
        "SITUA_ENCE": ["1", "2", "1"],
        "NOME_PESSOA": ["TESTE_FICTICIO_1", "TESTE_FICTICIO_2", "TESTE_FICTICIO_3"],
    }), fixture)

    def fake_download(entry, dst):
        assert entry["sha256"] == private.PARQUET_SHA256
        assert entry["key"] == private.PARQUET_KEY
        shutil.copyfile(fixture, dst)
        return private.PARQUET_SHA256, private.PARQUET_BYTES

    monkeypatch.setattr(private, "download_mirror_entry", fake_download)
    report = private.import_verified_research_2019()
    assert report["status_da_fonte_no_sqlite"] == "desconhecido"
    assert report["publicacao_autorizada"] is False
    assert "registros_importados" not in report
    database = root / "piloto-tb2019.sqlite3"
    records = catalogo(database)["bases_importadas"]
    assert len(records) == 1
    assert records[0]["status"] == "desconhecido"
    assert records[0]["tipo_fonte"] == private.SOURCE_TYPE
    with db_connect_readonly(database) as con:
        assert con.execute("SELECT COUNT(*) FROM registros").fetchone()[0] == 3
    assert b"TESTE_FICTICIO" not in database.read_bytes()
    assert not list(root.glob("piloto-import-*"))
