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

Stabilizes hierarchical cache designs.

## Implementation

Log `cache_peer` lines at appropriate debug level; aggregate to Splunk via UF.

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
