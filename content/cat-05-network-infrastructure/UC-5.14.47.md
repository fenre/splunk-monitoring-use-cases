<!-- AUTO-GENERATED from UC-5.14.47.json — DO NOT EDIT -->

---
id: "5.14.47"
title: "Traefik Default Router / Catch-All Traffic Spike"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.47 · Traefik Default Router / Catch-All Traffic Spike

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Performance &middot; **Status:** Draft

*We watch traefik default router / catch-all traffic spike and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Unexpected default-router hits expose config gaps.

## Value

Operations teams detect traffic spikes to Traefik default/catch-all routers, identifying misconfigured services, unregistered domains, and vulnerability scanners.

## Implementation

High catch-all volume may be scanners; pair with WAF and geo blocking.

## Detailed Implementation

### Prerequisites
* Traefik access logs with router information. Key access log fields: `RouterName`, `ServiceName`, `DownstreamStatus`, `RequestPath`. Data in `index=proxy` with `sourcetype=traefik:access`.
* Default router / catch-all: Traefik uses a priority-based routing system. When no specific rule matches, traffic goes to the default router (if configured) or returns 404. A catch-all router (e.g., `rule: PathPrefix(/)`) receives all unmatched traffic. Traffic spikes to the default router indicate: (1) misconfigured services, (2) new domains pointing to Traefik without routes, (3) scanners probing for vulnerabilities.

### Step 1 — - Configure data collection
```yaml
# Dynamic config -- catch-all router
http:
  routers:
    catch-all:
      rule: "PathPrefix(`/`)"
      priority: 1
      service: default-service
      entryPoints:
      - web
      - websecure
```
Verify:
```spl
index=proxy sourcetype="traefik:access" earliest=-4h
| stats count by RouterName
| sort -count
```

### Step 2 — - Create the search and alert

**Primary search -- Default/catch-all router traffic spike:**
```spl
index=proxy sourcetype="traefik:access" earliest=-4h
| eval is_default=if(match(RouterName, "(?i)catch.all|default|fallback") OR isnull(RouterName) OR RouterName="-", 1, 0)
| bin _time span=15m
| stats sum(is_default) as default_traffic count as total_traffic by _time
| eval default_pct=round(100*default_traffic/total_traffic, 2)
| eval severity=case(default_traffic > 1000 AND default_pct > 20, "HIGH -- >20% traffic to default router", default_traffic > 500, "WARNING -- significant unmatched traffic", 1==1, "OK")
| where severity != "OK"
| table _time, total_traffic, default_traffic, default_pct, severity
```

**Unmatched traffic analysis:**
```spl
index=proxy sourcetype="traefik:access" earliest=-4h
| where match(RouterName, "(?i)catch.all|default|fallback") OR isnull(RouterName) OR RouterName="-"
| rex field=RequestHost "(?<request_host>[^:]+)"
| stats count as requests dc(ClientAddr) as unique_clients by request_host, RequestPath
| sort -requests | head 20
```

### Step 3 — - Validate
(a) Request a URL with no matching route: `curl -H "Host: unknown.example.com" http://<traefik>/` -- should hit catch-all.
(b) Traefik API: `curl http://localhost:8080/api/http/routers` -- shows all configured routers and their priorities.
(c) Verify the catch-all has lowest priority (priority: 1).

### Step 4 — - Operationalize
Dashboard ("Traefik -- Unmatched Traffic"):
* Row 1 -- Single-value: "Default router requests", "% of total", "Unique hosts hitting default".
* Row 2 -- Unmatched traffic timechart.
* Row 3 -- Top unmatched hosts and paths.

Alerting:
* High (default traffic > 20% of total): many requests not matching routes.
* Warning (default traffic > 500/15m): investigate unmatched hosts.

### Step 5 — - Troubleshooting

* **New domain hitting catch-all** -- A DNS record points to Traefik but no router is configured for it. Add a router with the appropriate `Host` rule.

* **Scanners hitting catch-all** -- Automated scanners probing common paths. Consider: (1) blocking known scanner User-Agents with middleware, (2) returning 444 (connection close) for catch-all, (3) rate limiting the catch-all router.

* **Legitimate service hitting catch-all** -- Route rule may be wrong. Check: `Host` header matches the configured rule, `PathPrefix` is correct, TLS SNI matches for HTTPS routes.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| where RouterName=="default@internal" OR match(RouterName, "(?i)dashboard@internal")
| bin _time span=5m
| stats count by ClientAddr, entryPointName, _time
| where count > 200
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Traefik Default Router / Catch-All Traffic Spike» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/routing/routers/)
