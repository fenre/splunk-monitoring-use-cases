<!-- AUTO-GENERATED from UC-5.14.25.json — DO NOT EDIT -->

---
id: "5.14.25"
title: "Squid Cache Peer Selection and Failure Events"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.25 · Squid Cache Peer Selection and Failure Events

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Status:** Draft

*We watch squid cache peer selection and failure events and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Peer flaps shift load unexpectedly across the mesh.

## Value

Operations teams track Squid cache peer (parent/sibling) selection outcomes and ICP query failures, detecting peer hierarchy disruptions that force direct origin fetches.

## Implementation

Log `cache_peer` lines at appropriate debug level; aggregate to Splunk via UF.

## Detailed Implementation

### Prerequisites
* Squid cache logs with peer/parent selection events. Data in `index=proxy` with `sourcetype=squid:access` or `sourcetype=squid:cache`. Key fields: `peer_status` (e.g., DIRECT, PARENT_HIT, SIBLING_HIT, CLOSEST_PARENT_MISS), `peer_host`.
* Cache peers: Squid can forward cache misses to parent proxies or query sibling caches using ICP (Internet Cache Protocol) or HTCP. Peer selection failures mean Squid can't reach its configured parent/sibling, causing it to go DIRECT (if allowed) or fail. Peer hierarchy: `cache_peer parent|sibling <host> <port> <icp_port>`.

### Step 1 — - Configure data collection
```
# squid.conf
cache_peer parent1.example.com parent 3128 3130
cache_peer sibling1.example.com sibling 3128 3130
```
Verify:
```spl
index=proxy sourcetype="squid:access" earliest=-4h
| stats count by peer_status, peer_host
```

### Step 2 — - Create the search and alert

**Primary search -- Peer selection and failure analysis:**
```spl
index=proxy sourcetype="squid:access" earliest=-4h
| eval peer_result=upper(coalesce(peer_status, "UNKNOWN"))
| eval peer=coalesce(peer_host, "DIRECT")
| eval is_direct=if(match(peer_result, "DIRECT") OR peer="DIRECT", 1, 0)
| eval is_peer_fail=if(match(peer_result, "(?i)DEAD|TIMEOUT|FAIL|NONE"), 1, 0)
| eval is_peer_hit=if(match(peer_result, "(?i)PARENT_HIT|SIBLING_HIT"), 1, 0)
| bin _time span=15m
| stats count as total sum(is_direct) as direct sum(is_peer_fail) as peer_failures sum(is_peer_hit) as peer_hits by _time
| eval direct_pct=round(100*direct/total, 1)
| eval severity=case(peer_failures > 50, "CRITICAL -- cache peer failures", direct_pct > 90 AND total > 1000, "WARNING -- almost all traffic bypassing peers", 1==1, "OK")
| where severity != "OK"
| table _time, total, direct, direct_pct, peer_hits, peer_failures, severity
```

### Step 3 — - Validate
(a) `squidclient mgr:cache_peer` -- shows peer status and ICP query statistics.
(b) Stop a peer proxy and verify peer_failures increase and traffic goes DIRECT.
(c) Check ICP: `squidclient mgr:icp` -- ICP query/reply counts.

### Step 4 — - Operationalize
Dashboard ("Squid -- Cache Peers"):
* Row 1 -- Single-value: "Peer hit ratio", "Peer failures", "Direct %".
* Row 2 -- Peer selection distribution.

Alerting:
* Critical (peer failures > 50/hr): parent/sibling proxy unreachable.
* Warning (direct > 90%): peer hierarchy not being utilized.

### Step 5 — - Troubleshooting

* **All traffic going DIRECT** -- Check: (1) `cache_peer` directives in squid.conf, (2) `never_direct deny all` to force peer usage, (3) ICP port (3130) is open between proxies.

* **Peer timeout** -- ICP queries timing out. Check: (1) network connectivity to peer, (2) `icp_query_timeout` (default 2s), (3) peer's `icp_port` is listening.

* **Sibling returning MISS but has the object** -- ICP query might be configured to check only memory, not disk. Check peer's `icp_hit_stale` and cache store configuration.

## SPL

```spl
index=proxy sourcetype="squid:cache"
| regex _raw="(?i)(peer.*(?:DEAD|DOWN|FAILED)|DETECT UP|DETECT DOWN)"
| stats count by cache_peer
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid Cache Peer Selection and Failure Events» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/cache_peer/)
