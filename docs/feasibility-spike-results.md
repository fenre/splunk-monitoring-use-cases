# Phase 0.5 — feasibility spike results

> **Status:** complete, 2026-04-16. All four sub-proofs PASS.
> **Goal:** de-risk the tooling choices for Phase 1 by running end-to-end
> proofs of the four highest-risk items *before* we invest in schema or
> content work.
> **Audience:** Phase 1 schema designers, reviewers, and anyone auditing
> the methodology behind the regulatory-gold-standard catalogue.

---

## 1. Summary

| # | Spike | Script | Outcome | Time-boxed | Actual |
|---|---|---|---|---:|---:|
| 0.5a | OLIR / OSCAL catalogue ingest | `scripts/feasibility/olir_ingest_proof.py` | **PASS** | 4 h | 3 h |
| 0.5b | OSCAL generation + validation | `scripts/feasibility/oscal_generate_proof.py` + `scripts/feasibility/oscal_validate.mjs` | **PASS** (via Ajv) | 4 h | 6 h (incl. Python validator false start) |
| 0.5c | UC authoring ergonomics | `scripts/feasibility/validate_exemplar_uc.py` | **PASS** | 2 h | 2 h |
| 0.5d | Splunk-app POC | `scripts/feasibility/splunk_app_poc.py` | **PASS** (shape-check) | 4 h | 2 h |

Every output is reproducible from a clean clone:

```bash
.venv-feasibility/bin/python scripts/feasibility/olir_ingest_proof.py
.venv-feasibility/bin/python scripts/feasibility/oscal_generate_proof.py
.venv-feasibility/bin/python scripts/feasibility/validate_exemplar_uc.py
.venv-feasibility/bin/python scripts/feasibility/splunk_app_poc.py
```

---

## 2. Tool versions pinned

* Python feasibility venv — `.venv-feasibility/`
  * `jsonschema` 4.26.0 (used for UC sidecar validation, 0.5c)
  * `jsonschema-rs` — ECMA-262-aware alternative, **retained for 0.5c
    only**; see §4.2 for why it was the wrong tool for OSCAL.
  * `openpyxl` — used to introspect NIST CPRT XLSX exports.
* Node 25.9.0 (system)
  * `ajv` ^8.18.0 — OSCAL schema validation in Phase 0.5b.
  * `ajv-formats` ^3.0.1 — ISO date/time, URI format validators.
* No external network calls made by validators — all data vendored under
  `vendor/olir/`, `vendor/cprt/`, `vendor/oscal/`.

---

## 3. Detailed results

### 3.1 Phase 0.5a — OLIR / OSCAL catalogue ingest

**Goal.** Prove we can consume NIST's authoritative OSCAL catalogues
for CSF 2.0 and SP 800-53 Rev 5 without manual transcription.

**Source.** `https://raw.githubusercontent.com/usnistgov/OSCAL-content/main/nist.gov/...`

**Process.**
1. Downloaded the two OSCAL catalogue JSON files into
   `vendor/olir/` with SHA-256 provenance.
2. Normalised each into a flat `{id, name, text, links[]}` structure
   under `data/crosswalks/olir/`.
3. Captured findings in `data/crosswalks/olir/manifest.json`.

**Result — `manifest.json` excerpt:**
```json
{
  "findings": [
    "nist-csf-v2: no inline cross-framework links — relationships live in a separate OLIR/Profile artefact",
    "nist-sp-800-53-r5: inline links present (related=3512, reference=838, required=715, incorporated-into=166)"
  ]
}
```

**Numbers.** 219 CSF v2 controls and 1 196 800-53 r5 controls ingested.

**Implication for Phase 1.3.** The inline link surface on SP 800-53 is
already rich (5 231 links in total). CSF v2, by contrast, does not carry
inline cross-framework links in its catalogue file — crosswalks to
800-53, ISO 27001:2022 and PCI DSS v4.0 are distributed as separate
OLIR/Profile documents. Phase 1.3 must ingest those separately; the
gap is scheduled, not blocking.

**Known limitation.** We attempted to pull the NIST CPRT "JSON"
endpoint for Informative References; it serves XLSX, not JSON. That
is a NIST-side quirk we worked around by pinning the OSCAL-content
GitHub mirror (which is the same data in the format we want).

---

### 3.2 Phase 0.5b — OSCAL generation + validation

**Goal.** Prove we can generate a NIST OSCAL v1.1.1 Component
Definition from a UC JSON sidecar and validate it against the
authoritative schema.

**Exemplar input.** `use-cases/cat-22/uc-22.35.1.json`
**Generator.** `scripts/feasibility/oscal_generate_proof.py`
**Output.** `data/crosswalks/oscal/component-definition-uc-22.35.1.json`
**Validator.** `scripts/feasibility/oscal_validate.mjs` (Node + Ajv)

**Validator choice rationale.** This is the most important finding of
the spike. We went through three validator candidates:

| Validator | Outcome | Why |
|---|---|---|
| Python `jsonschema` 4.26.0 | **FAIL** | NIST OSCAL schema uses ECMA-262 Unicode property escapes (`\p{L}`, `\p{N}`) in `pattern` regexes. Python's `re` does not implement them. The schema cannot even be compiled. |
| `jsonschema-rs` (Rust, ECMA-262 regex) | **FAIL** | Handles the regex, but fails to resolve NIST's ~119 anchor-style `"$ref": "#id"` definitions. Even a minimal-valid component definition fails at `definitions/URIReferenceDatatype/type` because the validator falls through to treating the top-level object as a string. |
| **Node `ajv@^8` + `ajv-formats`** | **PASS** | Handles both ECMA-262 regex and anchor-style `$ref`s. Industry standard for OSCAL in JavaScript tooling, aligned with what NIST itself publishes. |

We pin Ajv for OSCAL in Phase 1+. `jsonschema-rs` is retained for the
UC sidecar validator (Phase 0.5c), where it is the correct tool.

**Result — final run:**
```
PASS: data/crosswalks/oscal/component-definition-uc-22.35.1.json
      validates against vendor/oscal/oscal_component_schema_v1.1.1.json (Ajv).
      generator output : data/crosswalks/oscal/component-definition-uc-22.35.1.json
      sha256 (on-disk) : 8a4c476921b94f7dc0d300c4f6f75b73c44dc7081590eae49ec706ef85f96243
```

**Generator-side findings.**
* The generator must **omit** `links` rather than emit `links: []` when
  a mapping has no `clauseUrl`. OSCAL's `links[]` has `minItems: 1`; an
  empty array fails validation.
* Deterministic UUIDs (namespace v5 over a stable seed) mean the
  generator is reproducible byte-for-byte across machines, which is a
  hard requirement for cryptographic provenance in Phase 2.
* The generator reports the SHA-256 of the **on-disk** bytes (not of
  an in-memory alternative serialisation). The reported hash equals
  `shasum -a 256 <file>`, which matters for chain-of-custody claims
  made at §7 and for Phase 2 evidence signing.

---

### 3.3 Phase 0.5c — UC authoring ergonomics

**Goal.** Prove the JSON-first authoring model is viable for the
compliance catalogue.

**Schema.** `schemas/uc.schema.json`
**Exemplar.** `use-cases/cat-22/uc-22.35.1.json`
**Validator.** `scripts/feasibility/validate_exemplar_uc.py` (Python
`jsonschema` 4.26.0 with Draft 2020-12)

**Result.**
```
PASS: use-cases/cat-22/uc-22.35.1.json conforms to schemas/uc.schema.json
```

**Schema changes locked in during the spike.**
1. `$schema` was not in the `properties` block while
   `additionalProperties: false` was on — IDE LSP hints caused the
   exemplar to be rejected. **Fix applied:** explicit
   `"$schema": { "type": "string", "format": "uri-reference" }`.
2. `compliance[].clauseUrl` must be optional (not every clause in every
   framework has a stable deep link). **Fix applied:** removed from
   `required`. Empty `links` arrays are handled at OSCAL generation
   (see 3.2).
3. `controlTest` block is schema-required at the top level (no
   fallback to marker comments).

See §5 for the full "schema changes recommended for Phase 1.1" list.

**Authoring-ergonomics verdict.** Two auditor-facing fields
(`assurance_rationale` and `mode`) turn what was a single free-text
`Regulations:` bullet into a sentence-long structured claim per clause.
This is more demanding to author than the current markdown bullet, but
it is exactly the shape auditors asked for in the literature review.
Phase 0.1 interviews will confirm or reshape the vocabulary; see
`docs/auditor-research/interview-guide.md` §4.

---

### 3.4 Phase 0.5d — Splunk-app POC

**Goal.** Prove that given a conformant JSON sidecar we can
deterministically emit an AppInspect-shaped Splunk app.

**Generator.** `scripts/feasibility/splunk_app_poc.py`
**Output.** `build/poc/SplunkAppForComplianceUseCases/`
**Shape-check validators** (performed in-script):
* Required files present (app.conf, savedsearches.conf, default.meta,
  app.manifest, nav XML, view XML, README).
* `app.manifest` JSON parses and `schemaVersion == 2.0.0`.
* `nav/default.xml` and `views/compliance_overview.xml` parse as XML.

**Result.**
```
PASS: generated 7 file(s) under build/poc/SplunkAppForComplianceUseCases
      sha256 (tree) : 769392e39b656684ecc487e6a0831c26f3cc07c9f2705c2ca8be394a10677ddf
```

**Why not run AppInspect here.** `splunk-appinspect` and
`slim package` require a Splunk account and an accepted dev agreement
to download; they are not free-tier. The POC therefore documents the
exact commands a reviewer would run in Phase 1:

```bash
slim package build/poc/SplunkAppForComplianceUseCases
splunk-appinspect inspect \
  --mode precert --included-tags cloud \
  build/poc/SplunkAppForComplianceUseCases
btool check --app=SplunkAppForComplianceUseCases
```

A `build/poc/` directory is generated on every run and is git-ignored
(regenerable).

**Compliance-specific saved-search wiring.** The POC emits a comment
line with the compliance tags derived from the UC's `compliance[]`
block so that the audit trail ("this saved search was generated from
UC-22.35.1, which asserts GDPR/HIPAA/PCI-DSS/SOC-2/SOX-ITGC
mappings") is visible to a human reviewing `savedsearches.conf`.

---

## 4. Scope boundaries that held

* **No external network calls from validators.** All schemas, catalogues,
  and test data are vendored. `npm install` and `pip install` ran
  exactly once during the spike and are captured in `package.json` /
  `package-lock.json`.
* **No NIST-licensed content vendored.** Everything under `vendor/` is
  either CC-BY, NIST-public, or a generated excerpt.
* **No `splunk-appinspect` execution.** The POC produces a tree that is
  structurally valid and documents what a free-tier reviewer would run.
* **No UC markdown content was modified.** The only content touched is
  the JSON sidecar exemplar `uc-22.35.1.json` and the schema.

---

## 5. Schema changes recommended for Phase 1.1

The schema is at `schemas/uc.schema.json`. Changes **applied during the
spike** plus changes **recommended for Phase 1.1**:

| # | Field | Applied here? | Phase 1.1 task |
|---|---|---|---|
| 1 | `$schema` at top level | ✅ applied | none |
| 2 | `compliance[].clauseUrl` optional | ✅ applied | keep; document rationale in schema description |
| 3 | `controlTest` required | ✅ applied | keep |
| 4 | `compliance[].assurance` enum | to refine after 0.1 | replace `full/partial/contributing` with auditor-tested vocabulary |
| 5 | `compliance[].mode` enum | to refine after 0.1 | replace `satisfies/detects-violation-of` with auditor-tested vocabulary |
| 6 | `compliance[].assurance_rationale` | ✅ applied | consider a maxLength cap (≤ 800 chars) |
| 7 | `references[]` objects with `retrieved` date | ✅ applied | enforce RFC 3339 date format |
| 8 | `controlFamily` | present as string | promote to enum after Phase 1.2 inventory is complete |
| 9 | `evidence` | free-text | split into structured `{artefactType, path}` once the evidence-pack generator is specified |
| 10 | `compliance[].version` | free-text | promote to pattern-validated string once `data/regulations.draft.json` becomes `data/regulations.json` |
| 11 | `lastReviewed` | date string | require RFC 3339 date |
| 12 | `reviewer` | free-text | document format (`"name <email>"`) for signed reviews in Phase 2 |

Recommended additions for Phase 1.1:

* `compliance[].provenance` — where did the clause mapping come from?
  (Possible enum: `maintainer`, `auditor-reviewed`, `olir-crosswalk`,
  `nist-cprt-ingest`.)
* `compliance[].signedBy` — optional string naming the reviewer who
  vetted the mapping.
* `evidence.signing` — optional block describing how evidence is
  timestamped/signed (RFC 3161 TSA, Sigstore, or none).

---

## 6. Known risks carried into Phase 1

1. **Auditor vocabulary.** `assurance` and `mode` values are draft;
   Phase 0.1 may change them. Not blocking because the schema is
   versioned and sidecars can be migrated with a single script.
2. **CSF v2 crosswalks.** Currently unavailable inline; must be
   ingested as separate OLIR/Profile artefacts in Phase 1.3.
3. **AppInspect verification.** Not exercised end-to-end in
   free-tier; documented commands for the first paying reviewer.
4. **NIST CPRT JSON endpoint.** Returns XLSX for some releases;
   pinned to OSCAL-content GitHub mirror instead. Phase 1.3 will
   re-assess.
5. **Splunk 9.x vs 10.x packaging differences.** Phase 0.5d only
   produces an AppInspect-shaped structure; Splunk Cloud vetting
   rules may add additional constraints in Phase 2.

---

## 7. Provenance

| Artefact | Path | SHA-256 |
|---|---|---|
| UC exemplar | `use-cases/cat-22/uc-22.35.1.json` | (tracked in git) |
| UC schema | `schemas/uc.schema.json` | (tracked in git) |
| OSCAL generated | `data/crosswalks/oscal/component-definition-uc-22.35.1.json` | `8a4c4769…6243` |
| OLIR ingest manifest | `data/crosswalks/olir/manifest.json` | (tracked in git) |
| Splunk POC tree | `build/poc/SplunkAppForComplianceUseCases/` | `769392e3…7ddf` |
| OSCAL schema | `vendor/oscal/oscal_component_schema_v1.1.1.json` | (tracked in git) |
| NIST CSF v2 catalogue | `vendor/olir/nist_csf_v2_catalog.json` | `e3edb5ef…e936` |
| NIST SP 800-53 r5 catalogue | `vendor/olir/nist_sp_800_53_r5_catalog.json` | `1645df6a…5bcc` |

Regenerate any of the above with its corresponding
`scripts/feasibility/*.py` script.

---

## 8. Decision

**Proceed to Phase 1.** No blockers. All four de-risking proofs pass
with reproducible commands. The only outstanding tooling decision
(validator for OSCAL) is resolved in favour of Node + Ajv, documented
in §3.2. Recommended schema changes (§5) are additive and non-breaking
against the current exemplar.
