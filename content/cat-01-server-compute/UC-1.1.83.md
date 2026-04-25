<!-- AUTO-GENERATED from UC-1.1.83.json — DO NOT EDIT -->

---
id: "1.1.83"
title: "Process CPU Affinity Changes"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.83 · Process CPU Affinity Changes

## Description

Aggregates **auditd** events for **sched_setaffinity**-class syscalls so you can review who pins threads to CPUs—common for **HFT** tuning, rare for random shells.

## Value

Unexpected affinity changes after a compromise can hide **crypto** miners on a subset of cores; for **HPC** estates, this is also how you prove apps respect your **NUMA** policy.

## Implementation

Syscall numbers vary by arch—replace `204` with your **ausyscall** output for **x86_64** vs **aarch64**. Prefer a stable `key=cpu_affinity` in **auditd** and search on `key` once you add it.

## Detailed Implementation

Prerequisites
• **auditd** syscall rules; be mindful of **performance** load on syscall=all systems—use **filters**.

**CIM** — **N/A**; map to a custom **Change** or **Endpoint** story only if your team standardizes it.


Step 3 — Validate
`ausearch -sc sched_setaffinity` (or your key) on the host; **taskset -p** on the **pid** when it is still alive.

Step 4 — Operationalize
Pair with the **NUMA imbalance** use case when both fire for the same host.



## SPL

```spl
index=os sourcetype=linux_audit (syscall=204 OR syscall=sched_setaffinity OR "SCHED_SETAFFINITY")
| stats count by host, pid, comm
| where count>0
```

## Visualization

Table, Alert

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
