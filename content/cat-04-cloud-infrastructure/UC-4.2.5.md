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

## Visualization

Line chart per VM, Heatmap, Gauge.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
