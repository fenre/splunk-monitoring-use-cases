<!-- AUTO-GENERATED from UC-5.1.38.json — DO NOT EDIT -->

---
id: "5.1.38"
title: "Spanning Tree Protocol (STP) Topology Changes (Meraki MS)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.38 · Spanning Tree Protocol (STP) Topology Changes (Meraki MS)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with spanning tree protocol so the team can act before it grows into a bigger outage.*

---

## Description

Alerts on unexpected STP topology changes that indicate link failures or network configuration issues.

## Value

Network engineers monitor Meraki MS STP topology changes, root bridge stability, and BPDU guard violations to detect network loops and unauthorized switch connections.

## Implementation

Monitor STP-related syslog events. Alert on excessive topology changes.

## Detailed Implementation

### Prerequisites
* Meraki MS STP event data from syslog. Data in `index=meraki` with `sourcetype=meraki:events`. Key events: topology change, root bridge change, BPDU guard violations.
* Meraki MS uses RSTP (Rapid Spanning Tree Protocol) by default. STP topology changes are logged via syslog. Root bridge is automatically determined by bridge priority (lowest wins). Dashboard: Switch > STP shows root bridge and topology.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Network-wide > General > Reporting
# Syslog: enable Event log
# STP events are included in the event log
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-7d
| where match(_raw, "(?i)STP|spanning|topology|BPDU|root.*bridge")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- STP topology change monitoring:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)STP|spanning|topology.*change|BPDU|root")
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| eval stp_event=case(
    match(_raw, "(?i)topology.*change"), "TOPOLOGY_CHANGE",
    match(_raw, "(?i)root.*change|new.*root"), "ROOT_CHANGE",
    match(_raw, "(?i)BPDU.*guard|bpdu.*block"), "BPDU_GUARD",
    match(_raw, "(?i)loop.*detect|loop.*guard"), "LOOP_DETECTED",
    1==1, "STP_EVENT")
| bin _time span=5m
| stats count as events values(stp_event) as event_types by _time, network_name, device
| eval severity=case(
    match(mvjoin(event_types, ","), "ROOT_CHANGE"), "CRITICAL -- STP root bridge change",
    match(mvjoin(event_types, ","), "LOOP_DETECTED"), "CRITICAL -- loop detected",
    match(mvjoin(event_types, ","), "BPDU_GUARD"), "WARNING -- BPDU guard violation",
    events > 10, "WARNING -- excessive topology changes",
    1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

### Step 3 — - Validate
(a) Dashboard: Switch > STP -- check root bridge and port states.
(b) Verify RSTP is the active STP mode.
(c) Check for loop guard and BPDU guard configuration.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- STP"):
* Row 1 -- Single-value: "Topology changes (4h)", "Root bridge changes", "BPDU guard violations".
* Row 2 -- STP event timeline.

Alert: Critical (root bridge change or loop detection): immediate investigation.

### Step 5 — - Troubleshooting

* **Excessive topology changes** -- Flapping port. Check port status and connected device. Enable STP guard on access ports in Dashboard.

* **Loop detected** -- Physical loop in the network. Meraki will block the port. Investigate cabling. Check for unauthorized switches.

* **BPDU guard violation** -- Port received BPDUs when it shouldn't (access port). Unauthorized switch connected. Port will be disabled automatically.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*STP*" OR signature="*topology*")
| stats count as change_count by switch_name, change_type
| where change_count > 3
```

## Visualization

Timeline of topology changes; table of affected switches; alert dashboard.

## Known False Positives

STP TCNs happen during access switch adds, link moves, and voice VLAN changes. Storm-control tuning can also shift TC rates.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
