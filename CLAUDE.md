# Development standards for code assistants

This file defines repository engineering constraints for automated code contributors. It is **not user documentation**. Human-facing product and research documentation is indexed in [docs/README.md](docs/README.md).

## Scope and verification

- Work from the current checked-out repository and the version declared in `pyproject.toml`. Do not rely on historical prompts or obsolete implementation briefs.
- Inspect relevant code, tests and documentation before modifying behavior.
- Use focused commits and report commands executed, tests passed or failed, and remaining limitations without implying unverified success.
- Validate changes with `python -m pytest -q` and applicable documentary contract checks. Use Python 3.11+.
- Preserve public MCP compatibility and keep deployment changes separate from documentation changes.

## Non-negotiable research and data controls

- Do not commit patient records, confidential datasets, credentials, quasi-identifying examples or real clinical test fixtures.
- The public MCP remains read-only and synthetic-only; no arbitrary SQL, row-level output, hidden ingestion or real patient statistics.
- Scientific evidence requires source/version provenance, temporal interpretation, exact denominators and review of privacy risks.
- SHA-256 verification and field-token occurrence do not prove an official 2024 dataset schema, epidemiological validity or independent approval.
- Keep reviews and release gates pending unless substantiated by authentic human decisions and the applicable legal/technical approvals.
- Do not publish, deploy, enable sensitive-data paths or modify external services without explicit operator authorization.

## Documentation convention

- Address readers, reviewers and developers in neutral, concise language. Avoid chat transcripts, paste-ready model instructions, speculative promises, unverified endorsements and conversational assistant phrasing in public documentation.
- Maintain consistent terminology between [README.md](README.md), [docs/pt-BR.md](docs/pt-BR.md), [documentation index](docs/README.md), [review protocol](docs/instruments-2024/REVIEW_PROTOCOL.md) and the software's actual contract.
- Document any newly verified source with a reproducible provenance record and an explicit description of what has **not** been verified.
