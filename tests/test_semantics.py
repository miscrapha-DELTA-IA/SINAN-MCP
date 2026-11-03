"""Public semantic planner: no real data, no ambiguous epidemiological claims."""
from __future__ import annotations

import asyncio
import inspect
import json

import pytest

from sinan_mcp import public_server as public
from sinan_mcp import semantics

BASE = dict(
    agravo="TUBE", ano_do_arquivo=2024,
    unidade_observacional="registro_de_notificacao",
    eixo_temporal="ano_do_arquivo",
    tipo_medida="contagem_registros",
)


def test_public_vocabulary_is_metadata_only():
    result = semantics.vocabulario_semantico()
    assert result["indicadores_reais_validados"] == []
    assert not result["consulta_executada"]
    assert "incidencia" in result["tipos_medida"]
    assert "ano_diagnostico" in result["eixos_temporais"]


def test_valid_reference_is_still_not_data_availability():
    p = semantics.planejar_medida_epidemiologica(**BASE)
    assert p["estado"] == "sem_fonte_e_metodo_validados_para_ano"
    assert p["valor"] is None
    assert p["aceito_para_calculo_real"] is False
    assert p["denominador"] == "nao_se_aplica"
    assert not p["consulta_executada"]


def test_incidence_without_denominator_refused():
    p = semantics.planejar_medida_epidemiologica(
        **{**BASE, "tipo_medida": "incidencia",
           "unidade_observacional": "caso_confirmado"})
    assert p["estado"] == "recusado_sem_denominador_e_fonte"
    assert not p["aceito_para_calculo_real"]


def test_incidence_with_unverified_reference_still_cannot_calculate():
    p = semantics.planejar_medida_epidemiologica(
        **{**BASE, "tipo_medida": "incidencia",
           "unidade_observacional": "caso_confirmado",
           "denominador": "pessoas_em_risco",
           "fonte_denominador": "ibge_a_verificar"})
    assert p["estado"] == "sem_fonte_e_metodo_validados_para_ano"
    assert p["valor"] is None
    assert not p["aceito_para_calculo_real"]


@pytest.mark.parametrize("changes,expected", [
    ({"agravo": "ABCD"}, "fora_do_indice_curado"),
    ({"unidade_observacional": "individuo"},
     "recusado_contagem_nao_e_registro_de_notificacao"),
    ({"tipo_medida": "letalidade", "unidade_observacional": "obito",
      "denominador": "populacao_residente",
      "fonte_denominador": "fonte_oficial_a_verificar"},
     "recusado_letalidade_sem_obitos_e_casos"),
    ({"tipo_medida": "prevalencia", "unidade_observacional": "individuo",
      "denominador": "pessoas_em_risco",
      "fonte_denominador": "ibge_a_verificar"},
     "recusado_prevalencia_sem_pessoas_e_populacao"),
    ({"denominador": "casos_confirmados"},
     "recusado_denominador_indevido_para_contagem"),
])
def test_refusal_states_are_structured(changes, expected):
    p = semantics.planejar_medida_epidemiologica(**{**BASE, **changes})
    assert p["estado"] == expected
    assert p["valor"] is None


@pytest.mark.parametrize("changes", [
    {"ano_do_arquivo": True}, {"ano_do_arquivo": "2024"},
    {"tipo_medida": "risco_ajustado"}, {"tipo_medida": None},
    {"eixo_temporal": "ano_do_diagnostico_privado"},
    {"unidade_observacional": "paciente_nomeado"},
    {"fonte_denominador": "https://malicious.test"},
    {"fonte_denominador": []}, {"denominador": {}},
    {"agravo": ["TUBE"]},
])
def test_untrusted_and_unknown_inputs_rejected(changes):
    with pytest.raises(ValueError):
        semantics.planejar_medida_epidemiologica(**{**BASE, **changes})


def test_public_synthetic_values_carry_unambiguous_semantics():
    r = public.contar_notificacoes("TUBE", 2024, 2024, "PI", None, "sexo")
    assert r["semantica"]["unidade_observacional"] == "registro_ficticio_nao_caso"
    assert r["semantica"]["denominador"] == "nao_se_aplica"
    assert r["semantica"]["nao_e_incidencia"]
    loss = public.proporcao_abandono_tuberculose(
        2024, 2024, "PI", None, "raca_cor")
    assert loss["semantica"]["denominador"] == "total_registros_ficticios_da_categoria"
    assert loss["semantica"]["nao_e_estimativa_de_risco"]
    assert "SINTÉTICO" in loss["aviso"]


def test_semantics_import_boundary_no_data_access():
    text = inspect.getsource(semantics)
    for forbidden in ("import sqlite3", "import os", "import requests",
                      "urllib", "SINAN_DB_PATH", "from .core import",
                      "from .server import", "subprocess"):
        assert forbidden not in text


def test_mcp_tools_and_current_protocol():
    from mcp import Client

    async def probe():
        async with Client(public.mcp, mode="auto", raise_exceptions=True) as client:
            assert str(client.protocol_version) == "2026-07-28"
            named = {t.name for t in (await client.list_tools()).tools}
            assert {"vocabulario_semantico", "planejar_medida_epidemiologica"} <= named
            r = await client.call_tool("planejar_medida_epidemiologica", BASE)
            assert not r.is_error
            assert r.structured_content["estado"] == "sem_fonte_e_metodo_validados_para_ano"
            assert r.structured_content["valor"] is None

    asyncio.run(probe())
