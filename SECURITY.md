# Security policy

**Research prototype only. Not an anonymization system.** Never commit real health records or credentials.

- MCP and local REST expose only narrow aggregates (one UF, one file-year, one approved dimension). Municipality filters, arbitrary SQL, row-level outputs and unrestricted totals are denied.
- Numeric public tools require one file-year + one UF; raw rows and arbitrary SQL remain unavailable.
- **New in v0.3.0a3:** Real-data numeric queries are **disabled by default**. After a local privacy review an administrator may explicitly set `SINAN_PUBLIC_REAL_DATA=1` on the server process. This also applies to local REST; do not set it on an unreviewed remote deployment.
- An all-or-nothing publication guard denies **both** sex and race dimensions and TB outcomes for an entire year/UF partition when any populated demographic group is below ten, any TB cure/abandonment subgroup contains 1–9 records, or the partition has fewer than 100 records. The same decision is enforced across public tables. This remains **non-DP** and does not formally prevent linkage, side channels or disclosures across years, data versions, external datasets, or future features.
- Numeric public queries use a read-only SQLite connection, never initialize a missing database or write to the storage file.
- Small-cell suppression and coarse grouping are **not guarantees** against differencing or reconstruction. Audit cross-query, temporal and external linkage before any public deployment.
- Local REST binds to `127.0.0.1`, checks Host, and caps JSON body sizes. Do not put either REST or MCP behind a public proxy.
- The CLI importer reads files locally; data projected into SQLite can remain sensitive as quasi-identifiers. Follow institutional policies for access, encryption and retention.
- Remote operation requires qualified privacy and security review, authentication/authorization, TLS, query budgets, rate limits, provenance controls and monitoring.
- Report security flaws privately to maintainers without including personal health information. Do not post sensitive details in public issues.

## OpenAI Secure MCP Tunnel precautions

- The tunnel is an outbound private route, **not** itself proof that demographic aggregates are safe for ChatGPT exposure. Verify who is authorized to invoke the connector; the returned MCP results are processed by the client platform.
- Start with `data/sinan-demo.sqlite3`. Keep `SINAN_PUBLIC_REAL_DATA` unset.
- Never store API keys or `tunnel_id` plus credentials in Git, CLI logs, screenshots, chat messages, README examples or tracking systems. Use a least-privileged runtime key.
- Keep the local profile and SQLite folder access-controlled. Do not use a network-shared disk or publish the HTTP/REST interface. Do not enable `SINAN_PUBLIC_REAL_DATA=1` unless the responsible data custodian has assessed provenance, disclosure risk, security controls, intended use and legal/institutional requirements.
- The offline `auditar-equidade` command consumes individual test predictions. Prediction CSVs may reveal health information; keep input and outputs private. Its results are **not** retrievable through MCP tools.

## Strict public/private boundary — v0.4.0a1

**Public production start: `python -m sinan_mcp.public_server` ONLY.** This module is isolated from `sinan_mcp.server`, `sinan_mcp.tool_api`, `sinan_mcp.core`, all SQLite operations, CLI imports and PySUS. It runs exclusively on hardcoded *fictional* records. An incorrectly set `SINAN_DB_PATH` or `SINAN_PUBLIC_REAL_DATA=1` cannot turn it into a real-data server.

HTTP `/mcp` uses stateless mode and JSON responses, limits request bodies and allows only a configured Host and ChatGPT browser origins. Starting without a valid hostname fails closed; TLS termination is the responsibility of the hosting proxy. Anonymous access is acceptable **only because** this public preview has no user state, real records, private resources or write actions. Adding any such capability requires a new access-control design.

The public release does not solve re-identification risks for a future dataset, perform differential privacy, certify official epidemiological metrics or make the private real-data feature flag appropriate for public use. See [public policy and launch gates](docs/PUBLIC_LAUNCH.md). A Render public service needs separate operational rate limiting, uptime/monitoring, retention policy and capacity planning.

## Precomputed real aggregates (under independent review)

The offline `release_pipeline` imports a strictly limited count table from a locally stored SINAN projection using SQLite read-only access. It blocks entire partitions if any included demographic cell has fewer than 20 observations or the whole population is below 100, supports one UF + one FILE-year + one demographic dimension, and excludes outcome and municipal data. The output is **UNAPPROVED** and saved only under gitignored `data/`.

An independent `aggregate_contract` module validates a human-reviewed static JSON release, its pinned SHA-256 and a two-reviewer record; this validates structure and attestations but **does not verify anonymity, reviewer identities or authorization**. The separate optional `approved_server` imports only this contract, never SQLite, PySUS or the research server. It fails closed if no reviewed release + pinned hash is provided and is NOT configured or deployed to Render.

Conservative count thresholds are **not a formal anonymization mechanism**. Other releases, temporal overlap, auxiliary datasets, data version differences and health-context sensitivity require expert disclosure review. No real package may be published without independent approval. See [aggregate publication guide](docs/AGGREGATE_PUBLICATION.md).

## Official table candidates (v0.4.0a4)

`preparar-tabela-oficial` is a **local-only** conservative schema/disclosure check for a user-provided preaggregated table. It does not access source websites, attest that values are authentic, validate the declared source SHA-256 against an export, or publish values. Its output remains an UNAPPROVED candidate inside gitignored `data/review-packages/`, not consumed by either public MCP service. Independent source reconciliation, cross-release disclosure risk and authorization are required before any public use.

## Segurança operacional da demonstração pública — implantada em 2026-11-04

O PR #38 foi integrado e implantado somente na **instância de demonstração sintética**, SHA `3ac1db9dd4bb81b3bf685356528da4572c4f0c3d`. O servidor público dispõe de orçamento global por processo (300 req/min), concorrência máxima de 16 chamadas MCP, HTTP 429 com Retry-After e build com lockfile verificado por hashes; não confia em X-Forwarded-For para identificar clientes. A sonda HTTPS pós-deploy foi aprovada. Esses controles **não** substituem proteção na borda, auditoria independente, homologação de dados epidemiológicos ou acesso autenticado a uma hipotética instância com dados sensíveis. Variáveis e retenção de logs da Render ainda aguardam atestado administrativo. Consultar [runbook operacional](docs/SECURITY_OPERATIONS.md), [proteção de branch](docs/BRANCH_PROTECTION.md) e [checklist Render](docs/RENDER_SECURITY_VERIFICATION.md).
