"""Local Parquet import; no remote data, no PySUS needed."""
import pytest
from sinan_mcp.core import contar, catalogo
from sinan_mcp.local_files import importar_parquet


def test_import_local_parquet_no_direct_identifiers(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    source = tmp_path / "TUBEBR24.parquet"
    pq.write_table(pa.table({
        "ID_MN_RESI": ["221100"] * 48,
        "CS_RACA": ["4"] * 48,
        "CS_SEXO": ["F"] * 48,
        "SITUA_ENCE": ["2"] * 48,
        "NM_PACIENT": ["FICTICIO_NAO_PUBLICAR"] * 48
    }), source)
    db = tmp_path / "research.db"
    record = importar_parquet(db, source, agravo="TUBE", ano=2024)
    assert record["registros_importados"] == 48
    assert catalogo(db)["bases_importadas"][0]["tipo_fonte"] == "parquet-local"
    assert contar(db, agravo="TUBE", ano_inicio=2024, ano_fim=2024,
                  uf="PI", por="raca_cor")["dados"][0]["notificacoes"] == 48
    assert b"FICTICIO_NAO_PUBLICAR" not in db.read_bytes()


def test_parquet_rejects_unexpected_schema_and_preserves_db(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    source = tmp_path / "wrong.parquet"
    pq.write_table(pa.table({"NOME": ["x"], "CPF": ["000"]}), source)
    with pytest.raises(ValueError, match="sem colunas SINAN"):
        importar_parquet(tmp_path / "output.db", source, agravo="TUBE", ano=2024)
