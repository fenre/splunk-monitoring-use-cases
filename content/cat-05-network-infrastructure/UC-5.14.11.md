<!-- AUTO-GENERATED from UC-5.14.11.json — DO NOT EDIT -->

---
id: "5.14.11"
title: "Varnish Thread Pool Queue Length (thread_queue_len)"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.11 · Varnish Thread Pool Queue Length (thread_queue_len)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We watch varnish thread pool queue length (thread_queue_len) and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Queued threads mean requests wait before VCL runs.

## Value

Operations teams monitor Varnish thread pool queue depth and thread creation failures, detecting request processing bottlenecks before dropped connections occur.

## Implementation

Poll every 30s via scripted input to HEC; flatten counter names per version.

## Detailed Implementation

### Prerequisites
* Varnish statistics collected via `varnishstat` or Varnish's Prometheus exporter forwarded to Splunk. Key counters: `MAIN.thread_queue_len` (requests waiting for a thread), `MAIN.threads`, `MAIN.threads_limited`, `MAIN.threads_created`, `MAIN.threads_destroyed`, `MAIN.threads_failed`. Data in `index=proxy` with `sourcetype=varnish:stats`.
* Varnish thread pools: configurable via `-p thread_pool_min`, `-p thread_pool_max`, `-p thread_pools`. When all threads are busy, new requests queue. `thread_queue_len > 0` sustained means Varnish is under thread pressure. If the queue exceeds `thread_pool_queue_limit`, requests are dropped.

### Step 1 — - Configure data collection
Collect varnishstat periodically:
```bash
# Cron or scripted input every 60s
varnishstat -1 -j > /var/log/varnish/varnishstat.json
```
Or use Splunk scripted input:
```
# inputs.conf
[script:///opt/splunk/etc/apps/TA-varnish/bin/varnishstat_collect.sh]
interval = 60
sourcetype = varnish:stats
index = proxy
```
Verify:
```spl
index=proxy sourcetype="varnish:stats" earliest=-4h
| spath input=_raw path="MAIN.thread_queue_len.value" output=queue_len
| stats avg(queue_len) as avg_queue max(queue_len) as max_queue
```

### Step 2 — - Create the search and alert

**Primary search -- Thread pool saturation:**
```spl
index=proxy sourcetype="varnish:stats" earliest=-4h
| spath input=_raw path="MAIN.thread_queue_len.value" output=queue_len
| spath input=_raw path="MAIN.threads.value" output=active_threads
| spath input=_raw path="MAIN.threads_limited.value" output=threads_limited
| spath input=_raw path="MAIN.threads_failed.value" output=threads_failed
| eval queue_len=tonumber(queue_len), active_threads=tonumber(active_threads), threads_limited=tonumber(threads_limited), threads_failed=tonumber(threads_failed)
| bin _time span=5m
| stats avg(queue_len) as avg_queue max(queue_len) as max_queue avg(active_threads) as avg_threads latest(threads_limited) as limited latest(threads_failed) as failed by _time
| eval severity=case(max_queue > 100, "CRITICAL -- deep thread queue (max=".max_queue.")", avg_queue > 10, "HIGH -- sustained queuing", limited > 0, "WARNING -- thread creation limited", failed > 0, "CRITICAL -- thread creation failures", 1==1, "OK")
| where severity != "OK"
| table _time, avg_threads, avg_queue, max_queue, limited, failed, severity
```

### Step 3 — - Validate
(a) `varnishstat -1 | grep -E "thread_queue_len|threads|threads_limited"`.
(b) Load test to exhaust threads and verify queue_len increases.
(c) Check configured limits: `varnishadm param.show thread_pool_max`.

### Step 4 — - Operationalize
Dashboard ("Varnish -- Thread Pool"):
* Row 1 -- Single-value: "Queue length", "Active threads", "Limited events", "Failed events".
* Row 2 -- Thread queue timechart.

Alerting:
* Critical (queue_len > 100 or threads_failed > 0): requests being dropped.
* High (queue_len > 10 sustained): approaching saturation.

### Step 5 — - Troubleshooting

* **Queue growing but threads not at max** -- Thread creation is being throttled by `thread_pool_add_delay` (default 0). Check with `varnishadm param.show thread_pool_add_delay`.

* **threads_limited > 0** -- `thread_pool_max` has been reached. Increase it: `varnishadm param.set thread_pool_max 5000`. Monitor memory impact.

* **threads_failed > 0** -- OS-level limit. Check: `ulimit -u` (max user processes) and `/proc/sys/kernel/threads-max`.

## SPL

```spl
index=proxy sourcetype="varnish:stats"
| eval tql=tonumber(thread_queue_len)
| where tql > 0
| timechart span=1m max(tql) as thread_queue_len by host
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Thread Pool Queue Length (thread_queue_len)» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/reference/varnishstat.html)
