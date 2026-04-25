<!-- AUTO-GENERATED from UC-5.3.28.json — DO NOT EDIT -->

---
id: "5.3.28"
title: "Citrix ADC TCP Connection Multiplexing Analysis"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.3.28 · Citrix ADC TCP Connection Multiplexing Analysis

## Description

Citrix ADC multiplexes many client connections onto fewer server-side connections through reuse and keep-alive, improving efficiency on backends. A falling reuse rate with rising front-end TPS, paired with high tail latency, can signal pool saturation, keep-alive misconfiguration, or backend slowness. The goal is to connect traffic shape to latency before servers exhaust ephemeral ports or file descriptors.

## Value

Citrix ADC multiplexes many client connections onto fewer server-side connections through reuse and keep-alive, improving efficiency on backends. A falling reuse rate with rising front-end TPS, paired with high tail latency, can signal pool saturation, keep-alive misconfiguration, or backend slowness. The goal is to connect traffic shape to latency before servers exhaust ephemeral ports or file descriptors.

## Implementation

Populate `citrix:netscaler:perf` from NITRO with TCP and HTTP vserver service metrics where available, and align AppFlow-derived TPS and response-time percentiles. Normalize field names in props if your TA uses custom aliases. Create baselines for reuse and p95 by application; alert when reuse drops and p95 increases together during steady load.

## Detailed Implementation

Prerequisites
• Metrics fields in `index=netscaler` from NITRO poll or HEC: connection reuse, keep-alive, TPS, response-time histograms.
• Documented mapping from vserver to microservice SLOs.

Step 1 — Configure data collection
Set poll interval 1–5 minutes; align system clock. Store raw counters and precompute deltas in scheduled search if needed (delta of new connections, etc.).

Step 2 — Create the search and alert
Adjust `coalesce` field list to your deployment. Use anomaly detection (predict or ML Toolkit) for optional adaptive thresholds on p95. Alert when reuse drops below baseline and p95 exceeds SLO for two consecutive windows.

Step 3 — Validate
Compare vservers, services, and load-balancing state in the Citrix ADC management view or command line for the same time window and objects.
Step 4 — Operationalize
Hand off to platform owners with a recommendation tree: check pool size, check backend time, review TCP parameters on vserver and service group.

## SPL

```spl
index=netscaler (sourcetype="citrix:netscaler:perf" OR sourcetype="citrix:netscaler:appflow")
| eval cps=coalesce(connections_per_sec, http_reqs_per_sec, 0), reuse_pct=coalesce(tcp_reuse_percent, connection_reuse_pct, 0), p95_latency_ms=coalesce(p95_resp_time_ms, app_resp_time_95, 0)
| bin _time span=5m
| stats avg(cps) as tps, avg(reuse_pct) as avg_reuse, avg(p95_latency_ms) as p95_ms by _time, host, lbvserver
| where p95_ms > 500 AND avg_reuse < 30 AND tps > 0
| table _time, host, lbvserver, tps, avg_reuse, p95_ms
```

## Visualization

Dual-axis line chart: TPS and reuse percent; scatter of reuse versus p95 latency; table of offending vservers.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — Load balancing and connection management](https://docs.citrix.com/en-us/citrix-adc/current-release/load-balancing.html)
