<!-- AUTO-GENERATED from UC-4.2.28.json — DO NOT EDIT -->

---
id: "4.2.28"
title: "Azure App Service Plan CPU and Memory"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.28 · Azure App Service Plan CPU and Memory

## Description

Platform-level resource pressure on App Service plan (not app-level) causes throttling, slow responses, and out-of-memory errors across all apps in the plan.

## Value

Platform-level resource pressure on App Service plan (not app-level) causes throttling, slow responses, and out-of-memory errors across all apps in the plan.

## Implementation

Configure Azure Monitor diagnostic settings or metrics API to export App Service Plan metrics (CpuPercentage, MemoryPercentage) to Event Hub or storage. Ingest via Splunk_TA_microsoft-cloudservices. Alert when CPU or memory exceeds 80% for 5+ minutes. Scale up plan or optimize app code. Distinguish plan-level metrics from app-level (requests, response time).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Cloud Services.
• Ensure the following data sources are available: Azure Monitor metrics (CpuPercentage, MemoryPercentage for App Service Plan).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Azure Monitor diagnostic settings or metrics API to export App Service Plan metrics (CpuPercentage, MemoryPercentage) to Event Hub or storage. Ingest via Splunk_TA_microsoft-cloudservices. Alert when CPU or memory exceeds 80% for 5+ minutes. Scale up plan or optimize app code. Distinguish plan-level metrics from app-level (requests, response time).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:metrics" resourceType="Microsoft.Web/serverfarms" (metric_name="CpuPercentage" OR metric_name="MemoryPercentage")
| stats avg(average) as avg_pct by resourceId, metric_name, bin(_time, 5m)
| where avg_pct > 80
| eval avg_pct=round(avg_pct, 1)
| table _time resourceId metric_name avg_pct
| sort -avg_pct
```

Understanding this SPL

**Azure App Service Plan CPU and Memory** — Platform-level resource pressure on App Service plan (not app-level) causes throttling, slow responses, and out-of-memory errors across all apps in the plan.

Documented **Data sources**: Azure Monitor metrics (CpuPercentage, MemoryPercentage for App Service Plan). **App/TA** (typical add-on context): Splunk Add-on for Microsoft Cloud Services. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:metrics, Microsoft.Web/serverfarms. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resourceId, metric_name, bin(_time, 5m)** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **avg_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Azure App Service Plan CPU and Memory**): table _time resourceId metric_name avg_pct
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure App Service Plan CPU and Memory** — Platform-level resource pressure on App Service plan (not app-level) causes throttling, slow responses, and out-of-memory errors across all apps in the plan.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on accelerated data model the CPU-related Performance model — enable that model in Data Models and CIM add-ons, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure App Service Plan CPU and Memory** — Platform-level resource pressure on App Service plan (not app-level) causes throttling, slow responses, and out-of-memory errors across all apps in the plan.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure App Service Plan CPU and Memory** — Platform-level resource pressure on App Service plan (not app-level) causes throttling, slow responses, and out-of-memory errors across all apps in the plan.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure App Service Plan CPU and Memory** — Platform-level resource pressure on App Service plan (not app-level) causes throttling, slow responses, and out-of-memory errors across all apps in the plan.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure App Service Plan CPU and Memory** — Platform-level resource pressure on App Service plan (not app-level) causes throttling, slow responses, and out-of-memory errors across all apps in the plan.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (CPU and memory % by plan over time), Table (plan, metric, avg %), Gauge (current utilization).

## SPL

```spl
index=azure sourcetype="mscs:azure:metrics" resourceType="Microsoft.Web/serverfarms" (metric_name="CpuPercentage" OR metric_name="MemoryPercentage")
| stats avg(average) as avg_pct by resourceId, metric_name, bin(_time, 5m)
| where avg_pct > 80
| eval avg_pct=round(avg_pct, 1)
| table _time resourceId metric_name avg_pct
| sort -avg_pct
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Line chart (CPU and memory % by plan over time), Table (plan, metric, avg %), Gauge (current utilization).

## References

- [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
