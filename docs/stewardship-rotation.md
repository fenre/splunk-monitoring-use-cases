# Stewardship rotation runbook

> Operational guide for the §P14 weekly per-category stewardship-rotation
> reminder. Pairs with [`docs/stewardship-digest.md`](stewardship-digest.md)
> (the global weekly digest) and with the per-category scorecard
> drill-downs at [`docs/scorecard.md#category-drill-downs`](scorecard.md#category-drill-downs).

## What it is

Every Monday at 08:30 UTC,
[`.github/workflows/stewardship-rotation.yml`](../.github/workflows/stewardship-rotation.yml)
runs and:

1. Picks one of the 23 content categories by computing
   `cat_num = (iso_week % 23) + 1`. Over a 23-week cycle every
   category is picked exactly once, so each owner receives
   ~2.3 reminders per year.
2. Reads the category's CODEOWNERS owner(s) from
   [`.github/CODEOWNERS`](../.github/CODEOWNERS) and its current
   quality scorecard from `dist/scorecard.json` (rebuilt on every
   workflow run).
3. Opens — or comments on, if a matching open issue already exists
   for the same ISO week — a GitHub issue assigned to the owner(s)
   with the scorecard drill-down link, current grade / composite
   score, dimension breakdown, and a stewardship checklist.

The picker itself is a stdlib-only Python verb invocable from a
shell:

```bash
PYTHONPATH=src python3 -m splunk_uc pick-rotation-category
```

Add `--week N --year YYYY` to pick for a specific ISO week. Add
`--write-issue-body PATH` to render the markdown body to a file.

## Why two stewardship workflows?

There are two complementary surfaces:

| Workflow | Cadence | Scope | Issue model |
|----------|---------|-------|-------------|
| [`stewardship.yml`](../.github/workflows/stewardship.yml) | Mondays 08:00 UTC | **Global** — release-over-release deltas, staleness counts, regression flags across every category | **One** tracking issue, appended-to weekly |
| [`stewardship-rotation.yml`](../.github/workflows/stewardship-rotation.yml) | Mondays 08:30 UTC | **Per-category** — picks one of 23 categories each week and pings its owner(s) | **One issue per (category, week)** combination |

The 30-minute schedule offset is deliberate: both notifications land
in the maintainer's first triage window of the week, but the global
digest arrives first so the per-category ping reads as an
expansion-on rather than a competing thread.

## Operating the rotation

### Routine maintenance

You don't have to do anything. The cron fires every Monday. If you
want to know what week's pick is going to be without waiting, run
the picker locally:

```bash
make build
PYTHONPATH=src python3 -m splunk_uc pick-rotation-category --week $(date -u +%V)
```

The JSON output tells you which category will be picked, who the
owners are, and what the current quality posture looks like.

### Manual catch-up

If the scheduled run was missed (e.g. GitHub Actions outage),
re-trigger it from the Actions UI:

* Workflow → "Stewardship rotation reminder" → "Run workflow"
* Leave `week` / `year` blank to use the current ISO week
* Or specify a back-dated week to backfill

If a future week needs testing, set `dry_run: true` so only the
markdown body lands in the workflow log + uploaded artefact —
no GitHub issue is created.

### Adding or renaming a category

The picker reads three surfaces in lockstep:

1. **The content directory** (`content/cat-NN-<slug>/`) — canonical
   source for the slug.
2. **The CODEOWNERS row** (`/content/cat-NN-<slug>/   @owner` in
   [`.github/CODEOWNERS`](../.github/CODEOWNERS)) — canonical
   source for the owner.
3. **The scorecard entry** (`dist/scorecard.json` `categories[].cat_num`)
   — canonical source for composite / dimensions / counts.

When adding a category:

1. Create the directory `content/cat-NN-<slug>/`.
2. Add the matching CODEOWNERS row (the structural test
   [`tests/build/test_codeowners.py`](../tests/build/test_codeowners.py)
   blocks the PR if you forget).
3. Bump `EXPECTED_CATEGORY_COUNT` in
   [`src/splunk_uc/tools/pick_rotation_category.py`](../src/splunk_uc/tools/pick_rotation_category.py)
   from 23 to 24 (or whatever the new total is) so the picker stops
   emitting the "fewer categories than expected" warning.
4. Update the per-category drill-down section of `docs/scorecard.md`
   (the build pipeline regenerates this — `make build`).

When renaming a category, the slug changes, which means:

* The CODEOWNERS path needs updating in the same PR.
* The scorecard drill-down anchor changes too (the auto-generated
  anchor matches the slug).
* Existing open rotation issues for the old slug stay tagged with
  the old label; close them by hand after merging.

### Assigning new owners

The picker's "owners" line in the rendered issue body is whatever
CODEOWNERS says. Adding a co-maintainer is a one-line CODEOWNERS
edit. The picker handles multi-owner lines transparently — every
`@`-prefixed token on the matching row is rendered into the issue
body.

## Algorithm rationale

Why `(iso_week % 23) + 1`?

* **Deterministic.** Same week → same category. The workflow's
  per-week label keeps issues idempotent.
* **Calendar-independent.** No epoch anchor to drift. Year boundaries
  don't reset the cycle: 52 % 23 = 6, so the year-over-year shift
  is just 6 categories per year — every category still gets its
  fair share.
* **Coprime with year length.** 52 / 23 ≈ 2.26 (and 53 / 23 ≈ 2.30),
  so the rotation never lands on the same calendar week → category
  pairing for years on end. Each category gets pinged in different
  parts of the year over time.
* **Cycle length matches CODEOWNERS row count.** If the rotation
  cycled over more weeks than there are categories, some categories
  would never come up; if fewer, some would come up twice in a
  cycle. Locking the modulus to the category count means every
  reviewer gets the same volume of attention.

## Troubleshooting

| Symptom | Probable cause | Fix |
|---------|----------------|-----|
| Workflow fails at "Build site so dist/scorecard.json is fresh" | `make build` is broken | Look at the build log — usually a content-tier audit failure. Fix locally then re-run. |
| Picker prints "scorecard.json has no entry for cat_num=N" | `dist/scorecard.json` is stale relative to `content/` | Re-run `make build` upstream of the picker. In CI this should never happen because the build step runs first. |
| Picker prints "warning: found N category directories under content/, expected 23" | A category was added/removed but `EXPECTED_CATEGORY_COUNT` wasn't bumped | Update the constant in `src/splunk_uc/tools/pick_rotation_category.py`. |
| Issue body has "_(no CODEOWNERS owner found …)_" | A new category was added without a CODEOWNERS row | Add the row to `.github/CODEOWNERS`. The structural test in `tests/build/test_codeowners.py` should have caught this in the original PR. |
| Two issues open for the same ISO week | Race between cron and a manual dispatch | The workflow's concurrency group should prevent this; if it happens, close the older issue manually. |

## See also

* [`docs/stewardship-digest.md`](stewardship-digest.md) — global
  weekly stewardship digest runbook.
* [`docs/scorecard.md#category-drill-downs`](scorecard.md#category-drill-downs)
  — the canonical per-category quality view.
* [`docs/workflow-audit.md`](workflow-audit.md) — full GitHub Actions
  workflow inventory.
* [`docs/ci-architecture.md`](ci-architecture.md) — per-workflow
  long-form description.
* [`docs/health-check-2026-progress.md`](health-check-2026-progress.md)
  — §P14 status row and historical drift ledger.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

_No external sources are cited inline in this document and no repository documents currently link to it._

<!-- END-AUTOGENERATED-SOURCES -->
