# SINAN MCP — public preview launch and review

**Status: public synthetic preview, not an epidemiological SINAN service.**

The production public server is **a separate module**: `sinan_mcp.public_server`. It has only hardcoded fictional records and static methodology/catalogue texts. It never reads `SINAN_DB_PATH`, opens SQLite, queries PySUS, receives credentials, accepts arbitrary filters, nor exposes import, prediction or fairness-audit endpoints. Its outputs consistently and explicitly mark numerical results as **synthetic**.

## Confirmed public preview — 2026-11-02

New Render web service `sinan-mcp-public-preview` deployed in a dedicated Free instance in `My Workspace`, with no databases, disks, or private tunnel credentials. Automatic deploys are disabled.

- Verified HTTPS health URL: https://sinan-mcp-public-preview.onrender.com/health
- Verified public MCP URL: https://sinan-mcp-public-preview.onrender.com/mcp
- Original deployment revision (2026-11-02): `43307f28f6831b6b43a533fa85ee624eab97fc18` (`v0.4.0a1`).
- **Latest live deploy reported by Render on 2026-11-04:** `678e15523bb13ec2f36778ffe879c479dff2b3bf` (manual/API deploy finished 2026-11-02 22:08 UTC). This is not the current GitHub `main` revision; the service has auto-deploy disabled.
- The earlier success of the live smoke probe establishes functionality for a historical deployment only. A fresh live smoke verification is still needed for the current deployed commit; the CI tests of a newer branch do not update Render.
- Independently verified by GitHub Actions workflow `public-live-smoke.yml` (success run `41506993125`): /health, MCP initialize, tools/list, listar_bases, contar_notificacoes and forbidden-Origin HTTP 403.
- Main CI at revision `01b758112a6db71309e87273254ca6ce2e0379ac` also passed. Changes after the deployment do not update the running service automatically.

**These tests establish endpoint functionality, not legal/official certification, immunity to denial-of-service, or approval for Plugin Directory listing.**

## Deployment architecture

Public client → HTTPS reverse proxy (e.g. Render) → MCP Streamable HTTP `/mcp` → static synthetic demo tools.

The private `sinan_mcp.server` and Secure MCP Tunnel are **not** suitable for public submissions under OpenAI's requirements. They remain a separate private-research channel.

Public release is independent of access to the operator's local SINAN SQLite. The `render.yaml` blueprint is a voluntary reference; it does not deploy itself. Use only a dedicated new public service; do not reuse the user's existing streaming/backend services.

## Deploy on Render

1. Explicitly select the Render workspace and an appropriate service plan; verify pricing and quota. Never infer the workspace from the login.
2. From the repository `main`, use the **public** Blueprint or a new Python web service with:
   - build: `python -m pip install -e .`
   - start: `python -m sinan_mcp.public_server`
   - health: `/health`
   - `PORT`: Render-supplied (defaults to 10000).
   - `RENDER_EXTERNAL_HOSTNAME`: Render-supplied public hostname. The server fails closed without `RENDER_EXTERNAL_HOSTNAME` or explicit `SINAN_PUBLIC_HOST`.
   - No databases, disks, secrets, `SINAN_DB_PATH` or real health datasets attached.
3. Confirm `https://<actual-render-host>/health` returns `{"status":"ok","deployment":"synthetic-only",...}`.
4. Confirm `https://<actual-render-host>/mcp` accepts MCP Streamable HTTP calls and lists only the ten public, read-only tools. Do not invent the URL until an actual deployment returns one.
5. Verify `Host` and `Origin` rejection: hostname allowlisted by `TransportSecuritySettings`; unexpected `Host` → HTTP 421; unapproved `Origin` → HTTP 403. Browser origins `https://chatgpt.com` and `https://chat.openai.com` are allowed; other clients without Origin can connect normally.
6. Verify synthetically-labelled results and failure of `agravo=DENG`, other dates/UFs, municipality and arbitrary dimensions. The server does not support real epidemiologic queries.
7. Monitor deploy health, error logs, response time, throughput and quotas. Set up rate limiting/edge abuse protection on the hosting account before broad announcement.
8. Connect a custom ChatGPT MCP plugin via the **actual stable HTTPS** `/mcp` URL. Do not select the private Secure MCP Tunnel for a public plugin submission. The platform's plugin publishing/review may require additional review/approval; a deployed URL is **not** equivalent to being listed in the public Plugin Directory.

## Compatibility / design

- Runtime `mcp>=2,<3`, `stateless_http=True`, `json_response=True`, `max_request_body_size=16384`.
- Application-host binding `0.0.0.0:$PORT` only in this synthetic public server; all real-data servers remain localhost-only.
- `TransportSecuritySettings` enforces Host/Origin allowlists.
- No OAuth required for the non-sensitive public demo (anonymous, no privileges, no persistent per-user state). Do **not** copy this configuration when adding private/restricted endpoints. Use a supported OAuth 2.1 / protected resource metadata flow and independent review for that deployment.
- Hosting charges and resource exhaustion are still potential risks; provider DDoS filtering alone does not constitute application rate limiting.
- Public example `listar_bases` is synthetic and must never report the operator's 113,012 real records.

## Post-launch release gates before any real SINAN aggregates

- Obtain validated, publicly releasable **pre-aggregated** data from a dated official open source, preferably with a versioned manifest, provenance, year of *diagnosis or notification* when defined, licencing and methodology.
- Use fixed public tables that have been subjected to disclosure review, complementary suppression and a cross-table / cross-year linkage analysis. No arbitrary SQL, dynamic denominator expansion, exact subgroup tiny cells, or remote per-record access.
- Cross-check independently against published official totals, especially treatment outcomes and cohort definitions. Add real-series regression tests without uploading individual health data.
- Threat model, privacy/information-security review, user-facing privacy policy, maintenance/incident response contact, provider terms, data retention, load testing, and operational monitoring.
- Do not claim that the existing `SINAN_PUBLIC_REAL_DATA=1` experimental flag makes real data safe for unrestricted public access. That gate is explicitly **not** enabled in the separate public module.

## Reference

- [OpenAI: Build an MCP Server for Plugins](https://developers.openai.com/plugins/build/mcp-server)
- [MCP Python SDK: deployment, host/origin security](https://py.sdk.modelcontextprotocol.io/run/deploy/)
- [Render: Web Services](https://render.com/docs/web-services)
