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
