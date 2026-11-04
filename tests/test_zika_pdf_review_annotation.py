"""Synthetic-only versioned Zika PDF documentary review observations."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from sinan_mcp.zika_pdf_private_review import (
    criar_pacote_revisao_zika, diagnosticar_pacote_revisao_zika,
)
from sinan_mcp.zika_pdf_review_annotation import registrar_observacao_documental_zika


def init(tmp_path):
    old = tmp_path / "zika-revisao-v0.json"
    criar_pacote_revisao_zika(old)
    return old


def test_add_field_observation_to_new_file_without_modifying_original(tmp_path):
    old = init(tmp_path)
    before = old.read_bytes()
    new = tmp_path / "zika-revisao-v1.json"
    report = registrar_observacao_documental_zika(
        old, new, tipo="campo", campo="nu_idade_n",
        avaliacao="DIVERGENCIA_DOCUMENTAL",
        nota="Exemplo sintetico: revisar na pagina 3 a unidade de idade codificada.",
    )
    assert old.read_bytes() == before
    assert new.is_file()
    assert report["campos_por_declaracao_do_operador"]["PENDENTE"] == 36
    assert report["campos_por_declaracao_do_operador"]["DIVERGENCIA_DOCUMENTAL"] == 1
    assert report["ressalvas_por_declaracao_do_operador"]["PENDENTE"] == 7
    assert report["parecer_independente_autenticado"] is False
    assert report["topicos_cientificos_pendentes"] == 10
    assert report["campos_2024_efetivamente_conferidos"] == 0
    assert report["publicacao_autorizada"] is False
    payload = json.loads(new.read_text(encoding="utf-8"))
    match = [x for x in payload["campos"] if x["campo"] == "nu_idade_n"]
    assert len(match) == 1
    assert match[0]["nota_documental"].startswith("Exemplo sintetico:")
    assert payload["revisao_independente_autenticada"] is False


def test_add_caveat_observation_then_diagnose(tmp_path):
    old = init(tmp_path)
    new = tmp_path / "zika-caveat-v1.json"
    report = registrar_observacao_documental_zika(
        old, new, tipo="ressalva", campo="nduplic_n",
        avaliacao="DIVERGENCIA_IDENTIFICADA",
        nota="Exemplo artificial de observacao documental na pagina 5.",
    )
    assert report["ressalvas_por_declaracao_do_operador"]["PENDENTE"] == 6
    assert report["ressalvas_por_declaracao_do_operador"]["DIVERGENCIA_IDENTIFICADA"] == 1
    again = diagnosticar_pacote_revisao_zika(new)
    assert again == report
    assert again["publicacao_autorizada"] is False


@pytest.mark.parametrize("tipo,campo,status,nota", [
    ("campo", "falso", "PENDENTE", ""),
    ("ressalva", "tp_not", "PENDENTE", ""),
    ("campo", "nu_idade_n", "APROVADO", "nota qualquer"),
    ("ressalva", "nduplic_n", "CONFERIDO_MANUALMENTE", "nota qualquer"),
    ("campo", "nu_idade_n", "CONFERIDO_MANUALMENTE", ""),
    ("campo", "nu_idade_n", "DIVERGENCIA_DOCUMENTAL", " "),
    ("campo", "nu_idade_n", "ILEGIVEL", ""),
    ("ressalva", "nduplic_n", "OBSERVACAO_DOCUMENTADA", ""),
    ("campo", "cs_raca", "CONFERIDO_MANUALMENTE", "x" * 601),
    ("campo", "cs_raca", "CONFERIDO_MANUALMENTE", "valor\rprivado"),
    ("qualquer", "cs_raca", "PENDENTE", ""),
])
def test_rejects_unknown_fields_states_and_unjustified_reviews(
        tmp_path, tipo, campo, status, nota):
    old = init(tmp_path)
    new = tmp_path / "versioned.json"
    with pytest.raises(ValueError):
        registrar_observacao_documental_zika(
            old, new, tipo=tipo, campo=campo, avaliacao=status, nota=nota,
        )
    assert not new.exists()


def test_never_overwrite_or_accept_same_target_or_other_directory(tmp_path):
    old = init(tmp_path)
    target = tmp_path / "v1.json"
    target.write_text("preserve previous notes", encoding="utf-8")
    args = dict(tipo="campo", campo="cs_raca", avaliacao="PENDENTE", nota="")
    with pytest.raises(FileExistsError):
        registrar_observacao_documental_zika(old, target, **args)
    assert target.read_text(encoding="utf-8") == "preserve previous notes"
    with pytest.raises(ValueError):
        registrar_observacao_documental_zika(old, old, **args)
    nested = tmp_path / "another"
    nested.mkdir()
    with pytest.raises(ValueError):
        registrar_observacao_documental_zika(
            old, nested / "v2.json", **args,
        )


def test_cli_accepts_explicit_synthetic_status_and_never_prints_note(tmp_path):
    old = init(tmp_path)
    target = tmp_path / "v1.json"
    note = "NOTA PRIVADA SINTETICA NAO DIVULGAR"
    cmd = [
        sys.executable, "-m", "sinan_mcp",
        "registrar-observacao-revisao-zika",
        "--arquivo", str(old), "--saida", str(target),
        "--tipo", "campo", "--campo", "nduplic_n",
        "--avaliacao", "ILEGIVEL", "--nota", note,
    ]
    proc = subprocess.run(cmd, cwd=tmp_path, capture_output=True,
                          text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    assert "NOVA VERSAO PRIVADA CRIADA" in proc.stdout
    assert "Ilegiveis declarados pelo operador: 1" in proc.stdout
    assert "Parecer independente autenticado: NAO" in proc.stdout
    assert "publicacao autorizada: NAO" in proc.stdout
    assert note not in proc.stdout + proc.stderr
    assert not (tmp_path / "sinan.sqlite3").exists()
    assert not (tmp_path / "ZIKABR24.json.zip").exists()
    assert not (tmp_path / "ZIKABR24.parquet.zip").exists()


def test_cli_cannot_fabricate_approval_or_replace_existing_checklist(tmp_path):
    old = init(tmp_path)
    new = tmp_path / "v1.json"
    proc = subprocess.run([
        sys.executable, "-m", "sinan_mcp",
        "registrar-observacao-revisao-zika",
        "--arquivo", str(old), "--saida", str(new),
        "--tipo", "campo", "--campo", "cs_raca",
        "--avaliacao", "HOMOLOGADO", "--nota", "tentativa invalida",
    ], cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 2
    assert not new.exists()
    assert "OBSERVACAO NAO REGISTRADA" in proc.stderr


def test_even_self_reported_manual_check_cannot_approve(tmp_path):
    old = init(tmp_path)
    new = tmp_path / "v1.json"
    result = registrar_observacao_documental_zika(
        old, new, tipo="campo", campo="cs_sexo",
        avaliacao="CONFERIDO_MANUALMENTE",
        nota="Exemplo artificial de conferencia da pagina 3.",
    )
    assert result["campos_por_declaracao_do_operador"]["CONFERIDO_MANUALMENTE"] == 1
    assert result["parecer_independente_autenticado"] is False
    assert result["assinatura_revisor_verificada"] is False
    assert result["topicos_cientificos_pendentes"] == 10
    assert result["indicadores_homologados"] == 0
    assert result["publicacao_autorizada"] is False
