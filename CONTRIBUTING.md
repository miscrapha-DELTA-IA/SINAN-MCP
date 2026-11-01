# Contributing

Contributions are welcome, especially for verified SINAN dictionaries, reproducible indicators and privacy engineering.

1. Use Python 3.11+; install `python -m pip install -e '.[dev]'`.
2. Run `python -m pytest -q` and report passes/skips accurately.
3. Use **synthetic fixtures only**. Never commit datasets with individual-level health information.
4. Include source, date, cohort, denominator and scientific limitations for any new indicator.
5. Keep ingest/admin privileges separate from MCP tools; avoid arbitrary SQL or row outputs.
6. Open a PR with the change rationale, validation and relevant privacy considerations.
