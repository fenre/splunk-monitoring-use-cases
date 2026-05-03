<!-- AUTO-GENERATED from UC-5.14.9.json — DO NOT EDIT -->

---
id: "5.14.9"
title: "Varnish Cache Hit Ratio Trending (HIT vs MISS vs PASS)"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.9 · Varnish Cache Hit Ratio Trending (HIT vs MISS vs PASS)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Status:** Draft

*We watch varnish cache hit ratio trending (hit vs miss vs pass) and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Hit ratio ties origin cost and latency directly to cache effectiveness.

## Value

Operations teams trend Varnish cache hit, miss, and pass ratios over time, identifying cache effectiveness degradation and high-pass-rate endpoints that bypass caching.

## Implementation

Ship VSL via `varnishncsa` custom format or HEC JSON lines. For counter view add `varnish:stats` companion panel.

## Detailed Implementation

### Prerequisites
* Varnish Cache 6.x/7.x with `varnishncsa` or `varnishlog` forwarding to Splunk. Data in `index=proxy` with `sourcetype=varnish:access` (NCSA combined log format) or `sourcetype=varnish:log` (VSL format). Key fields: `VCL_call` (hit/miss/pass/pipe), `TTL`, `Timestamp`, `BerespStatus`, `RespStatus`.
* Cache outcomes: HIT (served from cache), MISS (fetched from backend, cached for next request), PASS (fetched from backend, not cached -- e.g., uncacheable response), PIPE (raw TCP tunnel). HIT ratio = HIT / (HIT + MISS + PASS) -- PIPs and errors excluded.
* Create `varnish_backends.csv` lookup: `backend`, `application`, `owner`, `expected_hit_ratio`.

### Step 1 — - Configure data collection
NCSA log format with hit/miss indicator:
```
varnishncsa -a -w /var/log/varnish/access.log -F '%h %l %u %t "%r" %s %b "%{Referer}i" "%{User-agent}i" %{Varnish:handling}x %{Varnish:hitmiss}x %D %{Varnish:time_firstbyte}x %{VCL_Log:backend}x'
```
The `%{Varnish:handling}x` and `%{Varnish:hitmiss}x` custom fields log the cache decision. `%D` is request duration in microseconds.

Verify:
```spl
index=proxy sourcetype="varnish:access" earliest=-4h
| stats count by hitmiss
```

### Step 2 — - Create the search and alert

**Primary search -- Cache hit ratio trending with outcome breakdown:**
```spl
index=proxy sourcetype="varnish:access" earliest=-24h
| eval outcome=lower(coalesce(hitmiss, handling, "unknown"))
| eval is_hit=if(outcome="hit", 1, 0)
| eval is_miss=if(outcome="miss", 1, 0)
| eval is_pass=if(outcome="pass", 1, 0)
| eval is_pipe=if(outcome="pipe", 1, 0)
| bin _time span=15m
| stats sum(is_hit) as hits sum(is_miss) as misses sum(is_pass) as passes sum(is_pipe) as pipes count as total by _time
| eval hit_ratio=round(100*hits/(hits+misses+passes), 2)
| eval cacheable_miss_pct=round(100*misses/(hits+misses+passes), 2)
| eval pass_pct=round(100*passes/total, 2)
| eval severity=case(hit_ratio < 50, "CRITICAL -- hit ratio below 50%", hit_ratio < 70, "WARNING -- hit ratio below 70%", pass_pct > 30, "WARNING -- high pass rate (".pass_pct."%)", 1==1, "OK")
| where severity != "OK"
| table _time, total, hits, misses, passes, hit_ratio, pass_pct, severity
```

**Per-URL cache effectiveness:**
```spl
index=proxy sourcetype="varnish:access" earliest=-4h
| rex field=request "\S+ (?<uri>\S+)"
| eval is_miss=if(lower(hitmiss)="miss", 1, 0)
| stats count as requests sum(is_miss) as misses by uri
| eval miss_rate=round(100*misses/requests, 1)
| where requests > 50 AND miss_rate > 50
| sort -miss_rate | head 20
```

### Step 3 — - Validate
(a) `varnishstat -1 | grep -E "MAIN.cache_(hit|miss|pass)"` -- compare counters.
(b) Intentionally PASS an object (`set beresp.uncacheable = true;` in VCL) and verify pass count increases.
(c) Verify per-URL miss rates align with TTL settings.

### Step 4 — - Operationalize
Dashboard ("Varnish -- Cache Hit Ratio"):
* Row 1 -- Single-value: "Hit ratio (%)", "Misses", "Passes", "Pipes".
* Row 2 -- Hit ratio timechart (15m intervals).
* Row 3 -- Top URLs by miss rate.

Alerting:
* Critical (hit ratio < 50% for > 15 min): cache is largely ineffective.
* Warning (hit ratio < 70% for > 15 min): investigate cache invalidation or TTL issues.

### Step 5 — - Troubleshooting

* **Low hit ratio after deploy** -- New VCL deployment may have reset the cache. Also check if `Vary` headers have changed, causing cache fragmentation. Run: `varnishtop -i BerespHeader -I "^Vary:"`.

* **High pass rate** -- VCL logic is marking requests uncacheable. Common causes: (1) `req.http.Cookie` present (default VCL passes cookie requests), (2) `Cache-Control: no-cache` from backend, (3) POST/PUT methods. Review VCL `vcl_recv` for pass logic.

* **High miss rate on specific URL** -- Check TTL: `varnishlog -q "ReqURL eq '/path'" -i TTL`. If TTL is too short, objects expire before being re-requested. Consider increasing `beresp.ttl` for stable content.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| eval hit=if(match(_raw, "(?i)\bHIT\b|VCL_hit"),1,0)
| eval miss=if(match(_raw, "(?i)VCL_miss|\bMISS\b"),1,0)
| eval pass=if(match(_raw, "(?i)VCL_pass|\bPASS\b"),1,0)
| bin _time span=5m
| stats sum(hit) as hits sum(miss) as misses sum(pass) as passes
| eval hit_ratio=round(100*hits/(hits+misses+passes+0.001),2)
| timechart span=5m avg(hit_ratio) as hit_pct
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Cache Hit Ratio Trending (HIT vs MISS vs PASS)» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/intro.html)
