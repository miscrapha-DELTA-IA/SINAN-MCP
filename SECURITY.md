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

## Roadmap: offline verification and transport hardening

- The new administrator-only commands (`verificar-proveniencia`, `verificar-linhagem`, `auditar-qualidade`, `confrontar-tabnet`, `verificar-composicao`) deliberately **do not register as public MCP tools**. Reports from local SQLite or source tables can be sensitive and must not be pasted into issues or public assistants.
- SHA-256 verifies **local byte integrity only**; operator-supplied official URLs, download codes, dictionary versions and `final` flags remain unverified assertions until an independent provenance review. A CSV hash can be linked to the import snapshot; PySUS composite snapshot digests require a different attestation.
- The constrained PySUS catalog importer refuses redirected requests before contacting another host, caps transfer sizes, retries transient failures at most three times, removes partial files and avoids overwriting existing files. This does not replace transport penetration tests or a full supply-chain audit.
- The offline release composition gate rejects multiple approved packages involving the same disease and UF, across years/versions/dimensions. A successful check **never authorizes publication** or establishes cross-release anonymity, external linkage safety, legitimate reviewer identity or legal authorization.
- CI blocks tracked files in `data/` and common clinical/credential formats, but it is **only a path/extension check**, not a secret/PII content scan. Review the entire diff before merge; use organization-level secret scanning and restricted reviewer access.
- The service has no production remote microdata OAuth, scope-based permissions, institutional review attestation, or privacy-budget infrastructure. **Do not expose private data remotely or auto-deploy real aggregate releases.** See [implementation and blocking gates](docs/ROADMAP_IMPLEMENTATION.md).


## Evidências de fonte oficial por agravo e ano

A referência a um documento hospedado pelo Portal SINAN **não** garante
que esse dicionário seja aplicável ao arquivo de determinado ano. A
curadoria `year_evidence_registry` falha fechada: nenhum campo em JSON
pode promover documentação localizada a dataset autenticado, coorte
validada ou autorização de publicação. Nenhum novo endpoint acessa
SQLite, PySUS, arquivos privados ou rede.

`confrontar-evidencia-ano` é CLI administrativa local. Um PDF com
cabeçalho válido, nome igual e SHA-256 calculado localmente pode ser
falsificado; o relatório explicitamente **não** comprova publicação
ou identidade do arquivo. Conserve documentação e resultados sensíveis
fora de issues, PRs e artefatos de CI. A cadeia de confiança exige
revisores e provas externas autenticados antes de promover qualquer
registro anual.

## Distribuições anuais no catálogo oficial

`official_annual_resources` expõe exclusivamente links e UUIDs de recursos do portal governamental. Uma referência a uma distribuição não autoriza downloads automáticos, ingestão, publicação ou conclusão de consolidação; o portal pode atualizar arquivos sem alteração de seus nomes.

`conferir-zip-distribuicao` é CLI administrativa offline, com nome exato, limite de tamanho, SHA-256 local, ZIP de uma entrada e bloqueio de caminhos, symlinks e explosão de descompactação. A ferramenta não descompacta ou lê linhas, e seus hashes não autenticam a publicação. Não publique relatórios locais ou dados reais em issues/CI.



## Auditar localmente esquema e dicionário não autoriza uso dos dados

`local_schema_review` é um processo separado do MCP público e da ingestão clínica. Aceita arquivos locais de origem legítima sob responsabilidade do pesquisador: um ZIP de recurso anual curado, um PDF de dicionário e uma transcrição manual vinculada ao SHA local do PDF. CSV só lê cabeçalho; JSON opcional lê transitoriamente valores de no máximo 64 registros no parser ijson, sem reproduzi-los em resultados. A execução acontece exclusivamente na máquina autorizada. Não há busca online, upload, registro em servidor, logs de valores clínicos ou persistência de microdados.

O relatório privado inclui apenas nomes de campos previamente transcritos (metadados documentais), contagens de campos não reconhecidos e checksums locais. Um pacote com dez pendências é criado com modo restrito e sem sobrescrever arquivos. O resultado continua não autenticado e não validado epidemiologicamente. Nenhuma flag de contrato ou edição manual de parecer concede autorização de análise real ou publicação. Não executar sobre arquivos reais em CI, issues, prompts ou ambiente compartilhado.



## Rascunho de campos DBF do PDF local

`local_pdf_dictionary_candidate.py` é uma CLI administrativa que aceita somente o PDF de nome esperado para a referência documental curada DENG/CHIK, confere cabeçalho e SHA-256 local, limita tamanho/páginas/tokens e exige três campos âncora antes de criar novo contrato de páginas. Usa a dependência **opcional** PyMuPDF no computador do operador; não baixa PDFs, não acessa registros, não consulta o MCP e não confere a integridade binária por assinatura governamental. O candidato fica privado, é não revisado e jamais serve de aprovação. O layout de outros PDFs não é suportado, mesmo que outro arquivo seja renomeado para imitar o nome esperado.



## Confronto privado de PDF Dengue de 2024 e antigo PDF 2015

`local_dengue_dictionary_crosswalk.py` é exclusivamente administrativo, sem ligação com o MCP público. O perfil PDF de 22 páginas utiliza hash **local observado no arquivo compartilhado pelo pesquisador**, para recusar edições não revisadas. Esta verificação NÃO autentica a origem governamental nem confirma que o dicionário é aplicável ao ZIP de 2024. O ZIP é inspecionado pelo validador existente e a comparação lê somente a primeira linha CSV limitada a 128 KiB. Nomes fora dos dicionários não são ecoados e valores de notificações não são lidos. O relatório JSON exclusivo tem flags de validação e divulgação negativas; o código não aprova a fonte, a ciência ou a privacidade.


## Diagnóstico de prontidão do roadmap — não é aprovação

O módulo `roadmap_readiness.py` administra apenas checklists locais JSON por alias/ano. Não importa SQLite/PySUS/ZIP, não contata rede, não abre microdados e não cria release; não integra ferramentas MCP públicas. Cada gate reporta no máximo situação declarada e SHA-256 local de sua evidência, não identidade do avaliador. A implementação exige validação estrita de estrutura, recusando campos adicionais, nomes de status desconhecidos, autorização de publicação ou evidências declaradas sem hash. A avaliação **nunca produz autorização técnica ou legal para publicar ou acessar dados reais remotamente**, mesmo que todas as sete frentes sejam declaradas com parecer.



## P0 integration boundary guard (pending code review)

The new scripts/check_public_isolation.py statically examines transitive local imports reachable from sinan_mcp.public_server. Only the explicitly reviewed public metadata modules are allowed. Imports of the private ingestion, SQLite, PySUS, release, CLI and local-scientific-review modules fail CI. Dynamic import calls and a small set of private environment variables are also denied in the public import graph. This check runs on Windows and Linux, Python 3.11/3.12.

**This is static defense-in-depth, not a proof of safety:** Python can call APIs dynamically, dependencies can change and runtime behavior may have side effects. It does not replace the MCP tool contract snapshot, full diff review, dependency/secret scanning, pentesting or institutional privacy controls. Any new public import requires explicit security review and allowlist update.

**The legacy local MCP/REST service is NOT the public demonstration.** The legacy environment flag SINAN_PUBLIC_REAL_DATA=1 may enable sensitive aggregate access in sinan_mcp.tool_api under some conditions; it is **not** a permission model and must not be used for internet or third-party connector exposure without independent authority and security review. The Render Blueprint remains pinned to sinan_mcp.public_server, autoDeploy false and synthetic-only data.

**Year coverage is not clinical readiness:** the administrative command diagnosticar-cobertura-multiagravo reads only fixed, packaged reference catalogs and reports all real-data/indicator/publication approval flags as false for every disease/year. It does not open local datasets or modify readiness gates.
