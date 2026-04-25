<!-- AUTO-GENERATED from UC-8.4.22.json — DO NOT EDIT -->

---
id: "8.4.22"
title: "Tomcat Connector Connection Count Versus maxConnections"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.22 · Tomcat Connector Connection Count Versus maxConnections

## Description

Tomcat’s `connectionCount` against `maxConnections` shows accept-queue pressure distinct from busy worker threads.

## Value

Explains errors when threads are idle yet clients cannot connect.

## Implementation

Poll `Catalina:type=ThreadPool` and `ProtocolHandler` attributes per connector; names vary (`http-nio-8080`).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for JMX + Tomcat Connector MBean polling.
• Ensure the following data sources are available: `index=jmx` `sourcetype=jmx:tomcat:threadpool` (`connectionCount`, `maxConnections`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
If your Jolokia map omits `maxConnections`, add it via transforms or lookup from server.xml.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=jmx sourcetype="jmx:tomcat:threadpool"
| eval cx_pct=if(maxConnections>0, round(100*connectionCount/maxConnections,1), null())
| where cx_pct > 85
| timechart span=5m max(cx_pct) as conn_util by host, connector_name
```

Understanding this SPL

**Tomcat Connector Connection Count Versus maxConnections** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=jmx` `sourcetype=jmx:tomcat:threadpool` (`connectionCount`, `maxConnections`). **App/TA**: Splunk Add-on for JMX + Tomcat Connector MBean polling. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Line chart (utilization), combine with UC-8.2.12 thread busy metrics..

## SPL

```spl
index=jmx sourcetype="jmx:tomcat:threadpool"
| eval cx_pct=if(maxConnections>0, round(100*connectionCount/maxConnections,1), null())
| where cx_pct > 85
| timechart span=5m max(cx_pct) as conn_util by host, connector_name
```

## Visualization

Line chart (utilization), combine with UC-8.2.12 thread busy metrics.

## References

- [Splunk Add-on for Tomcat (Splunkbase)](https://splunkbase.splunk.com/app/2911)
- [Splunk Add-on for Java Management Extensions (Splunkbase)](https://splunkbase.splunk.com/app/2647)
