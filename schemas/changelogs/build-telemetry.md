# `build-telemetry.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes                                                                                                                                                                              |
|---------|----------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-Q2  | stable    | Initial release. Defines `dist/build-telemetry.json` — per-stage wall-clock timings emitted once per non-reproducible build by `tools/build/build.py`. Adding a new stage is non-breaking; renaming or removing the `schema_version` field is a major bump. |

## Stability commitment

`x-stability: stable` — no breaking changes will be made within the v1
major. Adding new stages (additive) is allowed; renaming or removing
fields requires a major bump and a parallel `/schemas/v3/` schema.
