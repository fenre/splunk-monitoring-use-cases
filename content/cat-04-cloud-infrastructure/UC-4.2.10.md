---
id: "4.2.10"
title: "Storage Account Access Anomalies"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.2.10 · Storage Account Access Anomalies

## Description

Unusual storage access patterns may indicate data exfiltration or compromised service principals accessing sensitive data.

## Value

Unusual storage access patterns may indicate data exfiltration or compromised service principals accessing sensitive data.

## Implementation

Enable storage diagnostic logging. Baseline normal access patterns. Alert on volumetric anomalies (unusual number of reads/writes) or new source IPs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Storage analytics logs via Event Hub.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable storage diagnostic logging. Baseline normal access patterns. Alert on volumetric anomalies (unusual number of reads/writes) or new source IPs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="StorageRead" OR Category="StorageWrite"
| stats count by callerIpAddress, accountName, operationName
| eventstats avg(count) as avg_ops, stdev(count) as stdev_ops
| where count > avg_ops + (2 * stdev_ops)
```

Understanding this SPL

**Storage Account Access Anomalies** — Unusual storage access patterns may indicate data exfiltration or compromised service principals accessing sensitive data.

Documented **Data sources**: Storage analytics logs via Event Hub. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by callerIpAddress, accountName, operationName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• Filters the current rows with `where count > avg_ops + (2 * stdev_ops)` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (IP, account, operations), Line chart (access over time), Map.

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="StorageRead" OR Category="StorageWrite"
| stats count by callerIpAddress, accountName, operationName
| eventstats avg(count) as avg_ops, stdev(count) as stdev_ops
| where count > avg_ops + (2 * stdev_ops)
```

## Visualization

Table (IP, account, operations), Line chart (access over time), Map.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
