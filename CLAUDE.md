# SINAN MCP — Claude Code repository instructions

## Work from the checked-out files, not from chat attachments

The entire source tree for SINAN MCP v0.1.0 is in this repository. Do not request a ZIP attachment, quote stale chat analysis as source code, or depend on previous session history. Read `README.md`, `pyproject.toml`, `sinan_mcp/`, `tests/` and `IMPLEMENTATION_TASK.md`.

## Mission

Evolve the existing open-source SINAN epidemiological MCP server into a trustworthy, developer-friendly, reproducible open-source package. Do real code changes and verify them; do not replace implementation with only plans. Preserve current working functions. Prioritize safety and scientific validity above marketing.

## Initial verification

1. Inspect repo contents, Python and installed dependencies.
2. Run `python -m pytest -q` from the project root if pytest is installed; if missing, install project dev dependencies in an isolated environment where allowed.
3. Record test outcomes (do not invent success for missing MCP SDK or network tests).
4. Inspect and audit code before editing.
5. Follow priorities and quality gates in `IMPLEMENTATION_TASK.md`.

## Coding policies

- No actual identifiable health records, real data fixtures or secret credentials in version control.
- Keep all research examples explicitly synthetic.
- Do not expose row-level queries or SQL to LLMs.
- Preserve small-cell protection; assess differencing risks.
- Do not label exploratory TB abandonment metrics 'official'.
- Preserve local-only defaults until a remote security model exists.
- Attribute source, imported snapshot, time-period interpretation and limitations in responses.
- Prefer typed structured output, minimal dependencies, tests and reproducible demo.
- Use official PySUS/SINAN dictionaries to confirm category mappings when online.
- Don't claim end-to-end compatibility without running it.
- Never publish to GitHub, PyPI or deploy services without explicit user approval.

## If tools or workspace malfunction

Run ONE quick, deterministic shell/tool probe, report its exact error, then stop that execution path. Do not repeatedly claim 'workspace is booting' or fabricate inspected files. Ask for a locally mounted repository or functional shell, not a re-upload into the same broken gateway.
