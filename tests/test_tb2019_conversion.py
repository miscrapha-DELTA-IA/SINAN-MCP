"""Private converter regression uses fake DBC/DBF and artificial values only."""
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys

import pytest

from sinan_mcp import tb2019_parity as parity
from scripts import _projetar_dbc_tb2019 as worker


def test_synthetic_dbf_to_projected_parquet(tmp_path, monkeypatch):
    pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq
    source = tmp_path / parity.NAME
    source.write_bytes(b"ARTIFICIAL_DBC_TEST_NOT_PATIENT_DATA")
    output_dir = tmp_path / "tmp-private"
    output_dir.mkdir()
    output = output_dir / "projection.parquet"
    monkeypatch.setattr(parity, "verify_local_dbc", lambda root: source.resolve())

    def fake_converter(_src, dest):
        Path(dest).write_bytes(b"ARTIFICIAL_DBF")
    rows = [
        {"ID_MN_RESI": "221100", "CS_SEXO": "M", "CS_RACA": "4", "SITUA_ENCE": "1"},
        {"ID_MN_RESI": "221100", "CS_SEXO": "F", "CS_RACA": None, "SITUA_ENCE": "2"},
    ]
    class FakeDBF:
        field_names = list(rows[0])
        def __iter__(self): return iter(rows)

    monkeypatch.setitem(sys.modules, "pyreaddbc", SimpleNamespace(dbc2dbf=fake_converter))
    monkeypatch.setitem(sys.modules, "dbfread", SimpleNamespace(DBF=lambda *_a, **_kw: FakeDBF()))
    n = worker._project(source, output)
    assert n == 2
    assert pq.read_table(output).to_pylist() == rows
    assert not (output_dir / "TUBEBR19-temporary.dbf").exists()


def test_converter_failure_contains_only_safe_code(tmp_path, monkeypatch):
    pytest.importorskip("pyarrow")
    source = tmp_path / parity.NAME
    source.write_bytes(b"ARTIFICIAL_DBC_TEST_NOT_PATIENT_DATA")
    output_dir = tmp_path / "tmp-private"
    output_dir.mkdir()
    output = output_dir / "projection.parquet"
    monkeypatch.setattr(parity, "verify_local_dbc", lambda root: source.resolve())

    def fake_converter(_src, _dest):
        raise RuntimeError("SENSITIVE_FAKE_RECORD_VALUE")
    monkeypatch.setitem(sys.modules, "pyreaddbc", SimpleNamespace(dbc2dbf=fake_converter))
    monkeypatch.setitem(sys.modules, "dbfread", SimpleNamespace(DBF=lambda *_a, **_kw: None))
    with pytest.raises(worker.ConversionFailure) as exc:
        worker._project(source, output)
    assert exc.value.stage == "DBC_TO_DBF"
    assert exc.value.code == "RuntimeError"
    assert "SENSITIVE_FAKE_RECORD_VALUE" not in str(exc.value)


def test_failure_does_not_repeat_parquet_download(tmp_path, monkeypatch):
    import json
    src = tmp_path / parity.NAME
    src.write_bytes(b"FAKE_CAPTURE")
    monkeypatch.setattr(parity, "verify_local_dbc", lambda _root: src)
    monkeypatch.setattr(parity, "plan_pysus_2019", lambda _root: {
        "parquet_key": "public/data/ftp/sinan/TUBE/2019/_/BR/TUBEBR19.parquet",
        "parquet_bytes_catalogo": 100,
        "parquet_sha256_catalogo": "a" * 64,
    })
    def no_download(*_args, **_kwargs):
        raise AssertionError("Parquet download must occur only after conversion succeeds")
    monkeypatch.setattr(parity, "download_mirror_entry", no_download)
    monkeypatch.setattr(parity.subprocess, "run", lambda *_a, **_kw: SimpleNamespace(
        returncode=2, stderr=json.dumps({
            "status": "error", "stage": "DBF_PROJECT", "code": "AttributeError"
        }) + "\n",
        stdout=""
    ))
    with pytest.raises(RuntimeError, match="etapa=DBF_PROJECT, codigo=AttributeError"):
        parity.compare_local_2019(tmp_path)
