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

Improves edge hygiene and security posture.

## Implementation

High catch-all volume may be scanners; pair with WAF and geo blocking.

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
