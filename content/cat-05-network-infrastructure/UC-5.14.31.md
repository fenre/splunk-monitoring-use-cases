<!-- AUTO-GENERATED from UC-5.14.31.json — DO NOT EDIT -->

---
id: "5.14.31"
title: "Squid HTTP Status Code Distribution"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.31 · Squid HTTP Status Code Distribution

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Security &middot; **Status:** Draft

*We watch squid http status code distribution and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Spikes in 5xx often precede origin incidents visible here first.

## Value

Gives NOC a single pane for user-impacting web errors.

## Implementation

Separate `ERR_*` Squid codes from upstream HTTP for triage.

## SPL

```spl
index=proxy sourcetype="squid:access"
| eval sc=tonumber(status_code)
| where isnotnull(sc)
| bin sc span=100
| timechart span=1h count by sc
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid HTTP Status Code Distribution» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/http_status_codes/)
