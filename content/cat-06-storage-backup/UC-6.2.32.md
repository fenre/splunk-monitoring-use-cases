<!-- AUTO-GENERATED from UC-6.2.32.json — DO NOT EDIT -->

---
id: "6.2.32"
title: "Ceph monitor clock skew between mon hosts"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.32 · Ceph monitor clock skew between mon hosts

## Description

Monitors rely on tight clock agreement; skew causes false peon timeouts and spurious quorum transitions that destabilize the whole cluster.

## Value

Prevents mysterious peering flaps that are expensive to diagnose during production hours.

## Implementation

Also monitor `chrony`/`ntpd` metrics on mon hosts in parallel. Alert integration with DC ops for stratum changes.

## SPL

```spl
index=os sourcetype="ceph:log" earliest=-2h
| search "clock skew" OR "clock drift" OR "time skew"
| rex field=_raw "(?i)mon\.(?<mon_id>\S+)"
| stats count as skew_events latest(_time) as last_seen by host, mon_id
| where skew_events > 3
| sort - skew_events
```

## Visualization

Table (mon, skew_events), timeline.

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
