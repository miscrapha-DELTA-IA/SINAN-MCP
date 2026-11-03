"""Regression of offline human-curated ZIKA 2024 official CKAN identity."""
from __future__ import annotations

import copy
import inspect
import subprocess
import sys

import pytest

from sinan_mcp.zika_resource_identity import (
    SNAPSHOT, confrontar_snapshot_portal_zika_2024,
)


def test_zika_official_identity_snapshot_matches_two_annual_pointers():
    report = confrontar_snapshot_portal_zika_2024()
    assert report["agravo"] == "ZIKA"
    assert report["ano_rotulado"] == 2024
    assert report["data_curadoria_documental"] == "2026-11-03"
    assert report["registros_documentais_concordantes"] == 2
    assert len(report["sha256_snapshot_metadados"]) == 64
    assert {x["formato_documentado"] for x in report["registros"]} == {
        "JSON", "PARQUET"
    }
    assert {x["resource_id"] for x in report["registros"]} == {
        "264978ca-f795-4940-b5d3-ebc21e7d1c7c",
        "41bfda2a-5826-4ef9-8913-497247e6c9ce",
    }
    assert {x["id_conjunto_documentado"] for x in report["registros"]} == {
        "4557ba96-7d52-4a56-bd6f-f99a5af09f77",
    }
    assert report["consulta_web_nesta_execucao"] is False
    assert report["arquivos_binarios_acessados"] == 0
    assert report["campos_clinicos_lidos"] == 0
    assert report["arquivo_anual_autenticado"] is False
    assert report["dicionario_aplicavel_2024_validado"] is False
    assert report["indicador_real_homologado"] is False
    assert report["publicacao_autorizada"] is False
    assert all(row["concorda_com_catalogo_local"] for row in report["registros"])
    assert all(row["site_reconsultado_nesta_execucao"] is False
               for row in report["registros"])
    assert all(row["layout_2024_validado"] is False
               for row in report["registros"])
    assert all(row["publicacao_autorizada"] is False
               for row in report["registros"])


@pytest.mark.parametrize("tamper", [
    lambda a: a.pop(),
    lambda a: a.append(copy.deepcopy(a[0])),
    lambda a: a[0].update(resource_id=a[1]["resource_id"]),
    lambda a: a[0].update(portal_package_id="f" * 36),
    lambda a: a[0].update(portal_status="published"),
    lambda a: a[0].update(portal_format="CSV"),
    lambda a: a[0].update(portal_title="Zika - 2023"),
    lambda a: a[0].update(portal_page="https://evil.example.invalid/resource"),
    lambda a: a[0].update(
        portal_distribution="https://s3.sa-east-1.amazonaws.com/evil.zip"),
    lambda a: a[0].update(arquivo_binario_verificado=True),
    lambda a: a[0].update(portal_status=True),
    lambda a: a[0].update(resource_id=123),
])
def test_snapshot_tampering_fails_closed(tamper):
    records = copy.deepcopy(list(SNAPSHOT))
    tamper(records)
    with pytest.raises(ValueError):
        confrontar_snapshot_portal_zika_2024(tuple(records))


def test_zika_identity_cli_is_metadata_only_and_no_private_db(tmp_path):
    args = [
        sys.executable, "-m", "sinan_mcp", "confrontar-identidade-zika-2024",
    ]
    r = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    assert "Recursos com identidade documental concordante: 2" in r.stdout
    assert "Reconsulta online nesta execucao: NAO" in r.stdout
    assert "Arquivos binarios acessados: 0; campos clinicos lidos: 0" in r.stdout
    assert "Layout 2024 e consolidacao comprovados: NAO" in r.stdout
    assert "Acesso real e publicacao autorizados: NAO" in r.stdout
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "sinan.sqlite3").exists()


def test_crosswalk_acknowledges_portal_uuid_substep_but_retains_ten_gates():
    from sinan_mcp.documentary_crosswalk_2024 import planejar_confronto_documental_2024
    zika = planejar_confronto_documental_2024("ZIKA")
    sifa = planejar_confronto_documental_2024("SIFA")
    assert zika["identidade_publica_uuid_formato_documentada"] is True
    assert zika["recursos_cotejados_com_snapshot_portal"] == 2
    assert zika["data_curadoria_identidade_portal"] == "2026-11-03"
    assert sifa["identidade_publica_uuid_formato_documentada"] is False
    assert sifa["recursos_cotejados_com_snapshot_portal"] == 0
    for plan in (zika, sifa):
        assert plan["total_topicos_pendentes"] == 10
        assert all(item["status"] == "PENDENTE_DE_EVIDENCIA_E_REVISAO_HUMANA"
                   for item in plan["topicos_pendentes"])
        assert plan["metadados_site_reconsultados_na_execucao"] is False
        assert plan["arquivos_anuais_autenticados"] == 0
        assert plan["autorizacao_publicacao"] is False


def test_multidisease_diagnostic_and_sifa_official_counts_unaffected():
    from sinan_mcp.multiagravo_readiness import diagnosticar_cobertura_multiagravo
    from sinan_mcp.official_annual_resources import consultar_recursos_oficiais_ano
    report = diagnosticar_cobertura_multiagravo(2024)
    assert report["agravos_referenciados"] == 14
    assert report["agravos_com_documentacao_localizada"] == 12
    assert report["distribuicoes_catalogadas"] == 5
    assert consultar_recursos_oficiais_ano("SIFA", 2024)[
        "quantidade_recursos_catalogados"
    ] == 0
    assert report["publicacao_automatica"] is False


def test_snapshot_never_calls_network_or_private_database():
    from sinan_mcp import zika_resource_identity
    src = inspect.getsource(zika_resource_identity)
    for forbidden in (
        "import requests", "import sqlite3", "urllib.request", "urlopen(",
        "import pysus", "import subprocess", "SINAN_DB_PATH", "from .core import",
    ):
        assert forbidden not in src


def test_zika_official_portal_context_is_not_2024_file_approval():
    from sinan_mcp.zika_portal_context import consultar_contexto_portal_zika_2024
    ctx = consultar_contexto_portal_zika_2024()
    assert ctx["agravo"] == "ZIKA"
    assert ctx["ano_rotulado_no_arquivo"] == 2024
    assert ctx["url_conjunto_oficial"] == (
        "https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus"
    )
    assert ctx["sistema_de_notificacao_descrito_no_conjunto"] == "SINAN Net"
    assert ctx["sistema_de_notificacao_mencionado_pelo_portal"] is True
    assert ctx["sistema_de_origem_dos_bytes_2024_autenticado"] is False
    assert ctx["prazo_de_encerramento_documentado_dias"] == 60
    assert ctx["definicao_de_caso_validada_em_registros_2024"] is False
    assert ctx["series_historicas_congeladas_em_datas_especificas_por_ano"] is True
    assert ctx["data_de_corte_exata_do_zip_2024"] is None
    assert ctx["data_atualizacao_portal_equivale_a_corte_epidemiologico"] is False
    assert ctx["recurso_de_dicionario_zika_listado_no_portal"] is True
    assert ctx["titulo_recurso_dicionario"] == "Dicionário de dados - Zika Vírus"
    assert ctx["data_de_atualizacao_listada_do_dicionario"] == "2025-07-14"
    assert ctx["url_exata_pdf_dicionario_zika_recuperada"] is None
    assert ctx["conteudo_pdf_dicionario_zika_auditado"] is False
    assert ctx["dicionario_de_zika_aplicavel_ao_ano_2024_validado"] is False
    assert ctx["distribuicoes_anuais_catalogadas"] == 2
    assert ctx["arquivos_binarios_2024_verificados"] == 0
    assert ctx["campos_clinicos_lidos"] == 0
    assert ctx["dados_reais_disponiveis_no_mcp_publico"] is False
    assert ctx["indicadores_reais_homologados"] == 0
    assert ctx["publicacao_autorizada"] is False


def test_zika_crosswalk_context_does_not_close_scientific_gates():
    from sinan_mcp.documentary_crosswalk_2024 import planejar_confronto_documental_2024
    zika = planejar_confronto_documental_2024("ZIKA")
    sifa = planejar_confronto_documental_2024("SIFA")
    assert zika["sinan_net_descrito_no_portal"] is True
    assert zika["dicionario_especifico_zika_listado_no_portal"] is True
    assert zika["pdf_exato_zika_auditado"] is False
    assert zika["corte_exato_do_arquivo_2024_conhecido"] is False
    assert zika["origem_dos_bytes_2024_autenticada"] is False
    assert sifa["sinan_net_descrito_no_portal"] is False
    assert sifa["dicionario_especifico_zika_listado_no_portal"] is False
    for plan in (zika, sifa):
        assert plan["total_topicos_pendentes"] == 10
        assert all(item["status"] == "PENDENTE_DE_EVIDENCIA_E_REVISAO_HUMANA"
                   for item in plan["topicos_pendentes"])
        assert plan["autorizacao_analise_real"] is False
        assert plan["autorizacao_publicacao"] is False


def test_zika_portal_context_cli_keeps_cutoff_unknown(tmp_path):
    args = [
        sys.executable, "-m", "sinan_mcp",
        "planejar-confronto-documental-2024", "--agravo", "ZIKA",
    ]
    p = subprocess.run(
        args, capture_output=True, text=True, cwd=tmp_path, timeout=30,
    )
    assert p.returncode == 0, p.stderr
    assert "Sistema SINAN Net descrito no catalogo oficial: SIM" in p.stdout
    assert "Dicionario especifico Zika listado no portal: SIM" in p.stdout
    assert "PDF especifico Zika auditado: NAO" in p.stdout
    assert "Data de corte exata do arquivo ZIKA/2024: NAO IDENTIFICADA" in p.stdout
    assert "Topicos de revisao pendentes: 10" in p.stdout
    assert "Campos reais lidos: 0; indicadores homologados: 0" in p.stdout
    assert "Acesso real e publicacao autorizados: NAO" in p.stdout
    assert not (tmp_path / "data").exists()


def test_zika_context_only_uses_static_metadata():
    from sinan_mcp import zika_portal_context
    src = inspect.getsource(zika_portal_context)
    for forbidden in (
        "import requests", "import sqlite3", "urllib.request", "urlopen(",
        "import pysus", "import subprocess", "SINAN_DB_PATH", "from .core import",
    ):
        assert forbidden not in src
