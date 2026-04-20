---
id: "3.1.12"
title: "Compose Service Health"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.1.12 · Compose Service Health

## Description

Docker Compose stacks power dev/stage and edge; tracking service `healthcheck` state and replica counts catches bad releases before they reach Kubernetes.

## Value

Docker Compose stacks power dev/stage and edge; tracking service `healthcheck` state and replica counts catches bad releases before they reach Kubernetes.

## Implementation

Scheduled `docker compose -f <file> ps --format json` per project; parse `Health`, `State`, `Service`. Ship to HEC. Alert on unhealthy or restarting services for >5 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom script (docker compose ps --format json), vector/file collector.
• Ensure the following data sources are available: `sourcetype=docker:compose:ps`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scheduled `docker compose -f <file> ps --format json` per project; parse `Health`, `State`, `Service`. Ship to HEC. Alert on unhealthy or restarting services for >5 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:compose:ps"
| eval healthy=if(Health=="healthy",1,0)
| stats latest(Health) as health, latest(State) as state, values(Service) as services by project, Name
| where health=0 OR match(state, "^(exited|restarting)")
| table project Name health state services
```

Understanding this SPL

**Compose Service Health** — Docker Compose stacks power dev/stage and edge; tracking service `healthcheck` state and replica counts catches bad releases before they reach Kubernetes.

Documented **Data sources**: `sourcetype=docker:compose:ps`. **App/TA** (typical add-on context): Custom script (docker compose ps --format json), vector/file collector. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:compose:ps. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:compose:ps". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **healthy** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by project, Name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where health=0 OR match(state, "^(exited|restarting)")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Compose Service Health**): table project Name health state services


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid by service, Table (project, service, health), Timeline of state changes.

## SPL

```spl
index=containers sourcetype="docker:compose:ps"
| eval healthy=if(Health=="healthy",1,0)
| stats latest(Health) as health, latest(State) as state, values(Service) as services by project, Name
| where health=0 OR match(state, "^(exited|restarting)")
| table project Name health state services
```

## Visualization

Status grid by service, Table (project, service, health), Timeline of state changes.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
