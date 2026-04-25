<!-- AUTO-GENERATED from UC-5.7.6.json — DO NOT EDIT -->

---
id: "5.7.6"
title: "Port Scan Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.7.6 · Port Scan Detection

## Description

Hosts scanning many ports on targets indicate reconnaissance, worm propagation, or vulnerability scanning.

## Value

Hosts scanning many ports on targets indicate reconnaissance, worm propagation, or vulnerability scanning.

## Implementation

Detect hosts connecting to >50 unique ports on a single target in 5 minutes. Alert with source and target details.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for NetFlow.
• Ensure the following data sources are available: NetFlow.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Detect hosts connecting to >50 unique ports on a single target in 5 minutes. Alert with source and target details.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=netflow
| stats dc(dest_port) as unique_ports by src, dest
| where unique_ports > 50
| sort -unique_ports
```

Understanding this SPL

**Port Scan Detection** — Hosts scanning many ports on targets indicate reconnaissance, worm propagation, or vulnerability scanning.

Documented **Data sources**: NetFlow. **App/TA** (typical add-on context): Splunk Add-on for NetFlow. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: netflow.

**Pipeline walkthrough**

• Scopes the data: index=netflow. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by src, dest** so each row reflects one combination of those dimensions.
• Filters the current rows with `where unique_ports > 50` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` dc(All_Traffic.dest_port) as unique_ports
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest span=1h
| where unique_ports > 50
| sort -unique_ports
```

Understanding this CIM / accelerated SPL

**Port Scan Detection** — Hosts scanning many ports on targets indicate reconnaissance, worm propagation, or vulnerability scanning.

Documented **Data sources**: NetFlow. **App/TA** (typical add-on context): Splunk Add-on for NetFlow. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• `eval` defines or adjusts **bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Replay a test scan in a lab and confirm Splunk’s `src`/`dest`/`dest_port` coverage matches the generator; exclude vulnerability scanners and patch systems by allowlist in production.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Scatter plot, Timeline.

## SPL

```spl
index=netflow
| stats dc(dest_port) as unique_ports by src, dest
| where unique_ports > 50
| sort -unique_ports
```

## CIM SPL

```spl
| tstats `summariesonly` dc(All_Traffic.dest_port) as unique_ports
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest span=1h
| where unique_ports > 50
| sort -unique_ports
```

## Visualization

Table, Scatter plot, Timeline.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
