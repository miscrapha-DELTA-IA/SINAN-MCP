"""Synthetic report fixtures only; do not read patient data."""
import json
from pathlib import Path

import pytest

from sinan_mcp import tb2019_quality_summary as safe


def _create(root: Path, *, change=None):
    root.mkdir(parents=True, exist_ok=True)
    obj = {
        "stage": "PRIVATE_TB2019_QUALITY_PREFLIGHT_NOT_HOMOLOGATED",
        "ano_do_arquivo": 2019,
        "fontes": {
            "dbc_sha256_recebido": safe.PINNED_SHA256,
            "parquet_sha256_importado": safe.PARQUET_SHA256,
            "status_catalogo": "desconhecido"
        },
        "verificacoes": {
            "sqlite_integridade": "ok",
            "uma_unica_fonte": True,
            "somente_escopo_tube_2019": True,
            "quantidade_compativel_com_metadados": True,
            "codigos_projetados_no_dominio": True,
            "uf_municipio_projetados_consistentes": True
        },
        "completude_bandas": {
            "sexo": "mais_20_porcento",
            "uf": "mais_1_ate_5_porcento"
        },
        "publicacao_autorizada": False
    }
    if change:
        change(obj)
    (root / "TUBE2019-quality-20261119T000000000000Z.json").write_text(
        json.dumps(obj), encoding="utf-8"
    )


def test_summary_exposes_flags_but_never_completeness_bands(tmp_path):
    root = tmp_path / "data/private/tb2019"
    _create(root)
    result = safe.safe_quality_summary(root)
    assert result["checagens_tecnicas_sem_alertas"] is True
    assert result["publicacao_autorizada"] is False
    assert result["compatibilidade_temporal_dicionario_2019_verificada"] is False
    assert "mais_20" not in json.dumps(result)
    assert "sexo" not in json.dumps(result)
    assert "completude_bandas" not in json.dumps(result)


def test_individual_failed_flag_surfaces_without_data_values(tmp_path):
    root = tmp_path / "data/private/tb2019"
    _create(root, change=lambda x: x["verificacoes"].update(
        {"codigos_projetados_no_dominio": False}))
    out = safe.safe_quality_summary(root)
    assert out["checagens"]["codigos_projetados_no_dominio"] is False
    assert out["checagens_tecnicas_sem_alertas"] is False


@pytest.mark.parametrize("mutator", [
    lambda d: d["fontes"].update({"status_catalogo": "final"}),
    lambda d: d["fontes"].update({"parquet_sha256_importado": "a" * 64}),
    lambda d: d.update({"publicacao_autorizada": True}),
    lambda d: d["verificacoes"].update({"uma_unica_fonte": 1}),
])
def test_rejects_untrustworthy_report(tmp_path, mutator):
    root = tmp_path / "data/private/tb2019"
    _create(root, change=mutator)
    with pytest.raises(ValueError, match="invalido"):
        safe.safe_quality_summary(root)


def test_rejects_missing_report(tmp_path):
    with pytest.raises(FileNotFoundError):
        safe.safe_quality_summary(tmp_path)
