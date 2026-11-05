<div align="center">

<h1>SINAN MCP</h1>

<h3>An open research interface for epidemiological data, built around provenance.</h3>

<p><strong>Explore official SINAN references. Prototype with synthetic data. Keep sensitive research workflows separate.</strong></p>

<p>
  <a href="https://github.com/miscrapha-DELTA-IA/SINAN-MCP/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/miscrapha-DELTA-IA/SINAN-MCP/actions/workflows/ci.yml/badge.svg?branch=main" /></a>
  <a href="pyproject.toml"><img alt="Python 3.11+" src="https://img.shields.io/badge/Python-3.11%2B-24527a?logo=python&amp;logoColor=white" /></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-0f766e" /></a>
  <a href="#project-status"><img alt="Stage: Research Alpha" src="https://img.shields.io/badge/Stage-Research%20Alpha-6d28d9" /></a>
  <a href="https://modelcontextprotocol.io/"><img alt="Protocol: MCP" src="https://img.shields.io/badge/Protocol-MCP-334155" /></a>
</p>

<p><a href="#overview-for-reviewers">For reviewers</a> · <a href="#get-started">Local setup</a> · <a href="#public-synthetic-preview">Public demo</a> · <a href="docs/README.md">Documentation</a> · <a href="docs/pt-BR.md">Português</a></p>

</div>

---

> [!IMPORTANT]
> **Research alpha — not an official SINAN/DATASUS product.** The public MCP preview exposes **fictional tuberculosis records**, not live SINAN statistics. Its catalogue links are references, not validated datasets or approved epidemiological indicators. Do not use this project for clinical decisions, official reporting or public-health interventions.

## Why SINAN MCP?

Brazil's *Sistema de Informação de Agravos de Notificação* (SINAN) is a crucial source for public-health research. Working responsibly with surveillance information requires more than downloading a dataset: the source, notification system, data dictionary, reporting year, case definition and disclosure risks all matter.

**SINAN MCP** is an independent open-source project using the **Model Context Protocol (MCP)** to make official references and scientific limitations easier to inspect. It keeps documentary evidence, fictional software demonstrations, and restricted research workflows explicitly separate.

| **Discover** | **Prototype** | **Investigate** |
|:---|:---|:---|
| Find curated references to notifiable conditions, official portals and supporting documentation. | Explore a read-only MCP demonstration with deliberately fictional tuberculosis records. | Use separate local tools for imports, diagnostics and experimental methods, subject to human review. |

## Overview for reviewers

**What the project does:** it catalogues selected official SINAN reference pages and runs a read-only public MCP demonstration with fictitious TB records. For Zika and tuberculosis, a documentary matrix records 57 field identifiers from seven official PDF instruments.

**What is being requested:** independent readers can evaluate clarity, documentary field transcriptions, methodology, or privacy controls. The [external review guide](docs/instruments-2024/EXTERNAL_REVIEW.md) explains what to check and how to submit attributable findings. The [technical evidence protocol](docs/instruments-2024/REVIEW_PROTOCOL.md) contains source URLs, fixed hashes, page counts and open scientific questions.

**What is not established:** the 2024 dataset layouts have not been matched to the documents; epidemiological semantics and independent human reviews remain pending. Passing CI does not authorize research with actual patient records.

## What is available

| Capability | Current implementation | Important boundary |
|---|---|---|
| **Source discovery** | Official-source links and a catalogue with **14 internal condition aliases** | Catalogue entries do not prove that a usable dataset exists |
| **MCP interface** | Python-based tools for metadata, descriptions and synthetic examples | Public service never queries the local research database |
| **Synthetic demonstration** | Deterministic fictional TUBE/2024/PI records | Not real notifications, incidence, prevalence or patient counts |
| **Local research toolkit** | Administrative commands for file discovery, ingestion and data diagnostics | Must run in a controlled local environment |
| **Research methods** | Experimental local fairness and aggregate-review utilities | No officially validated predictive model or indicator is provided |
| **Documentation and tests** | Python test suite, CI matrix, security guidance and contribution policy | Passing tests is not a scientific, privacy or security certification |

A disease name appearing in the catalogue does **not** mean all its historical files, dictionaries or indicators are supported. See [catalogue scope](docs/MULTI_AGRAVO_CATALOG.md).

## Architecture

The public demonstration and the private research workflow are intentionally separate.

```mermaid
flowchart TB
  subgraph PUBLIC["Public MCP preview — synthetic only"]
    A["MCP client"] --> B["Read-only public_server.py"]
    B --> C["Source references<br/>and condition catalogue"]
    B --> D["Fictional TB demonstration"]
  end

  subgraph LOCAL["Private research — local operator"]
    E["Researcher / data steward"] --> F["Administrative CLI / local MCP"]
    F --> G["Local SQLite and research files"]
    F --> H["Quality checks and<br/>experimental audits"]
  end

  H -. "Requires separate human assessment" .-> I["Scientific, provenance<br/>and privacy review"]
  I -. "Not an automatic release" .-> J["Potential approved outputs"]

  classDef public fill:#eaf5f7,stroke:#0e7490,color:#0f172a;
  classDef local fill:#f2ecff,stroke:#7c3aed,color:#1f1637;
  classDef gate fill:#f8fafc,stroke:#64748b,color:#0f172a;
  class B,C,D public;
  class F,G,H local;
  class I,J gate;
```

**The public service has no route to private SQLite files, PySUS ingestion or row-level records.** Its demonstration data are generated by the application itself. Local operations require separate choices and controls. A future real-data publication workflow is **not** enabled merely by importing files or obtaining a test result.

## Get started

Requires **Python 3.11+** and Git. These commands create **synthetic demonstration data**, not an official SINAN dataset.

<details open>
<summary><strong>Windows PowerShell</strong></summary>

```powershell
git clone https://github.com/miscrapha-DELTA-IA/SINAN-MCP.git
cd SINAN-MCP

py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m sinan_mcp demo
.\.venv\Scripts\python.exe -m pytest -q
```

</details>

<details>
<summary><strong>macOS / Linux</strong></summary>

```bash
git clone https://github.com/miscrapha-DELTA-IA/SINAN-MCP.git
cd SINAN-MCP

python3.11 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m sinan_mcp demo
.venv/bin/python -m pytest -q
```

</details>

### Run a local MCP demonstration

After creating the synthetic database:

```bash
python -m sinan_mcp --db ./data/sinan-demo.sqlite3 servir
```

This command starts the **local stdio MCP server**. Configure your chosen MCP client to launch it with the appropriate absolute Python and database paths. Do **not** expose the local server on a public network. See the [Windows ChatGPT connector guide](docs/CHATGPT_TUNNEL_WINDOWS.md) and [security policy](SECURITY.md).

## Public synthetic preview

| Resource | Endpoint |
|---|---|
| **MCP Streamable HTTP** | [sinan-mcp-public-preview.onrender.com/mcp](https://sinan-mcp-public-preview.onrender.com/mcp) |
| **Service health check** | [sinan-mcp-public-preview.onrender.com/health](https://sinan-mcp-public-preview.onrender.com/health) |
| **Public-service rules** | [Launch and privacy disclosure](docs/PUBLIC_DISCLOSURE.md) |
| **Product information (`websiteURL`)** | [Sobre o projeto](https://sinan-mcp-public-preview.onrender.com/sobre) |
| **User support (`supportURL`)** | [Suporte e contato](https://sinan-mcp-public-preview.onrender.com/suporte) |
| **Privacy policy (`privacyPolicyURL`)** | [Política LGPD](https://sinan-mcp-public-preview.onrender.com/privacidade) · [conformidade em acompanhamento](docs/PRIVACY_RELEASE_GATE.md) |
| **Service terms (`termsOfServiceURL`)** | [Termos de Uso](https://sinan-mcp-public-preview.onrender.com/termos) |
| **Listing review preparation** | [URLs e requisitos ainda pendentes](docs/PUBLIC_LISTING_URLS.md) |
| **Portable plugin package (preflight only)** | [Manifestos, ZIP e portões de revisão](docs/PUBLIC_PLUGIN_PACKAGE_PREFLIGHT.md) |

The preview is hosted separately, with **synthetic records only**, and may take time to respond after inactivity on free hosting. Endpoint availability can change; a link is not an uptime guarantee.

**Examples of public MCP tools**

```text
pesquisar_agravos("tuberculose", limite=5)
descrever_agravo("TUBE")
listar_fontes_oficiais()
listar_agravos()
```

**Public documentary instrument references (`0.4.0a6`):** `descrever_agravo("ZIKA")` and `descrever_agravo("TUBE")` expose the immutable PDF source URLs, byte SHA-256 checks, observed versions and a **documentation-only** list of field names/cited pages. `pesquisar_agravos` adds a compact evidence summary. Neither route validates the 2024 data release, imports microdata, provides epidemiological statistics or represents an independent scientific approval.\n\n**Zika/TB 2024 documentary validation (pending independent review):** [7 official PDF source identities, 57 field metadata rows, byte-integrity audit and 3-person review protocol](docs/instruments-2024/REVIEW_PROTOCOL.md). This pack contains no data records, has no approved 2024 dataset concordance, and is not authorization to publish epidemiological indicators.\n\n**Evidence-tracked documentary catalogue (v1):** the 14 example condition entries now link to **17 individually identified institutional pages**, with source type, dated curation, limitations and a research checklist. Accent-tolerant search supports curated synonyms and typo suggestions; no clinical dictionary or real dataset has been verified or imported. See [documentary catalogue and provenance](docs/DOCUMENTARY_CATALOG_V1.md).

The public demonstration also includes narrow numeric examples for a **fictional** TUBE/2024/PI dataset. Any returned counts must be interpreted solely as software demonstration output, never as evidence about real populations.

## Project status

This is a **research prototype**, not a completed epidemiological data service.

| Workstream | Current status |
|---|---|
| Public reference catalogue and synthetic MCP demo | **Implemented** |
| Local import, diagnostics and experimental analysis | **Prototype** |
| Real-data metrics approved for public release | **None** |
| Independent epidemiological and privacy validation | **Required** |
| General-purpose disease coverage | **Not established** |
| Clinical or government use | **Out of scope** |

**Zika/TB documentary scope:** seven source-locked official PDFs and 57 field-code occurrences are now documented on the default branch. The 37 Zika fields, 15 selected TB fields and five common notification fields are **not** a verified 2024 export schema. Independent semantic, version-concordance and privacy reviews are still required. See the [review protocol](docs/instruments-2024/REVIEW_PROTOCOL.md).

Read the [epidemiological interpretation guide](docs/EPIDEMIOLOGY.md) before using any aggregate or exploratory measure in research.

## Security and research ethics

The project is designed to distinguish **reference discovery**, **local scientific work** and **potential publication**.

- **No patient records in GitHub or CI.** Tests use synthetic fixtures.
- **No real clinical dataset in the public preview.** No public row-level interface or arbitrary SQL.
- **Private datasets remain the operator's responsibility.** Local projections may contain quasi-identifiers; a reduced set of fields is not proof of anonymization.
- **Small-cell suppression is not a privacy guarantee.** Linkage and differencing risks require independent assessment.
- **No automatic endorsement.** Importing a file, checking a hash or reviewing a dictionary does not certify an epidemiological result.

Security concerns should be reported privately to maintainers, without including sensitive health information. See [SECURITY.md](SECURITY.md).

## Documentation

| Start here | What you will find |
|---|---|
| [Documentation hub](docs/README.md) | Scope, status, evidence, safety and technical navigation |
| [External review guide](docs/instruments-2024/EXTERNAL_REVIEW.md) | How to inspect sources and return a verifiable review |
| [Zika/TB evidence protocol](docs/instruments-2024/REVIEW_PROTOCOL.md) | Seven official PDFs, locked hashes, 57 field tokens and pending approvals |
| [Complete Portuguese README](docs/pt-BR.md) | Project overview in Portuguese |
| [Condition catalogue](docs/MULTI_AGRAVO_CATALOG.md) | Scope, sources and internal aliases |
| [Epidemiological interpretation](docs/EPIDEMIOLOGY.md) | Definitions, denominators and limitations |
| [Public preview and disclosure](docs/PUBLIC_DISCLOSURE.md) | Synthetic-data boundary and service notice |
| [Technical E2E and deployment baseline](docs/TECHNICAL_CONSOLIDATION_E2E.md) | Public MCP contract, tests and verified Render revision |
| [Local research and release safeguards](docs/AGGREGATE_PUBLICATION.md) | Candidate aggregates and independent review requirements |
| [Predictive fairness protocol](docs/FAIRNESS_PROTOCOL.md) | Exploratory offline assessment and limitations |
| [Security policy](SECURITY.md) | Data handling, threat boundaries and deployment precautions |
| [Contributing](CONTRIBUTING.md) | How to propose changes with reproducible evidence |
| [Historical technical notes](docs/TECHNICAL_README_ARCHIVE.md) | Archived detailed implementation context; not current validation status |

## Roadmap

- [x] Public, isolated, synthetic-only MCP demonstration
- [x] Source-reference catalogue for multiple notifiable conditions
- [x] Local administrative tooling and automated tests
- [ ] Independently reviewed, year-specific data dictionaries
- [ ] Reproducible source and release provenance across supported conditions
- [ ] Independently assessed privacy and epidemiological publication gates
- [ ] Research-grade evaluation of reliability, usability and limitations

These are **research milestones**, not delivery commitments or claims that real epidemiological services will be released.

## Contributing

Contributions are especially welcome in documentation, reproducible tests, epidemiological semantics, dictionary curation, data provenance, privacy engineering and MCP interoperability.

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
2. Start with an issue describing the use case, source or reproducible problem.
3. Submit focused changes using **synthetic fixtures only**; document scientific assumptions and limitations.

If the project is useful for your work, **star the repository**, share it with collaborators and help improve its scientific rigor. Stars support discovery; they are not evidence of scientific validity.

## Public-preview security operations

Security hardening is deployed in the **synthetic-only** public Render preview (2026-11-04, commit `3ac1db9`). Protections include per-process admission limits, cross-platform dependency audits and a hash-pinned runtime build. HTTPS smoke checks passed after deployment. A read-only [scheduled public smoke workflow](.github/workflows/public-live-smoke.yml) monitors the fictional MCP contract; scheduling is best effort and does not imply immediate alerts or clinical-data approval. Read [operational safeguards](docs/SECURITY_OPERATIONS.md), [branch protection](docs/BRANCH_PROTECTION.md) and [Render verification checklist](docs/RENDER_SECURITY_VERIFICATION.md).

## License and attribution

Original project code is licensed under the [MIT License](LICENSE). Optional third-party dependencies may carry separate licensing obligations.

**Independent open-source research project. Not affiliated with, endorsed by or operated by Brazil's Ministry of Health, DATASUS or SINAN.**

<div align="center">
  <sub>Built for reproducibility, transparency and responsible epidemiological research.</sub>
</div>