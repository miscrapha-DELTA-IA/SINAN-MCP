"""Artificial-only header tests: never inspect health files or expose rows."""
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

from sinan_mcp import tb2019_dbf_header as audit
from sinan_mcp import tb2019_parity as parity


def fake_modules(monkeypatch, *, length=2):
    def converter(_dbc, target):
        Path(target).write_bytes(b"FAKE_DBF_HEADER_ONLY")
    fields = [
        SimpleNamespace(name=name, type="C", length=length if name == "SITUA_ENCE" else 6)
        for name in parity.FIELDS
    ]
    class FakeDBF:
        def __init__(self, *args, **kwargs):
            assert kwargs.get("load") is False
            self.fields = fields
        def __iter__(self):
            raise AssertionError("Never iterate DBF health rows")
    monkeypatch.setitem(sys.modules, "pyreaddbc", SimpleNamespace(dbc2dbf=converter))
    monkeypatch.setitem(sys.modules, "dbfread", SimpleNamespace(DBF=FakeDBF))


def test_header_reports_only_four_field_names_and_widths(tmp_path, monkeypatch):
    file = tmp_path / "TUBEBR19.dbc"
    file.write_bytes(b"FAKE_HEADER")
    monkeypatch.setattr(audit, "verify_local_dbc", lambda _root: file)
    fake_modules(monkeypatch, length=2)
    output = audit.inspect_header(tmp_path)
    assert output["campo_situacao_10_cabe_em_largura"] is True
    assert set(output["campos"]) == set(parity.FIELDS)
    assert output["linhas_lidas"] is False
    assert output["publicacao_autorizada"] is False
    assert not list(tmp_path.rglob("*.dbf"))


def test_one_byte_end_code_width_is_flagged_without_claiming_truncation(tmp_path, monkeypatch):
    file = tmp_path / "TUBEBR19.dbc"
    file.write_bytes(b"FAKE_HEADER")
    monkeypatch.setattr(audit, "verify_local_dbc", lambda _root: file)
    fake_modules(monkeypatch, length=1)
    output = audit.inspect_header(tmp_path)
    assert output["campo_situacao_10_cabe_em_largura"] is False
    assert output["compatibilidade_temporal_do_dicionario_verificada"] is False


def test_refuse_if_header_lacks_required_field(tmp_path, monkeypatch):
    file = tmp_path / "TUBEBR19.dbc"
    file.write_bytes(b"FAKE_HEADER")
    monkeypatch.setattr(audit, "verify_local_dbc", lambda _root: file)
    fake_modules(monkeypatch)
    class Missing:
        def __init__(self, *args, **kwargs):
            self.fields = [SimpleNamespace(name="CS_SEXO", type="C", length=1)]
    monkeypatch.setitem(sys.modules, "dbfread", SimpleNamespace(DBF=Missing))
    with pytest.raises(ValueError, match="quatro variaveis"):
        audit.inspect_header(tmp_path)
    assert not list(tmp_path.rglob("*.dbf"))
