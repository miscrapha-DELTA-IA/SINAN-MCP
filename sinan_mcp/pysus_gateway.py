"""Admin-only PySUS adapter: remote discovery and bounded-memory file ingest.

Does not expose downloads, records or local file paths through MCP/REST.
PySUS 2.11+ namespaced API: https://pysus.readthedocs.io/en/stable/quickstart.html
"""
from __future__ import annotations

import csv
import hashlib
import importlib
import sys
import platform
from pathlib import Path
from typing import Iterable, Mapping, Any

MAX_FILES = 40
MAX_FILE_BYTES = 2 * 1024**3


def _pysus():
    try:
        pysus = importlib.import_module("pysus")
    except ImportError as exc:
        raise RuntimeError("PySUS ausente. Instale: python -m pip install -e '.[ingest]'") from exc
    ftp = getattr(pysus, "ftp", None)
    if not callable(getattr(ftp, "sinan", None)):
        raise RuntimeError("PySUS incompatível: requer pysus.ftp.sinan (2.11+)")
    return ftp


def _validate(agravo: str, ano: int, source: str):
    from .core import validate_agravo
    a = validate_agravo(agravo)
    if not isinstance(ano, int) or isinstance(ano, bool) or not 1980 <= ano <= 2100:
        raise ValueError("Ano deve ser inteiro entre 1980 e 2100")
    if source not in {"catalog", "origin"}:
        raise ValueError("source deve ser catalog ou origin")
    return a


def _files(bag) -> list:
    if bag is None:
        raise RuntimeError("PySUS não retornou lista de arquivos")
    items = list(bag)
    if not items:
        raise ValueError(
            "Catálogo PySUS vazio para o agravo/ano selecionados. "
            "A fonte pode estar indisponível, ou o catálogo local pode estar desatualizado. "
            "Experimente diagnosticar-pysus e, se necessário, --cache-dir "
            "apontando para uma pasta NOVA (sem apagar o cache original)."
        )
    if len(items) > MAX_FILES:
        raise ValueError(f"PySUS retornou {len(items)} arquivos (limite {MAX_FILES}); restrinja a consulta")
    return items


def descobrir(agravo: str, ano: int, source: str = "catalog") -> dict:
    """Discover remote file names without downloading health records."""
    a = _validate(agravo, ano, source)
    bag = _pysus().sinan(disease=a, year=ano, source=source,
                         download=False, as_dataframe=False)
    items = _files(bag)
    # Remote catalog paths use '/' even on Windows; pathlib.Path uses host rules.
    names = [str(getattr(item, "path", item)).replace("\\", "/").rsplit("/", 1)[-1]
             for item in items]
    return {"agravo": a, "ano_do_arquivo": ano, "origem": f"pysus.ftp/{source}",
            "total_arquivos": len(items), "nomes_arquivos": names,
            "download_realizado": False,
            "aviso": "Catálogo remoto: não comprova integridade, dicionário ou status definitivo."}



def diagnosticar(agravo: str, ano: int) -> dict:
    """Admin-only read-only diagnostics. No health records are downloaded.

    Note: PySUS 'origin' also consults its catalog metadata in version 2.11.7.
    """
    a = _validate(agravo, ano, "catalog")
    import pysus
    ftp = _pysus()
    cache = Path(pysus.CACHEPATH).expanduser()
    # PySUS 2.11.7 binds this path at import time. Keep a safe fallback
    # when tests or compatible upstream variants lack the internal module.
    try:
        from pysus.api.ducklake.catalog.adapters import BaseAdapter
    except ImportError:
        adapter_cache = cache / "ducklake"
    else:
        adapter_cache = Path(BaseAdapter.cache_dir).expanduser()
    db_files = ("catalog.duckdb", "catalog_sinan.duckdb", "catalog_columns.duckdb")
    results = {}
    for source in ("catalog", "origin"):
        try:
            bag = ftp.sinan(disease=a, year=ano, source=source,
                            download=False, as_dataframe=False)
            names = [str(getattr(item, "path", item)).replace("\\", "/").rsplit("/", 1)[-1]
                     for item in (list(bag) if bag is not None else [])]
            results[source] = {"quantidade": len(names), "arquivos": names[:MAX_FILES],
                               "disponivel": bool(names)}
        except Exception as exc:
            results[source] = {"erro": type(exc).__name__, "detalhe": str(exc)[:250]}
    # Read cache state AFTER the API calls. Previously this diagnostic could
    # falsely report files as missing, because PySUS downloads the catalogs
    # on the first query.
    cache_state = {}
    for name in db_files:
        path = adapter_cache / name
        cache_state[name] = {
            "presente": path.is_file(),
            "bytes": path.stat().st_size if path.is_file() else None,
        }
    return {
        "agravo": a, "ano_do_arquivo": ano,
        "ambiente": {"plataforma": platform.system(),
                     "python": sys.version.split()[0],
                     "pysus": str(getattr(pysus, "__version__", "desconhecido")),
                     "cache_pySUS": str(cache),
                     "diretorio_catalogo": str(adapter_cache)},
        "cache": cache_state,
        "fontes": results,
        "download_realizado": False,
        "proximo_passo": (
            "Se ambas as fontes estiverem vazias, teste o comando descobrir-pysus "
            "com --cache-dir em uma pasta NOVA para isolar um catálogo local antigo. "
            "Verifique conectividade HTTPS ao catálogo PySUS. "
            "Não apague o cache existente ou baixe bases indiscriminadamente."
        ),
    }


def _file_path(item) -> Path:
    raw = getattr(item, "path", item)
    path = Path(str(raw)).expanduser().resolve()
    if not path.is_file():
        raise ValueError("PySUS não entregou um arquivo local legível; confira a versão e a origem")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"Arquivo acima do limite de {MAX_FILE_BYTES // (1024**2)} MiB: {path.name}")
    return path


def _file_rows(path: Path) -> Iterable[Mapping[str, Any]]:
    extension = path.suffix.lower()
    if extension == ".parquet":
        try:
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise RuntimeError("pyarrow necessário: instale extras de ingestão") from exc
        reader = pq.ParquetFile(path)
        for batch in reader.iter_batches(batch_size=2048):
            yield from batch.to_pylist()
    elif extension == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            header = stream.read(8192)
            stream.seek(0)
            try:
                delimiter = csv.Sniffer().sniff(header, delimiters=",;\t|").delimiter
            except csv.Error:
                delimiter = ","
            yield from csv.DictReader(stream, delimiter=delimiter)
    else:
        raise ValueError(f"Formato do download PySUS não suportado ({extension}). Converta para Parquet ou CSV antes de importar; não carregamos dataframes gigantes na memória.")


def importar(db_path: str | Path, agravo: str, ano: int,
             source: str = "catalog", status: str = "desconhecido") -> dict:
    """Download only after explicit CLI request; stream files in batches.

    SHA256 fingerprints the ordered file manifest: basename + bytes digest.
    It is NOT a SHA256 checksum of an original single SINAN dataset.
    """
    from .core import _import_rows
    a = _validate(agravo, ano, source)
    remote = _pysus().sinan(disease=a, year=ano, source=source,
                            download=False, as_dataframe=False)
    _files(remote)
    local = remote.download()
    paths = sorted((_file_path(item) for item in _files(local)), key=lambda p: p.name)
    fingerprint = hashlib.sha256()
    for path in paths:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for part in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(part)
        fingerprint.update(path.name.encode("utf-8") + b"\0" + digest.hexdigest().encode("ascii") + b"\n")

    def records():
        for path in paths:
            yield from _file_rows(path)

    return _import_rows(db_path, records(), agravo=a, ano=ano,
                        identificador=f"pysus.ftp/{source}/{a}/{ano}",
                        tipo_fonte=f"pysus-{source}", status=status,
                        sha256=fingerprint.hexdigest())
