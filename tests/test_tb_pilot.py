"""Offline regression for source identity and repeatable import of the pilot."""
import hashlib
import shutil
from contextlib import closing

import pytest

from sinan_mcp import catalog_import, tb_pilot
from sinan_mcp.core import catalogo, db_connect_readonly
from sinan_mcp.tool_api import contagens_publicas


def test_pilot_provenance_and_reimport(tmp_path, monkeypatch):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    source = tmp_path / "fixture.parquet"
    pq.write_table(pa.table({"ID_MN_RESI": ["221100"], "CS_SEXO": ["F"],
                             "CS_RACA": ["4"], "SITUA_ENCE": ["1"],
                             "IGNORED": ["fixture only"]}), source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    downloads = []

    def fetch(entry, destination):
        assert entry == {"key": tb_pilot.KEY, "sha256": tb_pilot.SHA256, "size": tb_pilot.SIZE}
        downloads.append(destination)
        shutil.copyfile(source, destination)
        return digest, source.stat().st_size

    monkeypatch.setattr(catalog_import, "download_mirror_entry", fetch)
    db = tmp_path / "test.sqlite3"
    for _ in range(2):
        assert tb_pilot.import_snapshot(db)["registros_importados"] == 1
    assert all(not path.exists() for path in downloads)
    assert len(catalogo(db)["bases_importadas"]) == 1
    with closing(db_connect_readonly(db)) as con:
        assert con.execute("SELECT COUNT(*) FROM registros").fetchone()[0] == 1
    monkeypatch.setenv("SINAN_PUBLIC_REAL_DATA", "1")
    result = contagens_publicas(db, agravo="TUBE", ano_inicio=2024, ano_fim=2024,
                                uf="PI", por="sexo")
    assert result["resultado"]["status"] == "nao_divulgavel"
    prov = result["proveniencia"]
    assert prov["fingerprint_sha256"] == digest
    assert prov["fingerprint_tipo"] == "sha256_arquivo"
    assert prov["origem_referencia"] == tb_pilot.SOURCE_URL
