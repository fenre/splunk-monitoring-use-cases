<!-- AUTO-GENERATED from UC-3.4.4.json — DO NOT EDIT -->

---
id: "3.4.4"
title: "Registry Image Vulnerability Scan Results"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.4.4 · Registry Image Vulnerability Scan Results

## Description

Images with known CVEs in the registry pose risk when deployed. Tracking scan results ensures only approved images are used and triggers remediation.

## Value

Images with known CVEs in the registry pose risk when deployed. Tracking scan results ensures only approved images are used and triggers remediation.

## Implementation

Run vulnerability scanner against registry images (e.g. Trivy, Clair) and ingest results. Alert when Critical/High CVEs appear. Enforce policy to block deployment of failing images.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom API input (Trivy, Clair, registry scanner).
• Ensure the following data sources are available: Registry vulnerability scan output (JSON/CSV).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run vulnerability scanner against registry images (e.g. Trivy, Clair) and ingest results. Alert when Critical/High CVEs appear. Enforce policy to block deployment of failing images.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="registry:vuln_scan"
| search severity="Critical" OR severity="High"
| stats count as vuln_count, values(cve_id) as cves by image_tag, registry
| where vuln_count > 0
| sort -vuln_count
```

Understanding this SPL

**Registry Image Vulnerability Scan Results** — Images with known CVEs in the registry pose risk when deployed. Tracking scan results ensures only approved images are used and triggers remediation.

Documented **Data sources**: Registry vulnerability scan output (JSON/CSV). **App/TA** (typical add-on context): Custom API input (Trivy, Clair, registry scanner). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: registry:vuln_scan. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="registry:vuln_scan". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by image_tag, registry** so each row reflects one combination of those dimensions.
• Filters the current rows with `where vuln_count > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (image, CVE count, severity), Bar chart by image, Single value (images with critical vulns).

## SPL

```spl
index=containers sourcetype="registry:vuln_scan"
| search severity="Critical" OR severity="High"
| stats count as vuln_count, values(cve_id) as cves by image_tag, registry
| where vuln_count > 0
| sort -vuln_count
```

## Visualization

Table (image, CVE count, severity), Bar chart by image, Single value (images with critical vulns).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
