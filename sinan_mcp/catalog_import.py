"""Opt-in administrative import of public PySUS FTP-mirror Parquet files.

This is NOT an MCP tool. Metadata is read from the PySUS DuckLake index.
Raw downloaded files are held in a TemporaryDirectory, never committed to Git.
The caller must explicitly execute importar-pysus --source catalog; there is
no automatic substitution when --source origin was requested.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .catalog_fallback import MAX_FILES, catalog_path, _validate

MAX_FILE_BYTES = 2 * 1024**3
MAX_TOTAL_BYTES = 3 * 1024**3
_PREFIX = "public/data/ftp/sinan/"
_QUERY = """SELECT f.path, f.size, f.sha256
            FROM pysus.files f
            JOIN pysus.dataset_groups g ON f.group_id=g.id
            WHERE upper(g.name)=? AND f.year=?
              AND f.path LIKE 'public/data/ftp/sinan/%'
            ORDER BY f.path LIMIT ?"""


def _validate_manifest(rows) -> list[dict]:
    if len(rows) > MAX_FILES:
        raise ValueError("Catálogo retornou mais arquivos do que o permitido")
    result = []
    total = 0
    for key, bytes_value, sha in rows:
        key = str(key).replace("\\", "/")
        pieces = key.split("/")
        name = pieces[-1]
        if (not key.startswith(_PREFIX)
                or any(part in {"", ".", ".."} or not re.fullmatch(r"[A-Za-z0-9_.-]+", part)
                       for part in pieces)
                or not re.fullmatch(r"[A-Za-z0-9_.-]+[.]parquet", name)):
            raise ValueError("Caminho de arquivo inválido no catálogo PySUS")
        size = int(bytes_value) if bytes_value is not None else -1
        if size <= 0 or size > MAX_FILE_BYTES:
            raise ValueError(f"Tamanho ausente/inaceitável do arquivo {name}")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ValueError("Conjunto de arquivos supera o limite de transferência")
        sha = str(sha or "").strip().lower()
        if sha and not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError("Checksum SHA256 inválido no catálogo")
        result.append({"key": key, "name": name, "size": size, "sha256": sha or None})
    return result


def _rows_from_catalog(agravo: str, ano: int):
    _validate(agravo, ano)
    path = catalog_path()
    if not path.is_file():
        return []
    try:
        from pysus.api.ducklake.catalog.adapters import _SHARED_ENGINES
    except ImportError:
        _SHARED_ENGINES = {}
    engine = _SHARED_ENGINES.get(str(path.resolve()))
    if engine is not None:
        with engine.connect() as conn:
            return conn.exec_driver_sql(_QUERY, (agravo, ano, MAX_FILES + 1)).fetchall()

    # PySUS's cached DuckDB file may be locked in read/write mode on Windows.
    # An isolated child can open it read-only without exposing raw data.
    cp = subprocess.run(
        [sys.executable, "-m", "sinan_mcp.catalog_import", "--manifest",
         agravo, str(ano)],
        capture_output=True, text=True, timeout=30, check=False,
    )
    if cp.returncode:
        raise RuntimeError("Leitura do manifesto PySUS falhou")
    import json
    return json.loads(cp.stdout)


def _read_rows_isolated(agravo: str, ano: int):
    import duckdb
    with duckdb.connect(str(catalog_path()), read_only=True) as con:
        return con.execute(_QUERY, [agravo, ano, MAX_FILES + 1]).fetchall()


def manifest(agravo: str, ano: int) -> list[dict]:
    return _validate_manifest(_rows_from_catalog(agravo, ano))


class _RejectRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects BEFORE accessing their destinations (SSRF protection)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Redirecionamento HTTPS não permitido no adaptador PySUS")


def _open_strict(request, *, timeout: int):
    return urllib.request.build_opener(_RejectRedirect).open(request, timeout=timeout)


def _download(entry: dict, destination: Path) -> tuple[str, int]:
    """Bounded, integrity-checked, origin-locked read with limited retry.

    Retries only transient network responses, up to three attempts; never
    retries a checksum mismatch or HTTP 4xx other than 408/429. A failed
    attempt deletes its partial file before the next attempt.
    """
    from pysus.api import types

    valid = _validate_manifest([(
        entry["key"], entry["size"], entry.get("sha256")
    )])[0]
    host = str(types.S3_ENDPOINT)
    if host != "nbg1.your-objectstorage.com" or str(types.S3_BUCKET) != "pysus":
        raise RuntimeError("Endpoint PySUS inesperado; download bloqueado")
    url = "https://" + host + "/pysus/" + urllib.parse.quote(valid["key"], safe="/")
    request = urllib.request.Request(
        url, headers={"User-Agent": "SINAN-MCP/0.4 (local public data importer)"}
    )
    for attempt in range(3):
        digest = hashlib.sha256()
        count = 0
        try:
            with _open_strict(request, timeout=60) as response:
                actual_url = urllib.parse.urlsplit(response.geturl())
                if (actual_url.scheme != "https" or actual_url.hostname != host
                        or response.status != 200):
                    raise RuntimeError("Endpoint ou resposta de download não autorizado")
                with destination.open("xb") as out:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        count += len(chunk)
                        if count > MAX_FILE_BYTES or count > valid["size"]:
                            raise ValueError("Download excedeu tamanho declarado pelo catálogo")
                        digest.update(chunk)
                        out.write(chunk)
            if count != valid["size"]:
                raise ValueError("Download incompleto: tamanho diferente do catálogo")
            checksum = digest.hexdigest()
            if valid["sha256"] and checksum != valid["sha256"]:
                raise ValueError("SHA256 difere do catálogo: conteúdo rejeitado")
            return checksum, count
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, ConnectionError, OSError) as exc:
            destination.unlink(missing_ok=True)
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in (
                408, 429, 500, 502, 503, 504,
            ):
                raise RuntimeError("Erro HTTP permanente na fonte de dados") from None
            if attempt == 2:
                raise RuntimeError("Fonte indisponível após tentativas limitadas") from None
            time.sleep(min(2 ** attempt, 2))
        except BaseException:
            destination.unlink(missing_ok=True)
            raise
    raise RuntimeError("Falha inesperada na transferência")



def importar_fallback(db_path, *, agravo: str, ano: int, status: str):
    """Download only on explicit CLI invocation; remove raw files after import."""
    from .core import _import_rows
    from .pysus_gateway import _file_rows

    entries = manifest(agravo, ano)
    if not entries:
        raise ValueError("Catálogo SQL sem Parquet para esse agravo/ano; nada foi importado")

    digest_manifest = hashlib.sha256()
    with tempfile.TemporaryDirectory(prefix="sinan-public-import-") as tmp:
        folder = Path(tmp)
        paths = []
        for index, entry in enumerate(entries):
            dest = folder / f"{index:02d}_{entry['name']}"
            sha, count = _download(entry, dest)
            # The provenance hash is the ordered manifest of remote keys + verified content SHA.
            digest_manifest.update(entry["key"].encode("utf-8") + bytes([0]) +
                                   sha.encode("ascii") + bytes([10]))
            paths.append(dest)

        def rows():
            for path in paths:
                yield from _file_rows(path)

        result = _import_rows(
            db_path, rows(), agravo=agravo, ano=ano,
            identificador=f"pysus-ftp-mirror/ducklake/{agravo}/{ano}",
            tipo_fonte="pysus-catalog-verified", status=status,
            sha256=digest_manifest.hexdigest(),
        )
        result["arquivos_processados"] = len(entries)
        result["metodo_download"] = "https-publico-catalogo-ducklake"
        result["arquivos_brutos_removidos"] = True
        return result


if __name__ == "__main__":
    import json
    _validate(sys.argv[2], int(sys.argv[3])) if len(sys.argv) == 4 and sys.argv[1] == "--manifest" else sys.exit(2)
    print(json.dumps(_read_rows_isolated(sys.argv[2], int(sys.argv[3]))))
