---
id: "8.2.3"
title: "Thread Pool Exhaustion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.3 · Thread Pool Exhaustion

## Description

Exhausted thread pools cause request rejection and application unresponsiveness. Detection prevents complete service failure.

## Value

Exhausted thread pools cause request rejection and application unresponsiveness. Detection prevents complete service failure.

## Implementation

Poll thread pool metrics via JMX (Tomcat: Connector MBeans, WildFly: undertow subsystem). Alert at 80% thread pool utilization. Correlate with request rate and response time to distinguish traffic spikes from slow backends.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-jmx`, application metrics.
• Ensure the following data sources are available: JMX thread MBeans, Tomcat Connector metrics, application metrics endpoints.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll thread pool metrics via JMX (Tomcat: Connector MBeans, WildFly: undertow subsystem). Alert at 80% thread pool utilization. Correlate with request rate and response time to distinguish traffic spikes from slow backends.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=jmx sourcetype="jmx:threading"
| eval pct_used=round(currentThreadsBusy/maxThreads*100,1)
| timechart span=5m max(pct_used) as thread_pct by host
| where thread_pct > 80
```

Understanding this SPL

**Thread Pool Exhaustion** — Exhausted thread pools cause request rejection and application unresponsiveness. Detection prevents complete service failure.

Documented **Data sources**: JMX thread MBeans, Tomcat Connector metrics, application metrics endpoints. **App/TA** (typical add-on context): `TA-jmx`, application metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: jmx; **sourcetype**: jmx:threading. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=jmx, sourcetype="jmx:threading". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pct_used** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where thread_pct > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (% threads busy), Line chart (thread utilization over time), Table (servers approaching capacity).

## SPL

```spl
index=jmx sourcetype="jmx:threading"
| eval pct_used=round(currentThreadsBusy/maxThreads*100,1)
| timechart span=5m max(pct_used) as thread_pct by host
| where thread_pct > 80
```

## Visualization

Gauge (% threads busy), Line chart (thread utilization over time), Table (servers approaching capacity).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
