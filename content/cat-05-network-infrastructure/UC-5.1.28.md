<!-- AUTO-GENERATED from UC-5.1.28.json — DO NOT EDIT -->

---
id: "5.1.28"
title: "STP Topology Change Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.28 · STP Topology Change Rate

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault

*We help you know early when something looks wrong with stp topology change rate so the team can act before it grows into a bigger outage.*

---

## Description

Frequent topology changes indicating Layer 2 instability.

## Value

Network engineers analyze STP topology change rates to distinguish normal port transitions from TC storms indicating network loops or severe link flapping.

## Implementation

Poll BRIDGE-MIB dot1dStpTopChanges every 300s; ingest syslog for SPANTREE events. Alert when topology changes exceed 3 in 10 minutes. Correlate with root bridge changes for critical alerts.

## Detailed Implementation

### Prerequisites
* STP topology change rate data from SNMP or syslog. Extends UC-5.1.6 with rate-based analysis. SNMP OID: dot1dStpTopChanges (.1.3.6.1.2.1.17.2.4) -- cumulative TC count per bridge.
* STP topology change rate: tracking the TC rate over time helps distinguish between normal occasional changes (device plugged in) and abnormal storms (flapping link, loop). High TC rates cause network-wide MAC table flushes.

### Step 1 — - Configure data collection
```
# SNMP polling for STP counters
[snmp_stp]
interval = 300
sourcetype = snmp:stp
index = network
# OID: dot1dStpTopChanges (.1.3.6.1.2.1.17.2.4)
# dot1dStpTimeSinceTopologyChange (.1.3.6.1.2.1.17.2.3)
```
Verify:
```spl
index=network (sourcetype="snmp:stp" OR sourcetype="cisco:ios") earliest=-4h
| eval tc_count=tonumber(coalesce(dot1dStpTopChanges, stp_tc_count))
| where isnotnull(tc_count)
| stats latest(tc_count) by host
```

### Step 2 — - Create the search and alert

**Primary search -- STP topology change rate analysis:**
```spl
index=network earliest=-4h
| eval tc_count=tonumber(coalesce(dot1dStpTopChanges, stp_tc_count))
| eval device=coalesce(host, device_name)
| where isnotnull(tc_count)
| bin _time span=5m
| stats latest(tc_count) as tc by _time, device
| sort device, _time
| streamstats current=f last(tc) as prev_tc last(_time) as prev_time by device
| eval delta_tc=tc - prev_tc
| eval interval_min=(_time - prev_time)/60
| eval tc_rate=if(interval_min > 0, round(delta_tc/interval_min, 2), 0)
| where delta_tc > 0
| eval severity=case(
    tc_rate > 10, "CRITICAL -- STP TC storm (".tc_rate." TCs/min)",
    delta_tc > 5, "WARNING -- elevated TC rate",
    1==1, "INFO")
| where severity != "INFO"
| table _time, device, delta_tc, tc_rate, severity
| sort severity, -tc_rate
```

### Step 3 — - Validate
(a) CLI: `show spanning-tree detail | include topology` -- check TC count and last TC time.
(b) CLI: `show spanning-tree summary` -- overview of TC stats per VLAN.
(c) Identify port generating TCs: `show spanning-tree detail` and look for "forwarding" transitions.

### Step 4 — - Operationalize
Dashboard ("Network -- STP TC Rate"):
* Row 1 -- Single-value: "TC storms detected", "Total TCs (4h)".
* Row 2 -- STP TC rate timechart.

Alert: Critical (>10 TCs/min sustained): network loop or severe flapping.

### Step 5 — - Troubleshooting

* **TC storm** -- A port is rapidly transitioning. Identify: `show spanning-tree detail`. Enable portfast on access ports. Check for loop: trace the flapping port to the connected device.

* **Constant low-rate TCs** -- May be normal if many devices are connecting/disconnecting (conference rooms, hot-desking). Portfast on access ports prevents these.

* **TC after topology change** -- Expected after adding new switch or recabling. Should stabilize within minutes. If persistent, investigate root cause.

## SPL

```spl
index=network (sourcetype=snmp:stp OR sourcetype="cisco:ios") ("dot1dStpTopChanges" OR "%SPANTREE-5-TOPOTCHANGE" OR "%SPANTREE-2-ROOTCHANGE")
| eval stp_event=if(match(_raw,"TOPOTCHANGE|ROOTCHANGE|dot1dStpTopChanges"),1,0)
| bin _time span=10m
| stats sum(stp_event) as topo_changes by host, _time
| where topo_changes > 3
| sort -topo_changes
```

## Visualization

Line chart (topology changes per host), Table (host, count), Timeline.

## Known False Positives

STP TCNs happen during access switch adds, link moves, and voice VLAN changes. Storm-control tuning can also shift TC rates.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
