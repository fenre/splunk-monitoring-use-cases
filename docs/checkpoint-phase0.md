# Phase 0 checkpoint (cp0) — sign-off package

> **Status:** Phase 0 complete, 2026-04-16. Awaiting explicit sign-off
> before Phase 1.1 schema work begins.
> **Audience:** project owner. This document exists so the owner can
> approve Phase 0's exit, and decide the open questions in §5, in a
> single sitting.
> **What Phase 0 is.** A de-risking phase. No public-facing content
> changed; the existing catalogue is untouched. All Phase 0 outputs are
> research artefacts, inventories and reproducible proof scripts.

---

## 1. Phase 0 scope recap

Phase 0 had three sub-phases, each intentionally gated by explicit
deliverables:

| Sub-phase | Goal | Output | Status |
|---|---|---|---|
| 0.1 Auditor discovery | Build the research apparatus to get auditor requirements into Phase 1 with primary-source rigour. | `docs/auditor-research/*` (guide + survey + recruitment + findings template) | **READY**, fieldwork not yet conducted |
| 0.2 Content inventory & gap analysis | Know exactly what regulatory surface the existing catalogue has and what it is missing. | `scripts/inventory_ucs.py`, `data/inventory/*`, `data/regulations.draft.json`, `docs/content-gap-analysis.md` | **COMPLETE** |
| 0.5 Feasibility spikes | Prove the tooling works before Phase 1 invests in schema + content. | `scripts/feasibility/*`, `vendor/*`, `data/crosswalks/*`, `docs/feasibility-spike-results.md` | **COMPLETE, all PASS** |

Why there is no 0.3 / 0.4 in this report: those were Phase 0 subtasks
(regulatory coverage and architecture-review rehearsal) that merged
into 0.1 and 0.2 during scoping. The tracked IDs in `docs/plan/` reflect
the consolidated set.

---

## 2. Auditor research artefacts (0.1 summary)

Phase 0.1 produces the **instrument** for the research, not the
findings. Fieldwork (the interviews and survey) is scheduled for
Phase 1.0 and feeds Phase 1.1 schema decisions.

| Artefact | Path | Length | Purpose |
|---|---|---:|---|
| Interview guide | `docs/auditor-research/interview-guide.md` | 174 lines | 45-minute structured interview with QSA / DPO / SOC-2 / ISO / SOX variants; covers consent, evidence-pack realities, clause-level vocabulary tests. |
| Survey | `docs/auditor-research/survey.md` | 208 lines | Anonymous, scale-gathering survey on evidence-pack preferences (structure, signing, vocabulary). |
| Recruitment plan | `docs/auditor-research/recruitment.md` | 215 lines | Ethical outreach messaging for Splunk Trust, LinkedIn, IAPP, AICPA, ISO, partner consultancies. |
| Findings template | `docs/auditor-research/findings-template.md` | 193 lines | Empty aggregation template (no individual traceability) for `findings.md` once fieldwork completes. |

**Methodological notes locked in at this stage:**
* Consent and anonymisation language is in `interview-guide.md` §1.1
  and applies to every respondent equally.
* Aggregation occurs before publication; raw audio is deleted after
  synthesis.
* Target sample: **≥ 12 interviews** spread across 3 framework clusters
  (financial/SOX + PCI, privacy/GDPR + HIPAA, public-sector/NIS2 + DORA)
  plus **≥ 40 survey responses**. Explicit stop-criterion: saturation
  on the evidence-pack-structure question (§4.2 of the survey).

**Why it matters for the gold-standard claim.** The plan calls the
catalogue the "international gold standard" for compliance logging.
Gold standards are defined by their auditors, not their authors. The
Phase 0.1 artefacts are the only mechanism in the whole plan that
collects primary-source auditor requirements. Skipping them means
Phase 1's vocabulary (`assurance`, `mode`, evidence-pack shape) is
author-guessed rather than auditor-validated. The four documents
above are the minimum apparatus to prevent that failure mode.

---

## 3. Content inventory and gap summary (0.2 summary)

Full report: `docs/content-gap-analysis.md`.
Regeneration: `python3 scripts/inventory_ucs.py --stats && python3 scripts/gap_analysis.py`.

### 3.1 Headline numbers

| Metric | Value |
|---|---:|
| Total use cases in the catalogue | **6 304** |
| UCs carrying a `Regulations:` tag | **1 162** (18.4 %) |
| Distinct regulation labels in those tags | **70** |
| Tier-1 frameworks recognised by the draft index | **10** |
| Tier-2 labels not yet in the index | **60** |
| UCs mapping to ≥ 1 tier-1 framework | **510** |
| UCs whose tag does NOT resolve to tier-1 | **652** |

### 3.2 The three structural findings

1. **One-to-one framework → subcategory lock-in.** Every tier-1 framework
   is owned by exactly one cat-22 subcategory; there is no
   cross-category reuse, even when identical detections already exist
   in cat-09 (identity), cat-10 (security infra), cat-12 (DevOps). Phase 1
   must either lift the regulatory mapping into a transversal layer or
   duplicate tags across existing categories. Conservative estimate:
   ~800 non-regulatory UCs are one `compliance[]` block away from
   **doubling** the catalogue's regulatory surface.
2. **Shallow clause surface.** The tier-1 index currently exposes 11–19
   clauses per framework (auditor-reachable subset). Phase 1.3 must
   ingest the full NIST OLIR / OSCAL clause graph so UCs can claim
   precise, version-stamped clauses rather than framework-level tags.
3. **Flat assurance language.** Today's `Regulations:` bullet is a
   single free-text string; the Phase 1 JSON sidecar requires a
   structured `{clauseUrl, assurance, mode, controlTest}` claim per
   clause. Nothing in today's markdown content is recoverable for the
   new schema without re-authoring.

### 3.3 Tier-2 promotion candidates

20 labels are both real (≥ 15 UCs tagged) and have authoritative
public sources: NERC CIP, IEC 62443, API RP 1164, NIS2/DORA variants,
CCPA/CPRA, PSD2, FedRAMP, FDA 21 CFR Part 11, CMMC 2.0, SWIFT CSP,
APRA CPS 234, EU AI Act, EU CRA, eIDAS 2.0, and six more. All are
scheduled for promotion in Phase 1.3.

### 3.4 Quality caveat

The inventory relies on `scripts/inventory_ucs.py` parsing `### UC-`
headers and `Regulations:` bullets. Tags that use alternative
phrasings ("Relevant regulations:", "Compliance:") are not captured;
`gap_analysis.py` normalises known aliases but only for the tier-1
set. Phase 1.2 must reconcile every UC sidecar against the primary
source once it is in JSON, so any miscount in this snapshot is
corrected by construction in Phase 1.

---

## 4. Feasibility results (0.5 summary)

Full report: `docs/feasibility-spike-results.md`.

| Spike | Validates | Result |
|---|---|---|
| 0.5a OLIR / OSCAL ingest | NIST CSF v2 + 800-53 r5 catalogues are consumable | **PASS** — 219 CSF + 1 196 800-53 controls normalised; inline links preserved where present. |
| 0.5b OSCAL generation + validation | `UC sidecar → Component Definition → schema-valid` | **PASS** (via Node + Ajv) |
| 0.5c UC authoring ergonomics | `schemas/uc.schema.json` validates the exemplar | **PASS** |
| 0.5d Splunk-app POC | UC sidecar → AppInspect-shaped Splunk app | **PASS** (shape-check; AppInspect execution is Phase 1.) |

**One decision was forced by 0.5b.** We went through three validator
candidates before landing on Node + Ajv:

* Python `jsonschema` 4.26.0 — **fail**; the NIST OSCAL schema uses
  ECMA-262 Unicode property escapes (`\p{L}`, `\p{N}`) in `pattern`
  regexes, which Python's `re` module does not support.
* `jsonschema-rs` (Rust) — **fail**; handles the regex, but cannot
  resolve NIST's anchor-style `$ref: "#id"` definitions.
* **Node + Ajv** — **pass**; handles both. Industry standard for OSCAL
  in JavaScript tooling, aligned with NIST's own tooling.

The decision is baked into `package.json` (`ajv` + `ajv-formats` as
`devDependencies`) and `scripts/feasibility/oscal_validate.mjs`.

**Deterministic hashing fix applied during the spike.** The generator
previously reported a SHA-256 of an in-memory serialisation that did
not match `shasum -a 256 <file>`. This is now fixed — the reported
hash equals the on-disk hash — which matters for Phase 2 evidence
signing.

**Exit state of all four spikes.** Reproducible with four commands
from a clean clone; no external network calls during validation; all
schemas, catalogues and test data are vendored under
`vendor/oscal/`, `vendor/olir/`, `vendor/cprt/`.

---

## 5. Decisions requested (owner sign-off)

These are the questions Phase 1 cannot start on without an answer.
Each decision has a recommendation and alternatives; I need the owner
to pick one per row, or explicitly defer.

### 5.1 Validator for OSCAL

* **Recommendation:** Node + Ajv (proven in 0.5b).
* **Alternative:** Python + `jsonschema-rs` — rejected because of the
  `$ref` resolution bug on NIST schemas.
* **Decision needed:** ✅ confirm Node + Ajv is acceptable as a repo-
  level tooling dependency (i.e., `package-lock.json` tracked in git,
  CI needs a Node runtime). If the owner prefers zero-Node, the only
  alternative is to wait for a different Python validator or write our
  own.

### 5.2 Scope of auditor fieldwork before Phase 1.1

* **Recommendation:** block Phase 1.1 (schema lock) until at least 8
  of 12 target interviews are complete. The schema's `assurance` and
  `mode` enums otherwise remain author-guessed.
* **Alternative:** proceed with Phase 1.1 using the draft enums
  (`satisfies / detects-violation-of`, `full / partial / contributing`)
  and treat auditor feedback as a Phase 1.5 revision.
* **Decision needed:** ✅ wait-for-interviews vs. ✅ ship-draft-and-iterate.

### 5.3 Content authoring strategy for the 1 162 regulatory UCs

* **Recommendation:** Phase 1.2 re-authors all 1 162 UCs into JSON
  sidecars, populating clause mappings from `data/regulations.json`
  (the locked-in version of `data/regulations.draft.json`). This is
  large (~40 engineer-days) but is the only path to clause-level
  precision.
* **Alternative:** partial migration (e.g., only the 510 tier-1 UCs);
  markdown remains canonical for tier-2 and non-regulatory UCs.
* **Decision needed:** pick full, partial, or phased (e.g., tier-1
  first, tier-2 in Phase 1.5).

### 5.4 Cross-category reuse ("structural finding #1")

* **Recommendation:** Phase 1.4 attaches `compliance[]` sidecars to
  ~800 existing non-regulatory UCs (cat-09, -10, -12, -04, -07). This
  roughly doubles the regulatory surface without writing any new
  detections.
* **Alternative:** keep the cat-22 subcategory lock-in; all regulatory
  content lives under cat-22 and duplicates detection logic.
* **Decision needed:** lift-into-transversal-layer vs. duplicate-in-cat-22.

### 5.5 Empty-`Regulations:` UCs in cat-22 (0.2 §6)

* **Recommendation:** Move `UC-22.9.1`..`UC-22.9.5` out of the
  `compliance[]` schema and into a new `posture-measurement` control
  family. They measure the programme, not the detections.
* **Alternative:** Keep them in cat-22 with a `meta-kpi` tag on the
  existing `compliance[]` block.
* **Decision needed:** move or tag.

### 5.6 AppInspect execution

* **Recommendation:** defer actual AppInspect execution to Phase 2.
  Phase 1 produces an AppInspect-shaped tree (0.5d proven) and
  documents the verification commands; the first paid Splunk Cloud
  vetting run happens when the content is complete.
* **Alternative:** pay for a Splunk dev account now and run AppInspect
  on every commit in CI.
* **Decision needed:** defer vs. pay-now.

### 5.7 OSCAL component definition scope

* **Recommendation:** Phase 1.1 emits one OSCAL Component Definition
  per UC. This scales well and lines up with NIST's
  "component-level assertion" model.
* **Alternative:** one Component Definition per framework, with each
  UC contributing `implemented-requirements`. More compact but harder
  to diff when a single UC changes.
* **Decision needed:** per-UC vs. per-framework.

### 5.8 Signing / timestamping for evidence

* **Recommendation:** add `evidence.signing` (RFC 3161 TSA or Sigstore)
  to the schema in Phase 1.1 as an optional block; enforce for
  production evidence packs in Phase 2.
* **Alternative:** no cryptographic provenance in v1; rely on git
  SHA alone.
* **Decision needed:** TSA, Sigstore, or defer.

---

## 6. Exit criteria (meet every one before Phase 1.1 begins)

* [x] All four feasibility scripts exist and PASS from a clean clone.
* [x] `docs/content-gap-analysis.md` published with reproducible
  `data/inventory/*.json` inputs.
* [x] `docs/feasibility-spike-results.md` consolidates the four spikes
  and records validator-choice rationale.
* [x] `docs/auditor-research/` contains the full instrument (guide,
  survey, recruitment, findings template).
* [x] `package.json` and `package-lock.json` tracked in git; `build/poc/`
  gitignored.
* [ ] **Owner sign-off on §5 decisions.**  ⬅ waiting on this.

Once §5 is signed off, Phase 1.1 schema work is unblocked.

---

## 7. Provenance

All Phase 0 artefacts are under version control and reproducible:

```bash
.venv-feasibility/bin/python scripts/inventory_ucs.py --stats
.venv-feasibility/bin/python scripts/gap_analysis.py
.venv-feasibility/bin/python scripts/feasibility/olir_ingest_proof.py
.venv-feasibility/bin/python scripts/feasibility/oscal_generate_proof.py
.venv-feasibility/bin/python scripts/feasibility/validate_exemplar_uc.py
.venv-feasibility/bin/python scripts/feasibility/splunk_app_poc.py
```

Re-running the above from this commit must produce identical output
(modulo generated timestamps noted in each script).

---

## 8. What happens next

**Nothing** until §5 is signed off. This is the explicit stop from the
plan: Phase 0 ends here; Phase 1 does not begin without the owner's
decisions on §5.1–§5.8.
