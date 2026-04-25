<!-- AUTO-GENERATED from UC-2.1.1.json — DO NOT EDIT -->

---
id: "2.1.1"
title: "ESXi Host CPU Contention"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.1 · ESXi Host CPU Contention

## Description

CPU ready time measures how long a VM waits for physical CPU. High values (>5%) mean the host is overcommitted and VMs are starved for compute.

## Value

CPU ready time measures how long a VM waits for physical CPU. High values (>5%) mean the host is overcommitted and VMs are starved for compute.

## Implementation

Install `Splunk_TA_vmware` (Splunkbase 3215) on a Heavy Forwarder. Create a read-only vCenter service account with `System.View` and `VirtualMachine.Interact.ConsoleInteract` privileges. Configure collection intervals in the TA setup UI: 300s for performance metrics, 600s for inventory, 3600s for events. Set the `host_segment` to resolve ESXi hostnames. Verify data flow with `index=vmware sourcetype=vmware:perf:cpu | head 5`. Alert when CPU ready exceeds 5% per VM.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:perf:cpu`, vCenter performance metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install `Splunk_TA_vmware` (Splunkbase 3215) on a Heavy Forwarder. Create a read-only vCenter service account with `System.View` and `VirtualMachine.Interact.ConsoleInteract` privileges. Configure collection intervals in the TA setup UI: 300s for performance metrics, 600s for inventory, 3600s for events. Set the `host_segment` to resolve ESXi hostnames. Verify data flow with `index=vmware sourcetype=vmware:perf:cpu | head 5`. Alert when CPU ready exceeds 5% per VM.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:perf:cpu" counter="cpu.ready.summation"
| eval ready_pct = round(Value / 20000 * 100, 2)
| stats avg(ready_pct) as avg_ready by host, vm_name
| where avg_ready > 5
| sort -avg_ready
```

Understanding this SPL

**ESXi Host CPU Contention** — CPU ready time measures how long a VM waits for physical CPU. High values (>5%) mean the host is overcommitted and VMs are starved for compute.

Documented **Data sources**: `sourcetype=vmware:perf:cpu`, vCenter performance metrics. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:perf:cpu. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:perf:cpu". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **ready_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, vm_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_ready > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heatmap (VMs vs. hosts, colored by ready %), Bar chart (top VMs by ready time), Line chart (trending).

## SPL

```spl
index=vmware sourcetype="vmware:perf:cpu" counter="cpu.ready.summation"
| eval ready_pct = round(Value / 20000 * 100, 2)
| stats avg(ready_pct) as avg_ready by host, vm_name
| where avg_ready > 5
| sort -avg_ready
```

## Visualization

Heatmap (VMs vs. hosts, colored by ready %), Bar chart (top VMs by ready time), Line chart (trending).

## References

- [Splunk Add-on for VMware](https://splunkbase.splunk.com/app/3215)
- [vSphere API](https://developer.vmware.com/)
