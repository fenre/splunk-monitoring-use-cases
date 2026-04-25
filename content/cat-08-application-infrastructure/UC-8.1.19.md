<!-- AUTO-GENERATED from UC-8.1.19.json — DO NOT EDIT -->

---
id: "8.1.19"
title: "Tomcat Access Log Response Time Percentiles"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.19 · Tomcat Access Log Response Time Percentiles

## Description

Tomcat access logs with `%D` or `time-taken` show end-to-end request duration. Rising P95 latency often precedes thread pool exhaustion and timeouts.

## Value

Teams catch Tomcat slowdowns before pools saturate and users see widespread timeouts.

## Implementation

Enable the AccessLogValve with elapsed time (`%D` microseconds or equivalent). Ingest with the Splunk Add-on for Tomcat. Normalize milliseconds at ingest or in SPL. Baseline P95 per application and seasonality.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Tomcat (Splunkbase app 2911).
• Ensure the following data sources are available: `index=web` `sourcetype=tomcat:access` (W3C or extended format with elapsed time).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Tomcat access logging including request duration; forward logs into Splunk with the Tomcat add-on; confirm the elapsed-time field is extracted as `time-taken` or map it to `elapsed_ms` in SPL.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="tomcat:access"
| eval elapsed_ms=coalesce('time-taken', time_taken, timetaken, duration_ms)
| where isnotnull(elapsed_ms) AND elapsed_ms>0
| timechart span=5m perc95(elapsed_ms) as p95_ms by host
| where p95_ms > 2000
```

Understanding this SPL

**Tomcat Access Log Response Time Percentiles** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=web` `sourcetype=tomcat:access` (W3C or extended format with elapsed time). **App/TA**: Splunk Add-on for Tomcat (Splunkbase app 2911). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Line chart (P95 elapsed ms), table (top slow hosts), single value (current P95 vs SLO)..

## SPL

```spl
index=web sourcetype="tomcat:access"
| eval elapsed_ms=coalesce('time-taken', time_taken, timetaken, duration_ms)
| where isnotnull(elapsed_ms) AND elapsed_ms>0
| timechart span=5m perc95(elapsed_ms) as p95_ms by host
| where p95_ms > 2000
```

## CIM SPL

```spl
| tstats `summariesonly` perc95(Web.duration) as p95_ms avg(Web.duration) as avg_ms
  from datamodel=Web.Web
  by Web.dest Web.uri_path span=5m
| where p95_ms > 0
```

## Visualization

Line chart (P95 elapsed ms), table (top slow hosts), single value (current P95 vs SLO).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Splunk Add-on for Tomcat (Splunkbase)](https://splunkbase.splunk.com/app/2911)
- [Apache Tomcat Access Log Valve](https://tomcat.apache.org/tomcat-10.0-doc/config/valve.html#Access_Log_Valve)
