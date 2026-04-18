# Quality Remediation Plan — v6.0 Catalog Cleanup

**Source:** [`reports/quality-review/2026-04-18.md`](../reports/quality-review/2026-04-18.md)
**Scope:** ~653 findings (190 HIGH / 303 MED / 160 LOW) across 6,424 UCs in 23 categories
**Authoring date:** 2026-04-18
**Target completion:** ~2 weeks (see per-phase estimates)

---

## Guiding principles

1. **Automate before editing.** Every defect pattern that's mechanically detectable gets a linter *first*. Linters pay dividends on every PR forever; hand-edits don't.
2. **Policy gates before mass transforms.** Several fixes (CIM SPL, ESCU-mirrors, Monitoring-type labels) require a one-line policy decision that changes the blast radius from "thousands of edits" to "hundreds". Don't do the edits until the policy is settled.
3. **HIGH severity first; let automation sweep MED/LOW.** Correctness bugs block users. Most polish/consistency nits are caught by the linters once in place, so the manual effort concentrates on HIGH.
4. **Don't delete surface area without explicit consent.** Consolidating the ~900 ESCU-mirror UCs in §10.6–§10.7 would be a meaningful drop in catalog coverage numbers. That decision belongs to the user.
5. **Protect via CI.** Every fix category becomes an audit rule; the rule ships to `validate.yml` before the fix PR merges. Prevents silent regression.
6. **Use the same 26-shard structure for fixing that we used for reviewing.** Parallel reviewer agents worked; parallel fixer agents will too.

---

## Phase 0 — Policy decisions (blocking; ~1 session with user)

These decisions gate Phase 2. Nothing downstream can ship without them. The user answers once; the rest of the plan executes to those answers.

### P0-Q1: CIM SPL companion sections
Current: ~150+ HIGH/MED findings where the optional `CIM SPL` block is a generic boilerplate `tstats` that doesn't reflect the primary search.
Options:
- **A. Drop.** Remove all optional CIM SPL sections. Keep `CIM Models` as metadata-only.
- **B. Enforce.** Every CIM SPL must query the same data-model object(s) declared in `CIM Models` AND approximate the primary search's aggregation. Add linter. Rewrite or remove the broken ones.
- **C. Tiered.** Keep for UCs whose primary data *is* CIM-normalized (Authentication, Web, Network_Traffic, Malware). Drop for everything else.

### P0-Q2: ESCU-mirror UCs in §10.6–§10.7 (~900 UCs)
Current: Body SPL is `| from datamodel=Risk.All_Risk …` while Data Sources name raw vendor feeds. Visualization is `Table, Timeline (from ESCU)`. Near-identical across hundreds of UCs.
Options:
- **A. Consolidate.** Replace with one canonical "ESCU analytic surface" UC + machine-generated link table. Shrinks catalog by ~900 UCs.
- **B. Enrich.** Keep individual UCs but add the actual ESCU correlation search (from the ESCU app) as the primary SPL, demote the Risk-aggregation pipe to a reference panel.
- **C. Mark as pointers.** Keep count but reformat — each becomes a one-line pointer ("This UC is materialized by Splunk ESCU analytic `<search_name>`; see ESCU app for SPL."). No SPL block. Easy to automate.

### P0-Q3: Known-FP policy
Current: Required field per rubric but ~60% of UCs have it empty (`|`), missing, or copy-pasted boilerplate.
Options:
- **A. Require for all UCs.** Mechanical check: non-empty, >20 chars, not one of N known boilerplate strings.
- **B. Require only for designated noisy categories** (cat-9 IAM, cat-10 Security, cat-11 Email, cat-14 IoT/OT, cat-17 ZT, cat-22 Regulatory).
- **C. Promote to required and deprecate boilerplate.** Categories A+B; add regex list of forbidden phrases.

### P0-Q4: Monitoring-type label policy
Current: UCs about access control, policy violations, geofencing, session anomalies are tagged `Performance`. Semantically wrong.
Proposal: `Performance` is reserved for load/latency/throughput/availability. Security or access UCs use `Security`/`Compliance`/`Configuration`/`Audit` etc.
Options:
- **A. Per-category allowed-list.** Each category declares which monitoring types are valid; linter enforces.
- **B. Global allowed-list + semantic tagger.** Global list; for each UC, compare title/keywords to declared type and flag mismatches.

### P0-Q5: Index/sourcetype naming conventions
Current: Same vendor/product uses multiple index names within a single file (`cisco_aci` vs `aci`; `k8s` vs `containers`; `hci` vs `nutanix`; `finops` vs `cloud_cost`).
Options:
- **A. Freeze canonical name per vendor.** Publish a table; linter flags deviations; run one mass replace.
- **B. Accept multi-index via config map.** If both names are defensible (one is Enterprise, one is Cloud), keep both but require the index be declared in the UC's `Data Sources`. Linter still checks that SPL `index=` matches declaration.

### P0-Q6: SOX duplication (cat-22 §22.12)
Current: Two blocks — 22.12.1–35 (COSO-tagged) and 22.12.36–40 (Phase 2.3 append with broader tags).
Options:
- **A. Merge** into single coherent run; renumber; drop editorial scaffolding header.
- **B. Keep split** but relabel: rename the later block to a dedicated subcategory number (e.g., 22.12.x→22.51.x) with a clear theme.

### P0-Q7: Near-duplicate vendor UCs (Okta/Duo, EDR vendors, SIEM vendors, SWG vendors)
Current: Same detection pattern repeated for 3–5 vendors with only metadata differing.
Options:
- **A. Consolidate to generic UC + vendor-specific sidebar.** Fewer UCs, still searchable by vendor.
- **B. Keep each but make vendor-specific.** Require each vendor UC to highlight that vendor's *unique* detection primitive (Okta's `behavior.risk`, Duo's `access_device.is_encrypted`, etc.). Linter detects near-identity via SPL hash.
- **C. Keep each, no requirement.** Accept duplication as catalog breadth. (Not recommended.)

### Estimated time
1 session (30–60 min) to collect decisions. Until done, Phases 1–2 can start on the parts that don't depend on Q1–Q7.

---

## Phase 1 — Linters & audit scripts (high leverage; ~2 days, independent of Phase 0)

Each linter ships to `scripts/audit_*.py` with a `--check` mode for CI and a `--report` mode for human review. Each gets wired into `validate.yml`.

### P1-L1: SPL grammar linter — `audit_spl_grammar.py`
Detects:
- `stats … span=` (invalid; belongs on `bin`/`timechart`)
- `| mstats` without `index=` constraint
- `case("…*…", …)` where `*` is being treated as literal
- Field references in `where`/`eval` after `timechart` that don't exist in the timechart output
- `join` without time-bounded subsearch
- Multiple `index=` searches glued with `| comment`
- Leading `|` in SPL code fences (not runnable standalone)
- `streamstats current=` and similar invalid flags
- `timechart` followed by `stats` on non-`_time` fields (loses binning)

**Eliminates:** ~40 HIGH, ~30 MED findings across cat-02, 03, 04, 06, 07, 08, 13, 15, 17, 18, 20.

### P1-L2: CIM SPL consistency linter — `audit_cim_spl_alignment.py`
Only runs if P0-Q1 = "B" or "C":
- Parses declared `CIM Models:` (comma list).
- Parses `CIM SPL` code fence; extracts `datamodel=X` references.
- Fails if `X` isn't in the declared list.
- Warns if `CIM SPL` aggregates `count` or `sum(bytes)` only on obviously unrelated UCs (title keyword vs object mismatch — e.g., FIM UC using `Endpoint.Processes`).
- Optionally fails if CIM SPL is byte-identical across >N UCs (boilerplate detection).

**Eliminates:** ~150+ HIGH/MED findings (the single largest bucket).

### P1-L3: Index/sourcetype drift linter — `audit_index_naming.py`
Only runs if P0-Q5 = "A" or "B":
- Canonical table in `config/canonical_indexes.yaml` — one entry per vendor/product.
- Scans every UC's SPL for `index=X sourcetype=Y` and flags deviations from canonical.
- For multi-accepted case (P0-Q5-B), cross-checks declaration against Data Sources field.

**Eliminates:** ~20 MED, ~15 LOW findings across cat-03, 04, 16, 17, 18, 19, 20.

### P1-L4: Monitoring-type policy linter — `audit_monitoring_type.py`
Only runs if P0-Q4 is decided:
- `config/monitoring_types.yaml` — canonical types + per-category allowed-list.
- Keyword-to-type heuristic for obvious mismatches (e.g., "geofencing", "break-glass", "password policy" → NOT Performance).
- Emits downgrade suggestions; `--fix` applies them.

**Eliminates:** ~15 HIGH findings across cat-9, 15.

### P1-L5: Known-FP required-field linter — `audit_known_fp.py`
Only runs once P0-Q3 is decided:
- Required for listed categories.
- Rejects: empty, `|`, `None identified` (when FP is otherwise plausible), boilerplate "Administrative tasks, scheduled jobs, platform updates".
- Configurable `config/known_fp_boilerplate_deny.txt`.

**Eliminates:** ~60 MED findings across cat-9, 10, 11, 14, 17, 22.

### P1-L6: Placeholder detector — `audit_placeholders.py`
Detects:
- `TBD`, `FIXME`, `TODO`, `example.com`, `XXX`, `xxx.xxx`, `"…"` truncation markers
- Empty code fences (```...```)
- `makeresults | eval ...` as the only SPL (instructional stub)
- Literal `...` placeholders inside SPL
- Editorial scaffolding headers (`### Phase 2.3`, `### per-regulation content fill`)

**Eliminates:** ~15 LOW findings.

### P1-L7: MITRE ATT&CK taxonomy linter — `audit_mitre_taxonomy.py`
- Parses ATT&CK-adjacent fields (wherever declared).
- Rejects CVE-IDs listed as technique IDs (e.g., `CVE-2025-33073`).
- Validates technique IDs against a vendored ATT&CK STIX bundle or an allowed pattern (`T\d{4}(\.\d{3})?`).
- Warns when the referenced technique isn't plausibly detected by the primary SPL (keyword heuristic).

**Eliminates:** ~20 HIGH findings in cat-10 §10.6.

### P1-L8: Near-duplicate SPL detector — `audit_spl_duplicates.py`
- Normalizes SPL (lowercase, collapse whitespace, strip index/sourcetype literals).
- Hashes the normalized body.
- Reports hash-groups with ≥N members; `--fix` emits a dedupe candidate list.

**Informs:** P0-Q7 decision + drives Phase 2 consolidation.

### P1-L9: Threshold-vs-Implementation consistency — `audit_threshold_coherence.py`
- Parses Implementation prose for "N-minute window", "X% threshold", "M-sigma".
- Parses SPL for `bin span=…`, numeric comparison constants.
- Flags mismatches (prose says 15m, SPL has no `bin`/`span`).

**Eliminates:** ~30 MED findings across cat-1, 4, 5, 8, 9, 10, 14.

### P1-L10: Visualization linter — `audit_visualization_detail.py`
- Rejects bare chart-type lists ("Table, Bar chart, Line chart.").
- Requires either axes, split-by fields, or panel-specific language.
- Can be opt-in with `--severity=warn` initially.

**Eliminates:** ~30 LOW findings.

### CI wiring
Once each linter is green against the existing catalog (i.e., any findings it surfaces are fixed *in the same PR* that adds it), it joins `validate.yml`. New UCs can never regress old patterns.

---

## Phase 2 — Policy-driven mass transforms (~1 day; after P0 decisions)

Each transform is a single script run that emits a diff for human review, then lands as one PR.

### P2-T1: CIM SPL transform (depends on P0-Q1)
- If **A (drop)**: script removes `- **CIM SPL:**` blocks. Keeps `CIM Models`. ~2,000 blocks affected.
- If **B (enforce)**: script flags every CIM SPL block, routes to Phase 3 agents for rewrite.
- If **C (tiered)**: script drops from non-CIM UCs, flags the rest for Phase 3.

### P2-T2: ESCU-mirror transform (depends on P0-Q2)
- If **A (consolidate)**: script generates a single canonical UC (UC-10.6.CANON) + a link-table lookup; deletes the ~900 wrapper UCs; renumbers the rest of §10.6/§10.7.
- If **B (enrich)**: script leaves the structure but marks each for Phase 3 (agent must pull actual correlation search from ESCU repo).
- If **C (pointers)**: script replaces each wrapper's SPL block with a one-line pointer referencing the ESCU analytic name.

### P2-T3: Index naming normalization (depends on P0-Q5)
- Mass sed-like replace using the canonical table.
- Skip list for UCs where ambiguity is intentional.

### P2-T4: Monitoring-type normalization (depends on P0-Q4)
- Apply P1-L4 `--fix`.

### P2-T5: SOX block restructure (depends on P0-Q6)
- Merge or relabel the §22.12.36–40 block.
- Remove editorial `Phase 2.3` headings.

### P2-T6: Near-duplicate consolidation (depends on P0-Q7)
- Apply decision: consolidate, differentiate, or accept.

### Outputs
- One PR per transform (so reverting one doesn't block others).
- Each PR includes the regenerated `catalog.json`, `non-technical-view.js`, release notes entry, `VERSION` bump (patch or minor per rule set).

---

## Phase 3 — Per-shard semantic fixes (~3–5 days; parallel agents)

Reuse the 26-shard structure. Each agent gets:
1. Its shard's findings list (extracted from the review report)
2. The Phase 2 outcome (so it knows what's already been auto-fixed)
3. Permission to edit the markdown file (unlike reviewer agents, these are write-capable)
4. A validation loop: after each UC fix, re-run the relevant linter locally; only commit changes whose linter passes

### Fix discipline per UC
- **HIGH severity always fixed.** If the agent can't construct a correct SPL, the UC's SPL is replaced with an `<!-- FIX_ME: original SPL removed due to correctness issue — see findings -->` block and Known-FP is updated. Better a blank than a wrong detection.
- **MED severity fixed if trivial.** Else left with a source-linked TODO so future maintenance can pick it up.
- **LOW severity left alone.** Linters enforce these going forward; no backfill needed unless trivial.

### Parallelization strategy
- Run 5–8 agents concurrently (not all 26) so diffs are reviewable.
- Each wave: 1.5h agent wall time + 30m human review before the next wave.
- Total: ~4 waves × 2h ≈ 8h + inter-wave review ≈ 1.5 days.

### Agents receive a structured finding file
Example per-agent finding format (generated from `reports/quality-review/2026-04-18.md`):
```yaml
shard: cat-02-virtualization.md
findings:
  - uc: UC-2.1.8
    severity: HIGH
    pattern: spl-grammar
    issue: "DRS query uses `where count > N` after `timechart` where `count` isn't produced"
    hint: "Replace with `| where <split_by_field> > N` after stats"
  - uc: UC-2.3.16
    severity: HIGH
    pattern: spl-grammar
    issue: "`stats ... span=5m` is invalid syntax"
    hint: "Use `bin _time span=5m | stats ... by _time` or `timechart span=5m`"
  ...
```

### Quality gates per wave
- `pytest tests/` green
- All Phase 1 linters green on the touched files
- `python scripts/audit_uc_structure.py` green
- `python scripts/audit_uc_ids.py` green (no ID drift)
- `python scripts/audit_compliance_mappings.py` green if shard is cat-22

---

## Phase 4 — CI hardening & contributor docs (~1 day; parallel to Phase 3)

### P4-D1: Wire new linters into `validate.yml`
- Add each linter as a step (ordered so cheap ones run first).
- Fail the workflow on HIGH; warn-only on LOW at first (tune later).

### P4-D2: Update CONTRIBUTING
- Document the 14-point rubric (lifted from `plan/quality-remediation-2026-04-18.md` §Methodology).
- Show the lint commands contributors can run locally.
- Add a "new UC checklist" PR template.

### P4-D3: Regenerate manifests after Phase 2/3
- `catalog.json`
- `non-technical-view.js` (per the workspace rule)
- `CHANGELOG.md`, `index.html` release notes, `VERSION` bump
- API surface (`api/v1/index.json`, JSON-LD, OpenAPI)
- Search indexes if any

### P4-D4: Version decision
Before landing, **ask user** for the version bump:
- Patch (`6.0.0 → 6.0.1`) if fixes only
- Minor (`6.0.0 → 6.1.0`) if we consolidate ESCU-mirrors (meaningful content shift)
- Minor if CIM SPL mass-dropped (noticeable catalog change)

---

## Phase 5 — Re-review (~1 day)

Re-run the same 26-agent sweep against the updated catalog.

- Deliverable: `reports/quality-review/<DATE>.md` (v2).
- Success criteria: **zero HIGH** remaining; MED count reduced ≥70%; LOW count reduced ≥50%.
- If HIGH > 0, loop into a targeted Phase 3-b with the remaining findings.

---

## Dependency graph

```
P0 (policy) ───────────────────┐
                               ├──► P2 (mass transforms) ──┐
P1 (linters) ──► CI initial ───┘                           │
      │                                                    ├──► P3 (shard fixes) ──► P4 (CI hardening, manifests) ──► P5 (re-review)
      └───────────────────────────────────────────────────►│
                                                           │
                                       (P3 agents consume P1 linter output + P2 diff)
```

P1 is the critical-path unblocker — starting it immediately is high-leverage even before P0 decisions are back.

---

## Time & effort estimate

| Phase | Duration | Parallelizable | Gating factor |
|---|---|---|---|
| P0 Policy | 1 session | N/A | user availability |
| P1 Linters | 2 days | Yes (10 linters across 2–3 agents) | none |
| P2 Mass transforms | 1 day | Partially (per-transform PR) | P0 complete, P1 linters green |
| P3 Shard fixes | 2–3 days | Yes (5–8 agents / wave) | P1 + P2 |
| P4 CI + manifests | 1 day | Partially | P3 complete |
| P5 Re-review | 1 day | Yes (26 agents) | P4 complete |
| **Total** | **7–9 working days** | | |

With aggressive parallelization and quick P0 turnaround, this finishes in a ~1.5-week sprint. Conservative estimate: 2 weeks.

---

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Linter false positives create friction | Every linter starts `--severity=warn`; graduate to fail only after one clean catalog run |
| ESCU-mirror consolidation drops perceived catalog breadth | Keep the pointer list + make it searchable in the UI; count each pointer as a UC in catalog.json metadata |
| Mass `index=` replace breaks a rare legitimate override | Skip-list file; dry-run diff reviewed before landing |
| Shard agents introduce new SPL bugs | Linters gate every commit; CI blocks regression |
| CI runtime blows up from 10 new linters | Profile; batch cheap ones; run heavy ones in a nightly job if needed |
| Version mismatch between VERSION/CHANGELOG/index.html | Existing validate.yml already enforces; no change needed |

---

## Deliverables

1. **`scripts/audit_spl_grammar.py`** + 9 other linters (Phase 1)
2. **`config/canonical_indexes.yaml`**, **`config/monitoring_types.yaml`**, **`config/known_fp_boilerplate_deny.txt`** (Phase 1)
3. **Individual Phase-2 transform PRs** (one per P2-T*)
4. **Phase-3 shard-fix PRs** (grouped by wave, ≤8 shards each)
5. **Updated `validate.yml`** with linter steps
6. **`CONTRIBUTING.md`** rubric + PR template
7. **`reports/quality-review/<POST_FIX_DATE>.md`** re-review
8. **`CHANGELOG.md`** + `index.html` release notes + `VERSION` bump

---

## What we need from the user now

Answers to **P0-Q1 through P0-Q7**. Everything else can start in parallel.

The linter work (P1) is safe to kick off immediately — it's purely additive and doesn't change any use case content. P1 effort is not wasted regardless of how P0 resolves.
