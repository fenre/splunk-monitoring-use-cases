---
id: "8.2.8"
title: ".NET CLR Performance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.8 · .NET CLR Performance

## Description

CLR performance issues (high GC, exceptions, thread starvation) directly impact .NET application performance. Monitoring guides runtime tuning.

## Value

CLR performance issues (high GC, exceptions, thread starvation) directly impact .NET application performance. Monitoring guides runtime tuning.

## Implementation

Configure Perfmon inputs for .NET CLR counters in `inputs.conf`. Monitor % Time in GC, Gen 2 collections, exception throw rate, and thread contention rate. Alert when GC time exceeds 10% or exception rate spikes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Perfmon), custom .NET metrics.
• Ensure the following data sources are available: Windows Performance Counters (.NET CLR Memory, Exceptions, Threading).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon inputs for .NET CLR counters in `inputs.conf`. Monitor % Time in GC, Gen 2 collections, exception throw rate, and thread contention rate. Alert when GC time exceeds 10% or exception rate spikes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:CLR_Memory"
| timechart span=5m avg(Pct_Time_in_GC) as gc_pct, avg(Gen_2_Collections) as gen2_gc by instance
| where gc_pct > 10
```

Understanding this SPL

**.NET CLR Performance** — CLR performance issues (high GC, exceptions, thread starvation) directly impact .NET application performance. Monitoring guides runtime tuning.

Documented **Data sources**: Windows Performance Counters (.NET CLR Memory, Exceptions, Threading). **App/TA** (typical add-on context): `Splunk_TA_windows` (Perfmon), custom .NET metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:CLR_Memory. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:CLR_Memory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by instance** — ideal for trending and alerting on this use case.
• Filters the current rows with `where gc_pct > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (GC % over time), Multi-metric chart (CLR counters), Table (instances with high GC).

## SPL

```spl
index=perfmon sourcetype="Perfmon:CLR_Memory"
| timechart span=5m avg(Pct_Time_in_GC) as gc_pct, avg(Gen_2_Collections) as gen2_gc by instance
| where gc_pct > 10
```

## Visualization

Line chart (GC % over time), Multi-metric chart (CLR counters), Table (instances with high GC).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
