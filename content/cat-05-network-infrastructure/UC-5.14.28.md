<!-- AUTO-GENERATED from UC-5.14.28.json — DO NOT EDIT -->

---
id: "5.14.28"
title: "Squid HTTP Access Denied by ACL"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.28 · Squid HTTP Access Denied by ACL

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

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/http_access/)
