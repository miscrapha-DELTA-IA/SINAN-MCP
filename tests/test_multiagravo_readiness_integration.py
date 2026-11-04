"""Year-specific, metadata-only multiagravo readiness and integration tests."""
from __future__ import annotations

import subprocess
import sys

import pytest

from sinan_mcp.multiagravo_readiness import (
    BLOCKED, diagnosticar_cobertura_multiagravo,
)
from sinan_mcp.official_sources import CONDITIONS


def test_2024_registry_coverage_not_equivalent_to_research_approval():
    info = diagnosticar_cobertura_multiagravo(2024)
    assert info["agravos_referenciados"] == len(CONDITIONS) == 14
    assert info["agravos_com_documentacao_localizada"] == 13
    assert info["distribuicoes_catalogadas"] == 5
    assert info["status"] == "DIAGNOSTICO_DOCUMENTAL_SEM_VALIDACAO_EPIDEMIOLOGICA"
    assert info["dados_clinicos_consultados"] is False
    assert info["publicacao_automatica"] is False
    entries = {x["agravo"]: x for x in info["registros"]}
    assert set(entries) == {x[0] for x in CONDITIONS}
    assert entries["DENG"]["distribuicoes_anuais_catalogadas"] == 2
    assert entries["DENG"]["formatos_catalogados"] == ["CSV", "JSON"]
    assert entries["CHIK"]["distribuicoes_anuais_catalogadas"] == 1
    assert entries["CHIK"]["formatos_catalogados"] == ["JSON"]
    assert entries["ZIKA"]["documento_oficial_localizado"] is True
    assert entries["ZIKA"]["distribuicoes_anuais_catalogadas"] == 2
    assert entries["ZIKA"]["formatos_catalogados"] == ["JSON", "PARQUET"]
    assert entries["SIFA"]["documento_oficial_localizado"] is False
    assert entries["SIFA"]["distribuicoes_anuais_catalogadas"] == 0
    assert entries["TUBE"]["distribuicoes_anuais_catalogadas"] == 0
    for code in ("TUBE", "DENG", "CHIK"):
        assert entries[code]["documento_oficial_localizado"] is True
    for code, record in entries.items():
        assert all(record[field] is False for field in BLOCKED), code
        assert record["ano_do_arquivo"] == 2024


def test_catalogue_does_not_guess_years_or_other_disease_formats():
    future = diagnosticar_cobertura_multiagravo(2025)
    assert future["agravos_referenciados"] == 14
    assert future["agravos_com_documentacao_localizada"] == 0
    assert future["distribuicoes_catalogadas"] == 0
    chik = diagnosticar_cobertura_multiagravo(2024, "CHIK")
    assert chik["filtro_agravo"] == "CHIK"
    assert chik["agravos_referenciados"] == 1
    assert chik["distribuicoes_catalogadas"] == 1
    assert chik["registros"][0]["indicador_real_homologado"] is False
    assert chik["registros"][0]["propostas_metodologicas_nao_validadas"] == 0


@pytest.mark.parametrize("year,alias", [
    (True, None), (2024.5, None), (0, None), (2101, None),
    (2024, "FAKE"), (2024, "Dengue"), (2024, "deng"),
    (2024, ""), (2024, 1), (2024, "TUBE; DROP TABLE registros"),
])
def test_invalid_scope_rejected(year, alias):
    with pytest.raises(ValueError):
        diagnosticar_cobertura_multiagravo(year, alias)


def test_no_db_or_network_usage_under_environment_poisoning(monkeypatch, tmp_path):
    private_path = tmp_path / "secret.sqlite3"
    monkeypatch.setenv("SINAN_DB_PATH", str(private_path))
    monkeypatch.setenv("SINAN_PUBLIC_REAL_DATA", "1")
    answer = diagnosticar_cobertura_multiagravo(2024)
    assert answer["publicacao_automatica"] is False
    assert all(not x["dados_reais_disponiveis_no_mcp_publico"]
               for x in answer["registros"])
    assert not private_path.exists()


def test_cli_produces_only_metadata_counters(tmp_path):
    private_path = tmp_path / "private.sqlite3"
    cmd = [
        sys.executable, "-m", "sinan_mcp",
        "diagnosticar-cobertura-multiagravo", "--ano", "2024",
    ]
    ok = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    assert ok.returncode == 0, ok.stderr
    assert "Agravos no indice consultados: 14" in ok.stdout
    assert "Agravos com documentacao localizada: 13" in ok.stdout
    assert "Distribuicoes anuais catalogadas: 5" in ok.stdout
    assert "Acesso real e publicacao autorizados: NAO" in ok.stdout
    assert "DENG documento: SIM distribuicoes: 2" in ok.stdout
    assert "CHIK documento: SIM distribuicoes: 1" in ok.stdout
    assert "TUBE documento: SIM distribuicoes: 0" in ok.stdout
    assert "ZIKA documento: SIM distribuicoes: 2" in ok.stdout
    assert not private_path.exists()
    invalid = subprocess.run(cmd + ["--agravo", "FAKE"],
                             capture_output=True, text=True, timeout=30)
    assert invalid.returncode != 0
    assert "COBERTURA NAO DIAGNOSTICADA" in invalid.stderr
