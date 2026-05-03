<!-- AUTO-GENERATED from UC-5.9.53.json — DO NOT EDIT -->

---
id: "5.9.53"
title: "Cross-Platform Network Correlation"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.53 · Cross-Platform Network Correlation

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Anomaly, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*When something is slow, we check the network, the application, and the servers all at the same time in one place, so we can immediately tell which part is broken instead of having three teams argue about whose fault it is.*

---

## Description

Correlates ThousandEyes network performance data with application performance (APM) and infrastructure metrics to determine whether user-facing degradation is caused by the network, the application, or the infrastructure. This is the 'single pane of glass' correlation that justifies having all telemetry in Splunk.

## Value

When users report slowness, three teams point fingers: the network team says the network is fine, the application team says the app is fine, and the infrastructure team says the servers are fine. This UC eliminates the finger-pointing by correlating all three data sources in a single search. If ThousandEyes shows high latency (network) AND APM shows normal response times (application), the problem is network. If ThousandEyes shows normal latency AND APM shows high response times, the problem is the application. If infrastructure metrics show high CPU/memory, the problem is infrastructure. The correlation happens in Splunk because that's where all the data lives — ThousandEyes can't see APM data, and APM can't see network path data.

## Implementation

Join ThousandEyes network metrics with APM and infrastructure data using the target host or IP address as the correlation key. This requires consistent naming across data sources.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.1 apply.
- **At least one additional data source** — APM data (Splunk APM, AppDynamics, or similar) or infrastructure metrics (Splunk Infrastructure Monitoring, collectd, Prometheus) indexed in Splunk.
- **Consistent correlation keys** — The target IP/hostname in ThousandEyes (`server.address`) must map to the host/service identifier in your APM and infrastructure data. If they don't match natively, create a lookup table.

### Step 1 — Build the correlation lookup
If `server.address` in ThousandEyes doesn't match your APM/infra host naming:
```csv
target_host,apm_service,infra_host,thousandeyes_target
10.1.2.3,web-frontend,web-prod-01,10.1.2.3
app.example.com,api-gateway,api-prod-02,app.example.com
```
Upload as `thousandeyes_host_mapping.csv` and create a lookup definition.

### Step 2 — Create the correlation search
**Network + Infrastructure:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server" earliest=-1h
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss by server.address
| eval avg_latency_ms=round(avg_latency*1000,1)
| rename server.address as target_host
| lookup thousandeyes_host_mapping.csv target_host OUTPUT infra_host, apm_service
| join type=left infra_host [search index=em_metrics earliest=-1h | stats avg(cpu.utilization) as avg_cpu avg(memory.utilization) as avg_mem by host | rename host as infra_host]
| eval network_health=case(avg_latency_ms < 50 AND avg_loss < 0.5, "Good", avg_latency_ms < 100 AND avg_loss < 2, "Degraded", 1=1, "Critical")
| eval infra_health=case(avg_cpu < 70 AND avg_mem < 80, "Good", avg_cpu < 90 AND avg_mem < 90, "Degraded", 1=1, "Critical")
| table target_host, apm_service, avg_latency_ms, avg_loss, network_health, avg_cpu, avg_mem, infra_health
```

**Network + APM overlay (timechart):**
```spl
`stream_index` thousandeyes.test.type="http-server" server.address="app.example.com" earliest=-24h
| timechart span=5m avg(http.client.request.duration) as te_ttfb_s
| eval te_ttfb_ms=round(te_ttfb_s*1000,1)
| appendcols [search index=apm service="api-gateway" earliest=-24h | timechart span=5m avg(duration) as apm_response_ms]
| fields _time, te_ttfb_ms, apm_response_ms
```

### Step 3 — Validate
During a known maintenance window or load test, verify that the correlation shows degradation in the expected domain (network, app, or infra).

### Step 4 — Operationalize
**Decision tree for incident triage:**

| ThousandEyes Network | APM Response | Infrastructure | Root Cause |
|---|---|---|---|
| Degraded | Normal | Normal | Network path issue |
| Normal | Degraded | Normal | Application bug |
| Normal | Degraded | Degraded | Infrastructure capacity |
| Degraded | Degraded | Normal | Network causing app impact |
| Degraded | Degraded | Degraded | Cascading failure |

Build this as a Splunk dashboard with conditional formatting.

### Step 5 — Troubleshooting
- **Join returns no results** — Verify the correlation key matches. Run each subsearch independently first.
- **Temporal gaps** — Widen the time range or increase the `span` in timechart.
- **Missing APM/infra data** — This UC requires at least one other data source. If only ThousandEyes data is available, use UC-5.9.50 (ITSI) instead.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server" earliest=-1h
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss by thousandeyes.test.name, server.address
| eval avg_latency_ms=round(avg_latency*1000,1)
| where avg_latency_ms > 100 OR avg_loss > 1
| eval network_issue="true"
| rename server.address as target_host
| join type=left target_host [search index=em_metrics OR index=apm earliest=-1h | stats avg(response_time) as avg_app_response_ms avg(cpu_pct) as avg_cpu by target_host]
| table thousandeyes.test.name, target_host, avg_latency_ms, avg_loss, avg_app_response_ms, avg_cpu, network_issue
```

## Visualization

(1) Multi-panel dashboard: network metrics (ThousandEyes), application response times (APM), infrastructure utilization side by side. (2) Correlation table: per-host network vs application vs infrastructure health. (3) Timeline overlay: network latency and application response time on the same timechart.

## Known False Positives

**Correlation key mismatch.** ThousandEyes uses `server.address` (IP or hostname), APM may use service names, and infrastructure monitoring may use hostnames. If the naming doesn't match, the join produces empty results. Use a lookup table to map between naming conventions.

**Temporal misalignment.** ThousandEyes tests run at fixed intervals (e.g., every 2 minutes), APM samples continuously, and infrastructure metrics may report every 10 seconds. Time windows must be broad enough to capture data from all sources.

**Correlation ≠ causation.** High network latency and high application response time at the same time doesn't prove the network caused the application slowness. The application could be independently slow, causing network retransmissions. Use ThousandEyes path visualization (UC-5.9.5) to confirm network-layer issues.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [Splunk ITSI documentation](https://docs.splunk.com/Documentation/ITSI)
- [Splunk Observability Cloud](https://docs.splunk.com/observability/en/)
