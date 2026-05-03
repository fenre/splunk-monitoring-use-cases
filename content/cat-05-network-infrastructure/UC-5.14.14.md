<!-- AUTO-GENERATED from UC-5.14.14.json — DO NOT EDIT -->

---
id: "5.14.14"
title: "Varnish Ban List Growth and Lurker Lag"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.14 · Varnish Ban List Growth and Lurker Lag

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Operations &middot; **Status:** Draft

*We watch varnish ban list growth and lurker lag and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Ban lag leaves outdated objects live especially on busy news sites.

## Value

Operations teams monitor Varnish ban list accumulation and lurker thread processing lag, preventing cache invalidation backlogs that degrade per-request performance.

## Implementation

Investigate slow lurker or excessive `ban()` calls from publishers.

## Detailed Implementation

### Prerequisites
* Varnish statistics and log data for ban operations. Key counters: `MAIN.bans`, `MAIN.bans_lurker_tested`, `MAIN.bans_lurker_tests_tested`, `MAIN.bans_lurker_obj_killed`, `MAIN.bans_obj`, `MAIN.bans_req`. Data in `index=proxy` with `sourcetype=varnish:stats` or `sourcetype=varnish:log`.
* Bans: Varnish's cache invalidation mechanism. `ban req.url ~ "^/api/"` adds a ban expression. Objects matching the expression are removed when accessed (request-side ban) or when the lurker thread scans them (lurker ban). Ban list growth means bans accumulate faster than the lurker can process them. Lurker lag = time since the lurker last completed a full scan.

### Step 1 — - Configure data collection
Same as UC-5.14.11. Verify:
```spl
index=proxy sourcetype="varnish:stats" earliest=-4h
| spath input=_raw path="MAIN.bans.value" output=total_bans
| spath input=_raw path="MAIN.bans_lurker_tests_tested.value" output=lurker_tested
| stats latest(total_bans) as bans latest(lurker_tested) as lurker_tests
```

### Step 2 — - Create the search and alert

**Primary search -- Ban list size and lurker lag:**
```spl
index=proxy sourcetype="varnish:stats" earliest=-4h
| spath input=_raw path="MAIN.bans.value" output=total_bans
| spath input=_raw path="MAIN.bans_obj.value" output=obj_bans
| spath input=_raw path="MAIN.bans_req.value" output=req_bans
| spath input=_raw path="MAIN.bans_lurker_obj_killed.value" output=lurker_killed
| eval total_bans=tonumber(total_bans), obj_bans=tonumber(obj_bans), req_bans=tonumber(req_bans), lurker_killed=tonumber(lurker_killed)
| bin _time span=5m
| stats latest(total_bans) as active_bans latest(obj_bans) as obj_bans latest(req_bans) as req_bans latest(lurker_killed) as lurker_killed by _time
| streamstats current=f last(active_bans) as prev_bans last(lurker_killed) as prev_killed
| eval ban_growth=active_bans - prev_bans
| eval lurker_kills=lurker_killed - prev_killed
| eval severity=case(active_bans > 1000, "CRITICAL -- >1000 active bans", active_bans > 100, "HIGH -- ban list growing", ban_growth > 50 AND lurker_kills < 10, "WARNING -- lurker lag", 1==1, "OK")
| where severity != "OK"
| table _time, active_bans, ban_growth, req_bans, obj_bans, lurker_kills, severity
```

### Step 3 — - Validate
(a) `varnishadm ban.list` -- shows active bans and their creation time.
(b) Add a test ban: `varnishadm ban req.url == "/test"`. Verify ban list grows.
(c) Check lurker status: `varnishstat -1 | grep bans_lurker`.

### Step 4 — - Operationalize
Dashboard ("Varnish -- Ban Management"):
* Row 1 -- Single-value: "Active bans", "Lurker kills (/5m)", "Ban growth rate".
* Row 2 -- Ban list size timechart.

Alerting:
* Critical (active bans > 1000): ban list causing performance impact.
* Warning (ban growth outpacing lurker kills): lurker can't keep up.

### Step 5 — - Troubleshooting

* **Ban list keeps growing** -- Bans are being added faster than the lurker removes them. Options: (1) use `ban obj.status != 0` (obj-ban) instead of `req.url` (req-ban) -- obj-bans can be evaluated by the lurker, req-bans cannot. (2) Reduce ban frequency.

* **Lurker not killing objects** -- Check `ban_lurker_age` and `ban_lurker_sleep` parameters. If sleep is too high, the lurker is slow. `varnishadm param.set ban_lurker_sleep 0.01`.

* **Request-side bans (req_bans) growing** -- These bans can only be evaluated per-request, not by the lurker. Convert to obj-based bans where possible for better performance.

## SPL

```spl
index=proxy sourcetype="varnish:stats"
| eval bans=tonumber(bans), done=tonumber(bans_completed)
| eval lag=bans-done
| where lag > 1000
| table _time, host, bans, done, lag
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Ban List Growth and Lurker Lag» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/purging.html)
