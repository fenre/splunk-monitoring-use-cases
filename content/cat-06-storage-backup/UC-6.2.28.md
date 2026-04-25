<!-- AUTO-GENERATED from UC-6.2.28.json — DO NOT EDIT -->

---
id: "6.2.28"
title: "Ceph RADOS Gateway request latency and HTTP 5xx error rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.28 · Ceph RADOS Gateway request latency and HTTP 5xx error rate

## Description

S3/Swift workloads depend on predictable RGW latency. Rising p95 with elevated 5xx rates often tracks backend OSD saturation or Keystone integration failures.

## Value

Protects application SLAs for cloud-native apps using Ceph object storage.

## Implementation

Prefer structured ops logs with `http_status` at index time. If only unstructured, use `rex` for Apache/nginx-style lines.

## SPL

```spl
index=storage (sourcetype="ceph:log" OR sourcetype="ceph:pool")
| search rgw OR "RADOSGW" OR ":7480" OR ":443"
| eval code=coalesce(http_status, status_code)
| eval lat_ms=coalesce(request_time_ms, latency_ms)
| bin span=5m _time
| stats count as reqs perc95(lat_ms) as p95_ms sum(eval(if(code>=500,1,0))) as err5 by _time, rgw_instance
| eval err_pct=round(err5/reqs*100,2)
| where err_pct > 1 OR p95_ms > 500
```

## Visualization

Timechart (p95 and error %), table (RGW instance).

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
