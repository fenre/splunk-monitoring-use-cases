---
id: "3.4.2"
title: "Vulnerability Scan Results"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.4.2 · Vulnerability Scan Results

## Description

Registry-level scanning catches vulnerabilities before images are deployed. Trending shows whether security posture is improving or degrading.

## Value

Registry-level scanning catches vulnerabilities before images are deployed. Trending shows whether security posture is improving or degrading.

## Implementation

Poll registry scan APIs for results or configure webhook notifications on scan completion. Forward to Splunk via HEC. Alert on critical vulnerabilities in images tagged for production.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom input (Harbor, ACR, ECR scan APIs).
• Ensure the following data sources are available: Scan result JSON from registry API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll registry scan APIs for results or configure webhook notifications on scan completion. Forward to Splunk via HEC. Alert on critical vulnerabilities in images tagged for production.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="registry:scan"
| stats sum(critical) as critical, sum(high) as high, sum(medium) as medium by repository, tag
| where critical > 0
| sort -critical
```

Understanding this SPL

**Vulnerability Scan Results** — Registry-level scanning catches vulnerabilities before images are deployed. Trending shows whether security posture is improving or degrading.

Documented **Data sources**: Scan result JSON from registry API. **App/TA** (typical add-on context): Custom input (Harbor, ACR, ECR scan APIs). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: registry:scan. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="registry:scan". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by repository, tag** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where critical > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked bar chart (vulns by severity per image), Table, Trend line (vulns over time).

## SPL

```spl
index=containers sourcetype="registry:scan"
| stats sum(critical) as critical, sum(high) as high, sum(medium) as medium by repository, tag
| where critical > 0
| sort -critical
```

## Visualization

Stacked bar chart (vulns by severity per image), Table, Trend line (vulns over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
