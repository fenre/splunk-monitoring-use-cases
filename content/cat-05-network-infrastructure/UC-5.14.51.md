<!-- AUTO-GENERATED from UC-5.14.51.json — DO NOT EDIT -->

---
id: "5.14.51"
title: "Traefik Request Content-Length Distribution"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.51 · Traefik Request Content-Length Distribution

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Security, Performance &middot; **Status:** Draft

*We watch traefik request content-length distribution and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Big bodies stress buffers and may signal exfiltration.

## Value

Informs WAF and API gateway limits.

## Implementation

Use for large upload monitoring; pair with body size limits middleware.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| eval cl=tonumber(RequestContentSize)
| where cl > 5000000
| bin cl span=1000000
| stats count by cl, RouterName
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Traefik Request Content-Length Distribution» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/observability/access-logs/#access-logs)
