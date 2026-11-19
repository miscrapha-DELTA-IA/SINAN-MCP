# Release V2 — security and evidence contract (design only, NOT enabled)

**Status: DESIGN_ONLY_RELEASE_DISABLED.** The legacy `load_approved_release` path is fail-closed in PR #72. This is a specification for independent scientific, privacy, provenance and publication approvals; it is not an attestation that any approval exists. No live real-data service is authorized.

## Why V1 was closed

The legacy `sinan-aggregates-v1` shape checks aggregate bounds and an SHA-256 but also accepts `source.status_informado == "final"` and free-form reviewer names/reference. Neither attests authentic official file edition, independent authorship, role or legally authorized publication. A user with file control could forge these strings. In addition, a package-level threshold is insufficient against inference from multiple overlapping releases. For these reasons `sinan_mcp.aggregate_contract.load_approved_release` now always rejects V1 real aggregate packages. The private research candidate workflow remains usable, and the deployed synthetic MCP is unchanged.

## Proposed V2 trust architecture

1. **Immutable candidate identity:** canonical JSON using strict schema `sinan-aggregates-v2`, unique release ID, exact `agravo/ano_do_arquivo/UF/dimensao`, category rules, countermeasure policy, SHA-256 of exact candidate bytes and a fixed description of what is being counted (records, not people or incidence).
2. **Provenance evidence:** signed record of official retrieval observation, source path, raw DBC bytes/hash, PySUS artifact bytes/hash, decoding/normalization implementation commit, four-field concordance result, variable list, schema/field widths, dictionary-source URL and publication/revision date, explicit temporal-compatibility decision. FTP SIZE/MDTM and local SHA-256 alone do not authenticate source or guarantee final administrative revision.
3. **Independent role attestations:** roles `provenance_technical`, `scientific`, `privacy`, `publication_authority` must sign the *same exact* release digest and linked provenance/dictionary/policy digest using a well-reviewed signature primitive (e.g. Ed25519). Require distinct authorized identities and role-specific valid keys with rotation/revocation. Text names in a JSON cannot substitute for signatures. One operator cannot self-approve all roles.
4. **Trusted authority registry:** maintain only reviewer *public* keys and authorized roles as a reviewed, protected deployment artifact. The server must **never** trust reviewer keys, roles or approval decisions supplied in the package itself or via casually changeable environment variables. Private signing keys must stay outside the repo, CI logs, local test data and LLM sessions.
5. **Publication ledger:** before a package can be served, review it against the complete prior release set (other years, geographic partitions, dimensions, versions and timing) and calculate residual disclosure risk from intersections or subtraction. This decision must be linked to the exact release digest, not a generic boolean.
6. **Security deployment:** use an isolated read-only service that can access only the approved static package and public trust registry. It must have no SQLite or microdata mount, DB credentials, dynamic SQL, PySUS downloader, import command, raw diagnostic files or general file-system selectors. Enforce HTTPS, rate limits, secure deployment reviews, immutable versions and a quick revoke path.
7. **Revocation and expiry:** revoked key, rescinded permission, stale dictionary or changed source hash must fail-closed; manifest and approval history should record reason and never silently auto-promote another version.
8. **Institutional/governance review:** cryptographic verification proves signatures of registered keys, **not** that a scientific judgment, consent basis, or legal authorization is substantively adequate. Human review and institutional responsibility remain mandatory.

## Required negative tests

- Unsigned package, arbitrary status `final`, fake reviewer strings or self-signed reviewer key => reject.
- Single signer for all roles, revoked signers, tampered attestations, stale provenance revision => reject.
- Hash mismatch, different projection set, unknown date/cohort, unmatched official file edition, missing dictionary compatibility => reject.
- Repeated release enabling subtraction, small/zero cells that can be differenced, unnecessary dimensions => reject.
- Relative filesystem path traversal, symlink to raw database, missing trust registry or disabled service => reject.
- Synthetic fixtures remain available and do not become real data by changing `tipo`.

## Operational gates and status

| Gate | State |
| --- | --- |
| V1 public real-data loader | **Fail-closed** |
| Private research candidate generation | Still available; unapproved |
| TUBE/2019 4-field technical concordance | Operator reported success |
| 2019 historical semantic compatibility | Not independently reviewed |
| Approved scientific/privacy/publication signatures | **None** |
| V2 trusted keys and revocation process | Not provisioned |
| V2 release activation | **Forbidden** |
| Existing public synthetic service | Unchanged |

**No operator command, `--status final` flag, report of passing tests or GitHub merge can itself authorize real-data release.** A separate, reviewed implementation and trusted authority provisioning are required.
