"""Offline incident workflow tests: never contact GitHub or Render."""
from scripts import report_public_smoke_failure as subject


def payload(trigger="schedule", conclusion="failure", branch="main"):
    return {
        "action": "completed",
        "repository": {"full_name": subject.REPO},
        "workflow_run": {
            "name": subject.WORKFLOW_NAME,
            "repository": {"full_name": subject.REPO},
            "head_branch": branch, "event": trigger,
            "id": 12345, "run_attempt": 2,
            "status": "completed", "conclusion": conclusion,
            "html_url": "https://attacker.invalid/never-echo",
        },
    }


def test_identifies_only_failed_main_synthetic_probes():
    result = subject.failed_probe(payload())
    assert result["url"] == f"https://github.com/{subject.REPO}/actions/runs/12345/attempts/2"
    assert subject.failed_probe(payload(trigger="workflow_dispatch"))
    for event in ("pull_request", "push", "repository_dispatch"):
        assert subject.failed_probe(payload(trigger=event)) is None
    for status in ("success", "cancelled", "neutral"):
        assert subject.failed_probe(payload(conclusion=status)) is None
    assert subject.failed_probe(payload(branch="other")) is None


def test_rejects_spoofed_repository_identity_or_bad_ids():
    for field, value in (("id", True), ("id", -5), ("run_attempt", "2")):
        event = payload()
        event["workflow_run"][field] = value
        assert subject.failed_probe(event) is None
    event = payload()
    event["workflow_run"]["repository"]["full_name"] = "someone/else"
    assert subject.failed_probe(event) is None
    event = payload()
    event["repository"]["full_name"] = "someone/else"
    assert subject.failed_probe(event) is None


def test_first_failure_opens_sanitized_issue_without_event_url_or_token():
    calls = []
    def fake_api(method, path, token, body=None):
        calls.append((method, path, body))
        return [] if method == "GET" else {"number": 88}
    assert subject.report(payload(), "DO_NOT_PRINT_TOKEN", api=fake_api).startswith("created")
    posts = [c for c in calls if c[0] == "POST"]
    assert len(posts) == 1
    assert posts[0][1] == f"/repos/{subject.REPO}/issues"
    assert posts[0][2]["title"] == subject.TITLE
    serialized = str(posts)
    assert "attacker.invalid" not in serialized
    assert "DO_NOT_PRINT_TOKEN" not in serialized
    assert "/attempts/2" in serialized


def test_repeated_failure_comments_instead_of_creating_duplicate_issue():
    calls = []
    def fake_api(method, path, token, body=None):
        calls.append((method, path, body))
        return [{"title": subject.TITLE, "number": 43}] if method == "GET" else {"id": 10}
    assert subject.report(payload(), "TOKEN", api=fake_api).startswith("updated")
    assert calls[-1][1] == f"/repos/{subject.REPO}/issues/43/comments"


def test_non_failure_or_unknown_issue_list_never_causes_write():
    def forbid(*args, **kwargs):
        raise AssertionError("unexpected remote API call")
    assert subject.report(payload(conclusion="success"), "", api=forbid).startswith("skipped")
    def full_page(*args, **kwargs):
        return [{"title": "different issue"}] * 100
    try:
        subject.open_incident("TOKEN", api=full_page)
    except RuntimeError as exc:
        assert "pagination" in str(exc)
    else:
        raise AssertionError("incomplete pagination must fail closed")


def test_api_refuses_unrelated_write_before_any_network():
    try:
        subject.api_request("POST", f"/repos/{subject.REPO}/actions/runs", "TOKEN", {})
    except RuntimeError as exc:
        assert "unexpected" in str(exc)
    else:
        raise AssertionError("unrelated GitHub API writes must be refused")
