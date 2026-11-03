"""Offline verification of an operator-supplied disease/year source manifest.

SHA-256 verification proves only that a LOCAL file matches a declared digest.
It cannot certify the official origin, licensing, completeness, year semantics,
clinical coding, reviewer identity or permission to publish. Never exposed via MCP.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from .official_sources import CONDITIONS

SCHEMA = "sinan-source-evidence-v1"
MAX_MANIFEST_BYTES = 16_384
MAX_DATA_BYTES = 3 * 1024 ** 3
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
ALIAS = frozenset(x[0] for x in CONDITIONS)
OFFICIAL_HOSTS = frozenset({
    "www.gov.br", "datasus.saude.gov.br",
    "tabnet.datasus.gov.br", "portalsinan.saude.gov.br",
})
METHODS = frozenset({"csv-local", "pysus-catalog", "pysus-origin", "tabnet-export"})
YEAR_TYPES = frozenset({
    "ano_arquivo", "ano_notificacao", "ano_diagnostico",
    "ano_encerramento", "ano_ocorrencia",
})
SOURCE_KEYS = frozenset({
    "schema_version", "agravo", "ano_arquivo", "tipo_ano", "codigo_download_declarado",
    "metodo", "url_fonte", "url_dicionario", "versao_dicionario",
    "situacao_declarada", "extraido_em_utc", "arquivo_nome",
    "arquivo_bytes", "arquivo_sha256", "observacao_metodologica",
})


def _strict_object(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("Documento JSON com chave duplicada")
        out[key] = value
    return out


def _safe_text(value: object, *, max_length: int = 140) -> str:
    if (not isinstance(value, str) or not 1 <= len(value.strip()) <= max_length
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise ValueError("Campo textual inválido")
    return value.strip()


def _official_url(url: object) -> str:
    raw = _safe_text(url, max_length=1024)
    try:
        parts = urlsplit(raw)
        port = parts.port
    except ValueError as exc:
        raise ValueError("URL de fonte inválida") from exc
    if (parts.scheme != "https" or parts.hostname not in OFFICIAL_HOSTS
            or parts.username or parts.password or port not in (None, 443)
            or parts.fragment or "\\" in raw or any(ord(c) < 33 for c in raw)):
        raise ValueError("URL deve apontar a domínio oficial HTTPS conhecido")
    return raw


def validate_manifest(doc: object) -> dict:
    """Strict structure validation. All provenance assertions remain untrusted."""
    if (not isinstance(doc, dict) or set(doc) != SOURCE_KEYS
            or doc.get("schema_version") != SCHEMA):
        raise ValueError("Esquema de manifesto incompatível")
    if doc["agravo"] not in ALIAS:
        raise ValueError("Agravo não consta do índice interno de referência")
    if type(doc["ano_arquivo"]) is not int or not 1980 <= doc["ano_arquivo"] <= 2100:
        raise ValueError("Ano de arquivo inválido")
    if doc["tipo_ano"] not in YEAR_TYPES or doc["metodo"] not in METHODS:
        raise ValueError("Tipo de ano ou método de obtenção não reconhecido")
    if doc["situacao_declarada"] not in {"final", "preliminar", "desconhecido"}:
        raise ValueError("Situação declarada inválida")
    download_code = _safe_text(doc["codigo_download_declarado"], max_length=24)
    if not re.fullmatch(r"[A-Za-z0-9_-]{2,24}", download_code):
        raise ValueError("Código de download declarado inválido")
    _official_url(doc["url_fonte"])
    _official_url(doc["url_dicionario"])
    _safe_text(doc["versao_dicionario"])
    _safe_text(doc["observacao_metodologica"], max_length=800)
    basename = _safe_text(doc["arquivo_nome"], max_length=150)
    if (basename in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,149}", basename)
            or "/" in basename or "\\" in basename):
        raise ValueError("Nome de arquivo inválido")
    if type(doc["arquivo_bytes"]) is not int or not 1 <= doc["arquivo_bytes"] <= MAX_DATA_BYTES:
        raise ValueError("Tamanho de arquivo inválido")
    if not isinstance(doc["arquivo_sha256"], str) or not HEX64.fullmatch(doc["arquivo_sha256"]):
        raise ValueError("Hash SHA-256 inválido")
    dt = _safe_text(doc["extraido_em_utc"], max_length=40)
    try:
        when = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Horário de extração inválido") from exc
    if (when.tzinfo is None or when.utcoffset().total_seconds() != 0
            or not 1980 <= when.year <= 2100):
        raise ValueError("Extração deve informar data/hora UTC")
    return doc


def load_manifest(path: str | Path) -> dict:
    """Never read patient file contents into a manifest parser."""
    p = Path(path).expanduser()
    if p.is_symlink():
        raise ValueError("Manifesto por link simbólico não permitido")
    if not p.is_file() or p.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError("Manifesto ausente ou grande demais")
    try:
        obj = json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("JSON de manifesto inválido") from exc
    return validate_manifest(obj)


def verify_local_file(manifest_path: str | Path, data_path: str | Path) -> dict:
    """Bounded-memory checksum verification, admin initiated, no network."""
    doc = load_manifest(manifest_path)
    source = Path(data_path).expanduser()
    if source.is_symlink() or not source.is_file():
        raise ValueError("Arquivo local ausente ou link simbólico")
    if source.name != doc["arquivo_nome"] or source.stat().st_size != doc["arquivo_bytes"]:
        raise ValueError("Nome ou tamanho divergente do manifesto")
    digest = hashlib.sha256()
    read = 0
    with source.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            read += len(chunk)
            if read > doc["arquivo_bytes"] or read > MAX_DATA_BYTES:
                raise ValueError("Arquivo cresceu durante verificação")
            digest.update(chunk)
    if read != doc["arquivo_bytes"] or digest.hexdigest() != doc["arquivo_sha256"]:
        raise ValueError("Conteúdo local diferente do checksum declarado")
    return {
        "schema_version": SCHEMA,
        "integridade_local_verificada": True,
        "identidade_fonte_oficial_verificada": False,
        "codigo_download_oficial_verificado": False,
        "status_final_documental_verificado": False,
        "aprovacao_para_publicacao": False,
        "agravo": doc["agravo"],
        "ano_do_arquivo": doc["ano_arquivo"],
        "tipo_ano_declarado": doc["tipo_ano"],
        "situacao_declarada": doc["situacao_declarada"],
        "metodo": doc["metodo"],
        "arquivo_sha256": digest.hexdigest(),
        "nota": (
            "Checksum local compatível. A origem, versão do dicionário, "
            "estado final e autorização de pesquisa/publicação exigem "
            "verificação independente e não são certificados por este comando."
        ),
    }



def verify_csv_import_lineage(
    manifest_path: str | Path, data_path: str | Path, db_path: str | Path,
) -> dict:
    """Compare verified CSV bytes with the active local SQLite snapshot digest.

    Supports only CSV imports with a direct file digest. PySUS composite
    digests use a different definition and cannot be equated to this hash.
    """
    from contextlib import closing
    from .core import db_connect_readonly

    summary = verify_local_file(manifest_path, data_path)
    doc = load_manifest(manifest_path)
    if doc["metodo"] != "csv-local":
        raise ValueError("Linhagem direta exige manifesto csv-local")
    with closing(db_connect_readonly(db_path)) as con:
        row = con.execute(
            "SELECT tipo_fonte, sha256, status, n_registros FROM fontes "
            "WHERE agravo=? AND ano=?", (doc["agravo"], doc["ano_arquivo"])
        ).fetchone()
    if row is None or row["tipo_fonte"] != "csv-local":
        raise ValueError("Snapshot CSV correspondente não está importado")
    if row["sha256"] != summary["arquivo_sha256"]:
        raise ValueError("Fingerprint do snapshot difere do arquivo verificado")
    return {
        **summary,
        "snapshot_csv_corresponde_ao_arquivo": True,
        "status_snapshot_declarado": row["status"],
        "registros_metadado_local": row["n_registros"],
        "fonte_original_independentemente_autenticada": False,
        "publicacao_autorizada": False,
        "nota_linhagem": (
            "Hash do CSV local coincide com a projeção importada. Isso não "
            "certifica a origem governamental, dicionário, data de corte "
            "nem a ausência de duplicações epidemiológicas."
        ),
    }
