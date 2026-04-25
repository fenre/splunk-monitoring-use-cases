<!-- AUTO-GENERATED from UC-5.7.4.json — DO NOT EDIT -->

---
id: "5.7.4"
title: "East-West Traffic Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.7.4 · East-West Traffic Monitoring

## Description

Lateral traffic between internal segments reveals application dependencies and detects lateral movement.

## Value

Lateral traffic between internal segments reveals application dependencies and detects lateral movement.

## Implementation

Export NetFlow from internal router/switch interfaces. Analyze internal traffic patterns. Establish baseline for anomaly detection.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for NetFlow.
• Ensure the following data sources are available: NetFlow from internal segments.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Export NetFlow from internal router/switch interfaces. Analyze internal traffic patterns. Establish baseline for anomaly detection.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=netflow
| where cidrmatch("10.0.0.0/8",src) AND cidrmatch("10.0.0.0/8",dest)
| stats sum(bytes) as bytes, count as flows by src, dest, dest_port
| sort -bytes | head 50
```

Understanding this SPL

**East-West Traffic Monitoring** — Lateral traffic between internal segments reveals application dependencies and detects lateral movement.

Documented **Data sources**: NetFlow from internal segments. **App/TA** (typical add-on context): Splunk Add-on for NetFlow. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: netflow.

**Pipeline walkthrough**

• Scopes the data: index=netflow. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where cidrmatch("10.0.0.0/8",src) AND cidrmatch("10.0.0.0/8",dest)` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by src, dest, dest_port** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out count as flows
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| eval bytes=bytes_in+bytes_out
| where cidrmatch("10.0.0.0/8", All_Traffic.src) AND cidrmatch("10.0.0.0/8", All_Traffic.dest)
| sort -bytes
| head 50
```

Understanding this CIM / accelerated SPL

**East-West Traffic Monitoring** — Lateral traffic between internal segments reveals application dependencies and detects lateral movement.

Documented **Data sources**: NetFlow from internal segments. **App/TA** (typical add-on context): Splunk Add-on for NetFlow. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• `eval` defines or adjusts **bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Validate a sample path against a packet capture or the exporting switch’s interface counters for the same subnet; confirm CIDRs match your internal addressing (replace `10.0.0.0/8` in both searches if you use other RFC1918 space).

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Chord diagram, Table, Sankey diagram.

## SPL

```spl
index=netflow
| where cidrmatch("10.0.0.0/8",src) AND cidrmatch("10.0.0.0/8",dest)
| stats sum(bytes) as bytes, count as flows by src, dest, dest_port
| sort -bytes | head 50
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out count as flows
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| eval bytes=bytes_in+bytes_out
| where cidrmatch("10.0.0.0/8", All_Traffic.src) AND cidrmatch("10.0.0.0/8", All_Traffic.dest)
| sort -bytes
| head 50
```

## Visualization

Chord diagram, Table, Sankey diagram.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
