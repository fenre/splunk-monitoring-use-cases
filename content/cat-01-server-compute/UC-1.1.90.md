<!-- AUTO-GENERATED from UC-1.1.90.json — DO NOT EDIT -->

---
id: "1.1.90"
title: "Journal Disk Usage Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.90 · Journal Disk Usage Monitoring

## Description

Tracks the latest **journal_size** in **MB** per **host** from a structured feed and alerts when persistent **journald** data on disk grows past about **one** **gigabyte** (tune to root **volume** size).

## Value

**Journal** growth on small **root** disks is a classic way to accidentally fill **/** and take down services that still need a few free **inodes** and blocks.

## Implementation

Run the script daily or weekly—**journal** size does not need per-minute precision. Consider `| where journal_size>0.15*root_fs_mb` once you ingest **df** for the same **host**.

## Detailed Implementation

Prerequisites
• **systemd** **journal** persistent storage enabled; know whether you are on **volatile** **/run/log/journal** only (this UC needs **/var/log/journal** or an explicit size path).

**CIM** — The `cimSpl` is a **disk** **fullness** proxy on **/** or **/var**, not the literal **journal** byte counter—use it when you already ingest **df** into **Performance.Storage**.


Step 3 — Validate
`journalctl --disk-usage` on the host; **systemd-tmpfiles** / **journald.conf** for **SystemMaxUse**; **df** **-h** on the **mount** that holds **journal**.

Step 4 — Operationalize
After a page, run `journalctl --vacuum-time=` or **--vacuum-size=** per your retention policy, not “delete everything” without **legal** review.



## SPL

```spl
index=os sourcetype=custom:journalctl_usage host=*
| stats latest(disk_usage_mb) as journal_size by host
| where journal_size>1000
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as used_pct from datamodel=Performance where nodename=Performance.Storage AND (Performance.mount="/" OR Performance.mount="/var") by Performance.host span=1d | where used_pct>85
```

## Visualization

Gauge, Single Value

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
