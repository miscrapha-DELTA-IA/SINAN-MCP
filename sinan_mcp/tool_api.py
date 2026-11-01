"""Privacy-limited public tool surface for MCP and local REST.

The storage/query core is intentionally separate from this disclosure policy.
An allowlisted, single-year, single-UF partition cannot be subdivided further
through the public tools. This is risk reduction, not formal anonymization.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import abandono_tb, catalogo, contar, dicionario
from .catalogue import CATALOGUE

ALLOWED_GROUPS = frozenset({"sexo", "raca_cor"})
POLICY_VERSION = "public-v1-single-uf-year"


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
    return {"agravo": row["agravo"], "ano_do_arquivo": row["ano"],
            "tipo_de_fonte": row["tipo_fonte"], "status": row["status"],
            "fingerprint_sha256": row["sha256"], "importado_em_utc": row["atualizado_em"],
            "origem_referencia": "https://pysus.readthedocs.io/en/stable/quickstart.html"
                                 if row["tipo_fonte"].startswith("pysus") else None,
            "fingerprint_tipo": "manifesto_hash_por_arquivo" if row["tipo_fonte"].startswith("pysus")
                                else "sha256_arquivo" if row["tipo_fonte"] == "csv-local" else None,
            "observacao": "Ano do arquivo, não necessariamente ano de notificação."}


def listar_bases_publicas(db: str | Path) -> dict:
    rows = catalogo(db)["bases_importadas"]
    return {"schema_version": "0.2", "politica": POLICY_VERSION,
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
    result = contar(db, agravo=agravo, ano_inicio=ano, ano_fim=ano,
                    uf=uf, por=por)
    return {"schema_version": "0.2", "tipo": "contagem_de_registros",
            "resultado": result, "proveniencia": origem, "politica": POLICY_VERSION,
            "limitacoes": ["Supressão de células menores que 10 não equivale a anonimização.",
                           "Sem consultas municipais, totais ou intervalos arbitrários nesta interface.",
                           "Não comparar como incidência, prevalência ou número de indivíduos únicos."]}


def abandono_publico(db: str | Path, *, ano_inicio: int | None = None,
                    ano_fim: int | None = None, uf: str | None = None,
                    municipio: str | None = None, por: str = "raca_cor") -> dict:
    ano, uf = _request(ano_inicio, ano_fim, uf, municipio, por)
    origem = _source(db, "TUBE", ano)
    result = abandono_tb(db, ano_inicio=ano, ano_fim=ano, uf=uf, por=por)
    return {"schema_version": "0.2", "tipo": "proporcao_exploratoria_TB",
            "resultado": result, "proveniencia": origem, "politica": POLICY_VERSION,
            "limitacoes": ["Não é o indicador oficial de abandono do Ministério da Saúde.",
                           "Não seleciona uma coorte epidemiológica oficial e não efetua desduplicação longitudinal.",
                           "A supressão de valores pequenos não garante anonimização."]}
