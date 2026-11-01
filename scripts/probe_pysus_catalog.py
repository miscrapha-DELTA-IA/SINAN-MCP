"""Metadata-only forensic probe for PySUS cross-platform discovery.

Run after 'descobrir-pysus' within the same PYSUS_CACHEPATH. Does NOT read
patient Parquet/DBC records and never prints individual health information.
"""
import json
from pathlib import Path
import duckdb
import pysus

db = Path(pysus.CACHEPATH) / "ducklake" / "catalog_sinan.duckdb"
out = {"catalog_exists": db.is_file(), "file_count": None,
       "pilot_2024": {}, "prefix_count": None}
if db.is_file():
    with duckdb.connect(str(db), read_only=True) as con:
        out["file_count"] = con.execute("SELECT count(*) FROM pysus.files").fetchone()[0]
        out["prefix_count"] = con.execute(
            "SELECT count(*) FROM pysus.files WHERE path LIKE 'public/data/ftp/sinan/%'"
        ).fetchone()[0]
        for disease in ("TUBE", "DENG"):
            out["pilot_2024"][disease] = {
                "joined": con.execute(
                    """SELECT count(*) FROM pysus.files f JOIN pysus.dataset_groups g
                       ON f.group_id=g.id WHERE upper(g.name)=? AND f.year=?""",
                    [disease, 2024],
                ).fetchone()[0],
                "prefix": con.execute(
                    """SELECT count(*) FROM pysus.files f JOIN pysus.dataset_groups g
                       ON f.group_id=g.id WHERE upper(g.name)=? AND f.year=?
                       AND f.path LIKE 'public/data/ftp/sinan/%'""",
                    [disease, 2024],
                ).fetchone()[0],
            }
print(json.dumps(out, ensure_ascii=False, indent=2))
