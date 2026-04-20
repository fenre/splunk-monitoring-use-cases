---
id: "7.3.2"
title: "Automated Failover Events"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.3.2 · Automated Failover Events

## Description

Managed database failovers cause brief outages. Detection enables impact analysis and root cause investigation.

## Value

Managed database failovers cause brief outages. Detection enables impact analysis and root cause investigation.

## Implementation

Ingest RDS event subscriptions via SNS → SQS → Splunk. Filter for failover events. Alert immediately with PagerDuty/ServiceNow integration. Correlate with application error spikes to measure impact duration.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws` (CloudTrail/EventBridge), Azure Activity Log.
• Ensure the following data sources are available: RDS events, Azure SQL activity log, Cloud SQL admin activity.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest RDS event subscriptions via SNS → SQS → Splunk. Filter for failover events. Alert immediately with PagerDuty/ServiceNow integration. Correlate with application error spikes to measure impact duration.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch:events"
| search detail.EventCategories="failover"
| table _time, detail.SourceIdentifier, detail.Message
```

Understanding this SPL

**Automated Failover Events** — Managed database failovers cause brief outages. Detection enables impact analysis and root cause investigation.

Documented **Data sources**: RDS events, Azure SQL activity log, Cloud SQL admin activity. **App/TA** (typical add-on context): `Splunk_TA_aws` (CloudTrail/EventBridge), Azure Activity Log. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch:events. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Automated Failover Events**): table _time, detail.SourceIdentifier, detail.Message


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (failover events), Table (failover details), Single value (days since last failover).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch:events"
| search detail.EventCategories="failover"
| table _time, detail.SourceIdentifier, detail.Message
```

## Visualization

Timeline (failover events), Table (failover details), Single value (days since last failover).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
