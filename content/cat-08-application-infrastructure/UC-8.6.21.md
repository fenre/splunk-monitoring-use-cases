<!-- AUTO-GENERATED from UC-8.6.21.json — DO NOT EDIT -->

---
id: "8.6.21"
title: "Squid cache.log ERROR and FATAL Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.6.21 · Squid cache.log ERROR and FATAL Events

## Description

ERROR/FATAL lines capture disk I/O failures, rock store corruption, and TLS helper crashes.

## Value

Protects forward-proxy availability beyond access-log HTTP codes.

## Implementation

Ensure log rotation preserves file tail; escalate FATAL immediately.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Universal Forwarder on Squid host.
• Ensure the following data sources are available: `index=proxy` `sourcetype=squid:cache`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Pad spaces in search to reduce false positives or use `rex` for syslog severity.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=proxy sourcetype="squid:cache"
| search " ERROR " OR " FATAL "
| stats count by host
| sort -count
```

Understanding this SPL

**Squid cache.log ERROR and FATAL Events** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=proxy` `sourcetype=squid:cache`. **App/TA**: Universal Forwarder on Squid host. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Table (host), timeline, integration with disk SMART alerts..

## SPL

```spl
index=proxy sourcetype="squid:cache"
| search " ERROR " OR " FATAL "
| stats count by host
| sort -count
```

## Visualization

Table (host), timeline, integration with disk SMART alerts.

## References

- [Squid Configuration Manual — Access Log](http://www.squid-cache.org/Doc/config/access_log/)
