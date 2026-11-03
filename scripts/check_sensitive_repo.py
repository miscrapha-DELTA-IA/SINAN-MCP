"""CI fail-closed guard against accidentally checking in private SINAN material.

Inspects tracked path names (not file contents), keeping the scan cheap.
This is defense in depth, NOT PII detection or a secret scanner.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import PurePosixPath

BLOCKED_SUFFIXES = frozenset({
    ".csv", ".tsv", ".xlsx", ".xls", ".parquet", ".dbc", ".dbf", ".db",
    ".sqlite", ".sqlite3", ".jsonl", ".pem", ".key", ".p12", ".pfx",
    ".duckdb", ".zip", ".7z", ".rds", ".sav",
})
BLOCKED_NAMES = frozenset({
    ".env", ".env.local", ".env.production", "credentials.json",
    "client_secret.json", "service_account.json",
})


def classify_path(path: str) -> str | None:
    value = path.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    item = PurePosixPath(value)
    parts = [part.lower() for part in item.parts]
    if not parts:
        return None
    if parts[0] in {"data", "private", "secrets", ".secrets"}:
        return "Diretório privado proibido"
    if item.name.lower() in BLOCKED_NAMES or item.name.lower().startswith(".env."):
        return "Arquivo de configuração/credencial proibido"
    if item.suffix.lower() in BLOCKED_SUFFIXES:
        return "Formato de dados ou credencial proibido"
    return None


def main() -> int:
    cp = subprocess.run(
        ["git", "ls-files", "--cached", "-z"],
        check=True, capture_output=True,
    )
    paths = [name.decode("utf-8", "replace") for name in cp.stdout.split(b"\0") if name]
    bad = [(name, classify_path(name)) for name in paths if classify_path(name)]
    if bad:
        for name, explanation in bad:
            # Only filenames, no file contents.
            print(f"BLOCKED: {name} ({explanation})", file=sys.stderr)
        print("Refuse release: investigate tracked files before merge.", file=sys.stderr)
        return 2
    print("Tracked-path safety gate: no forbidden private-data file types found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
