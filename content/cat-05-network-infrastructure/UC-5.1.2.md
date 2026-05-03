<!-- AUTO-GENERATED from UC-5.1.2.json — DO NOT EDIT -->

---
id: "5.1.2"
title: "Interface Error Rates"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.2 · Interface Error Rates

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We count interface errors on switches and routers so we can spot bad cables or optics before they become real outages for everyone on that link.*

---

## Description

CRC errors, drops indicate cabling, transceiver, or duplex issues.

## Value

Operations teams track interface error rates (CRC, input/output errors, discards) as delta counters to detect physical layer degradation and congestion before they cause outages.

## Implementation

Poll IF-MIB (ifInErrors, ifOutErrors, ifInDiscards) at 300s. Use `streamstats` for delta. Alert on increasing counts.

## Detailed Implementation

### Prerequisites
* SNMP polling or syslog data with interface error counters. Data in `index=network` with `sourcetype=cisco:ios`, SNMP MIB data, or `sourcetype=perfmon:network`. Key fields: `ifInErrors`, `ifOutErrors`, `ifInDiscards`, `ifOutDiscards`, `ifCRCErrors`, `interface`, `host`.
* Interface errors: CRC errors (bad cable/optics), input errors (frame errors, runts, giants), output errors (collisions, late collisions), discards (buffer overflow, QoS policy drops). Non-zero and increasing error counters indicate physical layer problems or congestion.

### Step 1 — - Configure data collection
```
# SNMP polling via Splunk Add-on for SNMP or SC4SNMP
# Poll IF-MIB counters every 5 minutes:
# ifInErrors (.1.3.6.1.2.1.2.2.1.14)
# ifOutErrors (.1.3.6.1.2.1.2.2.1.20)
# ifInDiscards (.1.3.6.1.2.1.2.2.1.13)
# ifOutDiscards (.1.3.6.1.2.1.2.2.1.19)

# inputs.conf (SNMP poller)
[snmp_interface_errors]
interval = 300
sourcetype = snmp:interface:errors
index = network
```
Verify:
```spl
index=network sourcetype="snmp:interface:errors" earliest=-1h
| stats latest(ifInErrors) latest(ifOutErrors) by host, ifName
```

### Step 2 — - Create the search and alert

**Primary search -- Interface error rate trending:**
```spl
index=network earliest=-4h
| eval in_errors=tonumber(coalesce(ifInErrors, input_errors, in_errors))
| eval out_errors=tonumber(coalesce(ifOutErrors, output_errors, out_errors))
| eval in_discards=tonumber(coalesce(ifInDiscards, input_discards))
| eval out_discards=tonumber(coalesce(ifOutDiscards, output_discards))
| eval interface=coalesce(ifName, interface, port)
| eval device=coalesce(host, device_name)
| bin _time span=5m
| stats latest(in_errors) as in_err latest(out_errors) as out_err latest(in_discards) as in_disc latest(out_discards) as out_disc by _time, device, interface
| sort device, interface, _time
| streamstats current=f last(in_err) as prev_in_err last(out_err) as prev_out_err last(in_disc) as prev_in_disc last(out_disc) as prev_out_disc by device, interface
| eval delta_in_err=in_err - prev_in_err
| eval delta_out_err=out_err - prev_out_err
| eval delta_in_disc=in_disc - prev_in_disc
| eval delta_out_disc=out_disc - prev_out_disc
| eval total_delta=delta_in_err + delta_out_err + delta_in_disc + delta_out_disc
| where total_delta > 0
| eval severity=case(
    delta_in_err > 100 OR delta_out_err > 100, "CRITICAL -- high error rate",
    total_delta > 50, "WARNING -- elevated errors/discards",
    total_delta > 10, "INFO -- low-level errors detected",
    1==1, "OK")
| where severity != "OK"
| table _time, device, interface, delta_in_err, delta_out_err, delta_in_disc, delta_out_disc, severity
| sort severity, -total_delta
```

### Step 3 — - Validate
(a) CLI: `show interface <intf>` -- check error counter details (CRC, frame, overrun, underrun).
(b) Compare SNMP counter deltas with syslog error messages.
(c) Check optics: `show interface transceiver` for light level issues.

### Step 4 — - Operationalize
Dashboard ("Network -- Interface Errors"):
* Row 1 -- Single-value: "Interfaces with errors", "Total error delta (4h)".
* Row 2 -- Error rate timechart by interface.
* Row 3 -- Top error interfaces table.

Alert: Critical (>100 errors/5min on critical interface): physical layer investigation.

### Step 5 — - Troubleshooting

* **CRC errors increasing** -- Bad cable, damaged SFP, or dirty fiber connector. Replace cable/optics. Check `show interface transceiver` for Rx/Tx power levels.

* **Input discards** -- Interface receive buffer overflow. Possible cause: traffic burst exceeding interface speed, or QoS not configured to prioritize critical traffic.

* **Output discards** -- Egress congestion. Interface is oversubscribed. Consider: traffic shaping, QoS, or upgrading link capacity.

## SPL

```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifInErrors) as prev by host, ifDescr
| eval delta = ifInErrors - prev | where delta > 0
| table _time host ifDescr delta
```

## Visualization

Line chart (error rate), Table, Heatmap across devices.

## Known False Positives

Brief error increments during transceiver replacement, software upgrades, or known-noisy access segments can look like a fault. Baseline by interface role before paging.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
