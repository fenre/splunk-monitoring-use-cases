---
id: "8.2.18"
title: "Tomcat Active Session Count"
criticality: "medium"
splunkPillar: "Security"
---

# UC-8.2.18 · Tomcat Active Session Count

## Description

Session explosion may indicate bot traffic, session fixation abuse, or missing session TTL. Per-context session counts from JMX.

## Value

Session explosion may indicate bot traffic, session fixation abuse, or missing session TTL. Per-context session counts from JMX.

## Implementation

Baseline sessions per context. Alert on 3× baseline or absolute cap. Correlate with marketing events or attacks.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-jmx`.
• Ensure the following data sources are available: `Catalina:type=Manager` `activeSessions`, `sessionMaxAliveTime`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline sessions per context. Alert on 3× baseline or absolute cap. Correlate with marketing events or attacks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=jmx sourcetype="jmx:tomcat:manager"
| timechart span=15m max(activeSessions) as sessions by host, context_path
| eventstats avg(sessions) as baseline by context_path
| where sessions > baseline * 3 AND sessions > 5000
```

Understanding this SPL

**Tomcat Active Session Count** — Session explosion may indicate bot traffic, session fixation abuse, or missing session TTL. Per-context session counts from JMX.

Documented **Data sources**: `Catalina:type=Manager` `activeSessions`, `sessionMaxAliveTime`. **App/TA** (typical add-on context): `TA-jmx`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: jmx; **sourcetype**: jmx:tomcat:manager. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=jmx, sourcetype="jmx:tomcat:manager". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by host, context_path** — ideal for trending and alerting on this use case.
• `eventstats` rolls up events into metrics; results are split **by context_path** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where sessions > baseline * 3 AND sessions > 5000` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (sessions over time), Table (context, sessions), Single value (peak sessions).

## SPL

```spl
index=jmx sourcetype="jmx:tomcat:manager"
| timechart span=15m max(activeSessions) as sessions by host, context_path
| eventstats avg(sessions) as baseline by context_path
| where sessions > baseline * 3 AND sessions > 5000
```

## Visualization

Line chart (sessions over time), Table (context, sessions), Single value (peak sessions).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
