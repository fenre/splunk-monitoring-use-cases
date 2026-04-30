# samples/

Per-use-case sample **log fixtures** and manifests for validating catalog SPL (Splunk search) against realistic raw events. This tree is separate from `sample-data/` (JSON compliance fixtures referenced by `controlTest.fixtureRef`).

## Layout

There is **one directory per use case**, named `UC-<full-id>` (for example `UC-1.1.1`, `UC-10.6.200`). As of the last index, **94** such directories exist, spanning **9** category prefixes: 1, 2, 3, 4, 5, 9, 10, 12, and 13.

```
samples/
├── _schema/
│   └── sample-manifest.schema.json    JSON Schema for manifest.yaml
└── UC-X.Y.Z/
    ├── manifest.yaml     UC id, index/sourcetype/source/host, timerange, expected counts/fields
    ├── positive.log      raw events for the scenario the UC should detect (newline-delimited)
    └── negative.log      optional counterexample events (distinct source in test harness)
```

Older docs sometimes mentioned `sample.jsonl`, `sample.csv`, or `expected.json`; the **current** convention is **`manifest.yaml` plus `positive.log` / `negative.log`**.

## Tooling

- **`scripts/samples_index.py`** — Validates manifests against `samples/_schema/sample-manifest.schema.json`, checks `uc_id` against `catalog.json`, and reports coverage tiers (manifest-only vs manifest + `positive.log`).
- **`scripts/run_uc_tests.py`** — For directories with `positive.log`, HEC-ingests fixtures into Splunk, runs the UC SPL from `catalog.json`, and asserts on `expected` in the manifest (optional `negative.log` for false-positive checks).

New UCs should add a `samples/UC-<id>/` tree when practical; missing fixtures reduce measured sample coverage in scorecards and audits.
