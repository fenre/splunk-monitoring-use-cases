---
id: "5.7.9"
title: "Unauthorized VLAN Traffic Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.7.9 · Unauthorized VLAN Traffic Detection

## Description

Traffic originating from or destined to unauthorized VLANs indicates misconfigured switch ports, VLAN hopping attacks, or rogue devices.

## Value

Traffic originating from or destined to unauthorized VLANs indicates misconfigured switch ports, VLAN hopping attacks, or rogue devices.

## Implementation

Map flow data to VLANs via input interface. Maintain a lookup of authorized VLANs per port. Alert on traffic from unauthorized VLANs. Correlate with 802.1X status.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Stream, NetFlow integrator.
• Ensure the following data sources are available: `sourcetype=netflow`, `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map flow data to VLANs via input interface. Maintain a lookup of authorized VLANs per port. Alert on traffic from unauthorized VLANs. Correlate with 802.1X status.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="netflow"
| lookup vlan_authorization_lookup src_vlan OUTPUT authorized
| where authorized!="yes" OR isnull(authorized)
| stats sum(bytes) as bytes, dc(src) as unique_hosts by src_vlan, input_interface
| sort -bytes
```

Understanding this SPL

**Unauthorized VLAN Traffic Detection** — Traffic originating from or destined to unauthorized VLANs indicates misconfigured switch ports, VLAN hopping attacks, or rogue devices.

Documented **Data sources**: `sourcetype=netflow`, `sourcetype=cisco:ios`. **App/TA** (typical add-on context): Splunk Stream, NetFlow integrator. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: netflow. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="netflow". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where authorized!="yes" OR isnull(authorized)` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by src_vlan, input_interface** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

Understanding this CIM / accelerated SPL

**Unauthorized VLAN Traffic Detection** — Traffic originating from or destined to unauthorized VLANs indicates misconfigured switch ports, VLAN hopping attacks, or rogue devices.

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
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VLAN, interface, hosts, volume), Alert panel, Status grid.

## SPL

```spl
index=network sourcetype="netflow"
| lookup vlan_authorization_lookup src_vlan OUTPUT authorized
| where authorized!="yes" OR isnull(authorized)
| stats sum(bytes) as bytes, dc(src) as unique_hosts by src_vlan, input_interface
| sort -bytes
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

Table (VLAN, interface, hosts, volume), Alert panel, Status grid.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
