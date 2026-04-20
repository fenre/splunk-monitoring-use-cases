---
id: "5.8.8"
title: "SNMP Polling Gap Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.8 · SNMP Polling Gap Detection

## Description

Missing SNMP polls create gaps in monitoring data. Detecting polling failures ensures metrics dashboards remain accurate.

## Value

Missing SNMP polls create gaps in monitoring data. Detecting polling failures ensures metrics dashboards remain accurate.

## Implementation

Track SNMP data arrival per device using `tstats`. Compare expected vs. actual poll count. Alert when gap exceeds 20%. Investigate SNMP community/credential issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk core (metadata search).
• Ensure the following data sources are available: Any SNMP sourcetype.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track SNMP data arrival per device using `tstats`. Compare expected vs. actual poll count. Alert when gap exceeds 20%. Investigate SNMP community/credential issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| tstats count where index=network sourcetype="snmp:*" by host, sourcetype, _time span=10m
| stats range(_time) as time_range, count as poll_count by host, sourcetype
| eval expected_polls=round(time_range/300,0)
| eval gap_pct=round((1-poll_count/expected_polls)*100,1)
| where gap_pct > 20 | sort -gap_pct
```

Understanding this SPL

**SNMP Polling Gap Detection** — Missing SNMP polls create gaps in monitoring data. Detecting polling failures ensures metrics dashboards remain accurate.

Documented **Data sources**: Any SNMP sourcetype. **App/TA** (typical add-on context): Splunk core (metadata search). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:*. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Uses `tstats` against precomputed summaries; ensure the referenced data model is accelerated.
• `stats` rolls up events into metrics; results are split **by host, sourcetype** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **expected_polls** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **gap_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where gap_pct > 20` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, expected, actual, gap %), Single value (devices with gaps), Heatmap.

## SPL

```spl
| tstats count where index=network sourcetype="snmp:*" by host, sourcetype, _time span=10m
| stats range(_time) as time_range, count as poll_count by host, sourcetype
| eval expected_polls=round(time_range/300,0)
| eval gap_pct=round((1-poll_count/expected_polls)*100,1)
| where gap_pct > 20 | sort -gap_pct
```

## Visualization

Table (device, expected, actual, gap %), Single value (devices with gaps), Heatmap.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
