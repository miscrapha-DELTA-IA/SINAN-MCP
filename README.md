# SINAN MCP

**Uma interface de ferramentas MCP para educação epidemiológica e estudos exploratórios sobre a estrutura do SINAN.**

> v0.4.0-alpha.4 · Independente, não afiliado ao Ministério da Saúde/DATASUS · Não indicado para decisões clínicas.

## Alcance: múltiplos agravos, não somente tuberculose

**Objetivo:** navegar, pesquisar e eventualmente consultar agregados aprovados de múltiplas doenças e agravos de notificação registrados no SINAN. **Não significa qualquer doença da medicina nem qualquer código CID.** A lista de agravos notificáveis e os sistemas de origem mudam; para alguns temas há bases em sistemas diferentes do SINAN.

O índice de referência possui atualmente **14 aliases internos de agravos** (TB, dengue, hanseníase, hepatites virais, sífilis, meningite, violências, etc.). Isso é um **índice exemplificativo, não a lista nacional exaustiva e não um mapa validado de códigos PySUS**. A pesquisa de referências **não contém contagens reais**, não comprova importação e não significa que um indicador foi validado.

- `pesquisar_agravos(termo, limite)`: busca por texto e nome, inclusive sem acentos.
- `descrever_agravo(codigo_interno)`: estado de implementação, limites e links oficiais.
- `listar_fontes_oficiais()`: páginas oficiais verificadas do MS, DATASUS/TABNET e Portal SINAN. Esses links são pontos de entrada, não arquivos de valores previamente auditados.
- `contar_notificacoes` e `proporcao_abandono_tuberculose`: **continuam limitadas ao exemplo inventado de TUBE/2024/PI no servidor público**, não a notificações reais.
- Os agregados reais dependerão de tabelas pré-computadas, documentação por agravo/ano e revisão independente antes de disponibilização; nenhum banco individual é acessado na modalidade pública.

Consulte [escopo e fontes do catálogo](docs/MULTI_AGRAVO_CATALOG.md).

## Two intentionally separate distributions

| Mode | Entry point | Data | Intended use |
|---|---|---|---|
| **Public HTTPS preview** | `python -m sinan_mcp.public_server` | Referências para múltiplos agravos; **120 registros TB fictícios apenas como demonstração**; sem SQLite ou SINAN real | Descoberta de fontes, educação e demonstração do protocolo |
| **Private/local research** | `python -m sinan_mcp --db ./data/sinan-demo.sqlite3 servir` | User-selected local SQLite; real data only under safeguards | Private protocol integration and research |

**The public deployment is not a live SINAN statistics source.** Any actual real-data output requires a separately validated, pre-aggregated dataset and independent privacy/security review. The 113,012 real TB 2024 records imported into the user's Windows were **not** copied to the public server.

## Instância pública em operação (somente dados sintéticos)

- **MCP Streamable HTTP:** [https://sinan-mcp-public-preview.onrender.com/mcp](https://sinan-mcp-public-preview.onrender.com/mcp)
- **Saúde:** [https://sinan-mcp-public-preview.onrender.com/health](https://sinan-mcp-public-preview.onrender.com/health)
- **Hospedagem:** Render, instância gratuita isolada, autoDeploy desativado
- **Validação externa:** [Public HTTPS MCP smoke — GitHub Actions](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/actions/workflows/public-live-smoke.yml)
- **Estado dos dados:** EXCLUSIVAMENTE 120 registros demonstrativos fictícios TUBE/2024/PI. **Não é uma API de estatísticas oficiais.**

No ChatGPT, crie um conector/servidor MCP personalizado por **URL HTTPS** (não por túnel), use o endereço `/mcp` acima e escolha sem autenticação apenas para esta instância de demonstração sem dados privados. A instalação local de pesquisa permanece separada. A publicação no Plugin Directory depende de revisão e aceite próprios da plataforma.

A instância gratuita pode suspender após inatividade, causando latência na primeira chamada. O operador deve considerar monitoramento e custo/cotas antes da divulgação ampla.

## Publishing today: safe public preview

See [public launch checklist](docs/PUBLIC_LAUNCH.md), [public privacy notice](docs/PUBLIC_DISCLOSURE.md), and [Render blueprint](render.yaml). The service starts only with a hosting-provided hostname:

```sh
python -m pip install -e .
SINAN_PUBLIC_HOST=example-mcp.your-domain.com PORT=10000 python -m sinan_mcp.public_server
```

`/health` is a non-sensitive uptime check; `/mcp` is the stateless Streamable HTTP endpoint. **Never configure a public server to load `data/sinan.sqlite3` or to run `sinan_mcp.server`.** The private local server remains available independently.

For private usage, continue below.

---



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

## Scientific scope (pilot)

- **Two pilot diseases:** TUBE and DENG. Disease-year codebooks still need validation.
- **Remote discovery without microdata download:** `python -m sinan_mcp descobrir-pysus --agravo TUBE --ano 2024` lists PySUS files without loading records. Requires `.[ingest]`.
- **Batch-wise ingestion:** PySUS downloads a FileBag or uses a bounded Windows SQL-catalog fallback and streams Parquet/CSV records, avoiding national dataframes in RAM. Local Windows ingestion of TUBE 2024 has been user-confirmed for 113,012 projected records; this does not validate epidemiologic definitions.
- **Administrator-only fairness audit:** `auditar-equidade` evaluates a local held-out prediction CSV, entirely outside the MCP surface. See [fairness protocol](docs/FAIRNESS_PROTOCOL.md).
- **Privacy-first MCP/REST:** Real-data numeric queries require explicit opt-in and pass a conservative cross-table small-cell guard; otherwise only the synthetic demo is queryable. See [security](SECURITY.md).
- **Administrator-only quality audit:** `diagnosticar-base` measures missing or ignored fields locally; not available to LLM tools.

See [scientific interpretation](docs/EPIDEMIOLOGY.md).

## Tools

| MCP tool | Function |
|---|---|
| `listar_bases` | Dataset snapshots (no local filenames or record totals) |
| `descrever_campos` | Variable definitions and caveats |
| `contar_notificacoes` | Counts for one UF + one file-year, by `sexo` or `raca_cor` |
| `proporcao_abandono_tuberculose` | Exploratory outcome ratio, **not** an official indicator |
| `listar_agravos` | Curated pilot disease catalogue and scope |
| `metodologia_abandono_tuberculose` | Formula and scientific limitations (not an official indicator) |

For numeric tools, provide `ano_inicio=ano_fim=2024`, `uf="PI"`, `por="raca_cor"` (or `sexo`). Public tools intentionally deny municipality filters, totals, date ranges and other cross-cutting groupings. Responses include `resultado`, `proveniencia`, `politica` and `limitacoes`. Small cells are suppressed. These restrictions **reduce but do not eliminate** statistical disclosure risk; *no formal anonymization guarantee exists.* No row-level or arbitrary SQL tools are exposed.

**Public release safeguard:** Since v0.3.0a3 the server refuses numeric MCP/REST queries against real imported snapshots unless an administrator deliberately sets `SINAN_PUBLIC_REAL_DATA=1` on the **server** process. This also affects previously functioning local REST real-data queries. Even with opt-in, an entire year/UF partition is withheld when too small or when cross-table comparison could reveal subcells of fewer than 10. Do **not** enable opt-in for remote use without an independent disclosure assessment. Synthetic demo remains enabled.

**Scientific caveats:** `ano` is the **imported file-year**, not necessarily the notification, diagnosis or closure year. Counts are records, not incidence or unique patients. The exploratory TB abandonment ratio computes `(SITUA_ENCE=2 or 10)/(SITUA_ENCE=1,2,10)`; without a formally validated case cohort and longitudinal deduplication it **must not be described as the Ministry's official treatment abandonment indicator**.

### Windows: empty PySUS catalog

If PySUS returns no files in your local environment, `descobrir-pysus` defaults to `--source auto`: it checks the PySUS mirror and, only when the mirror is empty/unreachable, requests discovery from the original DATASUS source. The result reports individual attempts and **never downloads health records**. A `nao_confirmado` result means the availability could not be established, **not** that the dataset does not exist. To troubleshoot independently use `--source catalog` and `--source origin`. The ingestion command deliberately retains a required, explicit source policy (`catalog` by default), so switching data providers cannot happen silently.

## Local ingestion (administrative operation, not an MCP tool)

```sh
python -m sinan_mcp importar-csv ./dataset.csv --agravo TUBE --ano 2024 --status desconhecido
python -m pip install -e '.[ingest]'
python -m sinan_mcp descobrir-pysus --agravo TUBE --ano 2024 --source auto
python -m sinan_mcp importar-pysus --agravo TUBE --ano 2024 --source catalog --status desconhecido
python -m sinan_mcp diagnosticar-base --agravo TUBE --ano 2024
```

`--source catalog` may use a PySUS mirror; `--source origin` selects the upstream origin. Verify actual availability, codebooks, year, source and preliminary/final status independently. The SQLite projection excludes direct identifiers but retains quasi-identifiers; keep it private. One imported snapshot per agravo/file-year is retained; reimport replaces the former snapshot. The optional PySUS component has separate copyleft license obligations; assess them before redistributing combined distributions.

## Local REST adapter

```sh
python -m sinan_mcp --db ./data/sinan-demo.sqlite3 servir --rest --port 8001
```

Routes: `GET /health`, `GET /v1/bases`, `GET /v1/campos`, `GET /v1/agravos`, `GET /v1/metodologia/tb`, `POST /v1/contagens`, `POST /v1/tb/abandono`.

```json
{"agravo":"TUBE","ano_inicio":2024,"ano_fim":2024,"uf":"PI","por":"raca_cor"}
```

MCP over local Streamable HTTP: `python -m sinan_mcp servir --http --port 8000` (`/mcp`). **Do not expose local REST/MCP endpoints publicly.** Remote use requires auth, transport security and formal statistical disclosure controls.

## Validation and documentation

```sh
python -m pip install -e '.[dev]'
python -m pytest -q
```

Includes synthetic core/REST/privacy tests and an **in-memory real MCP client** integration test when the v2 SDK is installed. Live PySUS downloads and desktop-client operation are not verified in this offline environment. The optional PySUS dependency and Parquet tests can be checked via the manually triggered `PySUS optional integration` workflow without downloading real records. CI checks supported Python/OS combinations after installation.

- [Guia em português](docs/pt-BR.md) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md)
- [Official SINAN portal](https://portalsinan.saude.gov.br/) · [PySUS docs](https://pysus.readthedocs.io/en/stable/quickstart.html) · [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/)

MIT-licensed original code; not an official DATASUS/SINAN service.

## Windows / empty PySUS catalogs

If both catalog and origin return `nao_confirmado`, the public PySUS 2.11.x implementation does **not** provide two independent backend checks: both use DuckLake catalog metadata. Test with a new isolated **metadata-only** cache and an HTTPS HEAD diagnostic:

```powershell
py -3.11 -m sinan_mcp descobrir-pysus --agravo TUBE --ano 2024 --cache-novo --diagnostico
```

`--cache-novo` changes `PYSUS_CACHEPATH` **only for this process**, creates a new cache under the project's ignored `data/` folder, and leaves the original PySUS cache untouched. The PySUS library may download public **catalog databases** for discovery; it does not download SINAN patient records because `download=False` is passed to the file fetcher. The HTTPS HEAD checks the public metadata index and reports status codes without printing credentials or local paths.

If the fresh catalog is empty but HTTPS responds, keep the diagnostic output for investigation (a connection to the catalog file does **not** prove that the dataset index is correctly populated). If HTTPS fails, check local DNS, corporate proxies or firewall restrictions; avoid disabling TLS certificate verification. Do not import real health records as a debugging step.

### Windows PySUS 2.11.x catalog-query compatibility

A reproducible issue occurs on Windows: PySUS may return empty FileBags despite successfully downloading the DuckLake catalog, which contains the expected TUBE/DENG file records. Linux discovery succeeds with the same catalog. The project now uses a **metadata-only SQL fallback**, strictly parameterized and restricted to public SINAN FTP Parquet file names, when ordinary discovery returns empty. This is an experimental compatibility workaround, **not** direct FTP access or validation that the complete data file is reachable. It does not automatically change the source of any clinical data ingestion.

Try after updating your git clone:

```powershell
git pull origin main
py -3.11 -m sinan_mcp descobrir-pysus --agravo TUBE --ano 2024 --diagnostico
py -3.11 -m sinan_mcp descobrir-pysus --agravo DENG --ano 2024 --diagnostico
```

Use `--cache-novo` only to isolate further cache problems. If the discovery reports `origem: "ducklake_sql_local/ftp-mirror"`, the **metadata-only** fallback was activated. The regular `importar-pysus` command still depends on the upstream PySUS download mechanism and may need a separate Windows compatibility fix.

## v0.3.0a2 — Windows safe import (experimental)

File discovery via DuckLake SQL has been tested on Windows, but discovery alone is **not** a downloaded or epidemiologically validated dataset. To preview the public FTP-mirror Parquet file size and expected checksum (no clinical data transferred):

```powershell
py -3.11 -m sinan_mcp planejar-pysus --agravo TUBE --ano 2024
```

Only if the file size, storage and access policies are appropriate, **explicitly** import into your own private database:

```powershell
py -3.11 -m sinan_mcp --db .\data\sinan.sqlite3 importar-pysus --agravo TUBE --ano 2024 --source catalog --status desconhecido
py -3.11 -m sinan_mcp --db .\data\sinan.sqlite3 diagnosticar-base --agravo TUBE --ano 2024
```

When PySUS returns an empty `FileBag` on Windows, the importer now resolves **only** the selected FTP-mirror files from the local public DuckLake catalog, downloads them over certificate-verified HTTPS with a fixed host, checks reported byte lengths and available SHA-256 digests, and streams only selected records into a local SQLite projection. Temporary raw Parquet files are removed on normal completion, but backups, OS cache, unexpected interruptions and the SQLite quasi-identifiers can still carry privacy risk; follow applicable institutional safeguards. No patients or raw files are sent to GitHub/CI, and public MCP/REST tools cannot trigger ingestion.

Do **not** infer that a catalog entry guarantees the file is available, that remote bytes match the recorded metadata, or that the TB exploratory proportion is a certified official metric. Full real-data import is **not yet verified**. `--source origin` refuses an empty PySUS result rather than silently switching to the catalog mirror. The importer enforces a 2 GiB limit per file and 3 GiB aggregate catalog size; large datasets may require a dedicated ingestion plan.

## ChatGPT Secure MCP Tunnel (Windows)

See [`docs/CHATGPT_TUNNEL_WINDOWS.md`](docs/CHATGPT_TUNNEL_WINDOWS.md). A private tunnel does not anonymize tool responses. Initial connector testing MUST use `sinan-demo.sqlite3`.

## Offline predictive fairness assessment (experimental)

```powershell
py -3.11 -m sinan_mcp auditar-equidade .\predicoes_teste.csv --grupo raca_cor --coorte 2022-2023 --limiar 0.5 --bootstrap 200
```

The **locally held-out** CSV must include only `y_true` (0/1), `y_score` (predicted LTFU probability 0–1) and `raca_cor` or `sexo`; extra columns are ignored by the auditor but should not be exported unnecessarily. Never upload it to ChatGPT or Git. This command audits predictions **already created elsewhere**; it cannot train or validate a TB model on the current seven-field projection. See [research protocol](docs/FAIRNESS_PROTOCOL.md).

## Reprodutibilidade de agregados reais — candidato local e revisão obrigatória

A ferramenta **`preparar-agregado`** lê somente o SQLite local e gera uma tabela demográfica candidata sob `data/review-packages/`, sem publicar nada. O módulo opcional **`sinan_mcp.approved_server`** é um servidor SEPARADO para apenas pacotes estáticos com revisões registradas e checksum travado. Ele não é o servidor público atualmente hospedado.

```powershell
py -3.11 -m sinan_mcp --db .\data\sinan.sqlite3 preparar-agregado --agravo TUBE --ano 2024 --uf PI --por raca_cor
```

O pacote real ainda não foi preparado no computador do operador, e nenhum dado real foi aprovado ou enviado para nuvem. A importação atual do arquivo TUBE 2024 tem `status=desconhecido`; isso **bloqueia** publicação antes da verificação oficial de consolidação. Consulte o [guia de publicação revisada](docs/AGGREGATE_PUBLICATION.md).
