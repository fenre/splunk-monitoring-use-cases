<!-- AUTO-GENERATED from UC-8.2.21.json — DO NOT EDIT -->

---
id: "8.2.21"
title: "Spring Boot Actuator Health Down"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.21 · Spring Boot Actuator Health Down

## Description

`/actuator/health` JSON with `status:DOWN` from liveness/readiness probes. Aggregates component failures (diskSpace, db, redis).

## Value

`/actuator/health` JSON with `status:DOWN` from liveness/readiness probes. Aggregates component failures (diskSpace, db, redis).

## Implementation

Ship health check responses (avoid PII). Alert on non-UP. Break down `components.*.status` for root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: HEC from K8s probe sidecar, access log.
• Ensure the following data sources are available: `spring:actuator` JSON lines, probe stderr.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ship health check responses (avoid PII). Alert on non-UP. Break down `components.*.status` for root cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="spring:actuator" OR path="/actuator/health"
| spath output=status status
| spath output=components components
| where status!="UP"
| table _time, host, app_name, status, components
```

Understanding this SPL

**Spring Boot Actuator Health Down** — `/actuator/health` JSON with `status:DOWN` from liveness/readiness probes. Aggregates component failures (diskSpace, db, redis).

Documented **Data sources**: `spring:actuator` JSON lines, probe stderr. **App/TA** (typical add-on context): HEC from K8s probe sidecar, access log. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: application; **sourcetype**: spring:actuator. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=application, sourcetype="spring:actuator". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Extracts structured paths (JSON/XML) with `spath`.
• Filters the current rows with `where status!="UP"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Spring Boot Actuator Health Down**): table _time, host, app_name, status, components


Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (app × component), Table (DOWN components), Timeline (health flaps).

## SPL

```spl
index=application sourcetype="spring:actuator" OR path="/actuator/health"
| spath output=status status
| spath output=components components
| where status!="UP"
| table _time, host, app_name, status, components
```

## Visualization

Status grid (app × component), Table (DOWN components), Timeline (health flaps).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
