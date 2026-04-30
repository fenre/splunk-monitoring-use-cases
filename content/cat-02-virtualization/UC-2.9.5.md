<!-- AUTO-GENERATED from UC-2.9.5.json — DO NOT EDIT -->

---
id: "2.9.5"
title: "OpenStack Glance Image Upload and Download Throughput"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.9.5 · OpenStack Glance Image Upload and Download Throughput

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Status:** Verified

*We monitor the building blocks of your private cloud—computers, networks, disks, and logins—so new systems come up reliably and people are not locked out when something upstream hiccups.*

---

## Description

Slow image transfers delay autoscale and CI image refreshes. Throughput trending highlights object-store latency or congested API networks.

## Value

Keeps golden image pipelines fast and reduces build queue time.

## Implementation

Compute mbps per operation. Alert on sustained slow large transfers. Compare stores (file vs rbd vs swift).

## SPL

```spl
index=openstack sourcetype="openstack:glance" earliest=-24h
| eval mbps=tonumber(bytes_transferred)/(1024*1024)/tonumber(duration_sec)
| where mbps<10 AND tonumber(bytes_transferred)>104857600
| stats avg(mbps) as avg_mbps, count as slow_ops by store, image_id
```

## Visualization

Line chart throughput; table slow images; histogram latency.

## Known False Positives

OpenStack metrics may swing during image builds, large migrations, or control-plane rolling updates; verify services are healthy in parallel before declaring data-plane failure.

## References

- [OpenStack Glance](https://docs.openstack.org/glance/latest/)
