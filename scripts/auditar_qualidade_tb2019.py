"""Run offline privacy-preserving quality preflight on local TUBE/2019 pilot.

Windows PowerShell, from repository root:
    .\.venv\Scripts\python.exe -m scripts.auditar_qualidade_tb2019

Reads SQLite read-only. Writes only a locally ignored quality flags report.
Never prints counts, individual records, or stratum distributions.
"""
from __future__ import annotations
import json
from sinan_mcp.tb2019_quality import audit_private_tb2019

if __name__ == "__main__":
    print(json.dumps(audit_private_tb2019(), ensure_ascii=False, indent=2))
