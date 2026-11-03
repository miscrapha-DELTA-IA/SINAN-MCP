"""Research registry and local attestation tests using synthetic files only."""
from __future__ import annotations

import asyncio
import copy
import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

from sinan_mcp import public_server, query_planner, year_evidence_registry as reg
from sinan_mcp.year_evidence_review import confrontar_documento_e_arquivo_local


def test_publisher_documents_linked_but_not_applied_to_year():
    items = reg.listar_evidencias_documentais()
    assert items["total_entradas_documentadas"] == 2
    assert items["quantidade_anos_de_arquivo_cientificamente_verificados"] == 0
    assert not items["base_real_disponibilizada"]
    assert len(items["catalog_metadata_sha256"]) == 64
    t = reg.consultar_evidencia_agravo_ano("TUBE", 2024)
    d = reg.consultar_evidencia_agravo_ano("DENG", 2024)
    assert t["estado"] == d["estado"] == (
        "documento_oficial_localizado_ano_nao_verificado"
    )
    assert t["evidencia_documental"]["edicao_documental"].startswith("SINAN NET 5.0")
    assert "2020.pdf" in t["evidencia_documental"]["documento_url"]
    assert "DIC_DADOS_ONLINE.pdf" in d["evidencia_documental"]["documento_url"]
    assert "2015" in d["evidencia_documental"]["edicao_documental"]
    for entry in [t, d]:
        assert entry["link_dicionario_oficial_localizado"] is True
        for flag in (
            "arquivo_anual_independentemente_verificado",
            "codigo_download_anual_verificado",
            "compatibilidade_dicionario_ano_verificada",
            "sha256_oficial_do_arquivo_disponivel",
            "consolidacao_anual_confirmada",
            "indicador_cientifico_ano_validado",
            "autorizacao_de_publicacao",
            "consulta_de_dados_executada",
        ):
            assert entry[flag] is False
    assert reg.listar_evidencias_documentais() == items


def test_unreviewed_year_does_not_inherit_dictionary():
    other = reg.consultar_evidencia_agravo_ano("TUBE", 2023)
    assert other["estado"] == "sem_documentacao_anual_curada"
    assert other["evidencia_documental"] is None
    x = reg.consultar_evidencia_agravo_ano("DENG", 2026)
    assert x["evidencia_documental"] is None
    unknown = reg.consultar_evidencia_agravo_ano("ABCD", 2024)
    assert unknown["indice_de_alias_contem_agravo"] is False
    assert unknown["evidencia_documental"] is None


@pytest.mark.parametrize("code,year", [
    ("TUB", 2024), ("TUBE", 1800), ("TUBE", True),
    ("TUBE", 2024.0), ("../../etc", 2024),
    (None, 2024), ([], 2024),
])
def test_unsafe_year_queries_fail_closed(code, year):
    with pytest.raises(ValueError):
        reg.consultar_evidencia_agravo_ano(code, year)


@pytest.mark.parametrize("change", [
    lambda x: x["entries"][0]["validacoes"].update(
        dicionario_aplicavel_ao_ano_confirmado=True),
    lambda x: x["entries"][0]["validacoes"].update(
        aprovacao_para_publicar=True),
    lambda x: x["entries"][0]["acesso_dados"].update(
        status_consolidacao_2024="final"),
    lambda x: x["entries"][0]["acesso_dados"].update(
        arquivo_exato_2024="TUBE2024.DBC"),
    lambda x: x["entries"][0]["documento"].update(
        integridade_binaria_publicada_por_autoridade="f" * 64),
    lambda x: x["entries"][0]["documento"].update(
        url_documento="https://portalsinan.saude.gov.br.attacker.invalid/a.pdf"),
    lambda x: x["entries"][0]["documento"].update(
        url_documento="http://portalsinan.saude.gov.br/a.pdf"),
    lambda x: x["entries"][0]["documento"].update(
        url_documento="https://portalsinan.saude.gov.br/%2e%2e/unsafe.pdf"),
    lambda x: x["entries"][0].update(
        ano_do_arquivo_pretendido=True),
    lambda x: x["entries"][0].update(
        agravo_alias_interno=[]),
    lambda x: x["entries"].append(
        copy.deepcopy(x["entries"][0])),
    lambda x: x["entries"][0].update(
        microdados={"names": "PROHIBITED"}),
])
def test_registry_refuses_unverified_status_unsafe_url_and_extra_fields(change):
    payload = {
        "schema_version": reg.SCHEMA,
        "catalog_revision": "2026-11-02-r1",
        "verified_portal_links_on": "2026-11-02",
        "scope": "evidencia_documental_de_fontes_oficiais_sem_atestado_de_compatibilidade_ano",
        "entries": [copy.deepcopy(v) for v in reg._index()[1]],
    }
    change(payload)
    with pytest.raises(ValueError):
        reg.validate_registry(payload)


def test_planner_includes_year_specific_evidence_without_real_numbers():
    planned = query_planner.planejar_consulta_agravo(
        "tuberculose", ano=2024, uf="PI")
    doc = planned["evidencia_documental_agravo_ano"]
    assert doc["link_dicionario_oficial_localizado"]
    assert not doc["compatibilidade_dicionario_ano_verificada"]
    assert not doc["consulta_de_dados_executada"]
    assert planned["resultado_epidemiologico"] is None
    earlier = query_planner.planejar_consulta_agravo("TUBE", ano=2023)
    assert earlier["evidencia_documental_agravo_ano"]["evidencia_documental"] is None
    unclear = query_planner.planejar_consulta_agravo("sífilis", ano=2024)
    assert unclear["evidencia_documental_agravo_ano"] is None
    absent = query_planner.planejar_consulta_agravo("TUBE")
    assert absent["evidencia_documental_agravo_ano"] is None


def test_public_registry_mcp_no_real_data():
    from mcp import Client

    async def exercise():
        async with Client(public_server.mcp, raise_exceptions=True) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
            assert {"listar_evidencias_documentais",
                    "consultar_evidencia_agravo_ano"} <= names
            result = await client.call_tool(
                "consultar_evidencia_agravo_ano", {"agravo": "TUBE", "ano": 2024}
            )
            assert not result.is_error
            c = result.structured_content
            assert c["evidencia_documental"]["titulo"]
            assert not c["autorizacao_de_publicacao"]
            assert not c["arquivo_anual_independentemente_verificado"]
            assert "TUBE" in json.dumps(c)
            others = await client.call_tool("listar_evidencias_documentais", {})
            assert not others.is_error
            assert others.structured_content[
                "quantidade_anos_de_arquivo_cientificamente_verificados"
            ] == 0

    asyncio.run(exercise())


def test_public_registry_code_no_private_imports():
    source = inspect.getsource(reg)
    for forbidden in (
        "import sqlite3", "from .core import", "pysus", "open(", "urlopen(",
        "requests.get", "from .provenance import",
        "SINAN_DB_PATH", "import subprocess",
    ):
        assert forbidden not in source


def _source_case(tmp_path):
    payload = b"CS_SEXO,CS_RACA\nF,4\n"
    datafile = tmp_path / "fictional.csv"
    datafile.write_bytes(payload)
    pdf_url = reg.consultar_evidencia_agravo_ano(
        "TUBE", 2024)["evidencia_documental"]["documento_url"]
    pdf = tmp_path / pdf_url.rsplit("/", 1)[-1]
    pdf.write_bytes(
        b"%PDF-1.4\n% synthetic placeholder ONLY; NOT official\n%%EOF\n"
    )
    manifest = {
        "schema_version": "sinan-source-evidence-v1",
        "agravo": "TUBE", "ano_arquivo": 2024,
        "tipo_ano": "ano_arquivo", "codigo_download_declarado": "TUBE",
        "metodo": "csv-local",
        "url_fonte": "https://www.gov.br/saude/pt-br/",
        "url_dicionario": pdf_url,
        "versao_dicionario": "example-not-validated",
        "situacao_declarada": "desconhecido",
        "extraido_em_utc": "2026-11-02T18:00:00Z",
        "arquivo_nome": datafile.name, "arquivo_bytes": len(payload),
        "arquivo_sha256": hashlib.sha256(payload).hexdigest(),
        "observacao_metodologica": "Apenas fixture inteiramente artificial",
    }
    path = tmp_path / "manifesto.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, datafile, pdf


def test_local_hash_cross_check_does_not_authenticate_counterfeit(tmp_path):
    manifest, datafile, pdf = _source_case(tmp_path)
    result = confrontar_documento_e_arquivo_local(manifest, datafile, pdf)
    assert result["checksum_dados_compativel_com_manifesto_local"]
    assert len(result["checksum_pdf_local_observado"]) == 64
    assert not result["conteudo_pdf_comparado_com_original_oficial"]
    assert not result["dicionario_compatibilidade_ao_ano_confirmada"]
    assert not result["autoriza_publicacao"]
    assert "CS_SEXO" not in json.dumps(result)
    assert "fictional.csv" not in json.dumps(result)


def test_local_cross_check_rejects_wrong_url_pdf_or_modified_file(tmp_path):
    manifest, datafile, pdf = _source_case(tmp_path)
    bad = json.loads(manifest.read_text(encoding="utf-8"))
    bad["url_dicionario"] = "https://portalsinan.saude.gov.br/tuberculose"
    manifest.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="URL do dicionário"):
        confrontar_documento_e_arquivo_local(manifest, datafile, pdf)
    bad["url_dicionario"] = reg.consultar_evidencia_agravo_ano(
        "TUBE", 2024)["evidencia_documental"]["documento_url"]
    manifest.write_text(json.dumps(bad), encoding="utf-8")
    pdf.write_bytes(b"FAKEPDF")
    with pytest.raises(ValueError, match="assinatura PDF"):
        confrontar_documento_e_arquivo_local(manifest, datafile, pdf)
    pdf.write_bytes(b"%PDF-1.4\n%%EOF")
    datafile.write_bytes(b"altered data")
    with pytest.raises(ValueError):
        confrontar_documento_e_arquivo_local(manifest, datafile, pdf)


def test_public_metadata_cli_does_not_need_private_db(tmp_path):
    cmd = [sys.executable, "-m", "sinan_mcp"]
    result = subprocess.run(
        cmd + ["consultar-evidencia-ano", "--agravo", "TUBE", "--ano", "2024"],
        cwd=tmp_path, capture_output=True, text=True, timeout=20
    )
    assert result.returncode == 0, result.stderr
    obj = json.loads(result.stdout)
    assert obj["link_dicionario_oficial_localizado"]
    assert not obj["compatibilidade_dicionario_ano_verificada"]
    assert not (tmp_path / "data").exists()
