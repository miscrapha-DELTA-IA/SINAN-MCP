"""CI safety gate tests; no actual sensitive fixtures."""
from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_sensitive_repo.py"
spec = importlib.util.spec_from_file_location("sinan_repo_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def test_sensitive_paths_are_blocked():
    for path in (
        "data/sinan.sqlite3", "data/review-packages/package.json",
        ".env.production", "foo/.env", "credentials.json",
        "records.csv", "example.parquet", "archive.dbc", "patient.jsonl",
        "secret.pem", "private/report.txt", "secrets/password.txt",
        "research.duckdb", "keys/client.p12",
    ):
        assert gate.classify_path(path) is not None


def test_source_and_artificial_metadata_examples_allowed():
    for path in (
        "sinan_mcp/core.py", "README.md", "docs/ROADMAP_IMPLEMENTATION.md",
        "examples/tabnet_artificial.example.json", "tests/test_roadmap_gates.py",
        ".github/workflows/ci.yml", ".gitignore",
    ):
        assert gate.classify_path(path) is None


def test_repository_currently_does_not_track_forbidden_paths():
    assert gate.main() == 0
