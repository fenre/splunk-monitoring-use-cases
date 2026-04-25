<!-- AUTO-GENERATED from UC-2.1.40.json — DO NOT EDIT -->

---
id: "2.1.40"
title: "VM NUMA Alignment"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.40 · VM NUMA Alignment

## Description

VMs that span NUMA nodes experience cross-node memory access latency — 2-3x slower than local access. Large VMs (8+ vCPUs or 32+ GB RAM) are most affected. Proper NUMA alignment can improve performance by 10-30% for memory-intensive workloads like databases and in-memory caches.

## Value

VMs that span NUMA nodes experience cross-node memory access latency — 2-3x slower than local access. Large VMs (8+ vCPUs or 32+ GB RAM) are most affected. Proper NUMA alignment can improve performance by 10-30% for memory-intensive workloads like databases and in-memory caches.

## Implementation

Collect host NUMA topology from inventory and VM sizing. Flag VMs whose vCPU count exceeds a single NUMA node's core count. For critical workloads, set `numa.vcpu.preferHT=true` and consider vNUMA configuration. Monitor `mem.llSwapUsed` for cross-NUMA penalties.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, custom scripted input.
• Ensure the following data sources are available: `sourcetype=vmware:perf:mem`, host NUMA topology.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect host NUMA topology from inventory and VM sizing. Flag VMs whose vCPU count exceeds a single NUMA node's core count. For critical workloads, set `numa.vcpu.preferHT=true` and consider vNUMA configuration. Monitor `mem.llSwapUsed` for cross-NUMA penalties.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:perf:mem" counter="mem.llSwapUsed.average"
| stats avg(Value) as ll_swap_kb by vm_name, host
| join max=1 host [search index=vmware sourcetype="vmware:inv:hostsystem" | eval numa_nodes=numNumaNodes | table host, numa_nodes, numCpuCores]
| join max=1 vm_name [search index=vmware sourcetype="vmware:inv:vm" | table vm_name, numCpu, memoryMB]
| eval vcpus_per_node=round(numCpuCores/numa_nodes, 0)
| eval spans_numa=if(numCpu > vcpus_per_node, "Yes", "No")
| where spans_numa="Yes"
| table vm_name, host, numCpu, memoryMB, vcpus_per_node, numa_nodes, spans_numa, ll_swap_kb
| sort -memoryMB
```

Understanding this SPL

**VM NUMA Alignment** — VMs that span NUMA nodes experience cross-node memory access latency — 2-3x slower than local access. Large VMs (8+ vCPUs or 32+ GB RAM) are most affected. Proper NUMA alignment can improve performance by 10-30% for memory-intensive workloads like databases and in-memory caches.

Documented **Data sources**: `sourcetype=vmware:perf:mem`, host NUMA topology. **App/TA** (typical add-on context): `Splunk_TA_vmware`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:perf:mem. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:perf:mem". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vm_name, host** so each row reflects one combination of those dimensions.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• `eval` defines or adjusts **vcpus_per_node** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **spans_numa** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where spans_numa="Yes"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **VM NUMA Alignment**): table vm_name, host, numCpu, memoryMB, vcpus_per_node, numa_nodes, spans_numa, ll_swap_kb
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, vCPUs, NUMA alignment), Scatter plot (VM size vs NUMA fit), Single value (misaligned VMs).

## SPL

```spl
index=vmware sourcetype="vmware:perf:mem" counter="mem.llSwapUsed.average"
| stats avg(Value) as ll_swap_kb by vm_name, host
| join max=1 host [search index=vmware sourcetype="vmware:inv:hostsystem" | eval numa_nodes=numNumaNodes | table host, numa_nodes, numCpuCores]
| join max=1 vm_name [search index=vmware sourcetype="vmware:inv:vm" | table vm_name, numCpu, memoryMB]
| eval vcpus_per_node=round(numCpuCores/numa_nodes, 0)
| eval spans_numa=if(numCpu > vcpus_per_node, "Yes", "No")
| where spans_numa="Yes"
| table vm_name, host, numCpu, memoryMB, vcpus_per_node, numa_nodes, spans_numa, ll_swap_kb
| sort -memoryMB
```

## Visualization

Table (VM, vCPUs, NUMA alignment), Scatter plot (VM size vs NUMA fit), Single value (misaligned VMs).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
