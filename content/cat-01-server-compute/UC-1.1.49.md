<!-- AUTO-GENERATED from UC-1.1.49.json — DO NOT EDIT -->

---
id: "1.1.49"
title: "Memory Cgroup Limit Enforcement"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.49 · Memory Cgroup Limit Enforcement

## Description

Surfaces kernel and runtime messages that show cgroup memory pressure, including OOM-style messages tied to cgroups, so you can act before services are throttled or killed at the limit.

## Value

Right-sizing container memory, adjusting limits, or moving workloads is easier when you see which cgroup names hit the wall, instead of only seeing generic out-of-memory noise.

## Implementation

Forward `kern`/`containerd`/`kubelet`-class syslog that includes cgroup paths or IDs. Prefer structured `custom:cgroup_memory` events with `current`, `max`, and `cgroup_id` for ratio alerts; this search starts from raw syslog keywords and counts hits per host and cgroup id.

## Detailed Implementation

Prerequisites
• Ingest the OS log stream that records cgroup memory events (often forwarded as syslog) or deploy a `custom:cgroup_memory` input that samples `/sys/fs/cgroup`.

Step 1 — Configure data collection
For syslog, ensure the forwarder is allowed to read `/var/log/kern.log` or `journal` streams with kernel priority. For structured metrics, sample usage and limit in MiB and tag `cgroup_id` from the path.

Step 2 — Create the search and alert

```spl
index=os sourcetype=syslog ("memory.max_usage_in_bytes" OR (("Out of memory" OR "oom") AND "cgroup"))
| stats count by host, cgroup_id
| where count > 0
```

Adjust keywords to match your distribution’s wording. Add `rex` to extract `cgroup_id` if the field is only in `_raw`.

**Understanding this SPL** — Counts qualifying messages per host and cgroup; raise when any appear in the window (tighten to `>5` in busy environments).


Step 3 — Validate
Reproduce a benign limit in a test cgroup and compare host-side `systemd-cgtop` or `cat` of the cgroup’s `memory.current` to the log lines Splunk received.

Step 4 — Operationalize
Route to the platform or container SRE queue with links to the namespace or workload, and add a follow-up search on usage/limit ratio if you add structured metrics.



## SPL

```spl
index=os sourcetype=syslog ("memory.max_usage_in_bytes" OR "Out of memory") "cgroup"
| stats count by host, cgroup_id
| where count > 0
```

## Visualization

Table, Gauge

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
