"""Admin-only PySUS adapter: remote discovery and bounded-memory file ingest.

Does not expose downloads, records or local file paths through MCP/REST.
PySUS 2.11+ namespaced API: https://pysus.readthedocs.io/en/stable/quickstart.html
"""
from __future__ import annotations

import csv
import hashlib
import importlib
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
        raise ValueError("Nenhum arquivo SINAN encontrado para o agravo/ano selecionados")
    if len(items) > MAX_FILES:
        raise ValueError(f"PySUS retornou {len(items)} arquivos (limite {MAX_FILES}); restrinja a consulta")
    return items


def descobrir(agravo: str, ano: int, source: str = "auto") -> dict:
    """Read-only discovery, with diagnostic attempts instead of a misleading 404.

    Auto uses catalog first, then explicitly origin only if catalog is empty/fails.
    Neither origin is asserted to be authoritative when a source is unreachable.
    Import/download remains explicit-source to prevent silent source substitution.
    """
    if source not in {"auto", "catalog", "origin"}:
        raise ValueError("source deve ser auto, catalog ou origin para descoberta")
    a = _validate(agravo, ano, "catalog" if source == "auto" else source)
    ftp = _pysus()
    attempts = []
    for selected in (["catalog", "origin"] if source == "auto" else [source]):
        try:
            bag = ftp.sinan(disease=a, year=ano, source=selected,
                            download=False, as_dataframe=False)
            items = list(bag) if bag is not None else []
            if len(items) > MAX_FILES:
                raise ValueError(f"Mais de {MAX_FILES} arquivos retornados; consulta não suportada")
            names = [Path(str(getattr(item, "path", item))).name for item in items]
            attempts.append({"fonte": selected, "status": "encontrado" if names else "catalogo_vazio",
                             "total_arquivos": len(names)})
            if names:
                return {"agravo": a, "ano_do_arquivo": ano, "status": "encontrado",
                        "origem": f"pysus.ftp/{selected}",
                        "total_arquivos": len(names), "nomes_arquivos": names,
                        "tentativas": attempts, "download_realizado": False,
                        "aviso": "Metadados de catálogo; não valida integridade, completude ou versão epidemiológica."}
        except (OSError, ConnectionError, TimeoutError) as exc:
            attempts.append({"fonte": selected, "status": "falha_de_acesso",
                             "erro_tipo": type(exc).__name__})
        # Unexpected errors are raised rather than masked, to aid debugging.
    return {"agravo": a, "ano_do_arquivo": ano, "status": "nao_confirmado",
            "origem": None, "total_arquivos": 0, "nomes_arquivos": [],
            "tentativas": attempts, "download_realizado": False,
            "aviso": "Nenhum resultado confirmado nas fontes consultadas. NÃO significa ausência de dados SINAN. Verifique rede, catálogo PySUS e tente --source origin."}


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
