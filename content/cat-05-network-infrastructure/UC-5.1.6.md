<!-- AUTO-GENERATED from UC-5.1.6.json — DO NOT EDIT -->

---
id: "5.1.6"
title: "Spanning Tree Topology Change"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.6 · Spanning Tree Topology Change

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Anomaly

*We help you know early when something looks wrong with spanning tree topology change so the team can act before it grows into a bigger outage.*

---

## Description

STP topology changes cause brief disruption and MAC flushing. Root bridge changes are critical.

## Value

Network engineers monitor STP topology changes and root bridge stability, detecting excessive reconvergence events that cause MAC table flushes and broadcast flooding.

## Implementation

Forward syslog. Alert on root bridge changes (critical). Track topology change frequency per VLAN.

## Detailed Implementation

### Prerequisites
* STP topology change syslog messages. Data in `index=network` with `sourcetype=cisco:ios` or vendor-specific sourcetypes. Key mnemonics: Cisco `%SPANTREE-5-TOPOTRAP`, `%SPANTREE-2-ROOTGUARD_BLOCK`; standard STP TCN BPDUs.
* Spanning Tree topology changes: when a switch detects a link failure or new device, it generates a Topology Change Notification (TCN) that causes all switches to flush MAC address tables and re-learn. Excessive TCNs cause broadcast flooding and network instability.

### Step 1 — - Configure data collection
```
# Cisco IOS -- STP is logged by default via syslog
# Ensure spanning-tree logging is at informational level
logging host <splunk-syslog-ip>
logging trap informational

# Optional: enable STP event detail
spanning-tree logging
```
Verify:
```spl
index=network earliest=-24h
| where match(_raw, "(?i)SPANTREE|STP|topology.change|TCN|root.guard|BPDU")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- STP topology change monitoring:**
```spl
index=network earliest=-4h
| where match(_raw, "(?i)SPANTREE|STP|topology.change|TCN|TOPOTRAP|root.bridge|root.guard|BPDU")
| rex field=_raw "(?i)(?:VLAN|vlan)\s*(?<vlan_id>\d+)"
| rex field=_raw "(?i)(?:port|interface|Port)\s+(?<stp_port>\S+)"
| eval device=coalesce(host, device_name)
| eval event_type=case(
    match(_raw, "(?i)topology.change|TOPOTRAP|TCN"), "TOPOLOGY_CHANGE",
    match(_raw, "(?i)root.guard|ROOTGUARD"), "ROOT_GUARD",
    match(_raw, "(?i)BPDU.*guard|bpduguard"), "BPDU_GUARD",
    match(_raw, "(?i)root.*change|new.root"), "ROOT_CHANGE",
    1==1, "STP_EVENT")
| bin _time span=5m
| stats count as events dc(vlan_id) as vlans_affected dc(stp_port) as ports_involved values(event_type) as event_types by _time, device
| eval severity=case(
    match(mvjoin(event_types, ","), "ROOT_CHANGE"), "CRITICAL -- STP root bridge change detected",
    match(mvjoin(event_types, ","), "ROOT_GUARD"), "WARNING -- root guard violation",
    events > 20, "WARNING -- excessive topology changes (".events." in 5 min)",
    events > 5, "INFO -- moderate topology changes",
    1==1, "OK")
| where severity != "OK"
| sort severity, -events
```

### Step 3 — - Validate
(a) CLI: `show spanning-tree detail | include topology` -- check TC count.
(b) CLI: `show spanning-tree root` -- verify root bridge is expected device.
(c) CLI: `show spanning-tree summary` -- overview of STP status per VLAN.

### Step 4 — - Operationalize
Dashboard ("Network -- Spanning Tree"):
* Row 1 -- Single-value: "Topology changes (4h)", "VLANs affected", "Root guard violations".
* Row 2 -- STP topology change rate timechart.

Alert: Critical (root bridge change): potential network loop or attack.

### Step 5 — - Troubleshooting

* **Excessive topology changes** -- Usually caused by a flapping interface. Identify the port generating TCNs: `show spanning-tree detail`. Enable `spanning-tree portfast` on access ports to suppress TCNs.

* **Unexpected root bridge change** -- Verify root guard is enabled on all downstream ports: `spanning-tree guard root`. Check priority: `show spanning-tree root`. Ensure designated root has lowest priority.

* **BPDU guard violation** -- Port received BPDUs when it shouldn't (access port with portfast). Investigate: unauthorized switch connected. Port goes to err-disabled; recover with `shutdown / no shutdown`.

## SPL

```spl
index=network sourcetype="cisco:ios" "%SPANTREE-5-TOPOTCHANGE" OR "%SPANTREE-2-ROOTCHANGE"
| stats count by host | where count > 5 | sort -count
```

## Visualization

Table, Timeline, Bar chart by VLAN.

## Known False Positives

STP TCNs happen during access switch adds, link moves, and voice VLAN changes. Storm-control tuning can also shift TC rates.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
