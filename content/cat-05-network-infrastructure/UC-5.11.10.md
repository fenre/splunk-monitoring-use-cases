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

If your Telegraf collector goes down or loses connectivity to a target device, all gNMI telemetry for that device stops silently — dashboards freeze at last-known-good values and alerts never fire. Monitoring the Telegraf pipeline itself (gather time, buffer usage, write failures, active connections) is essential to trust the data flowing through it.

## Implementation

Enable Telegraf `internal` input plugin to emit self-monitoring metrics every 60 seconds. Monitor `gather_time_ns` (should be <5s for healthy connections), `metrics_gathered` (should be >0), and `buffer_size` (should not grow unbounded). Alert when a specific device's gather count drops to zero (connection lost). Track `write_errors` to detect HEC ingestion issues. Deploy multiple Telegraf instances with overlapping targets for redundancy.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: Telegraf internal metrics → Splunk HEC.
- Ensure the following data sources are available: Telegraf `internal` metrics (`internal_gather`, `internal_write`, `internal_memstats`); `sourcetype=telegraf:internal`.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Enable Telegraf `internal` input plugin to emit self-monitoring metrics every 60 seconds. Monitor `gather_time_ns` (should be <5s for healthy connections), `metrics_gathered` (should be >0), and `buffer_size` (should not grow unbounded). Alert when a specific device's gather count drops to zero (connection lost). Track `write_errors` to detect HEC ingestion issues. Deploy multiple Telegraf instances with overlapping targets for redundancy.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats avg("internal_gather.gather_time_ns") AS gather_ns, latest("internal_gather.metrics_gathered") AS gathered WHERE index=gnmi_metrics BY host, input span=5m
| eval gather_ms=round(gather_ns/1000000, 1)
| where gather_ms > 5000 OR gathered=0
| table _time, host, input, gather_ms, gathered
| sort -gather_ms
```

#### Understanding this SPL

**Telegraf gNMI Collector Pipeline Health** — If your Telegraf collector goes down or loses connectivity to a target device, all gNMI telemetry for that device stops silently — dashboards freeze at last-known-good values and alerts never fire. Monitoring the Telegraf pipeline itself (gather time, buffer usage, write failures, active connections) is essential to trust the data flowing through it.

Documented **Data sources**: Telegraf `internal` metrics (`internal_gather`, `internal_write`, `internal_memstats`); `sourcetype=telegraf:internal`. **App/TA** (typical add-on context): Telegraf internal metrics → Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gnmi_metrics.

**Pipeline walkthrough**

- Uses `mstats` to query metrics indexes (pre-aggregated metric data).
- `eval` defines or adjusts **gather_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where gather_ms > 5000 OR gathered=0` — typically the threshold or rule expression for this monitoring goal.
- Pipeline stage (see **Telegraf gNMI Collector Pipeline Health**): table _time, host, input, gather_ms, gathered
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

CIM and metrics: Telegraf internal and pipeline health is **mstats** on the collector; it is unrelated to CIM DMX on network devices.


### Step 3 — Validate
On the Telegraf host, read Telegraf log + internal metrics for the `inputs.gnmi` plugin, HEC response codes, and queue depth; match gaps to gNMI subscription restarts in device logs.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (collector health matrix), Line chart (gather time per device), Single value (total active subscriptions), Alert list (stale collectors).

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
