<!-- AUTO-GENERATED from UC-5.2.43.json — DO NOT EDIT -->

---
id: "5.2.43"
title: "Juniper SRX Cluster Failover Events (Juniper SRX)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.43 · Juniper SRX Cluster Failover Events (Juniper SRX)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We see cluster and routing daemon messages on the SRX so a planned or surprise failover is something you can explain with timestamps.*

---

## Description

Chassis-clustered SRX devices use redundancy groups (RGs) so services fail over when a node, link, or priority changes. JSRPD and cluster-related messages record RG ownership changes, interface monitoring triggers, and manual switchovers. Frequent or flapping failovers point to unstable fabric links, NIC or RE problems, or split-brain risk. Tracking RG state, reason strings, and duration helps you distinguish planned maintenance from emerging hardware or path faults.

## Value

NOC teams track Juniper SRX chassis cluster failover events, identifying node failures, interface-triggered failovers, and cluster flapping to maintain firewall high availability.

## Implementation

Forward cluster member syslogs with millisecond timestamps and synchronized NTP. Alert on any RG primary change, interface monitoring-driven failover, or unexpected preempt. Dashboard current RG primary per cluster ID and correlate with interface `up`/`down` events on fabric/control links. For active/active designs, track both RGs independently. Keep runbooks for manual `request chassis cluster failover` versus automatic events.

## Detailed Implementation

### Prerequisites
* Juniper SRX chassis cluster failover event logs. Data in `index=juniper` or `index=firewall` with `sourcetype=juniper:srx:structured`. Key fields: `redundancy_group`, `cluster_id`, `failover_reason`, `node` (node0/node1), `priority`.
* SRX chassis cluster: two SRX devices in active/passive or active/active configuration using redundancy groups (RGs). RG0 controls the routing engine; RG1+ controls data plane. Failover occurs when a node's priority drops below the peer (due to interface failure, manual preempt, or node failure). Monitored via `show chassis cluster status`.

### Step 1 — - Configure data collection
```
# SRX configuration -- chassis cluster (already configured)
# Verify cluster status
show chassis cluster status
show chassis cluster interfaces

# Enable logging for cluster events
set security log stream splunk-stream category all
set system syslog host <splunk-ip> any info
set system syslog host <splunk-ip> match "CHASSISD|jsrpd|JSRP|RG_CHANGE|failover"
```
Verify:
```spl
index=juniper sourcetype="juniper:srx:*" earliest=-30d
| where match(_raw, "(?i)JSRP|jsrpd|RG_CHANGE|failover|chassis.cluster|redundancy.group|node.*priority")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Cluster failover event tracking:**
```spl
index=juniper sourcetype="juniper:srx:*" earliest=-30d
| where match(_raw, "(?i)JSRP|jsrpd|RG_CHANGE|failover|redundancy.group|priority.*change")
| eval cluster_node=coalesce(node, if(match(host, "node0"), "node0", if(match(host, "node1"), "node1", "unknown")))
| eval rg=coalesce(redundancy_group, mvindex(split(_raw, "redundancy-group "), 1))
| eval failover_type=case(
    match(_raw, "(?i)manual"), "MANUAL",
    match(_raw, "(?i)interface.*down|link.*down|control.*link"), "INTERFACE_FAILURE",
    match(_raw, "(?i)node.*reboot|node.*down|heartbeat.*lost"), "NODE_FAILURE",
    match(_raw, "(?i)preempt"), "PREEMPT",
    match(_raw, "(?i)priority.*change|weight.*decrease"), "PRIORITY_CHANGE",
    1==1, "UNKNOWN")
| sort _time
| streamstats current=f last(_time) as prev_time by host
| eval time_since_last_min=round((_time - prev_time)/60, 1)
| stats count as failover_events count(eval(failover_type="NODE_FAILURE")) as node_failures count(eval(failover_type="INTERFACE_FAILURE")) as if_failures latest(failover_type) as last_type latest(_time) as last_failover by host, cluster_node
| eval severity=case(
    node_failures > 0, "CRITICAL -- node failure detected",
    failover_events > 3, "WARNING -- frequent failovers (possible flapping)",
    if_failures > 0, "WARNING -- interface-triggered failover",
    1==1, "INFO")
| where severity != "INFO"
| eval last_failover_time=strftime(last_failover, "%Y-%m-%d %H:%M:%S")
| table host, cluster_node, failover_events, node_failures, if_failures, last_type, last_failover_time, severity
| sort severity
```

### Step 3 — - Validate
(a) CLI: `show chassis cluster status` -- verify current primary/secondary roles per RG.
(b) CLI: `show chassis cluster statistics` -- check heartbeat and probe stats.
(c) CLI: `show chassis cluster control-plane statistics` -- verify fabric link health.

### Step 4 — - Operationalize
Dashboard ("Juniper SRX -- Cluster Health"):
* Row 1 -- Single-value: "Failover events (30d)", "Node failures", "Current primary node".
* Row 2 -- Cluster failover event timeline.
* Row 3 -- Failover type distribution.

Alert: Critical (node failure): immediate hardware investigation.
Warning (>3 failovers in 24h): investigate for flapping.

### Step 5 — - Troubleshooting

* **Cluster flapping** -- Check fabric links (fab0/fab1) and control link health: `show chassis cluster control-plane statistics`. Split-brain can occur if fabric links fail.

* **Unexpected failover** -- Check interface monitoring: `show chassis cluster interfaces`. If a monitored interface goes down, the RG priority decreases triggering failover. Verify `redundancy-group weight` configuration.

* **Split-brain / dual-primary** -- Both nodes think they are primary. Usually caused by fabric link failure. Immediate action: manually disable one node with `request chassis cluster failover node <x> redundancy-group <rg>`.

## SPL

```spl
index=network sourcetype="juniper:junos:structured"
  (lower(process)="jsrpd" OR match(_raw, "(?i)chassis cluster|redundancy group|RG-\d+|failover|switchover"))
| rex "(?i)redundancy group (?<rg_id>\d+)"
| rex "(?i)Reason:\s*(?<failover_reason>[^\|]+)"
| rex "(?i)interface (?<ifname>\S+) (?<if_state>up|down)"
| table _time host rg_id failover_reason ifname if_state process _raw
| sort -_time
```

## Visualization

Timeline (failover markers), Table (RG, reason, node), Status panel (current primary per cluster).

## Known False Positives

Rehearsed failover, firmware upgrades, and fabric events can make cluster state messages spike during maintenance.

## References

- [Splunkbase app 2847](https://splunkbase.splunk.com/app/2847)
