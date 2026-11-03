"""Official annual resource pointers: software tests only, no health data."""
from __future__ import annotations

import asyncio
import copy
import io
import json
import subprocess
import sys
import zipfile

import pytest

from sinan_mcp import official_annual_resources as resources
from sinan_mcp import query_planner, public_server
from sinan_mcp.local_distribution_review import conferir_zip_recurso_local

DENG_CSV_ID = "4cf2f7b8-9920-41b5-817a-1ffc13e0690c"
DENG_JSON_ID = "28975ef7-da35-498e-b179-cfbde2150f90"
CHIK_JSON_ID = "74c005e0-e1b8-4db0-997d-8c80b2d37f8a"
ZIKA_JSON_ID = "264978ca-f795-4940-b5d3-ebc21e7d1c7c"
ZIKA_PARQUET_ID = "41bfda2a-5826-4ef9-8913-497247e6c9ce"


def test_official_resource_ids_and_unchanged_publishing_pages():
    result = resources.listar_recursos_oficiais_anuais()
    assert result["quantidade_distribuicoes_identificadas"] == 5
    assert result["arquivos_binarios_verificados"] == 0
    assert result["anos_com_dicionario_aplicavel_verificado"] == 0
    dengue = resources.consultar_recursos_oficiais_ano("DENG", 2024)
    assert dengue["estado"] == "recurso_anual_identificado_no_catalogo"
    assert dengue["quantidade_recursos_catalogados"] == 2
    assert {x["resource_id"] for x in dengue["recursos"]} == {
        DENG_CSV_ID, DENG_JSON_ID,
    }
    chik = resources.consultar_recursos_oficiais_ano("CHIK", 2024)
    assert chik["quantidade_recursos_catalogados"] == 1
    assert chik["recursos"][0]["resource_id"] == CHIK_JSON_ID
    zika = resources.consultar_recursos_oficiais_ano("ZIKA", 2024)
    assert zika["estado"] == "recurso_anual_identificado_no_catalogo"
    assert zika["quantidade_recursos_catalogados"] == 2
    assert zika["documento_de_dicionario_localizado"] is False
    assert not zika["compatibilidade_dicionario_ano_verificada"]
    assert {x["resource_id"] for x in zika["recursos"]} == {
        ZIKA_JSON_ID, ZIKA_PARQUET_ID,
    }
    assert {x["formato"] for x in zika["recursos"]} == {"JSON", "PARQUET"}
    for row in dengue["recursos"] + chik["recursos"] + zika["recursos"]:
        assert row["pagina_recurso_oficial"].startswith(
            "https://dadosabertos.saude.gov.br/dataset/")
        assert row["url_distribuicao_publicada"].startswith(
            "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/")
        assert row["nome_arquivo"].endswith(".zip")
        assert not row["checksum_oficial_publicado"]
        assert not row["arquivo_local_verificado"]
    assert all(dengue[x] is False for x in [
        "compatibilidade_dicionario_ano_verificada",
        "arquivo_binario_verificado", "situacao_preliminar_final_confirmada",
        "publicacao_autorizada", "microdados_acessados"
    ])


def test_tuberculosis_unknown_year_and_nonlisted_resources_not_fabricated():
    tb = resources.consultar_recursos_oficiais_ano("TUBE", 2024)
    assert tb["estado"] == "sem_recurso_anual_curado"
    assert tb["recursos"] == []
    assert tb["quantidade_recursos_catalogados"] == 0
    old = resources.consultar_recursos_oficiais_ano("DENG", 2023)
    assert old["estado"] == "sem_recurso_anual_curado"
    assert not old["publicacao_autorizada"]


def test_planner_keeps_document_vs_distribution_vs_data_validity_separate():
    query = query_planner.planejar_consulta_agravo("Dengue", ano=2024)
    assert query["resultado_epidemiologico"] is None
    assert query["evidencia_documental_agravo_ano"]["link_dicionario_oficial_localizado"]
    res = query["recursos_de_distribuicao_ano"]
    assert res["quantidade_recursos_catalogados"] == 2
    assert not res["compatibilidade_dicionario_ano_verificada"]
    assert not res["publicacao_autorizada"]
    ambiguous = query_planner.planejar_consulta_agravo("sífilis", ano=2024)
    assert ambiguous["recursos_de_distribuicao_ano"] is None


@pytest.mark.parametrize("bad", [
    lambda x: x["records"][0].update(
        publicacao_de_resultados_autorizada=True),
    lambda x: x["records"][0].update(
        arquivo_binario_baixado_ou_verificado=True),
    lambda x: x["records"][0].update(
        checksum_sha256_publicado_pela_autoridade="a" * 64),
    lambda x: x["records"][0].update(
        distribution_url="https://s3.sa-east-1.amazonaws.com.evil/abc"),
    lambda x: x["records"][0].update(
        distribution_url="https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Dengue/csv/%2e%2e/foo"),
    lambda x: x["records"][0].update(
        distribution_url="http://s3.sa-east-1.amazonaws.com/a.zip"),
    lambda x: x["records"][0].update(
        archive_filename="../../DENGBR24.csv.zip"),
    lambda x: x["records"][0].update(
        distribution_format="PARQUET"),
    lambda x: x["records"][0].update(
        resource_id="not-a-uuid"),
    lambda x: x["records"][-1].update(
        link_documental_do_dicionario_identificado=True),
    lambda x: x["records"][-1].update(
        distribution_url="https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/json/%2e%2e/z.zip"),
    lambda x: x["records"][-1].update(
        distribution_format="CSV"),
    lambda x: x["records"][0].update(
        agravo_alias_interno="TUBE"),
    lambda x: x["records"][0].update(
        ano_rotulado_no_portal=2023),
    lambda x: x["records"][0].update(
        ano_rotulado_no_portal=True),
    lambda x: x["records"].append(copy.deepcopy(x["records"][0])),
    lambda x: x["records"][0].update(
        patient_identifier="PROHIBITED"),
])
def test_registry_refuses_untrusted_metadata_and_fake_approval(bad):
    original = resources._index()[1]
    catalog = {
        "schema_version": resources.SCHEMA,
        "catalog_revision": "2026-11-03-r1",
        "scope": resources.SCOPE,
        "records": copy.deepcopy(list(original)),
    }
    bad(catalog)
    with pytest.raises(ValueError):
        resources.validate_resource_catalog(catalog)


def _fixture_zip(tmp_path, *, resource_id=DENG_CSV_ID, filename=None,
                 payload=b"CS_SEXO,CS_RACA\nF,4\n",
                 extra=False, badmember=False):
    row = next(r for r in resources._index()[1] if r["resource_id"] == resource_id)
    name = filename or row["archive_filename"]
    zpath = tmp_path / name
    expected_internal = name[:-4] if not badmember else "../leak.csv"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(expected_internal, payload)
        if extra:
            z.writestr("malicious/extra.txt", "DO-NOT-EXPORT")
    return zpath


def test_local_zip_inspection_is_bounded_and_does_not_read_records(tmp_path):
    zpath = _fixture_zip(tmp_path)
    report = conferir_zip_recurso_local(DENG_CSV_ID, zpath)
    assert report["arquivo_zip_estrutura_compativel_com_nome_registrado"]
    assert report["arquivos_extraidos"] == 0
    assert not report["conteudo_clinico_lido"]
    assert not report["origem_dos_bytes_autenticada"]
    assert not report["checksum_oficial_disponivel_para_comparacao"]
    assert not report["dicionario_aplicavel_validado"]
    assert not report["publicacao_autorizada"]
    assert len(report["arquivo_pacote_sha256_local"]) == 64
    assert "CS_SEXO" not in json.dumps(report)
    assert str(zpath) not in json.dumps(report)


@pytest.mark.parametrize("extra,badmember", [
    (True, False), (False, True),
])
def test_local_zip_rejects_member_injection_and_multiple_files(
    tmp_path, extra, badmember
):
    zipfile_path = _fixture_zip(tmp_path, extra=extra, badmember=badmember)
    with pytest.raises(ValueError):
        conferir_zip_recurso_local(DENG_CSV_ID, zipfile_path)


def test_local_zip_rejects_wrong_resource_and_corrupt_input(tmp_path):
    zpath = _fixture_zip(tmp_path)
    with pytest.raises(ValueError):
        conferir_zip_recurso_local(CHIK_JSON_ID, zpath)
    with pytest.raises(ValueError):
        conferir_zip_recurso_local("invalid-uuid", zpath)
    zpath.write_bytes(b"this is not a zip file that starts with PK\x03\x04")
    with pytest.raises(ValueError):
        conferir_zip_recurso_local(DENG_CSV_ID, zpath)


def test_zip_symlink_not_followed(tmp_path):
    zpath = _fixture_zip(tmp_path)
    link = tmp_path / "symlink.csv.zip"
    try:
        link.symlink_to(zpath)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink unavailable on runner")
    with pytest.raises(ValueError):
        conferir_zip_recurso_local(DENG_CSV_ID, link)


def test_public_mcp_only_metadata():
    from mcp import Client

    async def check():
        async with Client(public_server.mcp, raise_exceptions=True) as client:
            names = {x.name for x in (await client.list_tools()).tools}
            assert {"consultar_recursos_oficiais_ano",
                    "listar_recursos_oficiais_anuais"} <= names
            result = await client.call_tool(
                "consultar_recursos_oficiais_ano", {"agravo": "DENG", "ano": 2024}
            )
            assert not result.is_error
            assert not result.structured_content["arquivo_binario_verificado"]
            assert len(result.structured_content["recursos"]) == 2
            assert not result.structured_content["publicacao_autorizada"]

    asyncio.run(check())


def test_no_private_db_or_network_in_public_registry():
    import inspect
    src = inspect.getsource(resources)
    for forbidden in (
        "import sqlite3", "import requests", "urllib.request",
        "from .core import", "import subprocess", "urlopen(",
        "SINAN_DB_PATH",
    ):
        assert forbidden not in src


def test_cli_metadata_read_does_not_create_private_db(tmp_path):
    command = [sys.executable, "-m", "sinan_mcp", "consultar-distribuicao-ano",
               "--agravo", "DENG", "--ano", "2024"]
    p = subprocess.run(command, cwd=tmp_path, capture_output=True,
                       text=True, timeout=20)
    assert p.returncode == 0, p.stderr
    obj = json.loads(p.stdout)
    assert obj["quantidade_recursos_catalogados"] == 2
    assert not obj["publicacao_autorizada"]
    assert not (tmp_path / "data").exists()


def test_zika_only_metadata_and_no_2024_disease_specific_dictionary():
    metadata = resources.consultar_recursos_oficiais_ano("ZIKA", 2024)
    assert metadata["documento_de_dicionario_localizado"] is False
    assert metadata["microdados_acessados"] is False
    assert metadata["analise_epidemiologica_autorizada"] is False
    assert metadata["publicacao_autorizada"] is False
    assert metadata["quantidade_recursos_catalogados"] == 2
    assert resources.consultar_recursos_oficiais_ano("ZIKA", 2023)[
        "quantidade_recursos_catalogados"
    ] == 0
    assert resources.consultar_recursos_oficiais_ano("SIFA", 2024)[
        "quantidade_recursos_catalogados"
    ] == 0


def test_parquet_zip_only_inspects_synthetic_central_directory(tmp_path):
    path = _fixture_zip(tmp_path, resource_id=ZIKA_PARQUET_ID,
                        payload=b"synthetic parquet placeholder, no health data")
    audit = conferir_zip_recurso_local(ZIKA_PARQUET_ID, path)
    assert audit["arquivo_zip_estrutura_compativel_com_nome_registrado"] is True
    assert audit["formato_declarado"] == "PARQUET"
    assert audit["conteudo_clinico_lido"] is False
    assert audit["arquivos_extraidos"] == 0
    assert audit["origem_dos_bytes_autenticada"] is False
    assert audit["dicionario_aplicavel_validado"] is False
    assert audit["publicacao_autorizada"] is False
