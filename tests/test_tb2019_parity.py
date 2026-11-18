"""Synthetic-only regression for TUBE/2019 private projection concordance."""
import hashlib
import json

import pytest

from sinan_mcp import tb2019_parity as parity


def _entry(*, key="public/data/ftp/sinan/TUBE/2019/_/BR/TUBEBR19.parquet",
           sha="a" * 64, size=10000):
    return {"key": key, "name": key.rsplit("/", 1)[-1], "size": size, "sha256": sha}


def test_unambiguous_pysus_manifest_only():
    picked = parity._choose_entry([_entry()])
    assert picked["size"] == 10000
    with pytest.raises(ValueError):
        parity._choose_entry([])
    with pytest.raises(ValueError):
        parity._choose_entry([_entry(), _entry()])
    with pytest.raises(ValueError):
        parity._choose_entry([_entry(sha=None)])
    with pytest.raises(ValueError):
        parity._choose_entry([_entry(key="public/data/ftp/sinan/TUBE/2024/_/BR/TUBEBR19.parquet")])


@pytest.mark.parametrize(("raw", "canonical"), [
    (None, None), (" ", None), ("NaN", None), (float("nan"), None),
    (" 4 ", "4"), (4.0, "4"), ("004", "004"), ("10.0", "10"),
    ("00.0", "00"), ("F ", "F"),
])
def test_normalization_codes(raw, canonical):
    assert parity._norm(raw) == canonical


def test_snapshot_pin_and_manifest(tmp_path, monkeypatch):
    raw = b"FAKE_DBC_NOT_REAL_HEALTH_DATA"
    monkeypatch.setattr(parity, "PINNED_SHA256", hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(parity, "OBSERVED_SIZE", len(raw))
    root = tmp_path / "private"
    root.mkdir()
    src = root / parity.NAME
    src.write_bytes(raw)
    manifest = {
        "sha256_recebido": parity.PINNED_SHA256,
        "bytes_observados": len(raw),
        "ano_do_arquivo": parity.YEAR,
        "stage": "OFFICIAL_FTP_FILE_RECEIVED_NOT_HOMOLOGATED",
    }
    (root / "TUBEBR19.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert parity.verify_local_dbc(root) == src
    src.write_bytes(raw + b"x")
    with pytest.raises(ValueError, match="SHA-256 ou tamanho"):
        parity.verify_local_dbc(root)


def test_multiset_parquet_detects_duplicate_and_mismatch(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    cols = list(parity.FIELDS)
    a = [("221100", "M", "4", "1"), ("221100", "M", "4", "1"), ("221100", "F", "1", "2")]
    b = [("221100", "F", "1", "2"), ("221100", "M", "4", "1"), ("221100", "M", "4", "1")]
    c = [("221100", "F", "1", "2"), ("221100", "M", "4", "1"), ("221100", "M", "4", "10")]
    def write(rows, path):
        pq.write_table(pa.table({n: [row[i] for row in rows] for i, n in enumerate(cols)}), path)
    p1, p2, p3 = (tmp_path / name for name in ("a.parquet", "b.parquet", "c.parquet"))
    write(a, p1)
    write(b, p2)
    write(c, p3)
    assert parity.compare_projected_parquets(p1, p2, tmp_path / "match.sqlite3") is True
    assert parity.compare_projected_parquets(p1, p3, tmp_path / "mismatch.sqlite3") is False


def test_absent_columns_fail_closed(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    path = tmp_path / "wrong.parquet"
    pq.write_table(pa.table({"CS_SEXO": ["M"]}), path)
    with pytest.raises(ValueError, match="quatro campos"):
        list(parity._projected_rows(path))
