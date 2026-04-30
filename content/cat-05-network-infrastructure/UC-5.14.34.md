<!-- AUTO-GENERATED from UC-5.14.34.json — DO NOT EDIT -->

---
id: "5.14.34"
title: "Squid External ACL Helper Failures"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.34 · Squid External ACL Helper Failures

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Security &middot; **Status:** Draft

*We watch squid external acl helper failures and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

External ACLs are on the critical path for every request.

## Value

Prevents cascading auth outages.

## Implementation

Scale concurrent helpers; cap slow identity providers.

## SPL

```spl
index=proxy sourcetype="squid:cache"
| regex _raw="(?i)external_acl.*(?:fail|timeout|error)"
| stats count by host
| where count > 5
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid External ACL Helper Failures» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/external_acl_type/)
