"""Block accidental public Render deployments of real data or legacy MCP."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from scripts.check_public_deployment import (
    EXPECTED_BLUEPRINT,
    validate_public_blueprint,
)


def test_render_blueprint_is_exactly_synthetic_and_no_autodeploy():
    root = Path(__file__).resolve().parent.parent
    rendered = (root / "render.yaml").read_text(encoding="utf-8")
    validate_public_blueprint(rendered)
    assert "startCommand: python -m sinan_mcp.public_server" in rendered
    assert "autoDeploy: false" in rendered
    assert 'value: "0"' in rendered
    assert "SINAN_DB_PATH" not in rendered
    assert "SINAN_PUBLIC_HOST" not in rendered
    assert "sinan_mcp.server" not in rendered


@pytest.mark.parametrize("mutation", [
    lambda x: x.replace("sinan_mcp.public_server", "sinan_mcp.server"),
    lambda x: x.replace('value: "0"', 'value: "1"'),
    lambda x: x.replace("autoDeploy: false", "autoDeploy: true"),
    lambda x: x.replace(
        "    envVars:\n", "    envVars:\n      - key: SINAN_DB_PATH\n"
    ),
    lambda x: x + "  - type: web\n    name: second-service\n",
    lambda x: "# changed\n" + x,
    lambda x: x.replace("startCommand: python", "startCommand: sh"),
])
def test_any_deployment_manifest_change_requires_review(mutation):
    changed = mutation(EXPECTED_BLUEPRINT)
    assert changed != EXPECTED_BLUEPRINT
    with pytest.raises(ValueError):
        validate_public_blueprint(changed)


def test_ci_deployment_guard_runs_from_repo():
    root = Path(__file__).resolve().parent.parent
    completed = subprocess.run(
        [sys.executable, str(root / "scripts" / "check_public_deployment.py")],
        cwd=root, capture_output=True, text=True, timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    assert "PUBLIC DEPLOYMENT OK" in completed.stdout
