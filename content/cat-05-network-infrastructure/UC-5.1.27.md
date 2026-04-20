---
id: "5.1.27"
title: "Interface Error Rate Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.27 · Interface Error Rate Trending

## Description

CRC, runts, giants, input/output errors as rate over time.

## Value

CRC, runts, giants, input/output errors as rate over time.

## Implementation

Poll IF-MIB (ifInErrors, ifOutErrors) and EtherLike-MIB (dot3StatsFCSErrors) every 300s. Use streamstats for delta calculation. Alert when error rate exceeds threshold (e.g., >1/min on uplinks). Exclude admin-down interfaces.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: IF-MIB (ifInErrors, ifOutErrors), EtherLike-MIB.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll IF-MIB (ifInErrors, ifOutErrors) and EtherLike-MIB (dot3StatsFCSErrors) every 300s. Use streamstats for delta calculation. Alert when error rate exceeds threshold (e.g., >1/min on uplinks). Exclude admin-down interfaces.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=snmp:interface
| streamstats current=f last(ifInErrors) as prev_in, last(ifOutErrors) as prev_out, last(_time) as prev_time by host, ifDescr
| eval delta_in=ifInErrors-coalesce(prev_in,0), delta_out=ifOutErrors-coalesce(prev_out,0)
| eval interval_sec=_time-prev_time | where interval_sec>0 AND interval_sec<900
| eval in_err_rate=round(delta_in/interval_sec*60,2), out_err_rate=round(delta_out/interval_sec*60,2)
| where in_err_rate>0 OR out_err_rate>0
| timechart span=5m avg(in_err_rate) as in_errors_per_min, avg(out_err_rate) as out_errors_per_min by host
```

Understanding this SPL

**Interface Error Rate Trending** — CRC, runts, giants, input/output errors as rate over time.

Documented **Data sources**: IF-MIB (ifInErrors, ifOutErrors), EtherLike-MIB. **App/TA** (typical add-on context): SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:interface. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=snmp:interface. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `streamstats` rolls up events into metrics; results are split **by host, ifDescr** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **delta_in** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **interval_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where interval_sec>0 AND interval_sec<900` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **in_err_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where in_err_rate>0 OR out_err_rate>0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (error rate over time), Table (host, interface, rate), Heatmap.

## SPL

```spl
index=network sourcetype=snmp:interface
| streamstats current=f last(ifInErrors) as prev_in, last(ifOutErrors) as prev_out, last(_time) as prev_time by host, ifDescr
| eval delta_in=ifInErrors-coalesce(prev_in,0), delta_out=ifOutErrors-coalesce(prev_out,0)
| eval interval_sec=_time-prev_time | where interval_sec>0 AND interval_sec<900
| eval in_err_rate=round(delta_in/interval_sec*60,2), out_err_rate=round(delta_out/interval_sec*60,2)
| where in_err_rate>0 OR out_err_rate>0
| timechart span=5m avg(in_err_rate) as in_errors_per_min, avg(out_err_rate) as out_errors_per_min by host
```

## Visualization

Line chart (error rate over time), Table (host, interface, rate), Heatmap.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
