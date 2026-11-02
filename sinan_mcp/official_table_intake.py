"""Local-only intake for curated TABNET/publication aggregate tables.

This intentionally NEVER fetches URLs, constructs releases, executes arbitrary
queries, or writes to the public MCP. A source address + hash are
operator-declared metadata, NOT verified accuracy or authority.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

SCHEMA = "sinan-official-tabulation-candidate-v1"
STAGE = "UNAPPROVED_OFFICIAL_TABULATION"
K_MIN = 20
TOTAL_MIN = 100
MAX_BYTES = 65_536
VALID_DOMAINS = frozenset({
    "datasus.saude.gov.br",
    "tabnet.datasus.gov.br",
    "www.gov.br",
    "portalsinan.saude.gov.br",
})
UF = frozenset("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO BR".split())
REFERENCE_TIMES = frozenset({
    "ano_notificacao", "ano_diagnostico", "ano_arquivo", "ano_encerramento",
    "ano_ocorrencia",
})

# Accepted one-dimensional codes and familiar TABNET category labels. A free
# text category might encode a second dimension, age, place or individual detail.
# These are syntax checks only; omitted suppressed categories still require
# independent disclosure review against the ORIGINAL complete tabulation.
CATEGORY_ALIASES = {
    "sexo": {
        "f": "F", "feminino": "F", "m": "M", "masculino": "M",
        "i": "I", "ignorado": "I", "ignorada": "I",
        "ignorado/ausente": "I", "nao informado": "I",
        "sem informacao": "I",
    },
    "raca_cor": {
        "1": "1", "branca": "1", "branco": "1",
        "2": "2", "preta": "2", "preto": "2",
        "3": "3", "amarela": "3", "amarelo": "3",
        "4": "4", "parda": "4", "pardo": "4",
        "5": "5", "indigena": "5",
        "9": "9", "ignorado": "9", "ignorada": "9",
        "ignorado/ausente": "9", "nao informado": "9",
        "sem informacao": "9",
    },
}


def _normalized_category(value: str) -> str:
    s = unicodedata.normalize("NFKD", value.casefold().strip())
    return " ".join("".join(x for x in s if not unicodedata.combining(x)).split())


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON com chaves duplicadas não é admitido")
        result[key] = value
    return result


def _canonical(doc: dict) -> bytes:
    return json.dumps(doc, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def _check_text(text: object, *, minimum: int = 1, maximum: int = 120) -> str:
    if (not isinstance(text, str) or not minimum <= len(text.strip()) <= maximum
            or any(ord(c) < 32 for c in text)):
        raise ValueError("Metadado textual inválido")
    return text.strip()


def validate_official_tabulation(obj: object) -> dict:
    """Fail closed on small cells, unsupported schema and unknown provenance.

    Format checks are NOT validation against the true TABNET page, independent
    statistical disclosure review, or legal authorization.
    """
    if not isinstance(obj, dict) or set(obj) != {
        "schema_version", "stage", "source", "scope", "cells", "limitations"
    } or obj["schema_version"] != SCHEMA or obj["stage"] != STAGE:
        raise ValueError("Pacote não é candidato de tabela oficial compatível")
    src = obj["source"]
    if not isinstance(src, dict) or set(src) != {
        "url", "titulo_tabela", "extracao_utc", "sha256_arquivo_origem",
        "filtros_tabulacao", "estado_consolidacao"
    }:
        raise ValueError("Proveniência incompleta")
    url = _check_text(src["url"], maximum=1024)
    parsed = urlparse(url)
    if (parsed.scheme != "https" or parsed.hostname not in VALID_DOMAINS
            or parsed.username is not None or parsed.password is not None
            or parsed.port not in (None, 443)
            or parsed.fragment or parsed.query and len(parsed.query) > 500):
        raise ValueError("Somente HTTPS de páginas oficiais permitidas")
    _check_text(src["titulo_tabela"], maximum=200)
    _check_text(src["filtros_tabulacao"], minimum=10, maximum=1000)
    raw_hash = src["sha256_arquivo_origem"]
    if not isinstance(raw_hash, str) or not re.fullmatch("[0-9a-f]{64}", raw_hash):
        raise ValueError("SHA-256 da tabulação original obrigatório")
    if src["estado_consolidacao"] not in {"desconhecido", "preliminar", "final"}:
        raise ValueError("Estado de consolidação inválido")
    timestamp = _check_text(src["extracao_utc"], maximum=40)
    try:
        when = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Data da extração inválida") from exc
    if when.tzinfo is None or when.utcoffset().total_seconds() != 0 or not 2000 <= when.year <= 2100:
        raise ValueError("Extração deve conter horário UTC")
    scope = obj["scope"]
    if not isinstance(scope, dict) or set(scope) != {
        "agravo_codigo_interno", "agravo_nome", "uf", "ano_inicio",
        "ano_fim", "tipo_ano", "indicador", "dimensao"
    }:
        raise ValueError("Escopo incompleto")
    code = scope["agravo_codigo_interno"]
    if not isinstance(code, str) or not re.fullmatch("[A-Z]{4,8}", code):
        raise ValueError("Código interno inválido")
    _check_text(scope["agravo_nome"])
    if scope["uf"] not in UF:
        raise ValueError("Território inválido")
    if (type(scope["ano_inicio"]) is not int or type(scope["ano_fim"]) is not int
            or not 2000 <= scope["ano_inicio"] <= scope["ano_fim"] <= 2100):
        raise ValueError("Anos inválidos")
    if scope["tipo_ano"] not in REFERENCE_TIMES:
        raise ValueError("Tipo de período não definido")
    if scope["indicador"] != "registros_tabnet":
        raise ValueError("Este estágio só permite contagem de registros em TABNET")
    if scope["dimensao"] not in {"sexo", "raca_cor"}:
        raise ValueError("Somente uma dimensão simples permitida")
    rows = obj["cells"]
    if not isinstance(rows, list) or not 2 <= len(rows) <= 12:
        raise ValueError("Quantidade de células inválida")
    seen: set[str] = set()
    total = 0
    for cell in rows:
        if not isinstance(cell, dict) or set(cell) != {"categoria", "registros"}:
            raise ValueError("Estrutura de célula inválida")
        category = _check_text(cell["categoria"], maximum=50)
        normalized = _normalized_category(category)
        canonical = CATEGORY_ALIASES[scope["dimensao"]].get(normalized)
        if canonical is None:
            raise ValueError("Categoria não reconhecida para a dimensão declarada")
        if canonical in seen:
            raise ValueError("Categoria duplicada ou alias equivalente")
        seen.add(canonical)
        n = cell["registros"]
        if type(n) is not int or n < K_MIN or n > 100_000_000:
            raise ValueError("Célula abaixo do limite: não é divulgável")
        total += n
    if total < TOTAL_MIN:
        raise ValueError("Partição inteira abaixo do mínimo")
    _check_text(obj["limitations"], minimum=20, maximum=800)
    if len(_canonical(obj)) > MAX_BYTES:
        raise ValueError("Candidato acima do limite")
    return obj


def prepare_private_tabnet_candidate(path: str | Path,
                                     *, review_dir: str | Path = "./data/review-packages") -> Path:
    """Validate JSON provided locally by an operator, save private candidate.

    Never fetch URL or remotely confirm its contents. Never publish a release.
    """
    source = Path(path).expanduser().resolve(strict=True)
    if not source.is_file() or source.stat().st_size > MAX_BYTES:
        raise ValueError("Arquivo de tabela ausente ou excessivamente grande")
    try:
        obj = json.loads(source.read_text(encoding="utf-8"),
                         object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("JSON de tabela inválido") from exc
    validate_official_tabulation(obj)
    private_root = Path.cwd().resolve() / "data"
    # A symlinked data/ directory can redirect a private candidate into a
    # public checkout or a synchronized folder despite the .gitignore rule.
    if private_root.is_symlink():
        raise ValueError("Diretório data/ não pode ser link simbólico")
    target_dir = Path(review_dir).expanduser().resolve()
    if not target_dir.is_relative_to(private_root):
        raise ValueError("A saída precisa permanecer dentro de data/ ignorado pelo Git")
    target_dir.mkdir(parents=True, exist_ok=True)
    raw = _canonical(obj)
    digest = hashlib.sha256(raw).hexdigest()
    scope = obj["scope"]
    filename = (f"tabnet-{scope['agravo_codigo_interno']}-{scope['uf']}-"
                f"{scope['ano_inicio']}-{scope['ano_fim']}-{digest[:12]}.candidate.json")
    destination = target_dir / filename
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw + b"\n")
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return destination
