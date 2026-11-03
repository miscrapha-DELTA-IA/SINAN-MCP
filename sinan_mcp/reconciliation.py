"""Offline, exact-scope comparison of a local projection with a declared TABNET table.

An agreement is NOT source authentication or validation of epidemiological
cohorts. This code never performs a network request or serves an MCP tool.
"""
from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path

from .core import db_connect_readonly
from .official_table_intake import (
    CATEGORY_ALIASES, _normalized_category, _reject_duplicate_keys,
    validate_official_tabulation, MAX_BYTES, K_MIN, TOTAL_MIN,
)


def reconcile_declared_table(
    db: str | Path, tabulation_path: str | Path
) -> dict:
    source = Path(tabulation_path).expanduser()
    if source.is_symlink() or not source.is_file() or source.stat().st_size > MAX_BYTES:
        raise ValueError("Tabela local ausente, link simbólico ou arquivo excessivo")
    try:
        obj = json.loads(source.read_text(encoding="utf-8"),
                         object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("JSON de tabulação inválido") from exc
    validate_official_tabulation(obj)
    scope = obj["scope"]
    if (scope["uf"] == "BR" or scope["ano_inicio"] != scope["ano_fim"]
            or scope["tipo_ano"] != "ano_arquivo"):
        raise ValueError(
            "Comparação exige UF específica, ano único e tipo ano_arquivo. "
            "Outras séries temporais NÃO são equivalentes ao arquivo importado."
        )
    agravo, ano, uf = (
        scope["agravo_codigo_interno"], scope["ano_inicio"], scope["uf"]
    )
    dimension = scope["dimensao"]  # validated allowlist
    with closing(db_connect_readonly(db)) as con:
        metadata = con.execute(
            "SELECT tipo_fonte, status FROM fontes WHERE agravo=? AND ano=?",
            (agravo, ano),
        ).fetchone()
        if metadata is None:
            raise ValueError("Agravo/ano não importado localmente")
        rows = con.execute(
            f"SELECT {dimension} AS categoria, COUNT(*) AS n "
            "FROM registros WHERE agravo=? AND ano=? AND uf=? "
            f"GROUP BY {dimension}",
            (agravo, ano, uf),
        ).fetchall()

    # Block *entire* partition for small cells; no partial comparison.
    if (not rows or sum(int(row["n"]) for row in rows) < TOTAL_MIN
            or any(int(row["n"]) < K_MIN for row in rows)):
        raise ValueError("Partição local pequena ou vazia: comparação não permitida")

    mapping = CATEGORY_ALIASES[dimension]
    expected = {}
    for cell in obj["cells"]:
        code = mapping[_normalized_category(cell["categoria"])]
        expected[code] = int(cell["registros"])
    observed = {}
    for row in rows:
        key = (row["categoria"] if row["categoria"] is not None
               else "ignorado/ausente")
        code = mapping.get(_normalized_category(str(key)))
        if code is None or code in observed:
            raise ValueError("Categoria inesperada na projeção")
        observed[code] = int(row["n"])

    same_categories = set(expected) == set(observed)
    differences = (
        sum(expected[code] != observed[code] for code in expected)
        if same_categories else None
    )
    return {
        "schema_version": "sinan-offline-reconciliation-v1",
        "tipo": "COMPARACAO_LOCAL_NAO_CERTIFICADA",
        "agravo": agravo,
        "ano_do_arquivo": ano,
        "uf": uf,
        "dimensao": dimension,
        "categorias_iguais": same_categories,
        "contagens_iguais": same_categories and differences == 0,
        "numero_de_categorias_com_diferenca": differences,
        "status_fonte_local_declarado": metadata["status"],
        "status_tabela_declarado": obj["source"]["estado_consolidacao"],
        "status_sintetico": metadata["tipo_fonte"] == "synthetic",
        "arquivo_fonte_oficial_autenticado": False,
        "dicionario_reconciliado_com_ano": False,
        "coorte_epidemiologica_validada": False,
        "publicacao_autorizada": False,
        "aviso": (
            "Comparação estrutural e numérica local, sem revelar células. "
            "Equivalência não prova origem oficial, identidade de coortes, "
            "ano de diagnóstico, deduplicação ou proteção contra diferenças. "
            "Requer parecer humano independente antes de qualquer divulgação."
        ),
    }
