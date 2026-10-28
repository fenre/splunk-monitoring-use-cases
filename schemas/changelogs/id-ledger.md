# `id-ledger.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes |
|---------|----------|-----------|-------|
| 1.1.0   | v8.26.0  | stable    | Adds the append-only `fingerprintRevisions` history (content fingerprint + catalogue version) to each entry. `generate-id-ledger` fails when the history would shorten. |
| 1.0.0   | v8.26.0  | stable    | Initial release. Validates `data/id-ledger.json`: every UC identifier ever issued, its status, and its current content fingerprint. Removed identifiers are never reissued. See [ADR-0016](../../docs/adr/0016-permanent-uc-identifiers.md). |

## Stability commitment

`x-stability: stable` — downstream consumers rely on identifier permanence.
Fields are only added; existing fields are not renamed or removed.
