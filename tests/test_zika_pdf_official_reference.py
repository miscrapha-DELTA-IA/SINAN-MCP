"""ZIKA official PDF reference: exact URL, documentary fields, and fail-closed gates."""
from __future__ import annotations

import inspect
import subprocess
import sys

from sinan_mcp.admin_zika_dictionary_discovery import _download_pdf_url
from sinan_mcp.zika_official_dictionary_reference import (
    PDF_URL, RESOURCE_ID, RESOURCE_URL, VISIBLE_FIELD_EXAMPLES,
    diagnosticar_pdf_oficial_zika,
)


def test_exact_ministry_pdf_outside_old_pdf_subdirectory_is_accepted():
    assert _download_pdf_url(PDF_URL) == PDF_URL
    for tampered in (
        PDF_URL.replace(".pdf", ".PDF"),
        PDF_URL + "?dl=1", PDF_URL + "#pdf",
        PDF_URL.replace("https://", "http://"),
        PDF_URL.replace("dic_dados_zika.pdf", "../dic_dados_zika.pdf"),
        PDF_URL.replace("Zikavirus", "Dengue"),
        PDF_URL.replace("s3.sa-east-1.amazonaws.com",
                        "s3.sa-east-1.amazonaws.com.evil.invalid"),
        PDF_URL.replace("dic_dados_zika.pdf", "fake_zika.pdf"),
    ):
        assert _download_pdf_url(tampered) is None


def test_documentary_reference_is_specific_and_safe():
    report = diagnosticar_pdf_oficial_zika()
    assert report["agravo"] == "ZIKA"
    assert report["ano_do_arquivo_pretendido"] == 2024
    assert report["id_recurso_dicionario"] == RESOURCE_ID
    assert report["url_recurso_governamental"] == RESOURCE_URL
    assert report["url_pdf_governamental"] == PDF_URL
    assert report["numero_de_paginas_visualizado"] == 8
    assert report["numero_de_campos_numerados_no_documento"] == 37
    assert report["documento_especifico_zika_localizado"] is True
    assert report["ligacao_resource_id_pdf_conferida_no_portal"] is True
    assert report["documento_inspecionado_visualmente"] is True
    assert report["conteudo_completo_transcrito_ou_homologado"] is False
    assert report["checksum_pdf_oficial_publicado"] is False
    assert report["sha256_bytes_pdf_efetivamente_calculado"] is False
    assert report["dicionario_comparado_a_cabecalho_2024"] is False
    assert report["campos_da_distribuicao_2024_lidos"] == 0
    assert report["data_corte_do_arquivo_2024_verificada"] is False
    assert report["situacao_final_preliminar_2024_verificada"] is False
    assert report["indicadores_reais_homologados"] == 0
    assert report["publicacao_autorizada"] is False
    assert len(report["exemplos_de_campos_visualmente_conferidos"]) == len(
        VISIBLE_FIELD_EXAMPLES
    )
    assert {x["campo"] for x in report["exemplos_de_campos_visualmente_conferidos"]} >= {
        "dt_notific", "cs_raca", "classi_fin", "dt_encerra", "tp_sistema"
    }


def test_reference_only_updates_documentary_crosswalk_subfields():
    from sinan_mcp.documentary_crosswalk_2024 import planejar_confronto_documental_2024
    zika = planejar_confronto_documental_2024("ZIKA")
    sifa = planejar_confronto_documental_2024("SIFA")
    assert zika["pdf_especifico_zika_localizado_no_portal"] is True
    assert zika["pdf_zika_inspecionado_visualmente"] is True
    assert zika["numero_campos_documentados_zika"] == 37
    assert zika["numero_campos_pdf_transcritos_candidato_zika"] == 37
    assert zika["transcricao_pdf_zika_sem_revisao_independente"] is True
    assert sifa["numero_campos_pdf_transcritos_candidato_zika"] == 0
    assert zika["pdf_exato_zika_auditado"] is False  # no 2024 field-level audit
    assert zika["corte_exato_do_arquivo_2024_conhecido"] is False
    assert sifa["pdf_especifico_zika_localizado_no_portal"] is False
    assert sifa["numero_campos_documentados_zika"] == 0
    for row in (zika, sifa):
        assert row["total_topicos_pendentes"] == 10
        assert all(x["status"] == "PENDENTE_DE_EVIDENCIA_E_REVISAO_HUMANA"
                   for x in row["topicos_pendentes"])
        assert row["arquivos_anuais_autenticados"] == 0
        assert row["indicadores_homologados"] == 0
        assert row["autorizacao_analise_real"] is False
        assert row["autorizacao_publicacao"] is False


def test_admin_reference_cli_does_not_access_case_data_or_network(tmp_path):
    cmd = [sys.executable, "-m", "sinan_mcp", "diagnosticar-pdf-oficial-zika"]
    result = subprocess.run(cmd, cwd=tmp_path, capture_output=True,
                            text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "PDF OFICIAL ZIKA LOCALIZADO" in result.stdout
    assert RESOURCE_ID in result.stdout
    assert PDF_URL in result.stdout
    assert "Paginas no PDF: 8" in result.stdout
    assert "Campos numerados no documento: 37" in result.stdout
    assert "Confronto com esquema do arquivo ZIKA/2024: NAO" in result.stdout
    assert "Publicacao autorizada: NAO" in result.stdout
    assert not (tmp_path / "sinan.sqlite3").exists()
    assert not (tmp_path / "data").exists()


def test_public_multiagravo_counters_and_public_server_unchanged():
    from sinan_mcp.multiagravo_readiness import diagnosticar_cobertura_multiagravo
    from sinan_mcp import public_server, zika_official_dictionary_reference
    result = diagnosticar_cobertura_multiagravo(2024)
    assert result["agravos_referenciados"] == 14
    assert result["agravos_com_documentacao_localizada"] == 13
    assert result["distribuicoes_catalogadas"] == 5
    assert result["publicacao_automatica"] is False
    assert "zika_official_dictionary_reference" not in inspect.getsource(public_server)
    src = inspect.getsource(zika_official_dictionary_reference)
    for unsafe in ("urllib.request", "import requests", "import sqlite3",
                   "import pysus", "import subprocess", "import os"):
        assert unsafe not in src
