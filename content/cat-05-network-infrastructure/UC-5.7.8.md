---
id: "5.7.8"
title: "Multicast Traffic Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.7.8 · Multicast Traffic Monitoring

## Description

Uncontrolled multicast traffic floods switches and consumes bandwidth. Monitoring ensures multicast storms are detected before impacting unicast traffic.

## Value

Uncontrolled multicast traffic floods switches and consumes bandwidth. Monitoring ensures multicast storms are detected before impacting unicast traffic.

## Implementation

Enable NetFlow on core/distribution switches. Filter for multicast destination range (224.0.0.0/4). Baseline expected multicast groups. Alert on new or high-volume groups.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Stream, NetFlow integrator.
• Ensure the following data sources are available: `sourcetype=netflow`, `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable NetFlow on core/distribution switches. Filter for multicast destination range (224.0.0.0/4). Baseline expected multicast groups. Alert on new or high-volume groups.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="netflow" dest="224.0.0.0/4"
| stats sum(bytes) as total_bytes, dc(src) as sources by dest
| eval MB=round(total_bytes/1048576,1) | sort -total_bytes
| head 20
```

Understanding this SPL

**Multicast Traffic Monitoring** — Uncontrolled multicast traffic floods switches and consumes bandwidth. Monitoring ensures multicast storms are detected before impacting unicast traffic.

Documented **Data sources**: `sourcetype=netflow`, `sourcetype=cisco:ios`. **App/TA** (typical add-on context): Splunk Stream, NetFlow integrator. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: netflow. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="netflow". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by dest** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **MB** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

Understanding this CIM / accelerated SPL

**Multicast Traffic Monitoring** — Uncontrolled multicast traffic floods switches and consumes bandwidth. Monitoring ensures multicast storms are detected before impacting unicast traffic.

Documented **Data sources**: `sourcetype=netflow`, `sourcetype=cisco:ios`. **App/TA** (typical add-on context): Splunk Stream, NetFlow integrator. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• `eval` defines or adjusts **bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (multicast group, volume, sources), Timechart (multicast volume), Bar chart.

## SPL

```spl
index=network sourcetype="netflow" dest="224.0.0.0/4"
| stats sum(bytes) as total_bytes, dc(src) as sources by dest
| eval MB=round(total_bytes/1048576,1) | sort -total_bytes
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

## Visualization

Table (multicast group, volume, sources), Timechart (multicast volume), Bar chart.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
