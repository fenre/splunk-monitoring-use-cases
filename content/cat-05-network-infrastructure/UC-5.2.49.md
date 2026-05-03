<!-- AUTO-GENERATED from UC-5.2.49.json — DO NOT EDIT -->

---
id: "5.2.49"
title: "Check Point SecureXL Acceleration Status (Check Point)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.49 · Check Point SecureXL Acceleration Status (Check Point)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We look at fast-path and acceleration state so a sudden return to slow inspection is a visible clue before users call about slowness.*

---

## Description

SecureXL offloads connection handling from the firewall kernel to an acceleration layer, increasing throughput by 2–10×. When SecureXL cannot accelerate a connection (due to complex NAT, certain blade inspections, or resource limits), traffic falls back to the slow path (Firewall kernel or even Medium path). A rising percentage of non-accelerated connections signals policy complexity growth, blade misconfiguration, or capacity limits — reducing effective throughput well before CPU saturation appears.

## Value

Operations teams monitor Check Point SecureXL acceleration status and packet processing ratios, detecting disabled acceleration or degraded offload that causes firewall performance degradation.

## Implementation

Use `fwaccel stat` and `fwaccel conns` via scripted input on the gateway (every 5 min) or parse SecureXL log messages from system events. Baseline accelerated vs slow-path ratio per gateway. Alert when slow-path percentage exceeds 30% sustained for 1 hour. Correlate with policy install events (UC-5.2.48) — new rules with unsupported features often shift traffic to slow path. Report on acceleration trends after blade enablement changes.

## Detailed Implementation

### Prerequisites
* Check Point SecureXL acceleration status data. Data in `index=checkpoint` with `sourcetype=cp_log` or custom scripted input from `fwaccel stat`. Key fields: `acceleration_status`, `accel_connections`, `accel_packets`, `pxl_connections`.
* SecureXL: hardware/software acceleration layer that offloads established connections from the firewall kernel (F2F path) to the accelerated path (SecureXL). When enabled, throughput increases 2-10x. Connections can be accelerated (fast path), medium-path (partial inspection), or slow-path (full inspection). Monitoring: `fwaccel stat`, `fwaccel stats -s`.

### Step 1 — - Configure data collection
```
# Custom scripted input to collect SecureXL stats
# inputs.conf
[script:///opt/splunk/etc/apps/checkpoint_inputs/bin/secureXL_stats.sh]
interval = 300
sourcetype = checkpoint:securexl
index = checkpoint
disabled = false

# secureXL_stats.sh
#!/bin/bash
echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
fwaccel stat 2>/dev/null | while read line; do echo "securexl_stat="$line""; done
fwaccel stats -s 2>/dev/null | while read line; do echo "securexl_detail="$line""; done
fwaccel conns 2>/dev/null | head -5 | while read line; do echo "securexl_conns="$line""; done
```
Verify:
```spl
index=checkpoint sourcetype="checkpoint:securexl" earliest=-1h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- SecureXL acceleration status monitoring:**
```spl
index=checkpoint (sourcetype="checkpoint:securexl" OR sourcetype="cp_log") earliest=-4h
| eval accel_enabled=if(match(_raw, "(?i)accelerator.*status.*on|securexl.*enabled"), "ON", if(match(_raw, "(?i)accelerator.*status.*off|securexl.*disabled"), "OFF", null()))
| eval accel_packets=tonumber(coalesce(accel_packets, "0"))
| eval pxl_packets=tonumber(coalesce(pxl_packets, "0"))
| eval f2f_packets=tonumber(coalesce(f2f_packets, "0"))
| eval total_packets=accel_packets + pxl_packets + f2f_packets
| eval accel_pct=if(total_packets > 0, round(100*accel_packets/total_packets, 1), 0)
| eval pxl_pct=if(total_packets > 0, round(100*pxl_packets/total_packets, 1), 0)
| eval f2f_pct=if(total_packets > 0, round(100*f2f_packets/total_packets, 1), 0)
| bin _time span=5m
| stats latest(accel_enabled) as status avg(accel_pct) as accel_pct avg(pxl_pct) as medium_pct avg(f2f_pct) as slow_pct by _time, host
| eval severity=case(
    status="OFF", "CRITICAL -- SecureXL disabled, performance severely degraded",
    accel_pct < 50, "WARNING -- low acceleration ratio (".accel_pct."%), high kernel processing",
    accel_pct < 70, "INFO -- suboptimal acceleration ratio",
    1==1, "OK")
| where severity != "OK"
| table _time, host, status, accel_pct, medium_pct, slow_pct, severity
```

### Step 3 — - Validate
(a) CLI (expert mode): `fwaccel stat` -- verify SecureXL is enabled and check status.
(b) CLI: `fwaccel stats -s` -- show acceleration statistics (packets accelerated/not-accelerated).
(c) CLI: `fwaccel conns` -- show accelerated connection table count.

### Step 4 — - Operationalize
Dashboard ("Check Point -- SecureXL Acceleration"):
* Row 1 -- Single-value: "SecureXL status", "Acceleration ratio (%)", "Slow-path packets (%)".
* Row 2 -- Acceleration ratio timechart.

Alert: Critical (SecureXL disabled or acceleration < 50%): performance impact, investigate.

### Step 5 — - Troubleshooting

* **SecureXL disabled** -- Re-enable: `fwaccel on`. If disabled intentionally for debugging, re-enable after troubleshooting. Check `cpinfo -y all` for known issues.

* **Low acceleration ratio** -- Many connections may be in slow-path due to: (1) security blades requiring deep inspection (IPS, Application Control), (2) HTTPS inspection enabled, (3) fragmented packets. Check which blades are forcing F2F: `fwaccel stat` shows blade impact.

* **SecureXL template count high** -- Connection templates consume memory. Monitor with `fwaccel conns -s`. Consider connection table optimization.

## SPL

```spl
index=firewall sourcetype="cp_log" earliest=-24h
| where match(lower(product),"(?i)securexl|fwaccel") OR match(lower(logdesc),"(?i)accel|template|f2f|medium.path|pxl")
| eval gw=coalesce(orig, src, hostname)
| eval path=case(
    match(lower(_raw),"(?i)accel|template"),"accelerated",
    match(lower(_raw),"(?i)medium.path|pxl"),"medium_path",
    match(lower(_raw),"(?i)f2f|slow|firewall.path"),"slow_path",
    1=1,"unknown")
| stats count by gw, path
| eventstats sum(count) as total by gw
| eval pct=round(100*count/total,1)
| where path!="accelerated" AND pct>20
```

## Visualization

Pie chart (accelerated vs medium vs slow path), Line chart (acceleration ratio over time), Table (gateways with low acceleration), Bar chart (slow-path reasons).

## Known False Positives

Policy changes, debug toggles, and version shifts can make acceleration messages noisy until you set a baseline.

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
