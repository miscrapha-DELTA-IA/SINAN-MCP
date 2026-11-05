# Changelog

## 0.4.0-alpha.6 (2026-11-05): evidence-locked Zika/TB documentary instruments

- Indexed seven official source PDFs with source-specific URLs, page counts, byte sizes and locked SHA-256 hashes.
- Located 57 field-code occurrences on the cited PDF pages (37 Zika, 15 selected TB and five common fields). These are text-presence tests, **not scientific validation of labels or a 2024 data export**.
- Published the public, read-only documentary snapshot through existing ZIKA/TUBE description tools, without patient records or new numerical endpoints.
- Kept independent epidemiology, information-system, privacy, release concordance and legal gates **pending**. Public service uses only fictional numerical fixtures.

## Documentation maintenance (2026-11-05)

- Added a reader-first documentation index, external-review guide and neutral local setup instructions.
- Removed obsolete agent-handoff briefs and non-operational GitHub About advice from publicly browsable root/documentation paths.
- Aligned public overviews and catalogue status with the verified evidence and the pending review gate.
- Documentation restructuring does not alter MCP runtime behavior, data permissions or scientific approvals.

## 0.4.0-alpha.5 (2026-11-05): source-aware catalogue

- Added curated institutional-source references across 14 condition themes with 17 distinct institutional page URLs.
- Added explicit provenance, dated curation, scope disclaimers and typo suggestions without remote fetching inside MCP calls.
- No automatic acceptance of reference pages as epidemiological datasets.


## 0.4.0-alpha.4 (2026-11-02): multi-agravo reference and official-source catalogue

- Created a static catalogue of **14 internal disease/notification aliases** and four curated official navigation sources for SINAN/DATASUS, clearly differentiated from valid datasets or statistics.
- Added three public read-only MCP tools: `pesquisar_agravos`, `descrever_agravo`, `listar_fontes_oficiais`, supporting Unicode/diacritic-insensitive searches and explicit availability flags.
- Kept all public numerical tools **synthetic-only TB demonstration**; no SQLite, individual records, dynamic remote downloading, live case counts or public health outcome statistics.
- Added local `preparar-tabela-oficial` intake for explicitly declared, pre-aggregated TABNET tables across disease codes. It requires source URL, extraction timestamp, declared export SHA-256, filters, year semantics, dimension and bounded cells, then produces only a PRIVATE UNAPPROVED candidate. It does not verify authenticity or approval.
- Documented non-exhaustive scope, internal alias caveats and per-agravo validation milestones; added safety and HTTP smoke regression tests.
- Does not automatically deploy changes to Render. Public deployment remains independently controlled.



## 0.4.0-alpha.3 (2026-11-02): cache-independent PySUS regression tests

- Fixed three mocked discovery tests that unexpectedly consulted the operator's installed PySUS DuckLake metadata cache after reporting intentionally empty FileBags. Fakes now pin the fallback to an empty result without modifying actual discovery behavior.
- Tested cache isolation using a fresh child interpreter; retained the guard that refuses a cache-path switch after PySUS import. No existing user cache is deleted or rewritten.
- `preparar-agregado` now reports small-cell block and existing-candidate errors concisely without a traceback. No count details, groups, raw rows or files are released.
- Added offline full-suite PySUS-installed CI in Windows and Linux to reproduce users' optional-dependency setups. Both environments passed 69 tests on the development branch.
- No changes to the public synthetic Render service, real-data access gates, or manual review requirements.



## 0.4.0-alpha.2 (2026-11-02): REAL-DATA RELEASE ENGINEERING, NOT PUBLICATION

- Added offline `preparar-agregado` to generate a **private unapproved** fixed demographic count candidate from local SINAN SQLite (one file-year, one UF, one dimension; no outcomes/municipalities or row-level data).
- Fail-closed conservative small-cell guard (`min_cell=20`, `min_partition=100`), strict source and category validation, SHA-256 fingerprints, exclusive local file creation under gitignored `data/`.
- Independent pure-stdlib `aggregate_contract` requires separate privacy/scientific review attestations, source `final` status, exact candidate and package digest, no extra keys and a single approved table.
- Added `sinan_mcp.approved_server`: separate opt-in MCP Streamable HTTP process for ONLY immutable reviewed static JSON. Fails on missing/invalid approval, with no connection to databases or the existing synthetic public service.
- Added dedicated synthetic privacy/security tests and an operator guide. **No real aggregates published, no change to Render synthetic preview.**



## 0.4.0-alpha.1 (2026-11-02): PUBLIC DEMONSTRATION (synthetic only)

- Added **dedicated** `sinan_mcp.public_server` module with static fictional fixture, no import path to the private SQLite/ingestion/MCP server, and no patient data access.
- Added seven narrowly scoped public read-only MCP tools with repeated explicit synthetic disclaimers, strict demonstration-only filters, and a non-sensitive health endpoint.
- Added real Streamable HTTP with `stateless_http=True`, JSON replies, 16 KiB request limit, and validated Host/Origin allowlists; refuses to start without an approved hostname.
- Added isolated Render blueprint (`render.yaml`), deployment/review guide, a standalone privacy notice and security regression tests. Requires an operator-approved workspace and deployment. **Not yet certified for real health-data release.**
- Clarified that OpenAI Secure MCP Tunnel is not sufficient for public plugin submissions and that Plugin Directory publication requires a separate platform review.



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
