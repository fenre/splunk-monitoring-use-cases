<!-- AUTO-GENERATED from UC-5.14.3.json — DO NOT EDIT -->

---
id: "5.14.3"
title: "HAProxy Queue Time vs Response Time Saturation Ratio"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.3 · HAProxy Queue Time vs Response Time Saturation Ratio

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Status:** Draft

*We watch haproxy queue time vs response time saturation ratio and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Queue-heavy latency means the proxy or servers cannot dequeue fast enough even if app CPU is fine.

## Value

Operations teams decompose HAProxy request latency into queue time vs server response time, detecting backend saturation where requests spend excessive time in queue.

## Implementation

Confirm millisecond units in `props.conf`. Tune ratio threshold per API; pair with server `cur_sess`.

## Detailed Implementation

### Prerequisites
* HAProxy HTTP logs with timing fields. Key fields: `Tq` (request queue time), `Tw` (waiting in queue), `Tc` (connect time), `Tr` (server response time), `Tt` (total time), `backend`, `server`.
* HAProxy timing breakdown: Tt (total) = Tq + Tw + Tc + Tr + Td. When Tw (queue time) is a significant portion of Tt, the backend is saturated -- requests are queuing because all server connections are busy.

### Step 1 — - Configure data collection
Verify timing fields:
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| where isnotnull(Tw) AND isnotnull(Tr)
| stats avg(Tw) as avg_queue avg(Tr) as avg_response by backend
| sort -avg_queue
```

### Step 2 — - Create the search and alert

**Primary search -- Queue vs response time saturation:**
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| eval queue_ms=tonumber(Tw)
| eval response_ms=tonumber(Tr)
| eval total_ms=tonumber(Tt)
| eval connect_ms=tonumber(Tc)
| where isnotnull(queue_ms) AND isnotnull(response_ms) AND total_ms > 0
| eval queue_pct=round(100*queue_ms/total_ms, 1)
| eval server_pct=round(100*response_ms/total_ms, 1)
| bin _time span=5m
| stats avg(queue_ms) as avg_queue avg(response_ms) as avg_response avg(queue_pct) as avg_queue_pct avg(connect_ms) as avg_connect p95(total_ms) as p95_total count as requests by _time, backend
| eval bottleneck=case(avg_queue_pct > 30, "QUEUING -- backend saturated (".round(avg_queue_pct, 0)."% time in queue)", avg_connect > 100, "CONNECT -- slow TCP connect (".round(avg_connect, 0)."ms)", avg_response > 2000, "BACKEND -- slow responses (".round(avg_response, 0)."ms)", 1==1, "OK")
| where bottleneck != "OK"
| sort bottleneck, -avg_queue_pct
```

### Step 3 — - Validate
(a) Compare timing with HAProxy stats page: check `qtime`, `rtime` columns.
(b) Overload a test backend and verify queue time increases.
(c) Verify Tt = Tq + Tw + Tc + Tr approximately for a sample of requests.

### Step 4 — - Operationalize
Dashboard ("HAProxy -- Request Timing"):
* Row 1 -- Single-value: "Avg queue time", "Avg response time", "P95 total", "Backends queuing".
* Row 2 -- Bottleneck analysis per backend.
* Row 3 -- Timing breakdown trending timechart.

Alerting:
* Warning (queue time > 30% of total for > 5 min): backend capacity issue.
* Warning (P95 total > 5s): severe latency.

### Step 5 — - Troubleshooting

* **High queue time** -- All server connections are busy. Options: (1) add more backend servers, (2) increase `maxconn` per server, (3) optimize backend response time.

* **High connect time** -- TCP connection to backend is slow. Check: network latency, server TCP backlog (`net.core.somaxconn`), firewall connection tracking table.

* **High response time, no queue** -- Backend application is slow. This is not an HAProxy issue -- investigate the application.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| eval Tw=tonumber(Wait), Tr=tonumber(Response)
| eval q_ratio=if(Tr>0, round(Tw/Tr,3), null())
| where Tw > 50 AND q_ratio > 0.5
| timechart span=5m perc95(q_ratio) by backend
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy Queue Time vs Response Time Saturation Ratio» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.haproxy.com/blog/)
