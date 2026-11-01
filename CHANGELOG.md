# Changelog

## 0.3.0-alpha.3 (2026-11-01)

- Public MCP/REST numeric queries now open the SQLite database **read-only** and refuse to initialize missing databases.
- **Breaking privacy safeguard:** imported real datasets are blocked from public numeric tools unless an administrator explicitly sets `SINAN_PUBLIC_REAL_DATA=1` on the server process. The synthetic demo needs no opt-in.
- **Conservative complementary disclosure guard:** if any sex/race category or TB case/control subcell is too small, numeric tools deny the complete UF/file-year partition across dimensions; no suppressed residuals or category names are returned. A minimum partition size of 100 applies. This is not differential privacy or a formal anonymization guarantee.
- Added `auditar-equidade`: **local administrator-only** assessment of held-out prediction CSVs (AUROC, AP, Brier, ECE, TPR/FPR, SPD/EOD/AAOD, optional IID bootstrap). No model training, clinical risk prediction, patient data exchange, or MCP exposure.
- Added privacy and reproducibility regression tests, ChatGPT Tunnel instructions, and research protocol. Experimental deployment still requires independent security and epidemiological review.


## 0.3.0-alpha.2 (2026-11-01)

- Added administrator-only metadata import preview for public FTP-mirror Parquet snapshots.
- Added conservative Windows fallback when the PySUS FileBag is empty: validated DuckLake catalog manifest, fixed-host HTTPS transfer with size/optional SHA256 checking, streamed SQLite projection and temporary raw-file cleanup.
- No hidden source substitution: origin import still requires a working origin FileBag. No real clinical data downloaded during CI.
- **Still pending:** Windows end-to-end real-file download validation and year-specific epidemiological dictionary validation.


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
