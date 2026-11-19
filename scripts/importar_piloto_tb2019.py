"""Import TUBE/2019 four-field research projection into local-only SQLite.

Run from repository root:
  .venv/Scripts/python.exe -m scripts.importar_piloto_tb2019

Rechecks official DBC hash, cross-source concordance and Parquet SHA-256.
No patient records or counts are printed. No public service is modified.
"""
from __future__ import annotations
import json
from sinan_mcp.tb2019_private_import import import_verified_research_2019

if __name__ == "__main__":
    print(json.dumps(import_verified_research_2019(), ensure_ascii=False, indent=2))
