"""Offline import safety tests. Never retrieve actual epidemiological records."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from sinan_mcp import catalog_import as ci
from sinan_mcp import pysus_gateway as gateway
from sinan_mcp.core import catalogo


def _entry(name="TUBEBR24.parquet", sha=None, size=300):
    return {
        "key": "public/data/ftp/sinan/TUBE/2024/BR/" + name,
        "name": name,
        "size": size,
        "sha256": sha,
    }


def test_manifest_validation_is_restricted_and_bounded():
    valid = "public/data/ftp/sinan/TUBE/2024/BR/TUBEBR24.parquet"
    results = ci._validate_manifest([(valid, 1234, "a" * 64)])
    assert results[0] == _entry(sha="a" * 64, size=1234)
    with pytest.raises(ValueError):
        ci._validate_manifest([("public/data/ftp/sinan/../../secret.parquet", 5, None)])
    with pytest.raises(ValueError):
        ci._validate_manifest([("https://example.org/clinical.parquet", 5, None)])
    with pytest.raises(ValueError):
        ci._validate_manifest([(valid, 0, None)])
    with pytest.raises(ValueError):
        ci._validate_manifest([(valid, ci.MAX_FILE_BYTES + 1, None)])
    with pytest.raises(ValueError):
        ci._validate_manifest([(valid, 99, "not-a-sha")])


def test_manifest_reads_only_matching_public_ftp_metadata(tmp_path, monkeypatch):
    duckdb = pytest.importorskip("duckdb")
    cache = tmp_path / "ducklake"
    cache.mkdir()
    path = cache / "catalog_sinan.duckdb"
    with duckdb.connect(str(path)) as conn:
        conn.execute("CREATE SCHEMA pysus")
        conn.execute("CREATE TABLE pysus.dataset_groups (id INTEGER, name VARCHAR)")
        conn.execute("CREATE TABLE pysus.files (path VARCHAR, group_id INTEGER, year INTEGER, size BIGINT, sha256 VARCHAR)")
        conn.execute("INSERT INTO pysus.dataset_groups VALUES (1, 'TUBE'), (2, 'DENG')")
        conn.execute("INSERT INTO pysus.files VALUES (?, 1, 2024, 1234, ?)",
                     [_entry()["key"], "a" * 64])
        conn.execute("INSERT INTO pysus.files VALUES (?, 1, 2024, 1234, ?)",
                     ["public/data/dadosgov/sinan/TUBE/2024/not_ftp.parquet", None])
        conn.execute("INSERT INTO pysus.files VALUES (?, 2, 2024, 1234, ?)",
                     ["public/data/ftp/sinan/DENG/2024/DENGBR24.parquet", None])
    monkeypatch.setenv("PYSUS_CACHEPATH", str(tmp_path))
    entries = ci.manifest("TUBE", 2024)
    assert len(entries) == 1
    assert entries[0]["name"] == "TUBEBR24.parquet"
    assert entries[0]["size"] == 1234


def test_catalog_only_fallback_import_and_cleanup(tmp_path, monkeypatch):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    src = tmp_path / "fictional.parquet"
    pq.write_table(pa.table({
        "CS_SEXO": ["F"] * 20,
        "CS_RACA": ["4"] * 20,
        "ID_MN_RESI": ["221100"] * 20,
        "SITUA_ENCE": ["1"] * 20,
        "NM_PACIENT": ["FICTICIO"] * 20,
    }), src)
    size = src.stat().st_size
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    entry = _entry(size=size, sha=digest)
    monkeypatch.setattr(ci, "manifest", lambda agravo, ano: [entry])
    paths = []

    def synthetic_download(e, dst):
        paths.append(dst)
        shutil.copyfile(src, dst)
        return digest, size

    monkeypatch.setattr(ci, "_download", synthetic_download)
    monkeypatch.setattr(gateway, "_pysus", lambda: SimpleNamespace(
        sinan=lambda **kwargs: []))
    db = tmp_path / "private.sqlite3"
    result = gateway.importar(db, agravo="TUBE", ano=2024, source="catalog")
    assert result["registros_importados"] == 20
    assert result["arquivos_processados"] == 1
    assert result["arquivos_brutos_removidos"] is True
    assert all(not p.exists() for p in paths)
    assert b"FICTICIO" not in db.read_bytes()
    assert catalogo(db)["bases_importadas"][0]["tipo_fonte"] == "pysus-catalog-verified"
    with pytest.raises(ValueError, match="origem solicitada"):
        gateway.importar(db, agravo="TUBE", ano=2024, source="origin")
    assert catalogo(db)["bases_importadas"][0]["n_registros"] == 20


def test_network_reader_requires_real_checksum(tmp_path, monkeypatch):
    pytest.importorskip("pysus")
    import io
    from urllib import request

    payload = b"fictional-parquet-test-bytes"
    digest = hashlib.sha256(payload).hexdigest()
    e = _entry(size=len(payload), sha=digest)

    class Reply(io.BytesIO):
        status = 200

        def geturl(self):
            return "https://nbg1.your-objectstorage.com/pysus/public/data/ftp/sinan/TUBE/2024/BR/TUBEBR24.parquet"

    monkeypatch.setattr(ci, "_open_strict", lambda req, timeout: Reply(payload))
    output = tmp_path / "test.parquet"
    assert ci._download(e, output) == (digest, len(payload))
    assert output.read_bytes() == payload
    with pytest.raises(ValueError, match="SHA256"):
        ci._download({**e, "sha256": "0" * 64}, tmp_path / "bad.parquet")


def test_no_implicit_remote_download_on_discovery(tmp_path, monkeypatch):
    monkeypatch.setenv("PYSUS_CACHEPATH", str(tmp_path))
    assert ci.manifest("TUBE", 2024) == []



def test_redirect_rejected_before_following_host():
    blocker = ci._RejectRedirect()
    with pytest.raises(RuntimeError, match="Redirecionamento"):
        blocker.redirect_request(None, None, 302, "found", {},
                                 "http://127.0.0.1/internal")


def test_catalog_rejects_unsafe_path_segment():
    with pytest.raises(ValueError, match="Caminho"):
        ci._validate_manifest([(
            "public/data/ftp/sinan/TUBE/2024/%2f/private.parquet", 100, None
        )])


def test_transient_transfer_retry_cleans_partial_file(tmp_path, monkeypatch):
    pytest.importorskip("pysus")
    import io
    from urllib.error import URLError

    payload = b"fictional-bytes-only"
    e = _entry(size=len(payload), sha=hashlib.sha256(payload).hexdigest())
    calls = []
    delays = []

    class Reply(io.BytesIO):
        status = 200

        def geturl(self):
            return "https://nbg1.your-objectstorage.com/pysus/public/data/ftp/sinan/TUBE/2024/BR/TUBEBR24.parquet"

    def attempt(request, *, timeout):
        calls.append(timeout)
        if len(calls) == 1:
            raise URLError("simulated transient outage")
        return Reply(payload)

    monkeypatch.setattr(ci, "_open_strict", attempt)
    monkeypatch.setattr(ci.time, "sleep", lambda s: delays.append(s))
    file = tmp_path / "retry.parquet"
    assert ci._download(e, file) == (e["sha256"], len(payload))
    assert len(calls) == 2 and delays == [1]
    assert file.read_bytes() == payload


def test_permanent_http_error_never_retried(tmp_path, monkeypatch):
    pytest.importorskip("pysus")
    from urllib.error import HTTPError

    def unavailable(request, *, timeout):
        raise HTTPError("https://nbg1.your-objectstorage.com", 404,
                        "not found", {}, None)

    monkeypatch.setattr(ci, "_open_strict", unavailable)
    monkeypatch.setattr(ci.time, "sleep",
                        lambda *_: pytest.fail("Permanent error must not retry"))
    target = tmp_path / "no.parquet"
    with pytest.raises(RuntimeError, match="permanente"):
        ci._download(_entry(size=300), target)
    assert not target.exists()



def test_download_does_not_delete_preexisting_destination(tmp_path, monkeypatch):
    pytest.importorskip("pysus")
    target = tmp_path / "preexisting.parquet"
    target.write_bytes(b"DO-NOT-TOUCH")
    monkeypatch.setattr(ci, "_open_strict",
                        lambda *_args, **_kwargs: pytest.fail("must not connect"))
    with pytest.raises(FileExistsError):
        ci._download(_entry(size=300), target)
    assert target.read_bytes() == b"DO-NOT-TOUCH"
