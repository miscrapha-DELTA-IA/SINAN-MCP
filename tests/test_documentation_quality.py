"""Repository documentation navigation and evidence-status regression checks."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

# External links are outside the scope of this offline test.
MARKDOWN_LINK = re.compile(r"(?<!!)[\[][^\]]+[\]]\(([^)\s]+)(?:\s+[^)]*)?\)")
HTML_LINK = re.compile(r'href=["\']([^"\']+)["\']')
FENCED_BLOCK = re.compile(r"```[\s\S]*?```", re.MULTILINE)
CHECKBOX = re.compile(r"^\s*[-*]\s+\[[ xX]\]", re.MULTILINE)


def published_pages() -> list[Path]:
    return sorted(set((ROOT / "README.md", ROOT / "SECURITY.md", ROOT / "CONTRIBUTING.md"))
                  | set(DOCS.rglob("*.md")))


def test_all_public_markdown_references_have_a_local_destination() -> None:
    for page in published_pages():
        text = FENCED_BLOCK.sub("", page.read_text(encoding="utf-8"))
        hrefs = MARKDOWN_LINK.findall(text) + HTML_LINK.findall(text)
        for link in hrefs:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or link.startswith(("#", "/")):
                continue
            relative = unquote(parts.path)
            if not relative:
                continue
            destination = (page.parent / relative).resolve()
            assert destination.is_relative_to(ROOT), (page, link)
            assert destination.exists(), f"{page.relative_to(ROOT)}: broken link {link}"


def test_documentation_information_architecture() -> None:
    for dirname in ("research", "operations", "compliance"):
        assert (DOCS / dirname / "README.md").is_file()
    for removed in (
        ROOT / "CLAUDE.md",
        ROOT / "IMPLEMENTATION_TASK.md",
        ROOT / "START_HERE_WINDOWS.md",
        DOCS / "GITHUB_ABOUT.md",
        DOCS / "TECHNICAL_README_ARCHIVE.md",
    ):
        assert not removed.exists(), removed
    assert sorted(x.name for x in DOCS.glob("*.md")) == [
        "LOCAL_SETUP.md", "QUICKSTART_PUBLICO.md", "README.md", "pt-BR.md",
    ]


def test_scientific_documents_do_not_resemble_chat_tasks() -> None:
    pages = [
        ROOT / "README.md",
        DOCS / "README.md",
        DOCS / "pt-BR.md",
        DOCS / "instruments-2024/REVIEW_PROTOCOL.md",
    ]
    for page in pages:
        text = page.read_text(encoding="utf-8")
        assert CHECKBOX.search(text) is None, page
        assert "Cole este prompt" not in text
        assert "Paste this into ChatGPT" not in text
        assert "## Critérios objetivos para a etapa seguinte" not in text


def test_scientific_gate_remains_closed() -> None:
    protocol = (DOCS / "instruments-2024/REVIEW_PROTOCOL.md").read_text(encoding="utf-8")
    review = (DOCS / "instruments-2024/EXTERNAL_REVIEW.md").read_text(encoding="utf-8")
    assert "57/57" in protocol and "7/7" in protocol
    assert "Não verificada" in protocol
    assert "Pendentes" in protocol
    assert "Não autorizado" in protocol
    assert "não substitui um parecer científico independente" in protocol
    assert "issues/62" in protocol
    for term in ("cs_gestant", "SITUA_ENCE", "TRATAMENTO", "Modalidade", "conflitos"):
        assert term.casefold() in review.casefold()
    assert "dados fictícios" in review
