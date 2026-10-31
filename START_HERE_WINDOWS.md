# Windows quick handoff to Claude Code

1. Extract this ZIP. Open PowerShell **inside** the `sinan-mcp` folder (where `pyproject.toml` and `CLAUDE.md` exist).
2. Verify current location with `Get-ChildItem`.
3. Run the following (Python 3.11+ required):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest -q
```

4. Install Claude Code if needed; see https://github.com/anthropics/claude-code . For native Windows, the official installer command (review security policy before executing downloaded installer) is:

```powershell
irm https://claude.ai/install.ps1 | iex
```

5. From this SAME `sinan-mcp` directory, launch:

```powershell
claude
```

6. Paste:

> Read CLAUDE.md and IMPLEMENTATION_TASK.md. Work only on files in this repository. Run the tests and implement Phase 1 now, including a real MCP client invocation. Do not use conversation attachments or stall in workspace-boot retries. Then proceed through remaining phases in tested increments, report real changes and actual command outputs.

If your gateway supplies only model inference but doesn't provide Claude Code with working filesystem and shell tools, switch to a working local Claude Code runtime or connected repository execution environment. A stronger model prompt cannot compensate for a missing workspace.
