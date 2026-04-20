---
id: "8.2.12"
title: "Tomcat JMX Thread Pool Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.12 · Tomcat JMX Thread Pool Utilization

## Description

Connector thread pool busy percentage and rejected connections indicate Tomcat capacity limits. Exhausted pools cause 503 errors and connection timeouts.

## Value

Connector thread pool busy percentage and rejected connections indicate Tomcat capacity limits. Exhausted pools cause 503 errors and connection timeouts.

## Implementation

Deploy Jolokia agent or Splunk JMX modular input on Tomcat. Configure polling for `Catalina:type=ThreadPool,name="http-nio-8080"` (adjust connector name per instance). Extract currentThreadsBusy, maxThreads, connectionCount (rejected). Poll every 5 minutes. Alert when pool_pct >80% or any rejected connections. Correlate with request rate and response time to distinguish traffic spikes from slow backends.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom JMX input (Jolokia, JMX modular input).
• Ensure the following data sources are available: JMX MBeans (`Catalina:type=ThreadPool,name="http-nio-8080"`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Jolokia agent or Splunk JMX modular input on Tomcat. Configure polling for `Catalina:type=ThreadPool,name="http-nio-8080"` (adjust connector name per instance). Extract currentThreadsBusy, maxThreads, connectionCount (rejected). Poll every 5 minutes. Alert when pool_pct >80% or any rejected connections. Correlate with request rate and response time to distinguish traffic spikes from slow backends.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=jmx sourcetype="jmx:tomcat:threadpool"
| eval pool_pct=round(currentThreadsBusy/maxThreads*100,1)
| where pool_pct > 80 OR connectionCount > 0
| timechart span=5m max(pool_pct) as busy_pct, sum(connectionCount) as rejected by host, connector_name
```

Understanding this SPL

**Tomcat JMX Thread Pool Utilization** — Connector thread pool busy percentage and rejected connections indicate Tomcat capacity limits. Exhausted pools cause 503 errors and connection timeouts.

Documented **Data sources**: JMX MBeans (`Catalina:type=ThreadPool,name="http-nio-8080"`). **App/TA** (typical add-on context): Custom JMX input (Jolokia, JMX modular input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: jmx; **sourcetype**: jmx:tomcat:threadpool. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=jmx, sourcetype="jmx:tomcat:threadpool". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pool_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pool_pct > 80 OR connectionCount > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host, connector_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (% threads busy), Line chart (thread utilization over time), Table (connectors with rejections), Single value (rejected connections).

## SPL

```spl
index=jmx sourcetype="jmx:tomcat:threadpool"
| eval pool_pct=round(currentThreadsBusy/maxThreads*100,1)
| where pool_pct > 80 OR connectionCount > 0
| timechart span=5m max(pool_pct) as busy_pct, sum(connectionCount) as rejected by host, connector_name
```

## Visualization

Gauge (% threads busy), Line chart (thread utilization over time), Table (connectors with rejections), Single value (rejected connections).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
