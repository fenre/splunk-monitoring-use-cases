<!-- AUTO-GENERATED from UC-8.2.13.json — DO NOT EDIT -->

---
id: "8.2.13"
title: "WildFly / JBoss Datasource Pool Usage"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.13 · WildFly / JBoss Datasource Pool Usage

## Description

JMX datasource pool active/idle/wait connections indicate database connectivity health. Exhausted pools cause application errors and slow transactions.

## Value

JMX datasource pool active/idle/wait connections indicate database connectivity health. Exhausted pools cause application errors and slow transactions.

## Implementation

Deploy Jolokia on WildFly/JBoss. Poll `jboss.as:subsystem=datasources,data-source=*` for AvailableCount, InUseCount, WaitingCount, MaxUsedCount. Poll every 5 minutes. Alert when pool availability drops below 20% or WaitingCount >0 (indicating connection starvation). Track MaxUsedCount for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom JMX input (Jolokia).
• Ensure the following data sources are available: JMX MBeans (`jboss.as:subsystem=datasources,data-source=*`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Jolokia on WildFly/JBoss. Poll `jboss.as:subsystem=datasources,data-source=*` for AvailableCount, InUseCount, WaitingCount, MaxUsedCount. Poll every 5 minutes. Alert when pool availability drops below 20% or WaitingCount >0 (indicating connection starvation). Track MaxUsedCount for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=jmx sourcetype="jmx:wildfly:datasource"
| eval pool_pct=round(AvailableCount/(AvailableCount+InUseCount)*100,1), wait_pct=round(WaitingCount/(AvailableCount+InUseCount+WaitingCount)*100,1)
| where pool_pct < 20 OR WaitingCount > 0
| timechart span=5m max(pool_pct) as avail_pct, avg(WaitingCount) as waiting by host, data_source
```

Understanding this SPL

**WildFly / JBoss Datasource Pool Usage** — JMX datasource pool active/idle/wait connections indicate database connectivity health. Exhausted pools cause application errors and slow transactions.

Documented **Data sources**: JMX MBeans (`jboss.as:subsystem=datasources,data-source=*`). **App/TA** (typical add-on context): Custom JMX input (Jolokia). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: jmx; **sourcetype**: jmx:wildfly:datasource. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=jmx, sourcetype="jmx:wildfly:datasource". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pool_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pool_pct < 20 OR WaitingCount > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host, data_source** — ideal for trending and alerting on this use case.


Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (% pool available), Line chart (active vs idle over time), Table (datasources with waiting connections), Single value (total waiting).

## SPL

```spl
index=jmx sourcetype="jmx:wildfly:datasource"
| eval pool_pct=round(AvailableCount/(AvailableCount+InUseCount)*100,1), wait_pct=round(WaitingCount/(AvailableCount+InUseCount+WaitingCount)*100,1)
| where pool_pct < 20 OR WaitingCount > 0
| timechart span=5m max(pool_pct) as avail_pct, avg(WaitingCount) as waiting by host, data_source
```

## Visualization

Gauge (% pool available), Line chart (active vs idle over time), Table (datasources with waiting connections), Single value (total waiting).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
