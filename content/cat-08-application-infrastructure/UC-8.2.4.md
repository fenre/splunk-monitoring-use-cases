---
id: "8.2.4"
title: "Application Error Rate"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.4 · Application Error Rate

## Description

Application exceptions indicate bugs, integration failures, or environmental issues. Tracking error rate by type guides debugging priority.

## Value

Application exceptions indicate bugs, integration failures, or environmental issues. Tracking error rate by type guides debugging priority.

## Implementation

Forward application logs via UF. Ensure structured logging (JSON preferred) for reliable field extraction. Classify errors by type/exception. Alert on error rate spikes above baseline. Create error type breakdown for developer triage.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom log input, application framework logging.
• Ensure the following data sources are available: Application log files (log4j, logback, NLog, Serilog).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward application logs via UF. Ensure structured logging (JSON preferred) for reliable field extraction. Classify errors by type/exception. Alert on error rate spikes above baseline. Create error type breakdown for developer triage.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="log4j" log_level=ERROR
| timechart span=5m count as error_count by host
| predict error_count as predicted
```

Understanding this SPL

**Application Error Rate** — Application exceptions indicate bugs, integration failures, or environmental issues. Tracking error rate by type guides debugging priority.

Documented **Data sources**: Application log files (log4j, logback, NLog, Serilog). **App/TA** (typical add-on context): Custom log input, application framework logging. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: application; **sourcetype**: log4j. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=application, sourcetype="log4j". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Pipeline stage (see **Application Error Rate**): predict error_count as predicted


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (error rate with baseline), Table (top error types), Bar chart (errors by component).

## SPL

```spl
index=application sourcetype="log4j" log_level=ERROR
| timechart span=5m count as error_count by host
| predict error_count as predicted
```

## Visualization

Line chart (error rate with baseline), Table (top error types), Bar chart (errors by component).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
