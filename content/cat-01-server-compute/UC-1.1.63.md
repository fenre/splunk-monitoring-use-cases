---
id: "1.1.63"
title: "Dropped Packets by Network Interface"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.63 · Dropped Packets by Network Interface

## Description

Dropped packets indicate network issues, buffer overflow, or driver problems affecting reliability.

## Value

Dropped packets indicate network issues, buffer overflow, or driver problems affecting reliability.

## Implementation

Monitor interface drop counters from /proc/net/dev or ethtool. Alert on any dropped packets, which should be zero in healthy networks. Correlate with driver errors and ring buffer exhaustion.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=interfaces`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor interface drop counters from /proc/net/dev or ethtool. Alert on any dropped packets, which should be zero in healthy networks. Correlate with driver errors and ring buffer exhaustion.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=interfaces host=*
| stats latest(dropped_in) as dropped_in, latest(dropped_out) as dropped_out by host, interface
| eval total_dropped=dropped_in+dropped_out
| where total_dropped > 0
| timechart sum(total_dropped) by host, interface
```

Understanding this SPL

**Dropped Packets by Network Interface** — Dropped packets indicate network issues, buffer overflow, or driver problems affecting reliability.

Documented **Data sources**: `sourcetype=interfaces`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: interfaces. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=interfaces. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, interface** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **total_dropped** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where total_dropped > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time with a separate series **by host, interface** — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

Understanding this CIM / accelerated SPL

**Dropped Packets by Network Interface** — Dropped packets indicate network issues, buffer overflow, or driver problems affecting reliability.

Documented **Data sources**: `sourcetype=interfaces`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Alert

## SPL

```spl
index=os sourcetype=interfaces host=*
| stats latest(dropped_in) as dropped_in, latest(dropped_out) as dropped_out by host, interface
| eval total_dropped=dropped_in+dropped_out
| where total_dropped > 0
| timechart sum(total_dropped) by host, interface
```

## CIM SPL

```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

## Visualization

Timechart, Alert

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
