<!-- AUTO-GENERATED from UC-5.1.35.json — DO NOT EDIT -->

---
id: "5.1.35"
title: "LLDP / CDP Neighbor Change Detection"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.35 · LLDP / CDP Neighbor Change Detection

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Fault, Security

*We help you know early when something looks wrong with lldp / cdp neighbor change detection so the team can act before it grows into a bigger outage.*

---

## Description

Unexpected topology changes in cabling/connections.

## Value

Network engineers detect LLDP/CDP neighbor additions and removals via SNMP polling, identifying physical topology changes and potential rogue device connections between poll intervals.

## Implementation

Poll LLDP-MIB lldpRemTable and CISCO-CDP-MIB; ingest syslog for CDP/LLDP neighbor change events. Baseline neighbor table; alert on unexpected changes (new/removed neighbors). Useful for change validation and cable swap detection.

## Detailed Implementation

### Prerequisites
* CDP/LLDP neighbor change detection via SNMP polling. Extends UC-5.1.18 with SNMP-based neighbor table comparison. SNMP OIDs: cdpCacheDeviceId (.1.3.6.1.4.1.9.9.23.1.2.1.1.6), lldpRemSysName (.1.0.8802.1.1.2.1.4.1.1.9).
* Periodic SNMP polling of neighbor tables enables detecting changes that don't generate syslog (e.g., slow neighbor timeout). Comparing consecutive polls reveals additions and removals.

### Step 1 — - Configure data collection
```
[snmp_neighbors]
interval = 300
sourcetype = snmp:neighbors
index = network
# CDP: cdpCacheDeviceId, cdpCachePlatform, cdpCacheDevicePort
# LLDP: lldpRemSysName, lldpRemPortId, lldpRemChassisId
```
Verify:
```spl
index=network sourcetype="snmp:neighbors" earliest=-4h
| stats dc(neighbor_name) by host
```

### Step 2 — - Create the search and alert

**Primary search -- Neighbor table change detection:**
```spl
index=network sourcetype="snmp:neighbors" earliest=-4h
| eval device=coalesce(host, device_name)
| eval neighbor=coalesce(cdpCacheDeviceId, lldpRemSysName, neighbor_name)
| eval local_port=coalesce(local_interface, ifName, port)
| eval remote_port=coalesce(cdpCacheDevicePort, lldpRemPortId, remote_interface)
| eval protocol=if(isnotnull(cdpCacheDeviceId), "CDP", "LLDP")
| bin _time span=5m
| stats values(neighbor) as current_neighbors by _time, device, local_port, protocol
| sort device, local_port, _time
| streamstats current=f last(current_neighbors) as prev_neighbors by device, local_port
| eval added=mvfilter(NOT match(current_neighbors, mvjoin(prev_neighbors, "|")))
| eval removed=mvfilter(NOT match(prev_neighbors, mvjoin(current_neighbors, "|")))
| where isnotnull(added) OR isnotnull(removed)
| eval change_detail=case(
    isnotnull(added) AND isnotnull(removed), "REPLACED: ".removed." -> ".added,
    isnotnull(added), "ADDED: ".added,
    isnotnull(removed), "REMOVED: ".removed)
| eval severity=case(
    isnotnull(removed), "WARNING -- neighbor removed on ".local_port,
    isnotnull(added), "INFO -- new neighbor on ".local_port,
    1==1, "INFO")
| table _time, device, local_port, protocol, change_detail, severity
| sort severity, _time
```

### Step 3 — - Validate
(a) CLI: `show cdp neighbors` / `show lldp neighbors` -- verify current topology.
(b) Cross-reference with physical topology documentation.
(c) Check for unauthorized devices.

### Step 4 — - Operationalize
Dashboard ("Network -- Neighbor Changes"):
* Row 1 -- Single-value: "Neighbors added", "Neighbors removed".
* Row 2 -- Neighbor change table.

Alert: Warning (neighbor removed from uplink/trunk port): potential connectivity impact.

### Step 5 — - Troubleshooting

* **Neighbor removed** -- Device disconnected, powered off, or cable pulled. Verify physical connection and remote device status.

* **New unknown neighbor** -- Potential rogue device. Verify against inventory. Apply 802.1X if appropriate.

* **Neighbor oscillating** -- CDP/LLDP hold timer too short. Default CDP holdtime is 180s. Adjust if needed: `cdp holdtime <seconds>`.

## SPL

```spl
index=network (sourcetype=snmp:lldp OR sourcetype=snmp:cdp OR sourcetype="cisco:ios") ("lldpRem" OR "CDP-4-NATIVE" OR "LLDP" OR "neighbor")
| rex "neighbor (?<neighbor>\S+)|lldpRemSysName[=:]\s*(?<neighbor>\S+)|port (?<port>\S+)"
| bin _time span=1h
| stats dc(neighbor) as neighbor_changes, values(neighbor) as neighbors by host, port, _time
| where neighbor_changes > 1
| table host port _time neighbor_changes neighbors
```

## Visualization

Table (host, port, changes), Timeline, Single value (unexpected changes).

## Known False Positives

New cables, SFP swaps, and VoIP phone reboots change discovery neighbors. Ignore known moves in office refresh projects.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
