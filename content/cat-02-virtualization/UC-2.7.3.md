<!-- AUTO-GENERATED from UC-2.7.3.json — DO NOT EDIT -->

---
id: "2.7.3"
title: "Proxmox VE Cluster Quorum Loss Detection from Corosync and pmxcfs Signals"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-2.7.3 · Proxmox VE Cluster Quorum Loss Detection from Corosync and pmxcfs Signals

## Description

Quorum loss freezes cluster management APIs and can strand operators during incidents. Corosync and pmxcfs messages are the earliest observable signals of ring faults, vote drift, or qdevice misconfiguration.

## Value

Shortens time-to-detect for cluster brain-split conditions and prevents destructive manual intervention on partially connected nodes.

## Implementation

Route corosync logs with host, ring, and node identity. Build eventtypes for quorum phrases. Page on critical phrases; throttle warnings with a sustained-count threshold. Correlate with NIC driver updates and switch port events.

## SPL

```spl
index=pve (sourcetype="proxmox:task" OR sourcetype="proxmox:ha") earliest=-4h
| search match(lower(_raw), "(?i)quorum|qdevice|not quorate|lost.*quorum|split.?brain|totem.*fault|ring.*fault")
| eval sev=if(match(lower(_raw), "(?i)lost.*quorum|not quorate|split.?brain"), "critical", "warning")
| bin _time span=5m
| stats count as sigs, values(host) as nodes by sev, _time
| where sigs>=5 AND sev="critical"
```

## Visualization

Timeline of quorum-related signals; choropleth or table of affected nodes; raw drilldown.

## References

- [Proxmox Cluster Manager pvecm](https://pve.proxmox.com/pve-docs/chapter-pvecm.html)
