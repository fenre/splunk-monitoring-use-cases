<!-- AUTO-GENERATED from UC-4.2.18.json — DO NOT EDIT -->

---
id: "4.2.18"
title: "Cosmos DB RU Consumption and Throttling"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.18 · Cosmos DB RU Consumption and Throttling

## Description

Throttling (429) occurs when RU consumption exceeds provisioned throughput. Monitoring supports right-sizing and autoscale tuning.

## Value

Throttling (429) occurs when RU consumption exceeds provisioned throughput. Monitoring supports right-sizing and autoscale tuning.

## Implementation

Collect Cosmos DB metrics. Alert when Http429 > 0 or RU consumption consistently near provisioned. Dashboard RU by operation type and partition. Consider autoscale for variable workload.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Azure Monitor Cosmos DB metrics (TotalRequestUnits, TotalRequests, Http429).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Cosmos DB metrics. Alert when Http429 > 0 or RU consumption consistently near provisioned. Dashboard RU by operation type and partition. Consider autoscale for variable workload.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:metrics" namespace="Microsoft.DocumentDB/databaseAccounts" metricName="TotalRequestUnits"
| timechart span=5m sum(total) by CollectionName
| eval ru_utilization_pct = TotalRequestUnits / provisioned_ru * 100
```

Understanding this SPL

**Cosmos DB RU Consumption and Throttling** — Throttling (429) occurs when RU consumption exceeds provisioned throughput. Monitoring supports right-sizing and autoscale tuning.

Documented **Data sources**: Azure Monitor Cosmos DB metrics (TotalRequestUnits, TotalRequests, Http429). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by CollectionName** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **ru_utilization_pct** — often to normalize units, derive a ratio, or prepare for thresholds.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Cosmos DB RU Consumption and Throttling** — Throttling (429) occurs when RU consumption exceeds provisioned throughput.

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

**Cosmos DB RU Consumption and Throttling** — Throttling (429) occurs when RU consumption exceeds provisioned throughput.

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

**Cosmos DB RU Consumption and Throttling** — Throttling (429) occurs when RU consumption exceeds provisioned throughput.

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

**Cosmos DB RU Consumption and Throttling** — Throttling (429) occurs when RU consumption exceeds provisioned throughput.

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

**Cosmos DB RU Consumption and Throttling** — Throttling (429) occurs when RU consumption exceeds provisioned throughput.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (RU, 429 by collection), Table (collection, RU, 429), Gauge (RU utilization %).

## SPL

```spl
index=azure sourcetype="mscs:azure:metrics" namespace="Microsoft.DocumentDB/databaseAccounts" metricName="TotalRequestUnits"
| timechart span=5m sum(total) by CollectionName
| eval ru_utilization_pct = TotalRequestUnits / provisioned_ru * 100
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Line chart (RU, 429 by collection), Table (collection, RU, 429), Gauge (RU utilization %).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
