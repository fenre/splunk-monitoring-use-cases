<!-- AUTO-GENERATED from UC-2.9.4.json — DO NOT EDIT -->

---
id: "2.9.4"
title: "OpenStack Keystone Token Issuance Rate and Authentication Failures"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.9.4 · OpenStack Keystone Token Issuance Rate and Authentication Failures

## Description

Authentication storms can indicate credential stuffing, mis-rotated application credentials, or IdP outages. Keystone is the choke point for all services.

## Value

Protects cloud control plane availability and speeds security investigations.

## Implementation

Parse JSON access logs if enabled. Whitelist service accounts in lookups. Correlate spikes with IdP incidents.

## SPL

```spl
index=openstack sourcetype="openstack:keystone" earliest=-4h
| eval hs=tonumber(http_status)
| eval fail=if(hs>=401 OR match(lower(reason), "(?i)invalid|locked|disabled"),1,0)
| bin _time span=5m
| stats count as authn, sum(fail) as fails by domain, _time
| eval fail_pct=round(100*fails/authn,2)
| where fails>50 AND fail_pct>10
```

## Visualization

Timechart failures; top domains; status code breakdown.

## References

- [OpenStack Keystone](https://docs.openstack.org/keystone/latest/)
