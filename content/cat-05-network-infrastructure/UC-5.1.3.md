<!-- AUTO-GENERATED from UC-5.1.3.json — DO NOT EDIT -->

---
id: "5.1.3"
title: "Interface Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.3 · Interface Utilization

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We help you know early when something looks wrong with interface utilization so the team can act before it grows into a bigger outage.*

---

## Description

Saturated links cause drops and congestion. Trending enables proactive upgrades.

## Value

Network engineers monitor interface utilization percentage across routers and switches, identifying bandwidth saturation and trending capacity for proactive planning.

## Implementation

Poll 64-bit counters every 300s. Alert at 80% sustained. Use `predict` for capacity planning.

## Detailed Implementation

### Prerequisites
* SNMP polling data with interface utilization counters. Data in `index=network` with `sourcetype=snmp:interface` or SNMP MIB data. Key fields: `ifHCInOctets`, `ifHCOutOctets`, `ifSpeed`, `ifName`, `host`.
* Interface utilization: percentage of available bandwidth consumed in each direction. Calculated from delta of octet counters divided by polling interval and interface speed. High utilization causes packet loss and latency; sustained >80% typically requires capacity planning.

### Step 1 — - Configure data collection
```
# SNMP polling via SC4SNMP or Splunk Add-on for SNMP
# Poll IF-MIB HC counters every 5 minutes:
# ifHCInOctets (.1.3.6.1.2.1.31.1.1.1.6) -- 64-bit counters
# ifHCOutOctets (.1.3.6.1.2.1.31.1.1.1.10)
# ifSpeed (.1.3.6.1.2.1.2.2.1.5) or ifHighSpeed (.1.3.6.1.2.1.31.1.1.1.15)

[snmp_interface_util]
interval = 300
sourcetype = snmp:interface
index = network
```
Verify:
```spl
index=network sourcetype="snmp:interface" earliest=-1h
| stats latest(ifHCInOctets) latest(ifHCOutOctets) latest(ifSpeed) by host, ifName
```

### Step 2 — - Create the search and alert

**Primary search -- Interface utilization monitoring:**
```spl
index=network earliest=-4h
| eval in_octets=tonumber(coalesce(ifHCInOctets, ifInOctets))
| eval out_octets=tonumber(coalesce(ifHCOutOctets, ifOutOctets))
| eval speed_bps=tonumber(coalesce(ifHighSpeed, ifSpeed))*if(isnotnull(ifHighSpeed), 1000000, 1)
| eval interface=coalesce(ifName, interface, port)
| eval device=coalesce(host, device_name)
| bin _time span=5m
| stats latest(in_octets) as in_oct latest(out_octets) as out_oct latest(speed_bps) as speed by _time, device, interface
| sort device, interface, _time
| streamstats current=f last(in_oct) as prev_in last(out_oct) as prev_out last(_time) as prev_time by device, interface
| eval interval_sec=_time - prev_time
| where interval_sec > 0 AND isnotnull(prev_in)
| eval in_bps=round(8*(in_oct - prev_in)/interval_sec, 0)
| eval out_bps=round(8*(out_oct - prev_out)/interval_sec, 0)
| eval in_util_pct=if(speed > 0, round(100*in_bps/speed, 1), 0)
| eval out_util_pct=if(speed > 0, round(100*out_bps/speed, 1), 0)
| eval max_util=max(in_util_pct, out_util_pct)
| eval in_mbps=round(in_bps/1000000, 1)
| eval out_mbps=round(out_bps/1000000, 1)
| eval severity=case(
    max_util > 90, "CRITICAL -- interface near saturation (".max_util."%)",
    max_util > 80, "WARNING -- high utilization (".max_util."%)",
    max_util > 70, "INFO -- elevated utilization",
    1==1, "OK")
| where severity != "OK"
| table _time, device, interface, in_mbps, out_mbps, in_util_pct, out_util_pct, severity
| sort severity, -max_util
```

### Step 3 — - Validate
(a) CLI: `show interface <intf>` -- check 5-minute input/output rate.
(b) Cross-reference with application traffic (NetFlow/sFlow) to identify top talkers.
(c) Verify interface speed is correctly reported (no speed/duplex mismatch).

### Step 4 — - Operationalize
Dashboard ("Network -- Interface Utilization"):
* Row 1 -- Single-value: "Interfaces > 80%", "Peak utilization", "Avg utilization".
* Row 2 -- Utilization timechart (top interfaces by peak).
* Row 3 -- High-utilization interface table.

Alert: Warning (sustained >80% for 30+ min): capacity planning trigger.

### Step 5 — - Troubleshooting

* **Counter wrap** -- 32-bit counters (ifInOctets) wrap on high-speed interfaces. Always use 64-bit HC counters (ifHCInOctets). If negative delta detected, discard that sample.

* **Sustained high utilization** -- Identify top talkers via NetFlow/sFlow. Consider: QoS traffic shaping, link aggregation, or capacity upgrade.

* **Utilization spikes at specific times** -- Correlate with backup schedules, patch distribution, or business activity patterns. Schedule bandwidth-heavy operations during off-peak.

## SPL

```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifHCInOctets) as prev_in, last(_time) as prev_time by host, ifDescr
| eval in_bps=((ifHCInOctets-prev_in)*8)/(_time-prev_time)
| eval util_pct=round(in_bps/ifSpeed*100,1) | where util_pct>80
```

## Visualization

Line chart, Gauge per critical link, Table sorted by utilization.

## Known False Positives

Short bursts during backups, patch pushes, or video calls can approach thresholds without an outage. Match alerts to business hours and known batch jobs.

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
