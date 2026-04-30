<!-- AUTO-GENERATED from UC-5.14.28.json — DO NOT EDIT -->

---
id: "5.14.28"
title: "Squid HTTP Access Denied by ACL"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.28 · Squid HTTP Access Denied by ACL

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Audit &middot; **Status:** Draft

*We watch squid http access denied by acl and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Policy tuning needs ranked deny reasons not anecdotes.

## Value

Supports zero-trust web gateway reviews.

## Implementation

Add ACL tag to `access_log format` (Squid 4+); sanitize sensitive domains in dashboards.

## SPL

```spl
index=proxy sourcetype="squid:access"
| where match(code, "TCP_DENIED|ERR_ACCESS_DENIED|NONE_ABORTED")
| stats count by acl, dst_domain, src_ip
| sort - count
| head 40
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid HTTP Access Denied by ACL» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/http_access/)
