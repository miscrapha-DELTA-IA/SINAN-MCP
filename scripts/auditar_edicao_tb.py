"""Inspect official DATASUS FTP file metadata without downloading health data.

Usage (from the repository root): python -m scripts.auditar_edicao_tb --anos 2019 2024
"""
from __future__ import annotations

import argparse
import json
from sinan_mcp.source_edition import inspect_tb_edition


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anos", nargs="+", type=int, default=[2019, 2024])
    args = parser.parse_args()
    results = [inspect_tb_edition(year) for year in args.anos]
    print(json.dumps({"etapa": "DISCOVERY_ONLY_NO_APPROVAL", "edicoes": results},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
