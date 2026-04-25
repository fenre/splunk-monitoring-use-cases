<!-- AUTO-GENERATED from UC-4.2.13.json — DO NOT EDIT -->

---
id: "4.2.13"
title: "App Service (Web App) HTTP 5xx and Slot Swap"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.13 · App Service (Web App) HTTP 5xx and Slot Swap

## Description

App Service 5xx and failed slot swaps impact user experience and deployment safety. Monitoring supports reliability and blue-green deployment.

## Value

App Service 5xx and failed slot swaps impact user experience and deployment safety. Monitoring supports reliability and blue-green deployment.

## Implementation

Collect App Service metrics. Alert on Http5xx rate >1%. Monitor slot swap operations in Activity Log; alert on swap failure. Track response time and memory usage for capacity.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Azure Monitor metrics (Http5xx, ResponseTime), Activity Log (Slot swap).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect App Service metrics. Alert on Http5xx rate >1%. Monitor slot swap operations in Activity Log; alert on swap failure. Track response time and memory usage for capacity.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:metrics" metricName="Http5xx" namespace="Microsoft.Web/sites"
| where average > 0
| timechart span=5m sum(total) by resourceId
```

Understanding this SPL

**App Service (Web App) HTTP 5xx and Slot Swap** — App Service 5xx and failed slot swaps impact user experience and deployment safety. Monitoring supports reliability and blue-green deployment.

Documented **Data sources**: Azure Monitor metrics (Http5xx, ResponseTime), Activity Log (Slot swap). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where average > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by resourceId** — ideal for trending and alerting on this use case.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**App Service (Web App) HTTP 5xx and Slot Swap** — App Service 5xx and failed slot swaps impact user experience and deployment safety.

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

**App Service (Web App) HTTP 5xx and Slot Swap** — App Service 5xx and failed slot swaps impact user experience and deployment safety.

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

**App Service (Web App) HTTP 5xx and Slot Swap** — App Service 5xx and failed slot swaps impact user experience and deployment safety.

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

**App Service (Web App) HTTP 5xx and Slot Swap** — App Service 5xx and failed slot swaps impact user experience and deployment safety.

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

**App Service (Web App) HTTP 5xx and Slot Swap** — App Service 5xx and failed slot swaps impact user experience and deployment safety.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (5xx, response time by app), Table (app, 5xx count), Timeline (slot swaps).

## SPL

```spl
index=azure sourcetype="mscs:azure:metrics" metricName="Http5xx" namespace="Microsoft.Web/sites"
| where average > 0
| timechart span=5m sum(total) by resourceId
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Line chart (5xx, response time by app), Table (app, 5xx count), Timeline (slot swaps).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
