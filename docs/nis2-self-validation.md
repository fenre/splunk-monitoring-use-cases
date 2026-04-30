# NIS2 Self-Validation Record

This record captures the validation evidence for the best-in-class NIS2 Splunk monitoring and evidence implementation. It is an engineering self-check, not legal certification.

## Validation Summary

- NIS2 no-gap audit (`scripts/audit_nis2_no_gap.py`) passes against the 149-row matrix and the NIS2 compliance entries on every NIS2-tagged UC.
- NIS2 gold-profile audit passes for every NIS2-tagged UC JSON file under `content/cat-22-regulatory-compliance/UC-22.2.*.json`.
- `catalog.json` schema validation passes.
- The compliance-story endpoint `api/v1/compliance/story/nis2.json` carries a `deepCoverage` block computed directly from `data/per-regulation/nis2-coverage-expansion.json` and `data/nis2-source-map.json`; the same canonical surface used for every other regulation renders that block at `compliance-story.html?reg=nis2`.
- The broad compliance-mapping audit reports a pre-existing schema validation issue on `UC-13.2.7` that is unrelated to the NIS2 implementation.

## Commands Run

```bash
python3 scripts/audit_nis2_no_gap.py
python3 scripts/audit_gold_profile.py --check --files <NIS2 UC JSON files>
python3 scripts/generate_evidence_packs.py
python3 scripts/generate_api_surface.py
python3 scripts/augment_regulation_api.py
python3 scripts/generate_clause_index.py
python3 scripts/generate_story_payload.py
python3 scripts/audit_compliance_mappings.py
python3 scripts/audit_compliance_gaps.py
python3 scripts/audit_catalog_schema.py
python3 scripts/audit_splunk_cloud_compat.py
```

## Spot Checks

- `data/regulations.json` tracks the NIS2 common clauses and includes the obligation-model pointer.
- `data/per-regulation/nis2-coverage-expansion.json` contains the 149-row no-gap matrix across directive, implementing-regulation, ENISA guidance, national guidance, and sector-overlay sources.
- `data/nis2-source-map.json` contains the source register and authority ranking referenced by both the deep-coverage block and the no-gap audit.
- `api/v1/compliance/story/nis2.json` carries the `deepCoverage` block; `compliance-story.html?reg=nis2` renders it next to the buyer / auditor / implementer blocks.
- `docs/evidence-packs/nis2.md`, `docs/nis2-monitoring-methodology.md`, `docs/nis2-external-review-pack.md`, `docs/nis2-maturity-benchmark.md`, and `docs/research/nis2-source-map.md` are populated.
- `sample-data/` contains fixture files for every `UC-22.2.*` NIS2 use case.

## Revalidation Triggers

Re-run this validation after changes to NIS2 source metadata, the no-gap matrix, any NIS2 UC JSON file, evidence-pack generation, compliance reports, or web story payloads.

## Validated NIS2 use cases

The following anchor use cases pass gold-profile audit and are validated against the no-gap matrix:

- UC-22.2.1 — NIS2 Art.23(4)(a): 24-Hour Early-Warning Notification Readiness
- UC-22.2.2 — NIS2 Art.21(2)(a): Risk Analysis Policy Evidence
- UC-22.2.3 — NIS2 Art.21(2)(b): Incident Handling Workflow Compliance

Related documentation: [NIS2 Monitoring Methodology](nis2-monitoring-methodology.md), [NIS2 External Review Pack](nis2-external-review-pack.md), [NIS2 Maturity Benchmark](nis2-maturity-benchmark.md).
