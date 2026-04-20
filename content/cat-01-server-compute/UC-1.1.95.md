---
id: "1.1.95"
title: "TCP Connection Establishment Rate"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.1.95 · TCP Connection Establishment Rate

## Description

High connection establishment rate may indicate application behavior changes or DDoS attack preparation.

## Value

High connection establishment rate may indicate application behavior changes or DDoS attack preparation.

## Implementation

Monitor TcpActiveOpens from /proc/net/snmp. Track baseline and detect anomalies. Create alerts for sustained elevation in connection rate indicating potential DDoS or application issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:netstat_stats, /proc/net/snmp`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor TcpActiveOpens from /proc/net/snmp. Track baseline and detect anomalies. Create alerts for sustained elevation in connection rate indicating potential DDoS or application issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:netstat_stats host=*
| stats avg(TcpActiveOpens) as avg_active by host
| streamstats avg(avg_active) as baseline, stdev(avg_active) as stddev
| where avg_active > baseline + 3*stddev
```

Understanding this SPL

**TCP Connection Establishment Rate** — High connection establishment rate may indicate application behavior changes or DDoS attack preparation.

Documented **Data sources**: `sourcetype=custom:netstat_stats, /proc/net/snmp`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:netstat_stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:netstat_stats. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `streamstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• Filters the current rows with `where avg_active > baseline + 3*stddev` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Anomaly Chart

## SPL

```spl
index=os sourcetype=custom:netstat_stats host=*
| stats avg(TcpActiveOpens) as avg_active by host
| streamstats avg(avg_active) as baseline, stdev(avg_active) as stddev
| where avg_active > baseline + 3*stddev
```

## Visualization

Timechart, Anomaly Chart

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
