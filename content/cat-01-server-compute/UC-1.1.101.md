<!-- AUTO-GENERATED from UC-1.1.101.json — DO NOT EDIT -->

---
id: "1.1.101"
title: "Context Switch Anomalies Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.101 · Context Switch Anomalies Detection

## Description

Context switch anomalies indicate scheduler issues or unexpected process workload changes.

## Value

Context switch anomalies indicate scheduler issues or unexpected process workload changes.

## Implementation

Use vmstat context switch field (`cs`) with statistical anomaly detection per host. Alert on 3-sigma deviations from the rolling baseline. Correlate with `ps`/`top` or service restarts for cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=vmstat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use vmstat context switch field with statistical anomaly detection. Alert on 3-sigma deviations from baseline. Include process state analysis (`top`, `pidstat`, `ps`) on Linux to identify cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=vmstat host=*
| bin _time span=5m
| stats avg(cs) as cs by host, _time
| eventstats avg(cs) as baseline stdev(cs) as stddev by host
| where cs > baseline + 3*stddev
```

Understanding this SPL

**Context Switch Anomalies Detection** — Context switch anomalies indicate scheduler issues or unexpected process workload changes.

Documented **Data sources**: `sourcetype=vmstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: vmstat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=vmstat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Buckets time into 5-minute bins, then averages **cs** (context switches per interval) per host and bucket.
• `eventstats` computes per-host mean and standard deviation of those bucketed averages so each row compares to its own recent history.
• Filters rows where the current bucket is more than three standard deviations above the mean—tune span and sigma as needed.

CIM does not expose raw `vmstat` context switches; keep this search on `sourcetype=vmstat`.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Anomaly Detector

## SPL

```spl
index=os sourcetype=vmstat host=*
| bin _time span=5m
| stats avg(cs) as cs by host, _time
| eventstats avg(cs) as baseline stdev(cs) as stddev by host
| where cs > baseline + 3*stddev
```

## Visualization

Timechart, Anomaly Detector

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
