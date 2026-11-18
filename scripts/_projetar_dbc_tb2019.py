"""Internal local-only DBC parser isolated in a subprocess.

Do not invoke on untrusted DBC files. Never prints sensitive fields.
"""
from __future__ import annotations
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    from sinan_mcp.tb2019_parity import FIELDS, verify_local_dbc
    import pyreaddbc
    import pyarrow as pa
    import pyarrow.parquet as pq
    source = verify_local_dbc(args.source.parent)
    if args.source.resolve() != source:
        raise ValueError("DBC nao corresponde ao snapshot local fixado")
    output = args.target.resolve()
    if not output.parent.is_relative_to(source.parent):
        raise ValueError("Projecao so pode existir na pasta privada")
    if output.exists():
        raise FileExistsError("Projecao nao pode sobrescrever arquivos")
    frame = pyreaddbc.read_dbc(str(source), encoding="iso-8859-1")
    mapping = {str(c).upper(): c for c in frame.columns}
    if len(mapping) != len(frame.columns) or not all(c in mapping for c in FIELDS):
        raise ValueError("Layout DBC sem campos requeridos")
    fields = frame[[mapping[c] for c in FIELDS]].copy()
    fields.columns = list(FIELDS)
    # Convert to Arrow string preserving missingness; canonical comparison
    # will normalize numeric trailing .0 and blank strings.
    fields = fields.astype("string")
    pq.write_table(pa.Table.from_pandas(fields, preserve_index=False), output)
    print("Projecao privada de quatro campos criada; nenhum dado exibido.")

if __name__ == "__main__":
    main()
