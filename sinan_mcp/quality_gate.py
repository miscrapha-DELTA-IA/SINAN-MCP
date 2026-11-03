"""Administrator-only quality gate for projected SINAN snapshots.

Counts can be sensitive: NEVER expose through an MCP tool, HTTP endpoint,
telemetry or assistant. No direct identifiers are stored in the projection.
An identical projected tuple is NOT proof of duplicate patients.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path

from .core import db_connect_readonly, validate_agravo

FIELDS = ("uf", "municipio", "sexo", "raca_cor")
VALID_SEX = ("M", "F", "I")
VALID_RACE = ("1", "2", "3", "4", "5", "9")
TB_END = ("1", "2", "10")


def audit_projected_snapshot(db: str | Path, *, agravo: str, ano: int) -> dict:
    """Assess an entire agravo/file-year locally, never sample patient rows."""
    agravo = validate_agravo(agravo)
    if type(ano) is not int or not 1980 <= ano <= 2100:
        raise ValueError("Ano inválido")
    with closing(db_connect_readonly(db)) as con:
        source = con.execute(
            "SELECT tipo_fonte, status, n_registros, sha256 FROM fontes "
            "WHERE agravo=? AND ano=?", (agravo, ano)
        ).fetchone()
        if source is None:
            raise ValueError("Snapshot não importado")
        # Query only fixed columns and return scalar aggregates.
        stats = con.execute("""
            SELECT COUNT(*) AS n,
              SUM(CASE WHEN uf IS NULL THEN 1 ELSE 0 END) AS sem_uf,
              SUM(CASE WHEN municipio IS NULL THEN 1 ELSE 0 END) AS sem_municipio,
              SUM(CASE WHEN sexo IS NULL OR sexo='I' THEN 1 ELSE 0 END) AS sem_sexo,
              SUM(CASE WHEN raca_cor IS NULL OR raca_cor='9' THEN 1 ELSE 0 END) AS sem_raca,
              SUM(CASE WHEN sexo IS NOT NULL AND sexo NOT IN ('M','F','I')
                THEN 1 ELSE 0 END) AS sexo_invalido,
              SUM(CASE WHEN raca_cor IS NOT NULL AND raca_cor NOT IN
                ('1','2','3','4','5','9') THEN 1 ELSE 0 END) AS raca_invalida,
              SUM(CASE WHEN uf IS NOT NULL AND length(uf)<>2
                THEN 1 ELSE 0 END) AS uf_invalida
            FROM registros WHERE agravo=? AND ano=?
        """, (agravo, ano)).fetchone()
        # SQL grouping uses columns, never arbitrary user-supplied names.
        repeats = con.execute("""
            SELECT COALESCE(SUM(n - 1),0) FROM (
              SELECT COUNT(*) n FROM registros
              WHERE agravo=? AND ano=?
              GROUP BY uf, municipio, sexo, raca_cor, situacao_encerramento
              HAVING COUNT(*) > 1
            )
        """, (agravo, ano)).fetchone()[0]
        if agravo == "TUBE":
            outcome = con.execute("""
                SELECT
                  SUM(CASE WHEN situacao_encerramento IS NULL THEN 1 ELSE 0 END),
                  SUM(CASE WHEN situacao_encerramento NOT IN ('1','2','10')
                           AND situacao_encerramento IS NOT NULL THEN 1 ELSE 0 END)
                FROM registros WHERE agravo=? AND ano=?
            """, (agravo, ano)).fetchone()
        else:
            outcome = None

    n = int(stats["n"])
    recorded = int(source["n_registros"])
    def entry(key: str) -> dict:
        value = int(stats[key] or 0)
        return {"n": value, "percentual": round(100 * value / n, 2) if n else None}
    integrity = n == recorded
    # Warn rather than certify quality or reject common projected patterns.
    checks = {
        "contagem_igual_metadado": integrity,
        "possui_registros": n > 0,
        "sexo_sem_codigo_invalido": not stats["sexo_invalido"],
        "raca_cor_sem_codigo_invalido": not stats["raca_invalida"],
        "uf_sem_formato_invalido": not stats["uf_invalida"],
    }
    return {
        "schema_version": "sinan-projected-quality-v1",
        "modalidade": "AUDITORIA_ADMINISTRATIVA_LOCAL_SENSIVEL",
        "agravo": agravo,
        "ano_do_arquivo": ano,
        "status_fonte_declarado": source["status"],
        "tipo_fonte": source["tipo_fonte"],
        "integridade_metadado": checks,
        "registros_snapshot": n,
        "registros_metadado": recorded,
        "ausencia_ou_ignorado": {
            "uf": entry("sem_uf"),
            "municipio": entry("sem_municipio"),
            "sexo": entry("sem_sexo"),
            "raca_cor": entry("sem_raca"),
        },
        "categorias_invalidas_apos_projecao": {
            "sexo": entry("sexo_invalido"), "raca_cor": entry("raca_invalida"),
            "uf": entry("uf_invalida")
        },
        "linhas_com_projecao_identica_alem_da_primeira": int(repeats or 0),
        "equivalencia_projecao_nao_indica_pessoa_duplicada": True,
        "encerramento_tuberculose": (
            {"ausente": int(outcome[0] or 0), "fora_codigos_exploratorios": int(outcome[1] or 0)}
            if outcome is not None else None
        ),
        "reconciliado_com_tabnet": False,
        "referencia_temporal_validada": False,
        "dicionario_ano_validado": False,
        "aprovado_publicacao": False,
        "aviso": (
            "Resultado reservado para curadoria LOCAL. Projeção descarta valores "
            "não reconhecidos, então este relatório NÃO identifica todos os erros "
            "do arquivo original. Equivalência de tuplas não prova duplicação "
            "de pacientes e contagens não são casos únicos nem incidência."
        ),
    }
