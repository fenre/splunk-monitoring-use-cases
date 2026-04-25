<!-- AUTO-GENERATED from UC-3.4.9.json — DO NOT EDIT -->

---
id: "3.4.9"
title: "Container Image Vulnerability Age"
criticality: "critical"
splunkPillar: "Security"
---

# UC-3.4.9 · Container Image Vulnerability Age

## Description

Images running with known CVEs older than N days.

## Value

Images running with known CVEs older than N days.

## Implementation

Run Trivy, Grype, or registry-native scanner (Harbor, ACR) against running images or registry catalog. Output JSON with image, CVE ID, severity, and discovered_at (or published date). Forward to Splunk via HEC. Alert when Critical/High CVEs have been known for >7 days (configurable). Integrate with CI/CD to block deployment of images with aged critical vulns. Track remediation SLA.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Trivy, Grype, or registry scanner output).
• Ensure the following data sources are available: vulnerability scanner JSON output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run Trivy, Grype, or registry-native scanner (Harbor, ACR) against running images or registry catalog. Output JSON with image, CVE ID, severity, and discovered_at (or published date). Forward to Splunk via HEC. Alert when Critical/High CVEs have been known for >7 days (configurable). Integrate with CI/CD to block deployment of images with aged critical vulns. Track remediation SLA.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan" OR sourcetype="registry:vuln_scan")
| eval vuln_date = coalesce(discovered_at, PublishedDate, published_date)
| eval vuln_age_days = round((now() - strptime(vuln_date, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where (Severity="Critical" OR Severity="High") AND vuln_age_days > 7
| stats count as vuln_count, min(vuln_age_days) as oldest_vuln_days by image, tag, Severity
| sort -oldest_vuln_days -vuln_count
```

Understanding this SPL

**Container Image Vulnerability Age** — Images running with known CVEs older than N days.

Documented **Data sources**: vulnerability scanner JSON output. **App/TA** (typical add-on context): Custom (Trivy, Grype, or registry scanner output). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: trivy:scan, grype:scan, registry:vuln_scan. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="trivy:scan". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **vuln_date** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **vuln_age_days** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where (Severity="Critical" OR Severity="High") AND vuln_age_days > 7` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by image, tag, Severity** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (image, tag, severity, vuln count, oldest days), Bar chart (images by vuln age), Single value (images with aged critical vulns).

## SPL

```spl
index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan" OR sourcetype="registry:vuln_scan")
| eval vuln_date = coalesce(discovered_at, PublishedDate, published_date)
| eval vuln_age_days = round((now() - strptime(vuln_date, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where (Severity="Critical" OR Severity="High") AND vuln_age_days > 7
| stats count as vuln_count, min(vuln_age_days) as oldest_vuln_days by image, tag, Severity
| sort -oldest_vuln_days -vuln_count
```

## Visualization

Table (image, tag, severity, vuln count, oldest days), Bar chart (images by vuln age), Single value (images with aged critical vulns).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
