---
id: "1.1.86"
title: "Fork Bomb Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.86 · Fork Bomb Detection

## Description

Fork bombs exhaust PID space and system resources, making systems unusable.

## Value

Fork bombs exhaust PID space and system resources, making systems unusable.

## Implementation

Track /proc process count or 'ps aux | wc -l'. Create alerts when process count spikes suddenly. Include threshold based on baseline plus 4x standard deviation to detect sudden fork activity.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:process_count`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track /proc process count or 'ps aux | wc -l'. Create alerts when process count spikes suddenly. Include threshold based on baseline plus 4x standard deviation to detect sudden fork activity.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:process_count host=*
| stats avg(process_count) as avg_procs, stdev(process_count) as stddev by host
| where process_count > (avg_procs + 4*stddev)
```

Understanding this SPL

**Fork Bomb Detection** — Fork bombs exhaust PID space and system resources, making systems unusable.

Documented **Data sources**: `sourcetype=custom:process_count`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:process_count. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:process_count. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where process_count > (avg_procs + 4*stddev)` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Anomaly Chart

## SPL

```spl
index=os sourcetype=custom:process_count host=*
| stats avg(process_count) as avg_procs, stdev(process_count) as stddev by host
| where process_count > (avg_procs + 4*stddev)
```

## Visualization

Alert, Anomaly Chart

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
