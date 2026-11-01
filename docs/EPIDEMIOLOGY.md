# Epidemiological interpretation and supported scope

The SINAN MCP is an **exploratory, aggregated database interface**. Its output is a count of imported records by **file-year** rather than a certified count of unique notified cases in a diagnosis cohort. File-year ≠ year of diagnosis, notification, cure, or treatment completion.

## Pilot diseases

- **TUBE** (tuberculosis): generic demographic counts; an **exploratory** share of records with closure code 2 or 10 among closure codes 1, 2 and 10.
- **DENG** (dengue): generic demographic counts only. No dengue incidence, positivity, hospitalization, death, or other clinical indicator is calculated.

Other four-letter codes may be ingested through the administrator CLI. There is no claim that their dictionaries, field mappings or epidemiological definitions have been validated. Both pilot diseases must be verified against the applicable year-specific public-health documentation before scientific reporting.

## Why the TB ratio is **not** an official indicator

The official Brazilian Ministry of Health's *Caderno de Indicadores da Tuberculose* specifies selection of cases, calendar references, outcome rules, and detailed implementation instructions. Its official indicator definitions cannot be reconstructed from the limited seven-column projection of this project. In particular, our denominator excludes many outcomes, and our time reference is file-year. We have not incorporated cohort definition, type-of-entry criteria, clinical form, diagnosis year, linkage, or longitudinal deduplication.

Do **not** compare the exploratory ratio to the Ministry's official targets or publish as an official treatment abandonment rate. This requires a separate, scientifically validated module, implemented using the published formulas and versioned disease dictionaries, and verified against known reference tabulations.

Sources:
- [Brazilian Ministry of Health — Caderno de Indicadores da Tuberculose](https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/svsa/tuberculose/caderno-de-indicadores-da-tuberculose)
- [SINAN — Tuberculose](https://portalsinan.saude.gov.br/tuberculose)
- [PySUS — curated column metadata](https://pysus.readthedocs.io/en/latest/guides/columns.html)

## Status of validation

- Verified by automated tests: projection excludes direct identifiers, synthetic TUBE/DENG demographic groupings, one-year/one-UF tool disclosure controls, atomic import rollback, administrative completeness diagnostics.
- Supported by API documentation, but not verified against live sources in this runtime: PySUS 2.11+ FTP catalog discovery and streamable Parquet/CSV downloads.
- Not established: official indicator equivalence, validity of all disease-year mappings, external privacy safety, remote server deployment.

## Quality assessment

The local administrator can run:

```sh
python -m sinan_mcp --db ./data/sinan.sqlite3 diagnosticar-base --agravo TUBE --ano 2024
```

This produces exact total counts and percentages of missing/ignored demographic fields. It is intentionally **not an MCP tool** and must not be exposed through remote APIs.
