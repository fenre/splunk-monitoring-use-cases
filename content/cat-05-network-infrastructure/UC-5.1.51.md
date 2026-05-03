<!-- AUTO-GENERATED from UC-5.1.51.json — DO NOT EDIT -->

---
id: "5.1.51"
title: "Uplink Health and Failover Events (Meraki MS)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.51 · Uplink Health and Failover Events (Meraki MS)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know early when something looks wrong with uplink health and failover events so the team can act before it grows into a bigger outage.*

---

## Description

Monitors primary/secondary uplink status to detect failover events and connection issues.

## Value

NOC teams monitor Meraki MS uplink health and failover events, detecting uplink failures that disconnect all downstream devices and trigger failover to redundant paths.

## Implementation

Monitor uplink status change events in syslog. Alert on failover.

## Detailed Implementation

### Prerequisites
* Meraki MS uplink health and failover events. Data in `index=meraki` with `sourcetype=meraki:events` or `sourcetype=meraki:api:switch:portstatus`. Key events: uplink port status changes, uplink failover (for switches with dual uplinks or stacked switches).
* Meraki MS uplinks: connection from access/distribution switch to upstream network. Uplink failure disconnects all downstream devices. Stacked switches may have multiple uplinks with failover capability.

### Step 1 — - Configure data collection
```
# Syslog: enable Event log
# API: GET /devices/{serial}/switch/ports/statuses
# Filter for uplink ports
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-7d
| where match(_raw, "(?i)uplink.*down|uplink.*up|uplink.*fail|uplink.*change")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Uplink health and failover:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:switch:portstatus") earliest=-7d
| where match(_raw, "(?i)uplink") OR (isnotnull(isUplink) AND isUplink="true")
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name, site_name
| eval port=coalesce(portId, port_id)
| eval status=case(
    match(_raw, "(?i)down|fail|disconnect|offline"), "DOWN",
    match(_raw, "(?i)up|active|connected|online"), "UP",
    match(status, "(?i)connected"), "UP",
    1==1, "CHANGE")
| sort device, port, _time
| stats count as events count(eval(status="DOWN")) as downs count(eval(status="UP")) as ups latest(status) as current by device, network_name, port
| eval severity=case(
    current="DOWN", "CRITICAL -- uplink DOWN (".network_name.")",
    downs > 3, "WARNING -- uplink flapping",
    1==1, "OK")
| where severity != "OK"
| sort severity
```

### Step 3 — - Validate
(a) Dashboard: Switch > Overview -- check uplink status.
(b) Dashboard: Switch > Switch ports -- check uplink port details.
(c) Verify upstream device port status.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- Uplink Health"):
* Row 1 -- Single-value: "Uplinks DOWN", "Uplink failover events".
* Row 2 -- Uplink status timeline.

Alert: Critical (uplink DOWN): all downstream devices lose connectivity.

### Step 5 — - Troubleshooting

* **Uplink DOWN** -- Check: (1) upstream switch port status, (2) cable/SFP, (3) VLAN trunk configuration, (4) spanning tree blocking.

* **Uplink flapping** -- Check cable quality, SFP module, and upstream port. Run cable test.

* **No redundant uplink** -- Single point of failure. Consider: stacking with dual uplinks, or dual-homing to two upstream switches.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Uplink*" OR signature="*failover*")
| stats count as failover_count by uplink_name, event_type
| where failover_count > 0
```

## Visualization

Uplink status dashboard; failover event timeline; connection health gauge.

## Known False Positives

Meraki cloud delays, dashboard API limits, and large site templates can look like a gap. Confirm in dashboard before opening a P1 on Splunk only.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
