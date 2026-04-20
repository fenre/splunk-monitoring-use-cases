---
id: "2.1.42"
title: "VM CPU Ready Time Percentage"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.42 · VM CPU Ready Time Percentage

## Description

Measures time VMs wait for physical CPU — distinct from host utilization. High CPU ready time indicates over-committed CPU; VMs are queued waiting for scheduler time even when host CPU % appears acceptable. Critical for identifying latent contention invisible from guest metrics.

## Value

Measures time VMs wait for physical CPU — distinct from host utilization. High CPU ready time indicates over-committed CPU; VMs are queued waiting for scheduler time even when host CPU % appears acceptable. Critical for identifying latent contention invisible from guest metrics.

## Implementation

TA-vmware collects cpu.ready.summation (milliseconds VM waited per 20s interval). Formula: ready_pct = Value / 20000 * 100 (20s = 20000ms). Alert when avg_ready_pct >5% over 10 minutes. Use rolling 15-min average to smooth spikes. Correlate with cluster CPU utilization and DRS migrations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:perf:cpu` (counter=cpu.ready.summation).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
TA-vmware collects cpu.ready.summation (milliseconds VM waited per 20s interval). Formula: ready_pct = Value / 20000 * 100 (20s = 20000ms). Alert when avg_ready_pct >5% over 10 minutes. Use rolling 15-min average to smooth spikes. Correlate with cluster CPU utilization and DRS migrations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:perf:cpu" counter="cpu.ready.summation"
| eval ready_pct = round(Value / 20000 * 100, 2)
| stats avg(ready_pct) as avg_ready_pct, max(ready_pct) as peak_ready_pct by host, vm_name
| where avg_ready_pct > 5
| sort -avg_ready_pct
| table vm_name, host, avg_ready_pct, peak_ready_pct
```

Understanding this SPL

**VM CPU Ready Time Percentage** — Measures time VMs wait for physical CPU — distinct from host utilization. High CPU ready time indicates over-committed CPU; VMs are queued waiting for scheduler time even when host CPU % appears acceptable. Critical for identifying latent contention invisible from guest metrics.

Documented **Data sources**: `sourcetype=vmware:perf:cpu` (counter=cpu.ready.summation). **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:perf:cpu. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:perf:cpu". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **ready_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, vm_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_ready_pct > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **VM CPU Ready Time Percentage**): table vm_name, host, avg_ready_pct, peak_ready_pct


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heatmap (VMs vs hosts, colored by ready %), Bar chart (top VMs by ready time), Line chart (ready % trend).

## SPL

```spl
index=vmware sourcetype="vmware:perf:cpu" counter="cpu.ready.summation"
| eval ready_pct = round(Value / 20000 * 100, 2)
| stats avg(ready_pct) as avg_ready_pct, max(ready_pct) as peak_ready_pct by host, vm_name
| where avg_ready_pct > 5
| sort -avg_ready_pct
| table vm_name, host, avg_ready_pct, peak_ready_pct
```

## Visualization

Heatmap (VMs vs hosts, colored by ready %), Bar chart (top VMs by ready time), Line chart (ready % trend).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
