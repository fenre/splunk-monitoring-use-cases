# Stewardship digest (on-demand)

> Repo-overhaul plan §P8 step 4 — landed 2026-05-09. The weekly
> scheduled workflow was retired 2026-05-17 (drift ledger #19 in
> `docs/health-check-2026-progress.md`); the generator is preserved
> and still produces the same JSON + markdown twin on demand.

The **stewardship digest** is a small JSON + markdown twin emitted by
`python -m splunk_uc generate-stewardship-digest` that distils three
recurring stewardship questions into a single artefact:

1. **What changed in the catalogue since the last release?**
   Counts, quality-tier mix, coverage axes, and movers in the
   regulations / MITRE / CIM / equipment leaderboards.
2. **Which audits are warning but not blocking?**
   Soft-failable audits (today only
   [`audit_roadmap_consistency.py`](../scripts/audit_roadmap_consistency.py))
   are gathered into the digest so they cannot rot silently.
3. **Which UC sidecars are overdue for review?**
   Every `content/cat-*/UC-*.json` whose `lastReviewed` is older than
   `--stale-threshold-days` (default 180) is surfaced, with the
   longest-overdue 20 UCs called out by name.

The digest is **derived**: it is *not* committed to the repo. PR CI
smoke-tests the generator against
[`schemas/v2/stewardship-digest.schema.json`](../schemas/v2/stewardship-digest.schema.json)
to keep the schema honest.

## Artefacts

| Path | Purpose |
|---|---|
| `dist/stewardship-digest.json` | Machine-readable payload, schema-validated. |
| `dist/stewardship-digest.md` | Human-friendly twin (drop into release notes verbatim). |
| `schemas/v2/stewardship-digest.schema.json` | JSON Schema 2020-12 contract. |
| `src/splunk_uc/generators/stewardship_digest.py` (verb `generate-stewardship-digest`) | Stdlib-only generator. |
| `tests/scripts/test_generate_stewardship_digest.py` | 55 unit tests. |

## How to regenerate locally

```bash
make build               # ensure dist/metrics.json is fresh
make stewardship-digest  # writes dist/stewardship-digest.{json,md}
```

By default the generator stamps the digest with **today (UTC)** as
both `generatedAt` and `referenceDate`. CI fixtures pin it via
`--reference-date 2026-05-09` so two runs on different machines
produce byte-identical artefacts.

## Reproducibility contract

Given the same inputs and the same `--reference-date`, the JSON is
byte-identical across runs and machines:

* `generatedAt` is derived from `--reference-date` at fixed UTC
  midnight, never from wall-clock `now()`.
* `staleUseCases` ages are computed as
  `referenceDate - sidecar.lastReviewed`, so a frozen reference date
  freezes the staleness calculation too.
* Top-mover sort breaks ties alphabetically by name; stale-UC sort
  breaks ties by UC id. Both are total orders, so output is stable.

When `--reference-date` is omitted (manual local runs) the artefact
is stamped with today's UTC date and is therefore **not**
reproducible across days. That is fine for ad-hoc use, but CI fixture
runs **must** pass an explicit reference date.

## Reading the markdown

```text
# Stewardship Digest

_Generated 2026-05-09T00:00:00Z (reference date: 2026-05-09)_

## Catalogue counts

| Field | Current | Previous | Delta |
|-------|---------|----------|-------|
| useCases | 7677 | 7548 | +129 |
| categories | 23 | 23 | +0 |
| ...

## Quality tier mix
| ...

## Coverage shifts
| ...

## Top movers: regulations
| ...

## Open audit warnings
- **audit_roadmap_consistency** (warn): ROADMAP "Current release"
  heading does not match VERSION (...)

## Stale use cases (4823 above 180-day threshold)

| ID | Title | Status | Last reviewed | Age (days) |
| ...
```

When `previous` is null (first release after the digest landed), the
"Previous" and "Delta" columns render as `—` and the top-movers
sections are omitted.

## How the PR CI gate works

The PR `validate.yml` job runs:

```bash
PYTHONPATH=src python3 -m splunk_uc generate-stewardship-digest \
  --reference-date 2026-05-09 \
  --out /tmp/stewardship-digest-ci
python3 -c '... jsonschema.Draft202012Validator(...)...'
```

This is purely a smoke test: it ensures the generator still
runs end-to-end against the live `dist/metrics.json` and that the
output validates. It deliberately does **not** commit the digest —
the digest is a derived artefact, refreshed on a schedule.

## Field reference

See the JSON Schema:
[`schemas/v2/stewardship-digest.schema.json`](../schemas/v2/stewardship-digest.schema.json).

Key invariants enforced by the schema:

* `schema_version` is pinned to `"1.0.0"`. Bump it the same PR you
  break the contract.
* `previous` is `null` only on the first release ever observed; in
  that case all `deltas.*` are zero and `topMovers.*` are empty
  arrays.
* `qualityShifts.previous` and `coverageShifts.<axis>.previousCount`
  are absent (not zero) when `previous` is null — schema uses
  `anyOf [{...}, {type: "null"}]` for `qualityShifts.previous`.
* `staleUseCases.thresholdDays >= 1`.
* `staleUseCases.topStale` is capped at 20 entries; `topMovers.<axis>`
  at 10.
* All UC ids follow `X.Y.Z` (no `UC-` prefix in the field; the
  prefix is display-only).

## When to bump `schema_version`

Bump from `1.0.0` to `1.1.0` when adding a new optional field; bump
to `2.0.0` when removing a field, renaming a field, or tightening a
type. Update the schema, the generator, **and** every test fixture
that mentions the constant in the same PR.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Splunk Common Information Model Add-on Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CIM

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

### Cited by

- [`docs/build-artefacts-reference.md`](build-artefacts-reference.md)

<!-- END-AUTOGENERATED-SOURCES -->
