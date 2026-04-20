---
id: "1.3.5"
title: "Application Crash Monitoring"
criticality: "low"
splunkPillar: "Security"
---

# UC-1.3.5 · Application Crash Monitoring

## Description

Frequent application crashes degrade user experience and may indicate malware, resource issues, or incompatible software.

## Value

Frequent application crashes degrade user experience and may indicate malware, resource issues, or incompatible software.

## Implementation

Forward `~/Library/Logs/DiagnosticReports/` and `/Library/Logs/DiagnosticReports/`. Use `monitor` input in inputs.conf. Parse process name and exception type from crash reports.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk UF.
• Ensure the following data sources are available: `/Library/Logs/DiagnosticReports/*.crash`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward `~/Library/Logs/DiagnosticReports/` and `/Library/Logs/DiagnosticReports/`. Use `monitor` input in inputs.conf. Parse process name and exception type from crash reports.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=macos_crash host=*
| rex "Process:\s+(?<process>\S+)"
| stats count by host, process
| sort -count
```

Understanding this SPL

**Application Crash Monitoring** — Frequent application crashes degrade user experience and may indicate malware, resource issues, or incompatible software.

Documented **Data sources**: `/Library/Logs/DiagnosticReports/*.crash`. **App/TA** (typical add-on context): Splunk UF. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: macos_crash. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=macos_crash. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host, process** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (process, host, count), Bar chart of top crashing apps.

## SPL

```spl
index=os sourcetype=macos_crash host=*
| rex "Process:\s+(?<process>\S+)"
| stats count by host, process
| sort -count
```

## Visualization

Table (process, host, count), Bar chart of top crashing apps.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
