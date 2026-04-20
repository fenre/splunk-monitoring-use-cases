---
id: "7.4.15"
title: "Azure Synapse Analytics SQL Pool Performance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.4.15 · Azure Synapse Analytics SQL Pool Performance

## Description

Synapse dedicated SQL pools have DWU-based resource limits. Queries competing for resources cause queueing, and tempdb contention degrades batch processing. Monitoring ensures analytics workloads meet SLAs.

## Value

Synapse dedicated SQL pools have DWU-based resource limits. Queries competing for resources cause queueing, and tempdb contention degrades batch processing. Monitoring ensures analytics workloads meet SLAs.

## Implementation

Collect Azure Monitor metrics for Synapse SQL pools. Alert when `DWUUsedPercent` exceeds 90% sustained (scale up DWU), when `QueuedQueries` exceeds 10 (resource contention), or when `AdaptiveCacheHitPercent` drops below 50% (cold cache after pause/resume). Enable diagnostics for `SqlRequests` to track query execution times and identify long-running queries consuming resources.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics).
• Ensure the following data sources are available: `sourcetype=azure:monitor:metric` (Microsoft.Synapse/workspaces/sqlPools), `sourcetype=azure:diagnostics` (SqlRequests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Azure Monitor metrics for Synapse SQL pools. Alert when `DWUUsedPercent` exceeds 90% sustained (scale up DWU), when `QueuedQueries` exceeds 10 (resource contention), or when `AdaptiveCacheHitPercent` drops below 50% (cold cache after pause/resume). Enable diagnostics for `SqlRequests` to track query execution times and identify long-running queries consuming resources.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.synapse/workspaces/sqlpools"
| where metric_name IN ("DWUUsedPercent","ActiveQueries","QueuedQueries","AdaptiveCacheHitPercent")
| timechart span=5m avg(average) as value by metric_name, resource_name
```

Understanding this SPL

**Azure Synapse Analytics SQL Pool Performance** — Synapse dedicated SQL pools have DWU-based resource limits. Queries competing for resources cause queueing, and tempdb contention degrades batch processing. Monitoring ensures analytics workloads meet SLAs.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.Synapse/workspaces/sqlPools), `sourcetype=azure:diagnostics` (SqlRequests). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:monitor:metric. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:monitor:metric". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where metric_name IN ("DWUUsedPercent","ActiveQueries","QueuedQueries","AdaptiveCacheHitPercent")` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by metric_name, resource_name** — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host span=5m | sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure Synapse Analytics SQL Pool Performance** — Synapse dedicated SQL pools have DWU-based resource limits. Queries competing for resources cause queueing, and tempdb contention degrades batch processing. Monitoring ensures analytics workloads meet SLAs.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.Synapse/workspaces/sqlPools), `sourcetype=azure:diagnostics` (SqlRequests). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance.CPU` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (DWU % and queued queries), Table (long-running queries), Gauge (cache hit ratio).

## SPL

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.synapse/workspaces/sqlpools"
| where metric_name IN ("DWUUsedPercent","ActiveQueries","QueuedQueries","AdaptiveCacheHitPercent")
| timechart span=5m avg(average) as value by metric_name, resource_name
```

## CIM SPL

```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host span=5m | sort - agg_value
```

## Visualization

Line chart (DWU % and queued queries), Table (long-running queries), Gauge (cache hit ratio).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
