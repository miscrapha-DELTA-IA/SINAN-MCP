"""Offline synthetic-only DENG quality rehearsal: no patient records or ZIP files."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from sinan_mcp import synthetic_dengue_csv_audit as qa


def _plan(tmp_path: Path) -> Path:
    p = tmp_path / "plano-qualidade-DENG-2024-privado.json"
    doc = {
        "schema_version": qa.PLAN_SCHEMA,
        "scope": {
            "agravo": "DENG", "ano_do_arquivo": 2024,
            "resource_id": qa.RESOURCE_ID,
        },
        "parecer_esquema_sha256_local": "a" * 64,
        "dossie_fonte_sha256_local": "b" * 64,
        "zip_sha256_local": "c" * 64,
        "quality_checkpoints": {
            name: {"status": "PENDENTE", "definicao_de_aceite": description}
            for name, description in qa.CHECKPOINTS.items()
        },
        "unidade_observacional": "NAO_DEFINIDA",
        "coorte_definida_independentemente": False,
        "revisao_clinica_independente": "PENDENTE",
        "data_cutoff_confirmada": False,
        "qualidade_dados_clinicos_auditada": False,
        "n_linhas_clinicas_lidas": 0,
        "indicadores_reais_calculados": False,
        "apto_analise_ou_publicacao": False,
        "roadmap_quality_gate_alterado": False,
        "status": "PLANO_PRIVADO_NAO_VALIDADO",
    }
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def test_synthetic_counts_and_no_implicit_case_classification():
    report = qa._scan_marked_synthetic_csv(qa._fixture())
    assert report["linhas_sinteticas"] == 6
    assert report["colunas_incluindo_marcador"] == 8
    assert report["datas_literais_invalidas"] == {
        "DT_NOTIFIC": 1, "DT_SIN_PRI": 0
    }
    assert report["notificacoes_fora_do_ano_rotulado_hipotetico"] == 1
    assert report["sequencias_sintomas_posteriores_a_notificacao_para_revisao"] == 1
    assert report["linhas_inteiras_textualmente_identicas_alem_da_primeira"] == 1
    assert report["ausentes_por_coluna_sintetica"]["DT_SIN_PRI"] == 1
    assert report["ausentes_por_coluna_sintetica"]["SG_UF"] == 1
    assert report["ausentes_por_coluna_sintetica"]["UF"] == 1
    assert report["ausentes_por_coluna_sintetica"]["CLASSI_FIN"] == 1
    assert report["ausentes_por_coluna_sintetica"]["CLINC_CHIK"] == 5
    assert report["casos_reais_contados"] is False
    assert report["CLINC_CHIK_alias_automatico"] is False
    assert report["CLASSI_FIN_dominios_inferidos"] is False
    assert report["UF_semantica_inferida"] is False


@pytest.mark.parametrize("mutate", [
    lambda x: x.replace(qa.MARKER_VALUE, "NOT_SYNTHETIC", 1),
    lambda x: x.replace("DT_NOTIFIC,", "DT_NOTIFIC,DT_NOTIFIC,", 1),
    lambda x: x + "incomplete,row\n",
    lambda x: x.replace("DT_NOTIFIC,", "NOT_IN_SCHEMA,", 1),
    lambda x: x.replace("2024-01-15", "X" * 257, 1),
    lambda x: x + (qa._fixture().splitlines()[1] + "\n") * 65,
    lambda x: x + ("X" * qa.MAX_CSV_BYTES),
])
def test_malformed_or_oversized_fixtures_are_rejected(mutate):
    with pytest.raises(ValueError):
        qa._scan_marked_synthetic_csv(mutate(qa._fixture()))


def test_parser_never_responds_with_csv_literal_values():
    data = qa._fixture().replace("2024-03-05", '=HYPERLINK("https://example.org")')
    counts = qa._scan_marked_synthetic_csv(data)
    assert "HYPERLINK" not in str(counts)
    assert "example.org" not in str(counts)
    assert counts["datas_literais_invalidas"]["DT_SIN_PRI"] == 1


def test_private_report_is_synthetic_and_nonreplacing(tmp_path):
    p = _plan(tmp_path)
    dest = tmp_path / "simulacao.json"
    response = qa.auditar_fixture_dengue_local(p, dest)
    assert response["linhas_sinteticas"] == 6
    assert response["casos_adversariais_recusados"] == 4
    assert response["registros_reais_lidos"] == 0
    assert response["checkpoints_cientificos_validados"] == 0
    assert response["publicacao_autorizada"] is False
    doc = json.loads(dest.read_text(encoding="utf-8"))
    assert doc["origem_dados"] == "FIXTURE_INTERNA_100_POR_CENTO_SINTETICA"
    assert doc["referencia_csv_real_lida"] is False
    assert doc["caminhos_csv_ou_zip_aceitos"] is False
    assert doc["roadmap_alterado"] is False
    assert doc["publicacao_autorizada"] is False
    assert doc["plano_privado_sha256_local"] == qa._plan_digest(p)
    assert "2024-01-15" not in str(doc)
    assert "2024-03-05" not in str(doc)
    if os.name != "nt":
        assert dest.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        qa.auditar_fixture_dengue_local(p, dest)


@pytest.mark.parametrize("tamper", [
    lambda d: d.update({"apto_analise_ou_publicacao": True}),
    lambda d: d.update({"qualidade_dados_clinicos_auditada": True}),
    lambda d: d.update({"roadmap_quality_gate_alterado": True}),
    lambda d: d.update({"n_linhas_clinicas_lidas": 99}),
    lambda d: d.update({"status": "APROVADO"}),
    lambda d: d["scope"].update({"agravo": "TUBE"}),
    lambda d: d["quality_checkpoints"]["consistencia_temporal"].update(
        {"status": "APROVADO"}
    ),
    lambda d: d.update({"zip_sha256_local": "not-a-sha"}),
])
def test_forged_approval_or_wrong_scope_fails_without_output(tmp_path, tamper):
    p = _plan(tmp_path)
    data = json.loads(p.read_text(encoding="utf-8"))
    tamper(data)
    p.write_text(json.dumps(data), encoding="utf-8")
    dest = tmp_path / "simulacao.json"
    with pytest.raises(ValueError):
        qa.auditar_fixture_dengue_local(p, dest)
    assert not dest.exists()


def test_duplicate_json_keys_fail_closed(tmp_path):
    p = _plan(tmp_path)
    raw = p.read_text(encoding="utf-8")
    p.write_text(raw[:-1] + ', "status": "PLANO_PRIVADO_NAO_VALIDADO"}',
                 encoding="utf-8")
    with pytest.raises(ValueError):
        qa.auditar_fixture_dengue_local(p, tmp_path / "simulacao.json")


def test_other_folder_rejected(tmp_path):
    p = _plan(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(ValueError):
        qa.auditar_fixture_dengue_local(p, outside / "simulacao.json")


def test_cli_accepts_plan_only_and_never_opens_user_csv(tmp_path):
    p = _plan(tmp_path)
    dest = tmp_path / "simulation.json"
    cmd = [sys.executable, "-m", "sinan_mcp",
           "auditar-csv-sintetico-dengue"]
    rejected = subprocess.run(cmd + [
        "--plano", str(p), "--zip", "never-access.csv.zip",
        "--saida", str(dest),
    ], capture_output=True, text=True, timeout=20)
    assert rejected.returncode != 0
    assert not dest.exists()
    valid = subprocess.run(cmd + [
        "--plano", str(p), "--saida", str(dest),
    ], capture_output=True, text=True, timeout=20)
    assert valid.returncode == 0, valid.stderr
    assert "NENHUM DADO SINAN LIDO" in valid.stdout
    assert "Linhas artificiais: 6" in valid.stdout
    assert "Publicacao autorizada: NAO" in valid.stdout
    assert dest.exists()
