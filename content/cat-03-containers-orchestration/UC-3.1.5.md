---
id: "3.1.5"
title: "Image Vulnerability Scanning"
criticality: "medium"
splunkPillar: "Security"
---

# UC-3.1.5 · Image Vulnerability Scanning

## Description

Container images with known CVEs are deployed directly into production. Scanning and tracking vulnerabilities prevents running exploitable workloads.

## Value

Container images with known CVEs are deployed directly into production. Scanning and tracking vulnerabilities prevents running exploitable workloads.

## Implementation

Run vulnerability scans in CI/CD pipeline (Trivy, Grype, or Snyk). Send Trivy/Grype scan results to Splunk via HEC with `sourcetype=trivy:scan` (or equivalent scanner output); batch results per image digest. Alert on `Severity=CRITICAL` for images whose `image_tag` matches production entries in a `prod_images` lookup. Exclude known-accepted CVEs via a `cve_exceptions.csv` lookup refreshed by the security team.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom input (Trivy, Snyk, Grype JSON output).
• Ensure the following data sources are available: JSON scan results from vulnerability scanners.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run vulnerability scans in CI/CD pipeline (Trivy, Grype, or Snyk). Send Trivy/Grype scan results to Splunk via HEC with `sourcetype=trivy:scan` (or equivalent scanner output); batch results per image digest. Alert on `Severity=CRITICAL` for images whose `image_tag` matches production entries in a `prod_images` lookup. Exclude known-accepted CVEs via a `cve_exceptions.csv` lookup refreshed by the security team.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="trivy:scan"
| stats count by image, Severity
| xyseries image Severity count
| sort -CRITICAL -HIGH
```

Understanding this SPL

**Image Vulnerability Scanning** — Container images with known CVEs are deployed directly into production. Scanning and tracking vulnerabilities prevents running exploitable workloads.

Documented **Data sources**: JSON scan results from vulnerability scanners. **App/TA** (typical add-on context): Custom input (Trivy, Snyk, Grype JSON output). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: trivy:scan. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="trivy:scan". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by image, Severity** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pivots fields for charting with `xyseries`.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (image, critical, high, medium, low), Stacked bar chart by image, Trend line.

## SPL

```spl
index=containers sourcetype="trivy:scan"
| stats count by image, Severity
| xyseries image Severity count
| sort -CRITICAL -HIGH
```

## Visualization

Table (image, critical, high, medium, low), Stacked bar chart by image, Trend line.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
