"""Direct administrative Parquet import for platforms where PySUS discovery fails.

Never exposes source paths, row data or import operations as MCP tools.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from .core import _import_rows, validate_agravo

MAX_IMPORT_BYTES = 2 * 1024**3


def importar_parquet(db_path: str | Path, arquivo: str | Path, *, agravo: str,
                     ano: int, status: str = "desconhecido") -> dict:
    path = Path(arquivo).expanduser().resolve(strict=True)
    if path.suffix.lower() != ".parquet" or not path.is_file():
        raise ValueError("Selecione um arquivo .parquet local regular")
    if path.stat().st_size > MAX_IMPORT_BYTES:
        raise ValueError("Parquet acima do limite de 2 GiB; processe em partes verificadas")
    a = validate_agravo(agravo)
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Instale o extra de ingestão: pip install -e '.[ingest]'") from exc
    pf = pq.ParquetFile(path)
    columns = set(pf.schema_arrow.names)
    approved = {"ID_MN_RESI", "MUNIC_RES", "CS_SEXO", "CS_RACA", "SITUA_ENCE"}
    if not {x.upper().strip() for x in columns} & approved:
        raise ValueError("Parquet sem colunas SINAN esperadas; verifique o dicionário do agravo")
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)

    def rows():
        for batch in pf.iter_batches(batch_size=2048):
            yield from batch.to_pylist()

    return _import_rows(db_path, rows(), agravo=a, ano=ano,
                        identificador=path.name, tipo_fonte="parquet-local",
                        status=status, sha256=checksum.hexdigest())
