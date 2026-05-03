<!-- AUTO-GENERATED from UC-5.14.31.json — DO NOT EDIT -->

---
id: "5.14.31"
title: "Squid HTTP Status Code Distribution"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.31 · Squid HTTP Status Code Distribution

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Security &middot; **Status:** Draft

*We watch squid http status code distribution and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Spikes in 5xx often precede origin incidents visible here first.

## Value

Operations teams track Squid HTTP status code distributions, detecting shifts toward error codes (502/503/407) that indicate backend reachability or authentication failures.

## Implementation

Separate `ERR_*` Squid codes from upstream HTTP for triage.

## Detailed Implementation

### Prerequisites
* Squid access logs with HTTP status codes. Data in `index=proxy` with `sourcetype=squid:access`. Key fields: `http_status_code`, `squid_request_status`, `request_url`, `http_method`, `src_ip`.
* Status code distribution: 2xx (success), 3xx (redirect), 4xx (client error -- bad request, unauthorized, not found), 5xx (server error). Sudden shifts in distribution (e.g., spike in 407 Proxy Authentication Required or 502 Bad Gateway) indicate issues. Squid-generated codes: 407 (proxy auth required), 502 (bad gateway -- backend unreachable), 503 (service unavailable -- overloaded).

### Step 1 — - Configure data collection
Default access log includes status codes. Verify:
```spl
index=proxy sourcetype="squid:access" earliest=-4h
| eval status_class=substr(http_status_code, 1, 1)."xx"
| stats count by status_class
| sort status_class
```

### Step 2 — - Create the search and alert

**Primary search -- Status code distribution with anomaly detection:**
```spl
index=proxy sourcetype="squid:access" earliest=-4h
| eval status_class=substr(http_status_code, 1, 1)."xx"
| bin _time span=15m
| stats count as total count(eval(status_class="2xx")) as ok count(eval(status_class="3xx")) as redirect count(eval(status_class="4xx")) as client_err count(eval(status_class="5xx")) as server_err count(eval(http_status_code=407)) as proxy_auth count(eval(http_status_code=502)) as bad_gw count(eval(http_status_code=503)) as svc_unavail by _time
| eval error_pct=round(100*(client_err+server_err)/total, 2)
| eval severity=case(server_err > 100 AND error_pct > 5, "HIGH -- >5% server errors", bad_gw > 50, "HIGH -- many 502s (backend issues)", proxy_auth > 200, "WARNING -- high 407s (auth problems)", svc_unavail > 50, "WARNING -- Squid returning 503 (overloaded?)", 1==1, "OK")
| where severity != "OK"
| table _time, total, ok, client_err, server_err, error_pct, bad_gw, svc_unavail, proxy_auth, severity
```

### Step 3 — - Validate
(a) Compare with `squidclient mgr:counters | grep http` -- shows per-code counters.
(b) Intentionally trigger 502 by requesting a URL with an unreachable origin.
(c) Verify 407 requires proxy authentication when `proxy_auth` ACL is configured.

### Step 4 — - Operationalize
Dashboard ("Squid -- HTTP Status Distribution"):
* Row 1 -- Single-value: "Error rate (%)", "502 count", "503 count", "407 count".
* Row 2 -- Status class distribution timechart.
* Row 3 -- Top error URLs.

Alerting:
* High (5xx > 5%): widespread server/proxy errors.
* Warning (407 spike): authentication infrastructure issue.

### Step 5 — - Troubleshooting

* **502 Bad Gateway** -- Squid can't connect to the origin. Check: (1) DNS resolution works, (2) origin server is reachable from Squid host, (3) firewall allows outbound connections from Squid, (4) `tcp_outgoing_address` is correct.

* **503 Service Unavailable** -- Squid is overloaded. Check: (1) `max_filedescriptors` limit, (2) memory usage, (3) connection count vs `max_open_disk_fds`.

* **407 spike** -- Proxy authentication backend (LDAP, Kerberos, NTLM) may be down. Check auth helper process: `squidclient mgr:auth_helper` and verify authentication infrastructure.

## SPL

```spl
index=proxy sourcetype="squid:access"
| eval sc=tonumber(status_code)
| where isnotnull(sc)
| bin sc span=100
| timechart span=1h count by sc
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid HTTP Status Code Distribution» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/http_status_codes/)
