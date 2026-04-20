---
id: "8.2.20"
title: "JBoss / WildFly Deployment Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.20 · JBoss / WildFly Deployment Failures

## Description

Failed deployments leave apps stopped or partial. Log markers `WFLYSRV0026`, `Deployment FAILED` require immediate attention.

## Value

Failed deployments leave apps stopped or partial. Log markers `WFLYSRV0026`, `Deployment FAILED` require immediate attention.

## Implementation

Parse deployment name from log line. Alert on any FAILURE during CI/CD window or outside window (rogue deploy). Correlate with Git commit from pipeline ID if present.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: JBoss server.log ingestion.
• Ensure the following data sources are available: `jboss:server.log`, `server.log` deployment phase.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse deployment name from log line. Alert on any FAILURE during CI/CD window or outside window (rogue deploy). Correlate with Git commit from pipeline ID if present.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="jboss:server"
| search "Deployment FAILED" OR "WFLYSRV0059" OR "Services with missing/unavailable dependencies"
| table _time, host, deployment, message
| sort -_time
```

Understanding this SPL

**JBoss / WildFly Deployment Failures** — Failed deployments leave apps stopped or partial. Log markers `WFLYSRV0026`, `Deployment FAILED` require immediate attention.

Documented **Data sources**: `jboss:server.log`, `server.log` deployment phase. **App/TA** (typical add-on context): JBoss server.log ingestion. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: application; **sourcetype**: jboss:server. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=application, sourcetype="jboss:server". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **JBoss / WildFly Deployment Failures**): table _time, host, deployment, message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (deployment outcomes), Table (failed deployment, error), Single value (failures 24h).

## SPL

```spl
index=application sourcetype="jboss:server"
| search "Deployment FAILED" OR "WFLYSRV0059" OR "Services with missing/unavailable dependencies"
| table _time, host, deployment, message
| sort -_time
```

## Visualization

Timeline (deployment outcomes), Table (failed deployment, error), Single value (failures 24h).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
