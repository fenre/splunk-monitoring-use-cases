<!-- AUTO-GENERATED from UC-5.1.21.json — DO NOT EDIT -->

---
id: "5.1.21"
title: "CRC Error Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.21 · CRC Error Trending

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with crc error trending so the team can act before it grows into a bigger outage.*

---

## Description

Increasing CRC errors indicate failing cables, SFPs, or electromagnetic interference. Early detection prevents link failures.

## Value

Network engineers trend CRC error counters across switch and router interfaces, identifying physical layer degradation from bad cables, contaminated fiber connectors, or failing SFP optics.

## Implementation

Poll IF-MIB counters every 300s. Use `streamstats` to compute deltas. Trend over days to detect worsening interfaces. Cross-reference with interface utilization.

## Detailed Implementation

### Prerequisites
* CRC error counter data from SNMP or syslog. Data in `index=network` with SNMP or `sourcetype=cisco:ios`. Key SNMP OID: dot3StatsFCSErrors (.1.3.6.1.2.1.10.7.2.1.3). CLI: `show interface <intf> | include CRC`.
* CRC errors: Frame Check Sequence failures indicating corrupted frames. Causes: bad cable, damaged SFP/optics, electromagnetic interference, connector contamination. CRC errors always indicate a physical layer problem and should never be ignored.

### Step 1 — - Configure data collection
```
# SNMP polling for CRC/FCS error counters
[snmp_crc_errors]
interval = 300
sourcetype = snmp:crc:errors
index = network
# OID: dot3StatsFCSErrors (.1.3.6.1.2.1.10.7.2.1.3)
# Also poll: ifInErrors for correlation
```
Verify:
```spl
index=network earliest=-4h
| eval crc=tonumber(coalesce(dot3StatsFCSErrors, crc_errors, fcs_errors))
| where crc > 0
| stats latest(crc) by host, ifName
| sort -latest(crc)
```

### Step 2 — - Create the search and alert

**Primary search -- CRC error trending:**
```spl
index=network earliest=-24h
| eval crc=tonumber(coalesce(dot3StatsFCSErrors, crc_errors, fcs_errors))
| eval interface=coalesce(ifName, interface, port)
| eval device=coalesce(host, device_name)
| where isnotnull(crc)
| bin _time span=5m
| stats latest(crc) as crc_count by _time, device, interface
| sort device, interface, _time
| streamstats current=f last(crc_count) as prev_crc by device, interface
| eval delta_crc=crc_count - prev_crc
| where delta_crc > 0
| eventstats sum(delta_crc) as total_crc avg(delta_crc) as avg_crc by device, interface
| eval severity=case(
    delta_crc > 100, "CRITICAL -- rapid CRC error accumulation",
    total_crc > 500, "WARNING -- sustained CRC errors over period",
    delta_crc > 10, "WARNING -- CRC errors increasing",
    1==1, "INFO")
| where severity != "INFO"
| table _time, device, interface, delta_crc, total_crc, severity
| sort severity, -delta_crc
```

### Step 3 — - Validate
(a) CLI: `show interface <intf>` -- check CRC, input errors, runts, giants counters.
(b) CLI: `show interface transceiver` -- check SFP Rx/Tx power levels.
(c) Physical inspection: check cable condition, connector cleanliness.

### Step 4 — - Operationalize
Dashboard ("Network -- CRC Error Trending"):
* Row 1 -- Single-value: "Interfaces with CRC errors", "Total CRC delta (24h)".
* Row 2 -- CRC error rate timechart by interface.

Alert: Critical (>100 CRC errors/5min): physical layer failure, dispatch technician.

### Step 5 — - Troubleshooting

* **CRC errors on copper** -- Replace patch cable first (cheapest test). If persistent, test with cable tester. Check for electromagnetic interference from power cables running parallel.

* **CRC errors on fiber** -- Clean fiber connectors with proper cleaning tools. Check SFP optic power levels: Rx power below receiver sensitivity indicates dirty connector, bend loss, or failing SFP. Replace SFP if power levels out of spec.

* **CRC errors on single direction** -- Problem is on the transmitting side. Check the remote device's transmit optics/cable.

## SPL

```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifInErrors) as prev_errors, last(_time) as prev_time by host, ifDescr
| eval error_rate=(ifInErrors-prev_errors)/(_time-prev_time)
| where error_rate > 0
| timechart span=1h avg(error_rate) by host limit=20
```

## Visualization

Line chart (error rate over time per interface), Heatmap (device × interface), Table.

## Known False Positives

Planned work, test traffic, and known moves can look like a fault for «CRC Error Trending». Filter by change windows, lab sites, and maintenance notices you already trust.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
