<!-- AUTO-GENERATED from UC-6.1.27.json — DO NOT EDIT -->

---
id: "6.1.27"
title: "MDS Inter-Switch Link (ISL) Utilization"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.27 · MDS Inter-Switch Link (ISL) Utilization

## Description

ISLs carry all inter-switch SAN traffic. Saturated ISLs cause frame queuing, slow drain propagation, and storage latency spikes. Proactive monitoring prevents cascading congestion before hosts see I/O timeouts.

## Value

ISLs carry all inter-switch SAN traffic. Saturated ISLs cause frame queuing, slow drain propagation, and storage latency spikes. Proactive monitoring prevents cascading congestion before hosts see I/O timeouts.

## Implementation

Poll ISL port counters via SNMP every 60 seconds. Tag ISL ports in a lookup. Alert at 70% sustained utilization (5-min average). Correlate with storage latency (UC-6.1.2) and FC port errors (UC-6.1.9).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP TA, `cisco:mds` syslog.
• Ensure the following data sources are available: SNMP IF-MIB (ifHCInOctets/ifHCOutOctets on ISL ports), MDS syslog.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll ISL port counters via SNMP every 60 seconds. Tag ISL ports in a lookup. Alert at 70% sustained utilization (5-min average). Correlate with storage latency (UC-6.1.2) and FC port errors (UC-6.1.9).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:if" host="mds*" port_type="ISL"
| eval util_pct=round((ifHCInOctets_delta+ifHCOutOctets_delta)*8/speed/poll_interval*100,1)
| timechart span=5m avg(util_pct) as avg_util by switch, port
| where avg_util > 70
```

Understanding this SPL

**MDS Inter-Switch Link (ISL) Utilization** — ISLs carry all inter-switch SAN traffic. Saturated ISLs cause frame queuing, slow drain propagation, and storage latency spikes. Proactive monitoring prevents cascading congestion before hosts see I/O timeouts.

Documented **Data sources**: SNMP IF-MIB (ifHCInOctets/ifHCOutOctets on ISL ports), MDS syslog. **App/TA** (typical add-on context): SNMP TA, `cisco:mds` syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:if; **host** filter: mds*. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:if". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by switch, port** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_util > 70` — typically the threshold or rule expression for this monitoring goal.

Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Line chart (ISL utilization over time), Heatmap (switch x ISL port), Single value (peak ISL utilization), Topology map.

## SPL

```spl
index=network sourcetype="snmp:if" host="mds*" port_type="ISL"
| eval util_pct=round((ifHCInOctets_delta+ifHCOutOctets_delta)*8/speed/poll_interval*100,1)
| timechart span=5m avg(util_pct) as avg_util by switch, port
| where avg_util > 70
```

## Visualization

Line chart (ISL utilization over time), Heatmap (switch x ISL port), Single value (peak ISL utilization), Topology map.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
