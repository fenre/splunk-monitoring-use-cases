---
id: "5.1.21"
title: "CRC Error Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.21 · CRC Error Trending

## Description

Increasing CRC errors indicate failing cables, SFPs, or electromagnetic interference. Early detection prevents link failures.

## Value

Increasing CRC errors indicate failing cables, SFPs, or electromagnetic interference. Early detection prevents link failures.

## Implementation

Poll IF-MIB counters every 300s. Use `streamstats` to compute deltas. Trend over days to detect worsening interfaces. Cross-reference with interface utilization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP Modular Input, IF-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=snmp:interface`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll IF-MIB counters every 300s. Use `streamstats` to compute deltas. Trend over days to detect worsening interfaces. Cross-reference with interface utilization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifInErrors) as prev_errors, last(_time) as prev_time by host, ifDescr
| eval error_rate=(ifInErrors-prev_errors)/(_time-prev_time)
| where error_rate > 0
| timechart span=1h avg(error_rate) by host limit=20
```

Understanding this SPL

**CRC Error Trending** — Increasing CRC errors indicate failing cables, SFPs, or electromagnetic interference. Early detection prevents link failures.

Documented **Data sources**: `sourcetype=snmp:interface`. **App/TA** (typical add-on context): SNMP Modular Input, IF-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:interface. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:interface". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `streamstats` rolls up events into metrics; results are split **by host, ifDescr** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **error_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_rate > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by host limit=20** — ideal for trending and alerting on this use case.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (error rate over time per interface), Heatmap (device × interface), Table.

## SPL

```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifInErrors) as prev_errors, last(_time) as prev_time by host, ifDescr
| eval error_rate=(ifInErrors-prev_errors)/(_time-prev_time)
| where error_rate > 0
| timechart span=1h avg(error_rate) by host limit=20
```

## Visualization

Line chart (error rate over time per interface), Heatmap (device × interface), Table.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
