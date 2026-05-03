<!-- AUTO-GENERATED from UC-5.14.32.json — DO NOT EDIT -->

---
id: "5.14.32"
title: "Squid Delay Pool Throttling Signals"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.32 · Squid Delay Pool Throttling Signals

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Governance &middot; **Status:** Draft

*We watch squid delay pool throttling signals and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Fair-use rules should be observable, not silent.

## Value

Operations teams detect Squid delay pool bandwidth throttling activation, identifying clients being rate-limited and evaluating whether throttle thresholds need adjustment.

## Implementation

Avoid verbose debug in prod; use short cache log notices or manager counters.

## Detailed Implementation

### Prerequisites
* Squid cache logs with delay pool events. Data in `index=proxy` with `sourcetype=squid:cache` or `sourcetype=squid:access`. Key events: delay pool class assignment, throttling applied.
* Delay pools: Squid's bandwidth throttling mechanism. Three classes: (1) single aggregate pool, (2) per-network pool, (3) per-host pool. When a client exceeds their bandwidth allocation, Squid slows the response. `delay_access` ACLs assign requests to pools. High throttling rates may indicate: (1) bandwidth limits too restrictive, (2) bandwidth hogs, (3) need for capacity upgrade.

### Step 1 — - Configure data collection
```
# squid.conf -- class 3 (per-host) delay pool
delay_pools 1
delay_class 1 3
delay_parameters 1 -1/-1 1000000/1000000 500000/500000
delay_access 1 allow all
```
Enable delay pool debugging:
```
debug_options ALL,1 77,5
```
Verify:
```spl
index=proxy (sourcetype="squid:cache" OR sourcetype="squid:access") earliest=-4h
| where match(_raw, "(?i)delay.*pool|throttl|bandwidth.*limit|delay_id")
| stats count
```

### Step 2 — - Create the search and alert

**Primary search -- Delay pool throttling signals:**
```spl
index=proxy (sourcetype="squid:cache" OR sourcetype="squid:access") earliest=-4h
| where match(_raw, "(?i)delay.*pool|throttl|bandwidth|delay_id|slow.*down")
| eval throttle_event=case(match(_raw, "(?i)delay.*pool.*assigned|delay_id"), "POOL_ASSIGNED", match(_raw, "(?i)throttl|slow|delayed"), "THROTTLED", match(_raw, "(?i)bandwidth.*exceeded|limit.*reached"), "LIMIT_HIT", 1==1, "OTHER")
| rex "(?:client|from|src)\s+(?<throttled_client>[0-9.]+)"
| stats count as events dc(throttled_client) as affected_clients by throttle_event
| eval severity=case(throttle_event="THROTTLED" AND events > 100, "WARNING -- heavy throttling", affected_clients > 50, "INFO -- many clients throttled", 1==1, "INFO")
| where severity != "INFO"
| table throttle_event, events, affected_clients, severity
```

### Step 3 — - Validate
(a) Download a large file through the proxy with delay pools active -- verify speed is limited.
(b) `squidclient mgr:delay` -- shows delay pool statistics.
(c) Monitor access log for requests with high `elapsed` time on cacheable content (indicates throttling).

### Step 4 — - Operationalize
Dashboard ("Squid -- Delay Pools"):
* Row 1 -- Single-value: "Throttled requests", "Affected clients".
* Row 2 -- Throttling event timeline.

### Step 5 — - Troubleshooting

* **Legitimate traffic throttled** -- Delay pool limits too restrictive. Increase `delay_parameters` rates. Or add ACL exceptions for specific destinations: `delay_access 1 deny allowed_fast_sites`.

* **Delay pools not working** -- Check: (1) `delay_pools` count matches number of defined pools, (2) `delay_access` ACL matches traffic, (3) `delay_class` is correct for the desired behavior (1=aggregate, 2=network, 3=individual).

* **Bandwidth usage still high despite throttling** -- Delay pools throttle individual connections, not aggregate. Many connections from the same client can bypass effective limits. Consider class 2 (per-network) or class 3 (per-host) pools.

## SPL

```spl
index=proxy sourcetype="squid:cache"
| regex _raw="(?i)Delay pool|delay_pool"
| bin _time span=5m
| stats count by host, _time
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid Delay Pool Throttling Signals» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/delay_pools/)
