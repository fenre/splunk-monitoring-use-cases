<!-- AUTO-GENERATED from UC-2.1.20.json — DO NOT EDIT -->

---
id: "2.1.20"
title: "Resource Pool Utilization and Limits"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.20 · Resource Pool Utilization and Limits

## Description

Resource pools with hard limits can silently throttle VMs even when the cluster has spare capacity. Pools without reservations provide no guarantees during contention. Monitoring utilization vs. configured limits/reservations reveals misconfigurations that cause unpredictable performance.

## Value

Resource pools with hard limits can silently throttle VMs even when the cluster has spare capacity. Pools without reservations provide no guarantees during contention. Monitoring utilization vs. configured limits/reservations reveals misconfigurations that cause unpredictable performance.

## Implementation

Collect resource pool inventory via Splunk_TA_vmware. Alert when resource pool utilization approaches its configured limit (>80%). Flag resource pools with unlimited limits and zero reservations in production — they offer no guarantees. Cross-reference with VM performance to detect pool-level throttling.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:inv:resourcepool`, `sourcetype=vmware:perf:cpu`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect resource pool inventory via Splunk_TA_vmware. Alert when resource pool utilization approaches its configured limit (>80%). Flag resource pools with unlimited limits and zero reservations in production — they offer no guarantees. Cross-reference with VM performance to detect pool-level throttling.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:resourcepool"
| eval cpu_limit_ghz=if(cpuAllocation_limit=-1, "Unlimited", round(cpuAllocation_limit/1000, 1))
| eval mem_limit_gb=if(memoryAllocation_limit=-1, "Unlimited", round(memoryAllocation_limit/1024, 1))
| table name, cluster, cpuAllocation_reservation, cpu_limit_ghz, cpuAllocation_shares, memoryAllocation_reservation, mem_limit_gb, memoryAllocation_shares
| sort cluster, name
```

Understanding this SPL

**Resource Pool Utilization and Limits** — Resource pools with hard limits can silently throttle VMs even when the cluster has spare capacity. Pools without reservations provide no guarantees during contention. Monitoring utilization vs. configured limits/reservations reveals misconfigurations that cause unpredictable performance.

Documented **Data sources**: `sourcetype=vmware:inv:resourcepool`, `sourcetype=vmware:perf:cpu`. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:resourcepool. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:resourcepool". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cpu_limit_ghz** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **mem_limit_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Resource Pool Utilization and Limits**): table name, cluster, cpuAllocation_reservation, cpu_limit_ghz, cpuAllocation_shares, memoryAllocation_reservation, mem_limit_gb, memoryAl…
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (pool hierarchy, limits, utilization), Tree map (pools by resource allocation), Gauge (utilization vs limit).

## SPL

```spl
index=vmware sourcetype="vmware:inv:resourcepool"
| eval cpu_limit_ghz=if(cpuAllocation_limit=-1, "Unlimited", round(cpuAllocation_limit/1000, 1))
| eval mem_limit_gb=if(memoryAllocation_limit=-1, "Unlimited", round(memoryAllocation_limit/1024, 1))
| table name, cluster, cpuAllocation_reservation, cpu_limit_ghz, cpuAllocation_shares, memoryAllocation_reservation, mem_limit_gb, memoryAllocation_shares
| sort cluster, name
```

## Visualization

Table (pool hierarchy, limits, utilization), Tree map (pools by resource allocation), Gauge (utilization vs limit).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
