# sample-data/

JSON fixtures used as **control-test evidence** for compliance-oriented use cases, especially in category 22. They are distinct from the [`samples/`](../samples/README.md) tree (per-UC Splunk log fixtures + manifests). Their split — and the contract that this tree owns compliance-evidence fixtures while `samples/` owns raw-event SPL fixtures — is ratified in [ADR-0010](../docs/adr/0010-sample-and-sample-data-co-exist.md).

## What exists today

- **`uc-22.2.*-fixture.json`** — Evidence-oriented records using top-level **`positive`** and **`negative`** arrays (metadata such as evidence IDs, owners, and gap status).
- **`uc-22.35.*` through `uc-22.49.*`** — Fixtures that follow a second shape: top-level **`events_positive`** and **`events_negative`** (often empty placeholders with a `$comment` noting future sandbox validation). Some files in this range instead use richer nested objects (e.g. **`positiveCase`** / **`negativeCase`** with synthetic event streams and expected alert behavior).

Roughly **97** `*-fixture.json` files live in this directory.

## References vs files on disk

Many `content/cat-22-regulatory-compliance/UC-*.json` entries set `controlTest.fixtureRef` to paths like `sample-data/uc-<id>-fixture.json`. A large share of those paths **do not yet have a matching file**—the references describe intended evidence, not guaranteed artifacts. Conversely, several committed fixtures are **not referenced** by any UC JSON today. Replacing stubs and aligning `fixtureRef` values is follow-on work.

## Schema summary

Two conventions appear in this folder:

1. **`positive` / `negative`** — Arrays of evidence or control objects (see `uc-22.2.*`).
2. **`events_positive` / `events_negative`** — Arrays intended for event-level positive/negative cases; many placeholders are empty pending content generation (see `uc-22.35.*`–`uc-22.49.*`, and related variants with nested case objects).
