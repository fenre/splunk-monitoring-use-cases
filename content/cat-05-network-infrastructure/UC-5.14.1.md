<!-- AUTO-GENERATED from UC-5.14.1.json — DO NOT EDIT -->

---
id: "5.14.1"
title: "HAProxy Backend Server Health Check Failures"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.1 · HAProxy Backend Server Health Check Failures

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Status:** Draft

*We watch haproxy backend server health check failures and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Backend health checks prevent traffic to failed nodes; log evidence shows which farm member and protocol failed first.

## Value

Operations teams detect HAProxy backend server health check failures and DOWN transitions, distinguishing L4 connection failures from L7 response errors and identifying backends with no available servers.

## Implementation

Forward HAProxy logs via syslog or UF file tail. Map `backend`/`server` fields per HAProxy 2.8 `log-format`. Correlate with `haproxy:stats` CSV from `show stat`.

## Detailed Implementation

### Prerequisites
* HAProxy 2.x+ configured with detailed log format forwarding to Splunk via syslog or UF file tail. Data in `index=proxy` with `sourcetype=haproxy:http`. Key log fields (from HAProxy default HTTP log format): `backend`, `server`, `status_code`, `Tw` (queue wait time), `Tc` (connect time), `Tr` (server response time), `termination_state` (session termination cause, e.g., "sD" = server down during data), `retries`.
* HAProxy health checks: TCP (connect), HTTP (GET /health expecting 200), agent-check (external health script). When a server fails the health check, HAProxy marks it DOWN and stops sending traffic. Key syslog messages: "Health check for server ... failed" and "Server ... is DOWN".
* Create `haproxy_backends.csv` lookup: `backend`, `server`, `application`, `owner`, `tier`.

### Step 1 — - Configure data collection
HAProxy syslog:
```
# haproxy.cfg
global
    log /dev/log local0 info
    log <splunk_syslog_ip>:514 local0 info

defaults
    log global
    option httplog
    option log-health-checks
```
The `option log-health-checks` directive is critical -- without it, health check transitions are not logged.

Verify:
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| where match(_raw, "(?i)(health check|DOWN|UP|NOLB|no server)")
| stats count by backend, server
```

### Step 2 — - Create the search and alert

**Primary search -- Backend health check failure analysis:**
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| where status >= 500 OR match(_raw, "(?i)NOLB|no server|DOWN|layer7 invalid|health check.*failed")
| eval failure_type=case(match(_raw, "(?i)health check.*failed"), "HEALTH_CHECK_FAIL", match(_raw, "(?i)NOLB|no server"), "NO_SERVER_AVAILABLE", match(_raw, "(?i)layer7 invalid"), "L7_INVALID_RESPONSE", match(_raw, "(?i)layer4.*connection"), "L4_CONNECTION_FAIL", status >= 502 AND status <= 504, "BACKEND_ERROR_".status, 1==1, "OTHER")
| lookup haproxy_backends.csv backend, server OUTPUT application, owner, tier
| stats count as failures dc(server) as affected_servers latest(_time) as last_failure by backend, failure_type, application, tier
| eval severity=case(failure_type="NO_SERVER_AVAILABLE", "CRITICAL -- all servers DOWN in backend", failure_type="HEALTH_CHECK_FAIL" AND affected_servers > 1, "HIGH -- multiple servers failing", failure_type="L7_INVALID_RESPONSE", "HIGH -- backend returning invalid responses", 1==1, "WARNING")
| sort severity, -failures
```

**Server state transition tracking:**
```spl
index=proxy sourcetype="haproxy:http" earliest=-24h
| where match(_raw, "(?i)(Server .* is (DOWN|UP)|going (down|up))")
| rex "Server (?<backend>\S+)/(?<server>\S+) is (?<new_state>\w+)"
| table _time, backend, server, new_state
| sort -_time
```

### Step 3 — - Validate
(a) Stop a backend service and verify the DOWN transition appears in Splunk.
(b) HAProxy stats page: `http://<haproxy>:9000/stats` -- compare server states.
(c) HAProxy runtime API: `echo "show stat" | socat stdio /var/run/haproxy/admin.sock` -- check `status` column.

### Step 4 — - Operationalize
Dashboard ("HAProxy -- Backend Health"):
* Row 1 -- Single-value: "Backends with DOWN servers", "Total DOWN servers", "NOLB events", "Health check failures (4h)".
* Row 2 -- Failure type analysis table.
* Row 3 -- Server state transition timeline (24h).

Alerting:
* Critical (NOLB/no server available on any backend): complete backend failure -- all traffic failing.
* High (> 2 servers DOWN in same backend): capacity severely degraded.
* Warning (health check failure on single server): investigate server health.

### Step 5 — - Troubleshooting

* **Health check failing but curl to backend works** -- HAProxy health check may use different URL, port, or HTTP method than your test. Check: `show backend <backend>` for `check`, `check-uri`, `check-port` settings.

* **"layer7 invalid response"** -- Backend is returning a response that doesn't match the expected health check criteria. Check: `option httpchk GET /health` and verify the backend returns 2xx status.

* **All servers DOWN (NOLB)** -- If all servers in a backend fail health checks simultaneously, it's likely a shared dependency (database, DNS, network). Check common infrastructure.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| where status >= 500 OR match(_raw, "(?i)NOLB|no server") OR match(_raw, "(?i)layer7 invalid")
| stats count by backend, server
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy Backend Server Health Check Failures» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#8.2.1)
