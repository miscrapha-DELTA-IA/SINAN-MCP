"""Fixed public mirror snapshot for the private TUBE 2024 research pilot."""
from pathlib import Path
from tempfile import TemporaryDirectory

SOURCE_TYPE = "pysus-snapshot-parquet"
KEY = "public/data/ftp/sinan/TUBE/2024/_/BR/TUBEBR24.parquet"
SOURCE_URL = "https://nbg1.your-objectstorage.com/pysus/" + KEY
SHA256 = "eb9231b27ad160fb54c1c4fb78735fee566a440eaffd21758bdc197d209c93b1"
SIZE = 4062325
COLUMNS = ["ID_MN_RESI", "CS_SEXO", "CS_RACA", "SITUA_ENCE"]


def import_snapshot(db_path: str | Path) -> dict:
    from .catalog_import import download_mirror_entry
    from .core import _import_rows
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Instale pyarrow para importar o piloto.") from exc

    with TemporaryDirectory(prefix="sinan-tube-") as tmp:
        parquet = Path(tmp) / "TUBEBR24.parquet"
        digest, _ = download_mirror_entry({"key": KEY, "sha256": SHA256, "size": SIZE}, parquet)
        with pq.ParquetFile(parquet) as reader:
            if not set(COLUMNS).issubset(reader.schema_arrow.names):
                raise ValueError("Layout incompatível com o piloto TUBE 2024")
            rows = (row for batch in reader.iter_batches(batch_size=2048, columns=COLUMNS)
                    for row in batch.to_pylist())
            return _import_rows(db_path, rows, agravo="TUBE", ano=2024, status="desconhecido",
                                identificador=SOURCE_URL, tipo_fonte=SOURCE_TYPE, sha256=digest)
