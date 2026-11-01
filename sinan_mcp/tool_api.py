"""Privacy-limited public tool surface for MCP and local REST.

The storage/query core is intentionally separate from this disclosure policy.
An allowlisted, single-year, single-UF partition cannot be subdivided further
through the public tools. This is risk reduction, not formal anonymization.
"""
from __future__ import annotations

from pathlib import Path
from contextlib import closing
import os
from typing import Any

from .core import abandono_tb, catalogo, contar, dicionario, db_connect_readonly
from .catalogue import CATALOGUE

ALLOWED_GROUPS = frozenset({"sexo", "raca_cor"})
POLICY_VERSION = "public-v2-restricted-partition"


def _request(ano_inicio: int | None, ano_fim: int | None,
             uf: str | None, municipio: str | None, por: str) -> tuple[int, str]:
    if not isinstance(ano_inicio, int) or isinstance(ano_inicio, bool) or ano_inicio != ano_fim:
        raise ValueError("Informe exatamente um ano de arquivo: ano_inicio = ano_fim.")
    if not isinstance(uf, str) or len(uf.strip()) != 2:
        raise ValueError("Informe a sigla de uma única UF (ex.: PI).")
    if municipio is not None:
        raise ValueError("Consultas municipais não estão disponíveis nas ferramentas públicas.")
    if por not in ALLOWED_GROUPS:
        raise ValueError("Agregue somente por sexo ou raca_cor nesta interface pública.")
    return ano_inicio, uf.strip().upper()


def _source(db: str | Path, agravo: str, ano: int) -> dict[str, Any]:
    if agravo.upper() not in CATALOGUE:
        raise ValueError("Agravo não habilitado na interface pública: apenas TUBE e DENG nesta etapa")
    matches = [x for x in catalogo(db)["bases_importadas"]
               if x["agravo"] == agravo.upper() and x["ano"] == ano]
    if not matches:
        raise ValueError(f"Base {agravo.upper()}/{ano} não importada. Execute a ingestão pela CLI.")
    row = matches[0]
    if row["tipo_fonte"] != "synthetic" and os.getenv("SINAN_PUBLIC_REAL_DATA", "") != "1":
        raise ValueError(
            "Dados reais bloqueados nas ferramentas públicas. Um administrador "
            "deve revisar a privacidade e definir SINAN_PUBLIC_REAL_DATA=1 "
            "explicitamente no processo do servidor."
        )
    return {"agravo": row["agravo"], "ano_do_arquivo": row["ano"],
            "tipo_de_fonte": row["tipo_fonte"], "status": row["status"],
            "fingerprint_sha256": row["sha256"], "importado_em_utc": row["atualizado_em"],
            "origem_referencia": "https://pysus.readthedocs.io/en/stable/quickstart.html"
                                 if row["tipo_fonte"].startswith("pysus") else None,
            "fingerprint_tipo": "manifesto_hash_por_arquivo" if row["tipo_fonte"].startswith("pysus")
                                else "sha256_arquivo" if row["tipo_fonte"] == "csv-local" else None,
            "observacao": "Ano do arquivo, não necessariamente ano de notificação."}


def _partition_releasable(db: str | Path, agravo: str, ano: int, uf: str) -> bool:
    """Fail closed across ALL public tables of the same disease/year/UF.

    Querying sex and race marginal tables (and TB eligible-outcome tables)
    separately can reveal small residual counts by subtraction. If *any*
    populated category or case/control subcell has 1-9 observations, disclose
    none of these tables. This conservative baseline is NOT DP and does not
    protect against external data, temporal joins or other datasets.
    """
    with closing(db_connect_readonly(db)) as con:
        total = con.execute(
            "SELECT COUNT(*) FROM registros WHERE agravo=? AND ano=? AND uf=?",
            (agravo.upper(), ano, uf)
        ).fetchone()[0]
        if total < 100:
            return False
        for dimension in ("sexo", "raca_cor"):  # fixed identifiers only
            rows = con.execute(
                f"""SELECT {dimension}, COUNT(*) n,
                    SUM(CASE WHEN situacao_encerramento IN ('2','10') THEN 1 ELSE 0 END) lost,
                    SUM(CASE WHEN situacao_encerramento = '1' THEN 1 ELSE 0 END) cured
                    FROM registros
                    WHERE agravo=? AND ano=? AND uf=?
                    GROUP BY {dimension}""",
                (agravo.upper(), ano, uf),
            ).fetchall()
            for row in rows:
                n = row["n"]
                if n < 10:
                    return False
                if agravo.upper() == "TUBE":
                    lost, cured = row["lost"] or 0, row["cured"] or 0
                    if (0 < lost < 10) or (0 < cured < 10):
                        return False
    return True


def _blocked_result(kind: str, agravo: str, ano: int, uf: str, por: str) -> dict:
    """No exact cells, breakdowns, totals or small category names."""
    result = {
        "agravo": agravo.upper(),
        "agrupar_por": por,
        "filtros": {"ano_inicio": ano, "ano_fim": ano, "uf": uf, "municipio": None},
        "dados": [],
        "status": "nao_divulgavel",
        "aviso": ("Partição não disponível segundo a política conservadora de "
                  "privacidade ou sem volume suficiente para divulgação."),
    }
    if kind == "tb":
        result["indicador"] = "Medida exploratória de abandono de TB, não oficial"
    else:
        result["definicao"] = "Contagens de registros, não casos únicos nem incidência"
    return result


def listar_bases_publicas(db: str | Path) -> dict:
    rows = catalogo(db)["bases_importadas"]
    return {"schema_version": "0.3", "politica": POLICY_VERSION,
            "bases": [{"agravo": r["agravo"], "ano_do_arquivo": r["ano"],
                       "tipo_de_fonte": r["tipo_fonte"], "status": r["status"],
                       "importado_em_utc": r["atualizado_em"]} for r in rows],
            "observacao": "Não inclui totais, nomes locais de arquivo ou registros individuais."}


def descrever_campos_publicos() -> dict:
    return {"schema_version": "0.2", "dicionario": dicionario(),
            "politica": POLICY_VERSION,
            "limites": ["Suporte experimental, verificar dicionário por ano/agravo.",
                        "Nenhum valor desta ferramenta representa estimativa de incidência."]}


def contagens_publicas(db: str | Path, *, agravo: str,
                       ano_inicio: int | None = None, ano_fim: int | None = None,
                       uf: str | None = None, municipio: str | None = None,
                       por: str = "raca_cor") -> dict:
    ano, uf = _request(ano_inicio, ano_fim, uf, municipio, por)
    origem = _source(db, agravo, ano)
    result = (
        contar(db, agravo=agravo, ano_inicio=ano, ano_fim=ano, uf=uf, por=por)
        if _partition_releasable(db, agravo, ano, uf)
        else _blocked_result("count", agravo, ano, uf, por)
    )
    return {"schema_version": "0.2", "tipo": "contagem_de_registros",
            "resultado": result, "proveniencia": origem, "politica": POLICY_VERSION,
            "limitacoes": ["Partições com células pequenas não são divulgadas em nenhuma dimensão pública.",
                           "Supressão de células menores que 10 não equivale a anonimização.",
                           "Sem consultas municipais, totais ou intervalos arbitrários nesta interface.",
                           "Não comparar como incidência, prevalência ou número de indivíduos únicos."]}


def abandono_publico(db: str | Path, *, ano_inicio: int | None = None,
                    ano_fim: int | None = None, uf: str | None = None,
                    municipio: str | None = None, por: str = "raca_cor") -> dict:
    ano, uf = _request(ano_inicio, ano_fim, uf, municipio, por)
    origem = _source(db, "TUBE", ano)
    result = (
        abandono_tb(db, ano_inicio=ano, ano_fim=ano, uf=uf, por=por)
        if _partition_releasable(db, "TUBE", ano, uf)
        else _blocked_result("tb", "TUBE", ano, uf, por)
    )
    return {"schema_version": "0.2", "tipo": "proporcao_exploratoria_TB",
            "resultado": result, "proveniencia": origem, "politica": POLICY_VERSION,
            "limitacoes": ["Partições com células pequenas não são divulgadas em nenhuma dimensão pública.",
                           "Não é o indicador oficial de abandono do Ministério da Saúde.",
                           "Não seleciona uma coorte epidemiológica oficial e não efetua desduplicação longitudinal.",
                           "A supressão de valores pequenos não garante anonimização."]}
