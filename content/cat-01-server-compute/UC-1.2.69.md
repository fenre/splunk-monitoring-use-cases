---
id: "1.2.69"
title: "Page File Usage & Exhaustion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.69 · Page File Usage & Exhaustion

## Description

Page file exhaustion prevents new process creation and causes "out of virtual memory" errors. System-managed page files can grow to fill the disk.

## Value

Page file exhaustion prevents new process creation and causes "out of virtual memory" errors. System-managed page files can grow to fill the disk.

## Implementation

Configure Perfmon inputs for Paging File object: `% Usage`, `% Usage Peak` (interval=300). Alert when usage exceeds 70% sustained (indicates memory pressure requiring page file). Track peak usage — if it regularly exceeds 80%, the system needs more RAM or has a memory leak. Also monitor EventCode 2004 in System log (page file too small) as a reactive indicator.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:Paging_File` (counter: % Usage, % Usage Peak).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon inputs for Paging File object: `% Usage`, `% Usage Peak` (interval=300). Alert when usage exceeds 70% sustained (indicates memory pressure requiring page file). Track peak usage — if it regularly exceeds 80%, the system needs more RAM or has a memory leak. Also monitor EventCode 2004 in System log (page file too small) as a reactive indicator.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:Paging_File" counter="% Usage" instance="_Total"
| timechart span=15m avg(Value) as pf_pct by host
| where pf_pct > 70
```

Understanding this SPL

**Page File Usage & Exhaustion** — Page file exhaustion prevents new process creation and causes "out of virtual memory" errors. System-managed page files can grow to fill the disk.

Documented **Data sources**: `sourcetype=Perfmon:Paging_File` (counter: % Usage, % Usage Peak). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:Paging_File. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:Paging_File". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where pf_pct > 70` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

Understanding this CIM / accelerated SPL

**Page File Usage & Exhaustion** — Page file exhaustion prevents new process creation and causes "out of virtual memory" errors. System-managed page files can grow to fill the disk.

Documented **Data sources**: `sourcetype=Perfmon:Paging_File` (counter: % Usage, % Usage Peak). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where mem_pct > 95 OR swap_pct > 20` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (page file usage over time), Gauge (current usage), Table (hosts with high usage).

## SPL

```spl
index=perfmon sourcetype="Perfmon:Paging_File" counter="% Usage" instance="_Total"
| timechart span=15m avg(Value) as pf_pct by host
| where pf_pct > 70
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

## Visualization

Line chart (page file usage over time), Gauge (current usage), Table (hosts with high usage).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
