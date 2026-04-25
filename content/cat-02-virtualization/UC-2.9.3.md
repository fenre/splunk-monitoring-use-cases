<!-- AUTO-GENERATED from UC-2.9.3.json — DO NOT EDIT -->

---
id: "2.9.3"
title: "OpenStack Cinder Volume Attach and Detach Error Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.9.3 · OpenStack Cinder Volume Attach and Detach Error Rate

## Description

Attach failures trap instances in BUILD or ERROR and break stateful apps. Trending error rates by backend isolates driver or SAN regressions.

## Value

Improves storage SLOs for databases and Kubernetes volumes on Cinder.

## Implementation

Tag backend driver name. Baseline hourly success ratio. Alert on spikes after upgrades.

## SPL

```spl
index=openstack sourcetype="openstack:cinder" earliest=-24h
| eval st=lower(coalesce(status, result))
| eval act=lower(coalesce(action, operation))
| where match(act, "(?i)attach|detach")
| eval ok=if(match(st, "(?i)success|complete"),1,0)
| bin _time span=1h
| stats count as n, sum(ok) as okc by _time, backend, host
| eval err_rate=round(100*(n-okc)/n,2)
| where err_rate>5
```

## Visualization

Timechart error rate; breakdown by backend; top error messages.

## References

- [OpenStack Cinder](https://openstack.org/cinder)
