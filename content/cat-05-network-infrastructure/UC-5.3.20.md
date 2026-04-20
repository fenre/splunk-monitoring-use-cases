---
id: "5.3.20"
title: "Citrix ADC System Resource Utilization (NetScaler)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.20 · Citrix ADC System Resource Utilization (NetScaler)

## Description

Citrix ADC appliances (physical or VPX) have finite CPU, memory, and throughput capacity. Unlike general-purpose servers, ADC resource exhaustion directly impacts all applications it fronts — causing connection drops, increased latency, and SSL handshake failures. Monitoring ADC system resources enables capacity planning and prevents appliance-level bottlenecks that affect the entire application delivery infrastructure.

## Value

Citrix ADC appliances (physical or VPX) have finite CPU, memory, and throughput capacity. Unlike general-purpose servers, ADC resource exhaustion directly impacts all applications it fronts — causing connection drops, increased latency, and SSL handshake failures. Monitoring ADC system resources enables capacity planning and prevents appliance-level bottlenecks that affect the entire application delivery infrastructure.

## Implementation

Poll the NITRO API `ns` (system) resource for CPU utilization, memory usage, and packet engine stats. Also poll `ssl` stats for SSL transactions per second (TPS). Run every 5 minutes. Key thresholds: CPU above 70% average (capacity planning), CPU spike above 90% (performance impact imminent), memory above 80% (connection table pressure), SSL TPS approaching licensed limit (SSL offload bottleneck). Track packet engine CPU separately from management CPU — high management CPU with low packet CPU indicates control plane issues. Trend resource utilization to forecast when additional ADC capacity is needed.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`), NITRO API scripted input.
• Ensure the following data sources are available: `index=network` `sourcetype="citrix:netscaler:perf"` fields `cpu_use_pct`, `mgmt_cpu_use_pct`, `mem_use_pct`, `disk_use_pct`, `active_connections`, `rx_mbps`, `tx_mbps`, `ssl_tps`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll the NITRO API `ns` (system) resource for CPU utilization, memory usage, and packet engine stats. Also poll `ssl` stats for SSL transactions per second (TPS). Run every 5 minutes. Key thresholds: CPU above 70% average (capacity planning), CPU spike above 90% (performance impact imminent), memory above 80% (connection table pressure), SSL TPS approaching licensed limit (SSL offload bottleneck). Track packet engine CPU separately from management CPU — high management CPU with low packet CPU in…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="citrix:netscaler:perf"
| bin _time span=5m
| stats avg(cpu_use_pct) as avg_cpu, max(cpu_use_pct) as max_cpu,
  avg(mem_use_pct) as avg_mem, avg(active_connections) as avg_conns,
  avg(ssl_tps) as avg_ssl_tps, avg(rx_mbps) as avg_rx, avg(tx_mbps) as avg_tx by host, _time
| where avg_cpu > 70 OR avg_mem > 80 OR max_cpu > 90
| table _time, host, avg_cpu, max_cpu, avg_mem, avg_conns, avg_ssl_tps, avg_rx, avg_tx
```

Understanding this SPL

**Citrix ADC System Resource Utilization (NetScaler)** — Citrix ADC appliances (physical or VPX) have finite CPU, memory, and throughput capacity. Unlike general-purpose servers, ADC resource exhaustion directly impacts all applications it fronts — causing connection drops, increased latency, and SSL handshake failures. Monitoring ADC system resources enables capacity planning and prevents appliance-level bottlenecks that affect the entire application delivery infrastructure.

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:perf"` fields `cpu_use_pct`, `mgmt_cpu_use_pct`, `mem_use_pct`, `disk_use_pct`, `active_connections`, `rx_mbps`, `tx_mbps`, `ssl_tps`. **App/TA** (typical add-on context): Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`), NITRO API scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: citrix:netscaler:perf. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="citrix:netscaler:perf". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_cpu > 70 OR avg_mem > 80 OR max_cpu > 90` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix ADC System Resource Utilization (NetScaler)**): table _time, host, avg_cpu, max_cpu, avg_mem, avg_conns, avg_ssl_tps, avg_rx, avg_tx

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.Network by Performance.host span=5m | sort - agg_value
```

Understanding this CIM / accelerated SPL

**Citrix ADC System Resource Utilization (NetScaler)** — Citrix ADC appliances (physical or VPX) have finite CPU, memory, and throughput capacity. Unlike general-purpose servers, ADC resource exhaustion directly impacts all applications it fronts — causing connection drops, increased latency, and SSL handshake failures. Monitoring ADC system resources enables capacity planning and prevents appliance-level bottlenecks that affect the entire application delivery infrastructure.

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:perf"` fields `cpu_use_pct`, `mgmt_cpu_use_pct`, `mem_use_pct`, `disk_use_pct`, `active_connections`, `rx_mbps`, `tx_mbps`, `ssl_tps`. **App/TA** (typical add-on context): Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`), NITRO API scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance.Network` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (CPU and memory over time), Gauge (current utilization), Table (ADCs above threshold).

## SPL

```spl
index=network sourcetype="citrix:netscaler:perf"
| bin _time span=5m
| stats avg(cpu_use_pct) as avg_cpu, max(cpu_use_pct) as max_cpu,
  avg(mem_use_pct) as avg_mem, avg(active_connections) as avg_conns,
  avg(ssl_tps) as avg_ssl_tps, avg(rx_mbps) as avg_rx, avg(tx_mbps) as avg_tx by host, _time
| where avg_cpu > 70 OR avg_mem > 80 OR max_cpu > 90
| table _time, host, avg_cpu, max_cpu, avg_mem, avg_conns, avg_ssl_tps, avg_rx, avg_tx
```

## CIM SPL

```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.Network by Performance.host span=5m | sort - agg_value
```

## Visualization

Line chart (CPU and memory over time), Gauge (current utilization), Table (ADCs above threshold).

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
