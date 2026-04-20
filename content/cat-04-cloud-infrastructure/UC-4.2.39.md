---
id: "4.2.39"
title: "Event Hub Capture Lag"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.2.39 · Event Hub Capture Lag

## Description

Capture to ADLS/Blob enables batch analytics; lag between enqueue and file availability delays downstream pipelines.

## Value

Capture to ADLS/Blob enables batch analytics; lag between enqueue and file availability delays downstream pipelines.

## Implementation

Ingest CaptureLag from Azure Monitor. Alert when lag exceeds SLA (for example 10 minutes). Check storage throttling and capture file naming collisions. Scale throughput units if needed.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Event Hub metrics (`CaptureLag`, incoming messages), storage write diagnostics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest CaptureLag from Azure Monitor. Alert when lag exceeds SLA (for example 10 minutes). Check storage throttling and capture file naming collisions. Scale throughput units if needed.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:metrics" resourceType="Microsoft.EventHub/namespaces" metric_name="CaptureLag"
| stats latest(average) as lag_ms by resourceId, bin(_time, 5m)
| where lag_ms > 600000
| eval lag_min=round(lag_ms/60000,1)
```

Understanding this SPL

**Event Hub Capture Lag** — Capture to ADLS/Blob enables batch analytics; lag between enqueue and file availability delays downstream pipelines.

Documented **Data sources**: Event Hub metrics (`CaptureLag`, incoming messages), storage write diagnostics. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:metrics, Microsoft.EventHub/namespaces. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resourceId, bin(_time, 5m)** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where lag_ms > 600000` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **lag_min** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (capture lag), Table (namespace, lag minutes), Single value (worst lag).

## SPL

```spl
index=azure sourcetype="mscs:azure:metrics" resourceType="Microsoft.EventHub/namespaces" metric_name="CaptureLag"
| stats latest(average) as lag_ms by resourceId, bin(_time, 5m)
| where lag_ms > 600000
| eval lag_min=round(lag_ms/60000,1)
```

## Visualization

Line chart (capture lag), Table (namespace, lag minutes), Single value (worst lag).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
