<!-- AUTO-GENERATED from UC-8.2.15.json — DO NOT EDIT -->

---
id: "8.2.15"
title: ".NET CLR Memory Pressure"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.15 · .NET CLR Memory Pressure

## Description

`# Bytes in all Heaps`, `LOH` size, and `% Time in GC` together indicate memory pressure vs high allocation rate. Refines UC-8.2.8.

## Value

`# Bytes in all Heaps`, `LOH` size, and `% Time in GC` together indicate memory pressure vs high allocation rate. Refines UC-8.2.8.

## Implementation

Collect every 1m for critical apps. Alert when GC time >15% and Gen 2 heap grows week-over-week. Trigger dump analysis workflow.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` Perfmon.
• Ensure the following data sources are available: `.NET CLR Memory`, `.NET Memory Cache`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect every 1m for critical apps. Alert when GC time >15% and Gen 2 heap grows week-over-week. Trigger dump analysis workflow.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:CLR_Memory"
| timechart span=5m avg(Gen_2_heap_size) as gen2_bytes, avg(Pct_Time_in_GC) as gc_pct by instance
| where gc_pct > 15
```

Understanding this SPL

**.NET CLR Memory Pressure** — `# Bytes in all Heaps`, `LOH` size, and `% Time in GC` together indicate memory pressure vs high allocation rate. Refines UC-8.2.8.

Documented **Data sources**: `.NET CLR Memory`, `.NET Memory Cache`. **App/TA** (typical add-on context): `Splunk_TA_windows` Perfmon. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:CLR_Memory. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:CLR_Memory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by instance** — ideal for trending and alerting on this use case.
• Filters the current rows with `where gc_pct > 15` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Dual-axis (heap vs GC %), Line chart (Gen 2 size), Table (instances over threshold).

## SPL

```spl
index=perfmon sourcetype="Perfmon:CLR_Memory"
| timechart span=5m avg(Gen_2_heap_size) as gen2_bytes, avg(Pct_Time_in_GC) as gc_pct by instance
| where gc_pct > 15
```

## Visualization

Dual-axis (heap vs GC %), Line chart (Gen 2 size), Table (instances over threshold).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
