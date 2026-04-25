<!-- AUTO-GENERATED from UC-2.9.7.json — DO NOT EDIT -->

---
id: "2.9.7"
title: "OpenStack Nova Scheduler Retry and Placement Filter Exhaustion Audit"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.9.7 · OpenStack Nova Scheduler Retry and Placement Filter Exhaustion Audit

## Description

High scheduler retries mean builds queue while operators think capacity exists. This exposes filter misconfiguration or stale placement inventory.

## Value

Speeds time-to-build for tenants and reduces mysterious ERROR states.

## Implementation

Tune log verbosity carefully. Alert on retry>3 patterns. Correlate with `openstack:placement` inventory sync.

## SPL

```spl
index=openstack sourcetype="openstack:nova" earliest=-4h
| search match(lower(_raw), "(?i)scheduler|retrying|no valid host|filter")
| eval r=tonumber(retry)
| where r>=3
| stats count as deep_retries, values(filter_name) as filters by host
| sort - deep_retries
```

## Visualization

Timechart retry rate; table filters; instance samples.

## References

- [OpenStack Nova Scheduler](https://docs.openstack.org/nova/latest/user/filter-scheduler.html)
