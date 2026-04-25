<!-- AUTO-GENERATED from UC-3.1.10.json — DO NOT EDIT -->

---
id: "3.1.10"
title: "Container Image Vulnerability Scanning Results"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.1.10 · Container Image Vulnerability Scanning Results

## Description

Centralizing scanner output (severity, package, image digest) proves compliance and speeds remediation when new CVEs hit production images.

## Value

Centralizing scanner output (severity, package, image digest) proves compliance and speeds remediation when new CVEs hit production images.

## Implementation

Forward CI and registry scan JSON to Splunk with stable fields (`image_name`, `image_digest`, `Target`). Deduplicate on digest+CVE. Alert when CRITICAL/HIGH appears on images referenced by running tags.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom HEC (Trivy, Grype, Snyk JSON), CI pipeline artifacts.
• Ensure the following data sources are available: `sourcetype=trivy:scan`, `sourcetype=grype:scan`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward CI and registry scan JSON to Splunk with stable fields (`image_name`, `image_digest`, `Target`). Deduplicate on digest+CVE. Alert when CRITICAL/HIGH appears on images referenced by running tags.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan")
| stats latest(Severity) as sev, values(VulnerabilityID) as cves, dc(VulnerabilityID) as vuln_count by image_name, image_digest, Target
| where mvfind(sev, "CRITICAL") OR mvfind(sev, "HIGH")
| sort -vuln_count
```

Understanding this SPL

**Container Image Vulnerability Scanning Results** — Centralizing scanner output (severity, package, image digest) proves compliance and speeds remediation when new CVEs hit production images.

Documented **Data sources**: `sourcetype=trivy:scan`, `sourcetype=grype:scan`. **App/TA** (typical add-on context): Custom HEC (Trivy, Grype, Snyk JSON), CI pipeline artifacts. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: trivy:scan, grype:scan. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="trivy:scan". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by image_name, image_digest, Target** so each row reflects one combination of those dimensions.
• Filters the current rows with `where mvfind(sev, "CRITICAL") OR mvfind(sev, "HIGH")` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Docker data, spot-check a few events against the Docker engine on the host and the container list you expect. Compare with known good and bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (image, digest, vuln count, severities), Treemap by repo, Trend (open vulns over time).

## SPL

```spl
index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan")
| stats latest(Severity) as sev, values(VulnerabilityID) as cves, dc(VulnerabilityID) as vuln_count by image_name, image_digest, Target
| where mvfind(sev, "CRITICAL") OR mvfind(sev, "HIGH")
| sort -vuln_count
```

## Visualization

Table (image, digest, vuln count, severities), Treemap by repo, Trend (open vulns over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
