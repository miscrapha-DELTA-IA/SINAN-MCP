# Changelog

## 0.3.1-alpha.1 (2026-11-01)

- Reproduced PySUS 2.11.7 Windows FileBag-empty problem against real TUBE/DENG metadata catalogue.
- Added **Windows-tested read-only metadata fallback** using PySUS's already-open shared SQLAlchemy/DuckDB engine. Restored discovery of public TUBEBR24 and DENGBR24 names without downloading microdata.
- Added `diagnosticar-pysus` and isolated `--cache-dir` options. Changing cache alone is **not** considered a fix.
- Added direct administrative `importar-parquet` for verified locally obtained public files, bypassing PySUS's problematic Windows remote ingest.
- Verified synthetic import tests and real remote metadata discovery through Linux and Windows GitHub Actions.
- **Not yet validated:** direct PySUS remote download/import on Windows, and clinical/official indicator equivalence.

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
