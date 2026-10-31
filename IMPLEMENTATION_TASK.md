# SINAN MCP — autonomous implementation brief

Upgrade the checked-out SINAN MCP prototype into the most useful and credible open-source tool possible for Brazilian public epidemiological data and multi-LLM MCP integration. Work in small, tested increments. Do not ask for input already available in the repo. Provide an end summary listing exact changed files and exact test results.

## Phase 1 — Proven, easy quickstart (top priority)

- Verify compatibility of the MCP server entrypoint with installed MCP SDK; fix using official current SDK docs as needed.
- Add a single `sinan-mcp demo` command that initializes ONLY an isolated synthetic dataset. Provide output with copy-and-paste next steps, never misleading epidemiological numbers.
- Test MCP tool discovery and one actual tool invocation using an MCP client, in addition to existing unit/REST tests.
- Improve packaging and dependency separation; validate install instructions for Python 3.11+ on Windows/macOS/Linux where CI allows.
- Add good errors (missing optional PySUS dependency, absent imported DB, invalid grouping, unsupported agravo, network errors).

## Phase 2 — Epidemiological and privacy correctness

- Versioned metadata/catalog for datasets and supported fields; source provenance (URL, extraction time, snapshot label, checksum).
- Distinguish file year from notification/diagnosis/closure year; do not synthesize unavailable time series.
- Check TB outcome code dictionaries and formally label indicators as exploratory unless official definitions/denominators are established.
- Restrict supported grouping/filtering fields and bound work/results; investigate small-cell suppression AND differencing attacks. Do not expose individual rows.
- Comprehensive synthetic fixtures for missing/ignored values, privacy suppression, import idempotency, path safety, error cases.

## Phase 3 — Developer experience, open-source trust and visual appeal

- Excellent bilingual (English/pt-BR) README/docs, clean CLI help, working Claude Code/Desktop/Cursor examples, honest compatibility matrix.
- GitHub Actions CI, Ruff, typing checks, PyTest; `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `CITATION.cff`, issue and PR templates, appropriate license.
- Attractive original SVG hero banner + concise architecture diagram, realistic screenshots or terminal capture generated from executing the demo; NO fabricated output or badges.
- Optional static demo/playground for synthetic datasets only; emphasize MCP call, tool arguments, JSON result, chart, and provenance.
- Publish-ready GitHub description and topics; LinkedIn launch copy in Portuguese and English; a reproducible 60-second demo script.

## Acceptance checks

- New user can reproduce a synthetic demo without downloading real health data.
- At least one real MCP tool call is exercised in a test.
- Documentation matches implemented behavior and install methods.
- No secrets or identifiable health information.
- Traceable metrics; scientifically cautious language.
- Report what was tested, untested, and blocked, by file or command.

## Workflow

Start with `git status`, architecture review and tests. Implement Phase 1 fully before adding features from later phases. Don't write planning-only responses. Commit locally in coherent steps if supported and authorized, but don't publish remotely. If blocked on a tool, make an honest report without endless retries.
