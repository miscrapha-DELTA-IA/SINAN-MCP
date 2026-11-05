"""Offline tests of the Render config audit. Never contact Render or use keys."""
from __future__ import annotations

import json

from scripts import audit_render_public_environment as audit


def clean_service():
    return {
        "id": audit.SERVICE_ID, "ownerId": audit.WORKSPACE_ID,
        "name": audit.SERVICE_NAME, "branch": "main",
        "repo": "https://github.com/miscrapha-DELTA-IA/SINAN-MCP",
        "type": "web_service", "autoDeploy": "no", "autoDeployTrigger": "off",
        "notifyOnFail": "default",
        "serviceDetails": {
            "plan": "free", "numInstances": 1, "healthCheckPath": "/health",
            "envSpecificDetails": {
                "buildCommand": audit.EXPECTED_BUILD,
                "startCommand": audit.EXPECTED_START,
            },
        },
    }


def direct_env(**overrides):
    values = {
        "PYTHON_VERSION": "3.11.17",
        "SINAN_PUBLIC_REAL_DATA": "0",
        "SINAN_PUBLIC_HOST": audit.PUBLIC_HOST,
    }
    values.update(overrides)
    return [{"envVar": {"key": key, "value": value}, "cursor": str(i)}
            for i, (key, value) in enumerate(values.items())]


def result_map(service=None, variables=None, secret_files=None, groups=None):
    return dict(audit.assessment(
        clean_service() if service is None else service,
        direct_env() if variables is None else variables,
        [] if secret_files is None else secret_files,
        [] if groups is None else groups,
    ))


def test_synthetic_service_config_passes_technical_gates_but_not_unverified_controls():
    status = result_map()
    assert status["specific synthetic service identity"] == "PASS"
    assert status["direct environment key allowlist"] == "PASS"
    assert status["environment group membership metadata"] == "PASS"
    assert status["no direct secret files"] == "PASS"
    assert status["no linked environment groups"] == "PASS"
    assert status["logs retention and delivery verified"] == "REVIEW"
    assert status["failure notifications destination"] == "REVIEW"


def test_disallowed_direct_environment_does_not_print_name_or_value(capsys):
    private_key = "SECRET_DATABASE_DSN"
    private_value = "PRIVATE_CREDENTIAL_NEVER_LOG_THIS"
    status = result_map(variables=direct_env(**{private_key: private_value}))
    print(status)
    printed = capsys.readouterr().out
    assert status["direct environment key allowlist"] == "FAIL"
    assert private_key not in printed
    assert private_value not in printed


def test_real_data_flag_and_wrong_python_pin_fail_closed():
    result = result_map(variables=direct_env(SINAN_PUBLIC_REAL_DATA="1", PYTHON_VERSION="3.14.0"))
    assert result["real-data opt-in disabled"] == "FAIL"
    assert result["explicit Python 3.11.17 runtime pin"] == "FAIL"


def test_secret_files_and_linked_groups_are_blockers_without_reading_content():
    result = result_map(
        secret_files=[{"secretFile": {"name": "private.pem", "content": "SECRET"}}],
        groups=[{"ownerId": audit.WORKSPACE_ID, "serviceLinks": [{"id": audit.SERVICE_ID}], "name": "private-group"}],
    )
    assert result["no direct secret files"] == "FAIL"
    assert result["no linked environment groups"] == "FAIL"


def test_unlinked_groups_do_not_fail_the_service_but_link_shape_is_checked():
    result = result_map(groups=[{"ownerId": audit.WORKSPACE_ID, "serviceLinks": [{"id": "srv-other"}]}])
    assert result["no linked environment groups"] == "PASS"
    assert result_map(groups=[{}])["environment group membership metadata"] == "REVIEW"
    assert result_map(groups=[{}])["no linked environment groups"] == "REVIEW"


def test_rate_concurrency_and_public_host_fail_on_invalid_values():
    result = result_map(variables=direct_env(
        SINAN_PUBLIC_RATE_PER_MINUTE="12000", SINAN_PUBLIC_MAX_IN_FLIGHT="128",
        SINAN_PUBLIC_HOST="other.example.com",
    ))
    assert result["MCP request budget at most 300/min"] == "FAIL"
    assert result["MCP concurrency at most 16"] == "FAIL"
    assert result["approved public hostname"] == "FAIL"


def test_pagination_fail_closed_when_cursor_missing(monkeypatch):
    monkeypatch.setattr(audit, "api_get", lambda path, token: [
        {"envVar": {"key": "PYTHON_VERSION", "value": "3.11.17"}} for _ in range(100)
    ])
    try:
        audit.api_list("/services/id/env-vars", "never-output")
    except audit.AuditUnavailable as exc:
        assert "pagination" in str(exc)
    else:
        raise AssertionError("Missing cursor should not silently pass")


def test_pythonunbuffered_is_a_known_benign_logging_option():
    status = result_map(variables=direct_env(PYTHONUNBUFFERED="1"))
    assert status["direct environment key allowlist"] == "PASS"
    assert status["Python unbuffered logging option"] == "PASS"
    assert status["no linked environment groups"] == "PASS"


def test_nonstandard_pythonunbuffered_value_needs_review_not_secret_logging(capsys):
    status = result_map(variables=direct_env(PYTHONUNBUFFERED="PRIVATE_VALUE_NOT_TO_ECHO"))
    print(status)
    assert status["direct environment key allowlist"] == "PASS"
    assert status["Python unbuffered logging option"] == "REVIEW"
    assert "PRIVATE_VALUE_NOT_TO_ECHO" not in capsys.readouterr().out


def test_genuine_linked_group_is_fail_not_ambiguous_review():
    linked = [{"ownerId": audit.WORKSPACE_ID, "serviceLinks": [{"id": audit.SERVICE_ID}], "name": "never-print"}]
    status = result_map(groups=linked)
    assert status["environment group membership metadata"] == "PASS"
    assert status["no linked environment groups"] == "FAIL"


def test_render_paginated_env_group_wrapper_is_normalized_before_membership():
    safe_group = {"id": "evg-other", "ownerId": audit.WORKSPACE_ID,
                  "serviceLinks": [{"id": "srv-other"}], "name": "DO_NOT_PRINT"}
    wrapped = [{"envGroup": safe_group, "cursor": "c-1"}]
    status = result_map(groups=wrapped)
    assert status["environment group membership metadata"] == "PASS"
    assert status["no linked environment groups"] == "PASS"


def test_paginated_env_group_wrapper_with_real_link_fails_closed():
    linked = {"ownerId": audit.WORKSPACE_ID,
              "serviceLinks": [{"id": audit.SERVICE_ID}],
              "name": "DO_NOT_PRINT"}
    status = result_map(groups=[{"envGroup": linked, "cursor": "c-1"}])
    assert status["environment group membership metadata"] == "PASS"
    assert status["no linked environment groups"] == "FAIL"


def test_malformed_group_owner_and_nested_link_do_not_cause_false_pass():
    wrong_owner = {"ownerId": "tea-not-the-workspace", "serviceLinks": []}
    missing_owner = {"serviceLinks": []}
    malformed_link = {"ownerId": audit.WORKSPACE_ID,
                      "serviceLinks": [{"wrong_id_key": audit.SERVICE_ID}]}
    bad_wrapped = {"envGroup": []}
    for group in (wrong_owner, missing_owner, malformed_link, bad_wrapped):
        status = result_map(groups=[group])
        assert status["environment group membership metadata"] == "REVIEW"
        assert status["no linked environment groups"] == "REVIEW"


def test_group_review_never_prints_names_or_nested_secrets(capsys):
    malicious = {"ownerId": audit.WORKSPACE_ID,
                 "envVars": [{"key": "PRIVATE_KEY", "value": "SECRET_NEVER_ECHO"}],
                 "name": "PERSONAL_GROUP_NEVER_ECHO"}
    status = result_map(groups=[{"envGroup": malicious}])
    print(status)
    output = capsys.readouterr().out
    assert status["no linked environment groups"] == "REVIEW"
    assert "SECRET_NEVER_ECHO" not in output
    assert "PERSONAL_GROUP_NEVER_ECHO" not in output
