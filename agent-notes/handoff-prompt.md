# Handoff Prompt — Splunk Monitoring Use Cases Gold Rewrite

**Last updated:** 2026-04-30 by agent session completing cat-18  
**Previous transcript:** `71c103e7-3973-4850-af08-327c912c2fa2`

---

## 1. What This Project Is

A repository of **7,337 Splunk monitoring use cases** (UCs) organized into 23 categories.  
Each UC is a JSON file (`content/cat-NN-*/UC-X.Y.Z.json`) with a companion `.md` sidecar.  
The goal is to rewrite every stub UC to **true-gold quality** — operationally useful, product-specific, implementable from the page alone.

**Repo root:** `/Users/fsudmann/Documents/GitHub/splunk-monitoring-use-cases`

---

## 2. Current Progress

| Status | Count |
|--------|-------|
| Verified (gold) | **959** |
| Stubs remaining | **6,378** |
| Completion | **13%** |

### Completed Categories (100%)
- `cat-18-data-center-fabric-sdn` — 76/76
- `cat-19-compute-infrastructure-hci-converged` — 93/93
- `cat-23-business-analytics` — 63/63

### Best Next Targets (fewest stubs remaining)
1. `cat-03-containers-orchestration` — **29 stubs** remaining (100/129, 78%)
2. `cat-13-observability-monitoring-stack` — 88 stubs (96/184, 52%)
3. `cat-20-cost-capacity-management` — 76 stubs (1/77, 1%)
4. `cat-15-data-center-physical-infrastructure` — 91 stubs (26/117, 22%)
5. `cat-12-devops-ci-cd` — 107 stubs (19/126, 15%)

---

## 3. Critical Warnings

1. **Do NOT touch NIS2 files** — regulatory compliance content has separate governance.
2. **Do NOT touch files from other agents' work** — only modify UCs you are actively rewriting.
3. **Do NOT commit build outputs** — `catalog.json`, `llms.txt`, `dist/` are generated artifacts.
4. **JSON is the source of truth** — `.md` files are always regenerated from JSON.
5. **One subagent per UC** — never have two agents writing the same file.

---

## 4. Quality Anchor

**UC-1.1.1** (`content/cat-01-server-compute/UC-1.1.1.json`) is the canonical quality exemplar.  
Read it before starting any wave to calibrate depth, voice, and structure.

---

## 5. The 16-Point Done-Criteria Checklist

Every UC must pass ALL 16 checks before marking `status: "verified"`:

| # | Check | Target |
|---|-------|--------|
| 1 | `detailedImplementation` length | 9,000–13,000 characters |
| 2 | `detailedImplementation` bold pairs (`**...**`) | 90–115 |
| 3 | `detailedImplementation` 5-step structure | Prerequisites, Step 1 (Configure data collection), Step 2 (Create the search), Step 3 (Validate), Step 4 (Operationalize), Step 5 (Operationalize & Troubleshoot) |
| 4 | `spl` length | 2,500–3,500 characters of real, product-specific SPL |
| 5 | `knownFalsePositives` length | 1,700–3,000 characters |
| 6 | `knownFalsePositives` tokens | 5–9 unique **`underscore_separated`** bold tokens at paragraph starts |
| 7 | `grandmaExplanation` length | 150–250 characters, plain language "We..." voice |
| 8 | `grandmaExplanation` sibling uniqueness | No 4-gram overlap with other verified UCs in same subcategory |
| 9 | `value` vs `description` | Must be genuinely distinct (not duplicated/rephrased) |
| 10 | `splunkPillar` | Typically "Observability" for infrastructure categories |
| 11 | `cimModels` | Real CIM model names (not "N/A") |
| 12 | `equipmentModels` | Must match regex `^[a-z0-9][a-z0-9_]*_[a-z0-9][a-z0-9_]*$` |
| 13 | Sourcetypes | 5 distinct sourcetypes across `dataSources` + `spl` |
| 14 | Step 5 content | Must contain visualization guidance AND alert design |
| 15 | Splunkbase app IDs | Only verified IDs: **4022**, **1546**, **7777**, **4856**, **1810** |
| 16 | References | Real URLs (vendor docs, Splunkbase) — no placeholder/fake links |

### Additional meta requirements:
- `status`: `"verified"`
- `lastReviewed`: today's date in `YYYY-MM-DD` format
- `reviewer`: `"agent-handcraft-YYYY-MM-DD"`
- Zero forbidden phrases: "ensure compliance", "proactive monitoring", "ensures compliance", "proactively monitor"
- `.md` sidecar must be regenerated after JSON edits
- `knownFalsePositives` tokens must not duplicate tokens from other verified siblings in same subcategory

---

## 6. Workflow Pattern

### Wave Processing (3 UCs per wave, from different subcategories)

```
1. IDENTIFY stubs
   python3 -c "import json,os,glob; [print(os.path.basename(fp).replace('.json',''),json.load(open(fp)).get('title','')) for fp in sorted(glob.glob('content/cat-XX-*/UC-*.json')) if json.load(open(fp)).get('status')!='verified']"

2. COLLECT sibling context (for uniqueness checks)
   - Read verified siblings' grandmaExplanation openers (first 6 words)
   - Read verified siblings' knownFalsePositives tokens

3. DISPATCH subagents (up to 3 in parallel, from different subcategories)
   - Each subagent gets: stub path, quality requirements, sibling uniqueness constraints, domain context
   - Each subagent must: read stub → rewrite all fields → write JSON → regenerate .md → self-verify

4. PARENT VERIFICATION (mandatory — never skip)
   Run programmatic 16-point check on each completed UC
   
5. FIX any failures via targeted subagent dispatch

6. UPDATE progress tracking
```

### .md Regeneration Command

**Retired 2026-05-18 (F21 close).** The per-UC `.md` companions under
`content/cat-*/UC-*.md` were deleted from git. The LLM-friendly
markdown twin is now emitted only at build time by
`tools/build/templates/uc.py::render_markdown_twin` into
`dist/uc/UC-X.Y.Z/uc.md`. Authors no longer need to regenerate any
`.md` companion after editing a JSON sidecar — `make build` (or a
single `python3 -m splunk_uc audit-doc-counts`-bearing CI run) covers
it. See [`docs/health-check-2026-progress.md`](../docs/health-check-2026-progress.md)
F21 row for the deletion rationale.

```bash
make build   # emits dist/uc/UC-X.Y.Z/uc.md for every sidecar
```

### Parent Verification Script (inline)
```python
python3 -c "
import json, re, os
ucid = 'UC-X.Y.Z'
fp = f'content/cat-XX-name/{ucid}.json'
with open(fp) as f:
    d = json.load(f)
di = d.get('detailedImplementation','')
bolds = len(re.findall(r'\*\*([^*]+)\*\*', di))
steps = all(s in di for s in ['Step 1','Step 2','Step 3','Step 4','Step 5'])
spl = d.get('spl','')
kfp = d.get('knownFalsePositives','')
kfp_t = re.findall(r'(?:^|\n)\s*[•\-]?\s*\*\*(\w+(?:_\w+)+)\*\*', kfp)
ge = d.get('grandmaExplanation','')
print(f'detImpl={len(di)} bolds={bolds} steps={steps}')
print(f'spl={len(spl)} kfp={len(kfp)} kfp_tokens={len(kfp_t)} ge={len(ge)}')
print(f'val!=desc={d.get(\"value\",\"\")!=d.get(\"description\",\"\")}')
print(f'pillar={d.get(\"splunkPillar\",\"\")} status={d.get(\"status\",\"\")}')
print(f'md={os.path.exists(fp.replace(\".json\",\".md\"))}')
"
```

### Known Regex Gotchas
- The **KFP token regex** `\*\*(\w+(?:_\w+)+)\*\*` catches ALL bold underscore terms in the text, not just paragraph-leading ones. Use the anchored version `(?:^|\n)\s*[•\-]?\s*\*\*(\w+(?:_\w+)+)\*\*` for accurate leading-token counts.
- The **sourcetype regex** varies by category. For Cisco/VMware use `((?:cisco|vmware|nxos|network|sdn):[a-z:_]+)`. Adjust prefixes per domain.

---

## 7. Subagent Prompt Template

```
You are rewriting a Splunk monitoring use case to "true-gold" quality.

## FILE
`content/cat-XX-name/UC-X.Y.Z.json`
Title: "..."

## QUALITY REQUIREMENTS
[paste the 16-point checklist targets]

## SIBLING UNIQUENESS (subcategory X.Y)
grandmaExplanation openers to avoid 4-gram clash: [list]
knownFalsePositives tokens already used: [list]

## DOMAIN CONTEXT
[product-specific APIs, MOs, CLIs, sourcetypes, key fields]

## STEPS
1. Read stub JSON
2. Rewrite ALL fields to true-gold quality
3. Write complete JSON back
4. *(Step removed 2026-05-18, F21 close: no in-tree `.md` companion
   to regenerate any more — the build emits it into `dist/`.)*
5. Run verification script
6. Return verification output
```

---

## 8. Anti-Patterns to Avoid

- **Bold overcount**: Subagents sometimes bold every technical term (200+ bolds). Target 90-115.
- **Short detailedImplementation**: After bold removal, length can drop below 9k. Always check both metrics together.
- **Duplicated description/value**: These must convey different information (what-it-detects vs business-impact).
- **Generic boilerplate**: "This dashboard provides comprehensive visibility..." — write operationally specific content instead.
- **Padding**: Repeating the same concept in different words to hit length targets.
- **"N/A" in cimModels**: Always use real CIM model names (Network_Traffic, Performance, Inventory, Change, Alerts, etc.)
- **Fake Splunkbase IDs**: Only use 4022, 1546, 7777, 4856, 1810.
- **Missing Step 5 viz/alert**: Step 5 must include dashboard panel layout AND alert configuration guidance.

---

## 9. Project File Structure

```
content/
  cat-01-server-compute/          # 281 UCs (UC-*.json + _category.json)
  cat-02-virtualization/           # 224 UCs
  ...
  cat-23-business-analytics/       # 63 UCs (complete)
schemas/
  uc.schema.json                   # JSON schema for UC files (validated at build time)
  uc-profile-gold.json             # Gold profile definition
scripts/
  generate_md_from_json.py         # RETIRED 2026-05-18 (F21 close); module
                                   #   src/splunk_uc/generators/md_from_json.py
                                   #   kept as a deprecation stub only.
  audit_gold_profile.py            # Gold quality auditor
  audit_gold_profile_v2.py         # V2 auditor
tools/
  build/
    build.py                       # Build orchestrator (the only build entry point)
    parse_content.py               # Reads content/**/*.json → Catalog object
    enrichment.py                  # Content enrichment (ESCU, equipment, pillar, regs)
    render_api.py                  # Generates API endpoints
    render_html.py                 # Generates HTML pages
    render_meta.py                 # Generates sitemap, llms.txt, feed.xml
```

**Build command:** `python3 tools/build/build.py --out dist`

The build validates all UC JSON files against `schemas/uc.schema.json` and
will abort on malformed JSON or schema violations.

---

## 10. Suggested First Actions for Next Agent

1. Read this handoff prompt in full
2. Read UC-1.1.1 as quality anchor: `content/cat-01-server-compute/UC-1.1.1.json`
3. Pick the next category to complete (recommended: `cat-03-containers-orchestration` with only 29 stubs)
4. Identify remaining stubs in that category
5. Begin wave processing: 3 UCs per wave, parent verification after each wave
6. Focus on quality over speed — the only metric that counts is the quality of the use cases
