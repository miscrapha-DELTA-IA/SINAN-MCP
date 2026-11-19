"""Plan or compare official 2019 DBC with PySUS 2019 Parquet, locally only.

Run from repository root:
  python -m scripts.avaliar_equivalencia_tb2019 --etapa planejar
  python -m scripts.avaliar_equivalencia_tb2019 --etapa comparar

Requires optional dependencies for PySUS, pyarrow, and pyreaddbc.
No patient rows or small-cell statistics are printed or uploaded.
"""
from __future__ import annotations
import argparse
import json
from sinan_mcp.tb2019_parity import plan_pysus_2019, compare_local_2019

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--etapa", required=True, choices=["planejar", "comparar"])
    args = parser.parse_args()
    data = plan_pysus_2019() if args.etapa == "planejar" else compare_local_2019()
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
