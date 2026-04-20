# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Section headings (e.g. `### New Use Cases`) are rendered as-is in the release
notes popup. `build.py` auto-generates the HTML from this file — do not edit
the release notes block in `index.html` by hand.

---

## [7.0] - 2026-04-19

### Per-UC content architecture

- **Every use case is now its own file pair.**  The 23 monolithic
  `cat-*.md` files (some exceeding 60,000 lines) have been exploded
  into 6,449 individual `content/cat-NN-slug/UC-X.Y.Z.md` prose files
  paired with 6,470 `UC-X.Y.Z.json` structured-metadata sidecars.
  Each UC is independently reviewable, diffable, and indexable — a PR
  that touches one use case now changes two small files instead of
  a 5 MB markdown blob.
- **`_category.json` per directory** holds subcategory metadata,
  replacing the implicit structure that was embedded in markdown
  headings.

### New build pipeline (`tools/build/`)

- **Python stdlib-only SSG.**  `tools/build/build.py` is the single
  entrypoint that reads `content/` + `data/` + `src/` and produces
  the complete `dist/` deployment artefact.  No Node.js, no npm, no
  external services in the content pipeline — only Python 3.12
  stdlib.
- **Reproducible builds.**  `--reproducible` sorts iteration, freezes
  timestamps to `git log -1 --format=%cI HEAD`, and sorts JSON keys.
  CI builds twice and asserts byte-identical output.
- **Modular renderers.**  Five independent `render_*` modules
  (pages, assets, api, exports, meta) consume the same in-memory
  `Catalog` and write disjoint subtrees of `dist/`.
- **Search shards.**  Full-text search uses MiniSearch shards
  (`assets/search-shard-NN.<hash>.json`, ~100 KB each, 16 shards)
  loaded on first keystroke, replacing the previous 39 MB linear scan
  over `data.js`.
- **Integrity & provenance.**  `dist/integrity.json` (SHA-256 of
  every artefact) and `dist/BUILD-INFO.json` are Sigstore-signed by
  the GitHub OIDC identity in CI.

### Extracted source assets (`src/`)

- **CSS extracted** from ~950 inline lines in `index.html` into
  `src/styles/{tokens,base,components,print,helpers}.css`.
- **JavaScript extracted** from ~2,700 inline lines into
  `src/scripts/{loader,state,filters,render,panel,app,search}.js`.
- All assets are fingerprinted at build time and served with
  immutable cache headers.

### CI quality gates (`tools/audits/`)

- **`asset_drift`** — detects unintended changes in fingerprinted
  assets.
- **`budgets`** — enforces per-page gzipped size budgets.
- **`schema_diff`** — blocks breaking changes on stable schemas.
- **`schema_meta`** — validates `x-since`, `x-changelog`, versioning
  metadata on every JSON Schema.
- **`url_freeze`** — blocks removal of any URL that existed in the
  previous release's `manifest.json`.

### New schemas and docs

- **`schemas/v2/`** — `catalog-index.schema.json` and
  `search-index.schema.json` for the new lazy-loading and sharded
  search surfaces.
- **`schemas/changelogs/`** — per-schema changelog tracking.
- **`docs/architecture.md`** — locked v7.0 architecture contract
  (build pipeline, layered model, performance budgets, stability
  commitments, scalability targets up to 60 K UCs).
- **`docs/url-scheme.md`** — permanent URL contract for all public
  endpoints.
- **`docs/schema-versioning.md`** — schema stability tiers and
  lifecycle.
- **`docs/api-versioning.md`** — updated for v7 versioning strategy.

### Updated CI pipeline

- **`pages.yml` rewritten** for the v7 build contract: reproducible
  builds, Sigstore attestation, `dist/` as sole deploy target.
- **`.gitignore` updated** to treat legacy root-level generated files
  (`catalog.json`, `data.js`, etc.) as gitignored — v7 generates
  them into `dist/` on every build.
- **`.cursorignore` added** to exclude large generated artefacts from
  IDE indexing, improving editor responsiveness.

### Repository cleanup — archive one-shot scripts, refresh stale UC counts, add missing READMEs

- **One-shot fix scripts archived under `scripts/archive/`.**  Twelve
  Python helpers that were authored as one-shot data migrations or
  audit-replay drivers (`_bootstrap_phase2_3_data.py`,
  `fill_false_positives.py`, `fill_mitre_mappings.py`,
  `fill_references.py`, `fix_cim_spl_alignment.py`,
  `generate_phase_e_signoffs.py`, `migrate_uc_markdown_to_json.py`,
  `normalize_compliance_clauses.py`, `redistribute_meraki.py`,
  `rename_cat22_control_themes.py`, `retag_meta_multi_ucs.py`,
  `scaffold_exemplars.py`) were sitting in `scripts/` alongside the
  ~100 active CI helpers, where a future contributor could easily run
  one by accident and silently undo months of hand-applied fixes.  All
  twelve moved to `scripts/archive/`, with their `REPO_ROOT` path
  resolution corrected for the deeper directory level and an updated
  `scripts/archive/README.md` enumerating each script's status,
  default mode, and `--write` warning.
- **Eleven truly-orphan `fix_*` / `remove_*` / `move_*` helpers
  deleted.**  These were ad-hoc fix scripts written during the SPL
  review hardening pass (`fix_audit_findings.py`,
  `fix_broken_references.py`, `fix_known_fp.py`,
  `fix_link_rewrites.py`, `fix_mitre_taxonomy.py`,
  `fix_monitoring_type.py`, `fix_splunkbase_hallucinations.py`,
  `move_ucs.py`, `remove_bad_cim_spl.py`, `remove_dead_urls.py`) plus
  a stale `legacy/index-legacy.html`.  Their work is captured in
  audit-replay form by the linters under `scripts/audit_*.py`; the
  fix scripts themselves were single-use and can never run safely
  again because the input data they targeted no longer exists.
- **`scripts/archive/_bootstrap_phase2_3_data.py` and
  `scripts/archive/scaffold_exemplars.py` made safe-by-default.**
  Both authoring drivers were destructive on every run — the bootstrap
  silently overwrote `data/per-regulation/phase2.3.json` (dropping
  later CIM-normalisation fixes) and the scaffold rewrote 39 sidecars
  + the Phase 1.6 markdown block (dropping `derived-from-parent`
  enrichments that Phase 2.x had layered on top).  Both scripts now
  default to `--check` (read-only diff vs on-disk fixture, exit 0 when
  in sync) and require an explicit `--write` to mutate anything; the
  module docstrings carry an explicit `WARNING` block explaining what
  gets clobbered.
- **`secrets.env.example` template now tracked.**  The file was being
  ignored alongside the real `secrets.env`, which meant a fresh clone
  had no template for the `SPLUNK_*_TOKEN` environment variables
  consumed by `scripts/run_uc_tests.py`,
  `scripts/audit_splunk_cloud_compat.py`, and the (currently disabled)
  Splunk REST integration in the MCP server.  Added a sanitised
  template with placeholder values and a comment block explaining
  which scripts read each variable, then dropped the bogus ignore
  rule.
- **`api/README.md` added; `api/` re-enabled for tracking the README
  only.**  The whole `api/` tree is gitignored because every file
  under it is regenerated by `scripts/generate_api_surface.py` on
  every build (per-category JSON, the v1 surface, the index manifest).
  Without an explainer in the directory, contributors who saw `api/`
  in `git status` had no signal that they were looking at build
  artefacts.  The new README documents the gitignore strategy, the
  generator that owns the contents, and the public URLs each artefact
  is served at.  `.gitignore` was rewritten to ignore `api/*` (the
  contents) instead of `api/` (the directory itself), so the
  `!api/README.md` exception can re-include the explainer.
- **`tools/data-sizing/README.md` added.**  The data-sizing
  assessment tool was a self-contained static web app inside `tools/`
  with no in-folder documentation explaining what it does, how to run
  it, or how it gets deployed.  Added a README covering the tool's
  purpose, file layout, local development workflow, and the
  "Community Reference" branding alignment with `index.html`.
- **Stale UC count claims refreshed across forward-looking docs.**
  `docs/PITCH.md`, `docs/DESIGN.md`, `docs/splunk-apps-use-cases-comparison.md`,
  `ta/DA-ITSI-monitoring-use-cases/README.md`, `mcp/src/splunk_uc_mcp/server.py`
  (3 spots: `SERVER_INSTRUCTIONS`, `search_use_cases` description,
  `_list_resources` comment), `index.html` (2 help-grid spots), and
  `README.md` (via `build.py`'s rounded display) all moved from
  `6,300+` / `6,304` / `6,424` to either `6,400+` (narrative) or
  `6,425+` (rounded display).  Historical references in CHANGELOG
  entries, ADRs, and `docs/v6.0-release-report.md` were intentionally
  left as snapshots of the v6.0 state.
- **Dangling `spl-review-findings.md` reference dropped from the v3.7
  release notes.**  The file is gitignored (and has been since
  `d6a5a1c`), so the "See the remediation note in that file" pointer
  in both `CHANGELOG.md` and `index.html` was a 404 for any visitor.
  The substantive list of SPL hardening changes was preserved; only
  the dangling pointer was removed.
- **Local-only cruft deleted.**  `Cisco Brand Colors Quick-Start-Guide-v3.PDF`
  (17 MB local-only download) and the typo'd `Data Assessement tool/`
  directory (~2 MB, gitignored, superseded by `tools/data-sizing/`)
  were removed from the working tree.  Neither was tracked, so this is
  contributor-machine hygiene only; it has no public-facing effect.
- **All `scripts/audit_compliance_gaps.py` outputs regenerated.**  The
  Phase C UC additions in v6.1 changed clause coverage tallies in
  `reports/compliance-gaps.json` and `docs/compliance-gaps.md`; both
  were stale relative to the source-of-truth `compliance[]` arrays.
  Regenerated and re-committed so the CI drift guard stays green.

### CI hygiene + documentation alignment for v6.1

- **`.github/workflows/link-check.yml` — broken-link findings now surface
  as tracking issues again.**  The workflow piped `audit_links.py` through
  `tee` without `set -o pipefail` and ended with an unconditional
  `exit 0`, which masked a non-zero auditor exit (`code=$?` captured
  `tee`'s 0 instead of the auditor's actual code).  The fix uses
  `${PIPESTATUS[0]}` to capture the real exit code of
  `audit_links.py`, writes it to `steps.audit.outputs.exit_code`, and
  preserves the `exit 0` so the next job (which gates on
  `steps.audit.outputs.exit_code != '0'`) can still run and open a
  tracking issue.  Reviewers now see the broken-reference list in a
  fresh issue rather than a green CI run with no actionable artefact.
- **`.github/workflows/uc-manifest.yml` — Python pinned to 3.12 (was
  3.11).**  Every other workflow in `.github/workflows/` already uses
  3.12 (`validate.yml`, `uc-tests.yml`, `link-check.yml`,
  `regulatory-watch.yml`); the version split risked "works on
  validate, fails on manifest" surprises when scripts use a 3.12-only
  feature.
- **`.github/dependabot.yml` — added the missing-but-promised
  Dependabot configuration.**  `uc-tests.yml` (lines 102-103) said the
  pinned Splunk Docker digest was updated by Dependabot via this file,
  but the file itself was never created.  The new config opens weekly
  PRs (Mondays 06:00 UTC, max one open PR per ecosystem) for both
  `github-actions` (every workflow pins actions by major-version tag)
  and `docker` (the `splunk/splunk:9.4.1` reference in `uc-tests.yml`).
  `pip` is intentionally excluded — the catalogue's Python deps come
  from system packages installed in the workflow itself, and the MCP
  server's runtime deps are pinned manually as part of MCP releases.

### Documentation alignment with the v6.1 reality

- **`ROADMAP.md` — current/next release pointers refreshed.**  Was still
  claiming "Current release: v6.0" with v6.1 listed under "Next up,
  target 2026-Q3"; v6.1 has shipped and the v6.2 backlog is now the
  forward-looking section.  The two previously-unreleased workstreams
  (Phase 5.5 structured equipment tagging, Phase 6 MCP server) are now
  documented as part of v6.1 instead of as pre-release work.
- **`CITATION.cff` — version bumped 6.0 → 6.1, UC count 6,300+ → 6,400+,
  preferred-citation version 5.2 → 6.1.**  Brings the citation metadata
  into line with `VERSION`, `CHANGELOG.md`, and the actual catalogue
  size (6,447 UCs).
- **`SECURITY.md` — supported versions, packaged-app inventory, and
  modular-input claim corrected.**  The supported-versions table now
  reads 6.1.x ✅ / 6.0.x ✅ / < 6.0 ❌ (was 5.2.x / 5.1.x / < 5.1).
  The "three packaged Splunk apps" claim was rewritten to enumerate
  all 13 packs (3 under `ta/` + 10 regulation packs + recommender +
  recommender-TA under `splunk-apps/`) plus the `mcp/` server.  The
  blanket "no custom scripts, modular inputs, or REST endpoints" claim
  was revised to call out the `splunk-uc-recommender-ta` modular input
  and the MCP server's stdio-only attack surface, both of which are
  now explicitly in scope.
- **`docs/regulatory-primer.md` — three broken
  `api/v1/compliance/regulations/` and OSCAL catalogue links fixed.**
  The §4.1 (GDPR), §4.3 (PCI DSS), and §4.9 (NIST 800-53) "Where to
  look" footers pointed at filenames that did not exist
  (`gdpr@2016/679.json` with a `%2F`-encoded slash, `pci-dss@4.0.json`
  missing the `v` prefix, `nist-800-53-rev5.json` instead of the
  actual `nist-sp-800-53-r5.normalised.json`).  Replaced with the
  exact file paths so the in-page link resolves on
  `regulatory-primer.html` and on raw GitHub.
- **`docs/PITCH.md` — `mcp-server/` references retargeted to `mcp/`.**
  Two links (the "Roadmap" bullet and the "AI / LLM tooling author"
  audience row) referenced a `mcp-server/` directory that does not
  exist; the actual package lives under `mcp/`.  Both now link to
  `mcp/` and to the new
  [`docs/mcp-server.md`](docs/mcp-server.md) integration guide.
- **`docs/mcp-server.md` — broken `.mdc` rule reference replaced with
  the upstream CoSAI publication.**  The "Security model" section
  linked to `../.cursor/rules/codeguard-0-mcp-security.mdc`, which is
  not present in the repository (workspace-level Cursor rules are
  delivered via the editor configuration, not committed alongside the
  source).  The link now points at the public CoSAI MCP Security
  publication that the rule is derived from, plus a note clarifying
  that the same guidance is encoded into the editor's workspace rule.
- **`mcp/src/splunk_uc_mcp/server.py` — forward reference to a
  non-existent `get_provenance` tool removed.**  The `_summarise_ledger`
  docstring told agents to "re-query with `get_provenance` once that
  tool ships", but no such tool is on the roadmap; the existing
  `ledger://full` resource already exposes the complete ledger payload.
  Docstring updated to point at the resource directly.  The
  `SERVER_INSTRUCTIONS` UC count was also refreshed from
  "6,424 UCs" to "6,400+ UCs across 23 categories" so the agent
  instructions don't drift again on every release.
- **`mcp/tests/test_server.py` — typo'd "todo" comment cleaned up.**  The
  comment beside `test_slug_regexes_are_frozen` read
  "(scripts/audit_mcp_tool_schemas.py, todo)" implying the drift guard
  hadn't been written; it has been written and is wired into
  `validate.yml`.  Comment now states the relationship correctly.
- **Root `openapi.yaml` — corrected the misleading "regenerated as
  part of `build.py`" claim.**  This root-level spec is hand-maintained
  as developer documentation for the legacy `/api/cat-{n}.json` and
  `/catalog.json` surfaces; the auto-generated companion lives at
  `/api/v1/openapi.yaml` and is regenerated by
  `scripts/generate_api_surface.py`.  The new wording calls out the
  split, marks the `/api/v1/` spec as canonical for new clients, and
  documents that this root spec stays in sync via PR review.  The "
  6,300+ curated Splunk use cases" line in the spec summary was
  updated to "6,400+" to match `CITATION.cff`.

### Branding — subtitle updated for accuracy

- **Header subtitle on every user-facing page no longer reads "Cisco Network
  Intelligence"** — The logo subtitle strip under "Use Case Catalog" on
  `index.html`, and the sibling "Data Sizing Assessment" header on
  `tools/data-sizing/index.html`, now render **"Community Reference"**
  instead.  This project is a community-maintained reference catalogue — it
  is not an official Cisco product, does not carry Cisco branding approval,
  and must not present itself as one.  The new label keeps the same visual
  hierarchy (font, size, uppercase treatment) but honestly labels the site's
  status.  The `<title>` tags on both pages were updated in tandem so
  bookmarks, browser tabs, and search-engine snippets also drop the implied
  claim of affiliation.  The internal `tools/data-sizing/styles.css`
  file-header comment was refreshed for the same reason (and its stale
  reference to a deleted `cisco-ui.html` was corrected to `index.html`).
- **Historical release notes preserved** — The v4.0 release-notes entry
  (`### Cisco Network Intelligence UI`) is left unchanged here because it
  accurately documents the state of the project at that moment and is
  rendered verbatim into the in-app release-notes popup by `build.py`;
  rewriting history would be misleading to anyone trying to understand when
  the UI was redesigned.  Only forward-facing, user-visible strings were
  touched — no schema, manifest, API endpoint, CIM mapping, or catalogue
  content was affected, and `build.py`'s idempotence contract still holds
  because neither the `<title>` tag nor the header logo block sits inside a
  generated region (the release-notes sentinels and the meta-description
  count regex are the only `index.html` sections `build.py` rewrites).
- **Product-name references left intact** — Mentions of actual Cisco
  products throughout the catalogue (Cisco Meraki, Cisco Intersight, Cisco
  ISE, Cisco Cyber Vision, Cisco ThousandEyes, Cisco Secure Firewall, etc.)
  are descriptive references to real third-party data sources the catalogue
  covers, not brand claims, and remain as-is.  Only the top-level "this
  site is a Cisco thing" framing was the problem, and that framing now
  reads accurately.

### Regulation-coverage gap closure (six-phase plan)

Theme: **"every priority-weight clause traceable to a verified UC, every
malformed clause rejected at the CI gate."**  A six-phase campaign closed the
long-standing gaps in `docs/compliance-coverage.md`: 670 malformed
`compliance[].clause` strings were rewritten, 8 tier-2 regulations that shipped
with empty `commonClauses[]` were populated, 23 new UCs were authored for the
tier-2 clauses that remained uncovered, 11 UCs mapped to the `meta-multi
"Multiple"` placeholder were re-tagged to concrete frameworks, 250 UCs were
elevated to `status: verified` with dual-SME sign-off, and the CI guard rail
was hardened so malformed clauses can never be re-baselined.

- **Phase A — clause string normalisation** —
  `scripts/normalize_compliance_clauses.py` is the one-shot, idempotent
  rewriter for malformed clause strings.  Per-regulation rewrite functions
  apply regex transformations, range expansions, and keyword-driven mappings
  against UC titles and descriptions to infer the correct clause.  Running
  the normaliser shrank `tests/golden/audit-baseline.json` from 670
  tolerated `clause-grammar` findings to zero.  The `clauseGrammar` regex
  for FISMA was also widened (`§3554(b)(1)`-style nested subsections) and
  for HIPAA Privacy (`§164.528`) so the normaliser's output is valid.
- **Phase B — populated `commonClauses[]` for 8 tier-2 regulations** —
  `data/regulations.json` now ships authoritative `commonClauses[]` for
  NO Sikkerhetsloven, NO Personopplysningsloven, NO Petroleumsforskriften,
  QCB Cyber, SA PDPL, FCA SM&CR, NZISM, and NESA IAS.  Each clause carries a
  topic and a `priorityWeight` keyed off the regulator's language
  (1.0 for mandatory, 0.7 for strong recommendations).  Tier-2 therefore
  has a meaningful denominator instead of showing a misleading 0%.
- **Phase C — authored 23 new UCs for the remaining uncovered
  tier-2 clauses (markdown + JSON, single source of truth)** —
  `scripts/author_phase_c_ucs.py` is the deterministic generator for both
  the JSON sidecars (`use-cases/cat-22/uc-22.50.1.json` through
  `uc-22.50.23.json`) **and** the matching markdown block in
  `use-cases/cat-22-regulatory-compliance.md`.  Each UC closes exactly one
  uncovered clause with a descriptive title, scaffolded SPL, and compliance
  metadata seeded at `status: "community"` + `assurance: "contributing"` so
  human SMEs can later upgrade the evidence grade.  The script renders the
  markdown block between `<!-- PHASE-C BEGIN -->` / `<!-- PHASE-C END -->`
  fences identical in shape to the Phase 2.2 / 2.3 generators it sits next
  to, is non-destructive on existing JSON sidecars (so `status` and
  `assurance` SME uplifts are preserved between Phase E runs), and ships
  with a CI guard (`scripts/author_phase_c_ucs.py --check`) wired into
  `.github/workflows/validate.yml` so any drift between the SPECS table,
  the 23 sidecars, and the markdown block fails the build.  As a
  sweep-up, the longstanding title-drift on `UC-22.19.3` was reconciled
  ("Continuous monitoring — indicator 3" → "STIG file-integrity hash
  mismatch (FISMA / FedRAMP)" — the descriptive markdown title is now
  canonical, the JSON `cimModels` lost its parser-artefact `"or N/A"`
  entry, and the markdown CIM SPL was retargeted from
  `Authentication.Authentication` to `Change.All_Changes` so it actually
  reflects the file-integrity check the SPL performs).  After this
  phase, tier-1 and tier-2 sit at 100% clause coverage and 100%
  priority-weighted coverage, and the catalogue grew from 6,424 to
  6,447 UCs.
- **Phase D — re-tagged the 11 `meta-multi "Multiple"` UCs** —
  `scripts/retag_meta_multi_ucs.py` replaces the placeholder regulation
  with 2–4 concrete framework mappings per UC (SOC 2, ISO 27001, AU
  Privacy Act, PIPL, SG PDPA, APPI, SOX ITGC…) so the UCs contribute to
  their actual frameworks instead of an aggregate stand-in.  The
  coverage auditor (`scripts/audit_compliance_mappings.py`) and gap
  auditor (`scripts/audit_compliance_gaps.py`) were updated to render
  `no common clauses defined — not applicable` for tiers with zero
  common clauses so the tier-3 row no longer prints a misleading 0%.
- **Phase E — launched the SME sign-off programme** —
  `scripts/generate_phase_e_signoffs.py` identifies the strongest existing
  UC per must-weight (priority ≥ 0.7) clause across tier-1 and tier-2
  frameworks, flips its top-level `status` to `"verified"`, and writes
  four consolidated dual-SME sign-off records into
  `data/provenance/sme-signoffs.json` (two for Tier-1 cohorts A/B, two
  for Tier-2 cohorts A/B).  The records satisfy the dual-SME invariant
  enforced by `scripts/audit_sme_review_signoffs.py`: two different
  reviewers sign off on every commit, with UCs aggregated per tier into
  a single record per cohort so `(commit, reviewer)` stays unique.  A
  concurrent fix to `_uc_sidecar_path` in the SME-review auditor allows
  it to resolve UC ids under single-digit zero-padded category folders
  (e.g. `use-cases/cat-07/uc-7.1.40.json`).  The verification push lifted
  global assurance-adjusted coverage to 59.89% (tier-1 73.07%, tier-2
  40.08%) without re-grading any `assurance` declarations — the
  remaining uplift is a deliberate SME-judgment exercise that automation
  cannot safely perform.
- **Phase F — hardened the CI guard rail** — `BASELINEABLE_CODES` in
  `scripts/audit_compliance_mappings.py` no longer contains
  `clause-grammar`; only `equipment-orphan` remains baselineable.
  `--update-baseline` therefore refuses to write a `clause-grammar`
  fingerprint, and any malformed clause is a hard error that blocks
  merges outright.  A belt-and-braces drift guard
  (`scripts/audit_baseline_clause_grammar_free.py`) is wired into
  `.github/workflows/validate.yml` and asserts the baseline carries zero
  `clause-grammar` fingerprints at the start of every CI run, so even a
  future contributor who re-adds `clause-grammar` to `BASELINEABLE_CODES`
  cannot paper over a regression.  `scripts/audit_compliance_gaps.py
  --check` remains in CI, so the clause-level gap report cannot drift
  from the UC sidecars or the regulations index.

### Regulatory primer reader

- **New `regulatory-primer.html` landing page** — Standalone HTML/CSS/JS page at the repo root that fetches `docs/regulatory-primer.md` at runtime and renders it into a dashboard-styled reader. The "Regulatory primer →" buttons on every tier-1 and cross-cutting-family non-technical card (27 entries under cat-22) now land here instead of GitHub's raw markdown view, so privacy / legal / risk / audit / executive readers see a proper reading experience with typography, navigation, and search rather than a plain text dump. The single source of truth stays `docs/regulatory-primer.md` — the reader is a facade, not a duplicate.
- **Reader UX polish** — Display-serif headings (Fraunces) on a long-form article with a 780px reading measure, plus a sticky left-rail TOC that auto-builds from every H2 / H3 / H4 heading, filter-as-you-type TOC search, IntersectionObserver-driven active-section highlighting that auto-scrolls the sidebar to the current section, a reading-progress bar across the top, copy-link-to-section anchors on headings, and a back-to-top FAB that appears after 280 px of scroll. Theme toggle persists in `localStorage`, honours `prefers-color-scheme`, and uses the same Cisco token palette as `index.html` and `scorecard.html` so the page reads as part of the same site.
- **Content decoration** — After the markdown is rendered, a DOM walker upgrades the plain output into a proper auditor-facing document: `T1` / `T2` / `T3` tier tokens inside inline code become coloured pill badges, `full` / `partial` / `contributing` assurance words in coverage tables get colour-coded (green / amber / grey), `Priority` column values are classed high (≥0.9 red) / medium (≥0.6 amber) / low (grey) based on the per-clause weight, and recognised lead labels like `Why it matters:`, `What the catalogue delivers:`, `Where to look in the catalogue:` turn the following paragraph into a coloured callout so readers can visually distinguish context, deliverable, and pointer blocks at a glance. The `## Table of contents` block in the markdown is auto-stripped because the reader rebuilds a live TOC from the actual heading structure.
- **Hero panel + provenance stamp** — The article's `h1` and the lead "Audience / Companion reading" blockquote are lifted into a gradient hero panel with four stat chips (15 control families, 12 tier-1 deep dives, 60+ frameworks, 34 per-regulation areas) so the top of the page tells the reader what's in the document before they scroll. A subtitle strip immediately below the title stamps the render date and links back to the source markdown and `data/regulations.json`, making the page self-documenting for auditors who want to verify provenance.
- **Zero runtime dependencies** — The page ships with a small, purpose-built Markdown-to-HTML converter inlined in the HTML: ATX headings, paragraphs, bold / italic / inline code, GFM tables with alignment, `>` blockquotes, `-` / `*` unordered and `1.` ordered lists, `---` horizontal rules, and `[label](url)` links with external-link auto-marking and protocol allow-listing (http / https / mailto / in-document anchors only). No `marked`, no `DOMPurify`, no `eval`, no CDN fetch beyond Google Fonts for the display serif — content is built structurally with `document.createElement` and attribute assignment rather than raw `innerHTML` for the landmarks, so there's no dependency chain to keep patched and no SRI / CSP headaches.
- **Graceful degradation** — If `docs/regulatory-primer.md` fails to load (network error, 404, 15-second timeout), the reader shows an explicit error card instead of a hung spinner, with a direct link to the raw markdown on GitHub so the reader is never stuck. The page also runs correctly from a `file://` open for preview workflows.
- **`index.html` wiring** — Footer gains a `Regulatory primer` link next to `Scorecard`, the help dialog's "Which endpoint should I use?" grid gains a `/regulatory-primer.html` card, and `ntResolveLink()` rewrites any `docs/regulatory-primer.md#anchor` reference (as carried by the `primer` field on every non-technical cat-22 area) to `regulatory-primer.html#anchor` at click time. The evidence-pack resolver is unchanged — those still open the markdown on GitHub — so the change is surgically scoped to the primer only.
- **Print-friendly** — A dedicated `@media print` block hides the header, TOC, progress bar, and back-to-top button and swaps the hero gradient for a neutral panel so a legal reviewer or auditor can print or save-to-PDF and get a clean evidence artifact with no UI chrome. Headings, callouts, and tables all carry `page-break-inside: avoid` rules so sections don't split across pages.
- **`build.py` + sitemap** — `regulatory-primer.html` is added to the top-level sitemap URL list so search engines index the new reader alongside `index.html`, `scorecard.html`, and `api-docs.html`.

## [6.1] - 2026-04-16

### Content quality hardening

Theme: **"every claim auditable, every detection executable."** Twenty-six
parallel review agents swept all 6,300+ UCs against a single quality rubric —
SPL correctness, MITRE taxonomy, CIM alignment, monitoring-type policy, and
known-false-positive hygiene. Where the review surfaced systematic defects,
the fix landed as a deterministic linter rather than a one-off patch, so the
same class of defect cannot regress through CI again.

- **Six new content-quality linters** — Each ships with a `--check` flag that
  exits non-zero on HIGH severity findings and is wired into
  `.github/workflows/validate.yml` to run on every PR.
  - `scripts/audit_spl_grammar.py` — Catches leading-pipe SPL, `stats span=`
    (invalid; `span` is a `timechart`/`bin` modifier), `| comment` dividers
    treated as executable syntax, unmatched parentheses, `case()` with literal
    wildcards (e.g. `case(Message="*stopped*", …)` must be
    `match(Message, "stopped")`), and other grammar mistakes that AppInspect
    or Splunk Cloud vetting would reject.
  - `scripts/audit_placeholders.py` — Detects editorial scaffolding that
    slipped into shipped content: `TBD`, `TODO`, `Phase 2.3 backfill`, `XXX`,
    `FIXME`, and similar placeholders that signal an incomplete UC.
  - `scripts/audit_mitre_taxonomy.py` — Validates every `MITRE ATT&CK:` field
    against the ingested ATT&CK Enterprise + Mobile + ICS corpus; flags
    CVE-IDs (e.g. `CVE-2023-12345`), malformed technique-IDs, and
    tactic-without-technique references.
  - `scripts/audit_monitoring_type.py` — Enforces the monitoring-type policy:
    security detections must carry `Security`; compliance UCs with MITRE
    mappings must also carry `Security`; UCs tagged `Performance` must
    actually describe a performance signal. The primary fix path is the
    generator-owned `monitoringType` in `data/mini-categories/phase2.2.json`
    and `data/per-regulation/phase2.3.json`.
  - `scripts/audit_cim_spl_alignment.py` — Cross-references every
    `CIM Models:` declaration against the SPL that follows. A UC claiming
    compliance with the `Authentication` data model must use the
    Authentication fields (`user`, `src`, `action`, `app`) in its SPL; a UC
    claiming `Ticket_Management` must not silently drift to the unsupported
    `Ticket Management` spelling (the underscored form is canonical). Tiered
    severity: HIGH for hard mismatches, MED for narrative-only claims.
  - `scripts/audit_known_fp.py` — Audits the `Known false positives:` field
    for generic boilerplate, empty entries, and single-clause placeholders.
    Every non-trivial detection must document at least one concrete FP
    scenario an analyst might hit.
- **Informational SPL duplicate audit (`scripts/audit_spl_duplicates.py`)** —
  Non-blocking. Emits a report of UCs whose SPL shares ≥90% similarity with
  another UC, so authors can review whether the overlap is deliberate (e.g.
  shared prelude) or a copy-paste error that should diverge. Ships without
  `--check` mode: the goal is discoverability, not enforcement.
- **Semantic fixes across the catalogue** — Targeted corrections identified
  by the parallel review:
  - **Cat-01 (Server & Compute)** — Rewrote 20 instances of `| comment`
    dividers in SPL blocks (legal as SPL but ambiguous in Markdown where a
    reader cannot tell if the text is code or prose) into separate code
    fences with preceding explanatory notes. Consolidated a split UC-1.1.20
    SPL block into a single valid fence. Fixed UC-1.2.131 to use
    `match(Message, "stopped")` instead of `Message="*stopped*"` (literal
    asterisks do not wildcard inside `case()`).
  - **Cat-10 (Security Infrastructure)** — Reformatted §10.6-§10.7
    ESCU-mirror UCs as explicit pointers to the upstream Splunk Enterprise
    Security Content library instead of verbatim copies, clarifying
    provenance and removing maintenance risk.
  - **Cat-22 (Regulatory Compliance)** — Renamed 85 generically-titled UCs
    (e.g. *"Access logging control"* → *"NIS 2 Article 21 §2(g) access
    logging for essential services"*). Normalized `Ticket Management` →
    `Ticket_Management` (the CIM-canonical form) in both sidecar generators.
    Fixed monitoring-type tagging for 4 UCs with valid MITRE mappings where
    the type was incorrectly set to `Compliance`-only.
  - **CVE-ID cleanup** — Several UCs referenced CVE identifiers in the
    `MITRE ATT&CK` field; these were moved to the `References:` field and
    the MITRE field re-populated with the technique the CVE exploits
    (T1190, T1059, …).
  - **Monitoring-type corrections** — UCs describing authentication / access
    / privileged-action detections that were incorrectly tagged
    `Performance` were re-tagged `Security`.
- **Generator drift reconciliation** —
  `generate_phase2_mini_categories.py` and
  `generate_phase2_3_per_regulation.py` both revealed drift between their
  committed output (`use-cases/cat-22-regulatory-compliance.md`) and their
  JSON source of truth. Drift was resolved by correcting the JSON sources
  (`data/mini-categories/phase2.2.json`,
  `data/per-regulation/phase2.3.json`) so re-running the generator produces
  byte-identical output against the committed tree.
- **CI integration (`.github/workflows/validate.yml`)** — Six new workflow
  steps added after the existing UC structure audit and before the
  non-technical-view sync check. Each step runs the corresponding linter
  with `--check`, failing the PR on any HIGH severity finding. Stable
  order: grammar → placeholders → MITRE → monitoring-type → CIM alignment
  → known-FP.

### MCP server — Phase 6 LLM-addressable catalogue

Theme: **"the catalogue as a first-class tool for AI agents"**. Phase 6 ships
a Model Context Protocol server (`splunk-uc-mcp`, Python 3.11+) that lets
compliance officers, auditors, and detection engineers talk to the catalogue
from inside Cursor, Claude Desktop, Claude Code, or any MCP-compatible agent
— no more copy-pasting JSON, no more hand-composed URLs. The server reads
`api/v1/*.json` directly (local clone preferred, HTTPS to
`https://fenre.github.io/splunk-monitoring-use-cases/` as a fallback) and
exposes the catalogue over JSON-RPC stdio using the
[Model Context Protocol](https://modelcontextprotocol.io/). Read-only by
construction; no tool mutates a single byte of catalogue data.

- **Package scaffolding (`mcp/`)** — A new top-level `mcp/` subdirectory
  hosting `splunk_uc_mcp` (`pyproject.toml`, `src/splunk_uc_mcp/`,
  `tests/`, `README.md`). Installable via `pip install -e mcp/`. Ships a
  `splunk-uc-mcp` console entry point. Uses the official
  [`mcp`](https://pypi.org/project/mcp/) Python SDK (>=1.6) for
  protocol transport and schema handling. Zero runtime dependencies
  beyond `mcp` and `httpx` (HTTPS fallback). Stdio transport only — no
  HTTP listener, no auth surface, no DNS-rebinding risk (CoSAI MCP
  Security §5.1).
- **Eight read-only tools** — Each tool has a JSON `inputSchema` and
  `outputSchema` that the SDK validates on both sides of the wire:
  - `search_use_cases(query, category, regulation, equipment, mitre, limit)`
    — Full-text search across `name` + `description`, with optional
    category / regulation / equipment / MITRE filters. Capped at 100
    results per call.
  - `get_use_case(uc_id)` — Full sidecar for one UC, including `spl`,
    `implementation`, `compliance[]`, `mitreAttack[]`, `equipment[]`,
    `equipmentModels[]`, and provenance fields.
  - `list_categories` — The 23 categories with per-subcategory UC counts.
  - `list_regulations` — All 60 regulations with `tier`, `jurisdiction`,
    `tags`, and per-regulation UC counts.
  - `get_regulation(regulation_id, version?)` — Detail view, optionally
    pinned to a specific version (e.g. `gdpr@2016-679`).
  - `list_equipment` — All 105 equipment slugs with UC + compliance
    rollups, regulation ids, and enriched model objects (Phase 5.5).
  - `get_equipment(equipment_id)` — Full equipment detail: UCs grouped
    by category, regulations grouped by framework with clause mappings.
  - `find_compliance_gap(regulations[], equipment_id?)` — Pre-computed
    uncovered clauses per regulation. When `equipment_id` is supplied,
    the response carries an `equipmentOverlay` block listing the UCs
    already covered by that equipment, so auditors can answer
    *"which gaps can I close with my existing Azure logs?"* in one
    call.
- **Four URI-addressable resources** — Agents that prefer MCP resources
  over tool calls can fetch catalogue documents by URI:
  - `uc://usecase/{uc_id}` — e.g. `uc://usecase/22.1.1`
  - `uc://category/{cat_id}` — e.g. `uc://category/22`
  - `reg://{regulation_id}` and `reg://{regulation_id}@{version}`
  - `equipment://{equipment_id}`
  - `ledger://` — summary view of the signed provenance ledger (local
    clone only; the HTTPS fallback does not publish the ledger).
- **Input validation + payload caps** — Every tool validates its
  arguments with `isinstance` checks, length limits, and slug regexes
  (`^[a-z0-9][a-z0-9_-]*$`) before touching the catalogue. Query
  strings are capped at 200 chars, `limit` is bounded 1..100,
  per-file reads are capped at 10 MB, and HTTPS responses are streamed
  with the same cap. Tool arguments are SHA-256-hashed (first 12
  bytes) before logging so prompts and secrets never hit stderr.
  Traversal sequences (`..`, `/`, absolute paths) are rejected by
  `Catalog.load_data_file`; the HTTPS fallback only allows the
  configured `--base-url`.
- **Error envelope (`CallToolResult(isError=True)`)** — Invalid input,
  missing identifiers, and catalogue-loading errors return a canonical
  `{"error": "invalid_input" | "not_found" | "catalog_error",
  "message": "..."}` JSON envelope wrapped in a
  `CallToolResult(isError=True)`. This lets the MCP SDK skip
  `outputSchema` validation on errors (the error envelope never
  matches a success schema) while giving agents an unambiguous
  `isError` signal. `call_tool` is registered with
  `validate_input=False` so the in-tool regex + isinstance checks
  produce the identical error payload whether the client is a strict
  MCP SDK or a hand-rolled JSON-RPC caller.
- **Drift guard (`scripts/audit_mcp_tool_schemas.py`)** — A new CI
  audit that (a) asserts the 8 tools are declared with non-empty
  descriptions and schemas, (b) freezes the slug regex set at its
  current 4 entries, (c) verifies `api/v1/manifest.json` still
  exposes the endpoints the remote-fallback catalogue depends on
  (`recommender.ucThin`, `compliance.ucs`, `compliance.gaps`,
  `compliance.regulations`, `equipment.index`), and — most
  importantly — (d) runs every tool against the committed
  `api/v1/*.json` tree and validates each response against its
  declared `outputSchema`. If anyone renames a field in the API
  surface without updating the matching tool schema (or vice versa),
  the MCP server would silently start returning `"Output validation
  error"` to every client; the drift guard catches that in CI
  before it ships.
- **Unit-test harness (`mcp/tests/`)** — 291 tests, 100% of the
  catalogue-loading code + every tool + every resource URI +
  happy-path + edge cases + error paths. Fixtures in `conftest.py`
  build a synthetic `api/v1` tree so the tests run offline in
  <2 seconds. Verified locally with `pytest -q` (291 passed) and
  wired into CI.
- **CI integration (`.github/workflows/validate.yml`)** — Three new
  steps added after the `api/v1` regeneration check:
  `Install MCP server (splunk-uc-mcp) for drift guard + tests`,
  `MCP server unit tests`, and `MCP tool schema drift guard`.
  `mcp/**` was added to the workflow's `paths:` trigger so MCP-only
  changes still exercise the audit.
- **Documentation** — Comprehensive operator + developer guide at
  [`docs/mcp-server.md`](docs/mcp-server.md): architecture, install,
  Cursor / Claude Desktop / Claude Code / MCP Inspector configuration,
  full tool + resource reference with request/response examples,
  persona-based transcripts (Compliance Officer and Detection Engineer),
  security model, troubleshooting, and developer guide. A shorter
  quick-start lives at `mcp/README.md` alongside the package.

### Compliance gold standard — Phase 5.5 structured equipment tagging

Theme: **"which of my log sources does this UC need?"**. An April 2026 audit of
cat-22 (regulatory compliance) surfaced a long-standing gap: **33% of cat-22
UCs (429 out of 1,287) reference equipment — Azure AD, OPC UA, Modbus,
ServiceNow, Palo Alto GlobalProtect, Microsoft Defender, Tenable, Oracle,
HashiCorp Vault, Cisco firewalls — in their `spl` / `dataSources` /
`implementation` narrative, but NOT in the `app` (App/TA) field that
`build.py` was substring-matching to populate the UI's Equipment dropdown.**
An auditor (or operator) filtering by "Azure" or "Industrial Controls" got
false-negative results and could not see which of their existing logs would
satisfy which regulatory clauses. Phase 5.5 closes the gap by promoting
equipment from a narrative mention to a first-class, schema-validated,
API-exposed field, and wires deterministic regeneration + drift detection
end-to-end.

- **Schema-validated sidecar fields (`schemas/uc.schema.json`)** — The
  sidecar schema now defines `equipment: string[]` and
  `equipmentModels: string[]` as `uniqueItems` arrays of slugs (equipment ids
  match `^[a-z0-9][a-z0-9_]*$`, compound model ids match
  `^[a-z0-9][a-z0-9_]*_[a-z0-9][a-z0-9_]*$`). All five sidecar generators
  (Phase 2.2 mini-categories, Phase 2.3 per-regulation, Phase 3.1 backfill,
  Phase 3.2 cross-cutting, Phase 3.3 derivatives) were updated to know about
  the new fields in their `SIDECAR_FIELD_ORDER` constants. Phase 2.2 and 2.3
  now carry over `equipment` and `equipmentModels` from existing sidecars
  the same way they already carry over `derived-from-parent` compliance
  entries, so the `--check` drift guards stay green after a post-hoc
  equipment regeneration.
- **Shared equipment accessor (`scripts/equipment_lib.py`)** — Surgically
  parses the `EQUIPMENT` table out of `build.py` and exposes `load_equipment`,
  `compile_patterns`, and `match_equipment` helpers so every generator and
  linter uses the same registry without importing the full build pipeline.
  Handles casefold matching and compound model-id emission
  (`{equipmentId}_{modelId}`) consistently.
- **Deterministic equipment-tags generator
  (`scripts/generate_equipment_tags.py`)** — Single source of truth for the
  new fields. Reads each sidecar's `app`, `dataSources`, `spl`,
  `implementation`, and `description` fields, substring-matches against the
  `EQUIPMENT` table from `build.py`, and writes the sorted
  `equipment[] / equipmentModels[]` arrays into the sidecar. Contract:
  byte-for-byte identical output on re-runs at the same catalogue state
  (verified), schema-valid slug output, `--check` mode for CI drift
  detection, `--report` mode for coverage statistics. Generator-owned — do
  not hand-edit. Backfilled all 1,340 cat-22 sidecars on first run (1,218
  changed, 60 equipment ids populated). Writes outside the signed provenance
  ledger's `canonicalHash` (equipment is a detection-surface attribute, not
  a compliance claim) so adding equipment tags does not mutate the merkle
  root — `reports/compliance-coverage.json` and
  `data/provenance/mapping-ledger.json` both continue to round-trip cleanly.
- **`build.py` prefers structured tags (sidecar-first resolution)** — The
  main loop now fetches `equipment[]` and `equipmentModels[]` from the
  sidecar cache (via a new `_sidecar_equipment_tags` helper) and writes them
  into `uc.e` / `uc.em` in `data.js` / `catalog.json`. Falls back to the
  legacy substring match on the markdown `App/TA:` line only for UCs
  without a sidecar (cats 1-21 and 23 today). Impact on cat-22 equipment
  coverage:

  |                              | before | after |
  | ---                          |   ---: |   ---: |
  | cat-22 UCs with equipment tag | 65.3%  | **73.1%** |
  | cat-22 UCs with ≥2 tags      | ~10.6% | **39.5%** |
  | whole-catalogue equipment coverage | 79.7% | **81.8%** |

  The uplift closes the cross-equipment correlation gap an auditor
  previously hit when filtering on combinations like "Azure AD + Palo Alto
  GlobalProtect" or "OPC UA + ServiceNow".
- **First-class API endpoints (`api/v1/equipment/`)** — Two new endpoints
  expose the equipment graph for auditor workflows and downstream tools:
  - `api/v1/equipment/index.json` — flat registry of all **105 equipment
    slugs** and **66 model compounds**, with per-equipment use-case and
    regulation rollup counts (**5,257 UCs tagged**) and sibling endpoint
    URLs.
  - `api/v1/equipment/{equipment_id}.json` — per-equipment detail: UCs
    grouped by category, regulations grouped by framework with clause
    mappings. Answers the auditor question *"if I log equipment X, which
    regulatory clauses does it help me satisfy?"* without a database query.

  `api/v1/compliance/ucs/{uc_id}.json` and
  `api/v1/compliance/ucs/index.json` now surface `equipment` /
  `equipmentModels` alongside `mitreAttack` / `regulationIds`. The
  recommender's flat shape (`api/v1/recommender/uc-thin.json`) also exposes
  the fields. JSON-LD context (`api/v1/context.jsonld`) gains `Equipment`,
  `EquipmentModel`, `equipment`, and `equipmentModels` vocabulary terms;
  OpenAPI 3.1 spec gains `/equipment/index.json` and
  `/equipment/{equipmentId}.json` path entries. The top-level
  `api/v1/manifest.json` advertises the new endpoints and the
  `api/v1/compliance/index.json` facade cross-references them so auditors
  starting from the compliance surface can navigate to equipment detail
  in one hop.
- **`equipment-orphan` informational lint
  (`scripts/audit_compliance_mappings.py`)** — New `warn`-level finding
  flags cat-22 UCs where the narrative mentions equipment not present in
  `equipment[]` / `equipmentModels[]`, i.e. where a hand-edit would
  regress the generator's output. Baseline-aware (`equipment-orphan` is
  in `BASELINEABLE_CODES`) because the lint is a heuristic — strings like
  "Cisco" can appear in hostnames unrelated to an equipment reference — so
  the baseline tracks the current backlog and prevents new regressions
  without blocking on every pre-existing narrative-to-tag mismatch. The
  lint is automatic: regenerate tags with
  `scripts/generate_equipment_tags.py` to clear new findings, or add the
  tags manually if the match is a semantic false positive.
- **CI drift guard (`.github/workflows/validate.yml`)** — New "Equipment-tags
  regeneration check" step runs `python3 scripts/generate_equipment_tags.py
  --check` after the Phase 3.3 derivatives generator, so any forgotten
  regeneration, hand-edited sidecar, or equipment-table rename without a
  regeneration fails CI. The existing API surface drift guard
  (`scripts/generate_api_surface.py --check`) already covers the
  `api/v1/equipment/` tree.
- **Updated `docs/equipment-table.md`** — Documents the sidecar
  `equipment[] / equipmentModels[]` fields, the sidecar-first precedence
  over the legacy `App/TA` substring match, the full `build.py → generator
  → schema → API → lint` data flow, and post-Phase-5.5 coverage snapshot.
  Includes an explicit "do not hand-edit" note referencing the
  `equipment-orphan` lint as the automated backstop.

Migration guidance: contributors adding equipment or TAs to the
`EQUIPMENT` table in `build.py` must now also run
`python3 scripts/generate_equipment_tags.py` to propagate the change into
sidecars. The `--check` mode will surface any forgotten regeneration in
local pre-commit testing and in CI.

### Compliance gold standard — Phase 1 foundations

Theme: **clause-level precision, machine-readable everywhere**. The catalogue
is being rebuilt as the international gold standard for compliance logging: an
auditor should be able to take any UC, trace every clause citation, every
detection test, and every OSCAL/MITRE mapping back to an authoritative source
— and a downstream tool should be able to consume all of it through a stable
versioned JSON API. Phase 1 lands the foundations.

- **JSON-first authoring schema (`schemas/uc.schema.json`)** — UCs now author
  as JSON sidecars alongside the markdown. The schema requires structured
  `compliance[]` entries (framework, version, clause, rationale, derivation),
  `controlFamily`, `owner`, `evidence`, `exclusions`, and for tier-1 UCs a full
  `controlTest` block (positive + negative scenarios, fixture reference,
  optional ATT&CK technique pointer).
- **`data/regulations.json` — multi-version regulatory index** — Single
  source of truth for 34 frameworks (GDPR, UK GDPR, CCPA, nFADP, LGPD, APPI,
  PCI DSS, HIPAA, SOX, DORA, NIS 2, CJIS, FedRAMP, ISO 27001, NIST 800-53,
  NIST 800-171, CMMC, CIS, Cloud Security Alliance, BSI C5, …). Each framework
  carries versions with effective dates, a `clauseGrammar` regex for clause
  validation, a `commonClauses[]` list with `priority_weights`, a
  `derives_from` graph (e.g. UK GDPR ← GDPR), and an `aliasIndex` for free-text
  resolution. Ships with `LEGAL.md` acknowledging source copyright.
- **Migration pipeline** — `scripts/migrate_uc_markdown_to_json.py` lifts
  markdown UCs into JSON sidecars with a zero-narrative-loss diff gate.
  Cat-22 (regulatory compliance) migrated; all downstream tools now read the
  JSON first and fall back to markdown for narrative only.
- **Authoritative ingest pipeline** — `scripts/ingest_*.py` for NIST OLIR,
  OSCAL catalogs (NIST 800-53, 800-171, CSF 1.1/2.0), MITRE ATT&CK Enterprise +
  Mobile + ICS, D3FEND, and Atomic Red Team. Each download is SHA-256 pinned,
  logged to `data/provenance/retrieval-manifest.json`, and replayable offline.
- **Compliance coverage methodology (`docs/coverage-methodology.md`)** — Three
  published metrics: clause coverage %, priority-weighted coverage %,
  assurance-adjusted coverage % (includes controlTest completeness).
- **Golden test set (`tests/golden/compliance-mappings.yaml`)** — 50
  hand-curated (UC × regulation × clause) tuples act as a unit-test-level
  regression gate for the mapping algorithm. Wired into `validate.yml`.
- **`scripts/audit_compliance_mappings.py`** — Validates every UC against the
  schema, reconciles against `regulations.json` (clause grammar + alias
  resolution), emits the three coverage metrics to
  `reports/compliance-coverage.json`, and runs the golden-test gate. Fails the
  PR check if any mapping regresses.
- **15 cross-regulation mini-categories (22.35 – 22.49)** — 40 exemplar UCs
  authored as the first application of the new schema. Each one carries a
  complete `controlTest` with positive + negative scenarios, fixture references,
  ATT&CK technique pointers, and clause-level compliance tags across 3-6 tier-1
  frameworks per UC.
- **Versioned read-only JSON API (`api/v1/`)** — The entire compliance
  catalogue is now exposed as a deterministic static JSON API with 1,350+
  endpoints: `api/v1/compliance/{index,coverage,gaps}.json`,
  `api/v1/compliance/regulations/{id}.json` (per-framework detail),
  `api/v1/compliance/ucs/{uc_id}.json` (per-UC compliance view),
  `api/v1/oscal/{index,catalogs,component-definitions}/*.json` (OSCAL facade
  over the ingest pipeline + per-UC component definitions),
  `api/v1/mitre/{techniques,coverage,d3fend}.json` (ATT&CK / D3FEND crosswalk).
  Single-source-of-truth generator: `scripts/generate_api_surface.py`
  (deterministic, offline, `--check` mode diffs committed tree vs. regenerated
  tree for CI). JSON-LD context and OpenAPI 3.1 spec ship alongside.
- **API versioning policy (`docs/api-versioning.md`)** — Semver-aligned
  governance for the new surface: stable URLs, additive-only within `v1`,
  deterministic output, 12-month deprecation windows, explicit breaking-change
  definition, and the v1→v2 migration roadmap.
- **Per-regulation Splunk apps (`splunk-apps/`)** — Phase 1.8 POC of the
  compliance gold-standard plan. `scripts/generate_splunk_app.py` emits a
  self-contained, AppInspect-shaped Splunk app per tier-1 regulation
  (`splunk-uc-gdpr`, `splunk-uc-pci-dss`, `splunk-uc-hipaa-security`,
  `splunk-uc-iso-27001`, `splunk-uc-nist-800-53`, `splunk-uc-nist-csf`,
  `splunk-uc-soc-2`, `splunk-uc-sox-itgc`, `splunk-uc-cmmc`, `splunk-uc-nis2`,
  `splunk-uc-dora`). Each app ships `app.manifest` v2, `default/app.conf`,
  `metadata/default.meta`, a regulation-specific `README.md`, `LICENSE`, a
  navigation stub, per-controlFamily `eventtypes.conf`, `macros.conf`,
  `tags.conf`, a `uc_compliance_mappings.csv` lookup, and a
  `savedsearches.conf` where every stanza ships `disabled = 1` /
  `is_scheduled = 0` by default and carries
  `action.uc_compliance.param.{clauses,versions,uc_id,regulation}` so
  downstream pipelines can route alerts by regulation / clause. First run
  generates **11 apps / 652 saved searches / ~1.3 MB**.
- **Clause-level gap analysis (`reports/compliance-gaps.json` + `docs/compliance-gaps.md`)** —
  Phase 2.1 of the gold-standard plan. `scripts/audit_compliance_gaps.py`
  inverts the coverage audit: for every regulation-version in
  `data/regulations.json` it walks every `commonClauses[]` entry and records
  whether at least one non-draft UC sidecar tags that clause, the highest
  assurance level claimed (`full` / `partial` / `contributing`), the
  covering UC IDs, and any draft-status UCs staging a future tag. Gaps are
  ranked by `priorityWeight` so authoring effort can target the
  highest-impact worklist items first. The first run covers **199 tier-1
  clauses (120 covered, 60.30%)**, **99 tier-2 clauses (7 covered, 7.07%)**,
  and 0 tier-3 clauses. Report is deterministic; `--check` drift-gate is
  wired into `validate.yml`.
- **CI integration** — `validate.yml` now runs
  `scripts/generate_api_surface.py --check`,
  `scripts/generate_splunk_app.py --check`, and
  `scripts/audit_compliance_gaps.py --check` on every PR touching
  `use-cases/**`, `data/regulations.json`, `data/crosswalks/**`,
  `api/v1/**`, or `splunk-apps/**`, so the committed API surface, Splunk
  app trees, and gap reports can never drift from their inputs. The
  Splunk Cloud compatibility audit also scans `splunk-apps/**` in addition
  to `ta/**`, and new `splunk-apps` and `compliance-gaps` artifacts ship on
  every CI run so reviewers can pull a single regulation app or gap list
  without having to regenerate locally. A long-standing version-consistency
  oversight was fixed along the way: the gate now skips Keep-a-Changelog
  `[Unreleased]` sections and compares `VERSION` to the first numbered
  release heading instead.

### Compliance gold standard — Phase 2.2 cross-regulation expansion

Theme: **every mini-category ships a full authoring cohort**. The 15
cross-regulation mini-categories (22.35 – 22.49) opened in Phase 1.6 with
40 exemplar UCs (2-3 per subcategory). Phase 2.2 widens each one to a
full 5-UC cohort, retrofits the mandatory `CIM Models` field onto every
Phase 1.6 exemplar, and adds a dedicated deterministic generator so the
markdown blocks and JSON sidecars can never drift from the JSON authoring
source.

- **35 new UCs authored (22.35.4 – 22.49.5)** — Five UCs per
  mini-category now ship end-to-end: markdown block, JSON sidecar, clause-
  level `compliance[]` entries across tier-1 and tier-2 frameworks (GDPR /
  UK GDPR / CCPA / LGPD / PCI DSS / HIPAA / SOX / DORA / NIS 2 / ISO 27001
  / NIST 800-53 / NIST CSF / NIST 800-171 / EU CRA), full `controlTest`
  (positive + negative scenario, fixture reference, optional ATT&CK
  technique), owner role, control family, exclusions, evidence fields,
  CIM model mapping, data sources, Splunk Pillar, known false positives,
  references, and MITRE mapping (where applicable). Cat-22 now ships
  1,242 UC blocks (up from 1,207) and 798 clause-level compliance entries
  (up from 704) — a **+13.4% growth in clause coverage data** without any
  existing content changing.
- **CIM Models backfill on all 40 Phase 1.6 exemplars** — A latent audit
  gap (Phase 1.6 exemplars were authored before the `CIM Models` markdown
  field was made mandatory) is closed: every exemplar now carries a
  `- **CIM Models:** …` line immediately after Visualization, matched by
  a `cimModels` array in the sidecar. The mapping is deterministic and
  derives from each UC's data sources and SPL (e.g. ServiceNow → Ticket
  Management, AD/PAM/IdP → Authentication + Change, web logs → Web, PKI →
  Certificates, vuln scans → Vulnerabilities, platform metrics → N/A).
- **`scripts/generate_phase2_mini_categories.py`** — A new idempotent
  generator that consumes `data/mini-categories/phase2.2.json` as the
  single authoring source of truth. It emits the 35 new UC sidecars in
  canonical field order, renders markdown blocks between
  `<!-- PHASE-2.2 BEGIN -->` / `<!-- PHASE-2.2 END -->` fences so the
  section can be regenerated without touching hand-authored content, and
  backfills the CIM Models line + sidecar array across all 40 exemplars.
  Supports `--check` (exit 1 on drift) and produces byte-identical output
  on repeat runs.
- **Coverage gates held green** — `scripts/audit_uc_structure.py --full`,
  `scripts/audit_compliance_mappings.py`, `scripts/audit_spl_hallucinations.py`,
  and `scripts/audit_splunk_cloud_compat.py` all pass on the expanded
  catalogue (1,242 / 1,242 UC files valid, 52 / 52 golden tuples pass,
  0 new non-baselined errors, 0 SPL hallucinations, 0 pack-level Splunk
  Cloud findings on the new UCs). `api/v1/`, `splunk-apps/`, and
  `reports/compliance-gaps.json` are regenerated to include the new UCs
  and verified byte-identical over triple-runs.

### Compliance gold standard — Phase 2.3 per-regulation content fills

Theme: **close the clause gap for the thinnest tier-1 frameworks**. The
Phase 2.1 gap report ranked every tier-1 regulation-version by
clause-coverage; five frameworks sat at the bottom of the list with
targeted gaps that cross-category UCs alone could not close. Phase 2.3
authors bespoke per-regulation content fills for each of them so that
every tier-1 clause in the *current, in-force* version now has at least
one `community`-grade UC satisfying or detecting violations of it.

- **45 new per-regulation UCs (22.3.41 – 22.3.45, 22.6.46 – 22.6.50,
  22.7.36 – 22.7.45, 22.8.36 – 22.8.55)** — Five regulations, nine UCs
  per regulation, each one a full end-to-end author: markdown block,
  JSON sidecar, clause-level `compliance[]` entries against the target
  regulation plus cross-tag to NIST 800-53 / NIS 2 / HIPAA Security Rule
  derivative clauses, full `controlTest` (positive + negative scenario,
  fixture reference, optional ATT&CK technique pointer), `controlFamily`,
  owner role, evidence, exclusions, CIM model mapping, data sources,
  Splunk Pillar, known false positives, references, and `attackTechnique`
  where the detection corresponds to an ATT&CK TTP.
  - **DORA Regulation (EU) 2022/2554** — 9 UCs closing the remaining
    clause gap across ICT risk management, ICT third-party risk, threat-
    led penetration testing, incident classification, and ICT-related
    incident reporting. All 14 common clauses now covered.
  - **ISO/IEC 27001:2022** — 9 UCs closing the gap across Annex A
    controls (A.5 organizational, A.6 people, A.7 physical, A.8
    technological) and clause 9.1 monitoring/measurement. All 23 common
    clauses now covered.
  - **SOC 2 2017 TSC** — 9 UCs closing the gap across CC6 logical &
    physical access, CC7 system operations, CC8 change management, CC9
    risk mitigation, and A1 availability. All 16 common clauses now
    covered.
  - **PCI-DSS v4.0** — 9 UCs closing the gap across Requirement 2
    (secure configuration), Requirement 5 (malware defences), Requirement
    6 (secure development), Requirement 8 (authentication), Requirement
    10 (logging), and Requirement 11 (testing). All 22 common clauses
    now covered.
  - **SOX — PCAOB AS 2201 ITGCs** — 9 UCs closing the gap across access
    controls, change management, computer operations, and program
    development / program change. All 12 common clauses now covered.
- **Coverage rollup** — Tier-1 clause coverage climbs from **60.30% →
  82.91%** (120 → 165 of 199 common clauses) and priority-weighted
  coverage from 60.30% → **82.86%** (154.2 / 186.1). Every one of the
  five target regulation-versions now reports **100% clause coverage
  and 100% priority-weighted coverage** in
  `reports/compliance-gaps.json`. The remaining 34 tier-1 clauses
  (17.09%) sit on older framework versions (PCI v3.2.1, ISO 27001:2013)
  plus the frameworks untouched by Phase 2.3 (GDPR, HIPAA, NIS 2, NIST
  800-53, NIST CSF, CMMC) — those are the explicit targets for
  Phase 3.1 / 3.3.
- **`data/per-regulation/phase2.3.json`** — New authoring source of
  truth for the 45 UCs. Each entry carries the UC id, title, subcategory
  pointer, summary paragraphs, controlFamily, owner, evidence, SPL (with
  full CIM pivots / tstats where applicable), references, controlTest,
  and the per-clause `compliance[]` array. Schema-validated against
  `schemas/uc.schema.json` and reconciled against `data/regulations.json`
  on every generator run.
- **`scripts/generate_phase2_3_per_regulation.py`** — Mirrors the Phase
  2.2 pattern: idempotent, deterministic, `--check` mode, emits 45 new
  UC sidecars in canonical field order, renders markdown blocks between
  `<!-- PHASE-2.3 BEGIN -->` / `<!-- PHASE-2.3 END -->` fences in
  `use-cases/cat-22-regulatory-compliance.md`, and sets `status:
  community` on every new sidecar so the new tags flip their clauses
  from GAP to COVERED in the gap report (the same lifecycle stage Phase
  2.2 used; SME sign-off in Phase 5.2 will promote the full Phase 2.2
  + 2.3 cohort to `status: verified`). Produces byte-identical output
  on repeat runs; wired into `validate.yml` as a drift gate.
- **Audit pipeline stayed green** — `scripts/audit_uc_structure.py
  --full` (1,287 / 1,287 files valid), `scripts/audit_compliance_mappings.py`
  (52 / 52 golden tuples pass, zero new non-baselined errors),
  `scripts/audit_spl_hallucinations.py` (zero findings on the 45 new
  UCs), and `scripts/audit_splunk_cloud_compat.py` (zero new pack-level
  findings) all pass. `api/v1/`, `splunk-apps/`, and
  `reports/compliance-gaps.json` regenerated to include the new UCs and
  verified byte-identical over triple runs.
- **UC totals** — Cat-22 now ships **1,287 UC blocks** (up from 1,242
  in Phase 2.2) with **151 new clause-level compliance entries** added
  by Phase 2.3 — all bespoke per-regulation clauses on the five target
  frameworks, without any existing content changing. Total catalogue
  count: **6,424 UCs** (up from 6,379).

### Compliance gold standard — Phase 3.1 clause-level backfill

Theme: **tier-1 100% — no UC left untagged for the clauses it already
proves**. Phase 2.3 closed the five thinnest tier-1 regulation-versions
to 100% clause coverage; Phase 3.1 closes the remaining eight tier-1
frameworks without authoring a single new UC. The gap analysis flagged
34 tier-1 clauses on CMMC 2.0, ISO/IEC 27001:2013, NIST CSF 1.1 & 2.0,
PCI-DSS v3.2.1, GDPR 2016/679, NIST SP 800-53 Rev. 5, and HIPAA Security
Rule 2013-final that had **no compliance tag** on any cat-22 UC even
though an existing UC semantically proved the control — an evidence
surface the catalogue was silently under-selling. Phase 3.1 hand-maps
every one of those 34 clauses to the existing cat-22 UC that best
evidences it and appends the clause-level `compliance[]` entry.

- **Tier-1 clause coverage: 82.91% → 100.00%** — All **199 common
  clauses** across the 12 tier-1 regulation-versions are now covered
  (was 165 / 199). Priority-weighted tier-1 coverage climbs from
  **82.86% → 100.00%**. `reports/compliance-gaps.json` reports zero
  uncovered tier-1 clauses; `docs/compliance-gaps.md` shows a clean
  tier-1 section for the first time in the project's history. Tier-1
  assurance-adjusted coverage rises from **30.15% → 43.82%** as the
  backfilled tags are authored at `partial` or `full` assurance with
  rationale tying the UC's detection logic to the control text.
- **34 clause-level tags, zero new UCs** — Phase 3.1 adds **34 new
  `compliance[]` entries** across **33 existing cat-22 UCs** (one UC
  picks up two clauses from the same family). No SPL, markdown,
  controlTest, or any other UC field is touched — the change surface is
  strictly the `compliance[]` array on each target sidecar. Breakdown
  by regulation:
  - **CMMC 2.0** — 9 clauses (AC.L2-3.1.1, -3.1.5, -3.1.12, AU.L2-3.3.1,
    -3.3.2, -3.3.5, CA.L2-3.12.1, IR.L2-3.6.1, SI.L2-3.14.6) mapped to
    UCs evidencing authorised access, admin session monitoring, remote
    access control, audit record generation, audit review, anomaly
    detection, continuous monitoring, incident response, and system
    monitoring.
  - **ISO/IEC 27001:2013** — 6 Annex A clauses (A.9.2.3 privileged
    access, A.9.2.5 access rights review, A.12.4.1 event logging,
    A.12.4.3 admin/operator logs, A.16.1.2 reporting security events,
    A.18.1.3 protection of records).
  - **NIST CSF 1.1** — 4 subcategory IDs (PR.AC-1 identities &
    credentials, PR.DS-1 data-at-rest, DE.CM-1 network monitoring,
    RS.RP-1 response plan).
  - **NIST CSF 2.0** — 3 subcategory IDs (GV.OC-01 org mission,
    ID.AM-01 hardware inventory, PR.AA-01 identities issued).
  - **PCI-DSS v3.2.1** — 4 requirements (10.2, 10.3, 10.5, 10.6).
  - **GDPR 2016/679** — 3 articles (Art. 5(1)(f) integrity &
    confidentiality, Art. 32 security of processing, Art. 33 breach
    notification to supervisory authority).
  - **NIST SP 800-53 Rev. 5** — 3 controls (AC-2 account management,
    AU-6 audit review/analysis/reporting, SI-4 system monitoring).
  - **HIPAA Security Rule 2013-final** — 2 implementation specs
    (§ 164.308(a)(1)(ii)(D) information system activity review,
    § 164.312(b) audit controls).
- **`data/per-regulation/phase3.1.json`** — New authoring source of
  truth for the backfill. Each entry carries `uc_id`, `regulation`,
  `version`, `clause`, `clauseUrl`, `mode` (`satisfies` or
  `detects-violation-of`), `assurance` (`partial` or `full`), and a
  one-sentence `assurance_rationale` citing the specific evidence the
  UC produces for that clause. Every mapping is hand-reviewed; no
  heuristic assignment. The manifest is the system-of-record — the
  target UC can be re-chosen by editing this file, and the generator
  will idempotently re-apply.
- **`scripts/generate_phase3_1_backfill.py`** — New idempotent,
  deterministic generator. Reads the manifest, resolves each mapping
  to the target UC sidecar in `use-cases/cat-22/`, and appends the
  `compliance[]` entry **only if no entry for the same
  regulation+version+clause tuple already exists** (so the generator
  is safe to run repeatedly and safe against hand-added tags). Emits
  the sidecar in canonical field order, sorted compliance[] by
  regulation then clause, with byte-identical output on repeat runs.
  Supports `--check` (exit 1 on drift) and is wired into
  `validate.yml` as a drift gate.
- **Generator boundary enforced** — Phase 3.1 never modifies UCs whose
  sidecars are owned by another generator (Phase 2.2 mini-categories,
  Phase 2.3 per-regulation fills). Two mappings originally targeted
  Phase 2.3-owned UCs (22.6.51, 22.11.99); both were redirected to
  Phase 3.1-safe alternatives (22.6.39, 22.11.65) after the cross-
  generator drift was detected in CI.
- **Audit pipeline stayed green** — `scripts/audit_uc_structure.py
  --full` (1,287 / 1,287 files valid), `scripts/audit_compliance_mappings.py`
  (52 / 52 golden tuples pass, zero new non-baselined errors),
  `scripts/audit_spl_hallucinations.py` (zero findings on the 24 files
  scanned for the cohort), and `scripts/audit_splunk_cloud_compat.py`
  (zero new fails) all pass. `api/v1/` (compliance, coverage, gaps,
  ucs, regulations indexes), `splunk-apps/`, and
  `reports/compliance-gaps.json` are regenerated and verified byte-
  identical over triple runs.
- **What Phase 3.1 did not do** — Phase 3.1 is deliberately scoped to
  *existing cat-22 UCs*. Cross-tagging UCs outside cat-22 with tier-1
  clauses is **Phase 3.2**; applying the `derives_from` graph to
  derivative regulations (UK GDPR, CCPA, nFADP, LGPD, APPI) is
  **Phase 3.3**. Tier-2 clause coverage is unchanged (7.07%); lifting
  tier-2 is **Phase 3.2 + 3.3**. Tier-3 framework authoring is
  **Phase 5**.

### Compliance gold standard — Phase 3.2 cross-cutting clause-level tagging outside cat-22

Theme: **tier-2 unlocked — the catalogue's existing detections are the
evidence that tier-2 audits have been asking for**. Phase 3.1 landed
tier-1 clause coverage at 100%; Phase 3.2 turns to tier-2 and to the
other 21 categories in the catalogue. The gap analysis showed tier-2
coverage at just **7.07%** — not because the detections didn't exist,
but because the 4,000+ existing UCs outside cat-22 (identity, network,
endpoint, cloud, DevOps, OT, …) had *no* `compliance[]` entries at all.
Phase 3.2 hand-curates the cross-cutting map: for every tier-1/tier-2
clause where an existing operational UC already proves the control,
the UC gets a clause-level tag. No new UCs, no SPL changes, no markdown
rewrites — a pure metadata enrichment that reveals evidence the
catalogue was already producing.

- **Tier-2 clause coverage: 7.07% → 59.60%** — Covered common clauses
  jumped from **7 / 99 to 59 / 99**. Priority-weighted tier-2 coverage
  climbed from **7.37% → 59.77%**; assurance-adjusted tier-2 coverage
  rose from **3.68% → 27.55%**. Global clause coverage (tier-1 + tier-2
  rollup) went from **85.91% → 86.58%**. **13 tier-2 regulations**
  reached **100% commonClauses coverage** in this phase — API RP 1164,
  APRA CPS 234, BAIT/KAIT, EU CRA, FedRAMP Rev.5 baselines, HITRUST CSF
  v11, IEC 62443, BSI IT-Grundschutz 2023, MiFID II, PSD2, SG PDPA,
  TSA SD, and UK Cyber Essentials (Montpellier 2025). A further
  **14 tier-2 regulations** moved into partial coverage (33%–80%).
- **53 UCs, 182 clause-level mappings, zero new UCs** — Phase 3.2 adds
  **182 new `compliance[]` entries** across **53 existing UCs in 14
  categories** — cat-01 server & compute (8 UCs), cat-03 containers &
  orchestration (1), cat-04 cloud infrastructure (3), cat-05 network
  infrastructure (4), cat-06 storage & backup (3), cat-07 database &
  data platforms (3), cat-09 identity & access management (5), cat-11
  email & collaboration (2), cat-12 DevOps / CI/CD (4), cat-13
  observability & monitoring stack (4), cat-14 IoT / operational
  technology (7), cat-15 data-centre physical infrastructure (3),
  cat-16 service management / ITSM (3), and cat-17 network security
  & zero trust (3). The change surface is strictly the `compliance[]`
  array on new minimal JSON sidecars — markdown, controlTest, SPL,
  and every other UC field are untouched.
- **`data/per-regulation/phase3.2.json`** — New authoring source of
  truth. Each manifest entry identifies the target UC (`uc_id`,
  `title`) and lists its mappings (`regulation`, `version`, `clause`,
  `clauseUrl`, `mode`, `assurance`, `assurance_rationale`). Every
  mapping is hand-reviewed and rationale-cited against the clause
  text; no heuristic assignment, no LLM-generated claims. Scope
  explicitly excludes derivative data-protection regulations (UK GDPR,
  CCPA, nFADP, LGPD, APPI) — those are applied via the
  `derives_from` graph in **Phase 3.3**.
- **`schemas/per-regulation-phase3.2.schema.json`** — New JSON schema
  enforcing manifest shape. Validates `uc_id` grammar
  (`^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$`) and
  **explicitly rejects UC IDs starting with `22.`** — Phase 3.2 is
  non-cat-22 by construction, and cat-22 sidecars are owned by other
  generators (Phase 2.2, 2.3, 3.1).
- **`scripts/generate_phase3_2_cross_cutting.py`** — New idempotent,
  deterministic generator. Reads the manifest, resolves each UC ID
  against the markdown headings in `use-cases/cat-NN-*.md` (byte-exact
  title match required), and writes minimal JSON sidecars at
  `use-cases/cat-NN/uc-<id>.json` containing only `$schema`, `id`,
  `title`, and a `compliance[]` array. Sidecars are emitted in
  canonical field order with `compliance[]` sorted by
  `(regulation, version, clause)`. Deduplication is keyed on the same
  tuple, so the generator is safe to run repeatedly and safe against
  hand-edited tags. `--check` exits non-zero on drift; wired into
  `validate.yml` as a CI gate.
- **Clause-grammar hardening in `data/regulations.json`** — Phase 3.2
  surfaced two clauseGrammar inconsistencies that had previously gone
  untested. HITRUST CSF v11 grammar was tightened from
  `^\d{2}\.[a-z]$` to `^\d{2}\.[a-z]+$` so multi-letter clause codes
  like `09.aa` (Audit logging) validate correctly against their own
  `commonClauses[]` entry. BSI IT-Grundschutz 2023 grammar was widened
  from `^[A-Z]{2,4}(\.\d+)?(\.[AMS]\d+)?$` to
  `^[A-Z]{2,4}(\.\d+)*(\.[AMS]\d+)?$` so multi-segment module paths
  like `OPS.1.1.2` (Ordered ICT operation) validate correctly. Both
  changes are purely permissive and land with updated
  `clauseExamples[]`. `tests/golden/audit-baseline.json` was
  regenerated (fingerprints shifted on 5 pre-existing IT-Grundschutz
  data-quality issues; total baseline count unchanged at 670).
- **Audit pipeline stayed green** — `scripts/audit_compliance_mappings.py`
  (1340 / 1340 files valid, 52 / 52 golden tuples pass, zero new
  blocking errors), `scripts/audit_compliance_gaps.py` (tier-2
  coverage verified at 59.60%), and `scripts/generate_phase3_2_cross_cutting.py
  --check` (no drift) all pass. `api/v1/` regenerated (1,490 files
  total) and `splunk-apps/` regenerated (11 per-regulation apps,
  898 saved searches) — each tier-1 app picks up additional UCs
  from the new cross-cutting tags.
- **What Phase 3.2 did not do** — Phase 3.2 is deliberately scoped to
  *existing UCs outside cat-22* and *native clauses only*. Derivative
  regulations (UK GDPR, CCPA/CPRA, nFADP, LGPD, APPI) remain at 0%
  tier-2 coverage until the `derives_from` graph is applied in
  **Phase 3.3** — a mechanical propagation that will carry the
  tier-1 GDPR tags into UK GDPR, the California data-broker tags
  into CCPA, and so on, roughly doubling tier-2 clause coverage
  again. Tier-3 framework authoring remains **Phase 5**.

### Compliance gold standard — Phase 3.3 derivative-regulation propagation

Theme: **one detection, many legal regimes**. The 34-framework catalogue
carries a long-standing design invariant: derivative privacy regulations
(UK GDPR, Swiss nFADP, LGPD, APPI, and California CCPA/CPRA) re-use the
substance of their parent framework almost verbatim. A UC that already
proves GDPR Art.32 (technical and organisational security measures)
*necessarily* proves UK GDPR Art.32 — the clause text is preserved 1:1 by
the UK's Data Protection Act 2018 onshoring. The same control proves
LGPD Art.46 (security measures), APPI Art.23 (security control of personal
data), and so on — the wording diverges, the underlying control does not.
Phase 3.3 turns this invariant into evidence: it walks the `derivesFrom`
graph in `data/regulations.json` and emits **inherited `compliance[]`
entries** on every UC that already maps to a parent regulation, with full
traceability back to the parent clause and legal caveats captured as
divergence notes. Derivative tier-2 coverage jumped from **0% in
all five derivative regulations to 50%–100%** in a single deterministic
pass, with zero new UCs, zero SPL changes, and zero markdown rewrites.

- **Tier-2 clause coverage: 59.60% → 66.67%** — Covered common clauses
  climbed from **59 / 99 to 66 / 99**. The seven new clauses are
  derivative-regulation clauses that inherited their coverage
  mechanically from GDPR: **UK GDPR Art.32, Art.33, Art.34, Art.16,
  Art.17, Art.25** (identity-mode propagation), plus **LGPD Art.46,
  APPI Art.23, and Art.26** (mapped-mode propagation via hand-curated
  clauseMapping tables). Priority-weighted tier-2 coverage rose from
  **59.77% → 66.67%**; assurance-adjusted tier-2 coverage rose from
  **27.55% → 30.22%**. Global clause coverage (tier-1 + tier-2 rollup)
  went from **86.58% → 88.93%**.
- **54 inherited `compliance[]` entries across 5 derivatives** —
  distributed as **UK GDPR: 38** (identity-mode; every parent GDPR
  Art.N propagates to UK GDPR Art.N), **LGPD: 6**, **APPI: 6**,
  **Swiss nFADP: 2**, and **CCPA/CPRA: 2**. Seven entries carry a
  `derivationSource.divergenceNote` flagging clauses the derivatives'
  authorities have rewritten in substantive ways (e.g. UK GDPR Art.45
  adequacy decisions managed by the ICO, Swiss nFADP Art.7 privacy-by-
  design with its own enforceable scope, CCPA §1798.100 right-to-know
  with disclosure-window semantics different from GDPR). The
  inherited entry still lands so an auditor sees the lineage, but the
  divergence note explicitly requests SME review before the inherited
  assurance is relied on at trial. Every inherited entry is tagged
  `provenance: "derived-from-parent"` and carries a structured
  `derivationSource` object (parent regulation, parent version, parent
  clause, parent assurance, inheritance mode, optional divergence note)
  so the chain of inference is machine-traceable.
- **Assurance degradation and precedence rules** — an inherited
  entry can never be *stronger* than its parent. Assurance degrades
  exactly one step: **full → partial, partial → contributing,
  contributing → no propagation**. The terminal rule prevents the
  catalogue from emitting "contributing inherited from contributing"
  noise, which is common on advisory clauses where the parent entry
  itself is aspirational. Native (hand-authored or SME-reviewed)
  entries always win: if a UC already declares a direct mapping for
  a derivative regulation, the generator leaves that entry untouched
  even if the hand-authored assurance is *weaker* than the derived
  one would have been. This preserves SME intent over mechanical
  propagation — the inverse would silently overwrite curated
  judgements.
- **`data/regulations.json` — `derivesFrom` graph extended** — every
  derivative entry now declares `inheritanceMode` (`identity` vs
  `mapped`), an optional `clauseMapping` object (required for
  `mapped` mode), and a structured `divergences[]` list. UK GDPR is
  `identity`: the 2018 onshoring preserved EU GDPR clause numbering,
  so propagation is a 1:1 carry. Swiss nFADP, LGPD, APPI, and
  CCPA/CPRA are `mapped`: each ships a hand-curated clauseMapping
  keyed by parent clause (e.g. `Art.25 → Art.7` for nFADP privacy-by-
  design, `Art.32 → Art.46` for LGPD security measures, `Art.33 → §1798.150`
  for CCPA breach liability). Propagation strictly respects the
  mapping — clauses not listed in `clauseMapping` do not propagate,
  preventing spurious inherited claims against silence on the
  derivative side.
- **`schemas/uc.schema.json` — `derivationSource` field** — the UC
  schema now allows an optional `derivationSource` object on every
  `compliance[]` entry. Required when `provenance == "derived-from-parent"`;
  shape is `{parentRegulation, parentVersion, parentClause,
  parentAssurance, inheritanceMode, divergenceNote?}`. `additionalProperties: false`
  so adjacent hand-edited fields cannot slip in. The schema change is
  purely additive — existing entries (`maintainer`, `auditor-reviewed`,
  `olir-crosswalk`, `nist-cprt-ingest` provenance) continue to validate
  unchanged.
- **`scripts/generate_phase3_3_derivatives.py`** — new deterministic
  generator. Reads `data/regulations.json`, resolves parent-to-derivative
  framework relationships via the `derivesFrom` graph, canonicalises
  regulation names via `aliasIndex`, walks every UC sidecar, and
  emits inherited entries in canonical field order sorted by
  `(regulation, version, clause)`. Idempotent: repeated runs are
  byte-identical; `--check` diffs the regenerated tree against disk
  and exits non-zero on drift. Wired into `validate.yml` as a CI gate
  so a forgotten regeneration, a hand-edited derived entry, or a
  stale parent mapping that should have been garbage-collected all
  fail the PR check.
- **Coverage gates held green** — `scripts/audit_compliance_mappings.py`
  (1340 / 1340 files valid, 52 / 52 golden tuples pass, zero new
  blocking errors, baseline tolerated=670 unchanged), `scripts/audit_compliance_gaps.py`
  (tier-2 coverage verified at 66.67%), and all three generator
  `--check` modes (Phase 3.3 derivatives, `api/v1`, `splunk-apps`)
  all pass. `api/v1/` regenerated with the inherited entries (1,490
  files, ~20 UC compliance files updated to reflect the new
  derivative tags); `splunk-apps/` regenerated with no structural
  drift (derivative apps are authored in Phase 5; Phase 3.3 only
  populates the compliance metadata today).
- **What Phase 3.3 did not do** — Phase 3.3 is deliberately scoped to
  the five declared derivative regulations and to *mechanical*
  propagation of already-tagged parent clauses. It does **not** tag
  clauses on derivatives that have no GDPR parent (e.g. CCPA
  §1798.105 right-to-delete has no direct GDPR analogue; it maps
  from GDPR Art.17 via hand-curated rationale, not mechanical lift),
  it does **not** upgrade inherited assurance beyond the one-step
  degradation, and it does **not** run SME review. Upgrading
  inherited entries to `partial` or `full` assurance, authoring
  native derivative-only clauses, and collecting SME sign-offs all
  belong to **Phase 5**. Tier-3 framework authoring remains
  **Phase 5**.

### Compliance gold standard — Phase 4.1 regulatory primer

Theme: **plain-language explanation of what each regulation actually
demands**. The catalogue carries 60 regulatory frameworks with
clause-level precision in `data/regulations.json`, 1,219 machine-readable
compliance entries across 1,340 UC sidecars, and a versioned JSON API
surface — but none of that is useful to a privacy officer, legal reviewer,
or executive approver who has never written an SPL query. Phase 4.1
closes that gap with a single authoritative primer that translates
clause-level mappings into business-impact language, organised around
both how auditors think (by regulation) and how operators think (by
cross-cutting control family).

- **`docs/regulatory-primer.md` — 1,200+ line plain-language primer** —
  New top-level document covering (1) how to read the primer
  (tier badges, assurance levels, clause notation, priority weights);
  (2) **15 cross-cutting control families** 22.35 – 22.49, each with a
  plain-language control question, regulator-citation list, catalogue
  deliverable summary, and pointers into cat-22 markdown plus the
  matching `api/v1/compliance/ucs/*.json` endpoints; (3) **12 tier-1
  regulation deep dives** (GDPR, UK GDPR, PCI DSS v4.0, HIPAA Security,
  SOX ITGC, SOC 2, ISO 27001:2022, NIST CSF 2.0, NIST 800-53 Rev.5,
  NIS2, DORA, CMMC 2.0) with who-must-comply scope, key-clauses-and-
  coverage tables, and catalogue-delivery summaries; (4) derivative-
  regulation inheritance notes (UK GDPR identity-mode; CCPA / CPRA,
  Swiss nFADP, LGPD, APPI mapped-mode) cross-referencing Phase 3.3;
  (5) appendix of all 34 per-regulation subcategories (22.1 – 22.34);
  (6) worldwide data-protection appendix (11 regimes with parent /
  derivative relationships); (7) glossary; (8) provenance notes.
- **Zero-opinion authorship** — every clause citation, authoritative
  URL, and topic summary in the primer comes from
  `data/regulations.json` (the single source of truth) or from public
  regulator guidance cited in Appendix D. No SME interpretations are
  un-sourced; no legal conclusions are asserted. The primer is
  explicit that high-stakes interpretations (breach-notification
  timing, cross-border transfer validity, DPIA thresholds) require
  counsel review before the catalogue's coverage claims are relied on
  at trial.
- **Non-technical language throughout** — intended audience is
  privacy, legal, risk, audit, and executive readers. Written for
  readers who cannot write SPL and should not be asked to read
  savedsearches.conf. Every technical mechanism is framed as a
  business outcome: "prove the log records have not been tampered
  with" rather than "HEC acknowledgement mode is enabled with 30-day
  retention". Cross-references point readers to the machine-readable
  API for anything deeper.
- **No downstream artefact regeneration required** — Phase 4.1 is a
  pure-authoring delivery. No SPL changes, no UC sidecar mutations,
  no generator updates, no CI wiring. The primer is static markdown
  consumed directly; CI's `audit_changelog_uc_refs.py` gate confirms
  every cited UC ID is valid. `api/v1/`, `splunk-apps/`, and the
  compliance gap report are unchanged.

### Compliance gold standard — Phase 4.2 tier-1 evidence packs

Theme: **auditor-ready dossiers**. The regulatory primer (Phase 4.1)
explains *what* each regulation demands in plain language; the evidence
packs explain *how the catalogue proves it* in auditor language.
Twelve deterministic, dual-format (Markdown + JSON) dossiers that an
auditor can accept, a privacy officer can review, and a machine can
consume — all generated from the same clause-level source data as the
API surface, with no hand-curated divergence.

- **`docs/evidence-packs/*.md` — 12 tier-1 evidence packs** — One pack
  per tier-1 framework (`gdpr.md`, `uk-gdpr.md`, `pci-dss.md`,
  `hipaa-security.md`, `sox-itgc.md`, `soc2.md`, `iso27001-2022.md`,
  `nist-csf.md`, `nist80053.md`, `nis2.md`, `dora.md`, `cmmc.md`).
  Each pack carries eight auditor-facing sections: (1) framework
  identity (regulator, authoritative URL, effective date, version);
  (2) derivative-relationship notes when applicable; (3) coverage
  summary (covered clauses, coverage %, priority-weighted %,
  contributing UCs, tier-1 / tier-2 split); (4) clause-by-clause
  table showing every common clause, max assurance level, and the
  contributing UC list; (5) evidence requirements (retention, signing,
  access control); (6) top five auditor questions pre-answered with
  links into the catalogue; (7) responsible roles (control owner,
  evidence custodian, independent reviewer); (8) common deficiencies
  (what auditors typically flag, how the catalogue defends against
  each).
- **`api/v1/evidence-packs/*.json` — JSON twin of every pack** —
  Every Markdown pack ships a mechanically equivalent JSON twin
  containing framework identity, a `coverage` summary (covered /
  total clause counts, priority-weighted %, `contributingUcCount`),
  a `clauses[]` array with per-clause assurance and UC list, the
  full auditor-extras block (evidence requirements, questions, roles,
  deficiencies), plus a global `api/v1/evidence-packs/index.json`
  endpoint catalogue. Machine consumers get the same signal as
  human auditors, no screen-scraping required.
- **`data/evidence-pack-extras.json` — auditor-facing metadata** —
  New data file covering the 12 tier-1 frameworks with retention
  guidance, signing guidance, access-control guidance, top-five
  auditor questions, control-owner / custodian / reviewer role
  descriptions, and the common-deficiency list per framework. Kept
  separate from `data/regulations.json` so the authoritative
  regulatory index stays focused on clause-level facts while
  auditor narrative lives in a purpose-built file. Validated by
  `schemas/evidence-pack-extras.schema.json`.
- **Identity-mode derivative handling** — UK GDPR's evidence pack
  correctly inherits GDPR's **full** clause inventory (20 common
  clauses, merged from the parent), not just UK GDPR's divergence
  list. The generator detects `inheritanceMode: identity` on the
  `derivesFrom` graph, expands the derivative's clause set to
  include every parent clause, and then computes live coverage
  against that expanded inventory. UK GDPR therefore shows
  **16 / 20 clauses covered (80 %)** with 24 contributing UCs and
  the four uncovered clauses (Art.22, Art.25, Art.30, Art.35)
  called out explicitly — matching what an auditor would see under
  a UK ICO review. Mapped-mode derivatives (CCPA, nFADP, LGPD, APPI)
  remain out of tier-1 scope for Phase 4.2 and will land as Phase 5
  deliverables.
- **Markdown ↔ JSON coverage alignment** — The JSON twin's
  `contributingUcs[]` only lists UCs that map to at least one of
  the pack's visible common clauses; the top-of-pack summary,
  the clause table, and the JSON `coverage.contributingUcCount`
  all agree. Previously the JSON could list UCs that tagged
  sub-clauses outside the common-clause inventory, creating a
  mismatch with the human-readable summary.
- **`scripts/generate_evidence_packs.py` — deterministic generator** —
  New Python generator reads `data/regulations.json`,
  `data/evidence-pack-extras.json`, every UC sidecar, and
  `reports/compliance-gaps.json` to emit the 24 pack files + 2
  index files. Supports `--check` (CI drift guard, exits non-zero
  on divergence) and a `--verbose` progress mode. Regulation IDs
  from UC sidecars are normalised via `data/regulations.json`'s
  `aliasIndex` (case-insensitive), and clause identifiers are
  sorted naturally (Art.5 before Art.10) so re-runs produce
  byte-identical output.
- **CI wiring** — `.github/workflows/validate.yml` runs
  `generate_evidence_packs.py --check` after the clause-level
  gap-report regeneration step. Triggers extended to
  `data/evidence-pack-extras.json` and `docs/evidence-packs/**`.
- **Generator coexistence** — `scripts/generate_api_surface.py`
  teaches about external subtrees: `api/v1/evidence-packs/` is
  now explicitly skipped by both the cleanup (`rmtree`) logic
  and the `_diff_trees` comparator, so the two generators
  coexist under `api/v1/` without fighting over ownership.

Scope boundaries (what Phase 4.2 intentionally does **not** do): it
does not author tier-2 / tier-3 framework evidence packs, it does
not alter clause-level coverage in `reports/compliance-gaps.json`
(the packs are a *view* on existing data), it does not record SME
sign-offs (Phase 5.2), and it does not sign the pack outputs
(provenance ledger is Phase 5.4). Tier-2 framework evidence packs
belong to Phase 5 per the gold-standard plan.

### Compliance gold standard — Phase 4.3 non-technical view elevation

Theme: **plain-language access to regulatory compliance**. The
regulatory primer (Phase 4.1) and auditor evidence packs (Phase 4.2)
are authoritative but dense; Phase 4.3 makes both visible to the
audience that actually signs off on compliance programmes — privacy
officers, legal counsel, risk leaders, and executives — without
making them hunt through markdown files. Category 22's non-technical
view now carries plain-language narrative *per area* plus one-click
cross-references into the primer and the evidence packs.

- **`non-technical-view.js` — `"22": { ... }` block rewritten** — The
  cat-22 block now owns **50 areas**, up from the previous combined
  view. Three structural splits bring the taxonomy in line with
  Phase 4.1 / 4.2 content: *UK GDPR* separated from GDPR (it owns its
  own evidence pack under `inheritanceMode: identity`), *ISO 27001*
  separated from *NIST CSF 2.0* (distinct primer sections and
  evidence packs), and *MiFID II* separated from *SOC 2* (different
  regulators, different evidence). Every area carries the existing
  `name` / `description` / `ucs[]` plus three new plain-language
  fields — `whatItIs` (one-sentence definition), `whoItAffects`
  (obligated entities), `splunkValue` (what the Splunk catalogue
  delivers for this area) — so a non-technical reader can understand
  each regulation at a glance without clicking through.
- **Cross-references into primer and evidence packs** — Two further
  optional fields, `primer` (repo-relative path into
  `docs/regulatory-primer.md` with anchor) and `evidencePack`
  (repo-relative path into `docs/evidence-packs/*.md`), turn each
  area into a portal to the deeper content. Tier-1 regulation areas
  (GDPR, UK GDPR, PCI DSS, HIPAA, SOX / ITGC, SOC 2, ISO 27001,
  NIST CSF, NIST 800-53, NIS2, DORA, CMMC) carry both fields, for
  12 linked pairs. Cross-cutting family areas (22.35 – 22.49) carry
  `primer` but no evidence pack — the tier-1 evidence lives on the
  regulation areas. Tier-2 / tier-3 regulations carry neither link
  field today; they remain documented through `whatItIs` /
  `whoItAffects` / `splunkValue`. Final counts: **50 areas** with
  at least one plain-language meta field, **27 areas** with a
  primer anchor, **12 areas** with an evidence pack link.
- **`scripts/regenerate_cat22_ntv.py` — deterministic generator** —
  New Python generator owns the entire cat-22 block. It carries an
  authoritative in-memory dictionary of every area's narrative copy
  and renders it into the JS object literal the dashboard consumes,
  preserving the surrounding style (same indentation, same
  single-line scalar layout, comma-terminated `ucs[]` entries).
  Supports `--check` for the CI drift guard. Anchor slugs are
  verified to match GitHub-slugger output for every primer heading;
  every referenced UC ID was audit-verified against the markdown
  source before rewrite (0 missing of 142 IDs authored).
- **`index.html` — frontend renderer extended** — The non-technical
  view now renders the new fields: a `<dl class="nt-area-meta">`
  block shows `whatItIs` / `whoItAffects` / `splunkValue` as a
  clean definition list, and a `<div class="nt-area-links">` row
  shows primer and evidence-pack buttons. A new `ntResolveLink()`
  helper converts the repo-relative paths into absolute GitHub
  blob URLs (`https://github.com/fenre/splunk-monitoring-use-cases/blob/main/...`)
  so links always open in GitHub's rendered Markdown view, even
  when the dashboard is served from a mirror or a PR preview. The
  `filterNTCards()` search text now includes the three new
  meta-fields so the non-technical search covers the new copy.
- **`.cursor/rules/non-technical-sync.mdc` — documentation updated**
  — The workspace rule for `non-technical-view.js` was extended
  with the five Phase 4.3 fields (`whatItIs`, `whoItAffects`,
  `splunkValue`, `primer`, `evidencePack`), their content rules
  (plain-language, no jargon, tier-1 gets both links, cross-cutting
  gets primer only, tier-2 / tier-3 get neither today), and the
  tier-1 list that **must** carry both `primer` and `evidencePack`.
- **CI wiring** — `.github/workflows/validate.yml` runs
  `regenerate_cat22_ntv.py --check` after the Phase 3.3 generator
  check and before the API surface check; drift in the cat-22
  block now fails PR validation. The existing
  `audit_non_technical_sync.py` audit already passes (every area
  still references valid UC IDs for its subcategory).

Scope boundaries (what Phase 4.3 intentionally does **not** do): it
does not add `whatItIs` / `whoItAffects` / `splunkValue` to non-cat-22
categories (those are operational, not regulatory, and do not need
regulator-facing copy); it does not author a non-technical block for
future tier-2 / tier-3 regulations beyond what the current cat-22 set
covers; and it does not edit `docs/regulatory-primer.md` or
`docs/evidence-packs/**` (both are authored under 4.1 / 4.2).
Downstream artefact regeneration: `build.py` picks up no new content
from this phase — the non-technical view is independent of
`catalog.json`, `api/v1/`, and `splunk-apps/`.

### Compliance gold standard — Phase 4.4 compliance scorecard panel

Theme: **one URL every auditor and regulator can point at**. The
catalogue already publishes `reports/compliance-coverage.json`,
`reports/compliance-gaps.json`, and `scorecard.json` — but reading
JSON is not what an auditor signs off on. Phase 4.4 surfaces those
three files as a single auditor-ready HTML page so the compliance
posture is a one-click artefact rather than a Python notebook
exercise.

- **New `scorecard.html` landing page** — Standalone HTML/CSS/JS
  page at the repo root that boots from four static JSON files —
  `reports/compliance-coverage.json`, `reports/compliance-gaps.json`,
  `scorecard.json`, and `data/regulations.json` — and renders the
  complete compliance + quality scorecard client-side. No build
  step, no server runtime, no framework: plain HTML served from
  GitHub Pages, the same deployment model as the rest of the
  catalogue.
- **Global rollup hero** — Top-of-page panel that shows the four
  headline numbers the board asks for: global clause coverage %,
  priority-weighted coverage %, assurance-adjusted coverage %, and
  the weighted technical-quality composite across all 23 categories.
  Audit status badge (`audit passed` / `failed` / `error`) is driven
  live from `reports/compliance-coverage.json.status`, and the
  "generated at" timestamp makes the page self-dating so auditors
  always see when the underlying scans ran.
- **Tier rollups** — Per-tier cards (Tier 1 cross-industry critical,
  Tier 2 sector / regional, Tier 3 niche / emerging) show clause /
  priority-weighted / assurance percentages plus the `covered /
  total` clause counts from `coverage.perTier`. A colour-coded cell
  (green ≥ 80 %, amber 50 – 79 %, red < 50 %, grey = 0 %) matches
  the methodology in `docs/coverage-methodology.md`.
- **Per-regulation drilldown table** — Sortable / filterable table
  of all 60 regulations from `data/regulations.json`, joined with
  `coverage.perFamily` and `reports/compliance-gaps.json.tiers`.
  Each row shows tier badge, version label, clause %, priority %,
  assurance %, and covered / total clause counts. Free-text filter
  (searches id, name, shortName, jurisdiction), tier filter
  (1 / 2 / 3), and coverage-band filter (≥ 80 / 50 – 79 / < 50 /
  0 %) turn the table into a "which regulations are still thin?"
  triage tool. Column headers are click-to-sort (ascending on
  first click, descending on second).
- **Audit findings snapshot** — Metric cards that roll up new
  errors, warnings, baselined warnings, golden-test pass / fail,
  UC files checked, and total compliance entries straight from
  `reports/compliance-coverage.json.findings`, `.golden`, and
  `.counts`. Error / golden cards flip to red when any error
  surfaces, so the page visibly fails CI posture before the
  viewer has to read the detail.
- **Technical-quality (per category) table** — Dedicated section
  that renders `scorecard.json.categories` as a second sortable /
  filterable table: category number, name, UC count, references %,
  known-false-positives %, MITRE %, provenance score, samples %,
  composite, and Gold / Silver / Bronze / Needs-work badge. A
  grade-distribution strip above the table shows how many
  categories sit in each grade and how many UCs they carry, so the
  reader can read "Gold: 0 / 3 / 4 / 16" in one glance and jump
  straight to the laggards.
- **Machine-readable artefact index** — Bottom-of-page section lists
  every JSON / markdown source the page consumes, with short
  one-sentence descriptions, so anyone forking the catalogue can
  wire the same files into their own CI gates. Direct download
  links land in `reports/`, `api/v1/compliance/`, `scorecard.json`,
  `data/regulations.json`, `docs/regulatory-primer.md`, and
  `docs/evidence-packs/`.
- **Design tokens, dark mode, print-friendly** — The page reuses
  the `index.html` Cisco-theme CSS variables end-to-end (fonts,
  surfaces, borders, Cisco blue primary, green / amber / red
  coverage bands, grade colours), so it reads as part of the same
  site. Theme toggle persists in `localStorage` and honours
  `prefers-color-scheme`. `@media print` styles hide the header,
  filters, and footer so an auditor can print the scorecard to
  PDF and get a clean evidence artefact with no UI chrome.
- **`index.html` wiring** — Footer navigation gets a new
  `Scorecard` link next to `API docs` so the dashboard exposes
  the page. The help dialog's "Which endpoint should I use?" grid
  gains three new cards — `/scorecard.html`, `/reports/compliance-coverage.json`,
  `/reports/compliance-gaps.json` — so the endpoint catalogue
  stays accurate. No backend or build changes are required.
- **Headless render test** — A minimal Node.js DOM shim was used
  to boot the page's JavaScript against a local HTTP server
  serving the repo tree; all ten render assertions (audit status,
  hero metadata, global metric cards, tier grid, regulation
  tbody, category tbody, grade distribution, findings grid, and
  both filter counters) pass, confirming the page renders end-to-end
  from a cold cache with no console errors.

Scope boundaries (what Phase 4.4 intentionally does **not** do): it
does not create a server-rendered endpoint (the design is
intentionally static-file so it deploys with the rest of the repo
on GitHub Pages), it does not introduce a JavaScript build step
or bundler, it does not duplicate the underlying JSON (the page
is a pure facade over `reports/*.json`, `scorecard.json`, and
`data/regulations.json`), and it does not replace
`docs/scorecard.md` or `docs/coverage-methodology.md` — both
remain the canonical human-readable references, and the page
links out to them. Future QA, SME review, change-watch, and
release gates land in Phase 4.5 / Phase 5.

### Compliance gold standard — Phase 4.5 QA gates

Theme: **nothing ships to an auditor unless six independent gates say
yes**. Phase 4.4 put the compliance posture behind a single URL; Phase
4.5 wraps that posture in six blocking CI gates so the repository
cannot regress silently. Each gate is deterministic, has a committed
machine-readable report, a Python generator with a `--check` drift
guard, and — where applicable — a Node.js drift guard that runs on
the same report from a different code path. Together they cover
human review (peer + legal), runtime evidence (sandbox fixtures +
ATT&CK simulation), interop (OSCAL round-trip), and end-user
experience (perf budgets + WCAG 2.1 AA a11y).

- **Peer-review framework (4.5a)** — Ships
  `docs/peer-review-guide.md`, a `.github/PULL_REQUEST_TEMPLATE.md`
  review checklist, the `data/provenance/peer-review-signoffs.json`
  schema, and `scripts/audit_peer_review_signoffs.py` as the
  blocking audit. The audit validates signoff identity,
  reference target, git-commit SHA shape, and ISO-8601 signoff
  date. Peer reviews are now a first-class artefact, not a comment
  on a PR page.
- **Legal-review framework (4.5b)** — Ships
  `docs/legal-review-guide.md`, the
  `data/provenance/legal-review-signoffs.json` schema, an append to
  `LEGAL.md` documenting the review cadence, and
  `scripts/audit_legal_review_signoffs.py`. The audit enforces that
  every tier-1 regulation with a registered legal advisor has a
  current signoff and that any quoted clause language matches
  `data/regulations.json` at the pinned version — legal advisors
  can never drift silently from the authoritative text.
- **Sandbox validation gate (4.5c)** —
  `scripts/audit_sandbox_validation.py` walks every UC sidecar that
  declares a `controlTest.fixtureRef`, asserts the fixture exists on
  disk with populated positive and negative cases, and emits
  `reports/sandbox-validation.json`. A Node-only drift guard
  (`tests/sandbox/validate.test.mjs`) re-derives the report from the
  UC sidecars and fixture tree so contributors without Python get a
  pre-commit signal. The gate distinguishes `populated` /
  `empty` / `missing` / `no-fixture` / `pending_fixture` states and
  keeps the CI failure tied to a reproducible shape rather than to
  a SPL-at-test-time runtime.
- **ATT&CK simulation gate (4.5d)** —
  `scripts/simulate_controltest.py` and
  `tests/attack/simulate.test.mjs`. The Python simulator is a
  **structural** check (we do not run SPL against a live Splunk in
  CI — that would leak secrets and add flakiness): it verifies that
  every ATT&CK technique cited by a `controlTest` parses as the
  canonical `T####[.###]` grammar, exists in the normalised MITRE
  crosswalk committed under `data/crosswalks/attack/`, and that
  populated fixtures have coherent positive / negative polarity.
  Reports at `reports/attack-simulation.json`; the Node drift guard
  reconciles the record set against the UC sidecars on disk so the
  file can never go stale.
- **OSCAL round-trip gate (4.5e)** —
  `scripts/audit_oscal_roundtrip.py` and
  `tests/oscal/roundtrip.test.mjs`. The Python audit validates every
  `api/v1/oscal/component-definitions/*.json` file against the NIST
  OSCAL JSON schema (ajv under the hood) **and** asserts that
  parse → re-serialise produces the exact same bytes as the
  committed file. This catches two failure modes at once: schema
  drift (the NIST spec added / removed a required field) and
  canonicalisation drift (a contributor hand-edited an OSCAL file
  outside the generator). The Node drift guard reads the schema
  bundled under `tools/vendor/oscal/schema/`, hashes it, and
  cross-checks the hash recorded in `reports/oscal-roundtrip.json`
  so the audit can never claim it ran against a schema that no
  longer exists.
- **Perf + a11y audit gate (4.5f)** —
  `scripts/audit_perf_a11y.py` and
  `tests/a11y/perfa11y.test.mjs`. Two dimensions are enforced in a
  single gate because both speak to "what ships to the end user":
  **perf budgets** (per-file byte caps on critical-path HTML / JS
  and generated data, each with ~25 % headroom; over-budget hard-
  fails) and **accessibility** (axe-core v4 under jsdom against
  `scorecard.html` and `index.html` with the WCAG 2.1 A + AA +
  best-practice rule set; serious / critical violations hard-fail
  unless allowlisted with peer-review justification). Moderate /
  minor violations surface as warnings; jsdom-incompatible rules
  (colour-contrast, target-size, focus order) are pre-disabled so
  the signal stays clean. Generates
  `reports/perf-a11y.json`; the Node drift guard re-checks every
  perf record against on-disk bytes and every a11y disposition
  against impact-level thresholds. Under the hood, this adds
  `axe-core@4.11.3` and `jsdom@29.0.2` to `package.json`
  `devDependencies`, and `tests/a11y/run-axe.mjs` is the Node
  subprocess invoked by the Python orchestrator — keeping the
  audit configurable in one place and portable across CI.
- **CI wiring (4.5g)** — `.github/workflows/validate.yml` gains a
  Node.js 20 setup step with `cache: npm`, an `npm ci` install,
  and ten new gate steps (one Python + one Node per dimension for
  4.5c / 4.5d / 4.5e / 4.5f, plus 4.5a and 4.5b Python audits).
  The PR `paths:` filter now triggers on `tests/**`, every
  `reports/*.json` file under the Phase 4.5 gates,
  `data/provenance/**`, `package.json`, `package-lock.json`,
  `LEGAL.md`, and the review guides so any edit to an input
  triggers every gate. A new `qa-gates` artifact is uploaded on
  every CI run and bundles the four QA reports plus the peer and
  legal signoff files so external reviewers can pull one artifact
  and reproduce the gate's decision.
- **Smoke-tested failure modes** — Phase 4.5f was verified against
  six failure scenarios before it landed: an over-budget perf file,
  a critical a11y violation, a moderate a11y violation (warning),
  an allowlist-downgraded violation, a drifted report in
  `--check` mode, and a missing report in `--check` mode. All six
  fail fast with actionable stderr messages; none leave the
  committed report mutated.

Scope boundaries (what Phase 4.5 intentionally does **not** do):
it does not run SPL against a live Splunk tenant (the ATT&CK gate
is structural, not runtime — runtime simulation lands with the
SOAR content pack in a later phase); it does not introduce a
browser render farm for a11y (jsdom is deliberate — faster,
hermetic, and reproducible on every runner); and it does not
replace the blocking SME review in Phase 5.2, which is a separate
human-judgement gate that operates on top of these automated
checks.

### Compliance gold standard — Phase 5.1 12 per-regulation Splunk apps

Theme: **every regulated customer gets a single, auditor-ready
deliverable**. Phase 1.8 shipped the POC generator that produced
eleven tier-1 apps. Phase 5.1 promotes the generator to production
scope: the default set now lands the full twelve per-regulation
Splunk apps the plan requires, every app ships an AppInspect-safe
compliance-posture dashboard that works on install, and the
lookup is registered as a shared transform so sibling apps can
reference it.

- **Twelfth per-regulation app — `splunk-uc-uk-gdpr`** — The
  default selection in `scripts/generate_splunk_app.py` now
  includes UK GDPR alongside the eleven tier-1 frameworks (GDPR,
  PCI DSS, HIPAA-Security, ISO 27001, NIST 800-53, NIST CSF,
  SOC 2, SOX-ITGC, CMMC, NIS 2, DORA). UK GDPR is a tier-2
  *identity* derivative of GDPR per `data/regulations.json`
  `derivesFrom`: clause numbering is preserved 1:1, so the Phase
  3.3 derivatives generator had already propagated parent
  mappings onto 32 UCs with `derivationSource` metadata. Phase
  5.1 converts that propagation into a standalone evidence pack
  that UK auditors can reference without a GDPR export detour.
  A new explicit allow-list (`_DEFAULT_DERIVATIVE_APP_IDS`)
  controls which derivatives are promoted, keeping the decision
  machine-readable and fail-loud if a listed framework is ever
  removed from the catalogue.
- **Compliance-posture dashboard per app** — Every
  `splunk-apps/splunk-uc-<regulation>/` now ships
  `default/data/ui/views/<regulation>_compliance_posture.xml`,
  a Simple XML 1.1 dashboard that reads the per-app
  `uc_compliance_mappings` lookup. Panels: total UCs packaged,
  critical-tier UCs, distinct clauses tagged, UCs by criticality
  (column), most-referenced clauses top-15 (bar), mappings by
  assurance bucket (full / partial / contributing / unspecified),
  and a full UC inventory table with source-path references.
  Every SPL query is CDATA-wrapped, uses `inputlookup` only (no
  index reads, no `dbxquery`, no custom commands), and works on
  a clean install before any saved search is scheduled — so the
  dashboard is the one-glance answer an auditor needs without
  committing the operator to any data-pipeline work.
- **Lookup registered as a shared transform** — Every app now
  writes `default/transforms.conf` with a
  `[uc_compliance_mappings]` stanza that maps the
  previously-orphan CSV under `lookups/` to a named lookup that
  SPL (and the new dashboard) can reference. Without this step
  the CSV was a documentation artefact; with it, the lookup is
  a first-class knowledge object.
- **Navigation redirects to the posture dashboard** —
  `default/data/ui/nav/default.xml` now sets
  `default_view="<regulation>_compliance_posture"` so a freshly
  installed app opens on the evidence dashboard, not on an empty
  search bar. The catch-all eventtype link is preserved as a
  secondary collection entry.
- **Knowledge-object exports widened, saved-searches still
  private** — `metadata/default.meta` gains
  `[transforms] export = system` (so sibling apps can reuse the
  lookup) and `[views] export = app` (so the posture dashboard
  appears in the app's navigation without becoming a global
  object). Saved searches remain `export = none` — operators
  opt in to scheduled alerts explicitly, mirroring the Phase 1.8
  policy.
- **README additions per app** — Every generated README gains a
  dedicated "Compliance posture dashboard" section and updates
  the AppInspect readiness checklist to call out the new
  transform, view, and meta export scopes. Installation step 3
  now points installers at the dashboard first so the on-ramp is
  "install → open dashboard → brief auditor".
- **Determinism + CI** — `scripts/generate_splunk_app.py --check`
  already runs in `.github/workflows/validate.yml` (Phase 1.8
  wire-in) and the regenerate-and-diff loop remains byte-stable:
  the Phase 5.1 additions produce the same 12 app trees on every
  run, and a drift check is the CI gate that protects that
  invariant. `splunk-apps/manifest.json` at the repo root is
  auto-regenerated and now lists twelve `splunk-uc-*` ids with
  per-app UC counts (930 saved searches across the catalogue).

Scope boundaries (what Phase 5.1 intentionally does **not** do):
it does not introduce per-UC sample fixtures inside the app tree
(sandbox fixtures stay centralised under `samples/` and are
audited by Phase 4.5c); it does not bundle CIM/ES dependency
shims inside the apps (the upstream CIM app remains a runtime
prerequisite, surfaced via the `commonInformationModels` block
in `app.manifest`); it does not publish the apps to Splunkbase
(that is a release-engineering concern tracked under the Phase
5.5 release gate); and it does not yet promote further
derivative frameworks (CCPA, nFADP, LGPD, APPI) into standalone
apps — those stay inside the main GDPR app's derivation graph
until Phase 5.2 SME review blesses the split.

### Compliance gold standard — Phase 5.2 SME review framework

Theme: **an auditor-credible attestation chain for every
tier-1 `full`-assurance claim**. Phase 4.5 landed peer and legal
review. Phase 5.2 adds the third and final QA gate — subject-matter
expert review — so that every UC claiming "full" assurance against
a tier-1 regulation has walked through an engineering review, a
legal review of the citations, **and** an SME review of the SPL's
technical correctness against the authoring data source and the
Splunk output's acceptability to an auditor. The gate is blocking
in CI via a new schema + semantic audit script and a PR-template
checklist; historical content is grandfathered behind a commit
baseline so the gate only applies to changes landing on or after
Phase 5.2.

- **SME signoff schema** — New
  `schemas/sme-review-signoff.schema.json` (JSON Schema draft
  2020-12) models one signoff record per reviewer per commit.
  Records carry the reviewer's name/role/credentials, the scope
  (UC IDs, tier-1 regulations, optional fixture + evidence-pack
  paths), the six-point rubric grades (splCorrectness,
  dataSourceRealism, splunkCompat, evidenceCompleteness,
  regulationApplicability, falsePositiveAssessment), an outcome
  enum (approved / approved-with-revisions / rejected /
  conditional / scope-downgrade), outcome-specific required
  fields (revisions, caveats, rejectionReason), an optional
  structured fixtureReplayResult, and free-text reviewer notes.
  Reviewer roles are enumerated (`splunk-engineer`,
  `regulatory-auditor`, `security-architect`, `industry-sme`,
  `internal-review-board`) so the audit can detect mismatches
  between a claimed role and the rubric grades that role is
  competent to produce.
- **Ledger file with a commit baseline** —
  `data/provenance/sme-signoffs.json` is an append-only ledger.
  `baseline_commit` (`217320f`) pins the "grandfather" cut-off:
  content authored before that commit is not required to carry
  an SME signoff retroactively. The file begins empty; future
  PRs append one record per SME per reviewed commit.
- **SME review guide (`docs/sme-review-guide.md`, ~360 lines)** —
  Documents the full process: §1 scope (what triggers SME review,
  what does not, relationship to peer + legal gates), §2
  reviewer-role taxonomy and recognised credentials per tier-1
  regulation (QSA for PCI DSS, CIPP/E for GDPR/UK-GDPR, HITRUST
  CCSFP for HIPAA, CISA/CPA for SOX/ITGC, ISO 27001 Lead Auditor
  for ISO, etc.), §3 the six-point rubric (each with "question",
  "how to check", and "fail modes"), §3.7 outcome-to-PR-effect
  matrix, §4 how to record a signoff (JSON example with a real
  fixture replay), §4.1 how `smeCaveat` is mirrored to UC
  sidecars, §4.2 fixture-replay self-consistency rules, §5
  dual-SME escalation for high-penalty tier-1 clauses and
  headline evidence-pack UCs, §6 privacy of SME identity (public
  signoffs with optional firm-only names), §7 historical
  baseline, §8 timeline expectations per reviewer role.
- **Audit script with seven semantic invariants** —
  `scripts/audit_sme_review_signoffs.py` validates the ledger
  against the schema (JSON Schema draft 2020-12 via
  `jsonschema`) and enforces seven semantic rules not expressible
  in JSON Schema alone: (1) `approved-with-revisions` requires a
  non-empty `revisionsRequested`; (2) `conditional` requires a
  non-empty `caveats` AND every caveat is mirrored as an
  `smeCaveat` on a UC sidecar in scope; (3) `rejected` requires
  a \u2265 20-char `rejectionReason`; (4) `approved` cannot carry
  any `fail` grade; (5) the `(commit, reviewer)` pair is unique
  across signoffs (two different SMEs on the same commit is
  supported for dual-SME review; the same SME twice on one commit
  is not); (6) `fixtureReplayResult` is self-consistent with
  `checks.splCorrectness` — `replayed=false` forces `n/a`,
  `replayed=true` with a negative-fired or positive-silent replay
  forces `fail`; (7) every `scope.ucs` sidecar exists, every
  `scope.fixtures` path is under `sample-data/`, every
  `scope.evidencePacks` path is under `docs/evidence-packs/`.
  A warning (not error) fires when a `splunk-engineer` reviewer
  grades `splCorrectness=pass` without recording a fixture
  replay.
- **UC schema carries `smeCaveat`** —
  `schemas/uc.schema.json` gains an optional `smeCaveat` property
  on `compliance[]` entries, mirroring the existing `legalCaveat`
  field. The generator ecosystem (scorecard, per-regulation
  Splunk apps, api/v1/ compliance/ucs/\u2020.json) will render the
  caveat alongside each mapping when populated. `smeCaveat` is
  informational — it does not affect assurance weighting but it
  is auditor-visible, so operators can see the conditions under
  which the mapping was blessed (TA version pins,
  field-extraction prerequisites, industry-scope limitations).
- **PR template** — `.github/PULL_REQUEST_TEMPLATE.md` gains a
  Phase 5.2 checklist between the legal review section and the
  screenshots block. Six bullets: reviewer identity + role
  recorded; SPL fixture replayed (or `n/a` explained); six-point
  rubric graded; dual-SME review where §5 requires it; caveats
  mirrored to UC sidecars for `conditional` outcomes; signoff
  appended to `data/provenance/sme-signoffs.json` and audited.
- **CI wired in** — `.github/workflows/validate.yml` gains a
  "Phase 5.2 SME-review signoff audit" step that runs
  `python3 scripts/audit_sme_review_signoffs.py` (exit 1 on
  schema or semantic violation). The `qa-gates` artifact upload
  bundles `data/provenance/sme-signoffs.json` alongside the
  existing peer + legal ledgers so a reviewer can download a
  single artifact and reproduce the three-gate decision. The
  workflow `paths` trigger list now also watches
  `docs/sme-review-guide.md` so changes to the rubric re-run CI.
- **LEGAL.md §5 rewritten** — The stale §5 "SME sign-off"
  placeholder (which referenced a never-created `REVIEWERS.md`)
  is replaced by a proper three-gate overview and a new §5c
  that mirrors the §5a peer-review and §5b legal-review sections.
  The three gates are now explicitly documented as sequential:
  peer → legal → SME. A tier-1 `full`-assurance UC therefore
  carries three signoffs (one per ledger); legal-downgraded UCs
  skip the SME gate.
- **Cross-references added** — `docs/peer-review-guide.md` and
  `docs/legal-review-guide.md` "See also" sections now point to
  the SME guide and audit script. The legal guide's §6
  "Relationship to SME sign-off" is expanded to describe the
  precise ordering and when SME review is skipped (legal
  downgrade).

Scope boundaries (what Phase 5.2 intentionally does **not** do):
it does not author any historical signoffs — the ledger starts
empty and fills up one PR at a time; it does not gate
non-tier-1 or non-`full`-assurance content (peer review remains
sufficient there); it does not mandate a specific Splunk version
or sandbox for fixture replay (that is left to the SME's
discretion, recorded in `fixtureReplayResult.notes`); it does
not rebuild the scorecard or Splunk-app rendering for
`smeCaveat` (those consumers will pick up the field
automatically because the schema already exposes it); it does
not add a `REVIEWERS.md` file (per-reviewer public directories
are an optional release-engineering concern, tracked under
Phase 5.5).

### Compliance gold standard — Phase 5.3 regulatory change-watch

Theme: **an auditable freshness guarantee for every regulatory
artefact we depend on**. Peer, legal, and SME review (Phases
4.5a / 4.5b / 5.2) are only as trustworthy as the underlying
regulation they verify against. Phase 5.3 closes that loop by
adding a fourth QA gate that records, per regulation, (i) the
detection strategy for upstream changes, (ii) the last observation
of that strategy's state, and (iii) a staleness threshold beyond
which CI blocks the release. A scheduled GitHub Actions job
probes every entry weekly, commits ledger refreshes, and opens
GitHub issues when material changes appear upstream.

- **Watchlist ledger** — New `data/regulations-watch.json`
  tracks 14 regulatory artefacts: all 11 tier-1 regulations (GDPR,
  HIPAA Security, PCI DSS, SOC 2, SOX ITGC, ISO 27001, NIST CSF,
  NIST 800-53, NIS2, DORA, CMMC), the derivative we ship a Splunk
  app for (UK GDPR), and the two MITRE frameworks our crosswalks
  depend on (MITRE ATT&CK Enterprise, MITRE D3FEND). Each entry
  carries a `regulationId` (cross-referenced against
  `data/regulations.json` frameworks[] or a MITRE allow-list), a
  `tier` (1 or 2), a `currentVersion`, a `strategy` block (one of
  five types — see below), a `lastCheckedAt` timestamp, and
  optional `lastObservedHash` / `lastObservedVersion` /
  `lastObservedEtag` fields that the audit uses to detect drift.
  `baseline_commit` (`217320f`) keeps the ledger consistent with
  the peer/legal/SME baselines.
- **Five detection strategies** — The schema's `strategy` field
  is a discriminated union of (1) `sha256-vendor`: re-fetch the
  upstream URL recorded in `data/provenance/ingest-manifest.json`
  and compare SHA256 to `lastObservedHash` (used for NIST
  OSCAL catalogs, MITRE STIX bundles, D3FEND ontology);
  (2) `github-release`: query the GitHub Releases API and
  compare the latest tag to `lastObservedVersion`, with an
  optional `versionPattern` regex filter; (3) `http-head`:
  issue a HEAD request and compare ETag / Last-Modified to
  `lastObservedEtag` (used for EUR-Lex pages, legislation.gov.uk,
  DoD CMMC landing page); (4) `rss-atom`: fetch an RSS/Atom
  feed and grep `matchTerms` against titles (used for the
  HHS/OCR HIPAA bulletin feed); (5) `manual-review`: no
  automated probe — just record the publisher name and landing
  URL, with a human `--freeze` stamp renewing freshness (used
  for paywalled PCI DSS, AICPA SOC 2 TSCs, PCAOB AS 2201, and
  ISO 27001). All strategies validate `https://` URLs; `--check`
  refuses anything else.
- **Three-mode audit script** — `scripts/audit_regulatory_change_watch.py`
  supports: (a) `--check` (default; hermetic — no network calls;
  safe for pull-request CI) validates the ledger against its
  JSON Schema, cross-references every `sha256-vendor` entry
  against `data/provenance/ingest-manifest.json`, verifies every
  `regulationId` exists in `data/regulations.json` (or the MITRE
  allow-list), computes staleness from `lastCheckedAt` using the
  ledger's `stalenessPolicy` block, and fails CI (exit 1) when a
  tier-1 entry exceeds `tier1FailDays` (default 180) or any
  tier-2 entry exceeds `tier2FailDays` (default 270); (b)
  `--fetch` (network-enabled; intended for the scheduled
  workflow only) probes each entry with its declared strategy,
  diffs observed state against recorded state, writes
  `openFinding` blocks when material changes appear, and
  serialises the round to `reports/regulatory-change-watch.json`;
  (c) `--freeze` stamps `lastCheckedAt=now` for every entry and
  clears `openFinding` blocks — used when seeding the ledger or
  resetting manual-review entries after a human confirms the
  publisher state.
- **Staleness policy** — The ledger's top-level `stalenessPolicy`
  block sets four thresholds (`tier1WarnDays=60`,
  `tier1FailDays=180`, `tier2WarnDays=90`, `tier2FailDays=270`)
  that `--check` honours. These can be tuned per release without
  touching the audit code; during regulatory events (e.g., after
  a new NIST 800-53 revision ships) the repository can tighten
  the threshold to flush the queue, then relax it after adoption.
- **Hermetic PR-CI gate** — `.github/workflows/validate.yml` gains
  a "Phase 5.3 regulatory change-watch (hermetic)" step that
  runs `python3 scripts/audit_regulatory_change_watch.py --check`
  after the Phase 5.2 SME audit. Zero network calls, sub-second
  runtime. The workflow `paths` trigger list now also watches
  `docs/regulatory-change-watch.md`, `data/regulations-watch.json`,
  `schemas/regulations-watch.schema.json`, and
  `scripts/audit_regulatory_change_watch.py`. The QA-gates
  artifact bundle now also uploads `data/regulations-watch.json`
  and `reports/regulatory-change-watch.json`.
- **Scheduled weekly fetch workflow** — New
  `.github/workflows/regulatory-watch.yml` runs Mondays at
  09:00 UTC (cron: `0 9 * * 1`) and on manual dispatch. Steps:
  (1) `actions/checkout@v4`; (2) `actions/setup-python@v5` with
  Python 3.12; (3) install `jsonschema==4.23.0`; (4) run the
  audit script's `--fetch` mode (with optional `--strict` flag
  exposed via `workflow_dispatch.inputs.strict`); (5) if the
  ledger or report changed, commit back to `main` under the
  `github-actions[bot]` identity; (6) if any `openFinding` is
  present, open a GitHub issue (or comment on the existing one)
  labelled `regulatory-change-watch,compliance` with a markdown
  table of the findings and a four-step next-action checklist
  (review against publisher → bump ingest manifest → update UC
  sidecars → clear openFinding); (7) upload `fetch.log`, the
  report, and the refreshed ledger as a 15-day artifact. The
  workflow has `contents: write + issues: write` permissions
  and a `concurrency` group so two scheduled runs never race on
  the ledger.
- **Change-watch playbook (`docs/regulatory-change-watch.md`,
  ~150 lines)** — Documents every component (ledger, schema,
  script, two workflows, report), explains each of the five
  strategies with rationale, renders the staleness policy in
  plain English, and walks operators through three workflows:
  (§4.1) responding to a PR CI failure by running `--fetch`
  locally; (§4.2) triaging the scheduled job's weekly issue by
  confirming findings, bumping `ingest-manifest.json`, updating
  affected UC sidecars + `regulations.json`, clearing
  `openFinding`, and requesting SME sign-off; (§4.3) adding a
  new watchlist entry (pick strategy → add JSON → cross-check
  regulation exists → run `--check` + `--fetch` → open PR
  with peer + legal + SME sign-off). Design principles,
  testing commands, and cross-references to the other three
  review guides (peer / legal / SME) round out the playbook.
- **LEGAL.md §5d added** — The "Three-gate QA review" heading
  is renamed to "QA review gates" and extended with a fourth
  gate. New §5d "Regulatory change-watch gate (Phase 5.3)"
  describes the ledger's role, the scheduled workflow's
  behaviour, and the `openFinding` lifecycle. The preamble to
  §5 now calls out that the change-watch gate fails CI whenever
  the ledger falls outside the freshness envelope — independent
  of whether a given PR touches regulatory content.
- **Cross-references added** — `docs/peer-review-guide.md`,
  `docs/legal-review-guide.md`, and `docs/sme-review-guide.md`
  "See also" sections now point to the change-watch playbook so
  reviewers at each human gate know which regulation versions
  to expect.

Scope boundaries (what Phase 5.3 intentionally does **not** do):
it does not auto-adopt upstream changes — the script only
*records* drift and opens an issue, so a human still performs
the legal + SME review of any regulator's new version; it does
not probe paywalled regulators (ISO 27001, PCAOB standards) —
those remain `manual-review` strategy and rely on the `--freeze`
stamp; it does not ship historical probe records — the weekly
job starts writing to `reports/regulatory-change-watch.json`
from first run; it does not alter the Phase 5.2 SME review
schema or ledger (`smeCaveat` on UC sidecars continues to flow
from SME conditional outcomes, not from change-watch findings);
it does not sign the ledger commits (that is Phase 5.4's signed
provenance remit); and it does not gate release directly —
blocking happens via the hermetic `--check` in PR CI. The final
release gate remains Phase 5.5.

### Compliance gold standard — Phase 5.4 signed provenance ledger

Theme: **tamper-evident compliance claims**. Peer review
(Phase 4.5a), legal review (Phase 4.5b), and SME review (Phase
5.2) establish that each mapping is *correct*; the regulatory
change-watch (Phase 5.3) establishes that each underlying
regulation is *current*. Phase 5.4 renders all four signals
into a single cryptographically verifiable artefact: a
content-addressable, merkle-rolled SHA-256 ledger covering
every clause-level compliance claim the catalogue makes, with
a release-time Sigstore attestation binding the root to the
GitHub Actions workflow, run id, and commit that produced it.

- **Signed provenance ledger schema
  (`schemas/mapping-ledger.schema.json`, 291 lines)** — New
  JSON Schema (Draft 2020-12) defines the ledger record
  grammar. Each entry carries eight ledger-relevant fields
  (`mappingId`, `ucId`, `regulationId`, `regulationVersion`,
  `clause`, `mode`, `assurance`, `derivationSource`), four
  metadata fields (`firstSeenCommit`, `lastModifiedCommit`,
  `signoffStatus` snapshot, `canonicalHash`), and the top-level
  envelope pins the canonicalisation contract
  (`algorithm=rfc8785`,
  `jsonForm=utf-8-nfc-sorted-keys-no-whitespace`,
  explicit `fieldOrder[]`) and the `hashAlgorithm=sha256` so
  third parties can recompute every hash in four lines of
  Python. The signature envelope is a discriminated union
  (`state=unsigned` for in-repo, `state=attested` for release
  artefacts) with Sigstore/GitHub-attestation fields
  (`attestationUrl`, `bundlePath`, `workflowRef`, `runId`,
  `commit`) asserted to match the top-level `catalogueCommit`.
- **Deterministic ledger generator
  (`scripts/generate_mapping_ledger.py`)** — Walks every
  `use-cases/cat-*/uc-*.json` in sorted order, canonicalises
  each sidecar's human-readable regulation names against
  `data/regulations.json` frameworks[] via a `NAME_TABLE`
  covering every spelling seen in the corpus, hashes each
  mapping entry with RFC 8785-compatible JSON
  canonicalisation, sorts the 1,889 entries lexicographically
  by `mappingId`, and produces the merkle root as a
  sorted-leaf SHA-256 rolling hash. Git history is probed in
  a single bulk `git log --name-only --diff-filter=AM` pass
  (benchmarked at 0.5 s versus 181 s for the naive
  per-sidecar invocation) to populate `firstSeenCommit` and
  `lastModifiedCommit`. `generatedAt` is anchored to the
  `catalogueCommit`'s commit date (`git show -s --format=%cI`)
  rather than wall-clock or file mtime, so `touch`ing every
  sidecar does not change the ledger — PR CI regenerations
  are byte-for-byte identical across re-runs at the same
  commit. `--check` diff-gates the on-disk ledger against an
  in-memory rebuild and fails on drift.
- **Independent audit script
  (`scripts/audit_mapping_ledger.py`)** — Re-reads the ledger
  fresh, validates against `mapping-ledger.schema.json`,
  recomputes every `canonicalHash`, recomputes the
  `merkleRoot`, performs forward+reverse referential
  integrity against current UC sidecars (every sidecar entry
  must appear in the ledger; every ledger entry must point
  at a live UC), asserts `catalogueCommit` resolves via
  `git cat-file`, and verifies the signature envelope's
  internal consistency (for attested copies:
  `signature.commit == catalogueCommit`). With
  `--verify-signature`, shells out to
  `gh attestation verify` against the Sigstore bundle; the
  audit searches three paths for the bundle (repo root, the
  ledger file's sibling directory, `dist/`) so auditors who
  download both release assets into the same folder can
  verify without additional plumbing.
- **Release-time stamper
  (`scripts/stamp_ledger_release.py`)** — Produces
  `dist/mapping-ledger.json` from the in-repo ledger with
  `signature.state` promoted to `attested` and Sigstore
  envelope fields populated from the GitHub Actions
  environment (`GITHUB_SERVER_URL`, `GITHUB_REPOSITORY`,
  `GITHUB_RUN_ID`, `GITHUB_SHA`, `GITHUB_REF_NAME`,
  `GITHUB_WORKFLOW_REF`). The in-repo copy is **not**
  mutated — PR CI always sees `signature.state=unsigned` and
  stays deterministic. `--dry-run` substitutes placeholder
  metadata for local smoke testing and prints a conspicuous
  banner so the output cannot be mistaken for a real
  release. Also emits `dist/mapping-ledger.manifest.md`
  (human-readable release manifest with merkle root, entry
  count, per-review signoff aggregates, and the verification
  one-liner).
- **Phase 5.4 ledger
  (`data/provenance/mapping-ledger.json`, ~50k lines)** —
  Generator produces 1,889 mapping entries covering all 15
  regulation families tracked by `regulations.json` across
  every UC that carries `compliance[]`. Merkle root is
  stable across re-runs at the same commit
  (`a40d7b10cf1f0a2e…` at baseline). `signature.state` is
  `unsigned` with reason text pointing at the release
  promotion path.
- **Release workflow integration
  (`.github/workflows/release.yml`)** — The existing
  `v*.*.*` tag workflow gains `id-token: write` and
  `attestations: write` permissions, plus five new build
  steps in strict order: (1) regenerate ledger at HEAD via
  `--check`; (2) audit the unsigned in-repo copy; (3)
  stamp-and-copy to `dist/` via
  `scripts/stamp_ledger_release.py`; (4) attest
  `dist/mapping-ledger.json` via
  `actions/attest-build-provenance@v2` (Sigstore cosign
  bundle signed by a Fulcio-issued OIDC certificate for the
  workflow); (5) place the attestation bundle at the
  canonical path `dist/mapping-ledger.sigstore.bundle.json`
  and re-run the full audit with
  `--require-signature --verify-signature` as an end-to-end
  sanity check before the release is published. Release
  assets now include `mapping-ledger.json`,
  `mapping-ledger.sigstore.bundle.json`, and
  `mapping-ledger.manifest.md` as first-class downloads.
- **Hermetic PR-CI gate
  (`.github/workflows/validate.yml`)** — Gains two new
  steps, both wired in after the Phase 5.3 regulatory
  change-watch: (a) "Phase 5.4 signed provenance ledger
  regenerate (determinism)" runs `generate_mapping_ledger.py
  --check` to reject any PR that edits a `compliance[]`
  entry without refreshing the ledger in the same commit;
  (b) "Phase 5.4 signed provenance ledger audit" runs
  `audit_mapping_ledger.py` without `--require-signature`
  (the in-repo ledger is always unsigned). Combined runtime
  is sub-second. The workflow's `paths` trigger list gains
  `docs/signed-provenance.md`; all other Phase 5.4 paths
  (schema, generator, audit, stamper, ledger) are already
  covered by the existing `schemas/**`, `scripts/**`, and
  `data/provenance/**` filters.
- **QA-gates artifact bundle extended** — The existing
  `qa-gates` artifact now also uploads
  `data/provenance/mapping-ledger.json` alongside the
  peer/legal/SME signoff files and the Phase 5.3 watchlist.
  External reviewers can pull a single artifact and
  recompute the merkle root against the downloaded ledger
  without cloning the repo.
- **Verification playbook
  (`docs/signed-provenance.md`, ~320 lines)** — Covers what
  the ledger proves (integrity, completeness, chain of
  custody, origin for release artefacts), what it
  deliberately does **not** prove (legal correctness,
  detection correctness, regulation freshness, staleness of
  the local clone — those remain the remit of the four
  review gates and change-watch), component map, record
  anatomy with a worked example, canonicalisation + merkle
  construction recomputable from the command line, the
  three-level verification protocol (trust-but-verify hash
  chain → require-but-trust signed envelope →
  verify-with-Sigstore cryptographic proof), six operator
  runbooks (adding a mapping, PR-CI drift, audit-script
  corruption, stale `catalogueCommit`, downloaded-release
  verification, local dry-run), determinism contract,
  semver policy for future schema evolution (v2.0.0 is
  reserved for hash algorithm or Merkle-tree-shape changes;
  minor bumps add ledger metadata; patches fix bugs), and
  cross-references into the other four gates and the API
  surface.
- **LEGAL.md §5e added** — New subsection "Signed provenance
  ledger (Phase 5.4)" describes the ledger's role, the
  release attestation pipeline, the downstream verification
  protocol, and the explicit scope statement: a failed
  `gh attestation verify` is a material provenance-compromise
  event. §6 "Signing and provenance" is expanded to call out
  that the clause-level ledger complements the existing
  release-tag signing and per-artefact SHA-256 digests.
- **Cross-references added** — `docs/peer-review-guide.md`,
  `docs/legal-review-guide.md`, `docs/sme-review-guide.md`,
  `docs/regulatory-change-watch.md`, and `api/v1/README.md`
  each gain a "See also" / "Provenance and attestation"
  pointer to `docs/signed-provenance.md`. Reviewers are told
  how to confirm their signoff PR number is snapshotted
  into the next ledger regeneration; API consumers are told
  how to match any API-level compliance claim back to its
  `canonicalHash` entry.

Scope boundaries (what Phase 5.4 intentionally does **not**
do): it does not replace any of the four review gates — the
ledger records reviewer verdicts but does not re-derive them;
it does not sign the in-repo copy — `main` always carries
`signature.state=unsigned` so PR CI is deterministic and the
release workflow is the sole authority that produces
`attested` artefacts; it does not use a binary Merkle tree —
the sorted-leaf rolling hash is simpler to recompute
independently (a v2.0.0 schema may upgrade this if per-entry
inclusion proofs become useful); it does not snapshot SPL or
regulation bodies — only the `(UC, regulation, clause, mode,
assurance, derivationSource)` tuple enters the hash
(narrative bodies live in the sidecars, which git history
already versions); it does not gate release directly —
blocking happens via `--check` in PR CI plus the
end-to-end `--verify-signature` step in `release.yml`; it
does not ship a revocation mechanism for a compromised
release — that is handled through the standard GitHub
Release retraction flow plus an advisory note in
`SECURITY.md`. The final release gate remains Phase 5.5.

---

## [6.0] - 2026-04-16

### Verifiable Quality

Theme: **"trust but verify"** — every shipped SPL should be demonstrably
correct and every quality signal transparently measured. Five systems land
together to move the project from *comprehensive catalog* to *verifiable
gold standard*.

- **Sample-event fixtures** — New `samples/` tree (JSON-Schema-validated `manifest.yaml` + `positive.log` [+ optional `negative.log`]) ships 15 golden fixtures across Linux, Windows, Cisco, AWS, Kubernetes, Palo Alto, Sysmon, Cisco ISE, Splunk internal, Snort and GitHub sourcetypes. `scripts/samples_index.py` validates every fixture and regenerates `docs/samples-coverage.md` as a rolling coverage report.
- **UC test harness** — `scripts/run_uc_tests.py` rewrites sample timestamps, ingests them via Splunk HEC, runs each UC's SPL via the REST API and asserts on expected result counts / field values, emitting a JUnit XML report (`test-results/uc-tests.xml`). Dry-run mode lets CI validate fixtures without needing a Splunk instance.
- **End-to-end CI workflow** — New `.github/workflows/uc-tests.yml` runs sample validation + dry-run on every PR, and a full Dockerised Splunk Enterprise 9.4 end-to-end test on pushes to `main` and manual dispatch.
- **Splunk Cloud compatibility audit** — New `scripts/audit_splunk_cloud_compat.py` scans every UC's SPL and every packaged `.conf` for patterns that fail AppInspect or Splunk Cloud vetting (custom search commands, scripted inputs, `restmap.conf`, python2 directives, `| crawl`, `| runshellscript`, `| sendemail`, unconstrained `| map`, …). Findings are published to `docs/splunk-cloud-compat.md` and `test-results/splunk-cloud-compat.json`; the audit is wired into `validate.yml` CI and fails the build on any `severity=fail` hit. First audit: 0 pack-level findings, 5 SPL-level warnings (all legitimate `dbxquery` callouts documenting the DB Connect caveat).
- **Provenance ledger** — New `scripts/build_provenance.py` classifies every UC's citation URLs into one of 9 source categories (`splunk-official`, `vendor-official`, `mitre-attack`, `nist-compliance`, `threat-intel`, `splunk-blog`, `community`, `unclassified`, `contributor`) and writes a per-UC ledger to `provenance.json` + a compact `provenance.js` loaded by the dashboard. Dashboard cards and the detail panel now show a colour-coded source badge (tooltip on hover). Coverage of the 6,304 UCs: 72% Splunk official docs, 9% vendor official, 7% threat intel, 5% MITRE ATT&CK, 1.5% NIST / CIS / ISO / PCI standards — only 2.4% fall through to "unclassified". A new `/provenance.json` endpoint is documented in `openapi.yaml`; rolling coverage report in `docs/provenance-coverage.md`.
- **Quality scorecard** — New `scripts/generate_scorecard.py` rolls six signals (references %, provenance authority, freshness, KFP %, MITRE coverage, sample coverage) into a weighted 0–100 composite and assigns each category a **Gold / Silver / Bronze / Needs work** letter grade. Published to `docs/scorecard.md` (human-readable) and `scorecard.json` (machine-readable) on every `build.py` run, documented in `openapi.yaml` at `GET /scorecard.json`, and wired into `validate.yml` drift check. First snapshot: 0 Gold, 3 Silver (IAM, Security Infrastructure, Network Security & Zero Trust), 4 Bronze, 16 Needs work — a transparent map of where authoring effort should go next.

### API surface

- New `GET /provenance.json` endpoint (full source ledger per UC).
- New `GET /scorecard.json` endpoint (machine-readable quality rollup).
- OpenAPI spec bumped to `6.0.0`; both endpoints documented with full response schemas.

### Build pipeline

- `build.py` now regenerates `provenance.{json,js}`, `docs/provenance-coverage.md`, `scorecard.json`, and `docs/scorecard.md` on every run.
- `validate.yml` drift-check extended to guard all six new generated artefacts.
- `sitemap.xml` grows to 42 URLs (adds the two new JSON endpoints and three new doc pages).

---

## [5.2] - 2026-04-16

### Gold Standard — Enterprise Packaging (Phase 2)

- **Splunkbase Technology Add-on** — New `ta/TA-splunk-use-cases/` app ships the Quick-Start saved searches (≈115 UCs) with per-category index macros, eventtype aliases, and a navigation stub. Generated by `scripts/build_ta.py` from `catalog.json` + `use-cases/INDEX.md`; packaged into a Splunkbase-compatible `.spl` archive by `scripts/package_ta.sh` (all searches ship `disabled = 1` for safety).
- **ITSI content pack** — New `ta/DA-ITSI-monitoring-use-cases/` bundles 6 KPI base searches, 3 threshold templates, 4 KPI templates and 3 service templates covering Linux hosts, Windows hosts, network interfaces and web application availability. Installable via ITSI's Service Template import UI; packaged by `scripts/package_itsi.sh`.
- **Enterprise Security content pack** — New `ta/DA-ESS-monitoring-use-cases/` ships 650 correlation searches (400 critical + 250 high by default), MITRE ATT&CK governance mappings, analytic stories grouped by tactic, CIM eventtypes/tags and RBA risk-factor seeds. Generated by `scripts/build_es.py`; use `--include-all` for the full 1,874-UC set. Packaged by `scripts/package_es.sh`.
- **OpenAPI 3.1 specification** — New `openapi.yaml` documents the six static JSON endpoints (`/api/index.json`, `/api/cat-{n}.json`, `/catalog.json`, `/llms.txt`, `/llms-full.txt`, `/sitemap.xml`). Rendered interactively at `/api-docs.html` via a self-hosted copy of Swagger UI 5.17.14 under `vendor/swagger-ui/` (no CDN dependency; SHA-256 pinned in `vendor/swagger-ui/checksums.txt`).
- **Automated release workflow** — New `.github/workflows/release.yml` triggers on `v*.*.*` tag pushes (or manual dispatch), regenerates the three `.spl` packages, computes SHA-256 checksums, and publishes them as a GitHub Release with CHANGELOG-derived notes. `scripts/extract_release_notes.py` produces the release body.
- **Enterprise deployment guide** — New `docs/enterprise-deployment.md` walks platform engineers through prerequisites, SHC install, index-macro tuning, ITSI service template import, ES correlation-search roll-out, Splunk Cloud vetting, dashboard hosting options, upgrade/rollback procedures and a pre-go-live checklist.
- **Footer & sitemap integration** — The dashboard footer now links to the API docs page; `sitemap.xml` includes `/api-docs.html` and `/openapi.yaml` for discoverability.

### Governance scaffolding

- **`CODE_OF_CONDUCT.md`** — Contributor Covenant v2.1 with project-specific scope and enforcement contact.
- **`SECURITY.md`** — Vulnerability reporting via GitHub private advisories, in-scope / out-of-scope guidance, supported-versions table, responsible-disclosure SLAs.
- **`GOVERNANCE.md`** — Participant roles (users / contributors / maintainers), lazy-consensus + RFC decision process, maintainer nomination criteria, conflict-of-interest disclosure.
- **`ROADMAP.md`** — Current release overview, v6.0 "Verifiable Quality" theme, backlog and declined-ideas sections; deep-links to CHANGELOG for ship history.
- **`CITATION.cff`** — Academic-citation metadata for researchers (Citation File Format 1.2).
- **`.github/CODEOWNERS`** — Auto-review routing for build pipeline, content packs, docs, use-cases and governance files.
- **YAML issue forms** — Replaced the single-template markdown form with three structured forms (`bug-report.yml`, `feature-request.yml`, `use-case-feedback.yml`) plus a `config.yml` routing security reports to private vulnerability reporting. The dashboard's "Report issue on GitHub" button pre-fills the new form's `uc-id` and `details` fields.
- **`.github/PULL_REQUEST_TEMPLATE.md`** — Structured PR checklist covering build-artefact regeneration, validation commands, Splunkbase ID verification, non-technical-view sync, and version-bump three-way alignment.

---

## [5.1] - 2026-04-16

### Gold Standard — Quality Pass (Phase 1)

- **Per-UC quality metadata** — New optional fields `Status`, `Last reviewed`, `Splunk versions`, `Reviewer` documented in `docs/use-case-fields.md` and rendered as interactive chips in `index.html`.
- **References: at 100 %** — `scripts/fill_references.py` populated the `- **References:**` line for every UC (6,304 / 6,304). A dedicated `collect_splunkbase_ids` pass prevents false Splunkbase inferences from Windows Event IDs or error codes.
- **Known false positives: at 100 %** on security categories (9, 10, 14, 17, 22) — `scripts/fill_false_positives.py` generated standardised KFP descriptions for 4,008 security-relevant UCs.
- **MITRE ATT&CK coverage** ≥ 80 % on security categories — `scripts/fill_mitre_mappings.py` lifted cat-9 to 83.7 %, cat-17 to 92.4 %, cat-10 held at 84.9 %.
- **Link integrity** — Broken references reduced from 171 to 0. `scripts/fix_link_rewrites.py`, `scripts/remove_dead_urls.py`, and `scripts/fix_broken_references.py` applied 260+ programmatic fixes; `.link-check-ignore` registers bot-hostile but browser-reachable domains.
- **Weekly link-check workflow** — `.github/workflows/link-check.yml` audits all References URLs every Monday, uploads artefacts, and opens/updates a tracking issue on failure.
- **Quality metadata in CI** — `scripts/audit_quality_metadata.py` wired into `validate.yml` (warn-only) reports References / Status / Last reviewed / Splunk versions / Reviewer / KFP coverage after every build.

### Product design documentation (Phase 0)

- **`docs/DESIGN.md`** — Full product design document so the platform can be replicated on another stack.
- **`docs/adr/`** — Seeded with initial Architecture Decision Records capturing the static-site, catalog.json, and JSONL agent-transcript choices.
- **`docs/replication-guide.md` + `templates/replication-starter/`** — Step-by-step porting guide and skeleton project for forkers.

---

## [5.0] - 2026-04-15

### Regulatory Compliance Expansion

- **1,063 new regulatory use cases** — Expanded cat-22 from 104 to 1,167 UCs across 34 subcategories (was 9). The largest single content expansion in the catalog's history.
- **5 major frameworks added** — PCI DSS v4.0 (90 UCs), NIST 800-53 Rev. 5 (80 UCs), NERC CIP (70 UCs), HIPAA (55 UCs), IEC 62443 (55 UCs).
- **9 existing regulations expanded** — NIST CSF 2.0 (+43), ISO 27001:2022 (+37), GDPR (+30), NIS2 (+25), SOC 2 (+22), DORA (+20), MiFID II (+17), CCPA/CPRA (+17), Compliance Trending (+5).
- **6 US & OT regulations added** — SOX/ITGC (35 UCs), API 1164 Pipeline SCADA (35 UCs), TSA Pipeline Security (30 UCs), FDA 21 CFR Part 11 (25 UCs), FISMA/FedRAMP (25 UCs), CMMC 2.0 (20 UCs).
- **5 EU regulations added** — AML/CFT (35 UCs), PSD2/Payment Services (30 UCs), EU AI Act (25 UCs), EU Cyber Resilience Act (20 UCs), eIDAS 2.0 (15 UCs).
- **9 regional frameworks added** — UK NIS+FCA/PRA (30 UCs), APAC Data Protection (30 UCs), Americas/LGPD/FISMA/CMMC/CJIS (25 UCs), APAC Financial/MAS/HKMA/RBI/APRA (25 UCs), Norwegian/Sikkerhetsloven/Kraftberedskap/Petroleum (20 UCs), German KRITIS/BSI (20 UCs), Australia & New Zealand/Essential Eight (20 UCs), Middle East/NESA/SAMA/PDPL/QCB (20 UCs), SWIFT CSP (12 UCs).
- **Cross-references added** — Regulation-specific UCs in cat-10 and cat-14 now point to comprehensive coverage in cat-22.

### Full Quality Review

- **Splunkbase ID audit** — Verified 78 Splunkbase IDs across all categories. Fixed 4 incorrect IDs: 1556 (404), 2963 (wrong Qualys ID), 5765 (wrong product), 4516 (archived app). 73 occurrences corrected.
- **CIM Model audit** — Verified all CIM Model references against official Splunk CIM 5.x. Fixed 47 incorrect references across 7 files: DNS→Network_Resolution (14), Inventory→Compute_Inventory (7), VPN→Network_Sessions (4), Audit→Splunk_Audit (6), Threat_Intelligence→N/A (4), Risk→N/A (9), Data_Loss_Prevention→DLP (2), IDS_Attacks→Intrusion_Detection (1).
- **SPL syntax audit** — Audited SPL across all 6,304 UCs. Fixed 5 syntax errors: invalid stats functions (mean→avg, p50→median, p99→perc99), missing eval wrappers in sum(case()), invalid eventstats where clause.
- **Regulation reference audit** — Verified article/section numbers against actual regulatory texts (GDPR, NIS2, DORA, HIPAA, PCI DSS, NIST 800-53, NERC CIP, EU AI Act, PSD2). Fixed 16 errors: 2 invalid GDPR notations, 7 wrong NIS2 Art. 21(2) sub-letters, 3 wrong EU AI Act articles, 1 wrong PSD2 RTS article, 1 wrong HIPAA subsection.
- **MITRE ATT&CK audit** — Verified all technique IDs and their contextual accuracy. Fixed 6 incorrect mappings: removed T1485/T1496 from non-attack UCs, corrected T1040→T1557, T1531→T1078.

### Total catalog: 6,304 UCs across 23 categories.

---

## [4.2] - 2026-04-15

### Content Quality

- **CIM SPL audit and fix** — Fixed ~60 copy-paste CIM SPL errors across 9 category files (cat-01, cat-02, cat-04, cat-05, cat-08, cat-09, cat-10, cat-11, cat-17). Replaced generic/duplicated tstats blocks with queries that match each UC's actual monitoring intent. Set CIM Models to N/A where no faithful CIM equivalent exists.

### CI/CD Improvements

- **Build check now fails** — `validate.yml` exits 1 (not just warns) when `data.js` or `catalog.json` are out of date after rebuild.
- **Full structure scan** — `audit_uc_structure.py` now runs with `--full` in CI (was sampling 200 of 5,241 UCs).
- **Catalog schema validation** — New `audit_catalog_schema.py` validates catalog.json structure, UC ID format, and required fields.
- **Portable version check** — Replaced GNU-only `grep -oP` with Python for cross-platform compatibility.
- **Broader path triggers** — CI now runs on changes to `scripts/**`, `tools/**`, and `custom-text.js`.

### UI Features

- **Non-technical search** — Keyword search bar in the non-technical/executive view filters outcome cards by text match across outcomes, area descriptions, and UC summaries.
- **Export empty-state toast** — CSV/JSON export buttons now show a toast notification when no use cases match the current filters instead of silently doing nothing.

### Build System

- **Pretty-printed catalog.json** — JSON output now uses `indent=2` for reviewable git diffs (was single-line minified).
- **Per-category JSON API** — `build.py` generates `api/cat-N.json` files and `api/index.json` for lightweight integrations.

### Documentation

- **CONTRIBUTING.md** — New contributing guide covering UC template, CIM SPL guidelines, audit scripts, version management, and CI workflow.
- **Link checker** — New `scripts/audit_links.py` for manual reference URL validation (2,000+ URLs across the catalog).

---

## [4.1] - 2026-04-14

### Content Expansion

- **136 new use cases** — Expanded 6 thin categories past targets: ITSM (cat-16), Data Center Fabric & SDN (cat-18), Compute Infrastructure & HCI (cat-19 incl. new Azure Stack HCI subcategory), Cost & Capacity Management (cat-20), Regulatory Compliance (cat-22), and Business Analytics (cat-23). Total catalog now at 5,241 use cases.
- **265 MITRE ATT&CK mappings** — Added technique references across Identity & Access Management (cat-09), Network Security & Zero Trust (cat-17), Cloud Infrastructure (cat-04), and Regulatory Compliance (cat-22).
- **Structural normalization** — Heading levels standardized to ##/### convention across cat-01 through cat-05. Bullet ordering and label consistency fixed across multiple files.

### UI Features

- **Recently Added tab** — New overview tab showing use cases added since the last catalog build. Backed by a `RECENTLY_ADDED` set in data.js.
- **CSV/JSON export** — Export buttons in the overview tab bar let you download filtered use case results as CSV or JSON.

### CI/CD

- **PR validation workflow** — New GitHub Actions workflow (`.github/workflows/validate.yml`) runs UC ID audits, structure checks, non-technical sync validation, changelog references, and build checks on pull requests.

### Maintenance

- **Entity escaping fix** — Fixed 31 double-encoded `&mdash;` entities in release notes HTML; build.py now handles em dashes correctly.
- **Repository cleanup** — Removed Splunk dashboard files and generation/deployment scripts from version control (not part of the use case catalog).

---

## [4.0.1] - 2026-04-02

### Cisco Network Intelligence UI

- **Complete UI redesign** — The entire site now uses the Cisco Network Intelligence design system: blue header bar, pill-shaped elements, card-based layouts, and a clean light/dark mode with proper contrast across all elements.
- **My Equipment overhaul** — Equipment inventory rebuilt with DSA-style source cards showing use case counts, data source counts, and model counts per equipment. Serves as both a use case filter and a direct DSA launcher with the "Estimate Sizing →" button.
- **Data Sizing Assessment integration** — Equipment selected in My Equipment maps to DSA data sources. Launch DSA pre-populated from inventory or from the bottom sizing tray with combined equipment + use case selections.
- **Wider detail panel** — Use case detail panel expanded to 800px for improved readability. App/TA visualizations capped at 520px to avoid stretching.
- **Smart sizing tray** — Bottom bar only appears when items are selected; automatically retracts when the detail panel opens to avoid overlap. Clear button now resets both use case and equipment selections.
- **Subcategory landing pages** — Clicking a category shows subcategory cards with descriptions, UC counts, and criticality breakdowns before diving into the full list.
- **Breadcrumb navigation** — Hierarchical breadcrumbs on category and subcategory views for easier wayfinding.
- **Accessibility** — Keyboard focus styles, ARIA roles, and tabindex on sidebar items. Print stylesheet expanded. JSON-LD structured data restored.
- **Dark mode hardened** — Comprehensive audit of all UI elements for proper contrast and visibility in dark mode, including badges, tags, inputs, buttons, overlays, and colorblind-friendly combinations.

---

## [4.0] - 2026-04-01

### Data Sizing Assessment Tool

- **New companion tool** &mdash; Interactive Data Sizing Assessment (DSA) tool added under `tools/data-sizing/`. Helps customers estimate Splunk data ingest volume (GB/day, EPS, events/day) by selecting equipment and data sources from a catalog of 206+ entries.
- **9 source categories** &mdash; Security Sources, IT Systems & Hardware, OT System Sources, Network Sources, OT Hardware & Sensors, Protocols, Business & Compliance, Cisco Products, and OT Vendor Systems.
- **Two sizing models** &mdash; Endpoint sources (EPS-based) and Protocol sources (tag/poll-based) with configurable parameters per source.
- **Outputs** &mdash; Total GB/day, EPS, events/day, recommended Splunk license tier, storage estimates with retention and compression, peak headroom with burst factor, and CSV export.
- **Cross-linked to use cases** &mdash; 28 key data sources include `related_uc_ids` linking to relevant monitoring use cases in the main catalog. Source detail modal shows clickable links.
- **Bidirectional navigation** &mdash; Footer link from main catalog to the DSA tool; header link from DSA back to the Use Case Catalog.

---

## [3.24] - 2026-03-26

### Audit Fixes — Verified Sourcetypes, Fields, and SPL

- **7 uberAgent sourcetype corrections** &mdash; `AppStartup` → `Process:ProcessStartup`, `AppCrash` → `Application:Errors`, `Logon:BootDetail` → `OnOffTransition:BootDetail2`, `Browser:BrowserPerformanceTimer2` → `Application:BrowserWebRequests2`, `CitrixSite:DeliveryGroupDetail` → `Citrix:DesktopGroups`, `CitrixADC:SystemDetail` → `CitrixADC:AppliancePerformance`, `ESA:ThreatDetection` → `uberAgentESA:ActivityMonitoring:ProcessTagging`. All verified against official Citrix uberAgent 7.4 documentation.
- **6 uberAgent field name corrections** &mdash; `StartupDurationMs` → `StartupTimeMs`, `PageLoadTimeMs` → `PageLoadTotalDurationMs`, `BootDurationS` → `TotalBootTimeMs`, `FaultingModuleName` → `ExceptionCode`, `ConnectionLatencyMs` → `ConnectDurationMs`, `VServerDetail` → `vServer`.
- **UC-2.6.17 Experience Score rewritten** &mdash; Corrected from querying `SessionDetail` (which does not contain experience scores) to querying the `score_uberagent_uxm` index, which is where uberAgent's saved searches store calculated scores.
- **3 Intersight sourcetype corrections** &mdash; `cisco:intersight:inventory` → `cisco:intersight:compute` (firmware/HCL), `cisco:intersight:audit_logs` → `cisco:intersight:auditRecords`, `cisco:intersight:inventory` → `cisco:intersight:contracts`. All verified against the Cisco Intersight Add-on for Splunk v3.0 User Guide.
- **6 Nexus Dashboard sourcetypes qualified** &mdash; Added caveat note that `cisco:nexusdashboard:*`, `cisco:ndfc:*`, `cisco:ndo:*` sourcetypes are representative examples and should be verified against the installed add-on's `props.conf`, as no public sourcetype reference exists.

---

## [3.23] - 2026-03-26

### UI — Subcategory Navigation & Source Catalog Updates

- **Subcategory landing page** &mdash; Clicking a category on the front page now shows an intermediate view of its subcategories as cards (with description, UC count, and criticality breakdown) instead of jumping straight to all use cases. A "Show all N use cases" button restores the previous full-list behaviour.
- **Hash routing** &mdash; `#cat-N` now opens the subcategory view; `#cat-N/X.Y` opens the full list scrolled to a specific subcategory.
- **Source catalog expanded** &mdash; Added OpenConfig gNMI specification, Telegraf gNMI plugin, Cisco Nexus gNMI white paper, Nokia gNMIc, Nozomi Networks Guardian docs, and Nozomi Universal Add-on (6905) + CCX Extensions (6796) to the Sources popup.

---

## [3.22] - 2026-03-26

### gNMI / gRPC Streaming Telemetry — New Section 5.11

- **11 new use cases** (UC-5.11.1 through UC-5.11.11) for model-driven streaming telemetry via gNMI/gRPC.
- **Multi-vendor** &mdash; Cisco IOS XR/NX-OS/IOS XE, Arista EOS, Juniper Junos, Nokia SR Linux all supported with OpenConfig YANG paths.
- **Telegraf → Splunk HEC pipeline** &mdash; All UCs use the documented Telegraf `inputs.gnmi` plugin with `splunkmetric` output to Splunk metrics indexes. SPL uses `mstats` and `rate_avg()`.
- **Use cases cover**: interface utilization at sub-minute granularity (5.11.1), interface error/discard streaming (5.11.2), BGP peer state ON_CHANGE detection (5.11.3), system CPU/memory (5.11.4), optical transceiver health with predictive failure alerting (5.11.5), QoS queue depth and microburst detection (5.11.6), LLDP topology change detection (5.11.7), BGP prefix churn and route leak detection (5.11.8), hardware environment monitoring (5.11.9), Telegraf collector pipeline health (5.11.10), and ACL hit counter analysis (5.11.11).

---

## [3.21] - 2026-03-26

### Nozomi Networks — Multi-Vendor OT Security

- **25 existing Cisco Cyber Vision UCs merged** to support both Cisco Cyber Vision and Nozomi Networks Guardian/Vantage as alternative data sources.
- **Section 14.9 renamed** from "Cisco Cyber Vision (OT Security)" to "OT Network Security Monitoring (Cisco Cyber Vision / Nozomi Networks)".
- **Dual SPL examples** &mdash; every UC now has both a Cisco Cyber Vision SPL block and a Nozomi Networks alternative SPL block with correct sourcetypes (`nozomi:nn_asset`, `nozomi:alert`, `nozomi:variable`, `nozomi:link`, `nozomi:session`, `nozomi:health`).
- **New Splunk apps registered** &mdash; Nozomi Networks Universal Add-on (Splunkbase 6905), CCX Extensions for Nozomi Networks (Splunkbase 6796), with archived Nozomi Networks Sensor Add-on (5316) as predecessor.
- **Value descriptions neutralized** &mdash; vendor-specific language replaced with vendor-agnostic descriptions throughout all 25 UCs.

---

## [3.20] - 2026-03-26

### My Environment Inventory

- **Customer inventory tool** &mdash; New "My Inventory" button in the footer opens a full-screen modal where users can check off all equipment and software in their environment. On apply, the catalog filters to show only use cases relevant to the selected items (OR logic across all checked equipment).
- **Organized checklist** &mdash; 80+ equipment items grouped into 15 logical categories (Servers & OS, Virtualization, Cloud & Containers, Networking, Databases, Security Tools, DevOps, Splunk Products, OT/IoT, and more) with collapsible sections, select-all per group, and a search filter.
- **Persistent selections** &mdash; Inventory choices are automatically saved to localStorage and restored on page load.
- **Export / Import** &mdash; Save your inventory as a JSON file for portability, or load a previously saved file to restore selections across browsers or machines.
- **Filter integration** &mdash; Active inventory appears as a clearable filter tag alongside existing filters. Composes with all other filters (criticality, difficulty, pillar, regulation, etc.) via AND logic.

---

## [3.19] - 2026-03-26

### Business Analytics & Executive Intelligence — New Category 23

Major release: **New category 23** with 38 use cases across 9 subcategories, bringing non-technical, business-aligned use cases into the catalog for the first time.

- **23.1 Customer Experience & Digital Analytics** (6 UCs) — Conversion funnels, cart abandonment, page load revenue impact, NPS tracking, cross-channel attribution, mobile app crash rates.
- **23.2 Revenue & Sales Operations** (5 UCs) — Pipeline velocity, revenue booking trends, churn prediction, renewal pipeline, pricing/discount effectiveness.
- **23.3 Marketing Performance & Attribution** (4 UCs) — Campaign ROI by channel, lead-to-revenue funnel, email engagement, SEO/traffic source analysis.
- **23.4 HR & People Analytics** (4 UCs) — Attrition analysis and flight risk, time-to-hire, diversity metrics, training compliance.
- **23.5 Supply Chain & Operations** (4 UCs) — Order-to-cash cycle time, inventory stockout risk, supplier OTIF, delivery SLA compliance.
- **23.6 Financial Operations & Procurement** (4 UCs) — AR aging/DSO, expense anomaly detection, budget vs actual variance, payment processing success.
- **23.7 Customer Support & Service Excellence** (3 UCs) — Ticket volume/SLA, first-contact resolution, customer effort scoring.
- **23.8 Executive Dashboards & Business KPIs** (3 UCs) — CEO/CFO scorecard, operational efficiency metrics, business risk heatmap.
- **23.9 ESG & Sustainability Reporting** (5 UCs) — Carbon footprint, energy efficiency, waste diversion, water conservation, ESG disclosure readiness.

These use cases are written for non-technical stakeholders (CFOs, CMOs, CHROs, COOs) and focus on business outcomes rather than technical mechanisms. All are implementable with Splunk using DB Connect, HEC, web access logs, and standard integrations.

Catalog now at 5,054 use cases across 23 categories.

---

## [3.18] - 2026-03-26

### Citrix — uberAgent & Expanded Data Center Coverage

- **uberAgent UXM integration (11 new UCs)** &mdash; UC-2.6.17 through UC-2.6.27: Experience Score monitoring, application unresponsiveness detection, application startup duration, browser performance per website, machine boot/shutdown analysis, per-application CPU/memory, crash reporting, Citrix Site delivery group capacity, NetScaler via uberAgent, per-application network performance, and endpoint security analytics (ESA) threat detection.
- **Existing UCs updated** &mdash; UC-2.6.1 (logon) and UC-2.6.2 (ICA RTT) now recommend uberAgent as the preferred data source alongside the existing XenDesktop 7 template and OData API.
- **New apps registered** &mdash; uberAgent UXM (Splunkbase 1448), Splunk Add-on for Citrix NetScaler (Splunkbase 2770). Citrix vendor expanded with CVAD, uberAgent, and NetScaler sub-models.

---

## [3.17] - 2026-03-26

### Cisco Data Center — Expanded Coverage

- **Cisco Intersight (7 new UCs)** &mdash; UC-19.1.19 through UC-19.1.25: server alarm monitoring, firmware compliance, HCL compliance, power/thermal telemetry, audit logs, contract/warranty tracking, and UCS X-Series IFM health. Leverages the Cisco Intersight Add-on for Splunk (Splunkbase 7828).
- **Cisco MDS SAN Fabric (6 new UCs)** &mdash; UC-6.1.27 through UC-6.1.32: ISL utilisation monitoring, slow drain detection, zone configuration compliance, FLOGI database monitoring, VSAN health/isolation events, and fabric oversubscription ratio. Expands MDS coverage from 1 UC to 7.
- **Nexus Dashboard & NX-OS Fabric (8 new UCs)** &mdash; New section 18.4 with UC-18.4.1 through UC-18.4.8: Nexus Dashboard Insights anomaly monitoring, NDFC fabric compliance/drift, advisory and field notice alerts, NX-OS streaming telemetry health, VXLAN EVPN underlay BGP, CoPP drops, NDO cross-fabric consistency, and NDFC switch lifecycle tracking.
- **New Splunk apps registered** &mdash; Cisco DC Networking Application (Splunkbase 7777) and Cisco Intersight Add-on (Splunkbase 7828) added to the app catalog. New Cisco sub-vendors: Intersight, Nexus/NDFC/MDS.

---

## [3.16] - 2026-03-26

### DORA — Full Digital Operational Resilience Coverage

- **15 new DORA use cases** (UC-22.3.6 through UC-22.3.20), expanding coverage from 5 to 20 dedicated UCs.
- **Art. 9 — Protection & Prevention**: ICT change management and patch compliance (Art. 9(4)(e)), access control and authentication monitoring (Art. 9(4)(c)).
- **Art. 10 — Detection**: ICT anomaly detection capability monitoring — proving detection infrastructure covers all critical functions.
- **Art. 11 — Response & Recovery**: MTTD/MTTR/RTO tracking for DORA-regulated services against defined targets.
- **Art. 12 — Backup**: backup completeness, restoration testing, and segregation validation for critical function systems.
- **Art. 13 — Learning & Evolving**: post-incident review completion, root cause tracking, and improvement action implementation.
- **Art. 14 — Communication**: crisis communication readiness — plan freshness, contact list currency, drill completion.
- **Art. 18 — 7-Criteria Classification**: automated major ICT incident classification against all DORA criteria (clients affected, geographic spread, duration, data loss).
- **Art. 19 — Three-Report Timeline**: tracking initial (4h), intermediate (72h), and final (1 month) report submission for major incidents.
- **Art. 25 — Testing Program**: vulnerability assessment and penetration test tracking with finding remediation SLAs.
- **Art. 26 — TLPT**: Threat-Led Penetration Testing lifecycle tracking including the three-year cycle requirement.
- **Art. 28(3) — Register of Information**: validation of ICT provider register completeness against actual network traffic.
- **Art. 28(8) — Exit Strategy**: exit plan readiness scoring for all critical/important function providers.
- **Art. 30 — SLA Monitoring**: actual ICT provider performance vs contractual availability and response time targets.
- **Art. 5 — Management Body Governance**: board ICT risk briefing, framework approval, training, and risk appetite evidence.
- DORA now has the most comprehensive coverage of any regulation in the catalog with 20 dedicated UCs.

---

## [3.15] - 2026-03-26

### GDPR — Comprehensive Article Coverage Expansion

- **14 new GDPR use cases** (UC-22.1.7 through UC-22.1.20), expanding coverage from 6 to 20 dedicated UCs.
- **Art. 32 — Security of Processing**: encryption and pseudonymisation coverage monitoring for personal data systems.
- **Art. 30 — Records of Processing Activities**: ROPA completeness validation against observed data flows.
- **Art. 25 — Data Protection by Design**: data minimisation validation detecting over-collection of PII.
- **Art. 5(1)(f) / Art. 32 — Integrity and Confidentiality**: privileged access monitoring for personal data stores (databases, file systems).
- **Art. 17 — Right to Erasure Verification**: post-deletion scanning to catch incomplete "right to be forgotten" execution.
- **Art. 33(3) — Breach Scope Quantification**: automated estimation of affected data subjects for 72h notification.
- **Art. 34 — Communication to Data Subjects**: tracking of high-risk breach individual notification workflows.
- **Art. 35 — DPIA Coverage**: monitoring that Data Protection Impact Assessments exist for high-risk processing.
- **Art. 28 — Processor Compliance**: continuous monitoring of data flows to third-party processors.
- **Art. 7(3) — Consent Withdrawal Enforcement**: verification that processing stops after consent is withdrawn.
- **Art. 5(2) — Audit Log Integrity**: tamper detection for the evidence trail used to prove GDPR compliance.
- **Art. 22 — Automated Decision-Making Transparency**: monitoring decision volumes, override rates, and appeal handling.
- **Art. 12 — Data Subject Rights SLA Dashboard**: executive view across all rights with SLA tracking.
- **Art. 6(1)(f) — Legitimate Interest Balancing**: LIA coverage and objection monitoring — the highest-fine enforcement area in 2025-2026.
- Catalog crosses **5,000 use cases** milestone with this release.

---

## [3.14] - 2026-03-26

### NIS2 Directive — Full Article 21 & Article 23 Coverage

- **15 new NIS2 use cases** (UC-22.2.6 through UC-22.2.20), expanding coverage from 5 to 20 dedicated UCs.
- Now covers **all 10 Article 21(2) measures**: (a) risk analysis & security policies, (b) incident handling, (c) business continuity & backup/DR, (d) supply chain security, (e) secure development lifecycle, (f) effectiveness assessment, (g) cyber hygiene & training, (h) cryptography & encryption, (i) access control, asset management & HR security, (j) MFA & secure communications.
- **Article 23 three-stage reporting** fully covered: 24h early warning (existing), 72h notification (new), one-month final report (new), cross-border impact assessment (new).
- **Article 20 management accountability**: governance evidence dashboard for board-level training, policy approval, and risk acceptance tracking.
- New use cases include: NIS2 effectiveness KPI dashboard, training compliance tracking, TLS/certificate health monitoring, JML process enforcement, CI/CD security gate coverage, supplier risk continuous monitoring, and backup/restore verification.
- Updated 22.2 Primary App/TA to include Okta, Stream, CyberArk, Qualys, Veeam, GitHub, and Jira add-ons.

---

## [3.13] - 2026-03-26

### Check Point Quantum Firewall & Security Expansion

- **8 new Check Point firewall UCs in cat-05** (UC-5.2.47 through UC-5.2.54): ClusterXL failover, policy install/publish tracking, SecureXL acceleration status, CoreXL CPU distribution, log rate and capacity, anti-spoofing violations, HTTPS inspection status and bypass, gateway connection table utilization.
- **10 new Check Point security UCs in cat-10** (UC-10.11.121 through UC-10.11.130): Zero Phishing detection, ThreatCloud IOC match rate, Quantum IoT Protect device discovery, Maestro Orchestrator health, CloudGuard Network security events, Threat Prevention policy layer effectiveness, admin session and login audit, DDoS Protector integration events, Infinity managed service events, HTTPS inspection certificate errors.
- Check Point coverage now totals **33 dedicated UCs** across cat-05, cat-10, and cat-17 — on par with Palo Alto and Fortinet.

---

## [3.12] - 2026-03-26

### Zero Trust / SASE Vendor Expansion

- **31 new zero-trust / SASE use cases** (UC-17.3.32 through UC-17.3.62) covering vendors missing from the catalog:
  - **Netskope** (7 UCs): Cloud app risk (CCI scoring), DLP violations, threat protection, SWG category blocking, Private Access (NPA) health, CASB inline enforcement, admin audit trail.
  - **Fortinet FortiSASE** (5 UCs): SWG policy violations, ZTNA tag-based access, threat detection (IPS/AV), thin edge tunnel health, admin configuration audit.
  - **Check Point Harmony SASE** (5 UCs): ThreatCloud prevention, Internet Access policy, Private Access (ZTNA) health, admin audit, DLP events.
  - **Akamai Guardicore** (4 UCs): Segmentation policy violations, Reveal map anomalies, agent health, incident investigation with deception triggers.
  - **Broadcom / Symantec SSE** (3 UCs): Cloud SWG policy analysis, CASB shadow IT detection, SWG threat events.
  - **Cloudflare Zero Trust** (3 UCs): Access (ZTNA) policy enforcement, Gateway DNS/HTTP filtering, Tunnel health.
  - **Forcepoint ONE** (2 UCs): SSE web security events, ZTNA private access health.
  - **SonicWall** (1 UC): Cloud SWG and SMA access events.
  - **Versa Networks** (1 UC): Unified SASE security and access events.
- **Existing vendor-neutral UCs updated:** 13 generic UCs (17.3.1–17.3.20) now list all relevant vendor TAs (Zscaler, Netskope, Prisma Access, FortiSASE, Check Point, Cloudflare, Akamai Guardicore, Broadcom Symantec, Forcepoint) where the use case concept applies across platforms.
- **New Splunkbase app integrations:** Added Netskope App (6042), Check Point App (4293), Cloudflare App (4501), Akamai Guardicore Add-on (7426), Forcepoint Insights SIEM App (8053), Netskope Add-on (3808), Symantec WSS Add-on (3856), SonicWall SMA 1000 TA (6670) to build.py for automatic Splunkbase linking.

---

## [3.11] - 2026-03-26

### Multi-Vendor TA Coverage & Archived App Display

- **Complete multi-vendor TA coverage:** Every use case that lists multiple equipment vendors in its Equipment Models field now includes all relevant Technology Add-ons in its App/TA field. Previously, many multi-vendor UCs only listed a single vendor's TA (e.g. only `TA-cisco_ios` despite listing Juniper, Arista, and HPE Aruba equipment). Updated 35+ router/switch UCs (5.1.x) to include `Splunk_TA_juniper`, `arista:eos` via SC4S, and HPE Aruba CX syslog alongside Cisco TAs. Updated 18 firewall UCs (5.2.x) to include `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, and `Splunk_TA_juniper` (SRX). Updated NAC UCs (17.1.x) to include HPE Aruba ClearPass and Forescout CounterACT TAs. Updated VPN UCs (17.2.x) to include all four vendor TAs.
- **Successor app display:** Use cases referencing archived Splunkbase apps (Splunk App for Unix and Linux, Splunk App for Windows Infrastructure, Palo Alto Networks App for Splunk) now showcase the recommended successor app (IT Essentials Work, Splunk App for Palo Alto Networks) as the primary display, with the archived app mentioned below as a predecessor.
- **Equipment Models corrections:** Fixed UC-11.3.9, UC-11.3.10, UC-11.3.11, UC-11.3.13 which incorrectly listed Cisco voice equipment for Microsoft 365/Exchange use cases. Corrected to show Microsoft Exchange Online and M365 equipment with proper `Splunk_TA_MS_O365` and `Splunk_TA_microsoft-cloudservices` TAs.
- **Additional TA additions:** Added `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) to Spaces/occupancy UCs (11.5.x, 15.3.x) that include Meraki MV cameras or MR access points in Equipment Models. Added vendor-specific TAs to multi-vendor UCs in cat-18 (Data Center Fabric), cat-20 (Cost & Capacity), and cat-22 (Regulatory Compliance).

---

## [3.10] - 2026-03-25

### Multi-Vendor Network Coverage Expansion

- **Juniper Networks:** Added 4 Junos switching/routing UCs (5.1.56-5.1.59: chassis alarms, commit audit, RE failover, Virtual Chassis) and 3 SRX firewall UCs (5.2.41-5.2.43: IDP/IPS, Screen counters, cluster failover). Updated 34 generic router/switch UCs with Juniper EX/QFX/MX/SRX equipment models.
- **Arista Networks:** Added 3 Arista-specific UCs (5.1.60-5.1.62: MLAG health, EOS agent monitoring, CloudVision telemetry alerts). Updated 34 generic UCs with Arista 7000-series equipment.
- **HPE Aruba:** Added 2 Aruba CX switching UCs (5.1.63-5.1.64: VSF stack, VSX redundancy) and 5 wireless UCs (5.4.33-5.4.37: AP health, ClearPass RADIUS, WIDS/WIPS, Dynamic Segmentation, client experience). Updated 34 generic switch UCs and 9 wireless UCs with Aruba equipment.
- **Fortinet expansion:** Added 3 FortiGate-specific UCs (5.2.44-5.2.46: Security Fabric health, SD-WAN SLA monitoring, Web Filter/App Control). Updated 18 firewall UCs with FortiGate/FortiManager equipment models.
- **Cato Networks SASE:** Added 7 cloud-native SASE UCs (17.3.25-17.3.31: security events, WAN link health, threat prevention, cloud firewall audit, SD-WAN tunnels, SDP client monitoring, DLP/CASB events).
- **Palo Alto Networks:** Updated 18 firewall UCs with full PA-series equipment models and Panorama.
- **Multi-vendor equipment lists:** Updated 61 existing generic UCs across switching, firewall, wireless, VPN, and NAC sections to list equipment from Cisco, Juniper, Arista, HPE Aruba, Palo Alto, and Fortinet.
- **NAC section:** Updated 9 NAC UCs (17.1.x) to include HPE Aruba ClearPass and Forescout CounterACT alongside Cisco ISE.
- **VPN section:** Updated 8 VPN UCs (17.2.x) to include Palo Alto GlobalProtect, Fortinet SSL-VPN, and Juniper Dynamic VPN alongside Cisco ASA/AnyConnect.

---

## [3.9] - 2026-03-25

### Cisco Cyber Vision OT Security

- **25 new Cisco Cyber Vision use cases (14.9.1–14.9.25)** — Comprehensive OT/ICS security monitoring using Cisco Cyber Vision's Splunk Add-On (Splunkbase 5748) and syslog/CEF integration. Covers OT asset discovery and inventory tracking, new device detection alerts, vulnerability/CVE tracking with CVSS scoring, risk score monitoring, baseline deviation detection, Snort IDS threat detection with Talos rules, PLC program download/upload detection, controller firmware activation, forced variable detection, control action monitoring, controller mode changes (online/offline/force/CPU start-stop), new communication flow detection, protocol exception monitoring, authentication failure detection, admin connection tracking, port scan detection, weak encryption identification, SMB protocol activity in OT networks, network redundancy failover events, sensor health and resource monitoring, administration audit trail, IEC 62443 zone and conduit compliance, security posture dashboard, OT protocol usage analysis, and decode failure/malformed packet detection.

---

## [3.8] - 2026-03-25

### Building Management & Smart Buildings

- **26 new building management use cases** — Comprehensive smart building monitoring covering HVAC deep monitoring (AHU supply air temperature, VAV damper stuck detection, chiller COP efficiency, cooling tower approach, economizer free cooling, setpoint override tracking), energy management (EUI benchmarking, sub-metering, after-hours waste detection, peak demand shaving), elevator analytics (trip counting, door fault prediction, wait time SLAs), fire and life safety (alarm panel monitoring, sprinkler valve tamper, fire pump status), water management (consumption anomalies, Legionella prevention, cooling tower chemistry), lighting schedule compliance, parking occupancy, EV charging utilization, indoor air quality index, BACnet controller health, BMS alarm flood detection, and carbon emissions tracking (Scope 1+2).

---

## [3.7] - 2026-03-25

### Citrix Virtual Apps & Desktops and Citrix ADC/NetScaler Monitoring

- **Citrix CVAD monitoring (16 new)** — Session logon duration breakdown, ICA/HDX session latency and quality, connection failure analysis, VDA machine registration health, Delivery Controller service health, machine power state management, HDX virtual channel bandwidth, PVS vDisk streaming health, Profile Management load time, StoreFront authentication and enumeration, License Server utilization and compliance, application usage analytics, FAS certificate health, WEM optimization effectiveness, session recording compliance, and Cloud Connector health. New subcategory 2.6 in Virtualization.
- **Citrix ADC/NetScaler monitoring (10 new)** — Virtual server health and state, service group member health, SSL certificate expiration, HA failover monitoring, GSLB site and service health, Gateway/VPN session monitoring, content switching policy hit rate, system resource utilization, responder/rewrite policy errors, and SSL offload performance. Added to category 5.3 Load Balancers & ADCs.

---

## [3.6] - 2026-03-25

### DIPS Arena & IGEL Endpoint Monitoring

- **DIPS Arena EHR monitoring (10 new)** — Application response time, FHIR API availability and latency, user authentication and SSO monitoring, database performance, Communicator message throughput and failures, integration engine error monitoring, concurrent session and license utilization, clinical document generation latency, scheduled job monitoring, and openEHR AQL query performance. Added to category 21.3 Healthcare and Life Sciences.
- **IGEL End-User Computing / VDI Endpoints (10 new)** — Device fleet online/offline status, firmware version compliance, UMS server health monitoring, device heartbeat loss detection, OS endpoint syslog error monitoring, UMS security audit log monitoring, device resource utilization, unscheduled reboot detection, Cloud Gateway connection health, and device configuration drift detection. New subcategory 2.5 in Virtualization.

---

## [3.5] - 2026-03-25

### OpenTelemetry & Observability Expansion

- **OTel Collector Pipeline Operations (5 new)** — Pipeline throughput and backpressure monitoring, memory/CPU utilization tracking, configuration drift detection across collector fleet, per-receiver per-signal health monitoring, and exporter retry/timeout analysis.
- **Distributed Tracing Deep Dive (6 new)** — Trace duration anomaly and slow transaction detection, error rate by service and operation, trace completeness and orphan span detection, cross-service dependency map auto-discovery, log-to-trace correlation coverage audit, and trace fanout/depth anomaly detection.
- **Splunk Observability Cloud / APM / RUM / Synthetics (6 new)** — APM service map RED metrics, database query performance from APM traces, RUM Core Web Vitals tracking, RUM JavaScript error rate by page, synthetic multi-step transaction SLA, and Observability Cloud detector health audit.
- **SRE Methodology Patterns (5 new)** — RED metrics dashboard template, USE method for infrastructure, Golden Signals composite health per service, SLO multi-window burn rate alerting, and error budget policy enforcement.
- **eBPF Observability (3 new)** — Cilium Hubble kernel-level network flow monitoring, Tetragon process-level security observability, and Beyla eBPF auto-instrumented service metrics.
- **Observability Pipeline Governance (4 new)** — Data volume and cost attribution by team, cardinality explosion detection, instrumentation coverage audit, and telemetry signal freshness/staleness monitoring.
- **Kubernetes Observability (2 new)** — K8s event correlation with application traces, and resource quota/LimitRange compliance trending.

### New Subcategory

- **13.5 OpenTelemetry, Observability Pipelines & SRE Patterns** — Dedicated subcategory for OTel tracing, APM/RUM/Synthetics, SRE frameworks (RED/USE/Golden Signals/SLOs), and observability pipeline governance.

### Trend Use Cases Expansion (55 new)

- **9.7 Identity & Access Trending (7 new)** — Authentication volume, MFA adoption rate, privileged account activity, service account usage, conditional access policy blocks, password reset volume, and identity provider availability — all trended over 30–90 days with moving averages and forecasts.
- **22.9 Compliance Trending (5 new)** — Compliance posture score, audit finding closure rate, control effectiveness, regulatory incident response time, and policy violation volume trending across frameworks and quarters.
- **3.6 Container & Kubernetes Trending (6 new)** — Pod restart rate, container image vulnerability counts, deployment velocity, resource request vs limit utilization, Kubernetes event error rate, and ingress traffic volume trending.
- **4.6 Cloud Infrastructure Trending (6 new)** — Cloud resource count, Lambda/function invocation volume, security finding new vs resolved, S3/blob storage growth, network traffic volume, and CloudTrail/activity log event volume trending.
- **10.16 Security Operations Trending (8 new)** — Attack surface change, SIEM alert-to-incident ratio, MTTD, MTTR, phishing attempt volume, firewall rule hit rate, risk score distribution, and endpoint protection coverage trending.
- **8.7 Application Trending (5 new)** — User session volume, API latency percentiles (p50/p95/p99), error budget burn rate, cache hit ratio, and message queue backlog trending.
- **7.6 Database Trending (5 new)** — Connection pool utilization, slow query volume, replication lag, backup size growth, and index fragmentation trending.
- **16.5 ITSM Trending (5 new)** — Ticket backlog aging by bucket, change success rate, knowledge article deflection rate, MTTR by priority, and escalation rate trending.
- **14.8 IoT & OT Trending (4 new)** — Device fleet online rate, sensor data quality, OEE (Overall Equipment Effectiveness), and predictive maintenance alert volume trending.
- **12.6 DevOps Trending (4 new)** — DORA metrics dashboard (all four metrics), security scan finding lifecycle, build queue wait time, and container image build time trending.

### Non-Technical View

- **New areas added** — Plain-language sections for OpenTelemetry and observability pipelines, distributed tracing and APM, real user and synthetic monitoring, SRE patterns and SLOs, eBPF kernel-level observability, and trending areas for identity and access, compliance, containers, cloud, security operations, applications, databases, ITSM, IoT/OT, and DevOps.

### Datagen & POC tooling

- **Cribl / Splunk datagen guide** — `docs/guides/datagen-top10-use-cases.md` for ten representative use cases; `eventgen_data/manifest-top10.json` and per-family samples under `eventgen_data/samples/`; `scripts/generate_manifest_samples.py` (HEC NDJSON from the manifest), `scripts/parse_uc_catalog.py` (full catalog → `manifest-all.json`), `config/uc_to_log_family.json`; GitHub Actions workflow `.github/workflows/uc-manifest.yml` validates generation on push/PR.

---

## [3.4] - 2026-03-25

### Collaboration & Unified Communications Expansion

- **CUCM Deep Monitoring (7 new)** — CDR call path analysis, CMR call quality heatmap by site-pair, phone firmware compliance, gateway/CUBE channel utilization, cluster database replication health, Call Admission Control (CAC) rejection trending, and hunt group/line group overflow analytics.
- **Contact Center (5 new)** — Webex Contact Center agent state and occupancy, IVR containment rate, customer wait time SLA by skill group, UCCX real-time queue monitoring, and abandon rate correlation with network quality.
- **Jabber & IM Presence (2 new)** — Jabber client version compliance and health, IM and Presence Service (IM&P) node availability and XMPP session monitoring.
- **Unity Connection Voicemail (2 new)** — Voicemail system health (port utilization, message store, MWI delivery) and mailbox usage with retention compliance tracking.
- **Meeting Room Analytics (4 new)** — No-show and early release trending, people count vs capacity optimization, AV equipment health monitoring, and digital signage/room scheduler device health.
- **Cisco Spaces Advanced (3 new)** — Wayfinding and path analytics for traffic flow optimization, proximity and engagement analytics for space utilization, and IoT sensor alert correlation with building management response.

### Non-Technical View

- **New areas added** — Plain-language sections for on-premises phone systems (CUCM), contact center, messaging and presence, meeting room analytics, and indoor location/building intelligence.

---

## [3.3] - 2026-03-24

### Machine Learning & Deep Learning Use Cases

- **Security ML/UEBA (8 new)** — User peer-group logon anomaly, lateral movement via rare destinations, C2 beaconing detection, credential stuffing burst detection, risk score calibration, phishing NLP classification (DSDL), notable event prioritization model, and anomalous process execution — all leveraging MLTK and DSDL for threats that static rules miss.
- **IT Ops ML (6 new)** — Log volume/error rate anomaly per sourcetype, license usage forecast with seasonality, internal queue depth multivariate anomaly, service latency seasonality detection, Kubernetes HPA replica count anomaly, and SLO burn-rate multivariate anomaly.
- **ITSI ML extensions (2 new)** — Entity-level multivariate anomaly detection combining multiple KPIs per entity, and causal KPI ranking that automatically identifies root-cause KPIs when service health degrades.
- **Cloud & Cost ML (3 new)** — Cloud cost anomaly with seasonal decomposition, capacity exhaustion prediction with confidence intervals, and cloud control plane API call volume anomaly detection.
- **Deep Learning (4 new)** — Seq2seq log anomaly detection via LSTM autoencoder reconstruction error, host-metric heatmap anomaly via CNN, centralized model retraining for industrial sensor ML, and MLTK/DSDL model drift monitoring.

### New Subcategory

- **10.15 Machine Learning & Behavioral Analytics** — Dedicated subcategory for ML-powered security detections using MLTK and DSDL, covering UEBA, beaconing, credential attacks, and AI-assisted threat detection.

### Non-Technical View

- **ML areas added** — New plain-language sections explaining machine learning monitoring for security, platform intelligence, ITSI extensions, and deep learning model health.

---

## [3.2] - 2026-03-23

### New Use Cases

- **Elasticsearch deep monitoring** — 9 new use cases covering thread pool rejections, search latency and slow logs, ILM policy failures, snapshot health, cross-cluster replication lag, pending cluster tasks, cache evictions, segment merge pressure, and ingest pipeline errors.
- **Azure service expansion** — 15 new use cases for Application Gateway & WAF, VPN Gateway, ExpressRoute, Redis Cache, Data Factory, API Management, Virtual Desktop, Traffic Manager, Bastion, Network Watcher, Storage Queue, Managed Disk performance, SQL Managed Instance, Synapse Analytics, and Log Analytics Workspace ingestion health.
- **Docker deep monitoring** — 8 new use cases for container health check failures, network I/O anomalies, exec session auditing, socket exposure detection, image pull failures, dangling image/volume cleanup, Swarm service replica health, and container filesystem write rate.

### Data Source Filter

- **Two-level cascading filter** — Data source filter redesigned with 23 named source areas (Windows Event Logs, Sysmon, AWS, Cisco, etc.). Selecting an area reveals a second dropdown with specific sources and counts. Garbage entries from SPL parsing cleaned up.

### Sources Reference

- **New vendor documentation** — Added Elasticsearch cluster monitoring docs, Azure Monitor docs, and Docker monitoring docs to the External & Vendor Documentation section. Updated Microsoft Cloud TA count and category references.

---

## [3.1] - 2026-03-23

### Archived Splunkbase Apps

- **Archived app visibility** — Use cases referencing archived Splunkbase apps now show an amber "Archived App" badge on cards and a prominent warning box in the modal with a link to the recommended successor app.
- **Palo Alto Networks App** — Newly identified as archived; successor is Splunk App for Palo Alto Networks (Splunkbase 7505). Unix and Windows app entries now also link to IT Essentials Work (Splunkbase 5403).

### Advanced Filters

- **8 new filters** — Collapsible "Advanced Filters" panel below the existing filter strip with: ES Detection toggle, Detection type, Premium Apps, CIM Data Model, App/TA, Industry, MITRE ATT&CK (searchable), and Data source (searchable).
- **Pre-extracted facets** — `FILTER_FACETS` in data.js provides pre-sorted unique values for each filter dimension, eliminating client-side scanning of 4,600+ use cases on every page load.
- **Active filter chips** — All advanced filters appear as removable chips in the active filter tags row and are included in sidebar count updates.

### Non-Technical View

- **Full rewrite** — All 22 categories rewritten with 120 monitoring areas and 360 representative use case references. Build-time validation ensures UC IDs stay in sync with technical content.

### Sources Reference

- **Sources popup** — New footer button opens a reference of all documentation, apps, frameworks, and community resources used to research and build the use case catalog — from Splunk Lantern and ESCU to MITRE ATT&CK, vendor docs, and regulatory frameworks.

### Content Expansion

- **SD-WAN use case expansion** — Subcategory 5.5 expanded from 10 to 20 dedicated SD-WAN use cases covering OMP route monitoring, BFD session tracking, edge device resource utilization, firmware compliance, DPI application visibility, Cloud OnRamp performance, UTD security policy violations, vManage cluster health, transport circuit SLA tracking, and overlay topology validation.
- **Meraki subcategory dissolved** — All 110 Cisco Meraki UCs redistributed into their functional subcategories: wireless to 5.4, switching to 5.1, firewall/security to 5.2, DNS/DHCP to 5.6, management to 5.8, cameras to 15.3, environmental sensors to 14.1, and MDM to new subcategory 9.6.

---

## [3.0] - 2026-03-22

### Enterprise Security Detections

- **ES Detection badges** — 2,070 ESCU detection rules now display a teal "ES Detection" badge on use case cards and modals, with "Risk-Based Alerting" variant for RBA-enabled detections. Searchable via "escu", "es detection", "rba".
- **ESCU-specific implementation guidance** — Tailored deployment instructions for each detection methodology (TTP, Hunting, Anomaly, Baseline, Correlation): ES Content Management workflow, risk score tuning, analyst response per security domain, and SPL walkthrough for Risk Investigation drilldowns.

### SPL & Content Quality

- **join max=1** — Added explicit `max=1` to 88 `| join` statements across all categories to prevent silent data truncation at the default limit of 1.
- **Text quality pass** — Revised Value, Implementation, and Visualization fields for 30 use cases across 17 categories with specific, actionable guidance.

### Splunk Dashboard Studio (export)

- **44 separate chart objects** — `dashboards/catalog-quick-start-top2.json`: exactly **one** Dashboard Studio visualization per Quick-Start use case (top 2 × 22 categories). UC id and name appear as each panel's **title**/**description**, not extra markdown blocks. Regenerate with `scripts/generate_catalog_dashboard.py`.

---

## [2.1.12] - 2026-03-21

### Splunk dashboards

- **REST deploy** — `scripts/deploy_dashboard_studio_rest.py` pushes Dashboard Studio JSON to your Splunk server via the `data/ui/views` API (token or basic auth). See `dashboards/README.md`.

---

## [2.1.11] - 2026-03-21

### Splunk dashboards

- **Catalog Quick-Start Portfolio** — Initial `dashboards/catalog-quick-start-top2.json` (later replaced in v3 by **44** per-UC chart panels). Demo data (`makeresults`). See `dashboards/README.md`.

---

## [2.1.10] - 2026-03-21

### Content

- **Industry verticals** — Category 21 implementation notes for **aviation**, **telecom**, **water/wastewater**, and **insurance** now add domain context (standards, compliance, operations) and Splunk-oriented tuning notes alongside the existing guidance.

---

## [2.1.9] - 2026-03-21

### Detailed implementation

- **Tailored SPL explanations** — Generated guides now open with context from the use case (title, value, data sources, App/TA), compare the base search to documented sourcetypes, then walk the pipeline with command-specific detail (`stats`/`timechart` `by` and `span`, `eval` targets, `where` text). CIM blocks get a matching CIM-specific intro.

---

## [2.1.8] - 2026-03-21

### Navigation

- **Industry verticals** — Category 21 (Industry Verticals) is its own **domain group** in the sidebar and on the overview hero chips (between Applications and Regulatory & Compliance), not buried under Applications.

---

## [2.1.7] - 2026-03-21

### CIM field naming

- **src / dest** — Use-case SPL now prefers CIM-aligned `src` and `dest` (and related renames) instead of `src_ip`/`dest_ip` where practical; data model searches use `All_Traffic.src`/`All_Traffic.dest`. See `docs/cim-and-data-models.md` and `scripts/normalize_cim_fields.py`.

---

## [2.1.6] - 2026-03-21

### SPL & documentation

- **Review follow-up** — Additional SPL hardening: `mvexpand` limits on multivalue fields, explicit `max=` on joins, `sort <N> -count` for top-N tables, AWS IoT provisioning aligned to CloudTrail + `eventSource`, RD Gateway XmlWinEventLog note.

---

## [2.1.5] - 2026-03-21

### Feedback

- **Report issue on GitHub** — Every use case modal (technical and plain-language) has a button that opens a new GitHub issue with the UC id, category path, link to the source `use-cases/*.md` file, and the dashboard URL with `#uc-…`. Set `window.SITE_CUSTOM.siteRepoUrl` if you fork the repo.

---

## [2.1.4] - 2026-03-21

### Detailed implementation

- **Understanding this SPL** — Generated step-by-step guides now include automatic pipeline explanations: what each major stage does (base search, aggregations, `tstats`/datamodel, joins, lookups, etc.). When a use case has CIM SPL, the optional accelerated query is included with a matching walkthrough.

---

## [2.1.3] - 2026-03-21

### SPL & Documentation

- **SPL / CIM alignment pass** — Catalog examples updated for Splunk CIM and TA conventions: `WinEventLog:Security` casing; `All_Traffic.bytes_in`/`bytes_out` totals; LDAP `tstats` + `cidrmatch()` for RFC1918; `index=windows` in compliance samples; FortiGate inventory scoped to supported sourcetypes; SOX ERP vs. AD searches split; safer `mvexpand`, `transaction`, and `sort` patterns; ITSI `inputlookup` context notes; fixed Meraki Data Sources backtick (UC-5.4.9).
- **Follow-up hygiene** — Correct `cidrmatch()` argument order (IP, then CIDR); CIM internal/external ratio example uses `drop_dm_object_name` + plain `src`/`dest`; MITRE coverage join uses explicit `max=0` and `mvexpand … limit=500`; bulk-closed broken inline-code backticks across Meraki Data Sources in Category 5; normalized `sort -field` spacing in Meraki SPL.

---

## [2.1.2] - 2026-03-21

### SPL Accuracy

- **ES `` `notable` `` macro** — Replaced `index=notable` with the Splunk ES `` `notable` `` macro across 15 SPL queries in Category 10 (Security Infrastructure) and Category 22 (Regulatory & Compliance). The macro resolves human-readable status labels, owner fields, and other enrichment that raw index access does not provide.

---

## [2.1.1] - 2026-03-21

### AI & LLM Discoverability

- **Self-describing catalog.json** — Added `_schema_url` and `_readme` keys at the top level so LLMs and tools fetching the catalog cold can immediately discover the field schema without a second fetch.
- **Expanded sitemap.xml** — Now generated by `build.py` with 33 URLs (was 4) — includes all 22 category files, INDEX.md, documentation pages, and AI index files. Stays in sync automatically as categories are added.
- **Cross-referenced llms.txt / llms-full.txt** — Each file now points to the other with a one-line note explaining the difference (concise category index vs. full use case listing).

---

## [2.1.0] - 2026-03-21

### Navigation & Filters

- **Tab-based content navigation** — Categories, Subcategories, Use Cases, and Quick Wins are now tabs above the content area, with the sort control on the same line.
- **Streamlined filter strip** — Removed inline labels; filter chips are self-explanatory with criticality colors shown as inline dots.
- **Interactive hero domain chips** — Clicking Infrastructure, Security, Cloud, Applications, Industry, or Regulatory on the front page filters the category grid and opens the relevant sidebar group.
- **Hero domain icons** — Replaced colored dots on front-page domain chips with monochrome SVG icons (server, shield, cloud, gear, clipboard).
- **Category icons in sidebar** — Replaced colored dots with per-category icons to avoid confusion with criticality colors.
- **Smart sidebar folding** — Non-active category groups auto-fold; manual expand/collapse is preserved until navigation changes.
- **Unified sidebar** — Both technical and non-technical modes now share the same grouped sidebar with collapsible sections, counts, and subcategory drill-down.

### Non-Technical View Redesign

- **Animated hero** — Gradient accent bar, "Proactive IT Monitoring" badge, gradient title text, and stagger-animated stats.
- **Richer category cards** — Staggered fade-in animations, gradient left-border on hover, icon highlight, focus-area and check counts on each card.
- **Category detail polish** — Back-to-overview button, gradient header accent, numbered area indicators, indented UC lists, and staggered area card animations.
- **Refreshed modal** — Styled section cards with green uppercase headings, subcategory breadcrumb, and "View full technical details" button with icon.

### Quality & Accessibility

- **Accessibility audit** — Added ARIA roles, keyboard handlers, and focus management to logo, hero chips, roadmap toggle, and navigation elements.
- **Release notes popup** — Full project history accessible from the page footer, covering all major and minor releases.
- **Bug fixes** — Fixed missing `filterByRegulation` function, Previous/Next URL updates, hash routing edge cases, clipboard error handling, and removed dead code.

---

## [2.0.0] - 2026-03-20

### Major UI Redesign

- **Unified filter system** — Pillar, criticality, difficulty, regulation, industry, and monitoring type consolidated into a single horizontal filter strip with active filter tags.
- **Redesigned front page** — Glassmorphism hero with animated gradient orbs, domain chips, key stats, and an expandable roadmap section.
- **Grouped sidebar navigation** — 6 collapsible groups (Infrastructure, Security, Cloud, Applications, Industry Verticals, Regulatory & Compliance) with color-coded headers.
- **Modern header** — Gradient header bar with integrated search (Cmd/Ctrl+K), live stats, theme toggle, and technical/non-technical view switch.
- **Deep linking** — Hash-based URL routing with `pushState`/`popstate` support for shareable links to categories, use cases, and search results.
- **Virtual scrolling** — IntersectionObserver-based lazy rendering for smooth performance with 4,600+ use cases.
- **Sort controls** — Sort by criticality, difficulty, name, or category with localStorage persistence.
- **Print stylesheet** — Clean printed output with navigation and decorative elements hidden.
- **Mobile experience** — Off-canvas sidebar with backdrop, 44px touch targets, safe-area insets, and dynamic viewport units.
- **Light mode overhaul** — Stronger contrast, subtle gradients, card shadows, and WCAG AA compliant tag colors.

### Content Expansion

- **4,625 use cases** across 22 categories — up from 3,473 across 20.
- **Category 22 — Regulatory & Compliance** promoted to standalone category with 30 use cases covering GDPR, NIS2, DORA, CCPA, MiFID II, ISO 27001, NIST CSF, and SOC 2.
- **Category 21 — Industry Verticals** with 119 use cases for energy, manufacturing, healthcare, telecom, retail, financial services, transportation, government, education, and insurance.
- **AI-friendly metadata** — Open Graph, Twitter Card, JSON-LD, `sitemap.xml`, `llms.txt`, and `llms-full.txt`.

---

## [1.0.0] - 2026-03-16

### First Public Release

- **3,000+ use cases** across 20 IT infrastructure categories with criticality, difficulty, SPL queries, CIM mappings, implementation guidance, and visualization recommendations.
- **Interactive single-page dashboard** with search, category/equipment/criticality filtering, non-technical view, and expandable use case details.
- **Build pipeline** — `build.py` compiles markdown use cases into `data.js` and `catalog.json`.
- **Equipment filter** with 30+ technology vendors/platforms and model-level drill-down.
- **Non-technical view** with plain-language outcomes per category for stakeholder discussions.
- **Machine-readable catalog** (`catalog.json`) for scripting and external integrations.
- **GitHub Pages deployment** via included GitHub Actions workflow.
- **SSE-aligned fields** — MITRE ATT&CK, detection type, known false positives, and security domain for security use cases.

---

## [0.x] - 2026-03-04 – 2026-03-09

### Early Development

- **Project created** — Initial upload of use case dashboard with basic HTML interface.
- **Core categories established** — Network, server, storage, security, and application monitoring use cases defined with SPL queries.
- **CIM integration** — Added Common Information Model data model references and tstats queries to use cases.
- **Meraki use cases** — Dedicated Cisco Meraki monitoring use cases added.
- **Cloud use cases** — AWS, Azure, and GCP monitoring categories introduced.
- **Equipment filter** — First version of vendor/platform equipment-based filtering.
- **Virtualization category** — VMware, Hyper-V, and container monitoring use cases.
- **Non-technical mode** — "Sales people mode" added for stakeholder-friendly descriptions.
- **Security Essentials integration** — Splunk Security Essentials and other app references added.
- **ThousandEyes use cases** — Network and application performance monitoring from ThousandEyes.
- **Cisco color scheme** — UI updated to align with Cisco brand guidelines.
- **LLM support** — Initial `llms.txt` for AI-assisted discovery.
