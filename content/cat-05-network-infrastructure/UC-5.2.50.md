<!-- AUTO-GENERATED from UC-5.2.50.json — DO NOT EDIT -->

---
id: "5.2.50"
title: "Check Point CoreXL CPU Distribution (Check Point)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.50 · Check Point CoreXL CPU Distribution (Check Point)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We look at per-core load on the gateway so a hot engine on one worker does not become packet loss and mystery slowness for everyone else.*

---

## Description

CoreXL distributes firewall inspection across multiple CPU cores (Firewall Worker instances). Uneven load distribution — where one core saturates while others idle — reduces effective throughput and causes packet drops on that core. This often happens when large flows or specific protocols always hash to the same core. Detecting core imbalance before it causes visible packet loss prevents elusive intermittent connectivity issues.

## Value

Operations teams monitor Check Point CoreXL CPU distribution across firewall workers, detecting load imbalance hotspots that create performance bottlenecks despite available CPU capacity.

## Implementation

Use `fw ctl multik stat` via scripted input (interval 300s) to capture per-core connection counts and CPU. Parse core ID and utilization. Alert when any single core exceeds 85% while the gateway average is below 50% — classic imbalance. Correlate with `fwaccel` to identify non-accelerated heavy flows. Tune CoreXL instance count and affinity after analysis.

## Detailed Implementation

### Prerequisites
* Check Point CoreXL CPU distribution data. Data in `index=checkpoint` with `sourcetype=cp_log` or custom scripted input from `fw ctl multik stat`. Key fields: `instance_id`, `connections`, `cpu_usage`, `packets`.
* CoreXL: distributes firewall inspection across multiple CPU cores (Firewall Worker instances / fw_worker_X). Uneven load distribution -- where one worker handles disproportionate traffic -- creates a bottleneck despite overall CPU availability. Monitoring: `fw ctl multik stat`, `fw ctl affinity -l -a`.

### Step 1 — - Configure data collection
```
# Custom scripted input for CoreXL stats
# inputs.conf
[script:///opt/splunk/etc/apps/checkpoint_inputs/bin/corexl_stats.sh]
interval = 300
sourcetype = checkpoint:corexl
index = checkpoint
disabled = false

# corexl_stats.sh
#!/bin/bash
echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "hostname=$(hostname)"
fw ctl multik stat 2>/dev/null | while read line; do echo "corexl_stat="$line""; done
fw ctl multik get_mode 2>/dev/null | while read line; do echo "corexl_mode="$line""; done
```
Verify:
```spl
index=checkpoint sourcetype="checkpoint:corexl" earliest=-1h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- CoreXL CPU distribution analysis:**
```spl
index=checkpoint sourcetype="checkpoint:corexl" earliest=-4h
| rex field=corexl_stat "(?i)(?<instance>\d+)\s+(?<conns>\d+)\s+(?<pkts>\d+)"
| where isnotnull(instance)
| eval instance=tonumber(instance)
| eval conns=tonumber(conns)
| eval pkts=tonumber(pkts)
| bin _time span=5m
| stats sum(conns) as total_conns sum(pkts) as total_pkts avg(conns) as avg_conns max(conns) as max_conns values(instance) as instances dc(instance) as num_workers by _time, host
| eval max_worker_pct=if(total_conns > 0, round(100*max_conns/total_conns, 1), 0)
| eval imbalance_ratio=if(avg_conns > 0, round(max_conns/avg_conns, 2), 0)
| eval severity=case(
    imbalance_ratio > 3, "CRITICAL -- severe CoreXL imbalance (hottest worker ".imbalance_ratio."x average)",
    imbalance_ratio > 2, "WARNING -- CoreXL imbalance detected",
    max_worker_pct > 40 AND num_workers > 4, "INFO -- one worker handling >40% of connections",
    1==1, "OK")
| where severity != "OK"
| table _time, host, num_workers, total_conns, avg_conns, max_conns, imbalance_ratio, severity
| sort severity
```

### Step 3 — - Validate
(a) CLI (expert mode): `fw ctl multik stat` -- show per-instance connection and packet counts.
(b) CLI: `fw ctl affinity -l -a` -- show CPU affinity assignments for each worker.
(c) CLI: `cpview` -- real-time monitoring of per-core CPU usage.

### Step 4 — - Operationalize
Dashboard ("Check Point -- CoreXL CPU Distribution"):
* Row 1 -- Single-value: "FW workers", "Hottest worker (%)", "Imbalance ratio".
* Row 2 -- Per-worker connection distribution.

Alert: Critical (imbalance ratio > 3x): performance bottleneck on single core.

### Step 5 — - Troubleshooting

* **Single worker overloaded** -- Check affinity: `fw ctl affinity -l -a`. Large flows (e.g., backup, streaming) may hash to one worker. Consider enabling Dynamic Dispatcher: `fw ctl multik set_mode 4`.

* **CoreXL hash imbalance** -- Default hash uses src/dst IP. Environments with few large talkers benefit from adding port to hash: `fw ctl set int fwmultik_use_ports 1`.

* **Insufficient workers** -- Check total available: `fw ctl multik get_mode`. Add workers if CPU cores are available. Requires reboot after change: `cpconfig` > Configure CoreXL.

## SPL

```spl
index=firewall sourcetype="cp_log" earliest=-4h
| where match(lower(product),"(?i)corexl|multik|fw_worker")
| eval gw=coalesce(orig, src, hostname)
| eval core_id=coalesce(core_id, fw_instance, worker_id)
| eval cpu_pct=coalesce(cpu_usage, cpu_pct, cpu_util)
| stats avg(cpu_pct) as avg_cpu max(cpu_pct) as max_cpu by gw, core_id
| eventstats avg(avg_cpu) as gw_avg by gw
| eval imbalance=round(max_cpu - gw_avg, 1)
| where imbalance > 30 OR max_cpu > 85
| sort -imbalance
```

## Visualization

Bar chart (CPU per core), Heatmap (core × time), Table (imbalanced gateways), Line chart (max core CPU trend).

## Known False Positives

Bursts, elephant flows, and short spikes can unbalance one core for minutes without a lasting performance problem.

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
