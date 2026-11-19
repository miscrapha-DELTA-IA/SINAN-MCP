"""Private-only audit of original TUBE/2019 codes versus projected SQLite.

Reads records only on the operator's machine; no records, categories, cell
counts or percentages leave the process. All intermediate DBF/SQLite files
are created under gitignored data/private/tb2019 and deleted afterwards.
This does NOT validate historical clinical meaning or authorize publication.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from .core import UF_CODIGOS, db_connect_readonly, project_record
from .tb2019_parity import FIELDS, _norm, verify_local_dbc
from .tb2019_private_import import (
    PRIVATE_ROOT, PARQUET_SHA256, SOURCE_TYPE,
)

DB_NAME = "piloto-tb2019.sqlite3"
MAX_DBF_BYTES = 512 * 1024 * 1024
CHUNK_SIZE = 2048
SEX = frozenset(("M", "F", "I"))
RACE = frozenset(("1", "2", "3", "4", "5", "9"))
# Documented TB v5.0 candidate codes; historical compatibility NOT attested.
END = frozenset(str(x) for x in range(1, 11))


def _evidence_row(row: dict) -> tuple[dict, dict, tuple]:
    """Return only booleans for domain and potentially lossy projection."""
    source = {k: _norm(row.get(k)) for k in FIELDS}
    projected = project_record(row, "TUBE", 2019)
    municipality = source["ID_MN_RESI"]
    sex = source["CS_SEXO"]
    race = source["CS_RACA"]
    end = source["SITUA_ENCE"]
    raw_valid = {
        "municipio": municipality is None or bool(re.fullmatch(r"\d{6}", municipality))
                     and municipality[:2] in UF_CODIGOS,
        "sexo": sex is None or sex.upper() in SEX,
        "raca_cor": race is None or race in RACE,
        "situacao_encerramento": end is None or end in END,
    }
    preserved = {
        "municipio": municipality is None or projected[3] == municipality,
        "sexo": sex is None or projected[4] == sex.upper(),
        "raca_cor": race is None or projected[5] == race,
        "situacao_encerramento": end is None or projected[6] == end,
    }
    return raw_valid, preserved, projected


def _write_rows(connection, keys, field: str):
    if not keys:
        return
    sql = (f"INSERT INTO tally(k,{field}) VALUES(?,1) "
           f"ON CONFLICT(k) DO UPDATE SET {field}={field}+1")
    connection.executemany(sql, [(key,) for key in keys])


def audit_original_projection(
    root: Path | str | None = None,
    *,
    converter=None,
    reader_factory=None,
    stage=None,
) -> dict:
    """Check source-domain/transform and exact multiset against local SQLite.

    Optional converter/reader_factory injection is only for synthetic unit tests.
    """
    root = (Path(root) if root is not None else PRIVATE_ROOT).resolve()
    if root != PRIVATE_ROOT.resolve():
        # Do not accidentally inspect an arbitrary database outside data/.
        raise ValueError("Somente a pasta privada fixada TUBE/2019 pode ser auditada")
    dbc = verify_local_dbc(root)
    dbpath = root / DB_NAME
    if not dbpath.is_file():
        raise ValueError("SQLite privado TUBE/2019 ausente")
    announce = stage if stage is not None else (lambda _name: None)
    announce("VERIFICAR_IDENTIDADE_SQLITE")
    with db_connect_readonly(dbpath) as conn:
        sources = conn.execute(
            "SELECT agravo,ano,tipo_fonte,status,sha256,n_registros "
            "FROM fontes"
        ).fetchall()
        if len(sources) != 1:
            raise ValueError("Identidade de fontes fora do escopo")
        source = sources[0]
        if (source["agravo"] != "TUBE" or source["ano"] != 2019
            or source["tipo_fonte"] != SOURCE_TYPE
            or source["status"] != "desconhecido"
            or source["sha256"] != PARQUET_SHA256):
            raise ValueError("Identidade do SQLite nao corresponde ao piloto fixado")
        n_sqlite = conn.execute("SELECT COUNT(*) FROM registros").fetchone()[0]
        if n_sqlite <= 0 or n_sqlite != source["n_registros"]:
            raise ValueError("Integridade do SQLite nao comprovada")

    if converter is None or reader_factory is None:
        import pyreaddbc
        from dbfread import DBF
        if converter is None:
            converter = pyreaddbc.dbc2dbf
        if reader_factory is None:
            reader_factory = DBF

    domains = {name: True for name in ("municipio", "sexo", "raca_cor", "situacao_encerramento")}
    losses = dict(domains)
    announce("CONVERTER_DBC_PRIVADAMENTE")
    with TemporaryDirectory(prefix="source-code-audit-", dir=str(root)) as temp:
        temp = Path(temp)
        dbf = temp / "source.dbf"
        comparer = temp / "multiset.sqlite3"
        converter(str(dbc), str(dbf))
        if (not dbf.is_file() or not 0 < dbf.stat().st_size <= MAX_DBF_BYTES):
            raise RuntimeError("DBC nao produziu DBF aceitavel")
        table = reader_factory(
            str(dbf), encoding="iso-8859-1",
            char_decode_errors="replace", load=False,
        )
        fields = list(table.field_names)
        mapping = {str(k).upper(): k for k in fields}
        if len(mapping) != len(fields) or any(key not in mapping for key in FIELDS):
            raise ValueError("Layout bruto sem campos esperados")

        announce("AUDITAR_CODIGOS_BRUTOS_SEM_DIVULGAR_VALORES")
        with closing(sqlite3.connect(str(comparer))) as scratch:
            scratch.execute(
                "CREATE TABLE tally (k TEXT PRIMARY KEY,"
                " raw_n INTEGER NOT NULL DEFAULT 0,"
                " projected_n INTEGER NOT NULL DEFAULT 0)"
            )
            buffer = []
            n_raw = 0
            for record in table:
                raw = {k: record[mapping[k]] for k in FIELDS}
                valid, preserved, projected = _evidence_row(raw)
                for key in domains:
                    domains[key] &= valid[key]
                    losses[key] &= preserved[key]
                buffer.append(json.dumps(projected, ensure_ascii=False, separators=(",", ":")))
                n_raw += 1
                if len(buffer) >= CHUNK_SIZE:
                    _write_rows(scratch, buffer, "raw_n")
                    buffer.clear()
            _write_rows(scratch, buffer, "raw_n")
            if n_raw != n_sqlite:
                raise ValueError("Quantidade original difere do SQLite privado")

            announce("COMPARAR_PROJECAO_COM_SQLITE")
            with db_connect_readonly(dbpath) as conn:
                buffer = []
                for row in conn.execute(
                    "SELECT agravo,ano,uf,municipio,sexo,raca_cor,situacao_encerramento "
                    "FROM registros"
                ):
                    buffer.append(json.dumps(tuple(row), ensure_ascii=False, separators=(",", ":")))
                    if len(buffer) >= CHUNK_SIZE:
                        _write_rows(scratch, buffer, "projected_n")
                        buffer.clear()
                _write_rows(scratch, buffer, "projected_n")
            is_equal = scratch.execute(
                "SELECT 1 FROM tally WHERE raw_n != projected_n LIMIT 1"
            ).fetchone() is None

    report = {
        "stage": "TUBE2019_SOURCE_CODES_PRIVATE_AUDIT_NOT_HOMOLOGATED",
        "raw_domain_checks": domains,
        "lossless_projection_checks": losses,
        "raw_vs_sqlite_multiset_equal": is_equal,
        "original_record_count_equal_to_sqlite": True,
        "historical_dictionary_compatibility_confirmed": False,
        "scientific_review_independent": False,
        "privacy_review_independent": False,
        "publication_authorized": False,
        "note": (
            "Code domains are candidate dictionaries, not a historical approval. "
            "An invalid nonmissing source code may have been set to NULL in SQLite. "
            "No patient rows, categories or cell counts are emitted."
        )
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    outfile = root / f"TUBE2019-source-audit-{stamp}.json"
    fd = os.open(outfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except BaseException:
        outfile.unlink(missing_ok=True)
        raise
    return {
        "stage": report["stage"],
        "dominios_brutos_sem_alertas": all(domains.values()),
        "projecao_sem_perda_de_codigos_preenchidos": all(losses.values()),
        "multiconjunto_original_projetado_igual_sqlite": is_equal,
        "relatorio_privado_criado": True,
        "quantidades_categorias_e_registros_exibidos": False,
        "compatibilidade_temporal_dicionario_2019_verificada": False,
        "revisao_cientifica_independente": False,
        "revisao_privacidade_independente": False,
        "publicacao_autorizada": False,
    }
