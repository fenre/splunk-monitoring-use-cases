<!-- AUTO-GENERATED from UC-8.6.20.json — DO NOT EDIT -->

---
id: "8.6.20"
title: "Tomcat Catalina SEVERE Log Storms"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.6.20 · Tomcat Catalina SEVERE Log Storms

## Description

Log storms precede thread death, memory pressure, or database outages in Tomcat-hosted applications.

## Value

Automates first-pass triage of Java stack traces without manual tailing.

## Implementation

Deduplicate known stack hashes via `cluster` command; route to owners per webapp.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Tomcat.
• Ensure the following data sources are available: `index=application` `sourcetype=tomcat:catalina`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Noise-filter benign startup exceptions in dev tiers.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="tomcat:catalina"
| search "SEVERE" OR "Exception" OR "OutOfMemoryError"
| bin _time span=5m
| stats count by host
| where count > 50
```

Understanding this SPL

**Tomcat Catalina SEVERE Log Storms** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=application` `sourcetype=tomcat:catalina`. **App/TA**: Splunk Add-on for Tomcat. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Timechart (events), top messages, drill to raw..

## SPL

```spl
index=application sourcetype="tomcat:catalina"
| search "SEVERE" OR "Exception" OR "OutOfMemoryError"
| bin _time span=5m
| stats count by host
| where count > 50
```

## Visualization

Timechart (events), top messages, drill to raw.

## References

- [Splunk Add-on for Tomcat (Splunkbase)](https://splunkbase.splunk.com/app/2911)
