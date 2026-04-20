---
id: "7.3.5"
title: "Maintenance Window Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.3.5 · Maintenance Window Tracking

## Description

Awareness of upcoming and completed maintenance ensures teams are prepared for potential service impact.

## Value

Awareness of upcoming and completed maintenance ensures teams are prepared for potential service impact.

## Implementation

Subscribe to RDS maintenance events via SNS. Ingest into Splunk. Create calendar view of upcoming maintenance. Alert 72 hours before scheduled maintenance. Log actual impact duration after completion.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cloud provider TAs.
• Ensure the following data sources are available: RDS event subscriptions, Azure Service Health, GCP maintenance notifications.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Subscribe to RDS maintenance events via SNS. Ingest into Splunk. Create calendar view of upcoming maintenance. Alert 72 hours before scheduled maintenance. Log actual impact duration after completion.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch:events"
| search detail.EventCategories="maintenance"
| table _time, detail.SourceIdentifier, detail.Message, detail.Date
| sort detail.Date
```

Understanding this SPL

**Maintenance Window Tracking** — Awareness of upcoming and completed maintenance ensures teams are prepared for potential service impact.

Documented **Data sources**: RDS event subscriptions, Azure Service Health, GCP maintenance notifications. **App/TA** (typical add-on context): Cloud provider TAs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch:events. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Maintenance Window Tracking**): table _time, detail.SourceIdentifier, detail.Message, detail.Date
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (upcoming/recent maintenance), Calendar view, Timeline (maintenance history).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch:events"
| search detail.EventCategories="maintenance"
| table _time, detail.SourceIdentifier, detail.Message, detail.Date
| sort detail.Date
```

## Visualization

Table (upcoming/recent maintenance), Calendar view, Timeline (maintenance history).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
