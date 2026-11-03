"""Offline proof-of-concept: versioned *synthetic* disease/year schema contracts.

Deliberately not hooked into real PySUS/CSV ingestion, release approvals, the
public MCP, or clinical interpretation. All contracts in this registry are
illustrative and MUST NOT be presented as confirmed official SINAN dictionaries.

Optional Pandera backend validates bounded CSV batches without returning or
logging values, columns rejected, row indices, sensitive paths or failure cases.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from importlib.resources import files
from pathlib import Path
from typing import Any

SCHEMA = "sinan-example-schema-contract-v1"
IDS = frozenset({"TUBE_2024_EXAMPLE", "DENG_2024_EXAMPLE"})
COLUMN_NAMES = frozenset({"ID_MN_RESI", "CS_SEXO", "CS_RACA", "SITUA_ENCE"})
PATTERNS = frozenset({"[0-9]{6}"})
MAX_CSV_BYTES = 64 * 1024 * 1024
MAX_BATCH = 512
MAX_VALUE_CHARS = 256


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("Contrato com chaves JSON duplicadas")
        out[key] = value
    return out


def load_example_contract(contract_id: str) -> dict[str, Any]:
    """Read only hard-coded, bundled names (not a user-selected path)."""
    if not isinstance(contract_id, str) or contract_id not in IDS:
        raise ValueError("Contrato de demonstração inexistente")
    path = files("sinan_mcp").joinpath("contracts", contract_id + ".json")
    doc = json.loads(path.read_text(encoding="utf-8"),
                     object_pairs_hook=_reject_duplicates)
    expected_keys = {
        "schema_version", "contract_id", "agravo_alias_interno",
        "ano_do_arquivo", "estado", "documento_oficial_verificado",
        "permissao_publicacao", "nota", "columns", "allow_extra_columns",
    }
    if not isinstance(doc, dict) or set(doc) != expected_keys:
        raise ValueError("Contrato com campos inesperados")
    if (doc["schema_version"] != SCHEMA or doc["contract_id"] != contract_id
            or doc["agravo_alias_interno"] != contract_id.split("_")[0]
            or type(doc["ano_do_arquivo"]) is not int
            or doc["ano_do_arquivo"] != int(contract_id.split("_")[1])
            or doc["estado"] != "DEMONSTRACAO_SINTETICA_NAO_VALIDADA"
            or doc["documento_oficial_verificado"] is not False
            or doc["permissao_publicacao"] is not False
            or doc["allow_extra_columns"] is not False):
        raise ValueError("Contrato não é um exemplo sintético restrito")
    columns = doc["columns"]
    if not isinstance(columns, list) or not 1 <= len(columns) <= 8:
        raise ValueError("Colunas de contrato inválidas")
    seen = set()
    for col in columns:
        if not isinstance(col, dict) or col.get("name") not in COLUMN_NAMES:
            raise ValueError("Coluna de contrato não autorizada")
        name = col["name"]
        if name in seen or col.get("required") is not True:
            raise ValueError("Contrato repetido ou requerimento inválido")
        seen.add(name)
        if col.get("kind") == "enum":
            if set(col) != {"name", "kind", "values", "required"}:
                raise ValueError("Campos de enum inválidos")
            vals = col["values"]
            if (not isinstance(vals, list) or not vals
                    or len(vals) != len(set(map(str, vals)))
                    or not all(isinstance(v, str) and len(v) <= 10 for v in vals)):
                raise ValueError("Domínio categórico inválido")
        elif col.get("kind") == "pattern":
            if set(col) != {"name", "kind", "expression", "required"}:
                raise ValueError("Campos de padrão inválidos")
            if col["expression"] not in PATTERNS:
                raise ValueError("Padrão de código não autorizado")
        else:
            raise ValueError("Tipo de validação não autorizado")
    return doc


def list_example_contracts() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "contratos": [
            {"id": name, "sha256": hashlib.sha256(
                _canonical(load_example_contract(name))
            ).hexdigest()}
            for name in sorted(IDS)
        ],
        "apenas_exemplos_sinteticos": True,
        "dicionarios_oficiais_verificados": False,
        "prontos_para_validacao_real": False,
    }


def diff_example_contracts(first: str, second: str) -> dict[str, Any]:
    """Compare schema definitions, not samples, without source data."""
    a, b = load_example_contract(first), load_example_contract(second)
    aa = {col["name"]: col for col in a["columns"]}
    bb = {col["name"]: col for col in b["columns"]}
    shared = sorted(aa.keys() & bb.keys())
    return {
        "schema_version": SCHEMA,
        "de": first,
        "para": second,
        "colunas_adicionadas": sorted(bb.keys() - aa.keys()),
        "colunas_removidas": sorted(aa.keys() - bb.keys()),
        "definicoes_alteradas": [name for name in shared if aa[name] != bb[name]],
        "comparacao_de_exemplos_nao_equivale_a_diff_oficial_entre_anos": True,
        "dicionarios_oficiais_verificados": False,
    }


def _schema(doc):
    """Import Pandera only for explicit administrative CSV validation."""
    try:
        import pandera.pandas as pa
    except ImportError as exc:
        raise RuntimeError(
            "Validação Pandera opcional ausente. Instale: pip install -e '.[quality]'"
        ) from None
    columns = {}
    for col in doc["columns"]:
        if col["kind"] == "enum":
            check = pa.Check.isin(col["values"])
        else:
            regex = col["expression"]
            check = pa.Check(
                lambda series, pattern=regex: series.str.fullmatch(pattern).fillna(False)
            )
        columns[col["name"]] = pa.Column(str, checks=[check],
                                          required=True, nullable=False)
    return pa.DataFrameSchema(columns, strict=True, coerce=False), pa


def validate_example_csv(
    path: str | Path, *, contract_id: str,
) -> dict[str, Any]:
    """Opt-in local-only PoC; no patient rows, values or paths in result.

    Not a replacement for source provenance, clinical dictionaries, official
    indicator computation, or a privacy risk review.
    """
    doc = load_example_contract(contract_id)
    source = Path(path).expanduser()
    if (source.is_symlink() or not source.is_file()
            or source.suffix.lower() != ".csv"
            or not 0 < source.stat().st_size <= MAX_CSV_BYTES):
        raise ValueError("CSV de exemplo ausente, link simbólico ou tamanho inválido")
    schema, pa = _schema(doc)
    try:
        import pandas as pd
    except ImportError:
        raise RuntimeError("Instale também pandas para o validador local") from None
    names = [x["name"] for x in doc["columns"]]
    processed = 0

    def check_batch(batch: list[dict]) -> None:
        try:
            schema.validate(pd.DataFrame.from_records(batch, columns=names),
                            lazy=True)
        except (pa.errors.SchemaError, pa.errors.SchemaErrors):
            # Pandera exceptions can contain actual row values: NEVER expose.
            raise ValueError("CSV rejeitado: categoria, tipo ou formato incompatível") from None

    try:
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, delimiter=",")
            if (not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames))
                    or set(reader.fieldnames) != set(names)):
                raise ValueError("CSV rejeitado: cabeçalho incompleto, duplicado ou extra")
            batch: list[dict] = []
            for row in reader:
                if (None in row or any(v is None or len(v) > MAX_VALUE_CHARS
                                      for v in row.values())):
                    raise ValueError("CSV rejeitado: linha malformada ou excessiva")
                batch.append(row)
                if len(batch) >= MAX_BATCH:
                    check_batch(batch)
                    processed += len(batch)
                    batch.clear()
            if batch:
                check_batch(batch)
                processed += len(batch)
    except (UnicodeError, csv.Error):
        raise ValueError("CSV rejeitado: codificação ou estrutura inválida") from None
    if not processed:
        raise ValueError("CSV rejeitado: sem linhas para validar")

    return {
        "schema_version": SCHEMA,
        "contrato": contract_id,
        "contrato_sha256": hashlib.sha256(_canonical(doc)).hexdigest(),
        "linhas_exemplo_processadas_localmente": processed,
        "estrutura_exemplar_compativel": True,
        "dicionario_oficial_ano_validado": False,
        "dados_reais_expostos_no_mcp": False,
        "publicacao_autorizada": False,
        "observacao": (
            "Somente prova de conceito local de estrutura sintética. "
            "Não comprova correção epidemiológica, autenticidade da fonte, "
            "privacidade ou adequação para bases reais."
        ),
    }
