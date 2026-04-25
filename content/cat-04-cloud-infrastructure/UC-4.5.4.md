<!-- AUTO-GENERATED from UC-4.5.4.json — DO NOT EDIT -->

---
id: "4.5.4"
title: "Azure Functions Host and Worker Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.5.4 · Azure Functions Host and Worker Health

## Description

Host startup failures, platform updates, and worker crashes take entire function apps offline; early detection reduces MTTR for serverless workloads on Azure.

## Value

Host startup failures, platform updates, and worker crashes take entire function apps offline; early detection reduces MTTR for serverless workloads on Azure.

## Implementation

Stream Function App diagnostics (FunctionAppLogs) to Event Hub and ingest with the Microsoft Cloud Services add-on. Normalize `resourceName` (app name) and severity. Optionally join with `mscs:azure:metrics` for `Http5xx` or `FunctionExecutionCount` drops. Alert on sustained host-level errors or absence of successful executions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:diagnostics` (Function App logs), `sourcetype=mscs:azure:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Stream Function App diagnostics (FunctionAppLogs) to Event Hub and ingest with the Microsoft Cloud Services add-on. Normalize `resourceName` (app name) and severity. Optionally join with `mscs:azure:metrics` for `Http5xx` or `FunctionExecutionCount` drops. Alert on sustained host-level errors or absence of successful executions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="FunctionAppLogs" (level="Error" OR level="Critical")
| bin span=5m _time
| stats count as errors by resourceName, operationName, _time
| where errors > 0
```

Understanding this SPL

**Azure Functions Host and Worker Health** — Host startup failures, platform updates, and worker crashes take entire function apps offline; early detection reduces MTTR for serverless workloads on Azure.

Documented **Data sources**: `sourcetype=mscs:azure:diagnostics` (Function App logs), `sourcetype=mscs:azure:metrics`. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by resourceName, operationName, _time** so each row reflects one combination of those dimensions.
• Filters the current rows with `where errors > 0` — typically the threshold or rule expression for this monitoring goal.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure Functions Host and Worker Health** — Host startup failures, platform updates, and worker crashes take entire function apps offline; early detection reduces MTTR for serverless workloads on Azure.

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

**Azure Functions Host and Worker Health** — Host startup failures, platform updates, and worker crashes take entire function apps offline; early detection reduces MTTR for serverless workloads on Azure.

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

**Azure Functions Host and Worker Health** — Host startup failures, platform updates, and worker crashes take entire function apps offline; early detection reduces MTTR for serverless workloads on Azure.

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

**Azure Functions Host and Worker Health** — Host startup failures, platform updates, and worker crashes take entire function apps offline; early detection reduces MTTR for serverless workloads on Azure.

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

**Azure Functions Host and Worker Health** — Host startup failures, platform updates, and worker crashes take entire function apps offline; early detection reduces MTTR for serverless workloads on Azure.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (errors by app), Table (resourceName, message pattern, count), Status indicator (healthy/degraded per Function App).

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="FunctionAppLogs" (level="Error" OR level="Critical")
| bin span=5m _time
| stats count as errors by resourceName, operationName, _time
| where errors > 0
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Timeline (errors by app), Table (resourceName, message pattern, count), Status indicator (healthy/degraded per Function App).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
