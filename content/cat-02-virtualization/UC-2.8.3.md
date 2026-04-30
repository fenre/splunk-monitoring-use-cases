<!-- AUTO-GENERATED from UC-2.8.3.json — DO NOT EDIT -->

---
id: "2.8.3"
title: "oVirt SPM Contention and Storage Pool Manager Election Spikes"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-2.8.3 · oVirt SPM Contention and Storage Pool Manager Election Spikes

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Performance, Fault &middot; **Status:** Verified

*We keep an eye on the control panel that runs your virtual datacenter—who changed what, whether storage and hosts are healthy, and when something is about to strand running machines.*

---

## Description

Frequent SPM elections or failures slow metadata operations and can stall LUN provisioning. This pattern often tracks flaky SAN paths or overloaded SPM hosts.

## Value

Avoids storage brownouts and long-running disk tasks across the virtual datacenter.

## Implementation

Tag SPM transitions with storage domain id. Compare with multipath events on the same hosts. Alert when hourly election count exceeds threshold.

## SPL

```spl
index=ovirt sourcetype="ovirt:spm" earliest=-24h
| eval ev=lower(coalesce(event, action))
| where match(ev, "(?i)elect|acquire|release|fail|spmove")
| bin _time span=1h
| stats count as spm_events, dc(host) as hosts by storage_domain, _time
| where spm_events>30
```

## Visualization

Timechart SPM events; table by storage domain; overlay with path failures if ingested.

## Known False Positives

AOS storage metrics can look worse during background heal, curator, or disk removal work; match alerts to Nutanix task progress and maintenance windows.

## References

- [oVirt Storage Administration](https://www.ovirt.org/documentation/administration_guide/#chap-Storage)
