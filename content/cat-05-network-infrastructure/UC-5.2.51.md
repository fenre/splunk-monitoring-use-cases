<!-- AUTO-GENERATED from UC-5.2.51.json — DO NOT EDIT -->

---
id: "5.2.51"
title: "Check Point Log Rate and Capacity (Check Point)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.51 · Check Point Log Rate and Capacity (Check Point)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch log rate and volume from the gateway so a flood of events or a near-full buffer is a warning before you lose the trail entirely.*

---

## Description

Check Point gateways forward logs to the management server or Log Server. When log rate exceeds the management capacity or network bandwidth, logs are queued, delayed, or dropped — creating blind spots in security monitoring. Tracking log rate per gateway and comparing to Log Server capacity prevents log loss before it impacts compliance and incident detection.

## Value

Operations teams monitor Check Point log forwarding rate and detect log gaps, ensuring continuous visibility and preventing blind spots from log capacity exhaustion or forwarding failures.

## Implementation

Baseline event rate per gateway. Alert on sudden spikes (possible attack or debug logging left enabled) and drops (log forwarding failure or connectivity issue). Monitor Log Server disk and queue depth. Correlate log drops with gateway CPU and network congestion.

## Detailed Implementation

### Prerequisites
* Check Point log rate and capacity data. Data in `index=checkpoint` with `sourcetype=cp_log` or custom scripted input. Key fields: `log_rate`, `log_queue`, `disk_usage`, `log_server`.
* Check Point gateways forward logs to the management server or dedicated Log Server via SIC-encrypted channel (TCP 257). When log rate exceeds management capacity, the gateway buffers logs locally. If local buffer fills, logs are dropped. Log rate capacity depends on management server/Log Server hardware. Monitoring: `fw log show`, `cpview`, and SmartConsole Logs & Monitor.

### Step 1 — - Configure data collection
```
# Custom scripted input for log rate monitoring
# inputs.conf
[script:///opt/splunk/etc/apps/checkpoint_inputs/bin/log_rate.sh]
interval = 300
sourcetype = checkpoint:lograte
index = checkpoint
disabled = false

# log_rate.sh (run on management/log server)
#!/bin/bash
echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "hostname=$(hostname)"
# Get log rate from cpview or cpstat
cpstat -f logging os 2>/dev/null | while read line; do echo "cpstat_log="$line""; done
df -h /var/log 2>/dev/null | tail -1 | while read line; do echo "disk_usage="$line""; done
```
Verify:
```spl
index=checkpoint sourcetype="checkpoint:lograte" earliest=-1h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Log rate and capacity monitoring:**
```spl
index=checkpoint sourcetype="cp_log" earliest=-4h
| bin _time span=1m
| stats count as log_rate by _time, host
| eventstats avg(log_rate) as avg_rate stdev(log_rate) as stdev_rate max(log_rate) as peak_rate by host
| eval z_score=if(stdev_rate > 0, round((log_rate - avg_rate)/stdev_rate, 2), 0)
| eval severity=case(
    log_rate > 50000, "CRITICAL -- extreme log rate may exceed capacity",
    z_score > 3 AND log_rate > 10000, "WARNING -- abnormal log rate spike",
    log_rate > 20000, "WARNING -- sustained high log rate",
    1==1, "OK")
| where severity != "OK"
| table _time, host, log_rate, avg_rate, peak_rate, z_score, severity
| sort severity, -log_rate
```

**Secondary search -- Log gap detection (missing logs):**
```spl
index=checkpoint sourcetype="cp_log" earliest=-24h
| bin _time span=5m
| stats count as log_count by _time, host
| makecontinuous _time span=5m
| fillnull value=0 log_count
| where log_count = 0
| eval severity="CRITICAL -- log gap detected (no logs for 5-minute window)"
| table _time, host, severity
```

### Step 3 — - Validate
(a) SmartConsole: Logs & Monitor > Statistics -- check log rate graph.
(b) CLI: `cpview` > Overview > Log Rate -- verify current log rate.
(c) CLI: `cpstat -f logging os` -- check log forwarding statistics and queue.

### Step 4 — - Operationalize
Dashboard ("Check Point -- Log Rate & Capacity"):
* Row 1 -- Single-value: "Current log rate (/min)", "Peak rate", "Log gaps detected".
* Row 2 -- Log rate timechart.
* Row 3 -- Log gap detection table.

Alert: Critical (log gap > 5 minutes): log forwarding failure, investigate immediately.

### Step 5 — - Troubleshooting

* **Log gaps** -- Check SIC connectivity between gateway and log server. Verify: `cpca_client lscert`. Check disk space on log server: `df -h /var/log`. Check fw buffer: `fw logswitch` may be needed.

* **Sustained high log rate** -- Review noisy rules. Enable "Log Implied Rules" selectively. Consider: dedicated Log Server, log indexing optimization, or Enable Log Compression.

* **Log server disk full** -- Implement log rotation: `fw logswitch`. Configure auto-purge in SmartConsole. Consider exporting old logs to external storage before purge.

## SPL

```spl
index=checkpoint sourcetype="cp_log" earliest=-24h
| bin _time span=5m
| stats count as events_5m by _time, orig
| eventstats avg(events_5m) as baseline by orig
| where events_5m > baseline*3 OR events_5m < baseline*0.2
| eval anomaly=if(events_5m > baseline*3, "spike", "drop")
| table _time, orig, events_5m, baseline, anomaly
```

## Visualization

Line chart (log rate per gateway), Single value (current aggregate rate), Table (anomalies), Bar chart (rate by gateway).

## Known False Positives

Backup windows, debug sessions, and compliance exports can all raise log rate without a logging-system failure.

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
