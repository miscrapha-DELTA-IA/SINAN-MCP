# Changelog

## 0.3.1-alpha.1 (2026-11-01)

- Windows PySUS empty-catalog incident reproduced in Windows GitHub Actions, unlike Linux.
- Introduced administrator-only `diagnosticar-pysus` and optional isolated `--cache-dir` for discovery/import, preserving existing local caches.
- Catalog-empty failures now provide actionable guidance instead of unhandled tracebacks.
- Extended optional PySUS CI coverage to Windows.
- **Confirmed upstream limitation:** live Windows PySUS catalogue discovery returned zero files even with a brand-new isolated cache; Linux returned public TUBE/DENG filenames.
- Added `importar-parquet` for local Parquet ingestion without PySUS catalogue discovery (synthetic CI coverage on Windows/Linux).
- An isolated cache is diagnostic only, not a proven fix.


## 0.3.0-alpha.1 (2026-11-01)

- PySUS discovery without download, plus streamed Parquet/CSV ingestion and content fingerprint.
- Empty/unexpected-schema imports abort atomically and preserve the previous snapshot.
- Local administrator-only quality diagnostic and pilot catalogue (TUBE/DENG).
- Public methodology tool explaining why the TB abandonment ratio is not official.
- Synthetic PySUS-adapter tests and optional GitHub Actions ingestion-dependency workflow.
- Verified live PySUS file discovery (no microdata download): TUBEBR24.parquet and DENGBR24.parquet via GitHub Actions.
- **Unverified:** complete DATASUS/PySUS network download and official epidemiological indicator equivalence.


## 0.2.0-alpha.1 (2026-11-01)

- Offline synthetic demo on a separate database.
- Provenance envelopes for public numeric MCP/REST responses.
- Restricted public disclosure controls and sanitized public dataset catalog.
- New synthetic security/regression and optional in-memory MCP client tests.
- English/Portuguese documentation, security guidance and GitHub CI.

**Not completed:** live PySUS validation, remote authorization/privacy framework, official epidemiological indicator validation or verification on real desktop MCP clients.
