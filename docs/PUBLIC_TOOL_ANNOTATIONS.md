# MCP public preview — tool safety annotation justifications

**Scope:** `sinan_mcp.public_server`, the externally accessible, *synthetic-only* MCP. This is a developer/reviewer audit aid, **not** a clinical-data approval, privacy certification, or substitute for a live tool scan.

## Serialized MCP annotation contract

Every tool advertises the following *explicit* wire-format annotations under `tools/list[].annotations`:

| Annotation | Value | Rationale |
| --- | --- | --- |
| `readOnlyHint` | `true` | No tool modifies external resources, databases, files or user state. All responses derive from bundled static documentation/catalogues or deterministic fictional rows generated in memory. |
| `destructiveHint` | `false` | No tool has an update/delete/administrative operation. This hint is not an authorization boundary; it is informational (and redundant for read-only tools). |
| `openWorldHint` | `false` | The tool implementations are limited to code-bundled records and in-process computations; none performs HTTP retrieval, reaches external APIs or navigates arbitrary resources. Returning curated URLs as inert text does **not** fetch or access them. |

The hints describe **runtime tool behavior**, not the user's future actions (e.g. the user can independently open a reference URL). The public application is intentionally separate from the local/private research MCP.

## Per-tool justification

For **each** tool below, `readOnlyHint=true`, `destructiveHint=false` and `openWorldHint=false` apply. The explanation states why all three are accurate; each operates only within the application's closed, non-mutating public fixture/catalogue domain.

| MCP tool | Review justification (read-only, not destructive, closed-world) |
| --- | --- |
| `sobre_o_servidor` | Returns only hard-coded software identity, license/provenance and warnings; does not read or modify external state. |
| `listar_bases` | Returns a static inventory of one *fictional* TUBE demonstration; does not load any SINAN file, database or other system. |
| `listar_agravos` | Reads the code-bundled curated condition catalogue and adds a synthetic-only disclaimer; no network lookup or writes. |
| `listar_fontes_oficiais` | Returns a fixed list of official-source navigation links as **text**; it does not contact these sites or ingest their data. |
| `pesquisar_agravos` | Performs in-memory string matching over the bounded curated catalogue; does not search the web or change the index. |
| `descrever_agravo` | Returns documentation for one in-code condition alias; official URLs are inert metadata, not live external queries. |
| `descrever_campos` | Returns predefined descriptions of synthetic field codes; does not open or update a patient record or dictionary file. |
| `metodologia_abandono_tuberculose` | Returns static explanation and methodological limitations; no live epidemiological calculations or external access. |
| `contar_notificacoes` | Counts only **120 deterministic fictional rows** in memory under hardcoded TUBE/2024/PI restrictions; arbitrary requests fail closed without data access. |
| `proporcao_abandono_tuberculose` | Computes a fictional percentage from the same 120 in-memory rows; cannot fetch, modify or expose real outcomes. |

## Verification and future change control

1. Run the tests, particularly `test_public_mcp_tools_no_private_admin_routes`, which verifies the ten-tool inventory and each annotation in `Client.list_tools()`.
2. Verify JSON serialization exposes `readOnlyHint`, `destructiveHint`, `openWorldHint` with explicit boolean values, not omitted/default fields.
3. After an **authorized manual deployment**, run the established read-only public HTTPS smoke probe; then use the OpenAI submission tool scanner on the **actual deployed** endpoint.
4. If a tool starts fetching external data, touching mutable resources, enabling an open query, or consulting real records, its annotation must be re-evaluated and the public launch gate must **fail closed**. Do not silently retain these hints.
5. These hints are **not access controls** and do not prove scientific, security, or privacy approval. Maintain independent code isolation, Host/Origin restrictions, size limits, request budgeting and the ban on real SINAN data.

Source: https://developers.openai.com/plugins/deploy/submission-errors — `annotations_required`, `justification_required`.
