# Metrics history — release-time trend snapshots

> Repo-overhaul plan §P8 step 2 (2026-05-09)

`dist/metrics.json` is regenerated on every build. It carries the
catalogue's top-line counts, quality tier distribution, depth
percentiles, coverage percentages, and Top-N leaderboards. Without a
release-time snapshot, that file is *ephemeral*: the next build
overwrites it and we lose the historical record.

This page documents the snapshot system that captures one permanent
metrics file per release into `data/metrics-history/<VERSION>.json`,
plus the index that lists every release ever captured.

## What gets committed

```
data/metrics-history/
├── index.json              # sorted list of every snapshot, newest first
├── 8.0.0.json              # snapshot for v8.0.0
├── 9.3.0.json              # snapshot for v9.3.0 (when released)
└── ...
```

Each `<VERSION>.json` is a **verbatim** copy of `dist/metrics.json`
at release time — no synthetic fields are added. This guarantees
the snapshot validates against the same
`schemas/v2/metrics.schema.json` (which has
`additionalProperties: false`) as the live build artefact, and
downstream tooling can consume snapshots with the same parser it
uses for `dist/metrics.json`. The snapshot's existing `generatedAt`
field already records the build time (frozen to git commit time in
reproducible builds), so we have no need for a separate
"capturedAt".

`index.json` is recomputed from disk on every `--write`; never edit
it by hand.

## Why a committed snapshot, not a database / live query

A live "fetch the previous build's metrics from CI artifacts" flow
is non-deterministic (artifact retention drops to zero after 90
days; CI logs disappear faster). A committed snapshot makes the
release-over-release diff:

* **Self-evident in code review** — a reviewer can `git diff` the
  snapshot in the same PR that bumps `VERSION`.
* **Permanent** — there is no separate retention policy that can
  silently delete history.
* **Stdlib-only** — no extra dashboard service, no auth tokens, no
  upstream metadata edits we don't control.

The trade-off is that snapshots add ~5 KB per release to the repo
weight. Over 100 releases that is ~500 KB; immaterial against the
~50 MB of catalog content.

## Release workflow (maintainers)

When you bump `VERSION` for a release:

```bash
# 1. Bump VERSION + CHANGELOG + index.html release notes
echo "9.3.0" > VERSION
${EDITOR:-vi} CHANGELOG.md index.html

# 2. Rebuild dist/ so dist/metrics.json reflects the catalogue
#    state being shipped.
make build

# 3. Capture the snapshot. This writes
#    data/metrics-history/9.3.0.json and refreshes
#    data/metrics-history/index.json.
make snapshot-metrics

# 4. Commit both alongside the version bump. CI's
#    `audit-metrics-snapshot` gate will reject the PR if you forget.
git add VERSION CHANGELOG.md index.html \
        data/metrics-history/9.3.0.json \
        data/metrics-history/index.json
git commit -m "release: bump VERSION to 9.3.0"
```

`make snapshot-metrics` is **idempotent**: running it twice on the
same release produces identical files (the `capturedAt` timestamp
is recomputed but the rest is byte-stable).

## CI gate

Workflow: `.github/workflows/validate.yml` — job `lint` — step
**"Metrics history snapshot audit (release-time trend record)"**.

The gate runs `python3 scripts/snapshot_metrics.py --check` and
fails the PR if any of these hold:

1. `data/metrics-history/<VERSION>.json` is missing.
2. The committed snapshot is malformed (not a JSON object,
   missing `schema_version`, missing `catalogueVersion`, missing
   `counts.useCases`, or wrong `$schema` reference).
3. The committed snapshot's `catalogueVersion` does not match
   `VERSION`.
4. `data/metrics-history/index.json` is out of sync with the
   actual snapshot files on disk.
5. **Only when** `dist/metrics.json` is also present (e.g. in a
   build job) — the live `schema_version` and committed
   `schema_version` disagree.

The gate **does not** assert per-field equality between the live
build and the committed snapshot. Content edits change metrics on
every PR; gating on numeric equality would just be noise. The
contract is "every release has a permanent record", not "every PR
matches the latest record".

## What the snapshot guarantees downstream

Because snapshots are well-typed (schema-validated against
`schemas/v2/metrics.schema.json`) and the index is sorted, downstream
consumers can rely on:

* **Stable shape** — every snapshot has the same JSON keys at the
  same paths regardless of release date. A new top-level section
  only ever appears with a `schema_version` bump.
* **Sorted history** — `data/metrics-history/index.json#snapshots`
  is sorted by semver descending. The first entry is always the
  newest release.
* **Cheap headline numbers** — `index.json` carries
  `useCases`, `schemaVersion`, `generatedAt`, `version` per release,
  so a dashboard can plot trend lines without fetching every
  snapshot individually.

## Adding a new metric to the schema

When adding a new top-level section to `metrics.json` (for example,
a new `cveTaxonomy` block):

1. Add the field to `tools/build/render_metrics.py:build_metrics`.
2. Add the field's contract to `schemas/v2/metrics.schema.json`.
3. Bump `schema_version` (in both `render_metrics.py` and the
   schema's default value).
4. Document the new field in this file and in the changelog entry
   covering the bump.
5. Re-run `make build && make snapshot-metrics` so the next
   committed snapshot picks up the new field for the current
   `VERSION`. The check gate's "schema_version mismatch" rule will
   otherwise fire on the next build.

If you want historical snapshots back-filled with the new field,
write a one-shot script under `scripts/migrations/` that loads
each `data/metrics-history/<VERSION>.json`, computes the new field
from a reproducible source, and writes it back. The fall-back when
back-fill isn't possible is to add the field as `optional` in the
schema for snapshots whose `schema_version` is older than the
current one.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Cited by

- [`docs/build-artefacts-reference.md`](build-artefacts-reference.md)

<!-- END-AUTOGENERATED-SOURCES -->
