---
id: "2.2.6"
title: "Hyper-V Host Resource Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.2.6 · Hyper-V Host Resource Utilization

## Description

Host-level CPU and memory utilization across all VMs determines capacity headroom. Unlike per-VM monitoring, host-level metrics reveal when the hypervisor itself is under pressure — affecting all VMs simultaneously. Tracks the root partition overhead which is invisible from within VMs.

## Value

Host-level CPU and memory utilization across all VMs determines capacity headroom. Unlike per-VM monitoring, host-level metrics reveal when the hypervisor itself is under pressure — affecting all VMs simultaneously. Tracks the root partition overhead which is invisible from within VMs.

## Implementation

Configure Perfmon inputs for `Hyper-V Hypervisor Logical Processor` (% Total Run Time, % Hypervisor Run Time) and `Memory` (Available MBytes, Committed Bytes). Set interval=60. Alert when host CPU exceeds 85% or available memory drops below 10% of physical. Track root partition overhead separately.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Hyper-V Perfmon inputs).
• Ensure the following data sources are available: `sourcetype=Perfmon:HyperV` (Hyper-V Hypervisor Logical Processor, Memory counters).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon inputs for `Hyper-V Hypervisor Logical Processor` (% Total Run Time, % Hypervisor Run Time) and `Memory` (Available MBytes, Committed Bytes). Set interval=60. Alert when host CPU exceeds 85% or available memory drops below 10% of physical. Track root partition overhead separately.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:HyperV" object="Hyper-V Hypervisor Logical Processor" instance="_Total" counter="% Total Run Time"
| bin _time span=5m
| stats avg(Value) as avg_cpu by host, _time
| where avg_cpu > 85
| table _time, host, avg_cpu
```

Understanding this SPL

**Hyper-V Host Resource Utilization** — Host-level CPU and memory utilization across all VMs determines capacity headroom. Unlike per-VM monitoring, host-level metrics reveal when the hypervisor itself is under pressure — affecting all VMs simultaneously. Tracks the root partition overhead which is invisible from within VMs.

Documented **Data sources**: `sourcetype=Perfmon:HyperV` (Hyper-V Hypervisor Logical Processor, Memory counters). **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V Perfmon inputs). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:HyperV. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:HyperV". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_cpu > 85` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Hyper-V Host Resource Utilization**): table _time, host, avg_cpu

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 85
```

Understanding this CIM / accelerated SPL

**Hyper-V Host Resource Utilization** — Host-level CPU and memory utilization across all VMs determines capacity headroom. Unlike per-VM monitoring, host-level metrics reveal when the hypervisor itself is under pressure — affecting all VMs simultaneously. Tracks the root partition overhead which is invisible from within VMs.

Documented **Data sources**: `sourcetype=Perfmon:HyperV` (Hyper-V Hypervisor Logical Processor, Memory counters). **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V Perfmon inputs). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where avg_cpu > 85` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (CPU/memory over time per host), Gauge (current utilization), Heatmap (hosts by load).

## SPL

```spl
index=perfmon sourcetype="Perfmon:HyperV" object="Hyper-V Hypervisor Logical Processor" instance="_Total" counter="% Total Run Time"
| bin _time span=5m
| stats avg(Value) as avg_cpu by host, _time
| where avg_cpu > 85
| table _time, host, avg_cpu
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 85
```

## Visualization

Line chart (CPU/memory over time per host), Gauge (current utilization), Heatmap (hosts by load).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
