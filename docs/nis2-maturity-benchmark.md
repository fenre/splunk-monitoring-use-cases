# NIS2 maturity and benchmark model

The NIS2 maturity view groups obligations into crawl, walk, and run stages.

- **Crawl**: source registers, essential/important classification, incident reporting clocks, minimum evidence exports.
- **Walk**: supplier risk, vulnerability disclosure, access review, backup/restore, secure development, dashboarded assurance.
- **Run**: evidence signing, maturity scoring, sector overlays, automated next-best-control recommendations, external-review pack readiness.

UC-22.2.57 operationalises this model from the no-gap matrix and the catalogue's UC implementation status data.

The repository compliance section exposes the same maturity view inside the canonical compliance story page at `compliance-story.html?reg=nis2`, which renders the `deepCoverage` block carried by `api/v1/compliance/story/nis2.json`. That block summarises:

- matrix rows, monitorable rows, NIS2-tagged UCs, and legal-boundary rows;
- coverage by Splunk coverage type and assurance target;
- review-confidence and source-authority distribution;
- per control-family (domain) coverage breakdown;
- direct links to the canonical artifacts (`data/nis2-source-map.json`, `data/per-regulation/nis2-coverage-expansion.json`, evidence pack, methodology, and external-review pack).

## Benchmark domains

- Scope, registry, DNS, and information sharing.
- Art.20 governance.
- Art.21 risk-management measures.
- Art.23 incident reporting.
- Implementing Regulation annex domains.
- Annex sector overlays.
- Supervision and enforcement readiness.
- Directive context and legal boundaries.
