<!-- AUTO-GENERATED from UC-5.3.28.json — DO NOT EDIT -->

---
id: "5.3.28"
title: "Citrix ADC TCP Connection Multiplexing Analysis"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.3.28 · Citrix ADC TCP Connection Multiplexing Analysis

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance

*We study connection reuse on the same box so a jump in multiplexing is something you can compare to a known database or long-lived flow.*

---

## Description

Citrix ADC multiplexes many client connections onto fewer server-side connections through reuse and keep-alive, improving efficiency on backends. A falling reuse rate with rising front-end TPS, paired with high tail latency, can signal pool saturation, keep-alive misconfiguration, or backend slowness. The goal is to connect traffic shape to latency before servers exhaust ephemeral ports or file descriptors.

## Value

Application delivery teams monitor Citrix ADC TCP connection multiplexing ratios and server busy errors, ensuring efficient backend connection reuse and detecting multiplexing failures.

## Implementation

Populate `citrix:netscaler:perf` from NITRO with TCP and HTTP vserver service metrics where available, and align AppFlow-derived TPS and response-time percentiles. Normalize field names in props if your TA uses custom aliases. Create baselines for reuse and p95 by application; alert when reuse drops and p95 increases together during steady load.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). NITRO API stats for TCP multiplexing. Key metrics: `server_busy_errors`, `tcp_connections_client`, `tcp_connections_server`, `surgecount`, `http_tot_requests`.
* TCP multiplexing (connection reuse): Citrix ADC maintains persistent backend TCP connections and multiplexes multiple client requests over fewer server connections. This reduces backend connection overhead. When multiplexing breaks down (server busy errors), each client request needs its own backend connection, causing connection explosion.

### Step 1 — - Configure data collection
Poll NITRO API: `GET /nitro/v1/stat/lbvserver` for per-vserver client/server connection counts. Verify:
```spl
index=netscaler sourcetype="citrix:netscaler:perf" earliest=-4h
| where isnotnull(tcp_connections_client) OR isnotnull(tcp_connections_server)
| eval ratio=round(tcp_connections_client/tcp_connections_server, 1)
| stats avg(ratio) as avg_ratio by host
```

### Step 2 — - Create the search and alert

**Primary search -- Multiplexing efficiency:**
```spl
index=netscaler sourcetype="citrix:netscaler:perf" earliest=-4h
| eval client_conns=coalesce(tcp_connections_client, clientconnections)
| eval server_conns=coalesce(tcp_connections_server, serverconnections)
| eval server_busy=coalesce(server_busy_errors, svrbusy, 0)
| eval vs=coalesce(vserver_name, vs_name)
| bin _time span=5m
| stats avg(client_conns) as avg_client avg(server_conns) as avg_server sum(server_busy) as total_busy by _time, host, vs
| eval mux_ratio=if(avg_server > 0, round(avg_client/avg_server, 1), null())
| eval status=case(total_busy > 0, "SERVER_BUSY -- multiplexing failing", isnotnull(mux_ratio) AND mux_ratio < 2, "LOW_MUX -- poor connection reuse", isnotnull(mux_ratio) AND mux_ratio > 50, "HIGH_MUX -- excellent reuse", 1==1, "OK")
| where status != "OK" AND NOT match(status, "HIGH_MUX")
| sort status, -total_busy
```

### Step 3 — - Validate
(a) On ADC CLI: `stat lb vserver <vs>` -- check client connections, server connections, and server busy errors.
(b) Calculate expected ratio: HTTP/1.1 with keep-alive should show 5-20x multiplexing. HTTP/2 even higher.
(c) If server_busy > 0, the backend is rejecting connections.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- Connection Multiplexing"):
* Row 1 -- Single-value: "Avg mux ratio", "Server busy errors", "Client conns", "Server conns".
* Row 2 -- Per-vserver multiplexing analysis.

Alerting:
* Warning (server busy errors > 0): backend connection limit hit.
* Info (mux ratio < 2): connection reuse not effective.

### Step 5 — - Troubleshooting

* **Server busy errors** -- Backend can't accept more connections. Check: (1) backend `max-connections` setting, (2) backend server ulimit / connection limit, (3) TIME_WAIT connections consuming backend ports.

* **Low multiplexing ratio** -- Check: (1) backend HTTP profile allows keep-alive, (2) ADC service has `maxReq` set too low, (3) backend returning `Connection: close` headers.

* **Improving multiplexing** -- Enable HTTP/2 on the ADC frontend profile. Configure backend keep-alive timeout to match expected inter-request intervals.

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

## Known False Positives

Long-lived and multiplexed flows can be healthy for databases and file transfers; check the app, not just the counter.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — Load balancing and connection management](https://docs.citrix.com/en-us/citrix-adc/current-release/load-balancing.html)
