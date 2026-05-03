<!-- AUTO-GENERATED from UC-5.1.42.json — DO NOT EDIT -->

---
id: "5.1.42"
title: "MAC Flooding and Bridge Table Exhaustion (Meraki MS)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.1.42 · MAC Flooding and Bridge Table Exhaustion (Meraki MS)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Capacity

*We help you know early when something looks wrong with mac flooding and bridge table exhaustion so the team can act before it grows into a bigger outage.*

---

## Description

Detects MAC address table exhaustion and flooding attacks that could overwhelm switch resources.

## Value

Security teams detect MAC flooding attacks and bridge table exhaustion on Meraki MS switches, identifying ports generating excessive MAC addresses that compromise network segmentation.

## Implementation

Monitor MAC-related syslog events. Alert on suspicious patterns.

## Detailed Implementation

### Prerequisites
* Meraki MS MAC table data. Data in `index=meraki` with syslog events or API data. Key events: MAC flooding indicators, bridge table overflow.
* MAC flooding: an attack or misconfiguration that fills the switch CAM table with fake MAC addresses. Once full, the switch floods unicast frames to all ports (hub behavior), enabling traffic sniffing.

### Step 1 — - Configure data collection
```
# Syslog: enable Event log
# Monitor for MAC table related events
# Port security helps mitigate MAC flooding
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-24h
| where match(_raw, "(?i)MAC.*flood|bridge.*table|CAM.*table|mac.*limit|mac.*learn")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- MAC flooding and table exhaustion indicators:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:switch:portstatus") earliest=-4h
| where match(_raw, "(?i)MAC.*flood|bridge.*table|mac.*limit|excessive.*mac|mac.*learn.*fail")
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| rex field=_raw "(?i)(?:port|Port)\s+(?<port_id>\d+)"
| eval event_type=case(
    match(_raw, "(?i)flood"), "MAC_FLOOD",
    match(_raw, "(?i)table.*full|exhaustion"), "TABLE_FULL",
    match(_raw, "(?i)limit|excessive"), "MAC_LIMIT_EXCEEDED",
    1==1, "MAC_EVENT")
| stats count as events values(port_id) as affected_ports by network_name, device, event_type
| eval severity=case(
    event_type="TABLE_FULL", "CRITICAL -- MAC table exhaustion",
    event_type="MAC_FLOOD", "CRITICAL -- MAC flooding detected",
    events > 10, "WARNING -- excessive MAC events",
    1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

### Step 3 — - Validate
(a) Dashboard: Switch > Switch ports -- check per-port client count.
(b) Check for ports with abnormally high MAC count.
(c) Verify port security policies are applied.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- MAC Table"):
* Row 1 -- Single-value: "MAC flooding events", "Table exhaustion events".
* Row 2 -- MAC event table.

Alert: Critical (MAC flooding or table exhaustion): security investigation.

### Step 5 — - Troubleshooting

* **MAC flooding attack** -- Identify the port with excessive MACs. Disable the port. Apply MAC limit per port in access policy.

* **Legitimate high MAC count** -- Virtualization (many VMs on one port) or hub connected. Use trunk port with proper VLAN configuration.

* **Prevention** -- Set MAC limit per port in Dashboard access policy. Enable dynamic ARP inspection.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*MAC*" OR signature="*flood*")
| stats count as flood_count by switch_name, port_id
| where flood_count > 50
```

## Visualization

Table of affected switches/ports; time-series of flood events; alert dashboard.

## Known False Positives

VMware vMotion, imaging carts, and conference room churn move MACs often. Baseline by VLAN before calling an attack.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
