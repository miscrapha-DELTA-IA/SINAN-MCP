"""Strict indicator-method readiness: never compute or certify real outcomes."""
from __future__ import annotations

import json
import subprocess
import sys
import inspect

import pytest

from sinan_mcp.indicator_protocols import plan_indicator
from sinan_mcp import indicator_protocols


def test_tb_method_is_exploratory_only():
    out = plan_indicator("TUBE", 2024)
    assert out["estado"] == "proposta_sem_validacao_para_ano"
    assert "TB_ABANDONO_EXPLORATORIO" in out["metodos"]
    assert out["indicadores_oficiais_disponiveis"] is False
    assert out["resultado_numerico"] is None
    assert out["consulta_de_dados_executada"] is False
    assert out["dicionario_validado_para_ano"] is False
    assert out["definicao_de_coorte_validada"] is False


def test_dengue_records_are_not_incidence():
    out = plan_indicator("DENG", 2022)
    assert out["metodos"]["DENG_REGISTROS_DESCRITIVOS"]["classificacao"] == (
        "CONTAGEM_DESCRITIVA_NAO_INCIDENCIA"
    )
    assert out["indicadores_oficiais_disponiveis"] is False


def test_other_agravo_has_no_fabricated_protocol():
    out = plan_indicator("HEPA", 2020)
    assert out["estado"] == "sem_protocolo_especifico"
    assert out["metodos"] == {}


@pytest.mark.parametrize("args", [
    ("UNKNOWN", 2024, None),
    ("tube", 2024, None),
    ("TUBE", True, None),
    ("TUBE", 2024, "DENG_REGISTROS_DESCRITIVOS"),
])
def test_reject_unsupported_disease_year_protocol(args):
    with pytest.raises(ValueError):
        plan_indicator(*args)


def test_no_data_or_network_imports_in_method_registry():
    code = inspect.getsource(indicator_protocols)
    for forbidden in ("sqlite3", "urllib", "requests", "pysus",
                      "SINAN_DB_PATH", "from .core", "os.environ"):
        assert forbidden not in code


def test_admin_cli_indicator_proposal_only(tmp_path):
    r = subprocess.run(
        [sys.executable, "-m", "sinan_mcp", "planejar-indicador",
         "--agravo", "TUBE", "--ano", "2024"],
        cwd=tmp_path, capture_output=True, text=True, timeout=20,
    )
    assert r.returncode == 0, r.stderr
    body = json.loads(r.stdout)
    assert body["resultado_numerico"] is None
    assert body["indicadores_oficiais_disponiveis"] is False
    assert not (tmp_path / "data").exists()
