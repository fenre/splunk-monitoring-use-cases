<!-- AUTO-GENERATED from UC-8.5.14.json — DO NOT EDIT -->

---
id: "8.5.14"
title: "WildFly Server Patch and Extension Audit Events"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-8.5.14 · WildFly Server Patch and Extension Audit Events

## Description

WildFly logs patch installs, subsystem changes, and extensions—critical for change auditing on Java EE platforms.

## Value

Provides evidence for CAB reviews and security baselines.

## Implementation

Forward `standalone/log/server.log` (or domain host-controller logs) with timestamps preserved. Capture patch installs, extension adds, and subsystem changes; validate message substrings against your WildFly major version in a lab. Suppress known-noisy startup sequences via allowlists.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: JBoss server.log forwarding.
• Ensure the following data sources are available: `index=application` `sourcetype=jboss:server` (patch installation markers).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward WildFly `server.log` from each node; include patch and extension events at INFO or higher as appropriate. Message IDs differ by version—validate search substrings against a lab upgrade before production alerts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="jboss:server"
| search "WFLYSRV0010" OR "installed patch" OR "Extension added" OR "Subsystem added"
| table _time, host, _raw
| sort -_time
```

Understanding this SPL

**WildFly Server Patch and Extension Audit Events** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=application` `sourcetype=jboss:server` (patch installation markers). **App/TA**: JBoss server.log forwarding. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with the cache or proxy product’s own stats (CLI or UI) and a small sample of indexed events.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Table (events), timeline, export for ticketing integration..

## SPL

```spl
index=application sourcetype="jboss:server"
| search "WFLYSRV0010" OR "installed patch" OR "Extension added" OR "Subsystem added"
| table _time, host, _raw
| sort -_time
```

## Visualization

Table (events), timeline, export for ticketing integration.

## References

- [WildFly Admin Guide — Access Logging](https://docs.wildfly.org/)
