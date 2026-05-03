<!-- AUTO-GENERATED from UC-5.14.6.json — DO NOT EDIT -->

---
id: "5.14.6"
title: "HAProxy HTTP Compression Ratio Effectiveness"
status: "draft"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.14.6 · HAProxy HTTP Compression Ratio Effectiveness

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Cost &middot; **Status:** Draft

*We watch haproxy http compression ratio effectiveness and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Compression reduces egress cost until misconfiguration disables it for large JSON.

## Value

Operations teams detect HAProxy connection pool exhaustion and server queue buildup, identifying backends where maxconn limits are reached and requests are queuing.

## Implementation

Add compression byte fields per HAProxy docs; document field order for parsers.

## Detailed Implementation

### Prerequisites
* HAProxy HTTP logs with connection counts and queue depth. Key fields: `actconn` (active connections), `feconn` (frontend connections), `beconn` (backend connections), `srv_conn` (server connections), `srv_queue` (server queue depth), `backend_queue` (backend queue depth).
* HAProxy connection limits: `maxconn` (global and per-server). When connections exceed maxconn, new requests are queued. Queue depth > 0 indicates saturation. If the queue fills, HAProxy returns 503.

### Step 1 — - Configure data collection
Log format with connection counters:
```
# haproxy.cfg
defaults
    log-format "%ci:%cp [%t] %ft %b/%s %Tq/%Tw/%Tc/%Tr/%Tt %ST %B %CC %CS %tsc %ac/%fc/%bc/%sc/%rc %sq/%bq"
```
The `%ac/%fc/%bc/%sc/%rc` block = active/frontend/backend/server/retries connections. `%sq/%bq` = server queue/backend queue depth.

Verify:
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| stats avg(actconn) as avg_active avg(srv_queue) as avg_queue by backend
| sort -avg_active
```

### Step 2 — - Create the search and alert

**Primary search -- Connection saturation and queue buildup:**
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| eval active=tonumber(actconn)
| eval be_conn=tonumber(beconn)
| eval s_queue=tonumber(srv_queue)
| eval b_queue=tonumber(backend_queue)
| bin _time span=5m
| stats avg(active) as avg_active max(active) as max_active avg(be_conn) as avg_backend_conn avg(s_queue) as avg_srv_queue max(s_queue) as max_srv_queue avg(b_queue) as avg_be_queue count as requests by _time, backend
| eval queue_pct=round(100*avg_srv_queue/requests, 2)
| eval saturation=case(max_srv_queue > 100, "CRITICAL -- deep queue (max=".max_srv_queue.")", avg_srv_queue > 10, "HIGH -- sustained queuing", avg_be_queue > 5, "WARNING -- backend queue building", 1==1, "OK")
| where saturation != "OK"
| table _time, backend, avg_active, avg_backend_conn, avg_srv_queue, max_srv_queue, saturation
```

### Step 3 — - Validate
(a) Check HAProxy stats page: `qcur` (current queued), `qlimit`, `scur` (current sessions).
(b) HAProxy runtime API: `echo "show stat" | socat stdio /var/run/haproxy/admin.sock | cut -d, -f1,2,5,18,30,31` -- shows queue and session counters.
(c) Load test with more connections than `maxconn` and verify queue growth.

### Step 4 — - Operationalize
Dashboard ("HAProxy -- Connection Saturation"):
* Row 1 -- Single-value: "Active connections", "Max queue depth", "Backends queuing".
* Row 2 -- Connection vs queue depth timechart.
* Row 3 -- Per-backend saturation table.

Alerting:
* Critical (queue depth > 100 sustained): immediate capacity issue.
* Warning (queue depth > 10 sustained): approaching capacity.

### Step 5 — - Troubleshooting

* **Queue building on specific servers** -- Server's `maxconn` is too low or server is slow. Check: `maxconn` per server in haproxy.cfg. Also check if server's keepalive connections are exhausted.

* **Queue on entire backend** -- All servers are saturated. Add more backend servers or increase capacity. Check if a single slow endpoint is causing all connections to pile up.

* **High active connections but no queue** -- System is handling load but approaching limits. Monitor trend and plan capacity.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| eval cin=tonumber(comp_in), cout=tonumber(comp_out)
| eval ratio=if(cin>0, round(100*cout/cin,1), null())
| timechart span=1h avg(ratio) by frontend
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy HTTP Compression Ratio Effectiveness» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#compression)
