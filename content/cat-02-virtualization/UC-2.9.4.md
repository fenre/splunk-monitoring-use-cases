<!-- AUTO-GENERATED from UC-2.9.4.json — DO NOT EDIT -->

---
id: "2.9.4"
title: "OpenStack Keystone Token Issuance Rate and Authentication Failures"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.9.4 · OpenStack Keystone Token Issuance Rate and Authentication Failures

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security, Performance &middot; **Status:** Verified

*We monitor the building blocks of your private cloud—computers, networks, disks, and logins—so new systems come up reliably and people are not locked out when something upstream hiccups.*

---

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

## Known False Positives

OpenStack metrics may swing during image builds, large migrations, or control-plane rolling updates; verify services are healthy in parallel before declaring data-plane failure.

## References

- [OpenStack Keystone](https://docs.openstack.org/keystone/latest/)
