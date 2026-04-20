# `regulations-watch.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released  | Stability | Notes                                                                                                  |
|---------|-----------|-----------|--------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-Q1   | stable    | Initial release for Phase 5.3. Records the externally-published regulatory artefacts the project depends on, the strategy used to detect updates, and the last-observed state. Consumed by the hermetic `--check` audit; refreshed weekly by the `regulatory-watch` workflow. |

## Stability commitment

`x-stability: stable` — no breaking changes within v1 major.

## Migration plan

See [`docs/schema-versioning.md`](../../docs/schema-versioning.md#migration-guides).
