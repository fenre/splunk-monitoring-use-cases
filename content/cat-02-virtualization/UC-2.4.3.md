---
id: "2.4.3"
title: "VM-to-Host Density Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.4.3 · VM-to-Host Density Trending

## Description

VM density (VMs per host) is a key capacity metric. Rising density indicates growing consolidation ratios that may exceed host capacity. Density spikes after HA failovers reveal hosts running at unsustainable loads. Trending density over time supports procurement planning and workload distribution decisions.

## Value

VM density (VMs per host) is a key capacity metric. Rising density indicates growing consolidation ratios that may exceed host capacity. Density spikes after HA failovers reveal hosts running at unsustainable loads. Trending density over time supports procurement planning and workload distribution decisions.

## Implementation

Count powered-on VMs per host from inventory data. Track daily for trend analysis. Calculate vcpu-to-pcpu ratio and memory overcommit per host. Alert when any host exceeds your density threshold (e.g., >30 VMs, >4:1 vCPU ratio, or >1.5:1 memory overcommit). Useful after HA events to verify surviving hosts aren't overloaded.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, `Splunk_TA_windows`.
• Ensure the following data sources are available: VM inventory from all hypervisors.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Count powered-on VMs per host from inventory data. Track daily for trend analysis. Calculate vcpu-to-pcpu ratio and memory overcommit per host. Alert when any host exceeds your density threshold (e.g., >30 VMs, >4:1 vCPU ratio, or >1.5:1 memory overcommit). Useful after HA events to verify surviving hosts aren't overloaded.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm" power_state="poweredOn"
| stats dc(vm_name) as vm_count, sum(numCpu) as total_vcpus, sum(memoryMB) as total_mem_mb by host
| eval total_mem_gb=round(total_mem_mb/1024, 0)
| sort -vm_count
| table host, vm_count, total_vcpus, total_mem_gb
```

Understanding this SPL

**VM-to-Host Density Trending** — VM density (VMs per host) is a key capacity metric. Rising density indicates growing consolidation ratios that may exceed host capacity. Density spikes after HA failovers reveal hosts running at unsustainable loads. Trending density over time supports procurement planning and workload distribution decisions.

Documented **Data sources**: VM inventory from all hypervisors. **App/TA** (typical add-on context): `Splunk_TA_vmware`, `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **total_mem_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **VM-to-Host Density Trending**): table host, vm_count, total_vcpus, total_mem_gb


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (VMs per host), Line chart (density trend over months), Table (host, VM count, ratios), Heatmap (density by cluster).

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm" power_state="poweredOn"
| stats dc(vm_name) as vm_count, sum(numCpu) as total_vcpus, sum(memoryMB) as total_mem_mb by host
| eval total_mem_gb=round(total_mem_mb/1024, 0)
| sort -vm_count
| table host, vm_count, total_vcpus, total_mem_gb
```

## Visualization

Bar chart (VMs per host), Line chart (density trend over months), Table (host, VM count, ratios), Heatmap (density by cluster).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
