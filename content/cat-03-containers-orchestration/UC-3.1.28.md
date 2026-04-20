---
id: "3.1.28"
title: "Docker Swarm Service Replica Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.1.28 · Docker Swarm Service Replica Health

## Description

Swarm services may show the correct replica count globally but have tasks stuck in "pending", "rejected", or "failed" state. Monitoring task-level health catches scheduling failures, resource constraints, and rolling update stalls that the service-level view hides.

## Value

Swarm services may show the correct replica count globally but have tasks stuck in "pending", "rejected", or "failed" state. Monitoring task-level health catches scheduling failures, resource constraints, and rolling update stalls that the service-level view hides.

## Implementation

Poll `docker service ls --format json` and `docker service ps <service> --format json` on a schedule. Extract `desired`, `running`, and task states. Alert when running replicas are fewer than desired for more than 2 consecutive checks. Track `update_status` during rolling updates — alert when an update is "paused" (hit failure threshold). Monitor task rejection reasons (resource constraints, image pull failures, port conflicts) to diagnose scheduling issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `docker service` scripted input, Docker daemon logs.
• Ensure the following data sources are available: `sourcetype=docker:service`, `sourcetype=docker:daemon`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `docker service ls --format json` and `docker service ps <service> --format json` on a schedule. Extract `desired`, `running`, and task states. Alert when running replicas are fewer than desired for more than 2 consecutive checks. Track `update_status` during rolling updates — alert when an update is "paused" (hit failure threshold). Monitor task rejection reasons (resource constraints, image pull failures, port conflicts) to diagnose scheduling issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:service"
| where desired_replicas != running_replicas OR failed_tasks > 0
| eval gap=desired_replicas - running_replicas
| table _time, service_name, desired_replicas, running_replicas, gap, failed_tasks, update_status
| sort -gap
```

Understanding this SPL

**Docker Swarm Service Replica Health** — Swarm services may show the correct replica count globally but have tasks stuck in "pending", "rejected", or "failed" state. Monitoring task-level health catches scheduling failures, resource constraints, and rolling update stalls that the service-level view hides.

Documented **Data sources**: `sourcetype=docker:service`, `sourcetype=docker:daemon`. **App/TA** (typical add-on context): `docker service` scripted input, Docker daemon logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:service. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:service". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where desired_replicas != running_replicas OR failed_tasks > 0` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **gap** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Docker Swarm Service Replica Health**): table _time, service_name, desired_replicas, running_replicas, gap, failed_tasks, update_status
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (services with replica gaps), Single value (unhealthy service count), Timeline (task failures).

## SPL

```spl
index=containers sourcetype="docker:service"
| where desired_replicas != running_replicas OR failed_tasks > 0
| eval gap=desired_replicas - running_replicas
| table _time, service_name, desired_replicas, running_replicas, gap, failed_tasks, update_status
| sort -gap
```

## Visualization

Table (services with replica gaps), Single value (unhealthy service count), Timeline (task failures).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
