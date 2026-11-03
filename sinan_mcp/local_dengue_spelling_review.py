"""Local-only, unapproved spelling hypotheses between official PDF fields and CSV headers.

Reads private *metadata reports* only, plus the locally pinned PDF. Does not
open or parse the CSV, ZIP, patient records, or their values. Never exposes
unrecognized CSV field names on stdout, MCP, HTTP or in repo artifacts.

A single insertion/deletion is NOT proof of semantic equivalence; this module
MUST NOT change or approve schema contracts or population data.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re

from .local_dengue_dictionary_crosswalk import examinar_pdf_dengue_local, RESOURCE_ID
from .local_dengue_csv_extra_review import (
    PRIVATE_SCHEMA, _load_previous_crosswalk,
)
from .local_schema_review import _reject_duplicate_keys

FIELD = re.compile(r"[A-Z][A-Z0-9_]{0,31}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
MAX_SIDECAR_BYTES = 128_000
MAX_EXTRA_NAMES = 2000
OUTPUT_SCHEMA = "sinan-private-dengue-header-spelling-hypotheses-v1"


def _exactly_one_insert_or_delete(first: str, second: str) -> bool:
    """Conservative name-only mismatch: exactly one extra character."""
    if min(len(first), len(second)) < 7:
        return False
    shorter, longer = sorted((first, second), key=len)
    return (len(longer) == len(shorter) + 1
            and any(longer[:i] + longer[i+1:] == shorter
                    for i in range(len(longer))))


def _load_sidecar(path: str | Path) -> dict:
    p = Path(path).expanduser()
    if (p.is_symlink() or not p.is_file()
            or not 2 <= p.stat().st_size <= MAX_SIDECAR_BYTES):
        raise ValueError("Lista privada anterior ausente ou fora do limite")
    try:
        with p.open("r", encoding="utf-8") as f:
            obj = json.load(f, object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("Metadados privados inválidos") from None
    if (not isinstance(obj, dict)
            or obj.get("schema_version") != PRIVATE_SCHEMA
            or obj.get("resource_id") != RESOURCE_ID
            or obj.get("publicacao_autorizada") is not False
            or obj.get("nomes_publicaveis") is not False
            or obj.get("revisao_independente") != "PENDENTE"
            or obj.get("n_linhas_clinicas_lidas") != 0):
        raise ValueError("Revisão anterior inválida ou com autorização inesperada")
    extra = obj.get("nomes_adicionais_csv_nao_documentados_no_pdf")
    if (not isinstance(extra, list)
            or not 1 <= len(extra) <= MAX_EXTRA_NAMES
            or type(obj.get("quantidade")) is not int
            or len(extra) != obj["quantidade"]
            or any(not isinstance(n, str) or not FIELD.fullmatch(n)
                   for n in extra)
            or extra != sorted(set(extra))):
        raise ValueError("Nomes do cabeçalho privado não conferem")
    if (not isinstance(obj.get("pdf_sha256_local"), str)
            or not HASH.fullmatch(obj["pdf_sha256_local"])
            or not isinstance(obj.get("zip_sha256_local"), str)
            or not HASH.fullmatch(obj["zip_sha256_local"])):
        raise ValueError("Hashes de revisão local inválidos")
    return obj


def gerar_hipoteses_grafia_dengue_local(
    pdf_path: str | Path,
    parecer_path: str | Path,
    extras_path: str | Path,
    destino: str | Path,
) -> dict:
    """Save unapproved name-only hypotheses in an exclusively created LOCAL file."""
    pdf = examinar_pdf_dengue_local(pdf_path)
    previous = _load_previous_crosswalk(parecer_path)
    private = _load_sidecar(extras_path)
    expected_pdf = pdf["pdf_sha256_local"]
    if (previous.get("pdf_atual_sha256_local") != expected_pdf
            or private["pdf_sha256_local"] != expected_pdf
            or previous.get("zip_sha256_local") != private["zip_sha256_local"]):
        raise ValueError("Edições documentais ou ZIPs não correspondem")
    extra = private["nomes_adicionais_csv_nao_documentados_no_pdf"]
    missing = previous.get("nomes_pdf_atual_ausentes_csv")
    if (not isinstance(missing, list)
            or any(not isinstance(n, str) or n not in pdf["nomes_documentais"]
                   for n in missing)
            or len(extra) != previous.get("quantidade_csv_fora_pdf_atual")):
        raise ValueError("Parecer anterior e extras não se conciliam")

    hypotheses = []
    unresolved = []
    for observed in extra:
        possible = sorted(
            documented for documented in missing
            if _exactly_one_insert_or_delete(observed, documented)
        )
        if possible:
            hypotheses.append({
                "nome_observado_csv": observed,
                "candidatos_nomes_pdf_publico": possible,
                "tipo": "UMA_INSERCAO_OU_REMOCAO_DE_CARACTERE",
                "situacao": "GRAFIA_CANDIDATA_NAO_VALIDADA",
                "mesmo_significado_clinico_confirmado": False,
                "alias_de_producao_autorizado": False,
            })
        else:
            unresolved.append(observed)

    target = Path(destino).expanduser()
    if (target.is_symlink() or target.suffix.lower() != ".json"
            or not target.parent.is_dir() or target.parent.is_symlink()):
        raise ValueError("Destino privado inválido")
    report = {
        "schema_version": OUTPUT_SCHEMA,
        "resource_id": RESOURCE_ID,
        "pdf_sha256_local": expected_pdf,
        "zip_sha256_local": private["zip_sha256_local"],
        "hipoteses_de_grafia": hypotheses,
        "nomes_csv_sem_correspondencia_de_um_caractere": unresolved,
        "n_extras": len(extra),
        "n_hipoteses_grafia": len(hypotheses),
        "n_sem_correspondencia": len(unresolved),
        "n_linhas_de_pacientes_lidas": 0,
        "revisao_independente": "PENDENTE",
        "equivalencia_semantica_verificada": False,
        "alias_automatico_habilitado": False,
        "nomes_publicaveis": False,
        "autorizacao_analise_real": False,
        "publicacao_autorizada": False,
        "aviso": (
            "HIPOTESES PRIVADAS baseadas somente em grafia, nao aprovacao de "
            "nomes, tipos, dominios ou equivalencia epidemiologica. "
            "Nao enviar este JSON ou os nomes CSV ao GitHub ou MCP."
        ),
    }
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except BaseException:
        try:
            target.unlink()
        except OSError:
            pass
        raise
    return {
        "extras_avaliados": len(extra),
        "hipoteses_grafia": len(hypotheses),
        "sem_correspondencia": len(unresolved),
        "revisao_independente": "PENDENTE",
        "nomes_no_terminal": False,
        "pacientes_lidos": 0,
        "publicacao_autorizada": False,
    }
