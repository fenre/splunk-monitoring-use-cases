---
id: "8.2.7"
title: "Session Count Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.2.7 · Session Count Trending

## Description

Active session counts indicate concurrent user load. Trending supports capacity planning and license management.

## Value

Active session counts indicate concurrent user load. Trending supports capacity planning and license management.

## Implementation

Poll session manager MBeans via JMX. Track active sessions per server. Correlate with user authentication events for validation. Use `predict` for capacity forecasting.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-jmx`, application metrics.
• Ensure the following data sources are available: JMX session MBeans, application metrics endpoints.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll session manager MBeans via JMX. Track active sessions per server. Correlate with user authentication events for validation. Use `predict` for capacity forecasting.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=jmx sourcetype="jmx:manager"
| timechart span=15m max(activeSessions) as sessions by host
| predict sessions as predicted future_timespan=7
```

Understanding this SPL

**Session Count Trending** — Active session counts indicate concurrent user load. Trending supports capacity planning and license management.

Documented **Data sources**: JMX session MBeans, application metrics endpoints. **App/TA** (typical add-on context): `TA-jmx`, application metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: jmx; **sourcetype**: jmx:manager. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=jmx, sourcetype="jmx:manager". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Pipeline stage (see **Session Count Trending**): predict sessions as predicted future_timespan=7


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (session count with prediction), Single value (current active sessions), Area chart (sessions over time).

## SPL

```spl
index=jmx sourcetype="jmx:manager"
| timechart span=15m max(activeSessions) as sessions by host
| predict sessions as predicted future_timespan=7
```

## Visualization

Line chart (session count with prediction), Single value (current active sessions), Area chart (sessions over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
