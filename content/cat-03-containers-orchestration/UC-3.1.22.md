---
id: "3.1.22"
title: "Container Health Check Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.22 · Container Health Check Failures

## Description

Docker HEALTHCHECK provides a built-in liveness signal. Containers stuck in "unhealthy" or "starting" state may still appear as "running" but are no longer serving traffic correctly, masking outages from basic uptime checks.

## Value

Docker HEALTHCHECK provides a built-in liveness signal. Containers stuck in "unhealthy" or "starting" state may still appear as "running" but are no longer serving traffic correctly, masking outages from basic uptime checks.

## Implementation

Docker emits `health_status` events for containers with a HEALTHCHECK instruction. Forward Docker daemon events to Splunk via HEC or syslog. Alert when a container enters "unhealthy" state or stays in "starting" for longer than the start period. Correlate with container logs to identify the failing check command. Track health check failure rate per image to identify systemic issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Docker logging driver (HEC), `docker events` scripted input.
• Ensure the following data sources are available: `sourcetype=docker:events`, `sourcetype=docker:inspect`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Docker emits `health_status` events for containers with a HEALTHCHECK instruction. Forward Docker daemon events to Splunk via HEC or syslog. Alert when a container enters "unhealthy" state or stays in "starting" for longer than the start period. Correlate with container logs to identify the failing check command. Track health check failure rate per image to identify systemic issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:events" type="container" action="health_status*"
| rex field=action "health_status: (?<health_status>\w+)"
| where health_status="unhealthy"
| stats count as unhealthy_count, latest(_time) as last_unhealthy by container_name, container_id, host
| where unhealthy_count > 3
| sort -unhealthy_count
```

Understanding this SPL

**Container Health Check Failures** — Docker HEALTHCHECK provides a built-in liveness signal. Containers stuck in "unhealthy" or "starting" state may still appear as "running" but are no longer serving traffic correctly, masking outages from basic uptime checks.

Documented **Data sources**: `sourcetype=docker:events`, `sourcetype=docker:inspect`. **App/TA** (typical add-on context): Splunk Docker logging driver (HEC), `docker events` scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Filters the current rows with `where health_status="unhealthy"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by container_name, container_id, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where unhealthy_count > 3` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (unhealthy containers with count), Single value (unhealthy container count), Timeline (health status transitions).

## SPL

```spl
index=containers sourcetype="docker:events" type="container" action="health_status*"
| rex field=action "health_status: (?<health_status>\w+)"
| where health_status="unhealthy"
| stats count as unhealthy_count, latest(_time) as last_unhealthy by container_name, container_id, host
| where unhealthy_count > 3
| sort -unhealthy_count
```

## Visualization

Table (unhealthy containers with count), Single value (unhealthy container count), Timeline (health status transitions).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
