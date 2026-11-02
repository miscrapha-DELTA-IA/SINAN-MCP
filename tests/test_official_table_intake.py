"""Offline fake fixtures for official TABNET candidate intake (never real data)."""
from __future__ import annotations

import copy
import json
import subprocess
import sys

import pytest

from sinan_mcp.official_table_intake import (
    prepare_private_tabnet_candidate, validate_official_tabulation,
)


def example():
    return {
        "schema_version": "sinan-official-tabulation-candidate-v1",
        "stage": "UNAPPROVED_OFFICIAL_TABULATION",
        "source": {
            "url": "https://datasus.saude.gov.br/informacoes-de-saude-tabnet/",
            "titulo_tabela": "EXEMPLO ARTIFICIAL, NAO EXTRAIDO DE SISTEMA REAL",
            "extracao_utc": "2026-11-02T18:00:00Z",
            "sha256_arquivo_origem": "a" * 64,
            "filtros_tabulacao": "exemplo ficticio; ANO 2024; UF PI; sexo",
            "estado_consolidacao": "desconhecido",
        },
        "scope": {
            "agravo_codigo_interno": "HEPA", "agravo_nome": "Hepatites virais",
            "uf": "PI", "ano_inicio": 2024, "ano_fim": 2024,
            "tipo_ano": "ano_notificacao", "indicador": "registros_tabnet",
            "dimensao": "sexo",
        },
        "cells": [{"categoria": "F", "registros": 120},
                  {"categoria": "M", "registros": 130}],
        "limitations": (
            "DADOS ARTIFICIAIS DE TESTE; nao equivalem a notificacoes "
            "reais, nao aprovados para publicacao."
        ),
    }


def test_multiple_diseases_can_enter_local_review_without_loading_mcp():
    for code, name in [
        ("HEPA", "Hepatites virais"),
        ("HANS", "Hanseníase"),
        ("DENG", "Dengue"),
        ("TUBE", "Tuberculose"),
        ("ANIM", "Acidentes animais peçonhentos"),
    ]:
        item = example()
        item["scope"]["agravo_codigo_interno"] = code
        item["scope"]["agravo_nome"] = name
        assert validate_official_tabulation(item) is item


@pytest.mark.parametrize("change", [
    lambda x: x["cells"][0].update(registros=2),
    lambda x: x["cells"][0].update(registros=True),
    lambda x: x["cells"].append({"categoria": "F", "registros": 500}),
    lambda x: x["source"].update(url="http://not-trusted.example.org/"),
    lambda x: x["source"].update(url="https://evil.example.org/data"),
    lambda x: x["source"].update(estado_consolidacao="certificada"),
    lambda x: x["scope"].update(indicador="risco_clinico_individual"),
    lambda x: x["scope"].update(tipo_ano="desconhecido"),
    lambda x: x["scope"].update(ano_inicio=2025, ano_fim=2024),
    lambda x: x["scope"].update(dimensao="municipio"),
    lambda x: x.update(stage="APPROVED_PUBLIC_AGGREGATE"),
    lambda x: x.update(pacientes=[{"nome": "SEGREDO"}]),
    lambda x: x["source"].update(sha256_arquivo_origem="nao-possui"),
])
def test_fail_closed_on_unreviewed_tabulations(change):
    data = example()
    change(data)
    with pytest.raises(ValueError):
        validate_official_tabulation(data)


def test_candidate_is_private_and_never_uploaded(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    original = tmp_path / "private_input.json"
    payload = example()
    original.write_text(json.dumps(payload), encoding="utf-8")
    private = prepare_private_tabnet_candidate(original)
    assert private.is_file()
    assert private.parent == tmp_path / "data" / "review-packages"
    assert private.name.startswith("tabnet-HEPA-PI-2024-2024-")
    assert json.loads(private.read_text(encoding="utf-8"))["stage"] == "UNAPPROVED_OFFICIAL_TABULATION"
    with pytest.raises(FileExistsError):
        prepare_private_tabnet_candidate(original)
    with pytest.raises(ValueError, match="data/"):
        prepare_private_tabnet_candidate(original, review_dir=tmp_path/"public")
    assert original.read_text(encoding="utf-8") == json.dumps(payload)


def test_local_cli_safe_output_no_cells(tmp_path):
    item = example()
    inp = tmp_path / "table.json"
    inp.write_text(json.dumps(item), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "sinan_mcp", "preparar-tabela-oficial", str(inp)],
        cwd=tmp_path, capture_output=True, text=True, timeout=20,
    )
    assert proc.returncode == 0, proc.stderr
    assert "CANDIDATO PRIVADO NÃO APROVADO" in proc.stdout
    assert "120" not in proc.stdout and "130" not in proc.stdout
    assert not any(tmp_path.rglob("*.sqlite3"))
    assert len(list((tmp_path/"data").rglob("*.candidate.json"))) == 1


def test_invalid_cli_refuses_and_writes_nothing(tmp_path):
    item = example()
    item["cells"][0]["registros"] = 3
    inp = tmp_path/"table.json"
    inp.write_text(json.dumps(item), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "sinan_mcp", "preparar-tabela-oficial", str(inp)],
        cwd=tmp_path, capture_output=True, text=True, timeout=20,
    )
    assert proc.returncode == 2
    assert "TABELA NÃO ADMITIDA" in proc.stderr
    assert "Traceback" not in proc.stderr
    assert not (tmp_path/"data"/"review-packages").exists()



def test_category_aliases_are_single_dimension_only():
    item = example()
    item["cells"] = [
        {"categoria": "Feminino", "registros": 120},
        {"categoria": "Masculino", "registros": 130},
    ]
    assert validate_official_tabulation(item) is item

    item["cells"][0]["categoria"] = "F"  # same canonical sex category
    item["cells"][1]["categoria"] = "Feminino"
    with pytest.raises(ValueError, match="duplicada"):
        validate_official_tabulation(item)

    item["cells"][1]["categoria"] = "F de 0 a 4 anos"  # covert intersection
    with pytest.raises(ValueError, match="não reconhecida"):
        validate_official_tabulation(item)

    item["scope"]["dimensao"] = "raca_cor"
    item["cells"] = [
        {"categoria": "Parda", "registros": 120},
        {"categoria": "Branca", "registros": 130},
    ]
    assert validate_official_tabulation(item) is item
    item["cells"][1]["categoria"] = "4"
    with pytest.raises(ValueError, match="duplicada"):
        validate_official_tabulation(item)


def test_duplicate_json_keys_refused_before_candidate_creation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = json.dumps(example(), ensure_ascii=False)
    payload = payload.replace(
        '"stage": "UNAPPROVED_OFFICIAL_TABULATION"',
        '"stage": "UNAPPROVED_OFFICIAL_TABULATION", "stage": "UNAPPROVED_OFFICIAL_TABULATION"',
        1,
    )
    source = tmp_path / "duplicate.json"
    source.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicadas"):
        prepare_private_tabnet_candidate(source)
    assert not (tmp_path / "data").exists()


def test_symlinked_data_root_cannot_leak_private_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    outside = tmp_path / "public-assets"
    outside.mkdir()
    try:
        (tmp_path / "data").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("O sistema não permite criar links simbólicos")
    source = tmp_path / "private.json"
    source.write_text(json.dumps(example(), ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="simbólico"):
        prepare_private_tabnet_candidate(source)
    assert list(outside.iterdir()) == []
