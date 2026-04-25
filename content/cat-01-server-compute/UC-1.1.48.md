<!-- AUTO-GENERATED from UC-1.1.48.json — DO NOT EDIT -->

---
id: "1.1.48"
title: "NUMA Memory Imbalance Per Node"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.48 · NUMA Memory Imbalance Per Node

## Description

Detects lopsided free-memory distribution across NUMA nodes on a host, which can drive extra remote-memory access and unstable latency for memory-sensitive workloads.

## Value

Balancing memory across nodes—or moving workloads—reduces hard-to-debug slowdowns in databases and HPC-style apps that assume local memory and predictable latency.

## Implementation

Emit one event per (host, numa_node) with a `node_free` field. Compare max vs min free memory across nodes; alert when the ratio passes 1.5, indicating meaningful imbalance for your hardware generation.

## Detailed Implementation

Prerequisites
• Install `Splunk_TA_nix` and a script that reads each NUMA node’s meminfo and prints structured fields, including `numa_node` and `node_free` in KB or bytes consistently.
• Index into `os` (or your standard OS index) with sourcetype `custom:numa_meminfo`.

Step 1 — Configure data collection
Run the script every few minutes; keep units consistent. Document whether `node_free` is kB, bytes, or pages so operators do not mix comparisons.

Step 2 — Create the search and alert

```spl
index=os sourcetype=custom:numa_meminfo host=*
| stats avg(node_free) as avg_free by host, numa_node
| stats max(avg_free) as max_free, min(avg_free) as min_free by host
| eval imbalance_ratio=if(min_free>0, max_free/min_free, null())
| where imbalance_ratio > 1.5
```

**Understanding this SPL** — Averages per node, then for each host compares the fullest and emptiest node by free memory. Large ratios mean one node is much freer than another.


Step 3 — Validate
On the host, use `numastat` and `/sys/devices/system/node/node*/meminfo` to compare free lines against what Splunk received for the same timestamp.

Step 4 — Operationalize
Pair the alert with a short runbook: check VM placement, `numactl` policies, and large pinned allocations; consider OS tuning or workload moves.



## SPL

```spl
index=os sourcetype=custom:numa_meminfo host=*
| stats avg(node_free) as avg_free by host, numa_node
| stats max(avg_free) as max_free, min(avg_free) as min_free by host
| eval imbalance_ratio=max_free/min_free
| where imbalance_ratio > 1.5
```

## Visualization

Gauge, Heatmap

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
