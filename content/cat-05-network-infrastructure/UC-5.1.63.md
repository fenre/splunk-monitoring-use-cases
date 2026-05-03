<!-- AUTO-GENERATED from UC-5.1.63.json — DO NOT EDIT -->

---
id: "5.1.63"
title: "Aruba CX VSF Stack Health (HPE Aruba)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.63 · Aruba CX VSF Stack Health (HPE Aruba)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know early when something looks wrong with aruba cx vsf stack health so the team can act before it grows into a bigger outage.*

---

## Description

VSF stacks present one logical switch; member loss or conductor changes can isolate access VLANs or reduce east-west capacity without a full box failure. Early detection of member state changes and inter-switch link issues prevents prolonged segments of a floor or IDF running on a single surviving member. Splunk gives stack-level visibility where SNMP polling alone may lag during control-plane events.

## Value

NOC teams monitor HPE Aruba CX VSF stack health, detecting member losses, stack link failures, and stack splits that reduce available ports and break unified management.

## Implementation

Send CX switch syslog to a dedicated VIP or SC4S; tag `host` or `orig_host` so searches can narrow to CX models. Filter false positives from non-CX syslog sharing the index. Alert on member down, split stack indicators, or repeated conductor re-election. Cross-check with `show vsf` if you ingest periodic CLI or API snapshots.

## Detailed Implementation

### Prerequisites
* HPE Aruba CX VSF (Virtual Switching Framework) stack health data from syslog. Data in `index=aruba` or `index=network` with `sourcetype=aruba:cx` or `sourcetype=syslog`. Key syslog: VSF member events, stack role changes, stack link status.
* Aruba CX VSF: physical stacking of AOS-CX switches (up to 10 members) into a single virtual switch. Stack uses dedicated VSF links for inter-member communication. Conductor (master) is elected from members. Member failure reduces available ports; stack link failure may split the stack.

### Step 1 — - Configure data collection
```
# AOS-CX configuration -- syslog forwarding
logging <splunk-ip> severity info
logging facility local7

# VSF events are included in system logging
```
Verify:
```spl
index=aruba sourcetype="aruba:cx" earliest=-30d
| where match(_raw, "(?i)VSF|vsf|stack|member.*join|member.*leave|conductor")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- VSF stack health monitoring:**
```spl
index=aruba sourcetype="aruba:cx" earliest=-30d
| where match(_raw, "(?i)VSF|vsf|stack|member.*join|member.*leave|conductor|split|vsf.*link")
| eval device=coalesce(host, device_name)
| eval vsf_event=case(
    match(_raw, "(?i)member.*leave|member.*down|member.*lost|member.*fail"), "MEMBER_LOST",
    match(_raw, "(?i)member.*join|member.*add|member.*up"), "MEMBER_JOINED",
    match(_raw, "(?i)vsf.*link.*down|stack.*link.*down"), "STACK_LINK_DOWN",
    match(_raw, "(?i)vsf.*link.*up|stack.*link.*up"), "STACK_LINK_UP",
    match(_raw, "(?i)split|partition|fragment"), "STACK_SPLIT",
    match(_raw, "(?i)conductor.*change|master.*change|role.*change"), "CONDUCTOR_CHANGE",
    1==1, "VSF_EVENT")
| stats count as events count(eval(vsf_event="MEMBER_LOST")) as members_lost count(eval(vsf_event="STACK_SPLIT")) as splits count(eval(vsf_event="STACK_LINK_DOWN")) as link_downs latest(vsf_event) as latest_event by device
| eval severity=case(
    splits > 0, "CRITICAL -- VSF stack split detected",
    members_lost > 0, "CRITICAL -- VSF member lost",
    link_downs > 0, "WARNING -- VSF stack link down (reduced redundancy)",
    1==1, "OK")
| where severity != "OK"
| sort severity
```

### Step 3 — - Validate
(a) CLI: `show vsf` -- VSF status overview (members, roles, topology).
(b) CLI: `show vsf member` -- per-member status and serial.
(c) CLI: `show vsf link` -- VSF inter-member link status.

### Step 4 — - Operationalize
Dashboard ("Aruba CX -- VSF Stack"):
* Row 1 -- Single-value: "VSF members online", "Members lost", "Stack splits".
* Row 2 -- VSF event timeline.

Alert: Critical (stack split or member lost): immediate investigation.

### Step 5 — - Troubleshooting

* **VSF member lost** -- Check: (1) power to the member, (2) VSF cable connections, (3) member LED indicators. Try: `vsf member <id> reboot` to recover.

* **Stack split** -- VSF link failure causing isolated partitions. Both partitions may claim the same management IP. Reconnect VSF cables. Resolve by determining primary partition.

* **Conductor change** -- New conductor elected. May cause brief control plane interruption. Check: `show vsf` for election reason and current conductor.

## SPL

```spl
index=network sourcetype=syslog
| search "VSF" OR "Virtual Switching Framework" OR "stack" OR "conductor" OR "standby" OR "Member"
| search "Aruba" OR "6300" OR "6400" OR "8320" OR "8360" OR host="*cx*"
| rex field=_raw "(?i)member\s*(?<member_slot>\d+)"
| stats count as vsf_events, latest(_raw) as last_event by host, member_slot
| sort -vsf_events
```

## Visualization

Stack topology-style table (member ID, role, last event); timeline of conductor changes; heatmap of stacks with events.

## Known False Positives

Stack member joins, firmware alignment, and split scenarios during transport work look scary but are often controlled—use Aruba Central or CLI status as ground truth.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
