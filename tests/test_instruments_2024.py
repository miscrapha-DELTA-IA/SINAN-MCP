"""Regression checks for the public-document-only ZIKA/TB scientific review gate."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from urllib.error import HTTPError

import pytest

from scripts import audit_instruments_2024 as audit


def test_locked_official_document_inventory_and_year_scope():
    manifest, items = audit.inspect_manifest()
    assert manifest["scope"] == "ONLY_PUBLIC_OFFICIAL_PDF_DOCUMENTATION_NO_REAL_RECORDS"
    assert len(items) == 7
    assert {x["id"] for x in items} == set(audit.EXPECTED_DOCUMENTS)
    assert {x["agravo"] for x in items} == {"ZIKA", "TUBE", "COMMON"}
    assert all(x["field_crosswalk_to_2024_data"] == "NOT_VERIFIED" for x in items)
    assert all(x["independent_review"]["decision"] == "PENDING" for x in items)
    assert all(x["byte_integrity"]["verified"] is True for x in items)
    assert all(len(x["byte_integrity"]["sha256"]) == 64
               and x["byte_integrity"]["bytes"] > 100
               and x["byte_integrity"]["provenance_run"].endswith("41994351476")
               for x in items)


def test_matrix_full_zika_selected_tb_and_not_validated_for_actual_2024_schema():
    rows = audit.inspect_matrix()
    assert rows == {
        "fields":57, "zika":37, "tb_selected":15, "common_selected":5,
        "verified_against_2024_dataset":False,
    }


def test_default_check_never_opens_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("network call was not authorized")
    monkeypatch.setattr(audit, "build_opener", forbidden)
    outcome = audit.audit(False, None)
    assert outcome["results"] == []
    assert outcome["sensitive_records_accessed"] is False
    assert outcome["all_sources_byte_verified"] is False
    assert outcome["independent_review_completed"] is False


def test_rejects_pdf_link_swapped_to_a_data_zip(monkeypatch, tmp_path):
    manifest = json.loads(audit.MANIFEST.read_text(encoding="utf-8"))
    manifest["files"][0]["source_url"] = (
        "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/json/ZIKABR24.json.zip"
    )
    changed = tmp_path / "replaced.json"
    changed.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(audit, "MANIFEST", changed)
    with pytest.raises(audit.AuditError, match="URI differs"):
        audit.inspect_manifest()


def test_rejects_premature_human_approval(monkeypatch, tmp_path):
    manifest = json.loads(audit.MANIFEST.read_text(encoding="utf-8"))
    manifest["files"][0]["independent_review"]["decision"] = "APPROVED"
    changed = tmp_path / "reviewed.json"
    changed.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(audit, "MANIFEST", changed)
    with pytest.raises(audit.AuditError, match="remain pending"):
        audit.inspect_manifest()


def test_rejects_unsupported_byte_hash_claim(monkeypatch, tmp_path):
    manifest = json.loads(audit.MANIFEST.read_text(encoding="utf-8"))
    manifest["files"][0]["byte_integrity"]["sha256"] = "BAD"
    changed = tmp_path / "unverified.json"
    changed.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(audit, "MANIFEST", changed)
    with pytest.raises(audit.AuditError, match="valid SHA-256"):
        audit.inspect_manifest()


def test_pdf_fetch_rejects_truncated_and_non_pdf(monkeypatch):
    document = audit.inspect_manifest()[1][0]
    class Response:
        status = 200
        headers = {"Content-Type":"application/pdf"}
        def __init__(self, body):
            self.body = body
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def geturl(self):return document["source_url"]
        def read(self,n):return self.body
    class Opener:
        def __init__(self, body):self.body=body
        def open(self, req, timeout):return Response(self.body)
    with pytest.raises(audit.AuditError, match="not a PDF"):
        audit.fetch_one(document, Opener(b"not pdf bytes" * 20))
    with pytest.raises(audit.AuditError, match="EOF marker"):
        audit.fetch_one(document, Opener(b"%PDF-1.7\n" + b"zeros" * 30))
