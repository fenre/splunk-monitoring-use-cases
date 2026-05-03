<!-- AUTO-GENERATED from UC-5.1.44.json — DO NOT EDIT -->

---
id: "5.1.44"
title: "Broadcast Storm Detection and Mitigation (Meraki MS)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.44 · Broadcast Storm Detection and Mitigation (Meraki MS)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Anomaly

*We help you know early when something looks wrong with broadcast storm detection and mitigation so the team can act before it grows into a bigger outage.*

---

## Description

Identifies and alerts on broadcast storms that can freeze network performance across all switches.

## Value

NOC teams detect broadcast storms on Meraki MS switches and track storm control actions including port disablement, enabling rapid identification and resolution of network loops.

## Implementation

Monitor broadcast traffic thresholds. Alert on sustained high broadcast rates.

## Detailed Implementation

### Prerequisites
* Meraki MS broadcast storm events from syslog. Data in `index=meraki` with `sourcetype=meraki:events`. Key events: storm control triggered, broadcast storm detected, port disabled by storm control.
* Broadcast storms: excessive broadcast traffic that saturates the network. Causes: network loops, misbehaving devices, or broadcast-heavy protocols. Meraki MS has built-in storm control that rate-limits or disables ports exceeding broadcast thresholds.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Switch > Storm control
# Configure storm control thresholds
# Syslog: enable Event log
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-7d
| where match(_raw, "(?i)storm|broadcast.*storm|storm.*control|broadcast.*rate")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Broadcast storm detection:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)storm|broadcast.*storm|storm.*control|broadcast.*rate|multicast.*storm")
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| rex field=_raw "(?i)(?:port|Port)\s+(?<port_id>\d+)"
| eval storm_action=case(
    match(_raw, "(?i)disabl|shut|block"), "PORT_DISABLED",
    match(_raw, "(?i)rate.*limit|throttl"), "RATE_LIMITED",
    match(_raw, "(?i)detect|alert"), "DETECTED",
    1==1, "STORM_EVENT")
| stats count as events values(storm_action) as actions values(port_id) as ports by network_name, device
| eval severity=case(
    match(mvjoin(actions, ","), "PORT_DISABLED"), "CRITICAL -- port disabled by storm control",
    events > 5, "WARNING -- repeated storm control events",
    1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

### Step 3 — - Validate
(a) Dashboard: Switch > Switch ports -- check for ports disabled by storm control.
(b) Check for physical loops (ports connected to same switch or hub).
(c) Dashboard: Network-wide > Event log -- review storm events.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- Storm Control"):
* Row 1 -- Single-value: "Storm events (4h)", "Ports disabled".
* Row 2 -- Storm control event timeline.

Alert: Critical (port disabled by storm control): investigate loop or misbehaving device.

### Step 5 — - Troubleshooting

* **Broadcast storm from loop** -- Trace the physical cabling. Check for unmanaged switches or hubs creating loops. Remove the loop and re-enable port.

* **Storm from misbehaving device** -- Identify the device on the storm-causing port. May be broadcasting excessively (ARP storm, DHCP storm). Isolate and fix the device.

* **Storm control threshold too sensitive** -- Adjust thresholds in Dashboard if false positives. Consider the normal broadcast level for the VLAN.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*broadcast*"
| stats sum(packet_count) as broadcast_packets by switch_name, port_id
| where broadcast_packets > 10000
```

## Visualization

Real-time alert dashboard; time-series of broadcast packets; affected port list.

## Known False Positives

Imaging, Wake-on-LAN, and some IoT devices can create broadcast spikes. Confirm port security and STP before blaming a DDoS.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
