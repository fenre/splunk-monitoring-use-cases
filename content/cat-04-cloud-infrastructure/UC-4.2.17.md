---
id: "4.2.17"
title: "Service Bus Queue Message Count and Dead Letter"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.17 · Service Bus Queue Message Count and Dead Letter

## Description

Growing queue or dead-letter count indicates consumers falling behind or message processing failures. Prevents backlog and lost messages.

## Value

Growing queue or dead-letter count indicates consumers falling behind or message processing failures. Prevents backlog and lost messages.

## Implementation

Collect Service Bus metrics per queue/topic. Alert when ActiveMessageCount exceeds threshold or DeadletterMessageCount > 0. Monitor message age via custom metric or run history if available.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Azure Monitor metrics (ActiveMessageCount, DeadletterMessageCount).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Service Bus metrics per queue/topic. Alert when ActiveMessageCount exceeds threshold or DeadletterMessageCount > 0. Monitor message age via custom metric or run history if available.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:metrics" namespace="Microsoft.ServiceBus/namespaces" metricName="ActiveMessageCount"
| bin _time span=5m
| stats avg(average) as active_messages by _time, EntityName
| where active_messages > 1000
```

Understanding this SPL

**Service Bus Queue Message Count and Dead Letter** — Growing queue or dead-letter count indicates consumers falling behind or message processing failures. Prevents backlog and lost messages.

Documented **Data sources**: Azure Monitor metrics (ActiveMessageCount, DeadletterMessageCount). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, EntityName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where active_messages > 1000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (message count, dead letter by queue), Table (queue, active, dead letter), Single value.

## SPL

```spl
index=azure sourcetype="mscs:azure:metrics" namespace="Microsoft.ServiceBus/namespaces" metricName="ActiveMessageCount"
| bin _time span=5m
| stats avg(average) as active_messages by _time, EntityName
| where active_messages > 1000
```

## Visualization

Line chart (message count, dead letter by queue), Table (queue, active, dead letter), Single value.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
