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
    assert public_server.PUBLIC_VERSION == "0.4.0a5"
    assert public_server.contar_notificacoes("TUBE", 2024, 2024, "PI")[
        "proveniencia"]["fonte"] == "synthetic-in-code/v1"


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
