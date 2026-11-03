"""Static public MCP isolation regression: no private module reachable."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from scripts.check_public_isolation import (
    PUBLIC_ALLOWLIST,
    audit_public_import_boundary,
    inspect_source,
)


def test_real_public_import_graph_stays_in_reviewed_metadata_allowlist():
    root = Path(__file__).resolve().parent.parent
    errors = audit_public_import_boundary(root)
    assert errors == [], "\n".join(errors)


@pytest.mark.parametrize("source,expected", [
    ("from .core import db_connect\n", "dependencia privada"),
    ("from .tool_api import listar_bases_publicas\n", "dependencia privada"),
    ("from . import rest\n", "dependencia privada"),
    ("import sinan_mcp.release_pipeline\n", "dependencia privada"),
    ("from sinan_mcp.local_annual_source_evidence import foo\n",
     "dependencia privada"),
    ("import sqlite3\n", "dependencia externa"),
    ("from urllib.request import urlopen\n", "dependencia externa"),
    ("from requests import get\n", "dependencia externa"),
    ("import subprocess\n", "dependencia externa"),
    ("import importlib\nimportlib.import_module('sinan_mcp.core')\n",
     "importlib.import_module proibido"),
    ("x=__import__('sinan_mcp.core')\n",
     "import dinamico proibido"),
    ("import os\nos.getenv('SINAN_DB_PATH')\n",
     "variavel de ambiente privada"),
    ("exec('from sinan_mcp.core import connect')\n",
     "execucao ou import dinamico"),
])
def test_known_isolation_bypasses_are_rejected_by_ast_policy(source, expected):
    deps, errors = inspect_source("public_server", source)
    assert any(expected in e for e in errors), (source, errors)


def test_safe_annual_metadata_import_and_stdlib_not_rejected():
    deps, errors = inspect_source(
        "public_server",
        "from .query_planner import matriz_capacidades\n"
        "from .year_evidence_registry import consultar_evidencia_agravo_ano\n"
        "from urllib.parse import urlsplit\n"
        "import os\n",
    )
    assert errors == []
    assert deps == {"query_planner", "year_evidence_registry"}


def test_new_public_module_requires_explicit_review():
    imports, errors = inspect_source(
        "public_server", "from .unreviewed_new_feature import boom\n"
    )
    assert imports == set()
    assert len(errors) == 1
    assert "nao revista" in errors[0]
    assert "unreviewed_new_feature" not in PUBLIC_ALLOWLIST


def test_cli_security_script_success():
    root = Path(__file__).resolve().parent.parent
    cmd = subprocess.run(
        [sys.executable, str(root / "scripts" / "check_public_isolation.py")],
        cwd=root, capture_output=True, text=True, timeout=30,
    )
    assert cmd.returncode == 0, cmd.stderr
    assert "PUBLIC MCP ISOLATION OK" in cmd.stdout


def test_public_graph_denies_an_added_private_import(tmp_path):
    src = tmp_path / "sinan_mcp"
    src.mkdir()
    (src / "public_server.py").write_text(
        "from .core import db_connect_readonly\n", encoding="utf-8"
    )
    violations = audit_public_import_boundary(tmp_path)
    assert any("core" in message for message in violations)
