"""Narrow, read-only DuckLake catalog lookup for a PySUS 2.11.x Windows issue.

This queries public *metadata* only. It never opens clinical microdata files.
The SQL is constant and parameterized, and results are only filenames.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

MAX_FILES = 40
_SQL = """SELECT f.path FROM pysus.files AS f
          JOIN pysus.dataset_groups AS g ON f.group_id = g.id
          WHERE upper(g.name) = ? AND f.year = ?
            AND f.path LIKE 'public/data/ftp/sinan/%'
          ORDER BY f.path LIMIT ?"""


def catalog_path() -> Path:
    root = Path(os.environ.get("PYSUS_CACHEPATH", str(Path.home() / "pysus")))
    return root.expanduser() / "ducklake" / "catalog_sinan.duckdb"


def _validate(agravo: str, ano: int) -> None:
    if not isinstance(agravo, str) or not re.fullmatch(r"[A-Z]{4}", agravo):
        raise ValueError("Agravo invalido")
    if not isinstance(ano, int) or not 1980 <= ano <= 2100:
        raise ValueError("Ano invalido")


def _names(records) -> list[str]:
    if len(records) > MAX_FILES:
        raise ValueError("Muitos arquivos no catalogo local")
    names = []
    for (path,) in records:
        p = str(path).replace("\\", "/")
        if not p.startswith("public/data/ftp/sinan/") or not p.endswith(".parquet"):
            continue
        names.append(p.rsplit("/", 1)[-1])
    return names


def lookup_local(agravo: str, ano: int) -> list[str]:
    """Read the catalog in a fresh process, without any PySUS engine open."""
    _validate(agravo, ano)
    path = catalog_path()
    if not path.is_file():
        return []
    import duckdb
    with duckdb.connect(str(path), read_only=True) as connection:
        rows = connection.execute(_SQL, [agravo, ano, MAX_FILES + 1]).fetchall()
    return _names(rows)


def lookup_after_pysus(agravo: str, ano: int) -> list[str]:
    """Reuse PySUS's already-open DuckDB engine; do not reopen a locked file."""
    _validate(agravo, ano)
    path = catalog_path()
    if not path.is_file():
        return []
    try:
        from pysus.api.ducklake.catalog.adapters import _SHARED_ENGINES
    except ImportError:
        _SHARED_ENGINES = {}
    engine = _SHARED_ENGINES.get(str(path.resolve()))
    if engine is not None:
        # The PySUS engine is read/write, but this method exclusively uses SELECT.
        with engine.connect() as connection:
            rows = connection.exec_driver_sql(
                _SQL, (agravo, ano, MAX_FILES + 1)
            ).fetchall()
        return _names(rows)
    completed = subprocess.run(
        [sys.executable, "-m", "sinan_mcp.catalog_fallback", "--agravo", agravo,
         "--ano", str(ano)],
        capture_output=True, text=True, timeout=25, check=False,
    )
    if completed.returncode:
        raise RuntimeError("Falha ao consultar metadados locais no subprocesso")
    return json.loads(completed.stdout)["arquivos"]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Consulta apenas metadados DuckLake")
    parser.add_argument("--agravo", required=True)
    parser.add_argument("--ano", required=True, type=int)
    args = parser.parse_args()
    print(json.dumps({"arquivos": lookup_local(args.agravo, args.ano)},
                     ensure_ascii=False))
