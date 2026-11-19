"""Local-only TUBE/2019 quality preflight for the private research projection.

No raw records, exact category counts or small cells are emitted. This is
NOT a scientific validation, source homologation, privacy approval or MCP tool.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from .core import db_connect_readonly, UF_CODIGOS
from .tb2019_private_import import PRIVATE_ROOT, PARQUET_SHA256, SOURCE_TYPE
from .tb2019_parity import PINNED_SHA256

DATABASE = "piloto-tb2019.sqlite3"


def _bucket(missing: int, total: int) -> str:
    """Deliberately coarsen quality signals instead of disclosing counts."""
    if total <= 0:
        return "sem_dados"
    if missing == 0:
        return "zero"
    share = missing / total
    if share <= .01:
        return "ate_1_porcento"
    if share <= .05:
        return "mais_1_ate_5_porcento"
    if share <= .20:
        return "mais_5_ate_20_porcento"
    return "mais_20_porcento"


def audit_private_tb2019(path: Path | str = PRIVATE_ROOT / DATABASE) -> dict:
    private_dir = PRIVATE_ROOT.resolve()
    db = Path(path).resolve()
    if db.parent != private_dir or db.name != DATABASE or not db.is_file():
        raise ValueError("Banco restrito data/private/tb2019/piloto-tb2019.sqlite3 ausente/invalido")

    from .tb2019_parity import verify_local_dbc
    verify_local_dbc(private_dir)

    with db_connect_readonly(db) as conn:
        integrity = conn.execute("PRAGMA quick_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise RuntimeError("SQLite falhou na verificacao de integridade")

        sources = conn.execute(
            "SELECT chave, agravo, ano, tipo_fonte, status, sha256, n_registros "
            "FROM fontes"
        ).fetchall()
        if len(sources) != 1:
            raise ValueError("Catálogo privado deve conter exatamente uma fonte")
        source = sources[0]
        if (source["agravo"] != "TUBE" or source["ano"] != 2019
                or source["tipo_fonte"] != SOURCE_TYPE
                or source["status"] != "desconhecido"
                or source["sha256"] != PARQUET_SHA256):
            raise ValueError("Fonte fora do piloto privado fixado; auditoria recusada")

        n = conn.execute("SELECT COUNT(*) FROM registros").fetchone()[0]
        n_in_scope = conn.execute(
            "SELECT COUNT(*) FROM registros WHERE chave=? AND agravo='TUBE' AND ano=2019",
            (source["chave"],)
        ).fetchone()[0]
        if n <= 0 or n != source["n_registros"] or n != n_in_scope:
            raise ValueError("Integridade de escopo ou quantidade de registros inconsistente")

        missing = conn.execute(
            """SELECT
                SUM(CASE WHEN uf IS NULL THEN 1 ELSE 0 END) AS uf,
                SUM(CASE WHEN municipio IS NULL THEN 1 ELSE 0 END) AS municipio,
                SUM(CASE WHEN sexo IS NULL OR sexo='I' THEN 1 ELSE 0 END) AS sexo,
                SUM(CASE WHEN raca_cor IS NULL OR raca_cor='9' THEN 1 ELSE 0 END) AS raca_cor,
                SUM(CASE WHEN situacao_encerramento IS NULL THEN 1 ELSE 0 END) AS situacao_encerramento
                FROM registros"""
        ).fetchone()

        invalid_codes = conn.execute(
            """SELECT COUNT(*) FROM registros WHERE
                (uf IS NOT NULL AND uf NOT IN (
                    'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS',
                    'MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'))
                OR (sexo IS NOT NULL AND sexo NOT IN ('F','M','I'))
                OR (raca_cor IS NOT NULL AND raca_cor NOT IN ('1','2','3','4','5','9'))
                OR (situacao_encerramento IS NOT NULL AND
                    (length(situacao_encerramento)>3
                    OR situacao_encerramento GLOB '*[^0-9]*'))
                OR (municipio IS NOT NULL AND
                    (length(municipio) != 6 OR municipio GLOB '*[^0-9]*'))"""
        ).fetchone()[0]

        known_uf = tuple(UF_CODIGOS.items())
        inconsistent_mun = 0
        if known_uf:
            # Mapping covers codes recognized by the ingestion projection.
            uf_case = "CASE substr(municipio,1,2) " + " ".join(
                "WHEN '" + prefix + "' THEN '" + state + "'"
                for prefix, state in known_uf
            ) + " ELSE NULL END"
            inconsistent_mun = conn.execute(
                f"SELECT COUNT(*) FROM registros WHERE municipio IS NOT NULL "
                f"AND uf IS NOT NULL AND ({uf_case}) IS NOT NULL "
                f"AND uf != ({uf_case})"
            ).fetchone()[0]

    report = {
        "stage": "PRIVATE_TB2019_QUALITY_PREFLIGHT_NOT_HOMOLOGATED",
        "ano_do_arquivo": 2019,
        "fontes": {
            "dbc_sha256_recebido": PINNED_SHA256,
            "parquet_sha256_importado": PARQUET_SHA256,
            "status_catalogo": "desconhecido"
        },
        "verificacoes": {
            "sqlite_integridade": "ok",
            "uma_unica_fonte": True,
            "somente_escopo_tube_2019": True,
            "quantidade_compativel_com_metadados": True,
            "codigos_projetados_no_dominio": invalid_codes == 0,
            "uf_municipio_projetados_consistentes": inconsistent_mun == 0,
        },
        "completude_bandas": {
            name: _bucket(int(missing[name] or 0), n)
            for name in ("uf", "municipio", "sexo", "raca_cor", "situacao_encerramento")
        },
        "limites": [
            "Bandas de ausentes/ignorados sao descritivas e nao validam o dicionario oficial.",
            "Codigos invalidos podem ter sido transformados em ausentes durante projecao.",
            "Nao verifica duplicatas individuais, casos unicos, ano de diagnostico nem semantica clinica.",
            "Nenhuma contagem estratificada ou microdado foi emitido."
        ],
        "revisao_cientifica_independente": False,
        "revisao_privacidade_independente": False,
        "equivalencia_integral_verificada": False,
        "publicacao_autorizada": False
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    outfile = private_dir / f"TUBE2019-quality-{stamp}.json"
    fd = os.open(outfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except BaseException:
        outfile.unlink(missing_ok=True)
        raise
    return {
        "stage": report["stage"],
        "verificacao_tecnica": "concluida",
        "relatorio_privado_criado": True,
        "atualizacao_do_sqlite": False,
        "contagens_ou_registros_exibidos": False,
        "status_final_homologado": False,
        "publicacao_autorizada": False,
        "proxima_etapa": "REVIEW_DICTIONARY_AND_PRIVACY"
    }
