<!-- AUTO-GENERATED from UC-5.14.17.json — DO NOT EDIT -->

---
id: "5.14.17"
title: "Varnish Object TTL Distribution Sampling"
status: "draft"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.14.17 · Varnish Object TTL Distribution Sampling

> **Criticality:** Low &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Analytics, Capacity &middot; **Status:** Draft

*We watch varnish object ttl distribution sampling and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

TTL spread explains hit ratio and origin offload variance.

## Value

Operations teams sample Varnish object TTL distributions to identify caching strategy gaps such as excessively short TTLs driving backend load or overly long TTLs serving stale content.

## Implementation

Sample high-volume VSL 1:N to control license cost.

## Detailed Implementation

### Prerequisites
* Varnish logs with TTL information. Key log tags: `TTL` (shows ttl, grace, keep values for objects), `ExpKill` (object expired and removed). Data in `index=proxy` with `sourcetype=varnish:log`.
* Object TTL distribution reveals caching strategy effectiveness. Very short TTLs (< 10s) create high backend load. Very long TTLs (> 24h) risk serving stale content. Understanding the distribution helps tune `beresp.ttl` in VCL.

### Step 1 — - Configure data collection
Log TTL decisions:
```
varnishlog -g session -i TTL > /var/log/varnish/ttl.log
```
Or collect via varnishstat for aggregate counters. Verify:
```spl
index=proxy sourcetype="varnish:log" earliest=-4h
| where match(_raw, "(?i)^-\s+TTL|beresp\.ttl|object\.ttl")
| head 20
```

### Step 2 — - Create the search and alert

**Primary search -- TTL distribution by backend:**
```spl
index=proxy sourcetype="varnish:log" earliest=-4h
| where match(_raw, "(?i)TTL")
| rex "TTL\s+\S+\s+(?<ttl_seconds>\d+)\s"
| rex "VCL_call\s+(?<vcl_call>\w+)"
| eval ttl=tonumber(ttl_seconds)
| where isnotnull(ttl)
| eval ttl_bucket=case(ttl < 10, "< 10s (very short)", ttl < 60, "10s-60s (short)", ttl < 300, "1-5 min", ttl < 3600, "5-60 min", ttl < 86400, "1-24 hours", 1==1, "> 24 hours")
| stats count as objects avg(ttl) as avg_ttl min(ttl) as min_ttl max(ttl) as max_ttl by ttl_bucket
| sort min_ttl
```

**Short-TTL objects causing high backend load:**
```spl
index=proxy sourcetype="varnish:access" earliest=-4h
| where lower(hitmiss)="miss"
| rex field=request "\S+ (?<uri>\S+)"
| stats count as misses by uri
| sort -misses | head 20
| eval recommendation=if(misses > 100, "Consider increasing TTL for this URI", "OK")
```

### Step 3 — - Validate
(a) `varnishlog -q "TTL" -i TTL` -- live TTL assignments.
(b) For a specific object: `varnishlog -q "ReqURL eq '/api/data'" -i TTL -i BerespHeader`.
(c) Verify backend `Cache-Control` headers match expected TTLs.

### Step 4 — - Operationalize
Dashboard ("Varnish -- TTL Distribution"):
* Row 1 -- TTL bucket distribution pie chart.
* Row 2 -- Shortest TTL objects table.
* Row 3 -- Top miss URIs (candidates for TTL increase).

### Step 5 — - Troubleshooting

* **All objects have very short TTL** -- Backend is sending `Cache-Control: max-age=0` or `no-cache`. Override in VCL: `set beresp.ttl = 300s;` when safe. Check for `Pragma: no-cache` legacy headers too.

* **TTL set in VCL not taking effect** -- VCL processing order: `beresp.ttl` set in `vcl_backend_response` overrides backend headers. But if `beresp.uncacheable = true` is also set, the TTL is irrelevant.

* **Long TTL but content changes** -- Use purge or ban mechanisms to invalidate changed content proactively rather than relying solely on TTL expiry.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| rex field=_raw "TTL:\s+(?<ttl>\d+)"
| where isnotnull(ttl)
| bin ttl span=30
| stats count by ttl
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Object TTL Distribution Sampling» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/increasing-your-hitrate.html)
