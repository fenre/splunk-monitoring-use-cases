<!-- AUTO-GENERATED from UC-5.1.58.json — DO NOT EDIT -->

---
id: "5.1.58"
title: "Junos Routing Engine Failover Monitoring (Juniper)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.58 · Junos Routing Engine Failover Monitoring (Juniper)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know early when something looks wrong with junos routing engine failover monitoring so the team can act before it grows into a bigger outage.*

---

## Description

Platforms with dual routing engines rely on GRES and related state transfer; an unplanned mastership change usually means primary RE failure, kernel panic, or loss of control-plane stability. Repeated failovers on the same chassis point to degrading hardware or software defects before a hard outage. Tracking these events in Splunk gives operations a single place to justify RMA, software upgrade, or emergency maintenance.

## Value

NOC teams monitor Juniper Routing Engine failover events, detecting crash-triggered switchovers and sync failures that indicate hardware issues requiring JTAC investigation.

## Implementation

Classify planned vs unplanned using maintenance windows or SNMP/CLI context if ingested. Critical alert on any mastership change outside a change window; warning if more than one event per chassis per 7 days. Attach device role (PE, core, aggregation) for prioritization.

## Detailed Implementation

### Prerequisites
* Junos Routing Engine (RE) failover events. Data in `index=juniper` with `sourcetype=juniper:structured`. Key syslog: `RPD_REDUNDANCY_RE_SWITCHOVER`, `KSYNCD_PEER_TIMEOUT`, `CHASSISD_RE_INIT_INVALID`.
* Juniper devices with dual Routing Engines (RE0/RE1) use Graceful Routing Engine Switchover (GRES) and Nonstop Active Routing (NSR) for hitless failover. RE failover is triggered by: RE crash, kernel panic, watchdog timeout, manual switchover, or RPD failure.

### Step 1 — - Configure data collection
```
# Junos -- redundancy is configured under routing-options
set chassis redundancy graceful-switchover
set routing-options nonstop-routing

set system syslog host <splunk-ip> any info
set system syslog host <splunk-ip> match "RPD_REDUNDANCY|KSYNCD|SWITCHOVER|RE_INIT|master|backup"
```
Verify:
```spl
index=juniper earliest=-30d
| where match(_raw, "(?i)SWITCHOVER|RE_SWITCHOVER|routing.*engine.*failover|master.*change|backup.*active")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Routing Engine failover monitoring:**
```spl
index=juniper earliest=-30d
| where match(_raw, "(?i)SWITCHOVER|RE_SWITCHOVER|routing.*engine.*failover|master.*backup|backup.*master|KSYNCD.*TIMEOUT|RE_INIT")
| eval device=coalesce(host, device_name)
| eval failover_type=case(
    match(_raw, "(?i)manual|admin"), "MANUAL",
    match(_raw, "(?i)crash|panic|core|exception|watchdog"), "CRASH",
    match(_raw, "(?i)KSYNCD.*TIMEOUT"), "SYNC_TIMEOUT",
    match(_raw, "(?i)RPD"), "RPD_FAILURE",
    1==1, "FAILOVER")
| eval re_from=case(match(_raw, "(?i)RE0.*master|master.*RE0"), "RE0", match(_raw, "(?i)RE1.*master|master.*RE1"), "RE1", 1==1, "unknown")
| stats count as events count(eval(failover_type="CRASH")) as crashes latest(failover_type) as last_type latest(_time) as last_failover by device
| eval severity=case(
    crashes > 0, "CRITICAL -- Routing Engine crash-triggered failover",
    events > 3, "WARNING -- frequent RE failovers",
    events > 0, "INFO -- RE failover occurred",
    1==1, "OK")
| where severity != "OK"
| eval last_failover_time=strftime(last_failover, "%Y-%m-%d %H:%M:%S")
| sort severity
```

### Step 3 — - Validate
(a) CLI: `show chassis routing-engine` -- check current RE master/backup status.
(b) CLI: `show system core-dumps` -- check for crash core files.
(c) CLI: `show krt state` -- verify kernel routing table sync status.

### Step 4 — - Operationalize
Dashboard ("Juniper -- RE Failover"):
* Row 1 -- Single-value: "RE failovers (30d)", "RE crashes", "Current master".
* Row 2 -- RE failover event timeline.

Alert: Critical (RE crash): collect core dump, open JTAC case.

### Step 5 — - Troubleshooting

* **RE crash** -- Collect: `file list /var/crash/` for core dumps. Run `show system core-dumps`. Open JTAC case with core file for analysis. Consider firmware upgrade if known bug.

* **KSYNCD timeout** -- Kernel sync between REs failed. Check: `show chassis routing-engine` for RE health. Possible RE hardware issue or backplane connectivity problem.

* **NSR not maintaining state** -- Verify NSR is configured: `show routing-options nonstop-routing`. Check: `show task replication` for replication status.

## SPL

```spl
index=network sourcetype="juniper:junos:structured"
| search SERD_MASTERSHIP OR RE_SWITCHOVER OR "mastership" OR "Routing Engine.*switch" OR "Become master"
| rex field=_raw "(?i)from\s+(?<old_role>\w+)\s+to\s+(?<new_role>\w+)"
| bin span=24h _time
| stats count as failover_events, values(_raw) as samples by host, _time
| where failover_events > 0
| sort -failover_events
```

## Visualization

Failover timeline per chassis; count of failovers per device last 30 days; list of recent raw messages for triage.

## Known False Positives

RE switchovers during hitless upgrades, GRES tests, and power work are normal when planned. Require sustained impact before escalation.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
