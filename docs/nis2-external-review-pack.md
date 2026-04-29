# NIS2 external-review pack

This pack is intended for later review by counsel, auditors, regulators, or competent-authority specialists. It gathers the implementation artifacts without implying external endorsement.

## Contents

- Source map: `data/nis2-source-map.json` and `docs/research/nis2-source-map.md`.
- No-gap matrix: `data/per-regulation/nis2-coverage-expansion.json`.
- Methodology: `docs/nis2-monitoring-methodology.md`.
- Evidence pack: `docs/evidence-packs/nis2.md` after regeneration.
- Web coverage surface: `compliance-story.html?reg=nis2` (driven by `api/v1/compliance/story/nis2.json`, the same per-regulation story endpoint used by every other regulation; the NIS2 story payload also carries a `deepCoverage` block computed directly from the matrix and source map).
- Catalogue rollups: `docs/compliance-coverage.md` and `reports/compliance-coverage.json`.
- Maturity benchmark: `docs/nis2-maturity-benchmark.md`.
- Self-validation record: `docs/nis2-self-validation.md`.
- Validation: `scripts/audit_nis2_no_gap.py`, `scripts/audit_compliance_mappings.py`, UC structure audits, and fixture references under `sample-data/`.

## Known limitations and legal-review questions

- National law determines final scope, competent authority, penalty detail, reporting forms, and deadlines where transposition differs.
- Splunk can prove evidence freshness, workflow progress, detections, and exceptions; it cannot perform board approval, legal interpretation, or official regulator filing.
- Background-check, HR, customer notification, and incident evidence must be privacy-reviewed before ingestion.
- `full` assurance is intentionally rare and requires integrated source-of-record logs.

## Best practical implementation statement

This repository implements a best-in-class Splunk-based NIS2 monitoring and evidence framework: official-source traceability, no-gap obligation matrix, conservative assurance calibration, concrete SPL/evidence artifacts, sample control tests, source-map governance, and generated web/report surfaces. It does not guarantee NIS2 compliance or replace qualified legal/audit review.

## Review questions to carry forward

- Which national transposition law and competent authority apply to the entity, service, sector, and establishment facts?
- Which `requires-legal-review` rows should be reviewed before board, regulator, or customer-facing use?
- Are HR, training, customer notification, supplier, and background-check fields privacy-minimised for the entity's jurisdiction?
- Are evidence exports retained in a tamper-evident store with access controls, retention, and deletion rules approved by the organisation?
- Are Splunk product dependencies, CIM accelerations, SOAR playbooks, ITSI services, and external source-of-record integrations present in the target environment?
