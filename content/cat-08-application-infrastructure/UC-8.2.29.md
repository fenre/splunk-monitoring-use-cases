<!-- AUTO-GENERATED from UC-8.2.29.json — DO NOT EDIT -->

---
id: "8.2.29"
title: "Tomcat AJP and Connector Protocol Errors"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.29 · Tomcat AJP and Connector Protocol Errors

## Description

AJP misconfiguration between httpd and Tomcat, packet loss, or stuck workers surface as protocol errors in catalina.out before user-visible 502s.

## Value

Speeds isolation of reverse-proxy integration failures.

## Implementation

Ingest catalina logs with timestamps; create `signature` via `cluster` or truncate message. Exclude known maintenance windows.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Tomcat (Splunkbase app 2911).
• Ensure the following data sources are available: `index=application` `sourcetype=tomcat:catalina`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Adjust keywords for your connector (AJP vs HTTP/2); test on historical incidents.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="tomcat:catalina"
| search ("AJP" AND ("IOException" OR "refused" OR "Unexpected")) OR "Protocol handler pause" OR "Failed to complete processing of a request"
| stats count by host, signature
| sort -count
```

Understanding this SPL

**Tomcat AJP and Connector Protocol Errors** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=application` `sourcetype=tomcat:catalina`. **App/TA**: Splunk Add-on for Tomcat (Splunkbase app 2911). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Table (message signatures), timeline, link to mod_jk/worker configs..

## SPL

```spl
index=application sourcetype="tomcat:catalina"
| search ("AJP" AND ("IOException" OR "refused" OR "Unexpected")) OR "Protocol handler pause" OR "Failed to complete processing of a request"
| stats count by host, signature
| sort -count
```

## Visualization

Table (message signatures), timeline, link to mod_jk/worker configs.

## References

- [Splunk Add-on for Tomcat (Splunkbase)](https://splunkbase.splunk.com/app/2911)
- [Apache Tomcat Access Log Valve](https://tomcat.apache.org/tomcat-10.0-doc/config/valve.html#Access_Log_Valve)
