<!-- AUTO-GENERATED from UC-5.3.34.json — DO NOT EDIT -->

---
id: "5.3.34"
title: "Citrix ADC Cluster Configuration Replication"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.34 · Citrix ADC Cluster Configuration Replication

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability

*We see cluster and sync style messages in one place so a split in configuration or a late peer is a dated fact, not a guess after tickets.*

---

## Description

A Citrix ADC cluster must keep a consistent configuration and routing view across members. If replication lags, quorum drifts, or a split is possible, different nodes can run divergent policy—bad for availability and for policy enforcement. The goal is to detect async failures and membership changes before a maintenance window or failure widens the gap.

## Value

Infrastructure teams monitor Citrix ADC cluster configuration replication, detecting sync failures and config mismatches that cause inconsistent traffic handling across cluster nodes.

## Implementation

Send cluster and nsync service logs to `index=netscaler`. If your deployment exposes a numeric lag metric via NITRO, mirror it in `citrix:netscaler:perf` for more precise SLO. Alert on any split-brain, repeated sync failures, or member departures outside change windows. Automate a ticket with last known `show cluster instance` if full context is in logs (mask secrets).

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC cluster syslog. Key fields: `cluster_node`, `node_state`, `config_sync_state`, `cluster_ip`, `clip_state`.
* Citrix ADC Cluster: multiple ADC nodes working as one. All nodes share the same configuration via cluster IP (CLIP). Configuration changes on CLIP propagate to all nodes. Sync failures mean nodes have different configs -- leading to inconsistent behavior.

### Step 1 — - Configure data collection
Verify cluster events:
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("cluster" OR "CLIP" OR "sync" OR "propagat" OR "node") earliest=-24h
| where match(_raw, "(?i)(sync|propagat|mismatch|fail|join|leave)")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Cluster config replication health:**
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("cluster" OR "CLIP" OR "sync" OR "propagat" OR "node") earliest=-4h
| eval event_type=case(match(_raw, "(?i)sync.*fail|propagat.*fail"), "SYNC_FAILURE", match(_raw, "(?i)mismatch|config.*differ"), "CONFIG_MISMATCH", match(_raw, "(?i)node.*join"), "NODE_JOIN", match(_raw, "(?i)node.*leave|node.*down"), "NODE_LEAVE", match(_raw, "(?i)sync.*success|propagat.*success"), "SYNC_SUCCESS", 1==1, null())
| where isnotnull(event_type)
| eval severity=case(event_type="SYNC_FAILURE", "HIGH -- config not propagating", event_type="CONFIG_MISMATCH", "HIGH -- nodes have different configs", event_type="NODE_LEAVE", "WARNING -- cluster member left", 1==1, "INFO")
| stats count as events latest(_time) as last_event by host, event_type, severity
| sort severity
```

### Step 3 — - Validate
(a) On ADC CLI: `show cluster instance` -- check node states and config sync status.
(b) Make a config change on CLIP and verify it propagates to all nodes.
(c) Check: `show cluster node` for individual node health.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- Cluster Health"):
* Row 1 -- Single-value: "Cluster nodes", "Sync failures", "Config mismatches", "Nodes active".
* Row 2 -- Cluster event history.

Alerting:
* High (config sync failure): nodes may have inconsistent configs.
* Warning (node left cluster): reduced cluster capacity.

### Step 5 — - Troubleshooting

* **Sync failure** -- Check: (1) network connectivity between nodes (cluster backplane), (2) cluster version mismatch (all nodes must be same firmware), (3) disk space on nodes.

* **Config mismatch** -- Force sync: `force cluster sync`. If that fails, check for conflicting configs.

* **Node won't rejoin** -- Check: (1) node state: `show cluster node <id>`, (2) network connectivity, (3) license status.

## SPL

```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("cluster" OR CLIP OR CCO OR NSYNC OR "quorum" OR "propagat" OR "split-brain" OR "split brain" OR "nsync" OR "replication" OR configsync OR "RHI")
| eval severity=if(match(_raw, "(?i)(split|mismatch|fail|unreachable)"),"high", if(match(_raw, "(?i)warn|lag|delay"),"medium","low"))
| rex field=_raw "(?i)cluster[\\s:]+(?<cluster_id>\\S+)"
| bin _time span=5m
| stats count as events, values(severity) as severities, latest(host) as node by _time, cluster_id, host
| where like(mvjoin(severities, " "), "%high%") OR like(mvjoin(severities, " "), "%medium%")
| table _time, cluster_id, host, node, severities, events
```

## Visualization

State timeline: cluster size and roles, time chart: sync-failure count, list: members with last heartbeat string.

## Known False Positives

Rehearsals, boot order, and network reachability can make cluster messages noisy without split brain.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — High availability and clustering](https://docs.citrix.com/en-us/citrix-adc/current-release/getting-started-with-citrix-adc/)
