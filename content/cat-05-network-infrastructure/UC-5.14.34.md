<!-- AUTO-GENERATED from UC-5.14.34.json — DO NOT EDIT -->

---
id: "5.14.34"
title: "Squid External ACL Helper Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.34 · Squid External ACL Helper Failures

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

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/external_acl_type/)
