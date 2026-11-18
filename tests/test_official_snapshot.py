"""All tests use artificial bytes and a fake FTP; never download microdata."""
from ftplib import error_perm
import hashlib
from pathlib import Path

import pytest
from sinan_mcp import official_snapshot as snap


class FakeFTP:
    def __init__(self, payload: bytes, *, size=None, mdtm=None, error=False):
        self.payload = payload
        self.current = ""
        self.size_field = len(payload) if size is None else size
        self.mdtm = snap.OBSERVED_MDTM if mdtm is None else mdtm
        self.error = error

    def connect(self, host, port, timeout):
        assert host == "ftp.datasus.gov.br"
        assert port == 21

    def login(self): pass

    def cwd(self, path): self.current = path.rsplit("/", 1)[-1]

    def nlst(self):
        if self.current == "FINAIS": return [snap.NAME]
        return []

    def voidcmd(self, cmd): assert cmd == "TYPE I"

    def size(self, name): assert name == snap.NAME; return self.size_field

    def sendcmd(self, cmd): return "213 " + self.mdtm

    def retrbinary(self, command, callback, blocksize):
        assert command == "RETR " + snap.NAME
        if self.error: raise error_perm("450 simulated transfer failure")
        for offset in range(0, len(self.payload), blocksize):
            callback(self.payload[offset:offset + blocksize])

    def close(self): pass


def test_official_snapshot_hash_and_manifest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = b"TEST_BYTES_FICTICIOS" * 30
    monkeypatch.setattr(snap, "OBSERVED_SIZE", len(payload))
    root = Path("data/private/tb2019")
    result = snap.capture_tb_2019(ftp_factory=lambda: FakeFTP(payload))
    assert result["sha256_recebido"] == hashlib.sha256(payload).hexdigest()
    assert result["publicacao_autorizada"] is False
    assert result["equivalencia_com_parquet_pysus"] is False
    assert (root / snap.NAME).read_bytes() == payload
    assert (root / "TUBEBR19.manifest.json").is_file()
    with pytest.raises(FileExistsError):
        snap.capture_tb_2019(ftp_factory=lambda: FakeFTP(payload))


def test_failure_cleans_partial_snapshot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = b"ANOTHER_FAKE" * 10
    monkeypatch.setattr(snap, "OBSERVED_SIZE", len(payload))
    with pytest.raises(error_perm):
        snap.capture_tb_2019(ftp_factory=lambda: FakeFTP(payload, error=True))
    assert not list((tmp_path / "data").rglob("*.dbc"))
    assert not list((tmp_path / "data").rglob("*.partial"))


def test_changed_metadata_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = b"FAKE" * 10
    monkeypatch.setattr(snap, "OBSERVED_SIZE", len(payload))
    with pytest.raises(RuntimeError, match="metadados fixados"):
        snap.capture_tb_2019(ftp_factory=lambda: FakeFTP(payload, mdtm="20200101000000"))
    assert not (tmp_path / "data").exists()


def test_outside_gitignored_folder_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="./data"):
        snap.capture_tb_2019(root=tmp_path / "outside", ftp_factory=lambda: None)
