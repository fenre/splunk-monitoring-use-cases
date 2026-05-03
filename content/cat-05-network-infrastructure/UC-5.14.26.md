<!-- AUTO-GENERATED from UC-5.14.26.json — DO NOT EDIT -->

---
id: "5.14.26"
title: "Squid CONNECT Tunnel Duration and Volume"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.26 · Squid CONNECT Tunnel Duration and Volume

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Security, Performance &middot; **Status:** Draft

*We watch squid connect tunnel duration and volume and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

CONNECT dominates bandwidth on many enterprise proxies.

## Value

Operations teams audit Squid CONNECT tunnel duration, volume, and target ports, detecting long-lived tunnels consuming resources and non-HTTPS protocols being tunneled through the proxy.

## Implementation

Ensure log format includes duration; never log decrypted payload. Comply with local interception law.

## Detailed Implementation

### Prerequisites
* Squid access logs with CONNECT method entries. Data in `index=proxy` with `sourcetype=squid:access`. Key fields: `http_method=CONNECT`, `request_url` (host:port), `elapsed` (duration in ms), `bytes` (total bytes transferred).
* CONNECT tunnels: when clients make HTTPS requests through an explicit proxy, they use HTTP CONNECT to establish a tunnel. Squid creates a TCP tunnel between client and origin. The tunnel stays open for the session duration. Long-lived CONNECT tunnels (WebSocket, streaming) consume file descriptors and memory.

### Step 1 — - Configure data collection
Verify CONNECT logging:
```spl
index=proxy sourcetype="squid:access" http_method=CONNECT earliest=-4h
| stats count avg(elapsed) as avg_duration_ms sum(bytes) as total_bytes
```

### Step 2 — - Create the search and alert

**Primary search -- CONNECT tunnel duration and volume analysis:**
```spl
index=proxy sourcetype="squid:access" http_method=CONNECT earliest=-4h
| eval duration_s=tonumber(elapsed)/1000
| eval bytes_mb=tonumber(bytes)/1048576
| rex field=request_url "(?<tunnel_host>[^:]+):(?<tunnel_port>\d+)"
| eval port_service=case(tunnel_port="443", "HTTPS", tunnel_port="8443", "Alt-HTTPS", tunnel_port="993", "IMAPS", tunnel_port="995", "POP3S", tunnel_port="5222", "XMPP", tunnel_port="22", "SSH (suspicious)", 1==1, "Port ".tunnel_port)
| bin _time span=15m
| stats count as tunnels avg(duration_s) as avg_duration_s max(duration_s) as max_duration_s sum(bytes_mb) as total_mb dc(tunnel_host) as unique_hosts by _time, port_service
| eval severity=case(port_service="SSH (suspicious)", "HIGH -- SSH over CONNECT", max_duration_s > 3600, "WARNING -- tunnel >1hr (max ".round(max_duration_s/60, 0)." min)", total_mb > 1000, "WARNING -- >1GB through tunnels", 1==1, "OK")
| where severity != "OK"
| table _time, port_service, tunnels, avg_duration_s, max_duration_s, total_mb, severity
```

### Step 3 — - Validate
(a) Make an HTTPS request through proxy: `curl -x http://<squid>:3128 https://example.com/` -- verify CONNECT log entry.
(b) `squidclient mgr:conn` -- shows active connections including tunnels.
(c) Check for long-lived tunnels: filter `elapsed > 60000` (> 60s).

### Step 4 — - Operationalize
Dashboard ("Squid -- CONNECT Tunnels"):
* Row 1 -- Single-value: "Active tunnels", "Avg duration", "Total bandwidth (MB)", "Non-443 tunnels".
* Row 2 -- Tunnel distribution by port/service.
* Row 3 -- Long-lived tunnel table.

Alerting:
* High (SSH/non-standard port CONNECT): potential policy violation.
* Warning (tunnel duration > 1hr): long-lived tunnel consuming resources.

### Step 5 — - Troubleshooting

* **SSH over CONNECT** -- Users tunneling SSH through the proxy. Block with ACL: `acl SSL_ports port 443 8443` and `http_access deny CONNECT !SSL_ports`.

* **Long-lived CONNECT tunnels** -- WebSocket or streaming connections. Set `read_timeout` and `connect_timeout` in squid.conf to limit tunnel duration if policy allows.

* **High CONNECT bandwidth** -- Large file downloads over HTTPS. Consider: (1) SSL bump peek-and-splice for visibility (UC-5.14.33), (2) bandwidth limits per tunnel.

## SPL

```spl
index=proxy sourcetype="squid:access"
| where request_method=="CONNECT"
| eval dur_ms=tonumber(time_taken_ms)
| eval bytes=tonumber(bytes_sent)+tonumber(bytes_received)
| timechart span=5m perc95(dur_ms) as p95_tunnel_ms sum(bytes) as tunnel_bytes
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid CONNECT Tunnel Duration and Volume» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/access_log/)
