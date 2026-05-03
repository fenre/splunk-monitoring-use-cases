<!-- AUTO-GENERATED from UC-5.2.54.json — DO NOT EDIT -->

---
id: "5.2.54"
title: "Check Point Gateway Connection Table Utilization (Check Point)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.54 · Check Point Gateway Connection Table Utilization (Check Point)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Performance

*We follow how full the connection table is so sudden growth, leaks, and attacks that eat state are visible with room to act.*

---

## Description

Each Check Point gateway has a finite concurrent connection table (configurable, typically 500K–25M depending on appliance). When utilization approaches the limit, new connections are dropped — causing application failures and user complaints. Unlike CPU, connection table exhaustion can happen suddenly during attacks or application bursts with little warning.

## Value

Operations teams monitor Check Point gateway connection table utilization and growth rate, preventing connection table exhaustion that causes new connection drops and service outages.

## Implementation

Use `fw tab -t connections -s` via scripted input (every 60s) to capture current and maximum connection counts. Alternatively parse system log messages about connection limits and aggressive aging (automatic cleanup when table is near capacity). Alert at 75% utilization. Page at 90%. Correlate with NAT pool usage and DDoS indicators. Enable aggressive aging thresholds as a safety net but alert when triggered.

## Detailed Implementation

### Prerequisites
* Check Point gateway connection table utilization data. Data in `index=checkpoint` with `sourcetype=cp_log` or custom scripted input from `fw tab -t connections -s`. Key fields: `connections_count`, `connections_limit`, `connections_peak`.
* Each Check Point gateway has a finite concurrent connection table (configurable, typically 500K-25M depending on appliance model). When the table fills, new connections are dropped. Monitoring: `fw tab -t connections -s`, `cpview`, `cpstat -f all os`.

### Step 1 — - Configure data collection
```
# Custom scripted input for connection table monitoring
# inputs.conf
[script:///opt/splunk/etc/apps/checkpoint_inputs/bin/conn_table.sh]
interval = 60
sourcetype = checkpoint:conntable
index = checkpoint
disabled = false

# conn_table.sh
#!/bin/bash
echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "hostname=$(hostname)"
fw tab -t connections -s 2>/dev/null | while read line; do echo "conn_table="$line""; done
cpstat -f all os 2>/dev/null | grep -i "connections" | while read line; do echo "cpstat="$line""; done
```
Verify:
```spl
index=checkpoint sourcetype="checkpoint:conntable" earliest=-1h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Connection table utilization monitoring:**
```spl
index=checkpoint sourcetype="checkpoint:conntable" earliest=-4h
| rex field=conn_table "(?i)(?<current>\d+).*(?<peak>\d+).*(?<limit>\d+)"
| eval current=tonumber(current)
| eval peak=tonumber(peak)
| eval limit=tonumber(limit)
| where isnotnull(current) AND isnotnull(limit)
| eval util_pct=round(100*current/limit, 1)
| eval peak_pct=round(100*peak/limit, 1)
| bin _time span=1m
| stats latest(current) as current_conns latest(peak) as peak_conns latest(limit) as max_limit latest(util_pct) as util_pct latest(peak_pct) as peak_pct by _time, host
| eval severity=case(
    util_pct > 90, "CRITICAL -- connection table near capacity (".util_pct."%), new connections will be dropped",
    util_pct > 75, "WARNING -- connection table at ".util_pct."% capacity",
    util_pct > 60, "INFO -- connection table utilization trending up",
    1==1, "OK")
| where severity != "OK"
| table _time, host, current_conns, peak_conns, max_limit, util_pct, peak_pct, severity
| sort severity, -util_pct
```

**Secondary search -- Connection table growth rate:**
```spl
index=checkpoint sourcetype="checkpoint:conntable" earliest=-4h
| rex field=conn_table "(?i)(?<current>\d+)"
| eval current=tonumber(current)
| where isnotnull(current)
| bin _time span=5m
| stats latest(current) as conns by _time, host
| sort host, _time
| streamstats current=f last(conns) as prev_conns last(_time) as prev_time by host
| eval growth_rate=round((conns - prev_conns)/(((_time - prev_time)/60)), 0)
| where growth_rate > 1000
| eval severity="WARNING -- rapid connection growth (".growth_rate." conns/min)"
| table _time, host, conns, growth_rate, severity
```

### Step 3 — - Validate
(a) CLI (expert mode): `fw tab -t connections -s` -- show current/peak/limit.
(b) CLI: `cpview` > Overview > Connections -- real-time connection count.
(c) CLI: `fw ctl pstat` -- verify connection table statistics.

### Step 4 — - Operationalize
Dashboard ("Check Point -- Connection Table"):
* Row 1 -- Single-value: "Current connections", "Utilization (%)", "Table limit".
* Row 2 -- Connection table utilization timechart.
* Row 3 -- Growth rate analysis.

Alerting:
* Critical (>90% utilization): immediate action required.
* Warning (>75% utilization): plan capacity increase.

### Step 5 — - Troubleshooting

* **Connection table filling rapidly** -- Possible DoS/DDoS or scanning. Check top connection sources: `fw tab -t connections | sort | uniq -c | sort -rn | head 20`. Consider aggressive timeout tuning.

* **Connection limit too low** -- Increase limit: `fw ctl set int fwconn_max_connections <value>` (temporary). Permanent: edit `$FWDIR/boot/modules/fwkern.conf` and add `fwconn_max_connections=<value>`. Requires reboot.

* **Stale connections not timing out** -- Check timeout values: `fw ctl get int fw_tcp_session_timeout`. Default TCP timeout is 3600s (1 hour). Reduce for short-lived connections. Consider enabling aggressive aging: `fw ctl set int fw_aggressive_aging_timeout <seconds>`.

## SPL

```spl
index=firewall sourcetype="cp_log" earliest=-4h
| where match(lower(product),"(?i)firewall") AND (match(lower(logdesc),"(?i)connection.*table|conn.*limit|aggressive.aging") OR isnotnull(connections_count))
| eval gw=coalesce(orig, src, hostname)
| eval conn_count=coalesce(connections_count, concurrent_connections)
| eval conn_limit=coalesce(connections_limit, table_limit)
| eval util_pct=if(isnotnull(conn_limit) AND conn_limit>0, round(100*conn_count/conn_limit,1), null())
| stats latest(conn_count) as conns latest(util_pct) as util_pct by gw
| where util_pct > 70 OR match(lower(logdesc),"(?i)aggressive.aging")
| sort -util_pct
```

## Visualization

Gauge (connection table utilization %), Line chart (connections over time), Single value (peak utilization today), Table (gateways approaching limit).

## Known False Positives

Large downloads, more remote users, and new sites can use more connections than a quiet baseline from last month.

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
