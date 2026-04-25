<!-- AUTO-GENERATED from UC-4.2.33.json — DO NOT EDIT -->

---
id: "4.2.33"
title: "App Service Health Metrics"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.33 · App Service Health Metrics

## Description

HTTP queue length, response time, and instance health explain user-visible slowness before 5xx rates spike.

## Value

HTTP queue length, response time, and instance health explain user-visible slowness before 5xx rates spike.

## Implementation

Stream App Service metrics via diagnostic settings. Correlate with App Service Plan saturation (UC-4.2.28). Alert on sustained queue depth or failed health probes. Scale out or warm up instances.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:metrics` (Microsoft.Web/sites — HttpQueueLength, AverageResponseTime, HealthCheckStatus).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Stream App Service metrics via diagnostic settings. Correlate with App Service Plan saturation (UC-4.2.28). Alert on sustained queue depth or failed health probes. Scale out or warm up instances.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:metrics" resourceType="Microsoft.Web/sites" (metric_name="HttpQueueLength" OR metric_name="AverageResponseTime" OR metric_name="HealthCheckStatus")
| stats avg(average) as v by resourceId, metric_name, bin(_time, 5m)
| where (metric_name="HttpQueueLength" AND v>100) OR (metric_name="AverageResponseTime" AND v>2000) OR (metric_name="HealthCheckStatus" AND v>0)
```

Understanding this SPL

**App Service Health Metrics** — HTTP queue length, response time, and instance health explain user-visible slowness before 5xx rates spike.

Documented **Data sources**: `sourcetype=mscs:azure:metrics` (Microsoft.Web/sites — HttpQueueLength, AverageResponseTime, HealthCheckStatus). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:metrics, Microsoft.Web/sites. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resourceId, metric_name, bin(_time, 5m)** so each row reflects one combination of those dimensions.
• Filters the current rows with `where (metric_name="HttpQueueLength" AND v>100) OR (metric_name="AverageResponseTime" AND v>2000) OR (metric_name="HealthCh…` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**App Service Health Metrics** — HTTP queue length, response time, and instance health explain user-visible slowness before 5xx rates spike.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (queue, response time, health), Table (app, metric, value), Status grid (probe per slot).

## SPL

```spl
index=azure sourcetype="mscs:azure:metrics" resourceType="Microsoft.Web/sites" (metric_name="HttpQueueLength" OR metric_name="AverageResponseTime" OR metric_name="HealthCheckStatus")
| stats avg(average) as v by resourceId, metric_name, bin(_time, 5m)
| where (metric_name="HttpQueueLength" AND v>100) OR (metric_name="AverageResponseTime" AND v>2000) OR (metric_name="HealthCheckStatus" AND v>0)
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Line chart (queue, response time, health), Table (app, metric, value), Status grid (probe per slot).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
