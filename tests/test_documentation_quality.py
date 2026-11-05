"""Offline checks for user-facing repository documentation."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PAGES = [
    ROOT / "README.md",
    ROOT / "docs" / "README.md",
    ROOT / "docs" / "pt-BR.md",
    ROOT / "docs" / "LOCAL_SETUP.md",
    ROOT / "docs" / "DOCUMENTARY_CATALOG_V1.md",
    ROOT / "docs" / "instruments-2024" / "REVIEW_PROTOCOL.md",
    ROOT / "docs" / "instruments-2024" / "EXTERNAL_REVIEW.md",
]

LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+[^)]*)?\)")
BLOCK = re.compile(r"```[\s\S]*?```", re.MULTILINE)


def test_public_documentation_has_reproducible_local_links() -> None:
    for page in PUBLIC_PAGES:
        assert page.is_file(), page
        text = BLOCK.sub("", page.read_text(encoding="utf-8"))
        for target in LINK.findall(text):
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith(("#", "/")):
                continue
            relative = unquote(parsed.path)
            if not relative:
                continue
            resolved = (page.parent / relative).resolve()
            assert resolved.is_relative_to(ROOT), (page, target)
            assert resolved.exists(), f"{page.relative_to(ROOT)}: broken link {target}"


def test_no_legacy_chat_handoff_in_public_paths() -> None:
    for filename in ("IMPLEMENTATION_TASK.md", "START_HERE_WINDOWS.md"):
        assert not (ROOT / filename).exists(), filename
    assert not (ROOT / "docs" / "GITHUB_ABOUT.md").exists()

    forbidden = [
        "paste the following prompt",
        "cole este prompt",
        "resposta do chatgpt",
        "como assistente de ia,",
        "vou realizar agora",
        "do not ask for input already available",
    ]
    for page in PUBLIC_PAGES:
        text = page.read_text(encoding="utf-8").casefold()
        for phrase in forbidden:
            assert phrase not in text, (page, phrase)


def test_review_pages_distinguish_machine_evidence_from_human_approval() -> None:
    protocol = (ROOT / "docs/instruments-2024/REVIEW_PROTOCOL.md").read_text(encoding="utf-8")
    review = (ROOT / "docs/instruments-2024/EXTERNAL_REVIEW.md").read_text(encoding="utf-8")
    assert "57/57" in protocol and "7/7" in protocol
    assert "Não verificada" in protocol
    assert "Pendentes" in protocol
    assert "Não autorizado" in protocol
    assert "não substitui um parecer científico independente" in protocol
    for term in ("cs_gestant", "SITUA_ENCE", "TRATAMENTO", "Modalidade", "conflitos"):
        assert term.casefold() in review.casefold()
    assert "dados fictícios" in review
    assert "não" in review and "2024" in review
