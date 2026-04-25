<!-- AUTO-GENERATED from UC-2.9.5.json — DO NOT EDIT -->

---
id: "2.9.5"
title: "OpenStack Glance Image Upload and Download Throughput"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.9.5 · OpenStack Glance Image Upload and Download Throughput

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

## References

- [OpenStack Glance](https://docs.openstack.org/glance/latest/)
