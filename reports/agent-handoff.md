# Agent Handoff Brief

> Written 2026-05-09 22:08 UTC+2, immediately after shipping **v8.1.0** to
> production GitHub Pages. Read this first if you are a new chat session
> picking up where the previous agent left off. Then run the
> "Quick state check" commands below and decide what to do.

---

## 1. Latest shipped release

| | |
|---|---|
| Version | **8.1.0** |
| Released | 2026-05-09 |
| Live URL | <https://fenre.github.io/splunk-monitoring-use-cases/> |
| Pages workflow | [run 25610354000](https://github.com/fenre/splunk-monitoring-use-cases/actions/runs/25610354000) — green |
| Git SHA on `main` at release time | `15fe8748f` |
| Headline | 67 gold-standard guides + 43-verb `splunk_uc` dispatcher + permanent xref guard + link-freshness sweep |

Three commits made up the release wave:

- `ac0aafdb0` — `release(8.1.0): gold-standard guide library + 43-verb dispatcher + xref guard` (214 files)
- `7f273cdfc` — `feat(recommender): Build 13 — three matcher fairness fixes for cat-22 over-dominance` (8 files)
- `15fe8748f` — `fix(schema): add required lifecycle metadata to stewardship-digest schema` (2 files; deploy hotfix)

The first deploy attempt failed because the brand-new
`schemas/v2/stewardship-digest.schema.json` was missing the four lifecycle
metadata fields that `tools/audits/schema_meta.py` enforces. Hotfix
landed in commit 3, second deploy passed. **Lesson for the next agent:
every new file under `schemas/**.schema.json` MUST declare `version`,
`x-stability`, `x-since`, `x-changelog` and have a matching
`schemas/changelogs/<name>.md`** — see `docs/schema-versioning.md`.

---

## 2. CRITICAL — there is a parallel agent currently writing to disk

When this brief was written, **another process (likely a parallel
Claude/Cursor agent the user kicked off in another window) was actively
writing files in the workspace** — most recent write was 7 seconds ago
(file `src/splunk_uc/generators/mapping_ledger.py`). The pattern
suggests it is running the **Tier-2 generator migration** of the P6 plan
(after Tier-1 audit migration completed in batch 11) **and** continuing
the recommender app iteration.

What's currently uncommitted on disk that came from the parallel agent:

- **P6 Tier-1 batch 11 (audit migration COMPLETE)** — moves the final 5
  audit scripts into `src/splunk_uc/audits/`:
  `gold_profile.py` (v1) + `perf_a11y.py` + `spl_grammar.py` +
  `spl_hallucinations.py` + `splunk_cloud_compat.py`. Dispatcher count
  43 → 48 verbs. The CHANGELOG entry for this **has already been
  written** by the parallel agent and was relocated into `[Unreleased]`
  by the previous chat agent (it was incorrectly placed inside the
  `[8.1.0]` section because the parallel agent didn't realise the
  release had already cut). Verify with:

  ```bash
  grep -nE '^### Repo overhaul plan §P6 — Tier 1 batch 11' CHANGELOG.md
  # should be after line 13 (## [Unreleased]) and before line ~160
  # (## [8.1.0] - 2026-05-09)
  ```

- **P6 Tier-2 generator migration (started)** — `src/splunk_uc/generators/`
  is being populated; new files appearing include
  `md_from_json.py`, `grandma_explanations.py`, `stewardship_digest.py`,
  `mapping_ledger.py`. Their `scripts/generate_*.py` siblings are being
  shrunk to thin shims (e.g. `scripts/generate_md_from_json.py` lost
  ~379 lines). Check with `git status --short | grep -E '^(.M | M).+(scripts/generate|src/splunk_uc/generators)'`.

- **Recommender Build 14+ (?)** — more recommender app changes are landing
  on top of the just-shipped Build 13: eventtypes.conf grew by ~324
  lines, recommender.js + match.test.mjs continue to evolve.

- **More ruff format polish** on `src/splunk_uc/audits/spl_grammar.py`
  and `src/splunk_uc/audits/splunk_cloud_compat.py`.

### What you (the new agent) should do FIRST

1. **Detect quiescence**. Run this until you see no writes for 60+ seconds:

   ```bash
   for f in $(git diff --name-only) $(git ls-files --others --exclude-standard); do
     stat -f "%m %N" "$f" 2>/dev/null
   done | sort -rn | head -5 | awk '{cmd="date -r " $1 " +%H:%M:%S"; cmd | getline t; close(cmd); $1=t; print}'
   date "+%H:%M:%S now"
   ```

2. **Sanity-check the working tree** before any commit:

   ```bash
   git status -sb
   git log --oneline -5
   git diff --stat
   PYTHONPATH=src python3 -m splunk_uc audit-changelog-uc-refs
   PYTHONPATH=src python3 -m splunk_uc audit-guide-xrefs
   PYTHONPATH=src python3 -m splunk_uc audit-repo-consistency
   python3 tools/audits/schema_meta.py        # gate that ate Pages run #1
   python3 tools/audits/asset_drift.py
   ```

3. **Verify version triple still in sync** before pushing anything new:

   ```bash
   VER=$(cat VERSION) && \
   CL_VER=$(grep -m1 -E '^## \[[0-9]' CHANGELOG.md | sed 's/## \[\(.*\)\].*/\1/') && \
   RN_VER=$(python3 -c "import re; m=re.search(r'<span class=\"rn-version-tag[^\"]*\">([^<]+)</span>', open('index.html').read()); print(m.group(1).strip() if m else '')") && \
   echo "VERSION=$VER  CHANGELOG-top-released=$CL_VER  index.html-top-RN=$RN_VER" && \
   [ "$VER" = "$CL_VER" ] && [ "$VER" = "$RN_VER" ] && echo "OK"
   ```

4. **Decide whether the in-flight work warrants its own release.** As
   shipped at 8.1.0, [Unreleased] in CHANGELOG already contains the P6
   batch 11 entry. The next release (probably **8.2.0**, minor) should
   bundle batch 11 + Tier-2 generator migration + recommender iteration
   + whatever else accumulates. Ask the user before bumping VERSION
   (per `.cursor/rules/versioning.mdc`).

---

## 3. Outstanding backlog (from this session)

### Documentation polish

| Item | Where | Notes |
|---|---|---|
| 29 Splunkbase app `404`s | `reports/external-links-todo.md` | Need vendor input on canonical replacements; not safe to guess |
| 40 vendor docs `404`/`5xx` | `reports/external-links-todo.md` | Same — defer until vendor docs stabilise |
| 57 product/sub-domain guides not promoted on `docs.html` | `docs.html` (`Deployment & Integration` section currently has only 2 cards) | Intentionally not done in 8.1.0 — already reachable via `subcategory.guide` in `_category.json` (catalog UI). Open design question: do we want a "Product Guides" section auto-rendered from `docs-uc-map.js`, or hand-curated cards? Ask the user. |

### Tier-2 generator migration (in flight, see §2)

`docs/scripts-taxonomy.md` is the canonical tracker. The five remaining
full-body audit scripts that batch 11 moves leave **only the intentional
non-verb one-shot driver** `scripts/audit_guide_external_links_oneshot.py`
in `scripts/audit_*.py` (it is excluded by design). The next major
migration cluster is the ~30 generator scripts in `scripts/generate_*.py`
— the parallel agent has started this; whether they finish it depends on
how their session was scoped.

### Tier-3 (post-soak shim deletion) and Tier-4 (post-P9 wheel package)

Not started. Wait for at least one minor release of soak before deleting
the legacy `scripts/audit_*.py` shims that re-export the new
`splunk_uc.audits.*` modules.

---

## 4. Session-discovered quirks

These will save the next agent debugging time:

### a. Background automation runs on VERSION bumps

When `VERSION` was edited from 8.0.0 → 8.1.0, **several files were
auto-regenerated within ~2 minutes**:

- `splunk-apps/splunk-uc-recommender/{README.md, app.manifest, default/app.conf, lookups/uc_recommender_static.csv, appserver/static/data/catalog-fallback.json, appserver/static/js/recommender.js}` (full app re-render via `scripts/generate_recommender_app.py`)
- ruff RUF022 (sorted `__all__`) auto-fixes across `src/splunk_uc/audits/*.py` and matching `scripts/audit_*.py` shims

If you bump VERSION, **wait 2 minutes for the auto-regeneration burst to
finish before committing**. Otherwise the build artefact (recommender
catalog-fallback.json) and the `__all__` ordering will drift between
your commit and reality.

### b. `dist/` is sandboxed away from the agent

The `Read` tool returns `Permission denied` for `dist/**` and `Glob`
returns 0 results. This is normal — `dist/` is gitignored and the
sandbox blocks it. Trust the build's stdout (`[build] DONE NN files,
NN MiB`) for verification, or use `gh` CLI for production checks.

### c. Pages workflow auto-deploys on push to main

`.github/workflows/pages.yml` triggers on every push to `main`, runs
all pre-build audits + reproducibility check + Sigstore attestation +
Pages publish. Typical end-to-end ~3-4 minutes. **No manual
deploy step needed** — `git push origin main` is the trigger.

### d. Pre-build audits to satisfy before push

`pages.yml` runs these BEFORE the build, and they fail-fast in <30s:

```bash
python3 tools/audits/schema_meta.py    # NEW schemas need 4 lifecycle fields
python3 tools/audits/asset_drift.py    # src/ ↔ inline blocks in index.html
```

### e. `src/splunk_uc/` requires `PYTHONPATH=src`

When invoking the dispatcher locally:

```bash
PYTHONPATH=src python3 -m splunk_uc <verb> [...args]
# or
make audit-<verb>     # the Makefile sets PYTHONPATH for you
```

---

## 5. Suggested first message for the new agent

Pick whichever applies (copy-paste into the new chat):

### If the parallel agent has finished and you want to ship 8.2.0

```
read reports/agent-handoff.md, verify the working tree is quiesced and
all audits pass, then propose a version bump (8.1.0 -> 8.2.0?) and
commit + push + deploy as a clean release.
```

### If you want to continue the documentation polish backlog

```
read reports/agent-handoff.md, then pick up the deferred
external-links-todo backlog: walk reports/external-links-todo.md
and resolve the Splunkbase 404s by either confirming the new app ID
or removing the dead reference.
```

### If you want the new agent to tackle the docs.html promotion question

```
read reports/agent-handoff.md, then propose a design for surfacing
the 57 product/sub-domain guides on docs.html. Ask me whether to
auto-render from docs-uc-map.js or to hand-curate cards by domain.
```

### If the parallel agent is still running and you want to coordinate

```
read reports/agent-handoff.md. The parallel agent appears to still be
running. Check git diff --name-only and wait for quiescence (no
writes for 60s+). Then summarise what changed since 8.1.0 was
shipped and propose how to package it.
```

---

## 6. Things deliberately NOT done in this session

- **Did not** delete the legacy `scripts/audit_*.py` shims (Tier 3,
  blocked on one minor release of soak).
- **Did not** add the 11 new product/sub-domain guides as cards on
  `docs.html` Deployment & Integration section. They are reachable via
  `subcategory.guide` in the catalog UI, and the user did not request
  this promotion.
- **Did not** convert `scripts/audit_guide_external_links_oneshot.py`
  into a registered dispatcher verb. Its module docstring labels it
  "intentionally a one-shot driver, not a registered verb."
- **Did not** resolve any of the 29 Splunkbase 404s or 40 vendor doc
  404s — these need vendor input.
- **Did not** bump the `splunk-uc-recommender` app to a new MAJOR or
  MINOR. The auto-regen at the 8.1.0 VERSION bump moved it to Build 13
  but kept the app at 8.1.0; the matcher fairness fixes in commit
  `7f273cdfc` justify the build bump within the same release.

---

*This brief is intentionally session-scoped. Once the next agent has
consumed it, feel free to delete `reports/agent-handoff.md` (or move it
to `reports/archive/`) so the directory does not accumulate stale handoffs.*
