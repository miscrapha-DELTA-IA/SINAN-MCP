#!/usr/bin/env python3
"""Auditoria estrita, sem microdados, de fontes PDF institucionais (ZIKA/TB).

Execução padrão: offline; --fetch permite SOMENTE sete URLs de PDF fixadas no
manifesto, em hosts e caminhos exatos, e grava exclusivamente hashes/contagens
de páginas. O usuário não fornece URL nem caminho arbitrário. Os documentos
brutos são removidos depois da inspeção, jamais publicados no repo ou CI.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs" / "instruments-2024"
MANIFEST = DIR / "source_manifest.json"
MATRIX = DIR / "field_matrix.csv"
EXPECTED_PDF_HOSTS = {
    "s3.sa-east-1.amazonaws.com",
    "portalsinan.saude.gov.br",
}
EXPECTED_DOCUMENTS = {
    "ZIKA-DIC": "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/dic_dados_zika.pdf",
    "ZIKA-FICHA": "https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/Ficha_conclusao_v5.pdf",
    "ZIKA-INSTR": "https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/Ficha_conclusao_v5_instr.pdf",
    "COMMON-NINDIV": "https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/DIC_DADOS_NET_Not_Individual_rev.pdf",
    "TUBE-DIC": "https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_NET_Tuberculose_23_07_2020.pdf",
    "TUBE-FICHA": "https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/Tuberculose_v5.pdf",
    "TUBE-ACOMP": "https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/Tuberculose_Acomp_v5.pdf",
}
MAX_PDF_BYTES = 12 * 1024 * 1024


class AuditError(ValueError):
    """Qualquer divergência de fonte/arquivo bloqueia homologação."""


class RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise AuditError("Redirecionamento proibido para impedir acesso a arquivo diferente")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AuditError(message)


def inspect_manifest() -> tuple[dict, list[dict]]:
    j = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(j.get("schema_version") == "sinan-document-check-v1", "Schema documental inesperado")
    require(j.get("scope") == "ONLY_PUBLIC_OFFICIAL_PDF_DOCUMENTATION_NO_REAL_RECORDS",
            "Scope cannot permit real records")
    files = j.get("files")
    require(isinstance(files, list) and len(files) == 7, "Exactly seven official PDFs expected")
    require({doc.get("id") for doc in files} == set(EXPECTED_DOCUMENTS), "Unexpected document IDs")
    for doc in files:
        url = doc["source_url"]
        require(url == EXPECTED_DOCUMENTS[doc["id"]], "PDF URI differs from reviewed official allowlist")
        parsed = urlsplit(url)
        require(parsed.scheme == "https" and parsed.hostname in EXPECTED_PDF_HOSTS
                and not parsed.query and not parsed.fragment and not parsed.username
                and not parsed.password, "Unsafe official source URL")
        require(doc["expected_pages_from_pdf_preview"] >= 1, "Invalid preview page count")
        require(doc["field_crosswalk_to_2024_data"] == "NOT_VERIFIED", "2024 data concordance not reviewed")
        integrity = doc["byte_integrity"]
        # A hash can be recorded after a CI execution; not a source signature.
        if integrity["verified"]:
            require(bool(re.fullmatch(r"[0-9a-f]{64}", integrity["sha256"] or "")),
                    "Verified PDF must have valid SHA-256")
            require(isinstance(integrity["bytes"], int) and 100 < integrity["bytes"] < MAX_PDF_BYTES,
                    "Verified PDF must have bounded byte size")
            require(integrity.get("verified_at"), "Verified PDF requires timestamp")
        else:
            require(integrity["sha256"] is None and integrity["bytes"] is None,
                    "Unknown source bytes must not have a claimed hash")
        review = doc["independent_review"]
        require(review["decision"] == "PENDING" and review["reviewer_id"] is None,
                "Independent review must remain pending until a signed decision")
    return j, files


def inspect_matrix() -> dict:
    with MATRIX.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 57, "Field matrix must contain the 57 curated documentary records")
    require(all(row["ano_alvo"] == "2024" for row in rows), "Unexpected target year")
    require(all(row["status_concordancia_extracao_2024"] == "NOT_VERIFIED"
                and row["status_revisao_independente"] == "PENDING"
                for row in rows), "Field-level concordance/review was asserted prematurely")
    require({row["fonte_id"] for row in rows} <= set(EXPECTED_DOCUMENTS),
            "Matrix references a document not reviewed")
    for disease, required in (("ZIKA", 37), ("TUBE", 15), ("COMMON", 5)):
        entries = [r for r in rows if r["agravo"] == disease]
        require(len(entries) == required, "Unexpected matrix size: " + disease)
        require(len({r["campo_documental"] for r in entries}) == required,
                "Duplicated field code in " + disease)
    zika = [r for r in rows if r["agravo"] == "ZIKA"]
    require({int(r["pagina_pdf"]) for r in zika} == set(range(1, 9)),
            "The 8-page Zika dictionary must be evidenced across each page")
    return {"fields":len(rows), "zika":37, "tb_selected":15, "common_selected":5,
            "verified_against_2024_dataset":False}


def _pdfinfo_pages(path: Path) -> int:
    """Use pypdf==5.9.0, pinned by CI; no Poppler or executables."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise AuditError("Install pinned pypdf==5.9.0 to verify PDF structure") from exc
    try:
        pages = len(PdfReader(str(path), strict=False).pages)
    except Exception as exc:
        raise AuditError("PDF parser rejected downloaded document") from exc
    require(pages > 0, "PDF page count unavailable")
    return pages

def fetch_one(document: dict, opener) -> dict:
    url = document["source_url"]
    req = Request(url, headers={"Accept": "application/pdf", "User-Agent": "SINAN-MCP-Document-Audit/1.0"})
    with opener.open(req, timeout=22) as response:
        final = response.geturl()
        require(final == url, "Source URL redirected to a different location")
        require(response.status == 200, "Official document is not HTTP 200")
        header = response.headers.get("Content-Type", "").lower().split(";")[0].strip()
        require(header in {"application/pdf", "application/octet-stream"},
                "Unexpected PDF MIME type")
        raw = response.read(MAX_PDF_BYTES + 1)
    require(100 < len(raw) <= MAX_PDF_BYTES, "PDF exceeds strict byte bound or is empty")
    require(raw[:5] == b"%PDF-", "Source body is not a PDF")
    require(b"%%EOF" in raw[-2048:], "PDF seems truncated (no EOF marker)")
    # Pinned after an independent GitHub Action fetch, so an upstream change
    # cannot silently replace an accepted source version.
    pinned = document["byte_integrity"]
    computed_sha256 = hashlib.sha256(raw).hexdigest()
    if pinned["verified"]:
        require(len(raw) == pinned["bytes"] and computed_sha256 == pinned["sha256"],
                "Official PDF bytes differ from pinned SHA-256; manual diff and review required")
    with tempfile.TemporaryDirectory(prefix="sinan-pdf-doc-only-") as tmp:
        path = Path(tmp) / "official-document.pdf"
        path.write_bytes(raw)
        pages = _pdfinfo_pages(path)
    require(pages == document["expected_pages_from_pdf_preview"], "Page count changed")
    return {
        "id": document["id"], "url": url, "source_mime": header, "bytes": len(raw),
        "sha256": computed_sha256, "pages": pages,
        "verified_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "method": "official_https_byte_download+pdf_magic+eof+pdfinfo",
        "independent_reviewer_approved": False,
        "validated_for_2024_data_layout": False,
    }


def audit(fetch: bool, output: Path | None) -> dict:
    _manifest, docs = inspect_manifest()
    matrix = inspect_matrix()
    result = {
        "status": "DOCUMENT_STRUCTURE_ONLY_NO_2024_DATASET_CONCORDANCE",
        "matrix": matrix,
        "official_documents": len(docs),
        "all_sources_byte_verified":False,
        "independent_review_completed":False,
        "sensitive_records_accessed":False,
        "results": [],
    }
    if fetch:
        opener = build_opener(RejectRedirect())
        for doc in docs:
            result["results"].append(fetch_one(doc, opener))
        result["all_sources_byte_verified"] = len(result["results"]) == len(docs)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Explicit opt-in for seven fixed public PDFs")
    parser.add_argument("--out", type=Path, default=None, help="Save JSON metadata only, never source bytes")
    args = parser.parse_args()
    result = audit(args.fetch, args.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("GATE: data-2024 schema concordance and independent human review remain PENDING.")


if __name__ == "__main__":
    main()
