<!-- AUTO-GENERATED from UC-8.6.22.json — DO NOT EDIT -->

---
id: "8.6.22"
title: "WildFly server.log Error Logger Spike"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.6.22 · WildFly server.log Error Logger Spike

## Description

WildFly clusters emit subsystem errors (datasources, messaging, EJB) in server.log with distinct codes.

## Value

Shortens Java EE incident response versus generic OS monitoring.

## Implementation

Use `cluster` to group stack traces; tune for bootstrap noise.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: JBoss/WildFly log forwarding.
• Ensure the following data sources are available: `index=application` `sourcetype=jboss:server`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Narrow WFLY tokens to your deployment (omit broad `WFLYSRV` if too noisy).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="jboss:server"
| search " ERROR " OR " WFLYCTL" OR " WFLYSRV"
| search "ERROR" OR "failure" OR "exception"
| bin _time span=5m
| stats count by host
| where count > 30
```

Understanding this SPL

**WildFly server.log Error Logger Spike** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=application` `sourcetype=jboss:server`. **App/TA**: JBoss/WildFly log forwarding. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Timechart, table of logger categories if parsed..

## SPL

```spl
index=application sourcetype="jboss:server"
| regex _raw="(?i)(ERROR|WFLYCTL|Exception|failed to|failure)"
| bin _time span=5m
| stats count by host
| where count > 30
```

## Visualization

Timechart, table of logger categories if parsed.

## References

- [WildFly Admin Guide — Access Logging](https://docs.wildfly.org/)
