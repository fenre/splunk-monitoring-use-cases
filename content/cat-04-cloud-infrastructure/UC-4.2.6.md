---
id: "4.2.6"
title: "Azure SQL Performance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.6 · Azure SQL Performance

## Description

DTU/vCore exhaustion causes query throttling. Deadlocks and long-running queries impact application performance directly.

## Value

DTU/vCore exhaustion causes query throttling. Deadlocks and long-running queries impact application performance directly.

## Implementation

Enable Azure SQL diagnostic logging to Event Hub. Collect SQL Insights, Deadlocks, and QueryStoreRuntimeStatistics categories. Alert on DTU >90%, deadlock events, and query duration outliers.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:diagnostics` (SQL diagnostics).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Azure SQL diagnostic logging to Event Hub. Collect SQL Insights, Deadlocks, and QueryStoreRuntimeStatistics categories. Alert on DTU >90%, deadlock events, and query duration outliers.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="SQLInsights" OR Category="Deadlocks"
| stats count by database_name, Category
| sort -count
```

Understanding this SPL

**Azure SQL Performance** — DTU/vCore exhaustion causes query throttling. Deadlocks and long-running queries impact application performance directly.

Documented **Data sources**: `sourcetype=mscs:azure:diagnostics` (SQL diagnostics). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by database_name, Category** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (DTU usage), Table (deadlocks), Bar chart (top slow queries).

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="SQLInsights" OR Category="Deadlocks"
| stats count by database_name, Category
| sort -count
```

## Visualization

Line chart (DTU usage), Table (deadlocks), Bar chart (top slow queries).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
