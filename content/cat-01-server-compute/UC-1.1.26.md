---
id: "1.1.26"
title: "CPU Frequency Scaling Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.26 · CPU Frequency Scaling Events

## Description

Frequency scaling changes indicate thermal throttling or power management adjustments affecting workload performance.

## Value

Frequency scaling changes indicate thermal throttling or power management adjustments affecting workload performance.

## Implementation

Monitor /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq for rapid changes. Create alerts when frequency scaling events occur frequently, indicating thermal or power issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=linux_audit OR custom:cpufreq`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq for rapid changes. Create alerts when frequency scaling events occur frequently, indicating thermal or power issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_audit path="/sys/devices/system/cpu/cpu*/cpufreq/*" action=modified
| stats count by host, path
| where count > 10
```

Understanding this SPL

**CPU Frequency Scaling Events** — Frequency scaling changes indicate thermal throttling or power management adjustments affecting workload performance.

Documented **Data sources**: `sourcetype=linux_audit OR custom:cpufreq`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, path** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Timeline

## SPL

```spl
index=os sourcetype=linux_audit path="/sys/devices/system/cpu/cpu*/cpufreq/*" action=modified
| stats count by host, path
| where count > 10
```

## Visualization

Table, Timeline

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
