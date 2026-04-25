<!-- AUTO-GENERATED from UC-4.2.5.json — DO NOT EDIT -->

---
id: "4.2.5"
title: "Azure VM Performance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.2.5 · Azure VM Performance

## Description

Azure Monitor metrics provide VM performance data without agents. Essential for capacity planning and correlating with application issues.

## Value

Azure Monitor metrics provide VM performance data without agents. Essential for capacity planning and correlating with application issues.

## Implementation

Configure Azure Monitor metrics collection in the Splunk TA. Collect CPU, memory, disk, and network metrics. Alert on sustained high utilization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Azure Monitor metrics collection in the Splunk TA. Collect CPU, memory, disk, and network metrics. Alert on sustained high utilization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:metrics" metricName="Percentage CPU"
| timechart span=1h avg(average) as avg_cpu by resourceId
| where avg_cpu > 80
```

Understanding this SPL

**Azure VM Performance** — Azure Monitor metrics provide VM performance data without agents. Essential for capacity planning and correlating with application issues.

Documented **Data sources**: `sourcetype=mscs:azure:metrics`. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by resourceId** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_cpu > 80` — typically the threshold or rule expression for this monitoring goal.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure VM Performance** — Azure Monitor metrics provide VM performance data without agents.

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

**Azure VM Performance** — Azure Monitor metrics provide VM performance data without agents.

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

**Azure VM Performance** — Azure Monitor metrics provide VM performance data without agents.

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

**Azure VM Performance** — Azure Monitor metrics provide VM performance data without agents.

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

**Azure VM Performance** — Azure Monitor metrics provide VM performance data without agents.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart per VM, Heatmap, Gauge.

## SPL

```spl
index=azure sourcetype="mscs:azure:metrics" metricName="Percentage CPU"
| timechart span=1h avg(average) as avg_cpu by resourceId
| where avg_cpu > 80
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Line chart per VM, Heatmap, Gauge.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
