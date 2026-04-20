---
id: "2.1.4"
title: "Datastore Latency Spikes"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.4 · Datastore Latency Spikes

## Description

Storage latency >20ms significantly impacts VM performance. Detects SAN issues, datastore contention, or storage path problems before applications are affected.

## Value

Storage latency >20ms significantly impacts VM performance. Detects SAN issues, datastore contention, or storage path problems before applications are affected.

## Implementation

Collected via TA-vmware. Alert when average read/write latency exceeds 20ms over 10 minutes. Correlate with IOPS and throughput counters for full picture.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:perf:datastore`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collected via TA-vmware. Alert when average read/write latency exceeds 20ms over 10 minutes. Correlate with IOPS and throughput counters for full picture.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:perf:datastore" (counter="datastore.totalReadLatency.average" OR counter="datastore.totalWriteLatency.average")
| eval latency_ms = Value
| stats avg(latency_ms) as avg_latency, max(latency_ms) as peak_latency by host, datastore, counter
| where avg_latency > 20
| sort -avg_latency
```

Understanding this SPL

**Datastore Latency Spikes** — Storage latency >20ms significantly impacts VM performance. Detects SAN issues, datastore contention, or storage path problems before applications are affected.

Documented **Data sources**: `sourcetype=vmware:perf:datastore`. **App/TA** (typical add-on context): `TA-vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:perf:datastore. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:perf:datastore". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, datastore, counter** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_latency > 20` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.read_latency) as read_ms avg(Performance.write_latency) as write_ms
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=5m
| eval worst_ms=max(read_ms, write_ms)
| where worst_ms > 20
```

Understanding this CIM / accelerated SPL

**Datastore Latency Spikes** — Storage latency >20ms significantly impacts VM performance. Detects SAN issues, datastore contention, or storage path problems before applications are affected.

Documented **Data sources**: `sourcetype=vmware:perf:datastore`. **App/TA** (typical add-on context): `TA-vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• `eval` defines or adjusts **worst_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where worst_ms > 20` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (latency over time), Heatmap (datastores vs. hosts), Table with avg/peak.

## SPL

```spl
index=vmware sourcetype="vmware:perf:datastore" (counter="datastore.totalReadLatency.average" OR counter="datastore.totalWriteLatency.average")
| eval latency_ms = Value
| stats avg(latency_ms) as avg_latency, max(latency_ms) as peak_latency by host, datastore, counter
| where avg_latency > 20
| sort -avg_latency
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.read_latency) as read_ms avg(Performance.write_latency) as write_ms
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=5m
| eval worst_ms=max(read_ms, write_ms)
| where worst_ms > 20
```

## Visualization

Line chart (latency over time), Heatmap (datastores vs. hosts), Table with avg/peak.

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
