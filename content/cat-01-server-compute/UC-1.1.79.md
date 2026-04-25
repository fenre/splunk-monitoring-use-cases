<!-- AUTO-GENERATED from UC-1.1.79.json — DO NOT EDIT -->

---
id: "1.1.79"
title: "Setcap Binary Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.79 · Setcap Binary Monitoring

## Description

Rolls up any audit trail that points to a Linux capability or file-caps change so you can spot new **setcap**-style rights on disk without parsing **getcap** output manually each week.

## Value

File capabilities are a **sudo**-like bypass; watching them is key on immutable infrastructure hosts where the base image should not drift outside **CI**.

## Implementation

Align the leading **search** with your `auditd` `key=`. Some builds only have **SYSCALL**+**BPR_FCAPS**; others emit **type=capability**—merge until your parser is stable, then harden the search.

## Detailed Implementation

Prerequisites
• `audit` rules for **bprm** and **cap** syscalls, not only **execve**.

**CIM** — There is no standard, widely deployed CIM projection for `file` capabilities; keep the primary search on `linux_audit` until your team models these into a custom `Change` mapping.


Step 3 — Validate
`getcap -r` on a host subset when investigating; not every capability shows in **auditd** the same way—pair with a weekly **AIDE** run from the FIM use case.

Step 4 — Operationalize
Require **CAB** for any new **setcap** in higher environments.



## SPL

```spl
index=os sourcetype=linux_audit (type=CAPABILITY_CHANGE OR "setcap" OR "BPR_FCAPS" OR "bprm_fcaps")
| stats count by host, name, comm
| where count>0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
