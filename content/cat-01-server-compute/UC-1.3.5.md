<!-- AUTO-GENERATED from UC-1.3.5.json — DO NOT EDIT -->

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

Spotting the same app crashing on many Macs, or a spike for one person, steers you toward a bad release, a bad plug-in, or a sick device before that pattern turns into a project-wide outage in disguise.

## Implementation

Forward `~/Library/Logs/DiagnosticReports/` and `/Library/Logs/DiagnosticReports/`. Use `monitor` input in `inputs.conf`. Parse process name and exception type from crash reports.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder with a file monitor of DiagnosticReports.
• Ensure the following data sources are available: `/Library/Logs/DiagnosticReports/*.crash` (and optionally per-user paths if policy allows).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use `[monitor://]` stanzas for the crash log directories, with `sourcetype=macos_crash` (or your name). The forwarder on macOS reads these as text; ensure full-disk access if the OS requires it for the forwarder. This path is for Apple crash logs, not host CPU or memory metrics from other platforms.

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

**Pipeline walkthrough**

• Scopes the data: `index=os`, `sourcetype=macos_crash`.
• `rex` pulls the `Process:` name for grouping.
• `stats` and `sort` list the hottest `(host, process)` pairs.


Step 3 — Validate
Trigger a test crash in a non-production app and confirm one event with an expected `process` in Search. For full details, see the Implementation guide: docs/implementation-guide.md

Step 4 — Operationalize
Set thresholds on `count` per host and process for paging vs. triage. Consider visualizations: Table (process, host, count), Bar chart of top crashing apps.

## SPL

```spl
index=os sourcetype=macos_crash host=*
| rex "Process:\s+(?<process>\S+)"
| stats count by host, process
| sort -count
```

## CIM SPL

```spl
N/A — application crash reports from macOS are not a standard CIM object; use raw events with a custom sourcetype and fields extracted from the `.crash` text.
```

## Visualization

Table (process, host, count), Bar chart of top crashing apps.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
