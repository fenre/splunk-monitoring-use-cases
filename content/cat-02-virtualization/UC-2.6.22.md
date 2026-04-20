---
id: "2.6.22"
title: "Per-Application CPU and Memory Consumption"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.22 · Per-Application CPU and Memory Consumption

## Description

Identifying which applications consume the most CPU and memory on shared VDAs is essential for capacity planning and noisy-neighbour detection. A single user running an unoptimised macro or media-heavy application can degrade performance for all other sessions on the same VDA. uberAgent provides per-process, per-user resource consumption with application-level attribution.

## Value

Identifying which applications consume the most CPU and memory on shared VDAs is essential for capacity planning and noisy-neighbour detection. A single user running an unoptimised macro or media-heavy application can degrade performance for all other sessions on the same VDA. uberAgent provides per-process, per-user resource consumption with application-level attribution.

## Implementation

uberAgent collects process-level resource metrics continuously. Identify top resource consumers per VDA and per user. Alert when a single user's process exceeds thresholds that impact co-hosted sessions. Feed into capacity planning: if average RAM per user session is 2 GB and VDAs have 64 GB, the safe session density is ~28 sessions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448).
• Ensure the following data sources are available: `sourcetype="uberAgent:Process:ProcessDetail"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
uberAgent collects process-level resource metrics continuously. Identify top resource consumers per VDA and per user. Alert when a single user's process exceeds thresholds that impact co-hosted sessions. Feed into capacity planning: if average RAM per user session is 2 GB and VDAs have 64 GB, the safe session density is ~28 sessions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=uberagent sourcetype="uberAgent:Process:ProcessDetail" earliest=-4h
| stats avg(ProcCPUPercent) as avg_cpu avg(WorkingSetMB) as avg_ram_mb by AppName, User, Host
| where avg_cpu > 25 OR avg_ram_mb > 500
| sort -avg_cpu
| table Host, User, AppName, avg_cpu, avg_ram_mb
```

Understanding this SPL

**Per-Application CPU and Memory Consumption** — Identifying which applications consume the most CPU and memory on shared VDAs is essential for capacity planning and noisy-neighbour detection. A single user running an unoptimised macro or media-heavy application can degrade performance for all other sessions on the same VDA. uberAgent provides per-process, per-user resource consumption with application-level attribution.

Documented **Data sources**: `sourcetype="uberAgent:Process:ProcessDetail"`. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: uberagent; **sourcetype**: uberAgent:Process:ProcessDetail. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=uberagent, sourcetype="uberAgent:Process:ProcessDetail", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by AppName, User, Host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_cpu > 25 OR avg_ram_mb > 500` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Per-Application CPU and Memory Consumption**): table Host, User, AppName, avg_cpu, avg_ram_mb

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host | sort - agg_value
```

Understanding this CIM / accelerated SPL

**Per-Application CPU and Memory Consumption** — Identifying which applications consume the most CPU and memory on shared VDAs is essential for capacity planning and noisy-neighbour detection. A single user running an unoptimised macro or media-heavy application can degrade performance for all other sessions on the same VDA. uberAgent provides per-process, per-user resource consumption with application-level attribution.

Documented **Data sources**: `sourcetype="uberAgent:Process:ProcessDetail"`. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance.CPU` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (top consumers), Bar chart (CPU by application), Heatmap (user x VDA).

## SPL

```spl
index=uberagent sourcetype="uberAgent:Process:ProcessDetail" earliest=-4h
| stats avg(ProcCPUPercent) as avg_cpu avg(WorkingSetMB) as avg_ram_mb by AppName, User, Host
| where avg_cpu > 25 OR avg_ram_mb > 500
| sort -avg_cpu
| table Host, User, AppName, avg_cpu, avg_ram_mb
```

## CIM SPL

```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host | sort - agg_value
```

## Visualization

Table (top consumers), Bar chart (CPU by application), Heatmap (user x VDA).

## References

- [uberAgent UXM](https://splunkbase.splunk.com/app/1448)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
