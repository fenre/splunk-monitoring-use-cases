# Contributing

> Solo-maintainer project. PRs are welcome but reviewed on a best-effort
> basis. The notes below are the minimum you need to land a content or
> tooling change without bouncing on CI.

## Quick start

```bash
git clone https://github.com/fenre/splunk-monitoring-use-cases.git
cd splunk-monitoring-use-cases
make build           # build the site into dist/
make serve           # preview dist/ at http://localhost:8080
```

The catalogue is single-source: `content/cat-*/UC-*.json` → `tools/build/build.py` → `dist/`.

## Adding a use case

### File and ID conventions

- **Category folder:** `content/cat-XX-descriptive-name/` (zero-padded `XX`).
- **UC file:** `UC-X.Y.Z.json` with `id` `"X.Y.Z"` matching the directory's `cat-XX`.
- Within a subcategory `(X.Y)`, `Z` values must be strictly increasing, no gaps. UC IDs are globally unique.

`make audit` enforces these.

### Required fields

Every UC validates against [`schemas/uc.schema.json`](schemas/uc.schema.json). The schema is authoritative; the most common required properties are:

| Property | Notes |
| --- | --- |
| `criticality` | `critical` \| `high` \| `medium` \| `low` |
| `difficulty` | `beginner` \| `intermediate` \| `advanced` \| `expert` |
| `monitoringType` | Non-empty array, values from schema enum |
| `value` | Why this matters (one-paragraph business case) |
| `app` | Primary Splunk app or TA |
| `dataSources` | What feeds the detection |
| `spl` | Plain-text SPL (no markdown fencing) |
| `implementation` | Deployment / tuning guidance |
| `visualization` | Suggested views |
| `cimModels` | Model name(s), `[]` if none |
| `grandmaExplanation` | 20–400 char plain-language one-liner (run `make sync-generated` if missing) |

Optional: `mitreAttack`, `cimSpl`, `references`, `wave`, `prerequisiteUseCases`, equipment tags, compliance entries. See [`docs/use-case-fields.md`](docs/use-case-fields.md) for the full authoring contract.

### Template

```json
{
  "id": "X.Y.Z",
  "title": "Short descriptive title",
  "criticality": "high",
  "difficulty": "intermediate",
  "wave": "walk",
  "prerequisiteUseCases": ["UC-1.1.1"],
  "monitoringType": ["Security"],
  "value": "One or two sentences on operational impact.",
  "app": "Your_TA_id",
  "dataSources": "Sourcetypes / APIs / logs.",
  "spl": "index=... | ...",
  "implementation": "How to roll it out and tune it.",
  "visualization": "Table, single value, etc.",
  "cimModels": ["Authentication"],
  "references": [{"url": "https://...", "title": "Vendor docs"}]
}
```

## Local validation before opening a PR

```bash
make build                      # full site build
make audit                      # core audit suite
make sync-generated-check       # 14 cascade-generator drift gates (PR-2 umbrella)
PYTHONPATH=src python3 -m pytest tests/build/ tests/scripts/ -q
```

`make sync-generated-check` is the single drift gate that replaces 14 individual cascade-regen `--check` steps. If it fails, run `make sync-generated && git add -A && git diff --staged` and commit the regenerated files.

## Parallel execution (multi-agent / worktree workflow)

When several catalogue-improvement tasks run at the same time, each task gets its
own **git worktree** so builds, branches, and local edits do not collide.

| Convention | Pattern | Example |
| --- | --- | --- |
| Worktree directory | `.worktrees/<lane>-<slug>` | `.worktrees/A-mcp-http-transport` |
| Branch (catalogue tasks) | `<lane>/<slug>` | `A/mcp-http-transport` |
| Build output | `<worktree>/dist/` (default) | isolated per checkout |

Quick start:

```bash
make worktree-new TASK=A-mcp-http-transport   # ad-hoc: branch worktree/<TASK>
cd .worktrees/A-mcp-http-transport
make devcontainer-init                        # optional full bootstrap
make build                                    # writes to this worktree's dist/
```

For tasks from the parallel execution programme, use the branch name `<lane>/<slug>`
from the task block (not `worktree/<TASK>`). The `make worktree-new` helper is for
smoke tests and ad-hoc isolation; real lane tasks should create worktrees with
`git worktree add -b <lane>/<slug> .worktrees/<lane>-<slug>`.

**Subagents must not edit UC sidecars** (`content/cat-*/UC-*.json`) or handwritten
starter-bundle entries — those are maintainer-authored only.

Full rules (central files, schema cycles, proposal queues, merge protocol):
[`docs/parallel-execution-substrate.md`](docs/parallel-execution-substrate.md).

## CI overview

Every PR runs [`.github/workflows/validate.yml`](.github/workflows/validate.yml) — five parallel jobs (`lint`, `audits-content`, `audits-build`, `mcp`, `frontend`). The detailed map is in [`docs/ci-architecture.md`](docs/ci-architecture.md); the umbrella drift gate sits at the top of `audits-content`.

A separate UC end-to-end harness ([`.github/workflows/uc-tests.yml`](.github/workflows/uc-tests.yml)) spins up Splunk Enterprise and replays every UC fixture; it requires two repo secrets (`UC_TEST_SPLUNK_PASSWORD`, `UC_TEST_HEC_TOKEN`) and short-circuits cleanly when they aren't present.

## JSON is the source of truth

The canonical authoring surface for every use case is the JSON sidecar at
`content/cat-NN-slug/UC-X.Y.Z.json` (validated against
`schemas/uc.schema.json`). Per-UC `.md` companions under `content/` were
deleted in 2026-05-18 (F21 close); the LLM-friendly markdown twin is now
emitted at build time only by `tools/build/templates/uc.py::render_markdown_twin`
into `dist/uc/UC-X.Y.Z/uc.md`. See
[`docs/adr/0007-json-as-source-of-truth.md`](docs/adr/0007-json-as-source-of-truth.md)
for the contract.

## Version bumps

`VERSION` is the single source of truth. The top entry of `CHANGELOG.md` and the newest release-notes section in `index.html` must match it (CI enforces). See [`.cursor/rules/versioning.mdc`](.cursor/rules/versioning.mdc) for the bump procedure.

## Quality tiers

The catalogue follows a quality-over-quantity philosophy.

| Tier | Target |
| --- | --- |
| Gold | API-polled products with complex TAs — full 5-step implementation depth |
| Silver | Syslog or simpler integrations — three substantive sections, ≥1 reference |
| Bronze | Minimum viable — enough metadata + SPL to be useful |

See [`docs/gold-standard-template.md`](docs/gold-standard-template.md) for the contract and the exemplar (UC-5.13.1).

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Gerhards, R. (2009, March). *The Syslog Protocol*. Internet Engineering Task Force. RFC 5424. https://www.rfc-editor.org/rfc/rfc5424

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-3"></a>**[3]** Splunk Inc. (2026). *Splunk AppInspect documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://dev.splunk.com/enterprise/docs/developapps/testvalidate/appinspect/

<a id="ref-4"></a>**[4]** Splunk Inc. (2026). *Splunk Cloud Platform App Vetting requirements*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SplunkCloud/latest/Service/SplunkCloudservice

<a id="ref-5"></a>**[5]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

### Cited by

- [`docs/replication-guide.md`](docs/replication-guide.md)

<!-- END-AUTOGENERATED-SOURCES -->
