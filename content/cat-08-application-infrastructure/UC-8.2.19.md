---
id: "8.2.19"
title: "WebLogic Stuck Threads"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.19 · WebLogic Stuck Threads

## Description

Stuck thread count >0 blocks request processing and triggers health check failures. Server log `BEA-000337` patterns.

## Value

Stuck thread count >0 blocks request processing and triggers health check failures. Server log `BEA-000337` patterns.

## Implementation

Forward stdout/stderr and domain logs. Alert on first stuck thread. Thread dump automation on critical domains.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: WebLogic Server logs, JMX.
• Ensure the following data sources are available: `weblogic:server` log, `StuckThreadCount` MBean.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward stdout/stderr and domain logs. Alert on first stuck thread. Thread dump automation on critical domains.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="weblogic:server"
| search "BEA-000337" OR "STUCK" OR stuck_thread_count>0
| stats count by domain, server_name, thread_name
| where count > 0
```

Understanding this SPL

**WebLogic Stuck Threads** — Stuck thread count >0 blocks request processing and triggers health check failures. Server log `BEA-000337` patterns.

Documented **Data sources**: `weblogic:server` log, `StuckThreadCount` MBean. **App/TA** (typical add-on context): WebLogic Server logs, JMX. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: application; **sourcetype**: weblogic:server. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=application, sourcetype="weblogic:server". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by domain, server_name, thread_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (domain, server, stuck count), Timeline (stuck events), Single value (stuck threads now).

## SPL

```spl
index=application sourcetype="weblogic:server"
| search "BEA-000337" OR "STUCK" OR stuck_thread_count>0
| stats count by domain, server_name, thread_name
| where count > 0
```

## Visualization

Table (domain, server, stuck count), Timeline (stuck events), Single value (stuck threads now).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
