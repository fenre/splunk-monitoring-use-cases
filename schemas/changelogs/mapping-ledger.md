# `mapping-ledger.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released  | Stability | Notes                                                                                                  |
|---------|-----------|-----------|--------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-Q1   | stable    | Initial release for Phase 5.4. Content-addressable, append-structured ledger of every compliance mapping. Each entry is hashed independently; the ledger root is a Merkle SHA-256 over all sorted entry hashes. A detached signature (Sigstore via GitHub OIDC) binds the root to a specific workflow run, commit, and repository. |

## Stability commitment

`x-stability: stable` — the on-disk shape of a ledger entry is locked.
The Merkle hashing rule is part of the contract: entry hashes are
SHA-256 over the canonical JSON serialization (sorted keys, no
whitespace, UTF-8). The root hashes the sorted entry-hash list.

## Migration plan

If the canonical-form rule ever changes, ledger v1 stays online
indefinitely so historical signatures remain verifiable.
