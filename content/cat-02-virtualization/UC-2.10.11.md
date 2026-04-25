<!-- AUTO-GENERATED from UC-2.10.11.json — DO NOT EDIT -->

---
id: "2.10.11"
title: "VxRail vSAN Encryption Key Manager Reachability Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.10.11 · VxRail vSAN Encryption Key Manager Reachability Audit

## Description

KMS outages or stale rotation policies risk compliance findings and data access issues during host rebuilds.

## Value

Protects encryption SLAs for regulated workloads on HCI.

## Implementation

Ingest crypto health daily. Alert on degraded. Track rotation age against policy (example 180-day warning).

## SPL

```spl
index=vxrail sourcetype="vxrail:vsan" earliest=-24h
| eval cs=lower(crypto_state)
| where cs!="healthy" OR now()-tonumber(last_rotation_epoch)>15552000
| stats latest(crypto_state) as state, latest(kmip_server) as kms by cluster_id
```

## Visualization

Table clusters vs KMS; timeline state; single value overdue rotations.

## References

- [vSAN encryption](https://www.vmware.com/products/cloud-infrastructure/vsan)
