"""Fail-closed, local READ-ONLY Render configuration audit for the synthetic MCP.

Only GET requests to Render's official API are used. API keys, environment
values, secret file names/contents and environment-group names are never printed.
Run locally: py -3.11 scripts/audit_render_public_environment.py
Do not put a Render API key in GitHub Actions, issues, chat or repository files.
"""
from __future__ import annotations

import getpass
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_ROOT = "https://api.render.com/v1"
SERVICE_ID = "srv-dbkdt4g8v5cc73f33cfg"
WORKSPACE_ID = "tea-db3km60m7kps73f2vqo0"
SERVICE_NAME = "sinan-mcp-public-preview"
PUBLIC_HOST = SERVICE_NAME + ".onrender.com"
EXPECTED_BUILD = (
    "python -m pip install --require-hashes --no-deps -r requirements-public.lock"
    " && python -m pip install --no-deps -e ."
)
EXPECTED_START = "python -m sinan_mcp.public_server"
APPROVED_KEYS = frozenset({
    "PYTHON_VERSION", "SINAN_PUBLIC_REAL_DATA", "SINAN_PUBLIC_HOST",
    "SINAN_PUBLIC_RATE_PER_MINUTE", "SINAN_PUBLIC_MAX_IN_FLIGHT", "PORT",
    "PYTHONUNBUFFERED",  # benign Python stdout/stderr buffering switch
})


class AuditUnavailable(RuntimeError):
    """Failed verification; never embed URLs, token or upstream response bodies."""


def api_get(path: str, token: str):
    """GET fixed Render API paths only; never echo any response or request headers."""
    if not path.startswith("/") or "://" in path or "\n" in path or "\r" in path:
        raise AuditUnavailable("unexpected API path")
    request = Request(
        API_ROOT + path,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=15) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise AuditUnavailable("API response exceeded safe size limit")
        return json.loads(data)
    except HTTPError as exc:
        # Never echo Render's error body: it might contain sensitive metadata.
        raise AuditUnavailable(f"Render API refused a read request (HTTP {exc.code})") from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise AuditUnavailable("Render API request or response could not be verified") from None


def api_list(path: str, token: str):
    """Read every cursor page; incomplete pagination must NOT produce PASS."""
    result = []
    seen_cursors = set()
    cursor = None
    for _ in range(40):
        query = {"limit": 100}
        if cursor is not None:
            query["cursor"] = cursor
        separator = "&" if "?" in path else "?"
        page = api_get(path + separator + urlencode(query), token)
        if not isinstance(page, list):
            raise AuditUnavailable("Render API returned an unexpected list shape")
        result.extend(page)
        if len(page) < 100:
            return result
        next_cursor = page[-1].get("cursor") if isinstance(page[-1], dict) else None
        if not isinstance(next_cursor, str) or not next_cursor or next_cursor in seen_cursors:
            raise AuditUnavailable("Render API pagination could not be completed")
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    raise AuditUnavailable("Render API pagination limit reached")


def assessment(service: dict, vars_list: list, secret_files: list, env_groups: list):
    """Return only fixed status labels, never external names, keys or values."""
    outcomes: list[tuple[str, str]] = []

    def put(label: str, state: str):
        outcomes.append((label, state))

    details = service.get("serviceDetails") if isinstance(service, dict) else None
    if not isinstance(details, dict):
        raise AuditUnavailable("Render service response has unknown structure")

    identity_ok = (
        service.get("id") == SERVICE_ID
        and service.get("ownerId") == WORKSPACE_ID
        and service.get("name") == SERVICE_NAME
        and service.get("branch") == "main"
        and service.get("repo") == "https://github.com/miscrapha-DELTA-IA/SINAN-MCP"
        and service.get("type") == "web_service"
    )
    put("specific synthetic service identity", "PASS" if identity_ok else "FAIL")
    put(
        "automatic deployment disabled",
        "PASS" if service.get("autoDeploy") == "no"
        and service.get("autoDeployTrigger") == "off" else "FAIL",
    )
    settings = details.get("envSpecificDetails") or {}
    if not isinstance(settings, dict):
        settings = {}
    put(
        "locked build and synthetic start",
        "PASS" if settings.get("buildCommand") == EXPECTED_BUILD
        and settings.get("startCommand") == EXPECTED_START else "FAIL",
    )
    put("dedicated health check", "PASS" if details.get("healthCheckPath") == "/health" else "FAIL")
    put(
        "single free web instance",
        "PASS" if details.get("plan") == "free"
        and details.get("numInstances") == 1 else "REVIEW",
    )
    # notifyOnFail='default' inherits another setting that this audit cannot read.
    notify = service.get("notifyOnFail")
    put(
        "failure notifications destination",
        "FAIL" if notify in ("none", "off", "disabled")
        else "REVIEW",  # Even a non-default override needs delivery verification.
    )

    env: dict[str, str] = {}
    valid_structure = True
    for entry in vars_list:
        item = entry.get("envVar") if isinstance(entry, dict) else None
        if not isinstance(item, dict) or not isinstance(item.get("key"), str) or not isinstance(item.get("value"), str):
            valid_structure = False
            continue
        name = item["key"]
        if name in env:
            valid_structure = False
        env[name] = item["value"]
    put("direct environment API response", "PASS" if valid_structure else "FAIL")
    put("direct environment key allowlist", "PASS" if set(env).issubset(APPROVED_KEYS) else "FAIL")
    # Python processes commonly set this to 1 for immediate log delivery.
    # An unusual value warrants review, not an assertion of data exposure.
    if "PYTHONUNBUFFERED" in env:
        put(
            "Python unbuffered logging option",
            "PASS" if env["PYTHONUNBUFFERED"] == "1" else "REVIEW",
        )
    put(
        "explicit Python 3.11.17 runtime pin",
        "PASS" if env.get("PYTHON_VERSION") == "3.11.17"
        else "REVIEW" if "PYTHON_VERSION" not in env else "FAIL",
    )
    put(
        "real-data opt-in disabled",
        "PASS" if env.get("SINAN_PUBLIC_REAL_DATA", "0") == "0" else "FAIL",
    )
    put(
        "approved public hostname",
        "PASS" if env.get("SINAN_PUBLIC_HOST", PUBLIC_HOST).strip().lower() == PUBLIC_HOST else "FAIL",
    )
    for key, upper, label in (
        ("SINAN_PUBLIC_RATE_PER_MINUTE", 300, "MCP request budget at most 300/min"),
        ("SINAN_PUBLIC_MAX_IN_FLIGHT", 16, "MCP concurrency at most 16"),
    ):
        raw = env.get(key)
        if raw is None:
            put(label, "PASS")  # hard-coded safe default in public_admission.py
        else:
            try:
                n = int(raw)
                put(label, "PASS" if 1 <= n <= upper else "FAIL")
            except ValueError:
                put(label, "FAIL")
    if "PORT" in env:
        try:
            n = int(env["PORT"])
            put("PORT safe range", "PASS" if 1024 <= n <= 65535 else "FAIL")
        except ValueError:
            put("PORT safe range", "FAIL")

    # Render's endpoint includes secret contents; do not inspect or log them.
    put("no direct secret files", "PASS" if not secret_files else "FAIL")

    if not isinstance(env_groups, list):
        raise AuditUnavailable("Render environment group response has unknown structure")
    links = 0
    invalid_groups = False
    for entry in env_groups:
        # Some paginated Render responses may contain {envGroup: ..., cursor: ...}
        # rather than a plain group object. Never interpret an unrecognized
        # shape as evidence that a group is absent.
        if not isinstance(entry, dict):
            invalid_groups = True
            continue
        group = entry.get("envGroup", entry)
        if not isinstance(group, dict):
            invalid_groups = True
            continue
        # Restrict the audit to the workspace explicitly selected by operator.
        # Missing ownerId is not proof of ownership or of safe separation.
        if group.get("ownerId") != WORKSPACE_ID:
            invalid_groups = True
            continue
        service_links = group.get("serviceLinks")
        if not isinstance(service_links, list):
            invalid_groups = True
            continue
        for link in service_links:
            if not isinstance(link, dict) or not isinstance(link.get("id"), str):
                invalid_groups = True
                continue
            if link["id"] == SERVICE_ID:
                links += 1
    put(
        "environment group membership metadata",
        "REVIEW" if invalid_groups else "PASS",
    )
    # Actual membership is a blocker. Unexpected metadata must not be
    # interpreted as proof of membership or proof of its absence.
    put(
        "no linked environment groups",
        "FAIL" if links else "REVIEW" if invalid_groups else "PASS",
    )

    # Source and runtime code isolation, Render email delivery, workspace log
    # retention and edge rate limiting require separate verification.
    put("logs retention and delivery verified", "REVIEW")
    put("provider abuse controls and alert thresholds verified", "REVIEW")
    return outcomes


def main() -> int:
    token = os.environ.get("RENDER_API_KEY", "").strip()
    if not token:
        try:
            token = getpass.getpass("Render API key (hidden; never paste in chat): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("AUDIT INCOMPLETE: no local credential provided")
            return 2
    if not token:
        print("AUDIT INCOMPLETE: no local credential provided")
        return 2

    try:
        service = api_get(f"/services/{SERVICE_ID}", token)
        env = api_list(f"/services/{SERVICE_ID}/env-vars", token)
        files = api_list(f"/services/{SERVICE_ID}/secret-files", token)
        groups = api_list(f"/env-groups?ownerId={WORKSPACE_ID}", token)
        outcome = assessment(service, env, files, groups)
    except AuditUnavailable as exc:
        print("AUDIT INCOMPLETE:", str(exc))
        return 2
    finally:
        token = ""  # Best-effort disposal of local reference.

    print("READ-ONLY RENDER AUDIT: no API writes, no environment values reported")
    for name, status in outcome:
        print(f"{status}: {name}")
    failures = sum(status == "FAIL" for _, status in outcome)
    review = sum(status == "REVIEW" for _, status in outcome)
    print(f"SUMMARY: {failures} FAILED, {review} MANUAL REVIEW; not a production privacy certification")
    return 1 if failures else 2 if review else 0


if __name__ == "__main__":
    raise SystemExit(main())
