"""Static aggregate release contract; imports no databases or health microdata.

Only a manually reviewed, SHA-256 pinned, tightly shaped package can be read
by the separate approved MCP service. This verifies format, not real-world
lawfulness, reviewer identities or anonymization.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "sinan-aggregates-v1"
K_MIN = 20
PARTITION_MIN = 100
MAX_RELEASE_BYTES = 65_536
UF_SIGLAS = frozenset("""AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO""".split())
CODES = {
    "sexo": frozenset({"F", "M", "I", "ignorado/ausente"}),
    "raca_cor": frozenset({"1", "2", "3", "4", "5", "9", "ignorado/ausente"}),
}
REFERENCE = ("https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/"
             "dados-em-transparencia-ativa/svsa/agravos-de-notificacoes/agravos-de-notificacoes")
HEX64 = re.compile(r"[a-f0-9]{64}\Z")

def _canonical(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def candidate_digest(candidate: dict) -> str:
    return hashlib.sha256(_canonical(candidate)).hexdigest()


def _validate_partition(agravo: str, ano: int, uf: str, group: str) -> tuple[str, int, str, str]:
    if not isinstance(agravo, str) or not re.fullmatch(r"[A-Z]{4}", agravo):
        raise ValueError("Agravo deve ter quatro letras maiúsculas")
    agravo = agravo.upper()
    if agravo not in {"TUBE", "DENG"}:
        raise ValueError("Somente TUBE e DENG possuem projeções demográficas-piloto")
    if type(ano) is not int or not 2000 <= ano <= 2100:
        raise ValueError("Informe um único ano inteiro de arquivo entre 2000 e 2100")
    if type(uf) is not str or uf.strip().upper() not in UF_SIGLAS:
        raise ValueError("Informe uma única UF válida")
    if type(group) is not str or group not in CODES:
        raise ValueError("Somente sexo ou raca_cor; cruzamentos não são liberados")
    return agravo, ano, uf.strip().upper(), group


def validate_candidate(candidate: Any) -> None:
    """Strict validation of a single static candidate. No auto-approval."""
    if not isinstance(candidate, dict) or set(candidate) != {
        "schema_version", "stage", "scope", "source", "policy", "cells", "limitations"
    } or candidate["schema_version"] != SCHEMA or candidate["stage"] != "UNAPPROVED_RESEARCH_CANDIDATE":
        raise ValueError("Formato de candidato de divulgação inválido")
    scope = candidate["scope"]
    if not isinstance(scope, dict) or set(scope) != {
        "agravo", "ano_do_arquivo", "uf", "dimensao", "data_type", "ano_nao_e_diagnostico"
    }:
        raise ValueError("Escopo inválido")
    disease, year, region, group = _validate_partition(
        scope["agravo"], scope["ano_do_arquivo"], scope["uf"], scope["dimensao"])
    if (scope["agravo"], scope["uf"]) != (disease, region) or scope["data_type"] != "registro" or scope["ano_nao_e_diagnostico"] is not True:
        raise ValueError("Escopo com metadados inconsistentes")
    src = candidate["source"]
    if not isinstance(src, dict) or set(src) != {
        "tipo", "status_informado", "fingerprint_sha256",
        "importado_em_utc", "referencia_oficial"
    } or not isinstance(src["fingerprint_sha256"], str) or not HEX64.fullmatch(src["fingerprint_sha256"]):
        raise ValueError("Proveniência inválida")
    if not isinstance(src["tipo"], str) or src["tipo"] not in {"synthetic", "csv-local"} and not src["tipo"].startswith("pysus"):
        raise ValueError("Fonte inválida")
    if (not isinstance(src["status_informado"], str)
            or src["status_informado"] not in {"desconhecido", "preliminar", "final"}
            or src["referencia_oficial"] != REFERENCE):
        raise ValueError("Status ou referência oficial inválida")
    if not isinstance(src["importado_em_utc"], str) or len(src["importado_em_utc"]) > 64:
        raise ValueError("Data de importação inválida")
    expected_policy = {
        "min_cell": K_MIN, "min_partition": PARTITION_MIN,
        "one_dimension": True, "outcomes_excluded": True,
        "not_official_indicator": True, "not_formal_anonymization": True,
    }
    if candidate["policy"] != expected_policy:
        raise ValueError("Política de divulgação alterada")
    cells = candidate["cells"]
    if not isinstance(cells, list) or not 2 <= len(cells) <= len(CODES[group]):
        raise ValueError("Número inválido de categorias")
    seen = set()
    total = 0
    for cell in cells:
        if not isinstance(cell, dict) or set(cell) != {"categoria", "registros"}:
            raise ValueError("Campo de célula inesperado")
        category, n = cell["categoria"], cell["registros"]
        if not isinstance(category, str) or category not in CODES[group] or category in seen:
            raise ValueError("Categoria inválida/duplicada")
        if type(n) is not int or not K_MIN <= n <= 50_000_000:
            raise ValueError("Contagem menor que mínimo autorizado ou inválida")
        seen.add(category)
        total += n
    if total < PARTITION_MIN:
        raise ValueError("Partição menor que o limite")
    if not isinstance(candidate["limitations"], str) or len(candidate["limitations"]) > 350:
        raise ValueError("Limitações inválidas")
    if len(_canonical(candidate)) > MAX_RELEASE_BYTES:
        raise ValueError("Pacote excessivamente grande")


def load_approved_release(path: str | Path, sha256: str) -> dict:
    """Validate independent manual approval and immutable checksum.

    Approval records document a review; the program cannot verify identities
    or guarantee anonymity. A public deployment needs another security review.
    """
    if not isinstance(sha256, str) or not HEX64.fullmatch(sha256):
        raise ValueError("SHA-256 explícito obrigatório para pacote publicado")
    file = Path(path)
    if not file.is_file() or file.stat().st_size > MAX_RELEASE_BYTES:
        raise ValueError("Pacote aprovado ausente ou excessivamente grande")
    raw = file.read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha256:
        raise ValueError("Checksum do pacote difere do aprovado")
    def strict_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Chave JSON duplicada")
            result[key] = value
        return result

    try:
        obj = json.loads(raw, object_pairs_hook=strict_pairs)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("Pacote JSON inválido") from exc
    if not isinstance(obj, dict) or set(obj) != {
        "stage", "candidate", "candidate_sha256", "review"
    } or obj["stage"] != "APPROVED_PUBLIC_AGGREGATE":
        raise ValueError("Pacote não recebeu aprovação explícita")
    candidate = obj["candidate"]
    validate_candidate(candidate)
    if obj["candidate_sha256"] != candidate_digest(candidate):
        raise ValueError("Candidato foi modificado após a revisão")
    if candidate["source"]["tipo"] == "synthetic":
        raise ValueError("Demonstração sintética não pode ser declarada como agregado real")
    # The preview deliberately refuses unknown source status.
    if candidate["source"]["status_informado"] != "final":
        raise ValueError("Fonte sem status final verificado: publicação bloqueada")
    review = obj["review"]
    if not isinstance(review, dict) or set(review) != {
        "privacy_reviewer", "scientific_reviewer", "review_reference",
        "publication_authorized", "cross_release_comparison_reviewed"
    } or review["publication_authorized"] is not True or review["cross_release_comparison_reviewed"] is not True:
        raise ValueError("Registro independente de aprovação incompleto")
    names = [review["privacy_reviewer"], review["scientific_reviewer"]]
    if not all(isinstance(n, str) and 4 <= len(n.strip()) <= 120 for n in names) or names[0] == names[1]:
        raise ValueError("Revisões independentes não identificadas")
    if not isinstance(review["review_reference"], str) or not 5 <= len(review["review_reference"]) <= 180:
        raise ValueError("Referência de parecer ausente")
    if len(_canonical(obj)) > MAX_RELEASE_BYTES:
        raise ValueError("Pacote aprovado excessivamente grande")
    return obj
