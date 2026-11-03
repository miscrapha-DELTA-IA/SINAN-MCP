"""Metadata-only crosscutting notification references; never clinical validation."""
from __future__ import annotations

import inspect
import json
import subprocess
import sys

import pytest

from sinan_mcp.shared_notification_documents import (
    diagnosticar_documentacao_transversal,
)


def test_shared_2018_document_has_distinct_evidence_strength_for_zika_and_sifa():
    report = diagnosticar_documentacao_transversal(2024)
    assert report["schema_version"] == "sinan-shared-notification-documentation-v1"
    assert report["agravos_consultados"] == 2
    assert report["referencias_transversais_candidatas"] == 2
    assert report["vinculos_diretos_na_pagina_do_agravo"] == 1
    assert report["dados_clinicos_consultados"] is False
    assert report["autorizacao_de_publicacao"] is False
    rows = {row["agravo"]: row for row in report["registros"]}
    assert set(rows) == {"ZIKA", "SIFA"}
    assert rows["ZIKA"]["vinculo_direto_na_pagina_do_agravo"] is True
    assert rows["SIFA"]["vinculo_direto_na_pagina_do_agravo"] is False
    assert rows["ZIKA"]["pagina_oficial"].endswith("/zika")
    assert rows["SIFA"]["pagina_oficial"].endswith("/notificacoes")
    assert rows["ZIKA"]["url_dicionario_compartilhado"] == rows["SIFA"][
        "url_dicionario_compartilhado"
    ]
    assert rows["ZIKA"]["url_dicionario_compartilhado"].endswith(
        "/NINDIV/DIC_DADOS_NET_Not_Individual_rev.pdf"
    )
    for row in rows.values():
        assert "2018" in row["edicao_documental"]
        assert row["dicionario_especifico_neste_registro"] is False
        assert row["compatibilidade_com_arquivo_anual_demonstrada"] is False
        assert row["sistema_origem_2024_verificado"] is False
        assert row["indicador_real_homologado"] is False
        assert row["acesso_clinico_executado"] is False
        assert row["publicacao_autorizada"] is False


def test_no_silent_2023_or_2025_compatibility_inheritance():
    for year in (2023, 2025):
        report = diagnosticar_documentacao_transversal(year)
        assert report["referencias_transversais_candidatas"] == 0
        assert report["vinculos_diretos_na_pagina_do_agravo"] == 0
        assert all(not x["compatibilidade_com_arquivo_anual_demonstrada"]
                   for x in report["registros"])
        assert all(x["url_dicionario_compartilhado"] is None
                   for x in report["registros"])


def test_other_reference_not_misrepresented_as_shared_disease_dictionary():
    tb = diagnosticar_documentacao_transversal(2024, "TUBE")
    assert tb["agravos_consultados"] == 1
    assert tb["referencias_transversais_candidatas"] == 0
    assert tb["registros"][0]["pagina_oficial"] is None
    assert tb["registros"][0]["dicionario_especifico_neste_registro"] is False


@pytest.mark.parametrize("ano,agravo", [
    (True, None), (2024.0, None), (1950, []), (2101, None),
    (2024, "zika"), (2024, "ZIKA;DROP"), (2024, "FAKE"),
    (2024, 10), (2024, ""), (0, None),
])
def test_invalid_scope_fails_closed(ano, agravo):
    with pytest.raises(ValueError):
        diagnosticar_documentacao_transversal(ano, agravo)


def test_offline_cli_output_retains_absence_of_approval(tmp_path):
    private_db = tmp_path / "sinan.sqlite3"
    cmd = [
        sys.executable, "-m", "sinan_mcp",
        "diagnosticar-documentacao-transversal", "--ano", "2024",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "Referencias transversais candidatas: 2" in result.stdout
    assert "Vinculos diretos na pagina do agravo: 1" in result.stdout
    assert "ZIKA referencia transversal: SIM vinculo direto: SIM" in result.stdout
    assert "SIFA referencia transversal: SIM vinculo direto: NAO" in result.stdout
    assert "Acesso real e publicacao autorizados: NAO" in result.stdout
    assert "compatibilidade 2024: NAO" in result.stdout
    assert not private_db.exists()
    error = subprocess.run(cmd + ["--agravo", "fake"], capture_output=True, text=True,
                           timeout=30, cwd=tmp_path)
    assert error.returncode != 0
    assert not private_db.exists()


def test_legacy_multiagravo_diagnosis_unchanged():
    from sinan_mcp.multiagravo_readiness import diagnosticar_cobertura_multiagravo
    result = diagnosticar_cobertura_multiagravo(2024)
    assert result["agravos_com_documentacao_localizada"] == 13
    assert result["distribuicoes_catalogadas"] == 5
    assert result["publicacao_automatica"] is False


def test_module_does_not_import_network_database_or_client():
    from sinan_mcp import shared_notification_documents as shared
    src = inspect.getsource(shared)
    for forbidden in (
        "import requests", "import sqlite3", "from .core import",
        "import pysus", "urllib.request", "urlopen(", "open(",
        "import subprocess", "SINAN_DB_PATH",
    ):
        assert forbidden not in src
