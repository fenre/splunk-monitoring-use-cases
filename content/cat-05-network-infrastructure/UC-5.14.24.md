<!-- AUTO-GENERATED from UC-5.14.24.json — DO NOT EDIT -->

---
id: "5.14.24"
title: "Squid Internal DNS Resolver Errors and Latency"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.24 · Squid Internal DNS Resolver Errors and Latency

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Status:** Draft

*We watch squid internal dns resolver errors and latency and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Resolver health is easy to overlook until all MISS latency spikes.

## Value

Shortens outages where Squid is blamed but DNS is root cause.

## Implementation

Point `dns_nameservers` at resilient anycast resolvers; alert on repeated failures.

## SPL

```spl
index=proxy sourcetype="squid:cache"
| regex _raw="(?i)(DNS|ipcache|fqdn).*(?:FAIL|timeout|missing)"
| stats count by host
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid Internal DNS Resolver Errors and Latency» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/dns_nameservers/)
