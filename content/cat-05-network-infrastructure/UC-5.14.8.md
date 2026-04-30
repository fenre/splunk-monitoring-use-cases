<!-- AUTO-GENERATED from UC-5.14.8.json — DO NOT EDIT -->

---
id: "5.14.8"
title: "HAProxy Frontend Connection Limiting and Denials"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.8 · HAProxy Frontend Connection Limiting and Denials

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Security, Availability &middot; **Status:** Draft

*We watch haproxy frontend connection limiting and denials and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Protective limits look like outages if unexplained; logging proves intent.

## Value

Separates attack traffic from true capacity exhaustion.

## Implementation

Set intentional `maxconn`; baseline deny velocity to catch DDoS or misconfigured clients.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| regex _raw="(?i)(denied by tcp-request connection|too many connections)"
| bin _time span=1m
| stats count by frontend, _time
| where count > 50
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy Frontend Connection Limiting and Denials» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#maxconn)
