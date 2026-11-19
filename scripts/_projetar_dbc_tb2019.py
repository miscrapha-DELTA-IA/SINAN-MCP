"""Private DATASUS DBC -> four-column Parquet projection, in a subprocess.

Conversion runs in a separate process because pyreaddbc invokes native C.
It writes temporary files only under data/private/ and emits no patient data.
Structured failures reveal just stage and exception class, never record values.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MAX_DBF_BYTES = 512 * 1024 * 1024
BATCH_SIZE = 4096


class ConversionFailure(RuntimeError):
    def __init__(self, stage: str, code: str):
        super().__init__(code)
        self.stage = stage
        self.code = code


def _project(source: Path, output: Path) -> int:
    from sinan_mcp.tb2019_parity import FIELDS, _norm, verify_local_dbc

    source = source.resolve()
    verified = verify_local_dbc(source.parent)
    if source != verified:
        raise ConversionFailure("PREFLIGHT", "SOURCE_NOT_PINNED")
    output = output.resolve()
    if not output.parent.is_relative_to(source.parent):
        raise ConversionFailure("PREFLIGHT", "DESTINATION_OUTSIDE_PRIVATE_FOLDER")
    if output.exists():
        raise ConversionFailure("PREFLIGHT", "DESTINATION_EXISTS")

    # pyreaddbc dbc2dbf is the low-level API; dbfread supports record iteration
    # without creating a full pandas DataFrame in memory.
    try:
        import pyreaddbc
        from dbfread import DBF
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        raise ConversionFailure("DEPENDENCIES", "OPTIONAL_DEPENDENCY_MISSING")

    converter = getattr(pyreaddbc, "dbc2dbf", None)
    if not callable(converter):
        raise ConversionFailure("DEPENDENCIES", "DBC2DBF_UNAVAILABLE")

    intermediate = output.parent / "TUBEBR19-temporary.dbf"
    if intermediate.exists():
        raise ConversionFailure("PREFLIGHT", "INTERMEDIATE_EXISTS")

    try:
        try:
            converter(str(source), str(intermediate))
        except Exception as exc:
            raise ConversionFailure("DBC_TO_DBF", type(exc).__name__) from None
        if not intermediate.is_file() or intermediate.stat().st_size == 0:
            raise ConversionFailure("DBC_TO_DBF", "DBF_NOT_CREATED")
        if intermediate.stat().st_size > MAX_DBF_BYTES:
            raise ConversionFailure("DBC_TO_DBF", "DBF_OVERSIZE")

        try:
            table = DBF(
                str(intermediate), encoding="iso-8859-1",
                char_decode_errors="replace", load=False,
            )
        except Exception as exc:
            raise ConversionFailure("DBF_READER", type(exc).__name__) from None

        names = {str(name).upper(): name for name in table.field_names}
        if len(names) != len(table.field_names) or not all(k in names for k in FIELDS):
            raise ConversionFailure("DBF_SCHEMA", "REQUIRED_FIELDS_MISSING")

        schema = pa.schema([(name, pa.string()) for name in FIELDS])
        buffer = {name: [] for name in FIELDS}
        rows = 0
        writer = None
        try:
            for record in table:
                for name in FIELDS:
                    buffer[name].append(_norm(record[names[name]]))
                rows += 1
                if len(buffer[FIELDS[0]]) >= BATCH_SIZE:
                    if writer is None:
                        writer = pq.ParquetWriter(str(output), schema)
                    writer.write_table(pa.Table.from_pydict(buffer, schema=schema))
                    buffer = {name: [] for name in FIELDS}
            if buffer[FIELDS[0]]:
                if writer is None:
                    writer = pq.ParquetWriter(str(output), schema)
                writer.write_table(pa.Table.from_pydict(buffer, schema=schema))
        except Exception as exc:
            raise ConversionFailure("DBF_PROJECT", type(exc).__name__) from None
        finally:
            if writer is not None:
                writer.close()
        if rows == 0:
            raise ConversionFailure("DBF_PROJECT", "EMPTY_FILE")
        return rows
    finally:
        intermediate.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    try:
        n_rows = _project(args.source, args.target)
    except ConversionFailure as exc:
        print(json.dumps({"status": "error", "stage": exc.stage,
                          "code": exc.code}), file=sys.stderr)
        raise SystemExit(2)
    except Exception as exc:
        # Do not leak exception messages, paths, DBF field values or records.
        print(json.dumps({"status": "error", "stage": "UNEXPECTED",
                          "code": type(exc).__name__}), file=sys.stderr)
        raise SystemExit(3)
    print(json.dumps({"status": "ok", "rows_projected": n_rows}))


if __name__ == "__main__":
    main()
