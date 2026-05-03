<!-- AUTO-GENERATED from UC-5.1.64.json — DO NOT EDIT -->

---
id: "5.1.64"
title: "Aruba CX VSX Redundancy Monitoring (HPE Aruba)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.64 · Aruba CX VSX Redundancy Monitoring (HPE Aruba)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know early when something looks wrong with aruba cx vsx redundancy monitoring so the team can act before it grows into a bigger outage.*

---

## Description

VSX pairs use an inter-switch link and keepalive; if both fail, split-brain can leave two active primaries forwarding independently, risking loops, duplicate MACs, and hard-to-diagnose application errors. Monitoring ISL, keepalive, and synchronization state is essential for data center and campus cores where VSX fronts servers or downstream stacks. Splunk lets you alert before both control and data paths degrade past recovery.

## Value

NOC teams monitor HPE Aruba CX VSX redundancy health including ISL, keepalive, and peer status, detecting split-brain conditions that cause dual-active forwarding inconsistencies.

## Implementation

Prefer synchronized clocks on VSX peers. Critical alert on keepalive loss, ISL down, or explicit split-brain / dual-primary messages. For SNMP, forward traps to Splunk and map OID to human-readable VSX state in `transforms.conf`. Correlate both peers’ logs into one notable event using a lookup of VSX pairs.

## Detailed Implementation

### Prerequisites
* HPE Aruba CX VSX (Virtual Switching Extension) redundancy data from syslog. Data in `index=aruba` or `index=network` with `sourcetype=aruba:cx`. Key syslog: VSX ISL status, keepalive status, device role, split-brain detection.
* Aruba CX VSX: two AOS-CX switches form a redundant pair providing active-active multi-chassis LAG. Unlike VSF stacking, VSX maintains independent control planes on each switch. Uses Inter-Switch Link (ISL) for data synchronization and keepalive link for peer health monitoring.

### Step 1 — - Configure data collection
```
# AOS-CX -- VSX events are logged via syslog
logging <splunk-ip> severity info
```
Verify:
```spl
index=aruba sourcetype="aruba:cx" earliest=-30d
| where match(_raw, "(?i)VSX|vsx|ISL|keepalive|split.brain|peer")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- VSX redundancy monitoring:**
```spl
index=aruba sourcetype="aruba:cx" earliest=-24h
| where match(_raw, "(?i)VSX|vsx|ISL|keepalive|split.brain|peer.*status")
| eval device=coalesce(host, device_name)
| eval vsx_event=case(
    match(_raw, "(?i)ISL.*down|inter.switch.*link.*down"), "ISL_DOWN",
    match(_raw, "(?i)ISL.*up|inter.switch.*link.*up"), "ISL_UP",
    match(_raw, "(?i)keepalive.*fail|keepalive.*timeout|keepalive.*down"), "KEEPALIVE_FAIL",
    match(_raw, "(?i)keepalive.*up|keepalive.*restore"), "KEEPALIVE_UP",
    match(_raw, "(?i)split.brain|dual.*active"), "SPLIT_BRAIN",
    match(_raw, "(?i)peer.*down|peer.*unreachable"), "PEER_DOWN",
    match(_raw, "(?i)peer.*up|peer.*active"), "PEER_UP",
    match(_raw, "(?i)role.*change|primary.*secondary|secondary.*primary"), "ROLE_CHANGE",
    1==1, "VSX_EVENT")
| stats count as events count(eval(vsx_event="ISL_DOWN")) as isl_downs count(eval(vsx_event="KEEPALIVE_FAIL")) as ka_fails count(eval(vsx_event="SPLIT_BRAIN")) as split_brains count(eval(vsx_event="PEER_DOWN")) as peer_downs latest(vsx_event) as latest_event by device
| eval severity=case(
    split_brains > 0, "CRITICAL -- VSX split-brain detected (dual active)",
    peer_downs > 0, "CRITICAL -- VSX peer down",
    isl_downs > 0, "CRITICAL -- VSX ISL down (no data sync)",
    ka_fails > 0, "WARNING -- VSX keepalive failure",
    1==1, "OK")
| where severity != "OK"
| sort severity
```

### Step 3 — - Validate
(a) CLI: `show vsx status` -- VSX overall status, role, and peer.
(b) CLI: `show vsx brief` -- ISL, keepalive, and sync status.
(c) CLI: `show lacp interfaces` -- LAG status for VSX multi-chassis LAGs.

### Step 4 — - Operationalize
Dashboard ("Aruba CX -- VSX Redundancy"):
* Row 1 -- Single-value: "VSX status", "ISL status", "Keepalive status".
* Row 2 -- VSX event timeline.

Alert: Critical (ISL down, peer down, or split-brain): immediate investigation.

### Step 5 — - Troubleshooting

* **ISL down** -- Data synchronization lost. Check ISL physical connectivity (usually LAG of multiple links). Verify: `show vsx status` and `show interface lag <id>`.

* **Keepalive failure** -- Peer health monitoring lost. If ISL is also down, split-brain risk. Check keepalive link (dedicated or routed). Verify: `show vsx keepalive`.

* **Split-brain** -- Both switches operate independently. Dangerous: duplicate IPs, inconsistent forwarding. Resolution: restore ISL and keepalive links. The secondary switch will relinquish active role upon ISL recovery.

## SPL

```spl
index=network (sourcetype=syslog OR sourcetype=snmptrapd OR sourcetype="snmp:trap")
| search "VSX" OR "Inter-Switch" OR "ISL" OR "keepalive" OR "split" OR "dual-primary" OR "InSync" OR "OutOfSync"
| rex field=_raw "(?i)VSX\s*[:,-]\s*(?<vsx_detail>[^\n]+)"
| stats count as vsx_events, latest(vsx_detail) as last_detail, latest(_raw) as sample by host
| sort -vsx_events
```

## Visualization

VSX pair health dashboard; ISL and keepalive status indicators; timeline of sync state changes.

## Known False Positives

Inter-switch link work and MCLAG role changes can raise VSX warnings until the fabric reconverges. Keep maintenance windows in the alert path.

## References

- [Splunkbase app 7523](https://splunkbase.splunk.com/app/7523)
- [Splunkbase app 2846](https://splunkbase.splunk.com/app/2846)
- [Splunkbase app 2847](https://splunkbase.splunk.com/app/2847)
