<!-- AUTO-GENERATED from UC-1.1.87.json — DO NOT EDIT -->

---
id: "1.1.87"
title: "Process Namespace Breakout Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.87 · Process Namespace Breakout Detection

## Description

Pulls **auditd** rows that mention **setns** or container escape–class types for a quick table of **host**, **pid**, and **comm** when your rules actually emit those strings.

## Value

Namespace games are core to **container** breakouts; even a noisy first-pass search gives IR a lead on which binary to **strace** next.

## Implementation

`type=CONTAINER_ESCAPE` may not exist on stock kernels—replace with your **key=** from `auditd` after you add the rules from your container hardening standard.

## Detailed Implementation

Prerequisites
• Tuned **auditd** on **container** hosts; consider **eBPF** complements for depth, not as a Splunk replacement.


Step 3 — Validate
`ausearch` for your **key**; `lsns` on the host to see namespaces live; **crictl** / **docker** for the **container** context when available.

Step 4 — Operationalize
Merge with the **AppArmor/SELinux** deny use cases when the process is both namespaced and blocked by policy.



## SPL

```spl
index=os sourcetype=linux_audit ("setns" OR syscall=setns OR type=CONTAINER)
| stats count by host, pid, comm
| where count>0
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
