<!-- AUTO-GENERATED from UC-5.1.18.json — DO NOT EDIT -->

---
id: "5.1.18"
title: "CDP/LLDP Neighbor Changes"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.18 · CDP/LLDP Neighbor Changes

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Availability, Configuration

*We help you know early when something looks wrong with cdp/lldp neighbor changes so the team can act before it grows into a bigger outage.*

---

## Description

Unexpected neighbor changes indicate cabling modifications, device replacements, or unauthorized devices connecting to the network.

## Value

Network engineers monitor CDP/LLDP neighbor changes to detect physical topology modifications, unauthorized device connections, and native VLAN mismatches across the switching fabric.

## Implementation

Poll CDP-MIB/LLDP-MIB at 600s intervals. Create a baseline lookup via `outputlookup`. Compare current neighbors against baseline. Alert on new/removed neighbors.

## Detailed Implementation

### Prerequisites
* CDP (Cisco Discovery Protocol) and LLDP (Link Layer Discovery Protocol) neighbor change events. Data in `index=network` with `sourcetype=cisco:ios` or vendor-specific sourcetypes. Key mnemonics: Cisco `%CDP-4-NATIVE_VLAN_MISMATCH`, `%CDP-4-DUPLEX_MISMATCH`; LLDP TLV changes.
* CDP/LLDP neighbor changes indicate: physical topology changes (new device connected, cable moved), device replacement, or rogue device insertion. Baseline neighbor tables enable detecting unauthorized changes.

### Step 1 — - Configure data collection
```
# Cisco IOS -- CDP is enabled by default
# Enable LLDP (for multi-vendor environments)
lldp run

# SNMP polling for neighbor tables
# CDP: cdpCacheDeviceId (.1.3.6.1.4.1.9.9.23.1.2.1.1.6)
# LLDP: lldpRemSysName (.1.0.8802.1.1.2.1.4.1.1.9)
```
Verify:
```spl
index=network earliest=-24h
| where match(_raw, "(?i)CDP|LLDP|neighbor.*change|neighbor.*add|neighbor.*remove")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- CDP/LLDP neighbor change detection:**
```spl
index=network earliest=-24h
| where match(_raw, "(?i)CDP|LLDP|neighbor.*change|neighbor.*add|neighbor.*remove|NATIVE_VLAN_MISMATCH")
| rex field=_raw "(?i)(?:Device.?Id|neighbor|sysname).*?[:\s]+(?<neighbor_name>\S+)"
| rex field=_raw "(?i)(?:Port.?Id|interface|port).*?[:\s]+(?<neighbor_port>\S+)"
| rex field=_raw "(?i)(?:local|interface|port)\s+(?<local_port>\S+)"
| eval device=coalesce(host, device_name)
| eval neighbor=coalesce(neighbor_name, remote_device)
| eval change_type=case(
    match(_raw, "(?i)NATIVE_VLAN"), "NATIVE_VLAN_MISMATCH",
    match(_raw, "(?i)DUPLEX_MISMATCH"), "DUPLEX_MISMATCH",
    match(_raw, "(?i)add|new|appear"), "NEIGHBOR_ADDED",
    match(_raw, "(?i)remov|delet|disappear|lost"), "NEIGHBOR_REMOVED",
    1==1, "NEIGHBOR_CHANGE")
| stats count as events values(change_type) as change_types values(neighbor) as neighbors values(local_port) as local_ports by device
| eval severity=case(
    match(mvjoin(change_types, ","), "NATIVE_VLAN_MISMATCH"), "WARNING -- native VLAN mismatch detected",
    match(mvjoin(change_types, ","), "NEIGHBOR_REMOVED"), "WARNING -- neighbor(s) lost",
    events > 10, "INFO -- significant topology changes",
    1==1, "INFO")
| where severity != "INFO" OR events > 5
| sort severity, -events
```

### Step 3 — - Validate
(a) CLI: `show cdp neighbors` / `show lldp neighbors` -- current neighbor table.
(b) Compare against documented physical topology.
(c) Check for native VLAN consistency: `show cdp neighbors detail | include Native`.

### Step 4 — - Operationalize
Dashboard ("Network -- Topology Discovery"):
* Row 1 -- Single-value: "Neighbor changes (24h)", "Native VLAN mismatches", "Neighbors lost".
* Row 2 -- CDP/LLDP change event table.

Alert: Warning (neighbor removed on critical port): cable or device failure.

### Step 5 — - Troubleshooting

* **Native VLAN mismatch** -- Trunk ports must agree on native VLAN. Fix: `switchport trunk native vlan <id>` on both sides. Mismatch causes traffic leaking between VLANs.

* **Unexpected neighbor** -- Rogue device connected. Verify against inventory. If unauthorized, shut port and investigate. Consider 802.1X port authentication.

* **Neighbor lost but link is up** -- CDP/LLDP may be disabled on the remote device. Check: `show cdp interface` and verify remote device configuration.

## SPL

```spl
index=network sourcetype="snmp:cdp"
| stats latest(cdpCacheDeviceId) as neighbor, latest(cdpCachePlatform) as platform by host, cdpCacheIfIndex
| appendpipe [| inputlookup cdp_baseline.csv]
| eventstats latest(neighbor) as current, first(neighbor) as baseline by host, cdpCacheIfIndex
| where current!=baseline | table host, cdpCacheIfIndex, baseline, current, platform
```

## Visualization

Table (host, interface, old neighbor, new neighbor), Change log timeline.

## Known False Positives

New cables, SFP swaps, and VoIP phone reboots change discovery neighbors. Ignore known moves in office refresh projects.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
