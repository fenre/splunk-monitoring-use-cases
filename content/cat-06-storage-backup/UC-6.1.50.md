<!-- AUTO-GENERATED from UC-6.1.50.json — DO NOT EDIT -->

---
id: "6.1.50"
title: "NetApp ONTAP MetroCluster switchover and DR event correlation"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.50 · NetApp ONTAP MetroCluster switchover and DR event correlation

## Description

Unplanned MetroCluster switchovers or failed negotiated switchovers strand I/O on one site and often precede extended outages. Rapid EMS correlation helps validate bridges, NVMe shelves, and mediator health before applications time out.

## Value

Reduces mean time to detect for site or fabric incidents affecting synchronous replication, protecting RTO for business-critical NAS and SAN workloads.

## Implementation

Install `TA-netapp_ontap` on a heavy forwarder. Enable EMS via `inputs.conf` (syslog from the cluster management LIF or scripted REST `/api/support/ems/events`). Normalize sourcetype to `netapp:ontap:event` or `netapp:ontap:ems` in `props.conf`. Schedule a 1-minute alert excluding maintenance windows from a CSV lookup.

## SPL

```spl
index=storage (sourcetype="netapp:ontap:event" OR sourcetype="netapp:ontap:ems")
| search (message="*metrocluster*" OR message="*MetroCluster*" OR message="*switchover*" OR EMSMessage="*metrocluster*" OR EMSMessage="*switchover*")
| eval cluster=coalesce(cluster_name, cluster, cluster_uuid)
| eval node=coalesce(node_name, node, origin_node)
| table _time, cluster, node, severity, EMSMessage, message
| sort - _time
```

## Visualization

Timeline by severity, table (cluster, node, message), single value (event count 15m).

## References

- [Splunk Add-on for NetApp Data ONTAP (Splunkbase)](https://splunkbase.splunk.com/app/1664)
- [MetroCluster IP documentation](https://docs.netapp.com/us-en/ontap-metrocluster/)
