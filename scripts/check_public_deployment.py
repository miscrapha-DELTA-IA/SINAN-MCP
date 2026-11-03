"""Freeze the exact reviewed SYNTHETIC Render Blueprint until human review.

This is a narrow configuration snapshot, not a YAML security parser or
a guarantee about external hosting settings. Changes must be deliberate.
"""
from __future__ import annotations

from pathlib import Path
import sys

EXPECTED_BLUEPRINT = """# Optional Render Blueprint: deliberately SYNTHETIC-ONLY public MCP.
# Requires user selection/approval of a Render workspace and service plan.
# Do not attach disks, private database URLs, PySUS caches, or tunnel credentials.
services:
  - type: web
    name: sinan-mcp-public-preview
    runtime: python
    plan: free
    buildCommand: python -m pip install -e .
    startCommand: python -m sinan_mcp.public_server
    healthCheckPath: /health
    autoDeploy: false
    envVars:
      - key: SINAN_PUBLIC_REAL_DATA
        value: "0"
"""


def validate_public_blueprint(text: str) -> None:
    if type(text) is not str or text != EXPECTED_BLUEPRINT:
        raise ValueError(
            "Blueprint publico diverge do snapshot sintetico aprovado "
            "para revisao tecnica; requer auditoria humana"
        )


def main() -> int:
    path = Path(__file__).resolve().parent.parent / "render.yaml"
    try:
        if path.is_symlink():
            raise ValueError("Blueprint nao pode ser symlink")
        validate_public_blueprint(path.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError) as exc:
        print("PUBLIC DEPLOYMENT FAIL:", exc, file=sys.stderr)
        return 2
    print("PUBLIC DEPLOYMENT OK: synthetic-only Render blueprint unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
