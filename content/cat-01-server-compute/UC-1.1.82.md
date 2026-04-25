<!-- AUTO-GENERATED from UC-1.1.82.json — DO NOT EDIT -->

---
id: "1.1.82"
title: "D-State (Uninterruptible Sleep) Process Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.82 · D-State (Uninterruptible Sleep) Process Detection

## Description

Counts processes in **D** (uninterruptible sleep) per **host** from each `ps` poll, so you can spot stuck I/O waiters that will not answer **SIGKILL** until the kernel finishes the op.

## Value

Long **D** states line up with bad storage, **NFS** hangs, and driver bugs; they are a top call for storage and OS SRE before app teams burn days in app logs only.

## Implementation

Use the `S` or `state` field your **ps** sourcetype actually ships; add `| where dstate_count>5` if a single **D** from a **df** snapshot is normal on your **NFS** clients.

## Detailed Implementation

Prerequisites
• **ps** script on a **5**-**15** minute cadence; faster if you need near-real-time **D** detection for trading stacks.

**CIM** — **process_state** naming may differ (`D` vs `uninterruptible`); align `cimSpl` after you see **Fieldsummary** on `Processes`.


Step 3 — Validate
`ps -o pid,stat,wchan,cmd` (or `top` then **H** for threads) on the host; use `echo w > /proc/sysrq-trigger` only with an operator and a runbook, not casually.

Step 4 — Operationalize
Open a **storage** bridge with **dmesg** **I/O** errors the same minute.



## SPL

```spl
index=os sourcetype=ps host=* (S="D" OR state="D")
| stats count as dstate_count by host
| where dstate_count>0
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Endpoint.Processes where Processes.process_state="D" by Processes.dest Processes.process_name span=5m | where count>0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
