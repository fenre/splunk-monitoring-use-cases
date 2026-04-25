<!-- AUTO-GENERATED from UC-5.7.10.json — DO NOT EDIT -->

---
id: "5.7.10"
title: "Long-Duration Flow Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.7.10 · Long-Duration Flow Detection

## Description

Extremely long-lived flows may indicate data exfiltration, persistent backdoors, or stuck sessions consuming resources.

## Value

Extremely long-lived flows may indicate data exfiltration, persistent backdoors, or stuck sessions consuming resources.

## Implementation

Analyze flow records for duration >60 minutes. Cross-reference with known long-lived services (VPN, database replication). Flag unknown long flows for investigation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Stream, NetFlow integrator.
• Ensure the following data sources are available: `sourcetype=netflow`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Analyze flow records for duration >60 minutes. Cross-reference with known long-lived services (VPN, database replication). Flag unknown long flows for investigation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="netflow"
| eval duration_min=duration/60
| where duration_min > 60
| stats sum(bytes) as total_bytes, max(duration_min) as max_duration by src, dest, dest_port
| eval GB=round(total_bytes/1073741824,2) | sort -max_duration
| head 20
```

Understanding this SPL

**Long-Duration Flow Detection** — Extremely long-lived flows may indicate data exfiltration, persistent backdoors, or stuck sessions consuming resources.

Documented **Data sources**: `sourcetype=netflow`. **App/TA** (typical add-on context): Splunk Stream, NetFlow integrator. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: netflow. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="netflow". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **duration_min** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where duration_min > 60` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by src, dest, dest_port** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **GB** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` max(All_Traffic.duration) as max_dur sum(All_Traffic.bytes_in) as bi sum(All_Traffic.bytes_out) as bo
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| eval total_bytes=bi+bo, duration_min=max_dur/60
| where duration_min > 60
| sort -max_dur
```

Understanding this CIM / accelerated SPL

**Long-Duration Flow Detection** — Extremely long-lived flows may indicate data exfiltration, persistent backdoors, or stuck sessions consuming resources.

Documented **Data sources**: `sourcetype=netflow`. **App/TA** (typical add-on context): Splunk Stream, NetFlow integrator. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• `eval` defines or adjusts **bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Pick a long flow and compare `duration` and byte totals in Splunk to the same tuple on the flow exporter or a PCAP summary; confirm whether your field is seconds, milliseconds, or per-export slice.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (source, destination, port, duration, bytes), Scatter plot (duration vs. bytes).

## SPL

```spl
index=network sourcetype="netflow"
| eval duration_min=duration/60
| where duration_min > 60
| stats sum(bytes) as total_bytes, max(duration_min) as max_duration by src, dest, dest_port
| eval GB=round(total_bytes/1073741824,2) | sort -max_duration
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` max(All_Traffic.duration) as max_dur sum(All_Traffic.bytes_in) as bi sum(All_Traffic.bytes_out) as bo
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| eval total_bytes=bi+bo, duration_min=max_dur/60
| where duration_min > 60
| sort -max_dur
```

## Visualization

Table (source, destination, port, duration, bytes), Scatter plot (duration vs. bytes).

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
