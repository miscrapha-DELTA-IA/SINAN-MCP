"""Local-only TUBE/2019 DBC <-> PySUS Parquet projection concordance.

Only four fields are compared. Equality is *not* full-dataset equivalence,
proof of official provenance, scientific validity, or release authorization.
No health records are printed, sent to network APIs or committed to Git.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from .catalog_import import download_mirror_entry, manifest
from .official_snapshot import NAME, OBSERVED_SIZE, YEAR

ROOT = Path("./data/private/tb2019")
PINNED_SHA256 = "7a00e29a5a309b794e21f1a650d3b04b9d3cb05fcc6ef8c9feefab3a961c9144"
FIELDS = ("ID_MN_RESI", "CS_SEXO", "CS_RACA", "SITUA_ENCE")
MAX_PARQUET_BYTES = 256 * 1024 * 1024


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def verify_local_dbc(root: Path | str = ROOT) -> Path:
    root = Path(root).resolve()
    source = root / NAME
    provenance = root / "TUBEBR19.manifest.json"
    if not source.is_file() or not provenance.is_file():
        raise FileNotFoundError("DBC ou manifesto local ausente em data/private/tb2019/")
    if source.stat().st_size != OBSERVED_SIZE or _sha256(source) != PINNED_SHA256:
        raise ValueError("SHA-256 ou tamanho do DBC diverge da captura original; bloqueado")
    data = json.loads(provenance.read_text(encoding="utf-8"))
    if (data.get("sha256_recebido") != PINNED_SHA256
            or data.get("bytes_observados") != OBSERVED_SIZE
            or data.get("ano_do_arquivo") != YEAR
            or data.get("stage") != "OFFICIAL_FTP_FILE_RECEIVED_NOT_HOMOLOGATED"):
        raise ValueError("Manifesto do DBC inconsistente com captura original")
    return source


def _choose_entry(entries: list[dict]) -> dict:
    matches = [e for e in entries if e.get("name", e["key"].rsplit("/", 1)[-1]).upper()
               == "TUBEBR19.PARQUET" and
               e["key"].startswith("public/data/ftp/sinan/TUBE/2019/")]
    if len(matches) != 1:
        raise ValueError("Catálogo PySUS 2019 ambíguo ou sem TUBEBR19.parquet")
    entry = matches[0]
    if (not entry.get("sha256") or not isinstance(entry.get("size"), int)
            or not 0 < entry["size"] <= MAX_PARQUET_BYTES):
        raise ValueError("Manifesto PySUS sem SHA-256/tamanho válido; baixar proibido")
    return entry


def plan_pysus_2019(root: Path | str = ROOT) -> dict:
    verify_local_dbc(root)
    try:
        from .pysus_gateway import _pysus
        # Only hydrate PySUS metadata; no patient data is downloaded.
        _pysus().sinan(disease="TUBE", year=YEAR, source="catalog",
                       download=False, as_dataframe=False)
        entry = _choose_entry(manifest("TUBE", YEAR))
    except ImportError as exc:
        raise RuntimeError("Dependencias PySUS ausentes; instale extras de ingestao") from exc
    return {
        "stage": "METADATA_ONLY_PARQUET_CANDIDATE_NOT_VERIFIED",
        "ano": YEAR, "dbc_sha256": PINNED_SHA256,
        "parquet_key": entry["key"], "parquet_bytes_catalogo": entry["size"],
        "parquet_sha256_catalogo": entry["sha256"],
        "parquet_conteudo_baixado": False,
        "projecao_4_campos_comparada": False,
        "equivalencia_integral_verificada": False,
        "status_final_homologado": False,
        "publicacao_autorizada": False,
    }


def _norm(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    value = str(value).strip()
    if not value or value.lower() in ("nan", "none", "null", "<na>"):
        return None
    # Arrow numeric columns may become 123456.0, while DBF char fields
    # contain 123456. Do not alter leading zeros.
    if value.endswith(".0") and value[:-2].isdigit():
        value = value[:-2]
    return value


def _projected_rows(path: Path):
    import pyarrow.parquet as pq
    with pq.ParquetFile(path) as reader:
        names = reader.schema_arrow.names
        mapping = {str(n).upper(): n for n in names}
        if len(mapping) != len(names) or not all(n in mapping for n in FIELDS):
            raise ValueError("Esquema Parquet sem os quatro campos exigidos")
        selected = [mapping[name] for name in FIELDS]
        for batch in reader.iter_batches(columns=selected, batch_size=2048):
            for row in batch.to_pylist():
                yield tuple(_norm(row.get(key)) for key in selected)


def compare_projected_parquets(left: Path, right: Path, scratch_db: Path) -> bool:
    """Exact multiplicity comparison on normalized 4-field tuples; no row output."""
    with closing(sqlite3.connect(str(scratch_db))) as con:
        con.execute("CREATE TABLE comparison (k TEXT PRIMARY KEY, left_n INT NOT NULL DEFAULT 0, right_n INT NOT NULL DEFAULT 0)")
        totals = []
        for path, column in ((left, "left_n"), (right, "right_n")):
            total = 0
            query = ("INSERT INTO comparison(k, " + column + ") VALUES(?, 1) "
                     "ON CONFLICT(k) DO UPDATE SET " + column + "=" + column + "+1")
            buffer = []
            for row in _projected_rows(path):
                buffer.append((json.dumps(row, ensure_ascii=False, separators=(",", ":")),))
                total += 1
                if len(buffer) == 2048:
                    con.executemany(query, buffer)
                    buffer.clear()
            if buffer:
                con.executemany(query, buffer)
            totals.append(total)
        if not all(totals):
            raise ValueError("Arquivo sem registros: concordancia nao testavel")
        difference = con.execute(
            "SELECT 1 FROM comparison WHERE left_n != right_n LIMIT 1"
        ).fetchone()
        return totals[0] == totals[1] and difference is None


def compare_local_2019(root: Path | str = ROOT) -> dict:
    source = verify_local_dbc(root)
    plan = plan_pysus_2019(root)
    entry = {"key": plan["parquet_key"],
             "size": plan["parquet_bytes_catalogo"],
             "sha256": plan["parquet_sha256_catalogo"]}
    root = source.parent
    with TemporaryDirectory(prefix="concordancia-", dir=str(root)) as tmp:
        temp = Path(tmp)
        projection = temp / "TUBEBR19-dbc-projecao.parquet"
        # Validate/convert DBC locally *before* downloading the remote
        # Parquet, to avoid repeating network traffic on converter errors.
        try:
            process = subprocess.run(
                [sys.executable, "-m", "scripts._projetar_dbc_tb2019",
                 "--source", str(source), "--target", str(projection)],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True, text=True, timeout=240, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Conversao DBC excedeu limite de execucao; "
                               "nenhuma equivalencia inferida.") from None
        if process.returncode != 0 or not projection.is_file():
            # The child prints only a bounded, structured error descriptor.
            # Never surface raw stderr, which might include personal records.
            stage, code = "PROCESS", "EXIT_" + str(process.returncode)
            for line in reversed(process.stderr.splitlines()):
                try:
                    detail = json.loads(line)
                except (ValueError, TypeError):
                    continue
                if not isinstance(detail, dict) or detail.get("status") != "error":
                    continue
                candidate_stage, candidate_code = detail.get("stage"), detail.get("code")
                import re
                if all(isinstance(v, str) and re.fullmatch(r"[A-Za-z0-9_]{1,64}", v)
                       for v in (candidate_stage, candidate_code)):
                    stage, code = candidate_stage, candidate_code
                    break
            raise RuntimeError(
                f"Conversao DBC local falhou: etapa={stage}, codigo={code}; "
                "nenhuma equivalencia inferida."
            )
        parquet = temp / "TUBEBR19-pysus.parquet"
        observed_sha, _ = download_mirror_entry(entry, parquet)
        if observed_sha != entry["sha256"]:
            raise ValueError("SHA-256 Parquet divergente")
        equal = compare_projected_parquets(projection, parquet,
                                           temp / "comparacao.sqlite3")
        return {
            "stage": "FOUR_COLUMN_RESEARCH_COMPARISON_NOT_HOMOLOGATED",
            "dbc_sha256_recebido": PINNED_SHA256,
            "parquet_sha256_verificado": observed_sha,
            "parquet_key": entry["key"],
            "campos_comparados": list(FIELDS),
            "multiconjunto_4_campos_igual": equal,
            "equivalencia_integral_verificada": False,
            "status_final_homologado": False,
            "publicacao_autorizada": False,
            "observacao": ("Comparacao local de quatro campos com multiplicidades. "
                          "Mesmo se igual, nao demonstra equivalencia integral "
                          "ou validação epidemiologica.")
        }
