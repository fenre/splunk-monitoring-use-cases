# sample-data/

JSON fixtures used as **compliance-control evidence** for compliance-oriented
use cases, especially in category 22. They are distinct from the
[`samples/`](../samples/README.md) tree (per-UC Splunk log fixtures +
manifests). The split — and the contract that this tree owns
compliance-evidence fixtures while `samples/` owns raw-event SPL
fixtures — is ratified in
[ADR-0010](../docs/adr/0010-sample-and-sample-data-co-exist.md), and
the canonical JSON shape used in this tree is ratified in
[ADR-0012](../docs/adr/0012-sample-data-canonical-shape.md).

## Canonical shape (ADR-0012)

Every new fixture in this directory uses the **phase3** shape: a
top-level object with `positive` and `negative` arrays of
evidence-attestation records. Authoring template:

```json
{
  "$comment": "Optional human-readable note about the fixture's purpose.",
  "uc": "UC-X.Y.Z",
  "description": "Optional plain-language summary of what the fixture demonstrates.",
  "positive": [
    {
      "evidence_id": "ev-<uc-id>-positive",
      "owner": "<role or team>",
      "status": "complete | gap"
    }
  ],
  "negative": [
    {
      "evidence_id": "ev-<uc-id>-negative",
      "owner": "<role or team>",
      "status": "complete | gap"
    }
  ]
}
```

Required structural invariants (enforced by
`python3 -m splunk_uc audit-sandbox-validation`):

1. Top-level JSON value is an object.
2. The object contains both `positive` and `negative` keys.
3. Both `positive` and `negative` are arrays (empty arrays are
   allowed during the placeholder phase).
4. Each item in either array is an object. Semantic content
   (`evidence_id` / `owner` / `status` / etc.) is the author's
   responsibility and is currently not schema-enforced.

## Legacy shapes (deprecated)

Two earlier shapes are still readable by the audit during the
migration window but **must not be used in new fixtures**:

| Shape       | Top-level keys                                | Where it still appears                                 |
|-------------|-----------------------------------------------|--------------------------------------------------------|
| **phase2**  | `events_positive` / `events_negative` arrays  | `uc-22.35.*` – `uc-22.49.*` (all 39 are empty placeholders) |
| **legacy**  | `positiveCase` / `negativeCase` objects with `events[]`, `expectedFire`, `sourcetype` | `uc-22.35.1-fixture.json` only (misclassified `samples/` artefact; will move) |

ADR-0012's follow-on PR mechanically renames the 39 phase2 files
(`events_positive` → `positive`, `events_negative` → `negative`)
and relocates the single legacy file's SPL content to
`samples/UC-22.35.1/` per ADR-0010, replacing it with an
initially-empty phase3 evidence fixture.

## References vs files on disk

Many `content/cat-22-regulatory-compliance/UC-*.json` entries set
`controlTest.fixtureRef` to paths like
`sample-data/uc-<id>-fixture.json`. A large share of those paths
**do not yet have a matching file on disk** — the references describe
**intended evidence**, not guaranteed artefacts. Conversely, several
committed fixtures are **not referenced** by any UC JSON today.
Replacing placeholder fixtures with real evidence records and
aligning `fixtureRef` values is content-authoring work tracked in
`docs/health-check-2026-progress.md` §P12, not a structural problem
with this directory.

## Cross-tree reference rule (ADR-0010)

A UC sidecar that needs both kinds of fixture carries two pointers:
`controlTest.fixtureRef` pointing into this directory, plus an
implicit `samples/UC-<id>/` pickup for the SPL harness. Neither
tree may name the other directly — fixtures here may not reference
log files in `samples/`, and `samples/UC-<id>/manifest.yaml` may
not reference JSON files here. The audit `python3 -m splunk_uc
audit-sandbox-validation` enforces this split.

## Tooling

The audit `python3 -m splunk_uc audit-sandbox-validation` walks
this directory, classifies each fixture (`populated` /
`half-empty` / `empty` / `missing` / `bad-json` / `malformed`),
and rolls up a status table for every UC carrying
`controlTest.fixtureRef`. See
[`src/splunk_uc/audits/sandbox_validation.py`](../src/splunk_uc/audits/sandbox_validation.py)
for the structural rules.
