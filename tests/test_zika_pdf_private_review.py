"""Synthetic-only private Zika PDF checklist security and progress tests."""
from __future__ import annotations

import copy
import inspect
import json
import os
import subprocess
import sys

import pytest

from sinan_mcp import zika_pdf_private_review as review
from sinan_mcp.zika_pdf_37_field_curation import carregar_transcricao_zika_pdf


def test_new_private_checklist_is_37_plus_7_and_never_approved(tmp_path):
    out = tmp_path / "zika-private-documentary-review.json"
    result = review.criar_pacote_revisao_zika(out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["campos"]) == 37
    assert len(data["ressalvas"]) == 7
    assert result["campos_por_declaracao_do_operador"]["PENDENTE"] == 37
    assert result["ressalvas_por_declaracao_do_operador"]["PENDENTE"] == 7
    assert data["hash_do_catalogo_versionado_nao_hash_oficial_pdf"] == (
        carregar_transcricao_zika_pdf()[
            "local_catalog_sha256_not_official_pdf_hash"
        ]
    )
    assert all(data[key] is value for key, value in review.STATIC_FLAGS.items())
    assert result["topicos_cientificos_pendentes"] == 10
    assert result["hash_oficial_pdf_autenticado"] is False
    assert result["parecer_independente_autenticado"] is False
    assert result["assinatura_revisor_verificada"] is False
    assert result["campos_2024_efetivamente_conferidos"] == 0
    assert result["indicadores_homologados"] == 0
    assert result["publicacao_autorizada"] is False
    if os.name != "nt":
        assert out.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        review.criar_pacote_revisao_zika(out)


def test_operator_may_report_documentary_findings_but_cannot_approve():
    data = review._build_checklist()
    data["campos"][0]["avaliacao_declarada_operador"] = "CONFERIDO_MANUALMENTE"
    data["campos"][12]["avaliacao_declarada_operador"] = "DIVERGENCIA_DOCUMENTAL"
    data["campos"][12]["nota_documental"] = "Comparar unidade codificada do PDF."
    data["campos"][21]["avaliacao_declarada_operador"] = "ILEGIVEL"
    data["campos"][21]["nota_documental"] = "A celula de categorias requer segunda leitura."
    data["ressalvas"][0]["avaliacao_declarada_operador"] = "OBSERVACAO_DOCUMENTADA"
    data["ressalvas"][0]["nota_documental"] = "Indicar interpretacao pendente."
    report = review.diagnosticar_dados_pacote_revisao_zika(data)
    counts = report["campos_por_declaracao_do_operador"]
    assert counts == {
        "CONFERIDO_MANUALMENTE": 1,
        "DIVERGENCIA_DOCUMENTAL": 1,
        "ILEGIVEL": 1,
        "PENDENTE": 34,
    }
    assert report["ressalvas_por_declaracao_do_operador"] == {
        "DIVERGENCIA_IDENTIFICADA": 0,
        "OBSERVACAO_DOCUMENTADA": 1,
        "PENDENTE": 6,
    }
    assert report["parecer_independente_autenticado"] is False
    assert report["publicacao_autorizada"] is False
    assert report["campos_2024_efetivamente_conferidos"] == 0


def test_even_all_fields_self_reported_remain_unapproved():
    data = review._build_checklist()
    for row in data["campos"]:
        row["avaliacao_declarada_operador"] = "CONFERIDO_MANUALMENTE"
    for issue in data["ressalvas"]:
        issue["avaliacao_declarada_operador"] = "OBSERVACAO_DOCUMENTADA"
        issue["nota_documental"] = "Nota documental nao autenticada."
    report = review.diagnosticar_dados_pacote_revisao_zika(data)
    assert report["campos_por_declaracao_do_operador"]["CONFERIDO_MANUALMENTE"] == 37
    assert report["ressalvas_por_declaracao_do_operador"]["OBSERVACAO_DOCUMENTADA"] == 7
    assert report["parecer_independente_autenticado"] is False
    assert report["assinatura_revisor_verificada"] is False
    assert report["topicos_cientificos_pendentes"] == 10
    assert report["publicacao_autorizada"] is False


@pytest.mark.parametrize("mutator", [
    lambda d: d.update(revisao_independente_autenticada=True),
    lambda d: d.update(assinatura_de_parecer_verificada=True),
    lambda d: d.update(dicionario_aplicavel_a_2024_validado=True),
    lambda d: d.update(esquema_arquivo_2024_conferido=True),
    lambda d: d.update(registros_clinicos_acessados=True),
    lambda d: d.update(indicadores_homologados=1),
    lambda d: d.update(publicacao_autorizada=True),
    lambda d: d.update(hash_do_catalogo_versionado_nao_hash_oficial_pdf="a"*64),
    lambda d: d.update(recurso_uuid_documental="264978ca-f795-4940-b5d3-ebc21e7d1c7c"),
    lambda d: d["campos"].pop(),
    lambda d: d["ressalvas"].pop(),
    lambda d: d["campos"][0].update(campo="fake"),
    lambda d: d["campos"][0].update(pagina_pdf=8),
    lambda d: d["campos"][0].update(tipo_documental="num(99)"),
    lambda d: d["campos"][0].update(dominio_descritor="qualquer"),
    lambda d: d["campos"][0].update(codigos_citados=["SECRET"]),
    lambda d: d["campos"][0].update(avaliacao_declarada_operador="APROVADO"),
    lambda d: d["campos"][0].update(avaliacao_declarada_operador=True),
    lambda d: d["campos"][0].update(
        avaliacao_declarada_operador="DIVERGENCIA_DOCUMENTAL"),
    lambda d: d["campos"][0].update(
        avaliacao_declarada_operador="ILEGIVEL"),
    lambda d: d["campos"][0].update(nota_documental="invalid\rcontrol"),
    lambda d: d["campos"][0].update(nota_documental="x"*601),
    lambda d: d["ressalvas"][0].update(campo="invalid"),
    lambda d: d["ressalvas"][0].update(motivo_documental="falsificado"),
    lambda d: d["ressalvas"][0].update(avaliacao_declarada_operador="APROVADO"),
    lambda d: d["ressalvas"][0].update(
        avaliacao_declarada_operador="OBSERVACAO_DOCUMENTADA"),
    lambda d: d.update(signed_pdf_url="https://unknown.example/patient"),
])
def test_review_rejects_forged_identity_approval_and_unexplained_differences(mutator):
    d = copy.deepcopy(review._build_checklist())
    mutator(d)
    with pytest.raises(ValueError):
        review.validar_pacote_revisao_zika(d)


def test_rejects_duplicate_keys_and_oversized_private_json(tmp_path):
    with pytest.raises(ValueError, match="repetida"):
        review._no_duplicate_keys([("agravo", "ZIKA"), ("agravo", "FAKE")])
    file = tmp_path / "malformed.json"
    file.write_bytes(b"x"*120_001)
    with pytest.raises(ValueError):
        review.diagnosticar_pacote_revisao_zika(file)
    file.write_text('{"status":1,"status":2}', encoding="utf-8")
    with pytest.raises(ValueError, match="repetida"):
        review.diagnosticar_pacote_revisao_zika(file)


def test_private_checklist_must_be_outside_git_worktree(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    target = repo / "private.json"
    with pytest.raises(ValueError, match="repositorio"):
        review.criar_pacote_revisao_zika(target)
    assert not target.exists()


def test_cli_created_and_reviewed_without_exposing_private_notes(tmp_path):
    file = tmp_path / "review-zika.json"
    command = [sys.executable, "-m", "sinan_mcp"]
    new = subprocess.run(
        command + ["preparar-revisao-documental-zika", "--saida", str(file)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert new.returncode == 0, new.stderr
    assert "Campos documentais: 37" in new.stdout
    assert "Ressalvas documentais: 7" in new.stdout
    assert "Parecer independente autenticado: NAO" in new.stdout
    data = json.loads(file.read_text(encoding="utf-8"))
    data["campos"][0]["avaliacao_declarada_operador"] = "DIVERGENCIA_DOCUMENTAL"
    data["campos"][0]["nota_documental"] = "NOTA INTERNA PRIVADA UNICA"
    file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    checked = subprocess.run(
        command + ["diagnosticar-revisao-documental-zika", "--arquivo", str(file)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert checked.returncode == 0, checked.stderr
    assert "Divergencias declaradas pelo operador: 1" in checked.stdout
    assert "NOTA INTERNA PRIVADA UNICA" not in checked.stdout
    assert "NOTA INTERNA PRIVADA UNICA" not in checked.stderr
    assert "Campos de ZIKABR24 lidos: 0" in checked.stdout
    assert "Indicadores homologados: 0; publicacao autorizada: NAO" in checked.stdout
    assert not (tmp_path / "sinan.sqlite3").exists()
    assert not (tmp_path / "ZIKABR24.json.zip").exists()
    assert not (tmp_path / "ZIKABR24.parquet.zip").exists()


def test_cli_refuses_preexisting_output_without_overwrite(tmp_path):
    out = tmp_path / "review.json"
    out.write_text("do not overwrite", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "sinan_mcp",
         "preparar-revisao-documental-zika", "--saida", str(out)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 2
    assert out.read_text(encoding="utf-8") == "do not overwrite"


def test_no_public_interface_or_case_loader_access():
    from sinan_mcp import public_server, local_schema_review
    source = inspect.getsource(review)
    for forbidden in ("import requests", "import sqlite3", "import pysus",
                      "urlopen(", "zipfile", "SINAN_DB_PATH"):
        assert forbidden not in source
    assert "zika_pdf_private_review" not in inspect.getsource(public_server)
    assert "Comparacao ZIKABR24 bloqueada" in inspect.getsource(
        local_schema_review.comparar_esquema_local
    )
