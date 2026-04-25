<!-- AUTO-GENERATED from UC-6.1.36.json — DO NOT EDIT -->

---
id: "6.1.36"
title: "Ceph Cluster Daemon Log Slow Request and Heartbeat Warnings"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.36 · Ceph Cluster Daemon Log Slow Request and Heartbeat Warnings

## Description

Recurring slow requests and heartbeat warnings in OSD logs precede stuck PGs, flapping OSDs, and client I/O timeouts. They are a leading indicator before `ceph health` moves out of `HEALTH_OK`.

## Value

Lets operators rebalance, replace disks, or tune `osd_op_complaint_time` before the cluster enters recovery storms or read-only modes.

## Implementation

Deploy forwarders on Ceph nodes with a `monitor://` stanza on `/var/log/ceph/*.log` (path varies by distro) or ship the same files through SC4S. Set `sourcetype=ceph:log` and `index=os`. Tune the event threshold per cluster size; small clusters may alert at >5 warnings/hour, large clusters use percentiles via summary indexing.

## SPL

```spl
index=os OR index=storage sourcetype="ceph:log" earliest=-4h
| search "slow request" OR "heartbeat_check" OR "blocked op" OR "request took"
| rex field=_raw max_match=1 "(?i)osd\.(?<osd_id>\d+)"
| stats count as warn_events latest(_time) as last_seen by host osd_id
| where warn_events > 10
| sort - warn_events
```

## Visualization

Timeline (warning bursts), table (host, OSD, count), top values on `host`.

## References

- [Ceph Documentation — Troubleshooting](https://docs.ceph.com/en/latest/rados/troubleshooting/)
- [Splunk Docs — Get data from files and directories](https://docs.splunk.com/Documentation/Splunk/latest/Data/Monitorfilesanddirectories)
