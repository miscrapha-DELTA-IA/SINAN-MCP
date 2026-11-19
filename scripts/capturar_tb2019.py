"""Capture the official TUBE/2019 DBC locally; never upload raw health data.

Run from the repo root: py -3.11 -m scripts.capturar_tb2019
"""
import json
from sinan_mcp.official_snapshot import capture_tb_2019

if __name__ == "__main__":
    result = capture_tb_2019()
    print(json.dumps(result, ensure_ascii=False, indent=2))
