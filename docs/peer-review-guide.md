# Peer review guide (Phase 4.5 QA gate)

> **Status:** active from Phase 4.5 onwards.
> **Audience:** every engineer reviewing a pull request that adds or
> changes compliance content.
> **What this is.** The rubric reviewers use to sign off on PRs that
> touch the compliance surface of the catalogue. It exists so that
> "a second pair of eyes" is more than a slogan — every claim a UC
> makes about a regulation has been checked by someone other than the
> author before it reaches `main`.

---

## 1. When a PR needs a peer review

A PR triggers the Phase 4.5 peer-review gate when **any** of the
following paths change:

- `use-cases/cat-22/**` — any regulatory UC sidecar.
- `use-cases/cat-*/uc-*.json` — any UC sidecar that carries a
  `compliance[]` array.
- `schemas/uc.schema.json` — the JSON schema every sidecar validates
  against.
- `data/regulations.json` — the 60-framework regulatory index.
- `data/crosswalks/**` — the ATT&CK, D3FEND, OSCAL, and OLIR crosswalks.
- `docs/regulatory-primer.md` — the plain-language primer.
- `docs/evidence-packs/**` — the tier-1 auditor packs.
- `tests/golden/compliance-mappings.yaml` — the hand-curated regression
  tuples.

Build-pipeline only changes (generators, CI, documentation tooling)
**do not** trigger the gate; the existing `validate.yml` steps are
sufficient for those.

Changes that only affect `index.html`, `scorecard.html`, the
non-technical view, or the dashboard CSS likewise do not trigger the
gate — reviewers eyeball the rendering and the usual PR template
applies.

## 2. Who can review

Peer review must be done by an engineer who is **not** the author of
the PR. The reviewer must have read this guide and the following
prerequisites at least once:

- `docs/coverage-methodology.md` — so the reviewer understands what
  `clause-coverage`, `priority-weighted`, and `assurance-adjusted`
  mean.
- `docs/api-versioning.md` — so the reviewer knows when a sidecar
  change is a breaking change to `api/v1/`.
- `schemas/uc.schema.json` — so the reviewer can read the schema
  grammar and spot invalid field combinations.

The reviewer does **not** need to be a lawyer, an auditor, or a
compliance officer. Those roles sit in the legal review (Phase 4.5b)
and the SME sign-off (Phase 5.2) respectively.

## 3. The six-point peer review rubric

Every peer review walks these six checks in order. A single "no"
blocks the PR until the author resolves the comment.

### 3.1 Clause precision

**Question.** Does every `compliance[].clause` point at a real clause
in the cited regulation version?

**How to check.**

1. Open the UC sidecar in `use-cases/cat-NN/uc-A.B.C.json`.
2. For every `compliance[]` entry, grep the regulation's version in
   `data/regulations.json` and verify the `clause` value matches the
   format in `commonClauses[]`. Example for GDPR:
   ```bash
   jq -r '.frameworks[] | select(.id == "gdpr") | .versions[] | select(.version == "2016/679") | .commonClauses[].id' data/regulations.json
   ```
3. Confirm that the `rationale` sentence names the specific obligation
   (e.g. "Logs processing activities under Art. 30(1)(a)"), not a
   generic "supports GDPR compliance" phrase.

**Fail modes.** Clause that doesn't exist in the cited version;
rationale that restates the UC description instead of naming the
clause obligation; `rationale` shorter than 20 characters.

### 3.2 Assurance honesty

**Question.** Does the `assurance` level match the evidence?

**Rules.**

| Assurance        | Required evidence                                                                   |
| ---------------- | ----------------------------------------------------------------------------------- |
| `full`           | `controlTest` block present with positive **and** negative scenarios, plus a committed fixture under `sample-data/`. |
| `partial`        | SPL present, no fixture or no negative scenario. |
| `contributing`   | SPL is informational/telemetry only (e.g., logs a dashboard widget but does not flag non-compliance). |

**Fail modes.** `full` without a fixture; `full` with a fixture that
is shorter than one event; `partial` where the SPL has no `stats`/
`eval`/`where` and only does `index=...`.

### 3.3 MITRE / OSCAL / D3FEND cross-refs

**Question.** Every external reference resolves to a vendored
authoritative source.

**How to check.**

- ATT&CK technique IDs appear in
  `vendor/attack/enterprise-attack.json` (or the Mobile / ICS
  matrices). Use:
  ```bash
  jq -r '.objects[] | select(.type=="attack-pattern") | .external_references[] | select(.source_name=="mitre-attack") | .external_id' vendor/attack/enterprise-attack.json | sort -u | grep -x "T1110"
  ```
- OSCAL controls appear in
  `vendor/oscal/nist_sp_800_53_r5_catalog.json` (or the matching
  catalog for 800-171, CSF, SSDF). The control ID must resolve in the
  catalog's `controls[].id` graph.
- D3FEND technique IDs appear in `vendor/d3fend/d3fend.json`.
- Symmetric check: if the UC cites technique `T1110`, then
  `api/v1/mitre/techniques/T1110.json` must list the UC in its
  `ucs[]` array.

**Fail modes.** Typos in technique IDs (`T110`, `T11110`); OSCAL
control IDs from the wrong catalog (e.g., NIST 800-53 Rev 4 when the
framework says Rev 5); symmetric index not regenerated
(`scripts/generate_api_surface.py --check` will flag this).

### 3.4 Provenance

**Question.** Where did this UC come from?

**Accepted provenance values.**

- `ssc:<commit>` — lifted from the Splunk Security Content repo, where
  `<commit>` is the short SHA.
- `vendor:<name>:<retrieval-date>` — lifted from a vendor doc (Cisco,
  Palo Alto, Microsoft, etc.). Include the URL in `notes` and match it
  against `data/provenance/retrieval-manifest.json`.
- `author:hand-authored` — new content authored for this repo. Require
  a reference URL in the UC's `references[]` for every factual claim
  (vendor docs, RFCs, CVE entries, regulator guidance).
- `derived-from-parent` — reserved for the Phase 3.3 derivatives
  generator; never appears on hand-authored content.

**Fail modes.** Missing `provenance`; `provenance: "author:…"` with
zero `references[]`; `ssc:<sha>` that doesn't resolve in the pinned
Splunk Security Content commit.

### 3.5 Derivatives (for UK GDPR / CCPA / nFADP / LGPD / APPI only)

**Question.** Are derivative entries correctly tagged?

**Rules (from `docs/coverage-methodology.md` §4).**

- `derivationSource.parentRegulation` must be listed as a parent in
  `data/regulations.json.derivesFrom`.
- `derivationSource.inheritanceMode` must match the mode declared in
  `regulations.json` (`identity` for UK GDPR; `mapped` for the
  others).
- `assurance` on a derived entry is strictly lower than the parent's
  (`full → partial`, `partial → contributing`). Raising assurance
  against the parent is a schema error.

**Fail modes.** Derived entry claims higher assurance than the parent;
inheritance mode mismatched with the graph; parent clause that no
longer exists in the parent version (indicates the author forgot to
re-run `scripts/generate_phase3_3_derivatives.py --check`).

### 3.6 Build hygiene

**Question.** Did the author regenerate the downstream artefacts?

**How to check.**

```bash
python3 build.py
python3 scripts/audit_compliance_mappings.py
python3 scripts/generate_api_surface.py --check
python3 scripts/generate_splunk_app.py --check
python3 scripts/regenerate_cat22_ntv.py --check
node --test tests/scorecard/render.test.mjs tests/recommender/match.test.mjs
```

All six commands must exit 0 before merge. CI runs them too, but the
reviewer confirms the author has seen the output locally.

## 4. Recording the sign-off

Every PR that triggers the gate appends a signoff record to
`data/provenance/peer-review-signoffs.json`. The record is validated
against `schemas/peer-review-signoff.schema.json` by
`scripts/audit_peer_review_signoffs.py`; a PR that touches the gated
paths **without** appending a record fails CI.

Example record:

```json
{
  "pr": "#123",
  "date": "2026-04-16",
  "commit": "abc1234",
  "author": "@github-author",
  "reviewer": "@github-reviewer",
  "scope": ["22.17", "22.17.1", "22.17.2"],
  "checks": {
    "clausePrecision": "pass",
    "assuranceHonesty": "pass",
    "mitreOscalCrossRefs": "pass",
    "provenance": "pass",
    "derivatives": "n/a",
    "buildHygiene": "pass"
  },
  "notes": "Reviewer requested rationale wording change on 22.17.2 before approving; see PR comment."
}
```

Fields:

- `pr` — GitHub PR number with leading `#`, or the empty string for
  direct commits to `main` (discouraged).
- `date` — ISO-8601 date of the sign-off.
- `commit` — short SHA of the commit being signed off (use `HEAD^`
  after landing the review).
- `author`, `reviewer` — GitHub handles; must differ.
- `scope` — UC IDs reviewed, plus `"regulations.json"` /
  `"schema"` / `"primer"` for meta-content changes.
- `checks` — one of `pass` / `fail` / `n/a` per rubric point.
- `notes` — free text; required when any `check` is `fail` (explain
  the fix) or when `derivatives` is `n/a` (state why).

## 5. Escalation

If a PR touches more than **10 UC sidecars** or changes the schema,
the peer reviewer should also tag the project maintainer for a second
sign-off. Major refactors (phase-level deliverables, new generator
scripts, new regulation ingest) always get two sign-offs.

## 6. Historical baseline

Content authored before Phase 4.5 was landed without peer-review
sign-offs. That content is grandfathered and does not block merges;
the audit script only enforces the gate on **new** (post-baseline)
paths. The baseline cut-off is the commit that introduces
`data/provenance/peer-review-signoffs.json` (see the Phase 4.5 entry
in `CHANGELOG.md`).

---

## See also

- `docs/legal-review-guide.md` — Phase 4.5b legal review rubric
  (regulatory claim surface).
- `docs/sme-review-guide.md` — Phase 5.2 SME review rubric (SPL
  correctness + auditor-evidence acceptability).
- `docs/regulatory-change-watch.md` — Phase 5.3 regulatory change-watch
  gate (staleness threshold + scheduled probe).
- `docs/signed-provenance.md` — Phase 5.4 signed provenance ledger
  (content-addressable merkle-root record of every compliance mapping;
  peer-review signoff state is snapshotted into each ledger entry).
- `docs/coverage-methodology.md` — clause / priority / assurance
  definitions.
- `docs/api-versioning.md` — when a UC sidecar change becomes a
  breaking change.
- `schemas/uc.schema.json` — authoritative sidecar grammar.
- `schemas/peer-review-signoff.schema.json` — peer-review record
  grammar.
- `schemas/sme-review-signoff.schema.json` — SME-review record
  grammar.
