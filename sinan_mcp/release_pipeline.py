"""OFFLINE administrator-only candidate generator. NEVER deployed as public MCP."""
from __future__ import annotations
import os
from contextlib import closing
from pathlib import Path
from .core import db_connect_readonly
from .aggregate_contract import (
    _validate_partition, candidate_digest, validate_candidate,
    _canonical, K_MIN, PARTITION_MIN, CODES, HEX64, SCHEMA, REFERENCE,
)

def prepare_candidate(db: str | Path, *, agravo: str, ano: int, uf: str,
                      por: str) -> dict:
    """Build one UF/file-year/group candidate in memory; never publishes it.

    No municipality, free SQL, individual outcome, age, dates or patient records
    are exposed. If *any* populated category is 1..19, reject the WHOLE
    partition rather than publishing residuals or suppression markers.
    Only one demographic dimension may occur in a release. Overlapping releases
    across dimensions/versions must be reviewed together, externally.
    """
    disease, year, region, group = _validate_partition(agravo, ano, uf, por)
    with closing(db_connect_readonly(db)) as con:
        source = con.execute(
            """SELECT tipo_fonte, status, sha256, atualizado_em
               FROM fontes WHERE agravo=? AND ano=?""", (disease, year)
        ).fetchone()
        if source is None:
            raise ValueError("Base solicitada não existe no SQLite local")
        rows = con.execute(
            f"""SELECT {group} AS categoria, COUNT(*) AS n FROM registros
                WHERE agravo=? AND ano=? AND uf=?
                GROUP BY {group} ORDER BY categoria""",
            (disease, year, region),
        ).fetchall()
    if not rows:
        raise ValueError("Partição vazia: nenhum agregado será gerado")
    # A broad enough partition is required, but not sufficient for publication.
    total = sum(r["n"] for r in rows)
    if total < PARTITION_MIN or len(rows) < 2:
        raise ValueError("Partição insuficiente: nenhum agregado será gerado")
    if any(r["n"] < K_MIN for r in rows):
        raise ValueError("Célula pequena presente: partição inteira bloqueada")
    cells = [{"categoria": str(r["categoria"]) if r["categoria"] is not None
              else "ignorado/ausente", "registros": int(r["n"])}
             for r in rows]
    if any(c["categoria"] not in CODES[group] for c in cells):
        raise ValueError("Código categórico inesperado: bloco recusado")
    if len({c["categoria"] for c in cells}) != len(cells):
        raise ValueError("Categorias duplicadas: bloco recusado")
    kind = source["tipo_fonte"]
    if kind not in {"synthetic", "csv-local"} and not kind.startswith("pysus"):
        raise ValueError("Tipo de fonte não reconhecido")
    fingerprint = source["sha256"]
    if not isinstance(fingerprint, str) or not HEX64.fullmatch(fingerprint):
        raise ValueError("Proveniência sem SHA-256 verificável")
    candidate = {
        "schema_version": SCHEMA,
        "stage": "UNAPPROVED_RESEARCH_CANDIDATE",
        "scope": {
            "agravo": disease, "ano_do_arquivo": year, "uf": region,
            "dimensao": group, "data_type": "registro", "ano_nao_e_diagnostico": True,
        },
        "source": {
            "tipo": kind, "status_informado": source["status"],
            "fingerprint_sha256": fingerprint,
            "importado_em_utc": source["atualizado_em"],
            "referencia_oficial": REFERENCE,
        },
        "policy": {
            "min_cell": K_MIN, "min_partition": PARTITION_MIN,
            "one_dimension": True, "outcomes_excluded": True,
            "not_official_indicator": True,
            "not_formal_anonymization": True,
        },
        "cells": cells,
        "limitations": (
            "Ano do arquivo não corresponde necessariamente ao ano de diagnóstico. "
            "Contagem de registros, não pessoas únicas nem incidência; "
            "ainda não revisado para divulgação pública."
        ),
    }
    validate_candidate(candidate)
    return candidate


def write_private_candidate(candidate: dict, *, root: str | Path = "./data/review-packages") -> Path:
    """Save candidate ONLY under ./data/ (which is gitignored); never upload."""
    validate_candidate(candidate)
    data_root = Path("./data").resolve()
    private_dir = Path(root).resolve()
    if not private_dir.is_relative_to(data_root):
        raise ValueError("Candidatos devem permanecer sob data/ ignorado pelo Git")
    private_dir.mkdir(parents=True, exist_ok=True)
    scope = candidate["scope"]
    name = (f"{scope['agravo']}-{scope['ano_do_arquivo']}-{scope['uf']}-"
            f"{scope['dimensao']}-{candidate_digest(candidate)[:12]}.candidate.json")
    target = private_dir / name
    # Atomic exclusive creation and no overwrite of previously reviewed outputs.
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_canonical(candidate) + b"\n")
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return target


