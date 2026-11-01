"""Read-only inspection of the local PySUS SINAN catalog, without microdata."""
from pathlib import Path
import json
import duckdb
import pysus
from pysus.api.ducklake.catalog.adapters import BaseAdapter

path = Path(BaseAdapter.cache_dir) / "catalog_sinan.duckdb"
result = {"catalog_file": str(path), "present": path.is_file()}
if path.is_file():
    result["bytes"] = path.stat().st_size
    try:
        with duckdb.connect(str(path), read_only=True) as conn:
            tables = conn.execute(
                "SELECT table_schema, table_name FROM information_schema.tables "
                "WHERE table_schema = 'pysus' ORDER BY table_name"
            ).fetchall()
            result["tables"] = [list(t) for t in tables]
            if ("pysus", "files") in tables:
                result["all_files"] = conn.execute("SELECT COUNT(*) FROM pysus.files").fetchone()[0]
                result["year_2024_count"] = conn.execute(
                    "SELECT COUNT(*) FROM pysus.files WHERE year=2024"
                ).fetchone()[0]
                result["samples_2024"] = conn.execute(
                    "SELECT path FROM pysus.files WHERE year=2024 ORDER BY path LIMIT 8"
                ).fetchall()
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:350]
print(json.dumps(result, ensure_ascii=False, indent=2))
