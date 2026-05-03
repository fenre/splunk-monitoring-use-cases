<!-- AUTO-GENERATED from UC-5.14.8.json — DO NOT EDIT -->

---
id: "5.14.8"
title: "HAProxy Frontend Connection Limiting and Denials"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.8 · HAProxy Frontend Connection Limiting and Denials

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Security, Availability &middot; **Status:** Draft

*We watch haproxy frontend connection limiting and denials and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Protective limits look like outages if unexplained; logging proves intent.

## Value

Operations teams detect HAProxy session persistence (sticky session) violations where clients lose their server affinity, causing session state disruption.

## Implementation

Set intentional `maxconn`; baseline deny velocity to catch DDoS or misconfigured clients.

## Detailed Implementation

### Prerequisites
* HAProxy HTTP logs with session persistence (stickiness) fields. Key fields: `cookie` (persistence cookie value), `termination_state`, `backend`, `server`, `client_ip`.
* HAProxy persistence: `cookie` insert (HAProxy sets cookie) or `cookie` prefix (appends to app cookie). When sticky sessions break, users lose session state (shopping carts, login state). Causes: (1) cookie not set, (2) target server DOWN (redirect to new server), (3) cookie expired.

### Step 1 — - Configure data collection
```
# haproxy.cfg
backend app_servers
    cookie SERVERID insert indirect nocache httponly secure
    server web1 10.0.0.1:80 cookie web1 check
    server web2 10.0.0.2:80 cookie web2 check
```
Verify:
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| where isnotnull(cookie) OR match(_raw, "SERVERID")
| stats count by backend, server, cookie
```

### Step 2 — - Create the search and alert

**Primary search -- Session persistence violations:**
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| eval has_cookie=if(isnotnull(cookie) AND cookie!="" AND cookie!="-", 1, 0)
| bin _time span=5m
| stats count as total count(eval(has_cookie=0)) as no_cookie dc(server) as servers_used by _time, backend, client_ip
| where no_cookie > 0 OR servers_used > 1
| eval violation=case(no_cookie > 0, "NO_COOKIE -- client not receiving persistence cookie", servers_used > 1, "MULTI_SERVER -- client distributed across ".servers_used." servers", 1==1, "OK")
| stats count as violations sum(total) as requests dc(client_ip) as affected_clients by backend, violation
| where violations > 0
| sort -violations
```

### Step 3 — - Validate
(a) Verify cookie is set: `curl -c - https://<haproxy>/` -- look for SERVERID cookie.
(b) Make multiple requests with cookie and verify same server: check `server` field is consistent.
(c) Take down the sticky server and verify redispatch occurs (session moves to new server).

### Step 4 — - Operationalize
Dashboard ("HAProxy -- Session Persistence"):
* Row 1 -- Single-value: "Persistence violations", "Clients without cookie", "Multi-server clients".
* Row 2 -- Violation analysis per backend.

Alerting:
* Warning (persistence violations > 5% of requests): clients losing session state.

### Step 5 — - Troubleshooting

* **Cookie not being set** -- Check: (1) `cookie` directive present in backend, (2) response passes through HAProxy (not cached upstream), (3) `httponly` and `secure` flags match client's connection (secure requires HTTPS).

* **Client hitting multiple servers** -- Check: (1) cookie name matches between config and client, (2) no intermediate proxy stripping cookies, (3) server that client was stuck to may have gone DOWN.

* **Session persistence after server scale-down** -- Clients with cookies for removed servers get 503. Use `option redispatch` to redirect these clients to available servers.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| regex _raw="(?i)(denied by tcp-request connection|too many connections)"
| bin _time span=1m
| stats count by frontend, _time
| where count > 50
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy Frontend Connection Limiting and Denials» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#maxconn)
