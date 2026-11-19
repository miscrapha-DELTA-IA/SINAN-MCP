"""Fail-closed local TUBE/2019 projection import for an unapproved research SQLite.

Not an MCP tool. Does not disclose cells and never marks source final.
The DBC-PySUS concordance must be independently re-run before import.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from .tb2019_parity import FIELDS, verify_local_dbc, compare_local_2019
from .catalog_import import download_mirror_entry
from .core import _import_rows

PARQUET_KEY = "public/data/ftp/sinan/TUBE/2019/_/BR/TUBEBR19.parquet"
PARQUET_BYTES = 3_603_114
PARQUET_SHA256 = "7c599143671bb8bd895e2dbd39a325682b12d9fd5a024fcec101bb76ed0fc277"
PARQUET_URL = "https://nbg1.your-objectstorage.com/pysus/" + PARQUET_KEY
SOURCE_TYPE = "pysus-tb2019-verified-four-field-projection"
PRIVATE_ROOT = Path("./data/private/tb2019")


def import_verified_research_2019(db_path: str | Path = "./data/private/tb2019/piloto-tb2019.sqlite3") -> dict:
    """Verify parity then import 4 fields. No public data access or final flag."""
    root = PRIVATE_ROOT.resolve()
    db_path = Path(db_path).resolve()
    if not db_path.is_relative_to(root) or db_path.suffix != ".sqlite3":
        raise ValueError("SQLite privado deve ficar em ./data/private/tb2019/")

    verify_local_dbc(root)
    check = compare_local_2019(root)
    if (check.get("multiconjunto_4_campos_igual") is not True
            or check.get("parquet_sha256_verificado") != PARQUET_SHA256
            or check.get("parquet_key") != PARQUET_KEY
            or check.get("equivalencia_integral_verificada") is not False
            or check.get("publicacao_autorizada") is not False):
        raise ValueError("Concordancia da projecao de 4 campos nao comprovada: importacao recusada.")

    import pyarrow.parquet as pq
    with TemporaryDirectory(prefix="piloto-import-", dir=str(root)) as temp:
        mirror = Path(temp) / "TUBEBR19.parquet"
        actual, size = download_mirror_entry(
            {"key": PARQUET_KEY, "size": PARQUET_BYTES, "sha256": PARQUET_SHA256},
            mirror,
        )
        if actual != PARQUET_SHA256 or size != PARQUET_BYTES:
            raise ValueError("Parquet diverge dos bytes fixados: importacao recusada.")

        with pq.ParquetFile(mirror) as reader:
            original = reader.schema_arrow.names
            names = {str(n).upper(): n for n in original}
            if len(names) != len(original) or not all(name in names for name in FIELDS):
                raise ValueError("Parquet TUBE/2019 sem os quatro campos exigidos.")
            selected = [names[name] for name in FIELDS]

            def rows():
                for batch in reader.iter_batches(batch_size=2048, columns=selected):
                    for row in batch.to_pylist():
                        yield {name: row[selected[i]] for i, name in enumerate(FIELDS)}

            _import_rows(
                db_path, rows(), agravo="TUBE", ano=2019,
                identificador=PARQUET_URL, tipo_fonte=SOURCE_TYPE,
                status="desconhecido", sha256=actual,
            )
    return {
        "stage": "PRIVATE_RESEARCH_IMPORT_NOT_HOMOLOGATED",
        "ano_do_arquivo": 2019,
        "tipo_fonte": SOURCE_TYPE,
        "dbc_sha256": check["dbc_sha256_recebido"],
        "parquet_sha256": PARQUET_SHA256,
        "projecao_4_campos_concordante": True,
        "status_da_fonte_no_sqlite": "desconhecido",
        "equivalencia_integral_verificada": False,
        "publicacao_autorizada": False,
        "aviso": "SQLite privado gerado. Não enviar o arquivo, microdados ou candidatos de agregação a serviços públicos."
    }
