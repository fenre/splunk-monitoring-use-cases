<!-- AUTO-GENERATED from UC-5.1.59.json — DO NOT EDIT -->

---
id: "5.1.59"
title: "Junos Virtual Chassis Health (Juniper)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.59 · Junos Virtual Chassis Health (Juniper)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know early when something looks wrong with junos virtual chassis health so the team can act before it grows into a bigger outage.*

---

## Description

Virtual Chassis merges multiple switches into one control plane; a member disconnect or role churn can blackhole VLANs or split forwarding across members. VCCP and member state messages are the earliest signal of stack cable, power, or software issues. Centralized monitoring reduces time to detect partial stack failures that users report as intermittent “random” connectivity loss.

## Value

NOC teams monitor Juniper Virtual Chassis health, detecting member losses, VC port failures, and VC splits that reduce switch fabric capacity and break single-chassis operation.

## Implementation

Baseline normal VCCP chatter; alert on member disconnect, not-primary transitions, or split-brain indicators per Juniper KB wording in your release. Correlate with interface errors on VCP ports. Map `host` to stack ID in a lookup for faster operator response.

## Detailed Implementation

### Prerequisites
* Juniper Virtual Chassis (VC) health data from syslog. Data in `index=juniper` with `sourcetype=juniper:structured`. Key syslog: `VC_*` messages, `VCCPD`, member join/leave, VC port status.
* Juniper Virtual Chassis: multiple physical switches operate as a single logical device. Members connected via VC ports (dedicated or uplink). Master RE elected from member pool. Member failures reduce available ports and may split the VC.

### Step 1 — - Configure data collection
```
# Junos -- Virtual Chassis logging
set system syslog host <splunk-ip> any info
set system syslog host <splunk-ip> match "VCCPD|VC_|virtual-chassis|member"
```
Verify:
```spl
index=juniper earliest=-30d
| where match(_raw, "(?i)VCCPD|VC_|virtual.chassis|member.*join|member.*leave|vc.*port")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Virtual Chassis health monitoring:**
```spl
index=juniper earliest=-30d
| where match(_raw, "(?i)VCCPD|VC_|virtual.chassis|member.*join|member.*leave|vc.*port.*down|split")
| eval device=coalesce(host, device_name)
| eval vc_event=case(
    match(_raw, "(?i)member.*leave|member.*down|member.*lost"), "MEMBER_LOST",
    match(_raw, "(?i)member.*join|member.*add|member.*up"), "MEMBER_JOINED",
    match(_raw, "(?i)vc.*port.*down|vcp.*down"), "VC_PORT_DOWN",
    match(_raw, "(?i)vc.*port.*up|vcp.*up"), "VC_PORT_UP",
    match(_raw, "(?i)split|partition"), "VC_SPLIT",
    match(_raw, "(?i)master.*change|mastership"), "MASTERSHIP_CHANGE",
    1==1, "VC_EVENT")
| stats count as events count(eval(vc_event="MEMBER_LOST")) as members_lost count(eval(vc_event="VC_SPLIT")) as splits count(eval(vc_event="VC_PORT_DOWN")) as vcp_downs by device
| eval severity=case(
    splits > 0, "CRITICAL -- Virtual Chassis split detected",
    members_lost > 0, "CRITICAL -- VC member lost",
    vcp_downs > 0, "WARNING -- VC port down (redundancy reduced)",
    1==1, "OK")
| where severity != "OK"
| sort severity
```

### Step 3 — - Validate
(a) CLI: `show virtual-chassis status` -- member list and roles (Master/Backup/Linecard).
(b) CLI: `show virtual-chassis vc-port` -- VC port status.
(c) CLI: `show virtual-chassis information` -- VC configuration mode.

### Step 4 — - Operationalize
Dashboard ("Juniper -- Virtual Chassis"):
* Row 1 -- Single-value: "VC members online", "Members lost", "VC splits".
* Row 2 -- VC health event timeline.

Alert: Critical (VC split or member lost): immediate investigation.

### Step 5 — - Troubleshooting

* **VC split** -- Members can no longer communicate. Check VC cable connections. Split-brain causes duplicate virtual IP/MAC. Resolve by reconnecting VC cables and resolving mastership.

* **Member lost** -- Check: (1) power to member, (2) VC cable connections, (3) member LED indicators. Try: `request virtual-chassis renumber`.

* **VC port down** -- Check VC cable integrity. VC ports use specific cable types (DAC, fiber). Replace cable and verify with `show virtual-chassis vc-port`.

## SPL

```spl
index=network sourcetype="juniper:junos:structured"
| search VCCPD OR "Virtual Chassis" OR "vcp-" OR "member.*state" OR "VC member"
| rex field=_raw "(?i)member\s+(?<member_id>\d+)"
| stats count as vc_events, dc(member_id) as members_seen, latest(_raw) as last_event by host
| sort -vc_events
```

## Visualization

VC member status matrix; event timeline for stack role changes; table of stacks with elevated event rate.

## Known False Positives

Chassis messages during FRU insertion, online diagnostics, and virtual chassis work are often expected. Follow vendor guidelines for one-shot vs sustained alarms.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
