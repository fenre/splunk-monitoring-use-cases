<!-- AUTO-GENERATED from UC-1.2.95.json — DO NOT EDIT -->

---
id: "1.2.95"
title: "Windows Container Health Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.95 · Windows Container Health Monitoring

## Description

Windows containers running on Server 2019+ need monitoring for resource limits, failures, and networking issues to ensure application availability.

## Value

Container hosts need the same care as VMs: if Hyper-V guests pause or the compute service errors, every app in those instances stalls together.

## Implementation

Enable Hyper-V Compute Operational log for container lifecycle events. Configure Perfmon inputs for container-specific counters (CPU, memory, network). Track container crashes (unexpected stops), OOM kills, and resource exhaustion. Alert on container restart loops and CPU throttling. Integrate with Docker/containerd logs for application-level visibility.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-Compute-Operational`, `sourcetype=Perfmon:Container`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Hyper-V Compute Operational log for container lifecycle events. Configure Perfmon inputs for container-specific counters (CPU, memory, network). Track container crashes (unexpected stops), OOM kills, and resource exhaustion. Alert on container restart loops and CPU throttling. Integrate with Docker/containerd logs for application-level visibility.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Hyper-V-Compute-Operational"
| eval Status=case(EventCode=13001,"Created", EventCode=13003,"Started", EventCode=13005,"Stopped", EventCode=13007,"Terminated", 1=1,"Other")
| stats count by host, ContainerName, Status
| append [search index=perfmon source="Perfmon:Container" counter="% Processor Time"
  | stats avg(Value) as AvgCPU max(Value) as MaxCPU by host, instance]
```

Understanding this SPL

**Windows Container Health Monitoring** — Windows containers running on Server 2019+ need monitoring for resource limits, failures, and networking issues to ensure application availability.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-Compute-Operational`, `sourcetype=Perfmon:Container`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, ContainerName, Status** so each row reflects one combination of those dimensions.
• Appends rows from a subsearch with `append`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

Understanding this CIM / accelerated SPL

**Windows Container Health Monitoring** — Windows containers running on Server 2019+ need monitoring for resource limits, failures, and networking issues to ensure application availability.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-Compute-Operational`, `sourcetype=Perfmon:Container`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where avg_cpu > 90` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (container status), Timechart (resource usage), Alert on crash loops.

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Hyper-V-Compute-Operational"
| eval Status=case(EventCode=13001,"Created", EventCode=13003,"Started", EventCode=13005,"Stopped", EventCode=13007,"Terminated", 1=1,"Other")
| stats count by host, ContainerName, Status
| append [search index=perfmon source="Perfmon:Container" counter="% Processor Time"
  | stats avg(Value) as AvgCPU max(Value) as MaxCPU by host, instance]
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as c
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| where c > 80
```

## Visualization

Table (container status), Timechart (resource usage), Alert on crash loops.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
