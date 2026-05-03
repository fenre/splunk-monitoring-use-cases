<!-- AUTO-GENERATED from UC-5.11.10.json — DO NOT EDIT -->

---
id: "5.11.10"
title: "Telegraf gNMI Collector Pipeline Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.11.10 · Telegraf gNMI Collector Pipeline Health

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know when the collector that ingests gNMI is falling behind, so a broken pipe does not look like a perfect network in Splunk.*

---

## Description

If your Telegraf collector goes down or loses connectivity to a target device, all gNMI telemetry for that device stops silently — dashboards freeze at last-known-good values and alerts never fire. Monitoring the Telegraf pipeline itself (gather time, buffer usage, write failures, active connections) is essential to trust the data flowing through it.

## Value

Operations teams monitor the health of the Telegraf gNMI collector pipeline itself, ensuring the telemetry infrastructure that feeds all gNMI-based monitoring UCs is functioning correctly with no silent data loss.

## Implementation

Enable Telegraf `internal` input plugin to emit self-monitoring metrics every 60 seconds. Monitor `gather_time_ns` (should be <5s for healthy connections), `metrics_gathered` (should be >0), and `buffer_size` (should not grow unbounded). Alert when a specific device's gather count drops to zero (connection lost). Track `write_errors` to detect HEC ingestion issues. Deploy multiple Telegraf instances with overlapping targets for redundancy.

## Detailed Implementation

### Prerequisites
- Telegraf deployed as the gNMI collector pipeline. This UC monitors the health of Telegraf itself — the collector is the critical middleware between network devices and Splunk. If Telegraf fails or falls behind, all gNMI data stops flowing.
- Telegraf internal metrics must be enabled. In `telegraf.conf`, add:
```toml
[[inputs.internal]]
  collect_memstats = true
  name_prefix = "telegraf_"
```
This generates metrics like `telegraf_internal_gather_errors`, `telegraf_internal_agent_metrics_gathered`, `telegraf_internal_write_metrics_written`, `telegraf_internal_write_buffer_size`, etc.
- Telegraf should output its own internal metrics to the same Splunk HEC endpoint (or a dedicated `telegraf_health` metrics index).
- Build a `telegraf_collectors.csv` lookup: `host,expected_devices,expected_subscriptions,owner` for each Telegraf collector instance.
- Understanding the pipeline: Telegraf `inputs.gnmi` → internal buffer → `outputs.http` (Splunk HEC) → metrics index. Each stage can fail independently: gNMI connection drops (input), buffer overflow (internal), HEC rejection (output).

### Step 1 — Configure data collection
Verify Telegraf internal metrics in Splunk:
```spl
| mcatalog values(metric_name) WHERE index=gnmi_metrics metric_name="telegraf_*"
```
Expected metrics: `telegraf_internal_gather_errors`, `telegraf_internal_write_metrics_written`, `telegraf_internal_write_buffer_size`, `telegraf_internal_memstats_alloc`.

Verify all collector instances are reporting:
```spl
| mstats latest("telegraf_internal_agent_metrics_gathered") AS gathered WHERE index=gnmi_metrics BY host span=5m
| lookup telegraf_collectors.csv host OUTPUT expected_devices owner
| eval status=if(isnotnull(gathered) AND gathered > 0, "Active", "SILENT")
| sort status
```

### Step 2 — Create the search and alert

**Primary search — Collector pipeline health:**
```spl
| mstats rate_avg("telegraf_internal_agent_metrics_gathered") AS gather_rate rate_avg("telegraf_internal_write_metrics_written") AS write_rate latest("telegraf_internal_write_buffer_size") AS buffer_size latest("telegraf_internal_gather_errors") AS gather_errors WHERE index=gnmi_metrics BY host span=1m
| eval gather_per_min=round(gather_rate*60, 0)
| eval write_per_min=round(write_rate*60, 0)
| eval pipeline_efficiency=if(gather_per_min > 0, round(100*write_per_min/gather_per_min, 1), 0)
| eval buffer_status=case(buffer_size > 90000, "CRITICAL-FULL", buffer_size > 50000, "WARNING-FILLING", 1==1, "OK")
| eval status=case(pipeline_efficiency < 80, "DEGRADED", buffer_status!="OK", buffer_status, gather_errors > 0, "INPUT-ERRORS", 1==1, "HEALTHY")
| where status!="HEALTHY"
| sort status
```

#### Understanding this SPL: Monitors the three critical pipeline stages: (1) `gather_rate` — how fast Telegraf collects data from gNMI devices (input); (2) `write_rate` — how fast it writes to Splunk HEC (output); (3) `buffer_size` — the internal buffer (backpressure indicator). If gather > write, the buffer fills — eventually Telegraf drops data. Pipeline efficiency < 80% means Splunk HEC is not accepting data fast enough.

**gNMI connection health — device-level:**
```spl
| mstats rate_avg("telegraf_internal_gather_errors") AS err_rate WHERE index=gnmi_metrics BY host span=5m
| eval errors_per_hour=round(err_rate*3600, 0)
| where errors_per_hour > 0
| lookup telegraf_collectors.csv host OUTPUT expected_devices
| sort -errors_per_hour
```

#### Understanding this SPL: Gather errors indicate gNMI connection problems — device unreachable, authentication failure, subscription rejected, or YANG path not supported. Each error means data loss for that collection interval.

**Collector silence detection (Telegraf down):**
```spl
| mstats latest("telegraf_internal_agent_metrics_gathered") AS last_gather WHERE index=gnmi_metrics BY host
| eval minutes_since_data=round((now()-_time)/60, 1)
| where minutes_since_data > 5
| lookup telegraf_collectors.csv host OUTPUT expected_devices owner
| eval severity=case(minutes_since_data > 30, "CRITICAL", minutes_since_data > 10, "HIGH", 1==1, "WARNING")
| sort -minutes_since_data
```

#### Understanding this SPL: If a Telegraf collector stops reporting internal metrics, it's either crashed, network-partitioned from Splunk, or the HEC token is expired/revoked. This is the most critical alert — a silent collector means ALL gNMI data from ALL devices it monitors is lost.

### Step 3 — Validate
(a) Check Telegraf logs: `journalctl -u telegraf --since "1 hour ago"`. Look for connection errors, write failures, and buffer warnings.
(b) Verify pipeline efficiency: the gather rate should approximately equal the write rate. If write rate is consistently lower, HEC is throttling or the token is misconfigured.
(c) Test: stop Telegraf on a collector and verify the silence detection alert fires within 5 minutes.

### Step 4 — Operationalize
Dashboard ("Telemetry — Collector Pipeline Health"):
- Row 1 — Single-value tiles: "Active collectors", "Silent collectors", "Pipeline efficiency (min)", "Buffer warnings".
- Row 2 — Table: collector host, gather_rate, write_rate, buffer_size, pipeline_efficiency, status.
- Row 3 — Timechart: gather vs. write rates over 24h (should be approximately equal).
- Row 4 — Error timeline: gather errors and write errors over 24h by collector.

Alerting:
- Critical (collector silent for > 10 minutes): page operations — all gNMI monitoring from this collector is offline.
- Critical (buffer > 90% full): HEC is not accepting data — check HEC health and token validity.
- High (pipeline efficiency < 80% for 15 minutes): Splunk HEC is throttling — increase HEC throughput or add a collector.
- Warning (gather errors increasing): gNMI devices may be unreachable or rejecting subscriptions.

Runbook:
1. **Collector silent**: SSH to the collector host. Check if Telegraf process is running (`systemctl status telegraf`). If crashed, check logs for the cause and restart. If running but no output, check HEC connectivity (`curl -k https://<splunk>:8088/services/collector/health`).
2. **Buffer filling**: Splunk HEC is the bottleneck. Check HEC health: `| rest /services/data/inputs/http` for status. Increase `metric_buffer_limit` in Telegraf if HEC is temporarily slow. Long-term: add HEC capacity.
3. **gNMI gather errors**: Check device gRPC service status. Common causes: device reboot, certificate expiry (TLS), password change, ACL blocking gRPC port.

### Step 5 — Troubleshooting

- **Telegraf internal metrics not appearing** — The `[[inputs.internal]]` plugin may not be configured. Add it to `telegraf.conf` and restart Telegraf.

- **Buffer size always 0** — This is good — it means writes keep up with gathers. The buffer only fills when there's backpressure.

- **High gather rate but low write rate** — Splunk HEC is the bottleneck. Check: (a) HEC token is valid and not disabled, (b) the target index exists and is not frozen, (c) Splunk indexer queue is not full (check `_internal` for indexer pipeline stats).

- **Telegraf memory growing over time** — Possible memory leak in the gNMI plugin or output plugin. Check Telegraf version for known issues. Monitor with `telegraf_internal_memstats_alloc` and restart periodically as a workaround.

## SPL

```spl
| mstats avg("internal_gather.gather_time_ns") AS gather_ns, latest("internal_gather.metrics_gathered") AS gathered WHERE index=gnmi_metrics BY host, input span=5m
| eval gather_ms=round(gather_ns/1000000, 1)
| where gather_ms > 5000 OR gathered=0
| table _time, host, input, gather_ms, gathered
| sort -gather_ms
```

## Visualization

Table (collector health matrix), Line chart (gather time per device), Single value (total active subscriptions), Alert list (stale collectors).

## Known False Positives

Telemetry pauses during device reboots, cert renewals, or transport changes; subscription restarts and path renames can look like drops without a live fault.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
