"""SIFA 2024 ministerial guidance and pending-only ZIKA/SIFA crosswalk tests."""
from __future__ import annotations

import inspect
import subprocess
import sys

import pytest

from sinan_mcp.documentary_crosswalk_2024 import (
    REVIEW_TOPICS, planejar_confronto_documental_2024,
)
from sinan_mcp.shared_notification_documents import diagnosticar_documentacao_transversal


def test_2024_ministry_guide_names_sifa_form_without_validating_sifa_file():
    result = diagnosticar_documentacao_transversal(2024)
    rows = {row["agravo"]: row for row in result["registros"]}
    sifa = rows["SIFA"]
    zika = rows["ZIKA"]
    assert sifa["orientacao_especifica_de_notificacao_no_guia_2024"] is True
    assert sifa["pagina_impressa_guia_ministerial"] == 506
    assert "Notificação/Conclusão" in sifa["instrumento_de_notificacao_orientado"]
    assert "/guia-de-vigilancia-em-saude-volume-2-6a-edicao" in sifa[
        "url_guia_ministerial_2024"
    ]
    assert sifa["url_nota_informativa_ministerial_2017"].endswith(
        "/Sifilis-Ges/Nota_Informativa_Sifilis.pdf"
    )
    assert sifa["vinculo_direto_na_pagina_do_agravo"] is False
    assert zika["orientacao_especifica_de_notificacao_no_guia_2024"] is False
    assert zika["url_guia_ministerial_2024"] is None
    assert zika["url_nota_informativa_ministerial_2017"] is None
    assert result["referencias_transversais_candidatas"] == 2
    assert result["vinculos_diretos_na_pagina_do_agravo"] == 1
    for x in rows.values():
        assert x["dicionario_especifico_neste_registro"] is False
        assert x["compatibilidade_com_arquivo_anual_demonstrada"] is False
        assert x["publicacao_autorizada"] is False


def test_sifa_crosswalk_keeps_guidance_separate_from_schema_claims():
    p = planejar_confronto_documental_2024("SIFA")
    assert p["agravo"] == "SIFA"
    assert p["numero_de_distribuicoes_catalogadas"] == 0
    assert p["orientacao_ministerial_2024_sobre_a_ficha"] is True
    assert "Notificação/Conclusão" in p["instrumento_de_notificacao_orientado"]
    assert p["vinculo_direto_do_pdf_na_pagina_do_agravo"] is False
    assert len(p["referencias_documentais"]) == 3
    assert {x["id"] for x in p["referencias_documentais"]} == {
        "dicionario_geral_2018", "guia_ministerial_2024", "nota_ms_2017"
    }
    assert next(x for x in p["referencias_documentais"]
                if x["id"] == "guia_ministerial_2024")["pagina_impressa"] == 506
    assert p["dicionario_especifico_curado"] is False
    assert p["compatibilidade_dicionario_2024_verificada"] is False
    assert p["arquivos_anuais_autenticados"] == 0


def test_zika_crosswalk_tracks_two_resources_without_verifying_content():
    p = planejar_confronto_documental_2024("ZIKA")
    assert p["numero_de_distribuicoes_catalogadas"] == 2
    assert p["orientacao_ministerial_2024_sobre_a_ficha"] is False
    assert p["instrumento_de_notificacao_orientado"] is None
    assert p["vinculo_direto_do_pdf_na_pagina_do_agravo"] is True
    assert p["dicionario_especifico_curado"] is True
    assert len(p["referencias_documentais"]) == 5
    assert {x["id"] for x in p["referencias_documentais"]} == {
        "dicionario_geral_2018", "pagina_oficial_zika",
        "dicionario_especifico_zika",
        "distribuicao_catalogada_1", "distribuicao_catalogada_2"
    }
    assert all(x["aplica_automaticamente_ao_arquivo_2024"] is False
               for x in p["referencias_documentais"])
    assert all(x["url"].startswith("https://") for x in p["referencias_documentais"])


@pytest.mark.parametrize("agravo", ["SIFA", "ZIKA"])
def test_every_review_gate_stays_pending_and_no_real_data(agravo):
    p = planejar_confronto_documental_2024(agravo)
    assert p["total_topicos_pendentes"] == len(REVIEW_TOPICS) == 10
    assert {x["topico"] for x in p["topicos_pendentes"]} == {
        x[0] for x in REVIEW_TOPICS
    }
    assert all(x["status"] == "PENDENTE_DE_EVIDENCIA_E_REVISAO_HUMANA"
               for x in p["topicos_pendentes"])
    assert all(x["campos_2024_conferidos"] is False
               for x in p["topicos_pendentes"])
    assert all(x["parecer_independente_autenticado"] is False
               for x in p["topicos_pendentes"])
    assert p["campos_de_arquivo_real_lidos"] == 0
    assert p["arquivos_anuais_autenticados"] == 0
    assert p["indicadores_homologados"] == 0
    assert p["autorizacao_analise_real"] is False
    assert p["autorizacao_publicacao"] is False


@pytest.mark.parametrize("invalid", [
    "sifa", "zika", "SIFC", "TUBE", "SIFG", "ZIKA/2023",
    "", " SIFA", "SIFA ", "SIFA;DROP", 2024, None, True, [],
])
def test_rejects_nonapproved_scope(invalid):
    with pytest.raises(ValueError):
        planejar_confronto_documental_2024(invalid)


def test_cli_runs_offline_and_does_not_create_a_private_database(tmp_path):
    cmd = [
        sys.executable, "-m", "sinan_mcp",
        "planejar-confronto-documental-2024", "--agravo", "SIFA"
    ]
    result = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True,
                            timeout=30)
    assert result.returncode == 0, result.stderr
    assert "MATRIZ DOCUMENTAL 2024" in result.stdout
    assert "Distribuicoes anuais catalogadas: 0" in result.stdout
    assert "Orientacao ministerial 2024 da ficha: SIM" in result.stdout
    assert "Topicos de revisao pendentes: 10" in result.stdout
    assert "Campos reais lidos: 0; indicadores homologados: 0" in result.stdout
    assert "Acesso real e publicacao autorizados: NAO" in result.stdout
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "sinan.sqlite3").exists()
    zika = subprocess.run(cmd[:-1] + ["ZIKA"], cwd=tmp_path,
                          capture_output=True, text=True, timeout=30)
    assert zika.returncode == 0, zika.stderr
    assert "Distribuicoes anuais catalogadas: 2" in zika.stdout
    assert "Orientacao ministerial 2024 da ficha: NAO" in zika.stdout


def test_public_contract_and_multidisease_counters_do_not_change():
    from sinan_mcp.multiagravo_readiness import diagnosticar_cobertura_multiagravo
    result = diagnosticar_cobertura_multiagravo(2024)
    assert result["agravos_referenciados"] == 14
    assert result["agravos_com_documentacao_localizada"] == 13
    assert result["distribuicoes_catalogadas"] == 5
    assert result["dados_clinicos_consultados"] is False
    assert result["publicacao_automatica"] is False


def test_crosswalk_uses_only_versioned_public_metadata():
    from sinan_mcp import documentary_crosswalk_2024 as module
    src = inspect.getsource(module)
    for forbidden in (
        "import requests", "import sqlite3", "urllib.request", "urlopen(",
        "import pysus", "import subprocess", "SINAN_DB_PATH", "from .core import",
    ):
        assert forbidden not in src
