# `uc-id-migration.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes |
|---------|----------|-----------|-------|
| 1.0.0   | v8.26.0  | stable    | Initial release. Manifest under `data/uc-id-migrations/` required when a pull request changes more identifiers than the blast-radius threshold. Lists every add, remove, remap, and same-id fingerprint change and whether content identity is preserved. See [ADR-0016](../../docs/adr/0016-permanent-uc-identifiers.md). |

## Stability commitment

`x-stability: stable` — `audit-uc-id-migration-blast` reads these manifests;
fields are only added.
