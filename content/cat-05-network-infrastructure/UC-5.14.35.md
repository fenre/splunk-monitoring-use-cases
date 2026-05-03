<!-- AUTO-GENERATED from UC-5.14.35.json — DO NOT EDIT -->

---
id: "5.14.35"
title: "Squid Client Connection Load from cachemgr"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.35 · Squid Client Connection Load from cachemgr

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Security &middot; **Status:** Draft

*We watch squid client connection load from cachemgr and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Proxies fail open or drop sessions when fds exhaust.

## Value

Operations teams monitor Squid client connection counts and per-client request rates, detecting file descriptor exhaustion and misbehaving clients consuming excessive proxy capacity.

## Implementation

Poll during incidents; baseline diurnal curves. Correlate with SYN flood mitigations.

## Detailed Implementation

### Prerequisites
* Squid cache manager output for client connections. Data from `squidclient mgr:client_list` or `squidclient mgr:conn` forwarded to Splunk. `sourcetype=squid:stats` in `index=proxy`. Key metrics: active client connections, connections per client IP, file descriptor usage.
* Connection load: Squid has a maximum file descriptor limit (`max_filedescriptors`). Each client connection consumes a file descriptor. When the limit is reached, new connections are refused. High connection counts from single IPs may indicate: (1) misbehaving applications, (2) bots, (3) misconfigured clients.

### Step 1 — - Configure data collection
Scripted input:
```bash
#!/bin/bash
squidclient mgr:client_list 2>/dev/null
```
```
# inputs.conf
[script:///opt/splunk/etc/apps/TA-squid/bin/squid_client_list.sh]
interval = 300
sourcetype = squid:clients
index = proxy
```
Or parse from access log:
```spl
index=proxy sourcetype="squid:access" earliest=-4h
| stats dc(src_ip) as unique_clients count as total_requests by host
```

### Step 2 — - Create the search and alert

**Primary search -- Client connection load analysis:**
```spl
index=proxy sourcetype="squid:access" earliest=-1h
| bin _time span=5m
| stats dc(src_ip) as unique_clients count as requests by _time, host
| eval requests_per_client=round(requests/unique_clients, 0)
| eval severity=case(unique_clients > 5000, "WARNING -- >5000 concurrent clients", requests_per_client > 500, "WARNING -- high per-client request rate", 1==1, "OK")
| where severity != "OK"
| table _time, host, unique_clients, requests, requests_per_client, severity
```

**Top connection consumers:**
```spl
index=proxy sourcetype="squid:access" earliest=-1h
| stats count as requests dc(request_url) as unique_urls by src_ip
| sort -requests | head 20
| eval concern=if(requests > 10000, "Investigate -- very high request rate", "Normal")
```

### Step 3 — - Validate
(a) `squidclient mgr:info | grep -i "file desc"` -- shows FD usage.
(b) `squidclient mgr:client_list` -- shows per-client connection counts.
(c) Check system limits: `ulimit -n` and `cat /proc/$(pidof squid)/limits | grep "open files"`.

### Step 4 — - Operationalize
Dashboard ("Squid -- Client Load"):
* Row 1 -- Single-value: "Active clients", "Total connections", "FD utilization %".
* Row 2 -- Client count timechart.
* Row 3 -- Top connection consumers.

Alerting:
* Warning (unique clients > 5000 or FD > 80%): capacity pressure.
* High (single client > 10000 requests/hr): investigate client behavior.

### Step 5 — - Troubleshooting

* **File descriptor exhaustion** -- Increase: (1) `max_filedescriptors` in squid.conf, (2) system `ulimit -n`, (3) `/proc/sys/fs/file-max`. Restart Squid after changes.

* **Single client consuming excessive connections** -- Identify the client application. Common causes: (1) browser with many tabs, (2) automated crawler, (3) update agent downloading many packages. Consider `max_conn_per_client` ACL.

* **Connection count growing but requests flat** -- Clients opening connections but not sending requests (idle keepalive). Tune `client_idle_pconn_timeout` (default 2 min) and `client_lifetime` (default 1 day).

## SPL

```spl
index=proxy sourcetype="squid:info"
| regex _raw="(?i)Current active connections|client_http\.conns"
| rex field=_raw "(?<conns>\d{3,})"
| eval conns=tonumber(conns)
| where conns > 20000
| table _time, host, conns
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid Client Connection Load from cachemgr» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/max_filedescriptors/)
