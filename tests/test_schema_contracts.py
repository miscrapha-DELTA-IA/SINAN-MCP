"""Optional Pandera PoC uses exclusively fictional records, no patient data."""
from __future__ import annotations

import csv
import json
import subprocess
import sys

import pytest

from sinan_mcp import schema_contracts as sc


def _csv(tmp_path, *, bad_value=None, extra_column=False, drop_column=False,
         repeat_column=False, empty=False):
    path = tmp_path / "fake-sinan.csv"
    cols = ["ID_MN_RESI", "CS_SEXO", "CS_RACA", "SITUA_ENCE"]
    if drop_column:
        cols.remove("SITUA_ENCE")
    if repeat_column:
        cols.append("CS_SEXO")
    if extra_column:
        cols.append("NM_PACIENT")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(cols)
        if not empty:
            record = {
                "ID_MN_RESI": "221100", "CS_SEXO": "F",
                "CS_RACA": "4", "SITUA_ENCE": "2", "NM_PACIENT": "DO-NOT-ECHO-ME",
            }
            if bad_value:
                record[bad_value[0]] = bad_value[1]
            writer.writerow([record[col] for col in cols])
    return path


def test_explicitly_synthetic_contract_metadata_and_reproducible_hash():
    out = sc.list_example_contracts()
    assert out["apenas_exemplos_sinteticos"]
    assert not out["dicionarios_oficiais_verificados"]
    assert len(out["contratos"]) == 2
    for item in out["contratos"]:
        assert len(item["sha256"]) == 64
        assert item["sha256"] == next(
            x["sha256"] for x in sc.list_example_contracts()["contratos"]
            if x["id"] == item["id"]
        )
        doc = sc.load_example_contract(item["id"])
        assert doc["permissao_publicacao"] is False
        assert doc["documento_oficial_verificado"] is False
        assert doc["allow_extra_columns"] is False


def test_contract_diff_is_comparable_but_not_official():
    diff = sc.diff_example_contracts(
        "DENG_2024_EXAMPLE", "TUBE_2024_EXAMPLE")
    assert diff["colunas_adicionadas"] == ["SITUA_ENCE"]
    assert not diff["dicionarios_oficiais_verificados"]
    reverse = sc.diff_example_contracts(
        "TUBE_2024_EXAMPLE", "DENG_2024_EXAMPLE")
    assert reverse["colunas_removidas"] == ["SITUA_ENCE"]


@pytest.mark.parametrize("name", [
    "TUBE_2023_EXAMPLE", "TUBE_2024_EXAMPLE/../../etc/passwd",
    "../DENG_2024_EXAMPLE", "TUBE", None, [], {},
])
def test_contract_registry_has_allowlisted_ids_only(name):
    with pytest.raises(ValueError):
        sc.load_example_contract(name)


def test_example_cli_lists_and_diffs_without_patient_files(tmp_path):
    cmd = [sys.executable, "-m", "sinan_mcp"]
    ls = subprocess.run(
        cmd + ["listar-contratos-demo"],
        cwd=tmp_path, capture_output=True, text=True, timeout=20
    )
    assert ls.returncode == 0, ls.stderr
    assert json.loads(ls.stdout)["apenas_exemplos_sinteticos"]
    diff = subprocess.run(
        cmd + ["comparar-contratos-demo", "DENG_2024_EXAMPLE",
               "TUBE_2024_EXAMPLE"],
        cwd=tmp_path, capture_output=True, text=True, timeout=20
    )
    assert diff.returncode == 0, diff.stderr
    assert "SITUA_ENCE" in diff.stdout
    assert not (tmp_path / "data").exists()


def test_pandera_accepts_clean_synthetic_rows_and_never_claims_validation(tmp_path):
    pytest.importorskip("pandera.pandas")
    fake = _csv(tmp_path)
    report = sc.validate_example_csv(fake, contract_id="TUBE_2024_EXAMPLE")
    assert report["linhas_exemplo_processadas_localmente"] == 1
    assert report["estrutura_exemplar_compativel"]
    assert not report["dicionario_oficial_ano_validado"]
    assert not report["publicacao_autorizada"]
    assert "221100" not in json.dumps(report)
    assert str(fake) not in json.dumps(report)


@pytest.mark.parametrize("options", [
    {"bad_value": ("CS_SEXO", "X")},
    {"bad_value": ("ID_MN_RESI", "not-a-code")},
    {"bad_value": ("CS_RACA", "99")},
    {"bad_value": ("SITUA_ENCE", "SECRETO_DO_PACIENTE")},
    {"extra_column": True}, {"drop_column": True},
    {"repeat_column": True}, {"empty": True},
])
def test_pandera_rejects_injected_schema_drift_without_raw_echo(tmp_path, options):
    pytest.importorskip("pandera.pandas")
    source = _csv(tmp_path, **options)
    with pytest.raises(ValueError) as ex:
        sc.validate_example_csv(source, contract_id="TUBE_2024_EXAMPLE")
    assert "SECRETO_DO_PACIENTE" not in str(ex.value)
    assert "DO-NOT-ECHO-ME" not in str(ex.value)
    assert str(source) not in str(ex.value)


def test_symlink_and_large_file_are_blocked(tmp_path):
    source = _csv(tmp_path)
    symlink = tmp_path / "alias.csv"
    try:
        symlink.symlink_to(source)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink unavailable in CI")
    with pytest.raises(ValueError, match="simbólico"):
        sc.validate_example_csv(symlink, contract_id="TUBE_2024_EXAMPLE")


def test_public_mcp_does_not_load_pandera_or_contract_validator():
    import inspect
    from sinan_mcp import public_server
    source = inspect.getsource(public_server)
    assert "from .schema_contracts import" not in source
    assert "pandera" not in source
    assert "validar-csv-demo" not in source
