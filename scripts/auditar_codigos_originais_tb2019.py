"""Read original TUBE/2019 DBC locally and audit projected code loss safely.

Uses existing captured DBC and private SQLite; no network or reimport.
Progress output includes only static stages, never sensitive values.
"""
from __future__ import annotations
import json
import sys

from sinan_mcp.tb2019_source_audit import audit_original_projection

def _status(name: str):
    print("ETAPA: " + name, file=sys.stderr, flush=True)

if __name__ == "__main__":
    try:
        result = audit_original_projection(stage=_status)
    except Exception as exc:
        print(json.dumps({"status": "falha", "codigo": type(exc).__name__,
                          "publicacao_autorizada": False}), file=sys.stderr)
        raise SystemExit(2) from None
    print(json.dumps(result, ensure_ascii=False, indent=2))
