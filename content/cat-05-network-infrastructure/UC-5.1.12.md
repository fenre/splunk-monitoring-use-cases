<!-- AUTO-GENERATED from UC-5.1.12.json — DO NOT EDIT -->

---
id: "5.1.12"
title: "ARP/MAC Table Anomalies"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.12 · ARP/MAC Table Anomalies

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Anomaly, Security

*We help you know early when something looks wrong with arp/mac table anomalies so the team can act before it grows into a bigger outage.*

---

## Description

MAC flapping indicates loops, misconfigurations, or layer-2 attacks.

## Value

Security and operations teams detect ARP/MAC table anomalies including MAC flapping, duplicate IPs, and ARP conflicts that indicate network loops, misconfigurations, or security attacks.

## Implementation

Forward syslog. Alert on MACFLAP events. Investigate the MAC to find the device.

## Detailed Implementation

### Prerequisites
* ARP and MAC table data from SNMP polling or syslog. Data in `index=network` with SNMP MIB data or syslog. Key SNMP OIDs: ipNetToMediaPhysAddress (ARP), dot1dTpFdbAddress (MAC table). Key syslog: `%IP-4-DUPADDR`, `%SW_MATM-4-MACFLAP_NOTIF`.
* ARP anomalies: duplicate IP addresses, ARP storms, ARP poisoning. MAC anomalies: MAC flapping (same MAC seen on multiple ports), MAC table overflow, rogue MAC addresses. These indicate misconfigurations, loops, or security attacks.

### Step 1 — - Configure data collection
```
# Cisco IOS -- MAC flap notifications are logged by default
# Key syslog: %SW_MATM-4-MACFLAP_NOTIF

# SNMP: poll ARP and MAC tables periodically
[snmp_mac_table]
interval = 300
sourcetype = snmp:mac:table
index = network
```
Verify:
```spl
index=network earliest=-24h
| where match(_raw, "(?i)MACFLAP|DUPADDR|arp.*conflict|mac.*flap|mac.*move|duplicate.*ip")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- ARP/MAC anomaly detection:**
```spl
index=network earliest=-4h
| where match(_raw, "(?i)MACFLAP|DUPADDR|arp.*conflict|mac.*flap|mac.*move|duplicate.*ip|gratuitous.*arp")
| rex field=_raw "(?i)(?:mac|MAC|address)\s+(?<mac_addr>[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})"
| rex field=_raw "(?i)(?:from|port)\s+(?<from_port>\S+)\s+(?:to|port)\s+(?<to_port>\S+)"
| rex field=_raw "(?i)VLAN\s*(?<vlan_id>\d+)"
| eval device=coalesce(host, device_name)
| eval anomaly_type=case(
    match(_raw, "(?i)MACFLAP|mac.*flap|mac.*move"), "MAC_FLAP",
    match(_raw, "(?i)DUPADDR|duplicate.*ip"), "DUPLICATE_IP",
    match(_raw, "(?i)arp.*conflict|gratuitous.*arp"), "ARP_CONFLICT",
    1==1, "ARP_MAC_ANOMALY")
| bin _time span=5m
| stats count as events dc(mac_addr) as unique_macs values(mac_addr) as macs values(vlan_id) as vlans by _time, device, anomaly_type
| eval severity=case(
    anomaly_type="MAC_FLAP" AND events > 50, "CRITICAL -- severe MAC flapping (possible loop)",
    anomaly_type="DUPLICATE_IP", "WARNING -- duplicate IP address detected",
    events > 20, "WARNING -- excessive ".anomaly_type." events",
    1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

### Step 3 — - Validate
(a) CLI: `show mac address-table count` -- check table utilization.
(b) CLI: `show ip arp` -- verify ARP table for duplicates.
(c) CLI: `show mac address-table notifications mac-move` -- check MAC move history.

### Step 4 — - Operationalize
Dashboard ("Network -- ARP/MAC Anomalies"):
* Row 1 -- Single-value: "MAC flaps (4h)", "Duplicate IPs", "Anomaly events".
* Row 2 -- ARP/MAC anomaly timeline.

Alert: Critical (>50 MAC flaps/5min): possible network loop.

### Step 5 — - Troubleshooting

* **MAC flapping** -- Same MAC seen on multiple ports indicates loop or dual-homed device without proper link aggregation. Check STP convergence (UC-5.1.6). Identify the physical device behind the MAC.

* **Duplicate IP address** -- Two devices configured with the same IP. Use ARP entry to identify MAC addresses of both devices, then trace to physical ports. Resolve IP conflict.

* **ARP storm** -- Excessive ARP broadcasts. May indicate scanning or worm. Check source MAC/IP and apply port security or DHCP snooping with DAI (Dynamic ARP Inspection).

## SPL

```spl
index=network sourcetype="cisco:ios" "%SW_MATM-4-MACFLAP_NOTIF"
| rex "(?<mac>[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})"
| stats count by host, mac | sort -count
```

## Visualization

Table, Timeline, Bar chart.

## Known False Positives

VMware vMotion, imaging carts, and conference room churn move MACs often. Baseline by VLAN before calling an attack.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
