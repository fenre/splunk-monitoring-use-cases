---
id: "1.1.62"
title: "Network Bandwidth Utilization by Interface (Linux)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.62 · Network Bandwidth Utilization by Interface (Linux)

## Description

High bandwidth utilization indicates potential capacity constraints or unexpected traffic patterns.

## Value

High bandwidth utilization indicates potential capacity constraints or unexpected traffic patterns.

## Implementation

Use Splunk_TA_nix interfaces input to track bytes in/out. Calculate bandwidth percentage based on interface speed. Create alerts for sustained utilization above 70% or unexpected spikes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=interfaces`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Splunk_TA_nix interfaces input to track bytes in/out. Calculate bandwidth percentage based on interface speed. Create alerts for sustained utilization above 70% or unexpected spikes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=interfaces host=*
| stats latest(bytes_in) as latest_in, earliest(bytes_in) as earliest_in by host, interface
| eval bytes_transferred=(latest_in-earliest_in)
| stats sum(bytes_transferred) as total_bytes by host
| eval bandwidth_util_pct=(total_bytes/interface_capacity_bits)*100
```

Understanding this SPL

**Network Bandwidth Utilization by Interface (Linux)** — High bandwidth utilization indicates potential capacity constraints or unexpected traffic patterns.

Documented **Data sources**: `sourcetype=interfaces`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: interfaces. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=interfaces. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, interface** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **bytes_transferred** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **bandwidth_util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

Understanding this CIM / accelerated SPL

**Network Bandwidth Utilization by Interface (Linux)** — High bandwidth utilization indicates potential capacity constraints or unexpected traffic patterns.

Documented **Data sources**: `sourcetype=interfaces`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Heatmap

## SPL

```spl
index=os sourcetype=interfaces host=*
| stats latest(bytes_in) as latest_in, earliest(bytes_in) as earliest_in by host, interface
| eval bytes_transferred=(latest_in-earliest_in)
| stats sum(bytes_transferred) as total_bytes by host
| eval bandwidth_util_pct=(total_bytes/interface_capacity_bits)*100
```

## CIM SPL

```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

## Visualization

Timechart, Heatmap

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
