"""Report a failed public synthetic smoke run as a sanitized GitHub issue.

Invoked only from a trusted workflow_run job. No Render credentials, data,
workflow artifacts, user IPs, or logs are read or posted.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO = "miscrapha-DELTA-IA/SINAN-MCP"
WORKFLOW_NAME = "Public HTTPS MCP smoke"
TITLE = "[monitoring] Public synthetic MCP HTTPS probe failed"
API = "https://api.github.com"


def failed_probe(payload: dict, repository: str = REPO) -> dict | None:
    if not isinstance(payload, dict) or payload.get("action") != "completed":
        return None
    run = payload.get("workflow_run")
    source = run.get("repository") if isinstance(run, dict) else None
    dest = payload.get("repository")
    if not all(isinstance(x, dict) for x in (run, source, dest)):
        return None
    if repository != REPO or source.get("full_name") != REPO or dest.get("full_name") != REPO:
        return None
    if (run.get("name") != WORKFLOW_NAME or run.get("head_branch") != "main"
            or run.get("status") != "completed" or run.get("conclusion") != "failure"
            or run.get("event") not in ("schedule", "workflow_dispatch")):
        return None
    run_id, attempt = run.get("id"), run.get("run_attempt")
    if type(run_id) is not int or run_id <= 0:
        return None
    if type(attempt) is not int or not 1 <= attempt <= 10000:
        return None
    return {
        "url": f"https://github.com/{REPO}/actions/runs/{run_id}/attempts/{attempt}",
        "trigger": run["event"],
    }


def api_request(method: str, path: str, token: str, body: dict | None = None):
    prefix = f"/repos/{REPO}/issues"
    if method not in ("GET", "POST") or not path.startswith(prefix):
        raise RuntimeError("unexpected GitHub API request")
    if method == "POST" and not (path == prefix or
            (path.startswith(prefix + "/") and path.endswith("/comments"))):
        raise RuntimeError("refused unrelated GitHub API write")
    req = Request(
        API + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=15) as response:
            raw = response.read(250001)
        if len(raw) > 250000:
            raise RuntimeError("oversized GitHub API response")
        return json.loads(raw)
    except HTTPError as exc:
        raise RuntimeError(f"GitHub API read/write failed: HTTP {exc.code}") from None
    except (URLError, OSError, TimeoutError, ValueError):
        raise RuntimeError("GitHub issue API response not verified") from None


def open_incident(token: str, api=api_request) -> int | None:
    for page in range(1, 21):
        rows = api("GET", f"/repos/{REPO}/issues?state=open&per_page=100&page={page}", token)
        if not isinstance(rows, list):
            raise RuntimeError("unexpected GitHub issue list structure")
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError("unexpected GitHub issue row")
            if row.get("title") == TITLE and "pull_request" not in row:
                n = row.get("number")
                if type(n) is not int or n < 1:
                    raise RuntimeError("unverified GitHub issue number")
                return n
        if len(rows) < 100:
            return None
    raise RuntimeError("unverified issue list pagination")


def report(payload: dict, token: str, repository: str = REPO, api=api_request) -> str:
    info = failed_probe(payload, repository)
    if info is None:
        return "skipped: unrelated or successful workflow"
    if not token:
        raise RuntimeError("ephemeral GitHub token missing")
    message = (
        "A sonda HTTPS do MCP público **exclusivamente sintético** falhou.\n\n"
        f"- Workflow: {info['url']}\n"
        f"- Gatilho: {info['trigger']}\n"
        "- Nenhum dado real foi solicitado pela sonda; a falha não prova vazamento.\n\n"
        "Verificar a execução no GitHub, o status de Render, os logs sanitizados "
        "e o SHA efetivamente implantado. Pode ser cold start, rede ou indisponibilidade.\n\n"
        "**Não efetuar deploy, reinício, rollback ou acesso a bases reais automaticamente.** "
        "Não anexar IPs, tokens, corpos de requisição, logs brutos ou dados clínicos.\n"
    )
    number = open_incident(token, api)
    if number is None:
        api("POST", f"/repos/{REPO}/issues", token, {"title": TITLE, "body": message})
        return "created: sanitized GitHub incident"
    api("POST", f"/repos/{REPO}/issues/{number}/comments", token,
        {"body": "Nova falha registrada automaticamente.\n\n" + message})
    return "updated: existing sanitized GitHub incident"


def main() -> int:
    path = os.environ.get("GITHUB_EVENT_PATH")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not path or repository != REPO:
        raise RuntimeError("only the trusted GitHub workflow can invoke this report")
    event = json.loads(Path(path).read_text(encoding="utf-8"))
    print(report(event, os.environ.get("GH_TOKEN", ""), repository))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
