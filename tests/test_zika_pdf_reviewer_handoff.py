"""Entirely offline tests for the reviewer-facing PUBLIC Zika PDF worksheet."""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from sinan_mcp import zika_pdf_reviewer_handoff as handoff
from sinan_mcp.zika_pdf_37_field_curation import carregar_transcricao_zika_pdf


def test_handoff_contains_all_37_fields_and_page_links():
    markdown = handoff.montar_roteiro_revisor_zika()
    source = carregar_transcricao_zika_pdf()
    assert markdown.startswith("# Roteiro para segunda conferência")
    assert "NÃO É PARECER ASSINADO" in markdown
    assert "Revisão independente autenticada: NÃO" in markdown
    assert "Publicação autorizada: NÃO" in markdown
    assert "Campos reais de ZIKABR24 lidos: 0" in markdown
    assert source["source_pdf"] in markdown
    assert source["local_catalog_sha256_not_official_pdf_hash"] in markdown
    rows = [r for r in markdown.splitlines()
            if re.match(r"^\| ([1-9]|[12][0-9]|3[0-7]) \|", r)]
    assert len(rows) == 37
    for i, row in enumerate(source["documentary_field_rows"]):
        matched = rows[i]
        assert matched.startswith(f"| {i+1} |")
        assert f"`{row['campo']}`" in matched
        assert f"`{row['tipo_documental']}`" in matched
        assert f"#page={row['pagina_pdf']}" in matched
        assert "[ ]" in matched
        assert "[x]" not in matched.lower()
    for issue in source["issues_requiring_independent_review"]:
        assert issue["campo"] in markdown
        assert issue["motivo"] in markdown
    assert markdown.count(" | __________ |") == 44


def test_ambiguous_duplication_is_not_silently_resolved():
    markdown = handoff.montar_roteiro_revisor_zika()
    assert "`nduplic_n`" in markdown
    assert "#page=5" in markdown
    assert "NDUPLIC_N" not in markdown or "deduplicação" in markdown.lower()
    assert "não autentica" in markdown.lower()
    assert "**não** valida" in markdown.lower()


def test_new_markdown_is_public_doc_only_and_never_overwritten(tmp_path):
    out = tmp_path / "revisor-zika.md"
    report = handoff.preparar_roteiro_revisor_zika(out)
    assert out.is_file()
    assert report["campos_publicos_para_conferencia"] == 37
    assert report["ressalvas_publicas_para_conferencia"] == 7
    assert report["notas_privadas_lidas"] is False
    assert report["pdf_baixado_ou_inspecionado_pelo_comando"] is False
    assert report["campos_reais_zikabr24_lidos"] == 0
    assert report["parecer_independente_autenticado"] is False
    assert report["indicadores_homologados"] == 0
    assert report["publicacao_autorizada"] is False
    assert out.read_text(encoding="utf-8") == handoff.montar_roteiro_revisor_zika()
    if os.name != "nt":
        assert out.stat().st_mode & 0o077 == 0
    before = out.read_bytes()
    with pytest.raises(FileExistsError):
        handoff.preparar_roteiro_revisor_zika(out)
    assert out.read_bytes() == before


def test_git_tree_is_disallowed_without_touching_output(tmp_path):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").mkdir()
    inside = checkout / "reviewer.md"
    with pytest.raises(ValueError, match="Git"):
        handoff.preparar_roteiro_revisor_zika(inside)
    assert not inside.exists()
    wrong = tmp_path / "reviewer.json"
    with pytest.raises(ValueError):
        handoff.preparar_roteiro_revisor_zika(wrong)
    assert not wrong.exists()


def test_cli_is_silent_about_private_operator_notes(tmp_path):
    private_note = "NOTA_PRIVADA_DO_OPERADOR_QUE_NAO_DEVE_SAIR"
    # The CLI is given only an output path, not the private JSON or its notes.
    private = tmp_path / "private-operator.json"
    private.write_text(private_note, encoding="utf-8")
    out = tmp_path / "external-review.md"
    args = [sys.executable, "-m", "sinan_mcp",
            "preparar-roteiro-revisor-zika", "--saida", str(out)]
    result = subprocess.run(args, cwd=tmp_path, capture_output=True,
                            text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "Campos documentais para conferir: 37" in result.stdout
    assert "Ressalvas documentais para conferir: 7" in result.stdout
    assert "Notas privadas do operador lidas: NAO" in result.stdout
    assert "Parecer independente autenticado: NAO" in result.stdout
    assert "Campos ZIKABR24 lidos: 0" in result.stdout
    assert private_note not in result.stdout + result.stderr
    assert private_note not in out.read_text(encoding="utf-8")
    assert not (tmp_path / "sinan.sqlite3").exists()
    assert not (tmp_path / "ZIKABR24.json.zip").exists()
    assert not (tmp_path / "ZIKABR24.parquet.zip").exists()


def test_markdown_escape_rejects_controls_and_pipe_injection():
    assert handoff._cell("1 | 2") == r"1 \| 2"
    assert handoff._cell("a[b]") == r"a\[b\]"
    with pytest.raises(ValueError):
        handoff._cell("field\nnew")
    with pytest.raises(ValueError):
        handoff._cell("x" * 501)
