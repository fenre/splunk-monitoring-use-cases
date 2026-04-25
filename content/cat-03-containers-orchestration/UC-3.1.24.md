<!-- AUTO-GENERATED from UC-3.1.24.json — DO NOT EDIT -->

---
id: "3.1.24"
title: "Docker Exec Session Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.1.24 · Docker Exec Session Audit

## Description

`docker exec` into a running container is an interactive access event that should be rare in production. Unexpected exec sessions may indicate troubleshooting without change control, unauthorized access, or an attacker establishing a foothold.

## Value

`docker exec` into a running container is an interactive access event that should be rare in production. Unexpected exec sessions may indicate troubleshooting without change control, unauthorized access, or an attacker establishing a foothold.

## Implementation

Docker emits `exec_start` and `exec_create` events when someone runs `docker exec`. Forward daemon events to Splunk. Alert on any exec in production environments, especially during non-business hours. Flag high-risk commands (shells like `/bin/bash`, `/bin/sh`, or commands accessing sensitive paths). Correlate with host SSH/login events to attribute the session to a user.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `docker events` scripted input, Docker daemon logs.
• Ensure the following data sources are available: `sourcetype=docker:events`, `sourcetype=docker:daemon`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Docker emits `exec_start` and `exec_create` events when someone runs `docker exec`. Forward daemon events to Splunk. Alert on any exec in production environments, especially during non-business hours. Flag high-risk commands (shells like `/bin/bash`, `/bin/sh`, or commands accessing sensitive paths). Correlate with host SSH/login events to attribute the session to a user.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:events" type="container" action="exec_start*"
| rex field=action "exec_start: (?<exec_cmd>.+)"
| stats count as exec_count, values(exec_cmd) as commands by container_name, host, _time
| sort -_time
```

Understanding this SPL

**Docker Exec Session Audit** — `docker exec` into a running container is an interactive access event that should be rare in production. Unexpected exec sessions may indicate troubleshooting without change control, unauthorized access, or an attacker establishing a foothold.

Documented **Data sources**: `sourcetype=docker:events`, `sourcetype=docker:daemon`. **App/TA** (typical add-on context): `docker events` scripted input, Docker daemon logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by container_name, host, _time** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Docker data, spot-check a few events against the Docker engine on the host and the container list you expect. Compare with known good and bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (exec sessions with command and container), Timeline (exec events), Single value (exec count last 24h).

## SPL

```spl
index=containers sourcetype="docker:events" type="container" action="exec_start*"
| rex field=action "exec_start: (?<exec_cmd>.+)"
| stats count as exec_count, values(exec_cmd) as commands by container_name, host, _time
| sort -_time
```

## Visualization

Table (exec sessions with command and container), Timeline (exec events), Single value (exec count last 24h).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
