# Gold-Standard Authoring Playbook

> **Purpose:** Codify the depth and rigour required to bring a regulatory-compliance use case (UC) to "implement from this page alone" quality, and provide a repeatable path to apply that bar to additional Tier-1 regulations (NIS2, DORA, GDPR, ISO 27001, NIST CSF, PCI DSS, HIPAA, etc.).
>
> **Audience:** Authors and reviewers of UC sidecars under `content/cat-22-regulatory-compliance/`. Also applicable to non-regulatory cat-22 categories where the author wants to lift quality to the same bar.

The playbook is opinionated. It is the contract enforced by
`python -m splunk_uc audit-gold-profile-v2`
(implementation: `src/splunk_uc/audits/gold_profile_v2.py`)
and the reference for SME and AI-agent authoring sessions.

---

## 1. Why a separate playbook for compliance UCs

`docs/gold-standard-template.md` documents the bar for all UCs (Bronze/Silver/Gold tiers, the 5-step `detailedImplementation`, anti-patterns, exemplar UC-5.13.1). That document is canon and overrides nothing here.

This playbook is an **overlay** that applies when the UC's purpose is regulatory evidence rather than purely operational monitoring. Compliance UCs differ in three ways that matter for authoring:

1. **Evidence is the deliverable.** The audit artefact (saved search, dashboard panel, archived export) IS the value, not a side-effect. The `evidence` and `evidenceArtifact` fields must name a tamper-evident place an auditor can see the artefact.
2. **Multiple authoritative sources.** Unlike "Linux CPU saturation" (one truth: `top`), an NIS2 obligation has the directive text, the implementing regulation, the ENISA technical guidance, and the national transposition. References must reflect that.
3. **Honest scope is non-negotiable.** Compliance UCs MUST state what they do not cover (legal interpretation, regulator filing, board approval) so reviewers don't read more into the claim than is supported. The `exclusions` field is mandatory and must be specific.

Everywhere else the existing gold-standard template applies in full.

---

## 2. The bar: what "comparable to UC-1.1.1" means

UC-1.1.1 (`content/cat-01-server-compute/UC-1.1.1.json`) is the catalogue exemplar for operational monitoring. UC-5.13.1 is the exemplar for product-integration monitoring. For compliance UCs, the bar is the union of both — operational depth plus regulatory rigour.

A UC meets the bar when **every** statement below is true:

### 2.1 Identity and metadata

- `id` follows `X.Y.Z`; `title` ≥30 characters and names both the obligation and the monitorable surface ("NIS2 Art.23 24-hour early-warning notification readiness", not "NIS2 incident reporting").
- `criticality`, `difficulty`, `wave` populated; `wave` is consistent with `prerequisiteUseCases` (a `crawl` UC depends on no other UCs).
- `owner` is one of the 11 enum values in `schemas/uc.schema.json`; matches who would actually be paged when this fails.
- `controlFamily` is set; matches the most specific of the 15 enum values rather than `regulation-specific`.
- `monitoringType` and `splunkPillar` are set; for compliance UCs always include `Compliance` and one of `Security`/`Audit`/`Governance`.
- `status` is `verified` only when an SME has signed off; otherwise `community` or `draft`.
- `lastReviewed` is within 12 months.

### 2.2 The two "what / why" sentences must be different

- `description` (≥80 chars) tells the reader **what is detected or measured**. It names the surface (e.g. "ES notables that breach the 24-hour acknowledgement deadline") and the rule (e.g. "high/critical urgency, status not Closed, _time older than 20 hours").
- `value` (≥80 chars) tells the reader **why it matters to the business**. It names the consequence of failure (e.g. "Missing the 24-hour clock loses the supervisory authority's good-faith presumption and triggers Annex II inquiry obligations under Art.32(4)").
- The Levenshtein distance between the two must be > 0.3. Copy-pasting one into the other fails review.

### 2.3 `dataSources` and `app` must be implementable

- `dataSources` (≥80 chars) names every index, sourcetype, lookup, and field the SPL depends on. Where the data comes from a TA, name the TA's modular input or scripted input by stanza, and list the key extracted fields.
- `app` (≥30 chars) names every TA / app that produces those events with **Splunkbase ID and minimum version** (e.g. "Splunk Add-on for Okta Identity Cloud (Splunkbase 6553) ≥3.0"). Premium apps (ES, ITSI, SOAR, UBA) go in `premiumApps[]`.

### 2.4 `spl` runs on real fields and produces real evidence

- The SPL targets the indexes, sourcetypes, and fields named in `dataSources`. No invented field names, no `myindex`, no `your_lookup_here`.
- The SPL produces a row-per-evidence-gap output with stable column names (typically `_time, owner, status, evidence_id, clause, affected_asset, hours_open` or domain-specific columns).
- Where a CIM data model is available, populate `cimSpl` with the `tstats summariesonly=true` variant and call out tradeoffs in `detailedImplementation` Step 2.

### 2.5 `knownFalsePositives` is specific and named

Generic phrases ("planned exercises", "approved exceptions") fail review. The bar is **at least 4 named scenarios**, each of which:
- Names a system or process ("KnowBe4 quarterly campaign rollover", "Veeam tape rotation maintenance window 03:00–05:00 Sunday", "ServiceNow GRC quarterly attestation push").
- States **how to distinguish** the false positive from a real finding ("correlate with `index=changes` for an active CHG record", "look for an entry in `nis2_exception_register.csv` with a non-expired `valid_until`").
- Names the **suppression mechanism** ("time-bound exception in `nis2_exception_register.csv`", "schedule alert outside the maintenance window via cron", "set `urgency=informational` on the rule for that source").

### 2.6 `detailedImplementation` is ≥1,500 characters AND has the five sections AND has product-specific depth

Length alone does not pass. The five sections must each be substantive:

1. **Prerequisites** — Splunkbase ID + minimum version; minimum Splunk version (Cloud / 9.x / 10.x); RBAC role; service-account scope/permissions; network access (egress destinations, ports, proxies); license headroom estimate; baseline operational knowledge expected.
2. **Configure data collection** — modular input stanza (or app config UI path), sourcetype assigned, default poll interval, expected event volume per entity, key extracted fields, where the CIM tagging lives, fallback to scripted input if the API isn't available.
3. **Create the search and alert** — full SPL fenced in `spl`; an "Understanding this SPL" walkthrough explaining each pipeline stage and the **rationale for thresholds** (why 24h, not 23h or 25h; why 80%, not 70% or 90%); cron schedule recommendation; alert action and throttle; the `cimSpl` variant if applicable, with a tradeoff sentence (DMA cost vs raw cost).
4. **Validate** — at least 3 specific validation checks: (a) compare to a vendor UI by name and screen path; (b) spot-check 2 known records against the source-of-truth field; (c) run a `timechart count` over 24h to find silent gaps; (d) confirm CIM tagging when applicable.
5. **Operationalize and Troubleshoot** — dashboard layout (rows, panel types, time pickers); access control; runbook integration with named owner; capacity-review cadence; **at least 6 specific failure modes** with cause and fix (e.g. "All `urgency` is `informational` → ES risk-based alerting is suppressing; check `index=risk` for the corresponding incident and confirm the correlation search urgency mapping in `Configure > Content Management`").

### 2.7 `references[]` ≥4 specific links

For NIS2 specifically:
- Splunkbase URL for each TA named in `app`
- The directive (`https://eur-lex.europa.eu/eli/dir/2022/2555/oj`)
- The implementing regulation where applicable (`https://eur-lex.europa.eu/eli/reg_impl/2024/2690/oj`)
- The ENISA technical implementation guidance
- A national transposition or competent-authority site when relevant
- Vendor documentation for the specific SPL surface (e.g. CIM Authentication docs, ES Notable framework docs)

### 2.8 `controlTest` describes a runnable test

- `positiveScenario` describes a fixture state where the UC fires, with named fields populated.
- `negativeScenario` describes a similar-looking state that should NOT fire (an active maintenance window, a closed notable, an approved exception).
- `fixtureRef` points to a `sample-data/uc-X.Y.Z-fixture.json` file under version control.
- `attackTechnique` names a MITRE ATT&CK technique where applicable.

### 2.9 Auditor-facing fields are populated

- `evidence`: names the saved search, dashboard panel, and archived export location.
- `evidenceArtifact` (per clause): the same, qualified by the specific clause.
- `evidenceSigning`: optional but recommended for production; specifies RFC 3161 TSA, sigstore, GPG, or none.
- `exclusions`: ≥40 chars; states what is NOT in scope (legal interpretation, regulator filing, board approval, counsel review).

### 2.10 `grandmaExplanation` is jargon-free, ≤400 chars, "we" voice

No `index=`, no SPL, no MITRE T-codes, no clause numbers, no `Splunkbase`, no acronyms. One to three sentences. Owned by `python -m splunk_uc generate-grandma-explanations` (impl. `src/splunk_uc/generators/grandma_explanations.py`); hand-edited only to polish.

---

## 3. The domain-pack pattern

Multiple UCs in the same regulation often share a data source. Without a shared pack of facts to draw from, authors invent slightly different `dataSources` strings, slightly different SPL, slightly different troubleshooting modes. Auditors read incoherence as risk.

The fix is the **domain pack**: a JSON record per data-source family at `data/{regulation}-domain-packs.json` (e.g. `data/nis2-domain-packs.json`) that pre-populates:

- `ta`: name, Splunkbase ID, minimum version, install scope (HF / SH / forwarder), license note
- `index`: canonical index name(s), sourcetype(s), expected event volume per entity, retention guidance
- `fields`: the field names the SPL depends on, with per-field origin (TA-extracted, CIM-mapped, lookup-derived)
- `cim`: CIM data models the data lands in (if any), DMA recommendation
- `validation`: vendor UI page to compare to, sample check queries
- `kfps`: list of named false positives with system, distinguish, and suppress fields
- `troubleshooting`: list of named failure modes with cause and fix
- `apps`: any premium apps (ES, ITSI, SOAR) typically required

When authoring a UC in that domain, the author pulls these facts from the pack and customises only what's specific to the obligation (the SPL filter, the threshold rationale, the runbook).

The pack is **reference material** — it is not auto-merged into UC sidecars. It exists so the catalogue is internally coherent (every Veeam-backed UC names "Veeam App for Splunk (Splunkbase 7312)", not three different spellings).

The pack is also testable:
`python -m splunk_uc audit-gold-profile-v2 --pack data/nis2-domain-packs.json`
checks each NIS2 UC's `dataSources`/`app` against the pack and warns on drift.

### 3.1 Domain-pack contents (NIS2 reference)

The NIS2 catalogue uses 12 packs (mapped in `data/nis2-domain-packs.json`):

| Pack | Family | Primary clause(s) covered |
|---|---|---|
| `es-notables` | Splunk ES correlation searches | Art.23, Art.21(2)(b) |
| `soar-cases` | Splunk SOAR cases / Phantom containers | Art.23(4), Art.21(2)(b) |
| `servicenow-grc` | ServiceNow GRC policies, risks, audits | Art.20, Art.21(2)(a) |
| `cmdb` | ServiceNow CMDB / asset registry | Art.2, Art.3, Art.26, Art.27 |
| `backup` | Veeam / Commvault / Rubrik / Cohesity / AWS Backup | Art.21(2)(c) |
| `idp` | Azure AD / Entra ID, Okta, ADFS, Microsoft 365 | Art.21(2)(i), Art.21(2)(j) |
| `pam` | CyberArk, BeyondTrust, Vault | Art.21(2)(i) |
| `vuln` | Tenable, Qualys, Rapid7, Defender Vulnerability | Art.21(2)(e), Art.21(2)(f) |
| `lms` | KnowBe4, Cornerstone, Workday Learning | Art.20, Art.21(2)(g) |
| `crypto` | Splunk Stream TLS, Venafi, HashiCorp Vault | Art.21(2)(h) |
| `dns` | Stream DNS, Cisco Umbrella, BIND, Windows DNS | Art.28, Art.29, Art.30 |
| `ot` | Cisco Cyber Vision, Nozomi, Claroty, Splunk Edge Hub | Art.21(2)(a) (OT scope) |

Each pack record is the source of truth for facts in that family. When authoring an Art.23 UC, draw from `es-notables` and `soar-cases`; the pack tells you the exact macro names, sourcetypes, fields, and KFPs to write into the UC.

---

## 4. The author workflow (per UC)

1. **Read the existing sidecar** under `content/cat-22-regulatory-compliance/UC-22.2.{n}.json`. Understand the clause(s) it claims, the owner, the control family.
2. **Identify the dominant domain pack** for the UC. Sometimes a UC spans two packs (e.g. UC-22.2.49 spans `es-notables` and `soar-cases`).
3. **Draft `description` and `value`** on paper before touching the file. Description: what is detected. Value: why the business cares. Force them apart — if they read similarly, redraft.
4. **Write `dataSources` and `app`** by pulling from the pack(s). Use the pack's exact wording for TA names, Splunkbase IDs, and indexes/sourcetypes.
5. **Write the SPL** to use the fields the pack lists. Add a domain-specific filter that maps to the obligation. Comment out any field that's not in the pack — that's an authoring red flag.
6. **Author the `detailedImplementation`** following the 5-section structure. Pull from the pack's `kfps` and `troubleshooting` lists for that section. Add UC-specific thresholds, runbooks, and rationale.
7. **Build `controlTest`** with a positive and negative narrative. Drop a `sample-data/uc-X.Y.Z-fixture.json` that exercises the positive case.
8. **Validate**:
   - `python3 scripts/audit_gold_profile.py --files content/cat-22-regulatory-compliance/UC-22.2.{n}.json`
   - `PYTHONPATH=src python3 -m splunk_uc audit-gold-profile-v2 --files content/cat-22-regulatory-compliance/UC-22.2.{n}.json`
   - `python3 scripts/audit_uc_structure.py --full`
9. **Regenerate** dependent artifacts:
   - `python3 scripts/generate_equipment_tags.py` (writes `equipment[]` / `equipmentModels[]` from your prose)
   - `PYTHONPATH=src python3 -m splunk_uc generate-grandma-explanations` if the field is empty
   - `PYTHONPATH=src python3 -m splunk_uc generate-md-from-json --files content/cat-22-regulatory-compliance/UC-22.2.{n}.json`
10. **Run the no-gap audit** to confirm the matrix is still complete:
    - `python3 scripts/audit_nis2_no_gap.py`

---

## 5. Applying the bar to other Tier-1 regulations

The methodology above is regulation-agnostic. To apply it to DORA, GDPR, ISO 27001, NIST CSF, PCI DSS, or HIPAA:

### 5.1 Phase 0 — Foundation (one-time per regulation)

| Step | Output | Owner |
|---|---|---|
| Survey the regulation's obligation taxonomy | A row-per-obligation matrix at `data/per-regulation/{reg}-coverage-expansion.json` | Author + Legal/Compliance SME |
| Build the domain packs | `data/{reg}-domain-packs.json` (use the NIS2 file as a template) | Author |
| Wire up the source map | `data/{reg}-source-map.json` (regulation-text URLs, supervisory-authority URLs, certified-translation URLs) | Author |
| Add the no-gap audit | `scripts/audit_{reg}_no_gap.py` (clone of `audit_nis2_no_gap.py`) | Author |
| Update the gold-profile-v2 audit's regulation registry to include `{reg}` so it runs in CI | One-line change to `src/splunk_uc/audits/gold_profile_v2.py` | Author |

### 5.2 Phase 1 — Anchor UC per domain pack

For each pack the regulation uses, author **one anchor UC** at full UC-1.1.1 depth. The anchor establishes the data source, the validation pattern, the KFP catalogue, and the troubleshooting matrix for that pack-in-this-regulation.

For NIS2 the anchors were UC-22.2.49 (es-notables anchor for Art.23), UC-22.2.17 (backup anchor for Art.21(2)(c)), UC-22.2.12 (idp anchor for Art.21(2)(j)), etc.

### 5.3 Phase 2 — Sibling UC uplift

For each non-anchor UC in the regulation, draw from the anchor's pattern. The sibling UC inherits the data source, TA, prerequisites, and validation steps; it customises the SPL filter, thresholds, KFPs, and runbook for the specific obligation.

### 5.4 Phase 3 — Audit and lock

Run `audit_gold_profile_v2.py` against every UC in the regulation. Any UC with depth_score < 80 fails CI. Re-author until the audit is green.

### 5.5 Phase 4 — Web surfaces

Confirm the regulation's compliance-story page (`compliance-story.html?reg={reg}`) renders the new depth correctly. The deep-coverage panel should list every domain pack and link to the anchor UCs.

---

## 6. Anti-patterns this playbook prevents

| Anti-pattern | Why it fails | Where to look in this playbook |
|---|---|---|
| `description` and `value` say the same thing | Two distinct audiences (auditor vs business sponsor) | §2.2 |
| `dataSources` is "ES notables" with no field list | Reader cannot run the SPL or know what to extract | §2.3 |
| SPL uses `${field_name_here}` style placeholders | Reader cannot verify it works | §2.4 |
| `knownFalsePositives` is "operational noise during maintenance windows" | No system named, no distinguish-from-real test, no suppression mechanism | §2.5 |
| `detailedImplementation` has 5 sections each one sentence long | Five paragraphs of padding, not depth | §2.6 |
| `references` only links the directive | No vendor docs, no Splunkbase, no transposition | §2.7 |
| `controlTest` says "the search returns the expected record" | Fixture not named; no negative scenario | §2.8 |
| Three different spellings of "Splunk Add-on for ServiceNow" across siblings | Catalogue incoherence reads as risk | §3 |
| Anchor UC and sibling UCs disagree on KFPs | Authors invented different KFP lists | §3, §5.2 |

---

## 7. Maintenance discipline

- The domain packs are versioned. Bumping a TA's minimum version (because Splunkbase released a new one) updates the pack first; sibling UC sidecars are then re-validated with `audit_gold_profile_v2.py --pack`.
- The regulation matrix is the source of truth for **what's covered**; the domain packs are the source of truth for **how it's covered**; the UC sidecars are the source of truth for **how a specific obligation is monitored**.
- When the regulation changes (new implementing act, new ENISA guidance, transposition deadline), update the matrix first, then re-derive whichever UCs are affected.
- Every UC's `lastReviewed` must be updated when the UC is materially changed. UCs older than 12 months are flagged by the audit.

---

## 8. Proven batch-uplift workflow (NIS2 reference)

The NIS2 regulation was the first to undergo a full gold-standard uplift of all 57 UCs. This section documents the exact sequence that was proven to work, so it can be replicated for DORA, GDPR, ISO 27001, and others.

### 8.1 Pre-flight

```bash
# 1. Confirm the audit baseline — how many UCs fail today?
PYTHONPATH=src python3 -m splunk_uc audit-gold-profile-v2 --regulation NIS2

# 2. Confirm the domain packs exist and are complete
python3 -c "import json; d=json.load(open('data/nis2-domain-packs.json')); print(len(d), 'packs')"

# 3. Group UCs by clause/data-source domain
#    This creates coherent batches where sibling UCs share TAs, fields, and KFPs.
#    For NIS2 the groups were:
#    A: Art.23 incident reporting (9 UCs)
#    B: Art.20 governance (5 UCs)
#    C: Art.21(2)(a-c) policies, IR, BC/DR (11 UCs)
#    D: Art.21(2)(d-f) supply chain, secure dev, cyber hygiene (8 UCs)
#    E: Art.21(2)(g-j) crypto, HR, IAM, secure comms (9 UCs)
#    F: Art.2/3/26/27 scope and registry (5 UCs)
#    G: Art.28-35 DNS, supervision, enforcement (5 UCs)
#    H: Cross-cutting (maturity, evidence integrity, certification) (5 UCs)
```

### 8.2 Batch processing

Each group is processed as a batch. Within a batch, UCs can be uplifted in parallel because they share the same domain pack and do not depend on each other. The key constraints per UC:

| Field | Constraint | Why |
|---|---|---|
| `compliance[]` | **Preserve exactly** — never rewrite clause, mode, assurance | Compliance mappings are authoritative and may have been reviewed |
| `id`, `$schema` | **Preserve** | Structural identity |
| `detailedImplementation` | ≥1,500 chars, 5 sections, ≥6 product-specific signals | Audit gate |
| `knownFalsePositives` | ≥4 named scenarios, each with distinguish + suppress | Audit gate |
| `dataSources` | ≥80 chars, Splunkbase IDs, field names | Audit gate |
| `app` | Splunkbase IDs | Audit gate |
| `description` / `value` | Distinct (Levenshtein >0.3) | Audit gate |
| `references` | ≥4 | Audit gate |
| `controlTest` | Distinct positive/negative scenarios | Audit gate |
| `evidence` / `exclusions` | ≥30 chars each | Audit gate |
| `evidenceSigning` | `rfc3161-tsa` (recommended) | Best practice |
| `grandmaExplanation` | Jargon-free, no SPL, no acronyms | Audit gate |

### 8.3 Validation loop

After each batch:

```bash
# 1. Gold-profile-v2 — the target standard (must be 100/100 for all NIS2 UCs)
PYTHONPATH=src python3 -m splunk_uc audit-gold-profile-v2 --regulation NIS2

# 2. No-gap — confirms every obligation is still covered
PYTHONPATH=src python3 -m splunk_uc audit-nis2-no-gap

# 3. Fix any failures, re-run until clean
```

After all batches:

```bash
# Full regeneration
python3 scripts/generate_evidence_packs.py
python3 scripts/generate_story_payload.py
python3 scripts/generate_api_surface.py

# Full audit sweep
python3 scripts/audit_compliance_mappings.py
python3 scripts/audit_compliance_gaps.py
python3 scripts/audit_uc_structure.py
python3 scripts/audit_catalog_schema.py
python3 scripts/audit_repo_consistency.py
python3 scripts/audit_non_technical_sync.py
python3 scripts/audit_placeholders.py
```

### 8.4 Final scorecard (NIS2 achieved)

| Audit | Result |
|---|---|
| Gold Profile v2 | 57/57 NIS2 UCs at 100/100 |
| NIS2 No-Gap | PASSED (149 rows, 115 NIS2 entries, 0 errors) |
| Compliance Mappings | 52/52 golden tuples passed |
| Compliance Gaps | 100% clause, 100% priority coverage (all tiers) |
| UC Structure | 0 issues |
| Catalog Schema | OK |
| Repo Consistency | 0 issues |
| Non-Technical Sync | 0 issues |
| Placeholders | 0 findings |

### 8.5 Lessons learned

1. **Group by data-source domain, not by article number.** Articles reference overlapping obligations; domain packs group by the data that enters Splunk. This keeps sibling UCs coherent.
2. **Preserve `compliance[]` arrays verbatim.** They are the regulatory mapping layer; rewriting them introduces golden-tuple failures and audit regressions.
3. **The v2 audit is the gate, not the legacy audit.** The legacy `audit_gold_profile.py` scores on different criteria (depth score, tier assignment). The v2 audit enforces the specific field-level requirements that make UCs implementable. Both can coexist; v2 is the mandatory gate.
4. **Domain packs prevent drift.** When 9 Art.23 UCs all name "Splunk Enterprise Security (Splunkbase 263)" with the same macro and field names, the catalogue reads as a coherent system, not a collection of independent drafts.
5. **KFP quality is the hardest requirement to meet.** Authors default to generic phrases. The "name a system, state how to distinguish, name the suppression mechanism" structure is non-negotiable and must be enforced by the audit.
6. **Regenerate API surface with elevated permissions.** The `generate_api_surface.py` script writes thousands of files and may require sandbox-free execution.

---

## 9. Regulation-specific quick-start checklist

Use this checklist when starting a new regulation uplift. Copy the table into a tracking issue or PR description.

| # | Step | Script / File | Done |
|---|---|---|---|
| 1 | Create obligation matrix | `data/per-regulation/{reg}-coverage-expansion.json` | [ ] |
| 2 | Create domain packs | `data/{reg}-domain-packs.json` | [ ] |
| 3 | Create source map | `data/{reg}-source-map.json` | [ ] |
| 4 | Add no-gap audit | `scripts/audit_{reg}_no_gap.py` | [ ] |
| 5 | Register regulation in v2 audit | One-line change to `audit_gold_profile_v2.py` | [ ] |
| 6 | Add golden tuples to `tests/golden/compliance-mappings.yaml` | At least 1 per anchor UC | [ ] |
| 7 | Author anchor UCs (1 per domain pack) | `content/cat-22-regulatory-compliance/UC-22.{sub}.{n}.json` | [ ] |
| 8 | Validate anchors pass v2 at 100/100 | `audit_gold_profile_v2.py --regulation {REG}` | [ ] |
| 9 | Author sibling UCs in batches | Grouped by domain pack | [ ] |
| 10 | Validate all UCs pass v2 at 100/100 | Same as step 8 | [ ] |
| 11 | Run no-gap audit | `audit_{reg}_no_gap.py` | [ ] |
| 12 | Regenerate all downstream artifacts | evidence packs, story payloads, API surface | [ ] |
| 13 | Run full audit sweep | compliance mappings, gaps, structure, schema, consistency | [ ] |
| 14 | Update `docs/compliance-coverage.md` with new regulation stats | Manual or script | [ ] |

---

## 10. Cross-references

- Bar definition: `docs/gold-standard-template.md`
- Profile schema: `schemas/uc-profile-gold.json`
- Legacy audit: `scripts/audit_gold_profile.py`
- Tightened audit: `python -m splunk_uc audit-gold-profile-v2`
  (implementation: `src/splunk_uc/audits/gold_profile_v2.py`)
- NIS2 domain packs: `data/nis2-domain-packs.json`
- NIS2 obligation matrix: `data/per-regulation/nis2-coverage-expansion.json`
- NIS2 source map: `data/nis2-source-map.json`
- NIS2 no-gap audit: `python -m splunk_uc audit-nis2-no-gap`
- NIS2 scorecard: §8.4 of this document
- Authoring rule: `.cursor/rules/gold-standard-authoring.mdc`
