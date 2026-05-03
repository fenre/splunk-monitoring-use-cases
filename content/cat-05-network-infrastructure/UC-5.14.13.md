<!-- AUTO-GENERATED from UC-5.14.13.json — DO NOT EDIT -->

---
id: "5.14.13"
title: "Varnish Grace and Keep Serving Stale Content Frequency"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.13 · Varnish Grace and Keep Serving Stale Content Frequency

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Reliability &middot; **Status:** Draft

*We watch varnish grace and keep serving stale content frequency and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Stale serving shields origins but can confuse content owners if unexplained.

## Value

Operations teams track how often Varnish serves stale objects via grace mode, identifying when TTLs are too short or backends too slow to refresh objects before they expire.

## Implementation

Tune thresholds against editorial SLOs; document VCL `grace`/`keep`.

## Detailed Implementation

### Prerequisites
* Varnish logs with grace/stale-serving indicators. Key fields: `TTL`, `Grace`, `Keep`, `VCL_call` with `hit` on expired objects. Data in `index=proxy` with `sourcetype=varnish:log`.
* Grace mode: when an object's TTL expires but is within the grace period, Varnish serves the stale object immediately and triggers a background fetch. This avoids waiting for the backend. `beresp.grace` sets the grace window. `beresp.keep` sets how long to keep the object for conditional requests (IMS/If-None-Match).
* Frequent grace serving indicates backends are slow or TTLs are too short relative to request frequency.

### Step 1 — - Configure data collection
VCL grace configuration:
```
sub vcl_backend_response {
    set beresp.ttl = 300s;
    set beresp.grace = 3600s;
    set beresp.keep = 86400s;
}
```
Verify:
```spl
index=proxy sourcetype="varnish:log" earliest=-4h
| where match(_raw, "(?i)grace|stale|HIT.*expired|hit-for-miss")
| stats count by _raw | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- Grace/stale serving frequency:**
```spl
index=proxy (sourcetype="varnish:log" OR sourcetype="varnish:access") earliest=-4h
| eval is_grace=if(match(_raw, "(?i)grace|HIT.*expired|stale-while-revalidate"), 1, 0)
| eval is_normal_hit=if(match(hitmiss, "(?i)^hit$") AND is_grace=0, 1, 0)
| eval is_miss=if(match(hitmiss, "(?i)miss"), 1, 0)
| bin _time span=15m
| stats sum(is_grace) as grace_hits sum(is_normal_hit) as fresh_hits sum(is_miss) as misses count as total by _time
| eval grace_pct=round(100*grace_hits/total, 2)
| eval severity=case(grace_pct > 20, "HIGH -- >20% requests served stale", grace_pct > 10, "WARNING -- >10% stale", 1==1, "OK")
| where severity != "OK"
| table _time, total, fresh_hits, grace_hits, grace_pct, misses, severity
```

### Step 3 — - Validate
(a) Set a very short TTL (e.g., 5s) with long grace (1h) on a test object. Request it after TTL expires -- should be served from grace.
(b) `varnishlog -q "TTL" -i TTL` -- shows TTL decisions including grace.
(c) Verify background fetches are succeeding after grace hits.

### Step 4 — - Operationalize
Dashboard ("Varnish -- Grace & Stale Serving"):
* Row 1 -- Single-value: "Grace hit rate (%)", "Stale objects served (4h)".
* Row 2 -- Grace vs fresh hit ratio timechart.

Alerting:
* Warning (grace_pct > 20% for > 30 min): most cached content is stale.

### Step 5 — - Troubleshooting

* **High grace serving** -- TTLs are too short or backends are too slow to refresh in time. Options: (1) increase `beresp.ttl`, (2) optimize backend response time, (3) use background fetches (`beresp.grace`) to smooth the impact.

* **Grace hit but no background fetch** -- Varnish may be rate-limiting backend requests. Check `MAIN.backend_busy` and `MAIN.backend_conn` stats.

* **Keep vs grace confusion** -- `grace` = serve stale while fetching. `keep` = retain object for conditional (304) requests even after grace expires. Both should be set for optimal cache behavior.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| regex _raw="(?i)(grace|stale|hit-for-pass)"
| bin _time span=15m
| stats count by host, _time
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Grace and Keep Serving Stale Content Frequency» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/vcl-grace.html)
