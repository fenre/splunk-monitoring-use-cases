# Roadmap board sync

> **Status (2026-05-18):** automated structural + link gate is live in CI;
> the JSON snapshot is published as a workflow artifact on every push to
> `ROADMAP.md`, every Monday 08:30 UTC, and on manual dispatch (see
> [`.github/workflows/roadmap-export.yml`](../.github/workflows/roadmap-export.yml));
> Project-board sync is documented here as a maintainer-side runbook
> that consumes that artifact. Wiring an actual GitHub Project v2 board
> is a maintainer-credentials operation and is intentionally not
> automated in this repository.

The single source of truth for the project's direction is
[`ROADMAP.md`](../ROADMAP.md) at the repo root. The
[`python3 -m splunk_uc audit-roadmap-consistency`](../scripts/audit_roadmap_consistency.py)
auditor enforces structural integrity, validates repo-relative links,
and exposes a JSON snapshot that downstream automation (a GitHub
Project v2 board, an external dashboard, an MCP `list_roadmap_items`
tool) can consume with a stable schema.

## CI gate (in repo today)

`make audit-roadmap` runs the script in `--check` mode; this is wired
into the `lint` job of `.github/workflows/validate.yml`:

| Failure class | Severity | What you fix |
|---|---|---|
| Required H2 section missing or empty | Hard error | Restore the section in `ROADMAP.md`; six are required (`Current release`, `Previous releases`, `Next up: vX.Y …`, `vX.Y+ backlog (no fixed date)`, `Deprecated / declined ideas`, `How to influence the roadmap`). |
| Repo-relative link broken | Hard error | Fix the path or remove the link. External (`http(s)://`, `mailto:`) and pure-anchor (`#section`) links are skipped. |
| `## Deprecated / declined ideas` empty | Hard error | Re-add the historical "no SaaS" / "no commercial edition" / "no LLM-generated SPL" commitments — these are persistent project-direction promises. |
| `## Current release` line missing | Hard error | Add a `**vX.Y — Title** *(shipped DATE)*` line to the body. |
| Version-triple drift (ROADMAP `vX.Y` ↔ `VERSION` ↔ `CHANGELOG.md` top) | Soft warning | Bump the `## Current release` heading on the same release-day PR that updates `VERSION` + `CHANGELOG.md`. CI prints the drift but exits 0 today; flip to `--strict-version` once the heading is reconciled. |

## JSON snapshot contract

`make export-roadmap` emits `dist/roadmap.json`. The schema is pinned
at version `"1.0"`; consumers should refuse anything else.

```jsonc
{
  "schema_version": "1.0",
  "captured_at": "2026-05-09T12:21:52+00:00",
  "git_head": "abc12345",
  "current_release": {
    "version": "9.2",
    "name": "Foo",
    "status": "shipped",
    "date": "2026-05-09"
  },
  "previous_releases": [
    {"version": "9.1", "name": "...", "status": "shipped", "date": "..."}
  ],
  "next_up": {
    "version": "9.3",
    "title": "Next up: v9.3 — ... *(in progress)*"
  },
  "backlog": [
    {
      "name": "Content",
      "items": [
        "**Industry-specific bundles** — Standalone content packs for ..."
      ]
    },
    {"name": "Tooling",  "items": ["..."]},
    {"name": "Community & process", "items": ["..."]}
  ],
  "deprecated_ideas": [
    "**Hosted SaaS** — The project stays static-site-first ..."
  ]
}
```

Stability commitments:

* The set of top-level keys is frozen in `schema_version: "1.0"`. Adding
  a key is a minor (`1.1`) bump; renaming or removing one is a major
  (`2.0`) bump.
* The `version` strings in `current_release`, `previous_releases`, and
  `next_up` carry only what `ROADMAP.md` declares — `vX.Y` or `vX.Y.Z`
  with the leading `v` stripped. Don't hard-parse expecting one or
  the other; treat both as opaque strings or normalise via
  `audit._versions_compatible` (X.Y prefix match).
* Bullet items preserve the leading `**Title**` Markdown so a downstream
  renderer can extract the title for an issue/card and the rest for the
  body.

## Maintainer runbook: GitHub Project v2 sync

Wiring the published `reports/roadmap-export.json` artifact into a
public Project board is a one-time setup that requires repo-admin
credentials. The recipe below is the recommended path; the repo
deliberately stops at *publishing the snapshot as a workflow artifact*
([`roadmap-export.yml`](../.github/workflows/roadmap-export.yml)) and
does not push to a Project v2 board, because the maintainer owns the
project ID + token binding, not the build pipeline.

Pull the latest artifact down with:

```bash
# Inspect the latest run of the publisher workflow:
gh run list --workflow roadmap-export.yml --limit 1
# Download the artifact from a specific run:
gh run download <run-id> --name roadmap-export --dir reports/
```

### One-time setup

```bash
# 1. Create the project and capture the project number.
gh project create \
  --owner "@me" \
  --title "Splunk Monitoring Use Cases — Roadmap" \
  --format json | jq -r '.number'
# → 7

# 2. Create labels for each release line and each backlog category.
for label in "milestone:9.2" "milestone:9.3" \
             "roadmap:current"  "roadmap:next-up" \
             "backlog:content" "backlog:tooling" "backlog:community"; do
  gh label create "$label" --description "Auto-managed by audit_roadmap_consistency"
done
```

### Per-release sync

```bash
# 1. Refresh the snapshot from the latest ROADMAP.md.
make export-roadmap                         # writes dist/roadmap.json

# 2. Sync each backlog item into a Project card. Items with a matching
#    title get updated in place; new items get added as drafts.
python3 scripts/_unmaintained/sync_roadmap_to_project.py \
  --project-number 7                        \
  --owner fenre                             \
  --snapshot dist/roadmap.json
```

> The sync script is intentionally **not** in `scripts/` today; an
> example reference implementation can live under
> `scripts/_unmaintained/` (gitignored) or in a private wrapper repo.
> The CI gate validates `ROADMAP.md` and the JSON snapshot; the
> downstream Project sync is owned by the maintainer.

### Single milestone-X.Y label per release

The convention is one `milestone:X.Y` label per upcoming release:

* Carries the `next_up` items and any backlog items the maintainer has
  promoted into the upcoming release.
* Mirrors the value of `## Next up: vX.Y …` in `ROADMAP.md`, so a
  consumer that asks "what's in the next release?" can either query
  the label *or* read `next_up.version` from the snapshot.
* Becomes immutable when the corresponding `## Current release`
  heading flips to `vX.Y` (i.e. on release day) — the audit's
  version-triple drift then applies to the new label.

## Why two layers (CI + maintainer runbook)?

Splitting the work this way means:

1. The **CI gate** catches the highest-frequency regression class (link
   rot, section drift) automatically with no maintainer action — every
   PR exercises it. This is the bulk of the value.
2. The **JSON snapshot** is a stable contract the maintainer or a
   downstream contributor can build a board sync against without
   coupling the repo's CI to a specific GitHub Projects v2 schema or
   token policy. Project numbers, labels, and field IDs change
   independently of `ROADMAP.md` and shouldn't break the build when
   they do.
3. The **runbook** documents the high-leverage ops step (sync to a
   public board) without smuggling repo-admin credentials into the
   build pipeline.

If the project later moves to a hosted Project board with full
automation rights, this doc becomes the authoritative description of
what the action should do; the JSON snapshot is the input contract it
will consume.

## See also

* [`python3 -m splunk_uc audit-roadmap-consistency`](../scripts/audit_roadmap_consistency.py) — the auditor.
* [`tests/scripts/test_audit_roadmap_consistency.py`](../tests/scripts/test_audit_roadmap_consistency.py) — 25 unit tests.
* [`ROADMAP.md`](../ROADMAP.md) — the source of truth.
* [`docs/migration-status.md`](migration-status.md) — `p11-roadmap-board` tracking entry.
* [`AGENTS.md`](../AGENTS.md) — the CI-gate listing for AI agents.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<!-- END-AUTOGENERATED-SOURCES -->
