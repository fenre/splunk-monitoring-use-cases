<!-- AUTO-GENERATED from UC-5.14.44.json — DO NOT EDIT -->

---
id: "5.14.44"
title: "Traefik Service Health Check Failures"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.44 · Traefik Service Health Check Failures

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Status:** Draft

*We watch traefik service health check failures and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Router health drives load balancing; silent failures hurt most.

## Value

Accelerates rollback when a deploy breaks probes.

## Implementation

Ship container stdout via sidecar; set log level INFO in prod.

## SPL

```spl
index=proxy sourcetype="traefik:log"
| regex _raw="(?i)(Health check failed|Status.*DOWN|Server.*Unhealthy)"
| stats count by service_name
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Traefik Service Health Check Failures» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/routing/services/#health-check)
