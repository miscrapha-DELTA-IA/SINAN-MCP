"""Administrative diagnostics for PySUS metadata discovery.

No patient records, downloaded datasets, credentials or private paths are
included in reports. Cache isolation never deletes the user's existing cache.
"""
from __future__ import annotations

import importlib
import importlib.metadata
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def create_isolated_cache() -> Path:
    """Configure a new cache before the PySUS module is imported."""
    if "pysus" in sys.modules:
        raise RuntimeError("O cache isolado deve ser escolhido antes de importar PySUS")
    parent = Path.cwd() / "data"
    parent.mkdir(parents=True, exist_ok=True)
    path = parent / f"pysus-metadata-probe-{uuid4().hex[:12]}"
    path.mkdir(exist_ok=False)
    os.environ["PYSUS_CACHEPATH"] = str(path.resolve())
    return path


def catalog_diagnostics(*, check_network: bool = True) -> dict:
    """Inspect cached catalog metadata and HEAD the documented public index."""
    pysus = importlib.import_module("pysus")
    catalog_dir = Path(pysus.CACHEPATH) / "ducklake"
    found = []
    for name in ("catalog.duckdb", "catalog_sinan.duckdb", "catalog_columns.duckdb"):
        path = catalog_dir / name
        try:
            if path.is_file():
                stat = path.stat()
                found.append({
                    "nome": name, "presente": True, "bytes": stat.st_size,
                    "atualizado_utc": datetime.fromtimestamp(
                        stat.st_mtime, timezone.utc
                    ).isoformat(),
                })
            else:
                found.append({"nome": name, "presente": False})
        except OSError:
            found.append({"nome": name, "presente": "indeterminado"})

    result = {
        "pysus_versao": importlib.metadata.version("pysus"),
        "catalogos_locais": found,
        "rede": {"status": "nao_verificada"},
        "observacao": (
            "No PySUS 2.11.x, catalog e origin consultam metadados DuckLake. "
            "Uma lista vazia nao prova que os arquivos SINAN nao existem."
        ),
    }
    if check_network:
        import urllib.error
        import urllib.request
        from pysus.api import types

        url = f"https://{types.S3_ENDPOINT}/{types.S3_BUCKET}/public/catalog.duckdb"
        req = urllib.request.Request(
            url, method="HEAD",
            headers={"User-Agent": "SINAN-MCP-catalog-check/0.3"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                result["rede"] = {
                    "status": "respondendo", "http_status": response.status,
                    "content_length": response.headers.get("Content-Length"),
                }
        except urllib.error.HTTPError as exc:
            result["rede"] = {"status": "erro_http", "http_status": exc.code}
        except (OSError, ValueError) as exc:
            result["rede"] = {
                "status": "falha_conexao", "tipo_erro": type(exc).__name__,
            }
    return result
