<!-- AUTO-GENERATED from UC-8.6.24.json — DO NOT EDIT -->

---
id: "8.6.24"
title: "HAProxy Alert and Emergency Syslog Messages"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.6.24 · HAProxy Alert and Emergency Syslog Messages

## Description

HAProxy emits ALERT/EMERG for proxy, stick-table, and peersync failures requiring immediate operator action.

## Value

Captures conditions not visible in HTTP access logs.

## Implementation

Forward syslog with high integrity; include program name `haproxy`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: HAProxy `log` targets with alert routing.
• Ensure the following data sources are available: `index=proxy` syslog `sourcetype=haproxy:syslog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Phrase match syslog format; some distros lowercase severity.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=proxy sourcetype="haproxy:syslog"
| search "[ALERT]" OR "[EMERG]" OR "fatal"
| table _time, host, _raw
| sort -_time
```

Understanding this SPL

**HAProxy Alert and Emergency Syslog Messages** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=proxy` syslog `sourcetype=haproxy:syslog`. **App/TA**: HAProxy `log` targets with alert routing. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Real-time alert feed, Slack/webhook integration..

## SPL

```spl
index=proxy sourcetype="haproxy:syslog"
| search "[ALERT]" OR "[EMERG]" OR "fatal"
| table _time, host, _raw
| sort -_time
```

## Visualization

Real-time alert feed, Slack/webhook integration.

## References

- [HAProxy Management Guide — Logging](https://www.haproxy.com/documentation/haproxy-management-guide/latest/observability/logging/)
