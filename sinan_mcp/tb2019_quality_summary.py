"""Present only non-identifying quality pass/fail flags from a local report.

Never reads SQLite, raw DBC/DBF/Parquet, cells or missingness percentages.
Scientific and publication approval remain false regardless of check results.
"""
from __future__ import annotations

import json
from pathlib import Path

from .tb2019_private_import import PRIVATE_ROOT, PARQUET_SHA256
from .tb2019_parity import PINNED_SHA256

FLAG_KEYS = (
    "uma_unica_fonte",
    "somente_escopo_tube_2019",
    "quantidade_compativel_com_metadados",
    "codigos_projetados_no_dominio",
    "uf_municipio_projetados_consistentes",
)


def safe_quality_summary(root: Path | str | None = None) -> dict:
    private = (Path(root) if root is not None else PRIVATE_ROOT).resolve()
    if not private.is_dir():
        raise FileNotFoundError("Pasta privada de auditoria nao encontrada")
    reports = sorted(private.glob("TUBE2019-quality-*.json"))
    if not reports:
        raise FileNotFoundError("Execute scripts.auditar_qualidade_tb2019 primeiro")
    file = reports[-1].resolve()
    if file.parent != private or not file.is_file() or file.stat().st_size > 65_536:
        raise ValueError("Relatorio fora do escopo privado ou de tamanho inesperado")
    data = json.loads(file.read_text(encoding="utf-8"))
    source = data.get("fontes")
    flags = data.get("verificacoes")
    if (data.get("stage") != "PRIVATE_TB2019_QUALITY_PREFLIGHT_NOT_HOMOLOGATED"
            or data.get("ano_do_arquivo") != 2019
            or not isinstance(source, dict)
            or source.get("dbc_sha256_recebido") != PINNED_SHA256
            or source.get("parquet_sha256_importado") != PARQUET_SHA256
            or source.get("status_catalogo") != "desconhecido"
            or data.get("publicacao_autorizada") is not False
            or not isinstance(flags, dict)
            or flags.get("sqlite_integridade") != "ok"
            or any(type(flags.get(key)) is not bool for key in FLAG_KEYS)):
        raise ValueError("Relatorio privado de qualidade invalido ou adulterado")

    tests = {key: flags[key] for key in FLAG_KEYS}
    return {
        "stage": "TB2019_QUALITY_FLAGS_REDACTED",
        "ano_do_arquivo": 2019,
        "sqlite_integridade": True,
        "checagens": tests,
        "checagens_tecnicas_sem_alertas": all(tests.values()),
        "bandas_de_completude_divulgadas": False,
        "contagens_ou_microdados_divulgados": False,
        "compatibilidade_temporal_dicionario_2019_verificada": False,
        "revisao_cientifica_independente": False,
        "revisao_privacidade_independente": False,
        "publicacao_autorizada": False,
    }
