<!-- AUTO-GENERATED from UC-2.8.7.json — DO NOT EDIT -->

---
id: "2.8.7"
title: "oVirt VDSM Host Agent Restarts and Crash Loops"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-2.8.7 · oVirt VDSM Host Agent Restarts and Crash Loops

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Fault, Reliability &middot; **Status:** Verified

*We keep an eye on the control panel that runs your virtual datacenter—who changed what, whether storage and hosts are healthy, and when something is about to strand running machines.*

---

## Description

VDSM ties kernel storage, networking, and libvirt to Engine. Crash loops desynchronize host state and break migrations.

## Value

Stabilizes the data plane before guests see I/O errors or network drops.

## Implementation

Collect vdsm.log from all hosts. Baseline error rates. Correlate spikes with package updates or new LUNs.

## SPL

```spl
index=ovirt sourcetype="ovirt:vdsm" earliest=-4h
| eval lv=upper(coalesce(log_level, level))
| where lv="ERROR" OR match(lower(_raw), "(?i)traceback|crash|respawn|supervisor")
| bin _time span=15m
| stats count as err_by_host by host, _time
| where err_by_host>=20
```

## Visualization

Timechart errors per host; top traceback tokens; link to host firmware ticket.

## Known False Positives

AOS storage metrics can look worse during background heal, curator, or disk removal work; match alerts to Nutanix task progress and maintenance windows.

## References

- [VDSM component](https://www.ovirt.org/develop/developer-guide/vdsm/)
