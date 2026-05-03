<!-- AUTO-GENERATED from UC-5.20.128.json — DO NOT EDIT -->

---
id: "5.20.128"
title: "IPv6 BGP Route Leak Detection and Classification"
status: "verified"
criticality: "critical"
splunkPillar: "ES"
---

# UC-5.20.128 · IPv6 BGP Route Leak Detection and Classification

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** ES &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*A route leak is when a postal worker accidentally shares your mail route with the wrong postal network, so your letters take a detour through places they shouldn't go. We watch for these routing mistakes because they can cause delays or let someone peek at the letters.*

---

## Description

Detects IPv6 BGP route leaks (RFC 7908) where routes are propagated through unauthorized paths. Route leaks can cause traffic to traverse unintended autonomous systems, enabling surveillance or causing congestion. Classifies leaks by type and severity.

## Value

BGP route leaks are a frequent cause of internet outages and traffic interception. Unlike prefix hijacks (which forge the origin), route leaks propagate legitimate routes through unauthorized paths. Monitoring for anomalous AS paths — especially transit ASes appearing in paths from non-transit peers — provides early detection before the leak causes widespread impact.

## Implementation

Monitor BGP UPDATE messages for anomalous AS path patterns. Detect transit ASes in non-transit peer paths. Track path length anomalies.

## Detailed Implementation

### Prerequisites
- BGP peering with AS path logging.
- Knowledge of expected AS paths for your prefixes.

### Step 1 — Enable BGP UPDATE logging.

### Step 2 — Create monitoring searches for anomalous AS paths.

### Step 3 — Validate: Compare detected paths against expected paths.

### Step 4 — Operationalize
**Dashboard:** BGP route leak detection. **Alert:** Route leak detected — critical.

### Step 5 — Troubleshooting
- Deploy BGP Roles (RFC 9234) to prevent route leaks at the protocol level.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="juniper:junos") earliest=-24h
  "%BGP" AND ("ipv6" OR "afi.*2") AND ("UPDATE" OR "AS_PATH")
| rex field=_raw "AS_PATH\s*(?<as_path>[\d\s]+)"
| rex field=_raw "prefix\s*(?<prefix>[0-9a-fA-F:/]+)"
| eval path_length=len(replace(trim(as_path), "\d+", ".")) + 1
| eval route_leak=case(
    path_length > 6 AND match(as_path, "(?:^|\s)(174|3356|1299|2914|6461|3257)(\s|$)"), "POSSIBLE LEAK — transit AS in path from peer",
    match(as_path, "(\d+)\s+\1"), "PREPENDING detected (may indicate leak mitigation)",
    1=1, null())
| where isnotnull(route_leak)
| stats count as events by host, prefix, as_path, route_leak
| sort -events
```

## Visualization

(1) Table: detected route leaks. (2) Timeline: leak events. (3) AS path analysis. (4) Single-value: active leaks.

## Known False Positives

**Legitimate transit.** Some paths legitimately traverse transit ASes. Baseline normal paths before alerting.

**BGP communities.** Some route leaks are mitigated before they reach you via BGP communities. The alert may fire for paths that are already mitigated upstream.

## References

- [RFC 7908 — Problem Definition and Classification of BGP Route Leaks](https://www.rfc-editor.org/rfc/rfc7908)
- [RFC 9234 — Route Leak Prevention and Detection Using Roles in UPDATE and OPEN Messages](https://www.rfc-editor.org/rfc/rfc9234)
