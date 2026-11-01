# SINAN MCP

**Epidemiological data from Brazil, exposed through auditable Model Context Protocol tools.**

> v0.2.0-alpha.1 · Local-first research prototype · Unaffiliated with the Ministry of Health · Not for clinical decisions or patient inference.

The LLM interprets the question; the server calculates the answer from locally imported public surveillance data. No real SINAN data ships with the project.

## 1-minute synthetic demo

Python 3.11+ (Windows, macOS or Linux):

```sh
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m sinan_mcp demo
python -m sinan_mcp --db ./data/sinan-demo.sqlite3 servir
```

The example creates **fictional records only** in a separate `sinan-demo.sqlite3` file. The server waits on stdin for an MCP host. Use an absolute Python interpreter path and absolute `--db` path in your client. Examples are provided under [`examples/`](examples/). Claude Desktop, Cursor and other clients require their own supported MCP configuration; **Cowork/gateway support has not been verified**.

Try asking: *"On the synthetic TUBE dataset, show the race/color distribution in PI for the 2024 file and explain the provenance and limitations."*

## Tools

| MCP tool | Function |
|---|---|
| `listar_bases` | Dataset snapshots (no local filenames or record totals) |
| `descrever_campos` | Variable definitions and caveats |
| `contar_notificacoes` | Counts for one UF + one file-year, by `sexo` or `raca_cor` |
| `proporcao_abandono_tuberculose` | Exploratory outcome ratio, **not** an official indicator |

For numeric tools, provide `ano_inicio=ano_fim=2024`, `uf="PI"`, `por="raca_cor"` (or `sexo`). Public tools intentionally deny municipality filters, totals, date ranges and other cross-cutting groupings. Responses include `resultado`, `proveniencia`, `politica` and `limitacoes`. Small cells are suppressed. These restrictions **reduce but do not eliminate** statistical disclosure risk; *no formal anonymization guarantee exists.* No row-level or arbitrary SQL tools are exposed.

**Scientific caveats:** `ano` is the **imported file-year**, not necessarily the notification, diagnosis or closure year. Counts are records, not incidence or unique patients. The exploratory TB abandonment ratio computes `(SITUA_ENCE=2 or 10)/(SITUA_ENCE=1,2,10)`; without a formally validated case cohort and longitudinal deduplication it **must not be described as the Ministry's official treatment abandonment indicator**.

## Local ingestion (administrative operation, not an MCP tool)

```sh
python -m sinan_mcp importar-csv ./dataset.csv --agravo TUBE --ano 2024 --status desconhecido
python -m pip install -e '.[ingest]'
python -m sinan_mcp importar-pysus --agravo TUBE --ano 2024 --source catalog --status desconhecido
```

`--source catalog` may use a PySUS mirror; `--source origin` selects the upstream origin. Verify actual availability, codebooks, year, source and preliminary/final status independently. The SQLite projection excludes direct identifiers but retains quasi-identifiers; keep it private. One imported snapshot per agravo/file-year is retained; reimport replaces the former snapshot. The optional PySUS component has separate copyleft license obligations; assess them before redistributing combined distributions.

## Local REST adapter

```sh
python -m sinan_mcp --db ./data/sinan-demo.sqlite3 servir --rest --port 8001
```

Routes: `GET /health`, `GET /v1/bases`, `GET /v1/campos`, `POST /v1/contagens`, `POST /v1/tb/abandono`.

```json
{"agravo":"TUBE","ano_inicio":2024,"ano_fim":2024,"uf":"PI","por":"raca_cor"}
```

MCP over local Streamable HTTP: `python -m sinan_mcp servir --http --port 8000` (`/mcp`). **Do not expose local REST/MCP endpoints publicly.** Remote use requires auth, transport security and formal statistical disclosure controls.

## Validation and documentation

```sh
python -m pip install -e '.[dev]'
python -m pytest -q
```

Includes synthetic core/REST/privacy tests and an **in-memory real MCP client** integration test when the v2 SDK is installed. Live PySUS downloads and desktop-client operation are not verified in this offline environment. CI checks supported Python/OS combinations after installation.

- [Guia em português](docs/pt-BR.md) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md)
- [Official SINAN portal](https://portalsinan.saude.gov.br/) · [PySUS docs](https://pysus.readthedocs.io/en/stable/quickstart.html) · [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/)

MIT-licensed original code; not an official DATASUS/SINAN service.
