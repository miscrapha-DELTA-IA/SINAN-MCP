"""Print only safe TUBE 2019 technical quality flags; no health values.

Run from the repository root:
  .\.venv\Scripts\python.exe -m scripts.resumir_qualidade_tb2019
"""
import json
from sinan_mcp.tb2019_quality_summary import safe_quality_summary

if __name__ == "__main__":
    print(json.dumps(safe_quality_summary(), ensure_ascii=False, indent=2))
