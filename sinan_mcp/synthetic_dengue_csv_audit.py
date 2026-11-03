"""Administrative DENG/2024 SYNTHETIC-ONLY raw CSV QA rehearsal.

This CLI has NO --zip/--csv/--db input, no external readers, no network
calls, and no path through which patient records could be supplied.
It generates its entire tiny test dataset IN MEMORY. Its low-level parser
requires a synthetic marker in EVERY row. That marker is a guardrail,
NOT proof that arbitrary third-party data are synthetic.

The checks are programming exercises, not clinical validation.
They must NEVER advance roadmap gates or authorize publication.
"""
from __future__ import annotations

import csv
from datetime import date
import hashlib
import io
import json
import os
from pathlib import Path
import re

from .local_dengue_dictionary_crosswalk import RESOURCE_ID
from .local_dengue_quality_protocol import PLAN_SCHEMA, CHECKPOINTS
from .roadmap_readiness import _strict_json_pairs, SHA

SCHEMA = "sinan-private-dengue-synthetic-csv-quality-rehearsal-v1"
MARKER = "__SYNTHETIC_ONLY__"
MARKER_VALUE = "EXEMPLO_ARTIFICIAL_SEM_PACIENTES"
COLUMNS = (
    "DT_NOTIFIC", "DT_SIN_PRI", "SG_UF_NOT", "SG_UF", "UF",
    "CLASSI_FIN", "CLINC_CHIK",
)
HEADER = (MARKER, *COLUMNS)
MAX_CSV_BYTES = 32768
MAX_ROWS = 64
MAX_FIELD_CHARS = 256
MAX_PLAN_BYTES = 32768
DATE_FORMAT = re.compile(r"\d{4}-\d{2}-\d{2}\Z")

# Hand-authored illustrative data: NOT derived from or fitted to SINAN data.
# These code strings are unvalidated tokens, NOT clinical code dictionaries.
ROWS = (
    (MARKER_VALUE, "2024-01-15", "2024-01-12", "22", "22", "22", "1", ""),
    (MARKER_VALUE, "2024-01-15", "2024-01-12", "22", "22", "22", "1", ""),
    (MARKER_VALUE, "2024-02-10", "", "22", "", "", "", ""),
    (MARKER_VALUE, "nao-e-data", "2024-02-01", "22", "22", "22", "8", ""),
    (MARKER_VALUE, "2024-03-02", "2024-03-05", "22", "22", "22", "11", "1"),
    (MARKER_VALUE, "2023-12-31", "2023-12-30", "22", "22", "22", "12", ""),
)


def _fixture() -> str:
    buf = io.StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(ROWS)
    return buf.getvalue()


def _date_or_none(value: str) -> tuple[date | None, bool]:
    if not value:
        return None, False
    if not DATE_FORMAT.fullmatch(value):
        return None, True
    try:
        return date.fromisoformat(value), False
    except ValueError:
        return None, True


def _scan_marked_synthetic_csv(raw: str) -> dict:
    """Exercise raw CSV shape and exploratory counts, never interpret cases."""
    if not isinstance(raw, str) or not 1 <= len(raw.encode("utf-8")) <= MAX_CSV_BYTES:
        raise ValueError("Fixture sintetica fora do limite de bytes")
    try:
        rows = csv.reader(io.StringIO(raw, newline=""), strict=True)
        header = next(rows)
        if tuple(header) != HEADER:
            raise ValueError("Cabecalho sintetico divergente ou repetido")
        n = 0
        missing = {name: 0 for name in COLUMNS}
        date_bad = {name: 0 for name in ("DT_NOTIFIC", "DT_SIN_PRI")}
        after_notification = 0
        notification_other_year = 0
        repeated_identical = 0
        seen: set[tuple[str, ...]] = set()
        for line in rows:
            n += 1
            if n > MAX_ROWS or len(line) != len(HEADER):
                raise ValueError("CSV sintetico com linha fora do esquema")
            if any(len(item) > MAX_FIELD_CHARS for item in line):
                raise ValueError("Campo de fixture excede limite")
            if line[0] != MARKER_VALUE:
                raise ValueError("Registro sem marcador artificial obrigatorio")
            record = tuple(line)
            if record in seen:
                repeated_identical += 1
            seen.add(record)
            values = dict(zip(COLUMNS, line[1:]))
            for name, val in values.items():
                missing[name] += int(not val.strip())
            notification, bad1 = _date_or_none(values["DT_NOTIFIC"])
            symptoms, bad2 = _date_or_none(values["DT_SIN_PRI"])
            date_bad["DT_NOTIFIC"] += int(bad1)
            date_bad["DT_SIN_PRI"] += int(bad2)
            if notification is not None and notification.year != 2024:
                notification_other_year += 1
            if notification is not None and symptoms is not None:
                after_notification += int(symptoms > notification)
        if n < 1:
            raise ValueError("Fixture sintetica vazia")
    except (csv.Error, UnicodeError, StopIteration):
        raise ValueError("Leitura do CSV sintetico recusada") from None
    return {
        "linhas_sinteticas": n,
        "colunas_incluindo_marcador": len(HEADER),
        "ausentes_por_coluna_sintetica": missing,
        "datas_literais_invalidas": date_bad,
        "notificacoes_fora_do_ano_rotulado_hipotetico": notification_other_year,
        "sequencias_sintomas_posteriores_a_notificacao_para_revisao": after_notification,
        "linhas_inteiras_textualmente_identicas_alem_da_primeira": repeated_identical,
        "tuplas_identicas_nao_provam_duplicidade_de_pacientes": True,
        "CLASSI_FIN_dominios_inferidos": False,
        "UF_semantica_inferida": False,
        "CLINC_CHIK_alias_automatico": False,
        "casos_reais_contados": False,
    }


def _assert_synthetic_protections() -> int:
    clean = _fixture()
    malformed = [
        clean.replace(MARKER_VALUE, "SEM_MARCADOR", 1),
        clean.replace("DT_NOTIFIC,", "DT_NOTIFIC,DT_NOTIFIC,", 1),
        clean + "coluna,insuficiente\n",
        "not,a,synthetic,dataset\n",
    ]
    rejected = 0
    for sample in malformed:
        try:
            _scan_marked_synthetic_csv(sample)
        except ValueError:
            rejected += 1
    if rejected != len(malformed):
        raise ValueError("Protecoes de fixture sintetica nao passaram")
    return rejected


def _plan_digest(path: str | Path) -> str:
    p = Path(path).expanduser()
    if (p.is_symlink() or not p.is_file()
            or p.suffix.lower() != ".json"
            or not 2 <= p.stat().st_size <= MAX_PLAN_BYTES):
        raise ValueError("Plano privado local ausente ou fora dos limites")
    raw = p.read_bytes()
    if len(raw) > MAX_PLAN_BYTES:
        raise ValueError("Plano privado excede tamanho maximo")
    try:
        plan = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_json_pairs)
    except (ValueError, UnicodeError):
        raise ValueError("Plano privado JSON invalido") from None
    if (not isinstance(plan, dict)
            or plan.get("schema_version") != PLAN_SCHEMA
            or plan.get("scope") != {
                "agravo": "DENG", "ano_do_arquivo": 2024,
                "resource_id": RESOURCE_ID,
            }
            or plan.get("status") != "PLANO_PRIVADO_NAO_VALIDADO"
            or plan.get("qualidade_dados_clinicos_auditada") is not False
            or plan.get("indicadores_reais_calculados") is not False
            or plan.get("apto_analise_ou_publicacao") is not False
            or plan.get("roadmap_quality_gate_alterado") is not False
            or plan.get("n_linhas_clinicas_lidas") != 0):
        raise ValueError("Plano nao representa candidato nao validado de DENG/2024")
    checkpoints = plan.get("quality_checkpoints")
    if (not isinstance(checkpoints, dict) or set(checkpoints) != set(CHECKPOINTS)
            or any(
                not isinstance(obj, dict)
                or obj.get("status") != "PENDENTE"
                or obj.get("definicao_de_aceite") != CHECKPOINTS[name]
                for name, obj in checkpoints.items()
            )):
        raise ValueError("Checkpoints locais nao estao no estado esperado")
    for field in ("parecer_esquema_sha256_local", "dossie_fonte_sha256_local",
                  "zip_sha256_local"):
        v = plan.get(field)
        if not isinstance(v, str) or not SHA.fullmatch(v):
            raise ValueError("Plano sem vinculacao documental SHA-256 valida")
    return hashlib.sha256(raw).hexdigest()


def auditar_fixture_dengue_local(
    plano_path: str | Path, destino: str | Path,
) -> dict:
    """Create a NEW private diagnostic from embedded synthetic rows only."""
    plan_hash = _plan_digest(plano_path)
    counts = _scan_marked_synthetic_csv(_fixture())
    denied = _assert_synthetic_protections()
    report = {
        "schema_version": SCHEMA,
        "agravo_apenas_de_contexto": "DENG",
        "ano_arquivo_apenas_de_contexto": 2024,
        "plano_privado_sha256_local": plan_hash,
        "origem_dados": "FIXTURE_INTERNA_100_POR_CENTO_SINTETICA",
        "referencia_csv_real_lida": False,
        "caminhos_csv_ou_zip_aceitos": False,
        "registros_reais_lidos": 0,
        "verificacoes_sinteticas": counts,
        "cenarios_de_entrada_invalida_recusados": denied,
        "checkpoints_cientificos_validados": 0,
        "qualidade_coorte_homologada": False,
        "roadmap_alterado": False,
        "publicacao_autorizada": False,
        "status": "SIMULACAO_TECNICA_SEM_DADOS_CLINICOS",
        "aviso": (
            "Todos os numeros neste arquivo sao ARTIFICIAIS. Nao sao "
            "estatisticas SINAN. Nenhuma definicao de caso, codigo clinico, "
            "deduplicacao ou decisao epidemiologica foi homologada."
        ),
    }
    out = Path(destino).expanduser()
    if (out.is_symlink() or out.suffix.lower() != ".json"
            or not out.parent.is_dir() or out.parent.is_symlink()
            or out.parent.resolve() != Path(plano_path).expanduser().parent.resolve()):
        raise ValueError("Saida privada deve estar junto ao plano original")
    fd = os.open(str(out), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except BaseException:
        try:
            out.unlink()
        except OSError:
            pass
        raise
    return {
        "linhas_sinteticas": counts["linhas_sinteticas"],
        "casos_adversariais_recusados": denied,
        "registros_reais_lidos": 0,
        "checkpoints_cientificos_validados": 0,
        "status": report["status"],
        "publicacao_autorizada": False,
    }
