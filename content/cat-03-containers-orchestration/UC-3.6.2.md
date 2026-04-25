<!-- AUTO-GENERATED from UC-3.6.2.json — DO NOT EDIT -->

---
id: "3.6.2"
title: "Container Image Vulnerability Trending"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.6.2 · Container Image Vulnerability Trending

## Description

Tracking critical and high CVE counts per image over time shows whether your build pipeline and patching cadence are reducing risk or if new vulnerabilities are outpacing remediation. Supports prioritization of image rebuilds and exception reviews.

## Value

Tracking critical and high CVE counts per image over time shows whether your build pipeline and patching cadence are reducing risk or if new vulnerabilities are outpacing remediation. Supports prioritization of image rebuilds and exception reviews.

## Implementation

Ingest scanner JSON on every build or scheduled registry scan with stable image and severity fields. Normalize severity to CRITICAL/HIGH. Schedule a daily saved search to populate a summary index. Compare jumps after base-image updates as expected versus organic growth. Pair with a lookup of accepted CVEs to subtract noise for trending net-new exposure.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Trivy/Grype/Snyk CI integration, Splunk HEC.
• Ensure the following data sources are available: `index=containers sourcetype=trivy:scan` OR `sourcetype=grype:scan`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest scanner JSON on every build or scheduled registry scan with stable image and severity fields. Normalize severity to CRITICAL/HIGH. Schedule a daily saved search to populate a summary index. Compare jumps after base-image updates as expected versus organic growth. Pair with a lookup of accepted CVEs to subtract noise for trending net-new exposure.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype IN ("trivy:scan", "grype:scan")
| where Severity IN ("CRITICAL", "HIGH")
| bin _time span=1d
| stats dc(VulnerabilityID) as cve_count by _time, image
| timechart span=1d sum(cve_count) as total_cves
| trendline sma7(total_cves) as cve_trend
```

Understanding this SPL

**Container Image Vulnerability Trending** — Tracking critical and high CVE counts per image over time shows whether your build pipeline and patching cadence are reducing risk or if new vulnerabilities are outpacing remediation. Supports prioritization of image rebuilds and exception reviews.

Documented **Data sources**: `index=containers sourcetype=trivy:scan` OR `sourcetype=grype:scan`. **App/TA** (typical add-on context): Trivy/Grype/Snyk CI integration, Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers.

**Pipeline walkthrough**

• Scopes the data: index=containers. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Severity IN ("CRITICAL", "HIGH")` — typically the threshold or rule expression for this monitoring goal.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, image** so each row reflects one combination of those dimensions.
• `timechart` plots the metric over time using **span=1d** buckets — ideal for trending and alerting on this use case.
• Pipeline stage (see **Container Image Vulnerability Trending**): trendline sma7(total_cves) as cve_trend


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked area chart (critical/high CVEs over time), line chart (7-day SMA), table of top images by CVE count.

## SPL

```spl
index=containers sourcetype IN ("trivy:scan", "grype:scan")
| where Severity IN ("CRITICAL", "HIGH")
| bin _time span=1d
| stats dc(VulnerabilityID) as cve_count by _time, image
| timechart span=1d sum(cve_count) as total_cves
| trendline sma7(total_cves) as cve_trend
```

## Visualization

Stacked area chart (critical/high CVEs over time), line chart (7-day SMA), table of top images by CVE count.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
