<!-- AUTO-GENERATED from UC-5.14.24.json — DO NOT EDIT -->

---
id: "5.14.24"
title: "Squid Internal DNS Resolver Errors and Latency"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.24 · Squid Internal DNS Resolver Errors and Latency

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Status:** Draft

*We watch squid internal dns resolver errors and latency and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Resolver health is easy to overlook until all MISS latency spikes.

## Value

Operations teams monitor Squid internal DNS resolver errors and timeout rates, detecting upstream DNS server failures that cascade into proxy request failures.

## Implementation

Point `dns_nameservers` at resilient anycast resolvers; alert on repeated failures.

## Detailed Implementation

### Prerequisites
* Squid cache logs or syslog messages including DNS events. Data in `index=proxy` with `sourcetype=squid:cache` or `sourcetype=squid:access`. Key events: DNS timeout, NXDOMAIN, DNS lookup latency.
* Squid's internal DNS resolver: Squid has its own async DNS resolver (not using system resolver by default). DNS failures cause request failures since Squid can't resolve the origin server. `dns_nameservers` in squid.conf configures upstream DNS. `dns_timeout` (default 30s) controls how long to wait.

### Step 1 — - Configure data collection
Enable DNS-related logging:
```
# squid.conf
debug_options ALL,1 78,3
```
Section 78 covers DNS. Level 3 gives detailed lookup info. Verify:
```spl
index=proxy (sourcetype="squid:cache" OR sourcetype="squid:access") earliest=-4h
| where match(_raw, "(?i)dns|NXDOMAIN|timeout.*lookup|name.*resolution|ipcache_nbgethostbyname")
| stats count by _raw | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- DNS error analysis:**
```spl
index=proxy (sourcetype="squid:cache" OR sourcetype="squid:access") earliest=-4h
| where match(_raw, "(?i)dns|NXDOMAIN|timeout.*look|name.*resolution.*fail|ipcache.*fail|ERR_DNS")
| eval dns_event=case(match(_raw, "(?i)NXDOMAIN|no such domain"), "NXDOMAIN", match(_raw, "(?i)timeout"), "DNS_TIMEOUT", match(_raw, "(?i)ERR_DNS|dns.*fail|resolution.*fail"), "DNS_FAILURE", match(_raw, "(?i)ipcache.*negative"), "NEGATIVE_CACHE", 1==1, "OTHER")
| rex "(?:for|host|domain)\s+(?<query_domain>[a-zA-Z0-9.-]+)"
| stats count as events dc(query_domain) as unique_domains values(query_domain) as sample_domains by dns_event
| eval severity=case(dns_event="DNS_TIMEOUT" AND events > 50, "CRITICAL -- DNS resolver timing out", dns_event="DNS_FAILURE" AND events > 100, "HIGH -- widespread DNS failures", dns_event="NXDOMAIN" AND unique_domains > 20, "WARNING -- many nonexistent domains", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

**DNS latency (from access log timing):**
```spl
index=proxy sourcetype="squid:access" earliest=-4h
| where match(squid_request_status, "TCP_MISS")
| eval total_ms=tonumber(elapsed)
| bin _time span=5m
| stats avg(total_ms) as avg_response_ms p95(total_ms) as p95_ms count as requests by _time
| where p95_ms > 5000
```

### Step 3 — - Validate
(a) Lookup a known-bad domain through the proxy: `curl -x http://<squid>:3128 http://nonexistent.example.test/` -- should produce ERR_DNS_FAIL.
(b) `squidclient mgr:ipcache` -- shows DNS cache contents and hits/misses.
(c) Check DNS server availability: `dig @<dns_server> example.com` from the Squid host.

### Step 4 — - Operationalize
Dashboard ("Squid -- DNS Health"):
* Row 1 -- Single-value: "DNS errors (4h)", "NXDOMAIN count", "DNS timeouts", "Unique failed domains".
* Row 2 -- DNS error breakdown by type.
* Row 3 -- Top failing domains.

Alerting:
* Critical (DNS timeouts > 50/hr): DNS server likely unreachable.
* Warning (NXDOMAIN > 20 unique domains): possible malware or misconfigured clients.

### Step 5 — - Troubleshooting

* **DNS timeouts** -- Squid's DNS server may be overloaded or unreachable. Check: (1) `dns_nameservers` in squid.conf, (2) network connectivity to DNS server from Squid host, (3) DNS server response time: `dig @<server> example.com +time=2`.

* **High NXDOMAIN rate** -- Clients are requesting nonexistent domains. Investigate: (1) malware on client machines, (2) misconfigured DNS suffixes, (3) typo domains.

* **Negative DNS cache causing stale failures** -- Squid caches negative DNS results. If a DNS issue was temporary, stale negative cache entries block resolution. `ipcache_size` and `ipcache_low`/`ipcache_high` control this. Force flush: `squidclient mgr:ipcache_flush`.

## SPL

```spl
index=proxy sourcetype="squid:cache"
| regex _raw="(?i)(DNS|ipcache|fqdn).*(?:FAIL|timeout|missing)"
| stats count by host
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid Internal DNS Resolver Errors and Latency» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/dns_nameservers/)
