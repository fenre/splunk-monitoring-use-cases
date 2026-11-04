# `uc-review-finding.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes |
|---------|----------|-----------|-------|
| 1.0.0   | 2026-Q4  | preview   | Initial release (catalogue v8.26). One review record per UC per tier (`deterministic`, `triage`, `deep`, `adjudication`) for the UC text-quality review. Emitted by `python3 -m splunk_uc audit-text-quality` and `scripts/uc_review_runner.py`; consumed by `review-prompt`, `generate-uc-review-report` and `lift-prompt --findings`. Rubric: [`docs/uc-text-review-rubric.md`](../../docs/uc-text-review-rubric.md). |

## Stability commitment

`x-stability: preview` — the review workflow is new; fields may change in a
minor release while the calibration and pilot runs settle the rubric. Every
record carries `rubric_version`, so consumers can ignore records produced
under an older rubric.
