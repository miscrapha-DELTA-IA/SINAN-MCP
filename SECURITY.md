# Security policy

**Research prototype only. Not an anonymization system.** Never commit real health records or credentials.

- MCP and local REST expose only narrow aggregates (one UF, one file-year, one approved dimension). Municipality filters, arbitrary SQL, row-level outputs and unrestricted totals are denied.
- Small-cell suppression and coarse grouping are **not guarantees** against differencing or reconstruction. Audit cross-query, temporal and external linkage before any public deployment.
- Local REST binds to `127.0.0.1`, checks Host, and caps JSON body sizes. Do not put either REST or MCP behind a public proxy.
- The CLI importer reads files locally; data projected into SQLite can remain sensitive as quasi-identifiers. Follow institutional policies for access, encryption and retention.
- Remote operation requires qualified privacy and security review, authentication/authorization, TLS, query budgets, rate limits, provenance controls and monitoring.
- Report security flaws privately to maintainers without including personal health information. Do not post sensitive details in public issues.
