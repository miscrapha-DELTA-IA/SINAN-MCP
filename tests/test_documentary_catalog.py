"""Evidence-tracked documentary search with no epidemiologic-data capability."""
from __future__ import annotations

import json
from importlib.resources import files
from urllib.parse import urlsplit

import pytest

from sinan_mcp import documentary, official_sources, public_server

CODES = {"TUBE", "DENG", "CHIK", "ZIKA", "HANS", "SIFA", "SIFC",
         "HEPA", "MENI", "VIOL", "LEIV", "LTAN", "ANIM", "COQU"}


def test_registry_covers_all_14_with_dated_official_provenance():
    registry = json.loads(
        files("sinan_mcp").joinpath("documentary_registry.json").read_text(encoding="utf-8")
    )
    assert registry["schema_version"] == "sinan-documentary-registry-v1"
    assert registry["data_da_curadoria"] == "2026-11-05"
    assert len(registry["registros"]) == 14
    assert {r["codigo_interno"] for r in registry["registros"]} == CODES
    assert sum(len(r["referencias"]) for r in registry["registros"]) == 17
    for item in registry["registros"]:
        assert item["estado_de_evidencia"] == "pagina_oficial_localizada_sem_auditoria_de_arquivo"
        assert item["arquivos_reais_importados"] is False
        assert item["indicadores_reais_homologados"] is False
        assert item["dicionario_ano_versao_confrontado"] is False
        assert item["referencias"]
        for ref in item["referencias"]:
            link = urlsplit(ref["url"])
            assert link.scheme == "https"
            assert link.hostname in documentary.ALLOWED_HOSTS
            assert link.username is None and link.password is None
            assert not link.query and not link.fragment
            assert ref["data_conferencia"] == "2026-11-05"
            assert ref["verificacao"] == "pagina_publica_identificada_titulo_escopo"
            assert ref["arquivo_baixado_e_validado"] is False
            assert ref["conteudo_integral_auditado"] is False
            assert "justificativa_curadoria" in ref


@pytest.mark.parametrize("code", sorted(CODES))
def test_disease_specific_documentary_bundle_and_scientific_gate(code):
    response = official_sources.descrever_agravo(code)
    assert response["agravo"]["codigo_interno"] == code
    assert response["agravo"]["dados_reais_disponiveis_no_mcp_publico"] is False
    assert response["agravo"]["dicionario_ano_versao_confrontado"] is False
    assert response["evidencia_por_agravo"]["codigo_interno"] == code
    assert response["evidencia_por_agravo"]["referencias"]
    assert response["auditoria_documental"]["data_do_ultimo_teste_online"] is None
    checks = response["checklist_pesquisa_antes_de_calcular"]
    assert len(checks) == 5
    assert [x["realizado"] for x in checks] == [True, False, False, False, False]
    assert all(ref["arquivo_baixado_e_validado"] is False
               for ref in response["agravo"]["fontes_documentais_especificas"])


@pytest.mark.parametrize("query,expected", [
    ("hanseniase", "HANS"),
    ("tuberculose", "TUBE"),
    ("TUBE", "TUBE"),
    ("escorpiao", "ANIM"),
    ("leishmaniose cutanea", "LTAN"),
    ("sifilis congenita", "SIFC"),
    ("coqueluche", "COQU"),
    ("zikv", "ZIKA"),
])
def test_curated_search_is_accent_tolerant_and_synonym_aware(query, expected):
    results = official_sources.pesquisar_agravos(query, 10)
    assert results["resultados"]
    assert results["resultados"][0]["codigo_interno"] == expected
    assert results["auditoria_documental"]["agravos_com_pagina_institucional"] == 14
    assert all(r["dados_reais_disponiveis_no_mcp_publico"] is False
               for r in results["resultados"])


def test_typo_suggestions_are_not_mislabelled_as_real_matches():
    suggestion = official_sources.pesquisar_agravos("tuberculoze")
    assert suggestion["resultados"] == []
    assert any(x["codigo_interno"] == "TUBE" for x in suggestion["sugestoes_de_grafia"])
    assert all(x["tipo"] == "sugestao_nao_resultado"
               for x in suggestion["sugestoes_de_grafia"])
    unknown = official_sources.pesquisar_agravos("uma doenca imaginaria inexistente")
    assert unknown["resultados"] == []


def test_source_directory_and_public_server_do_not_consult_external_sites(monkeypatch):
    # A network call in a public tool would invalidate openWorldHint=false.
    import socket
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Public catalogue attempted a network operation")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    sources = public_server.listar_fontes_oficiais()
    assert sources["natureza"] == "somente_metadados_de_navegacao"
    audit = sources["auditoria_documental"]
    assert audit["referencias_de_paginas_institucionais"] == 17
    assert audit["indicadores_epidemiologicos_homologados"] == 0
    assert audit["verificacao_ao_vivo_em_requisicoes_mcp"] is False
    assert public_server.descrever_agravo("ZIKA")["evidencia_por_agravo"]["referencias"][1]["url"].startswith(
        "https://dadosabertos.saude.gov.br/")
    assert public_server.pesquisar_agravos("hanseniase")["resultados"][0]["codigo_interno"] == "HANS"


def test_documentary_records_return_independent_copies():
    first = documentary.obter_evidencias("TUBE")
    first["referencias"][0]["url"] = "https://unsafe.example.invalid"
    second = documentary.obter_evidencias("TUBE")
    assert second["referencias"][0]["url"].startswith("https://portalsinan.saude.gov.br/")


def test_public_tool_inventory_remains_unchanged_and_all_data_is_synthetic():
    assert public_server.listar_bases()["dados_reais_disponiveis"] is False
    assert public_server.PUBLIC_VERSION == "0.4.0a6"
    assert public_server.contar_notificacoes("TUBE", 2024, 2024, "PI")[
        "proveniencia"]["fonte"] == "synthetic-in-code/v2"


def test_registry_rejects_non_official_domains_fail_closed(monkeypatch, tmp_path):
    source = json.loads((files("sinan_mcp") / "documentary_registry.json")
                        .read_text(encoding="utf-8"))
    source["registros"][0]["referencias"][0]["url"] = "https://evil.example.invalid/patient"
    malicious = tmp_path / "documentary_registry.json"
    malicious.write_text(json.dumps(source), encoding="utf-8")

    class FakePackage:
        def joinpath(self, _name):
            return malicious

    documentary._load_registry.cache_clear()
    monkeypatch.setattr(documentary, "files", lambda _name: FakePackage())
    try:
        with pytest.raises(ValueError, match="domínios permitidos"):
            documentary._load_registry()
    finally:
        documentary._load_registry.cache_clear()


@pytest.mark.parametrize("code,expected_fields", [("ZIKA", 42), ("TUBE", 20)])
def test_public_instrument_documentation_has_hashed_pdf_refs_but_no_2024_data(code, expected_fields):
    bundle = public_server.descrever_agravo(code)["instrumentos_e_campos_documentais_2024"]
    assert bundle["ano_alvo"] == 2024
    assert bundle["total_documentos"] == 4
    assert len(bundle["campos_documentais"]) == expected_fields
    assert bundle["total_campos_documentais"] == expected_fields
    assert bundle["correspondencia_arquivo_sinan_2024_validada"] is False
    assert bundle["revisao_independente_aprovada"] is False
    assert all(x["integridade_bytes_verificada"] is True
               and x["correspondencia_com_arquivo_2024_validada"] is False
               and x["parecer_independente_aprovado"] is False
               and len(x["sha256_pdf"]) == 64 for x in bundle["documentos"])
    assert all(x["correspondencia_arquivo_2024"] == "NAO_VERIFICADA"
               and x["revisao_humana"] == "PENDENTE" for x in bundle["campos_documentais"])
    indexed = public_server.pesquisar_agravos(code)
    found = next(r for r in indexed["resultados"] if r["codigo_interno"] == code)
    assert found["resumo_instrumentos_2024"]["codigos_de_campo_localizados_na_pagina"] == expected_fields
    assert found["resumo_instrumentos_2024"]["parecer_independente_aprovado"] is False


def test_public_snapshot_exactly_tracks_offline_source_manifest_and_field_matrix():
    import csv
    from pathlib import Path

    snapshot = json.loads(files("sinan_mcp").joinpath("public_instruments_2024.json")
                          .read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[1]
    original = json.loads((root / "docs/instruments-2024/source_manifest.json")
                          .read_text(encoding="utf-8"))
    with (root / "docs/instruments-2024/field_matrix.csv").open(encoding="utf-8") as f:
        fields = list(csv.DictReader(f))
    assert snapshot["actual_2024_dataset_schema_validated"] is False
    assert snapshot["independent_scientific_review_approved"] is False
    assert snapshot["real_data_access"] is False
    assert len(fields) == 57
    unique_docs = {}
    for code in ("ZIKA", "TUBE"):
        bundle = snapshot["diseases"][code]
        expected = [r for r in fields if r["agravo"] in (code, "COMMON")]
        assert len(bundle["campos_documentais"]) == len(expected)
        for got, row in zip(bundle["campos_documentais"], expected):
            assert got["codigo"] == row["campo_documental"]
            assert got["pagina_pdf"] == int(row["pagina_pdf"])
            assert got["documento_id"] == row["fonte_id"]
            assert got["rotulo_documental"] == row["rotulo_documental"]
            assert got["tipo_resumido"] == row["tipo_documental_resumido"]
            assert got["observacoes"] == row["observacao_ou_codificacao"]
        for doc in bundle["documentos"]:
            unique_docs[doc["id"]] = doc
            original_doc = next(d for d in original["files"] if d["id"] == doc["id"])
            assert doc["url_pdf"] == original_doc["source_url"]
            assert doc["sha256_pdf"] == original_doc["byte_integrity"]["sha256"]
            assert doc["tamanho_bytes_pdf"] == original_doc["byte_integrity"]["bytes"]
            assert doc["paginas"] == original_doc["expected_pages_from_pdf_preview"]
    assert len(unique_docs) == 7
    assert documentary.obter_instrumentos_2024("DENG") is None
    assert public_server.descrever_agravo("DENG")["instrumentos_e_campos_documentais_2024"] is None


def test_public_instruments_are_independent_read_only_copies():
    first = documentary.obter_instrumentos_2024("ZIKA")
    first["documentos"][0]["sha256_pdf"] = "0" * 64
    second = documentary.obter_instrumentos_2024("ZIKA")
    assert second["documentos"][0]["sha256_pdf"] != "0" * 64


def test_public_synthetic_fixture_is_demographically_balanced_and_fictional():
    from collections import Counter
    rows = list(public_server._fake_rows())
    assert len(rows) == 120
    for pos in (0, 1):
        categories = {row[pos] for row in rows}
        assert len(categories) == 2
        group_counts = Counter(row[pos] for row in rows)
        group_loss = Counter(row[pos] for row in rows if row[2] == "2")
        assert sorted(group_counts.values()) == [60, 60]
        assert sorted(group_loss.values()) == [12, 12]
    reported = public_server.proporcao_abandono_tuberculose(2024, 2024, "PI")
    assert all(row["proporcao_ficticia_percentual"] == 20.0
               for row in reported["resultado"]["dados"])
    assert reported["proveniencia"]["fonte"] == "synthetic-in-code/v2"
    assert "SINTÉTICO" in reported["aviso"]
