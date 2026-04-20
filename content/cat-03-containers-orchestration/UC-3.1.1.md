---
id: "3.1.1"
title: "Container Crash Loops"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.1.1 · Container Crash Loops

## Description

Containers restarting repeatedly indicate application bugs, misconfiguration, or dependency failures. Crash loops consume resources and never reach healthy state.

## Value

Containers restarting repeatedly indicate application bugs, misconfiguration, or dependency failures. Crash loops consume resources and never reach healthy state.

## Implementation

Install Splunk Connect for Docker or configure Docker logging driver to forward to Splunk HEC. Collect Docker events via `docker events --format '{{json .}}'`. Alert when a container restarts >3 times in 15 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Docker, Docker events via syslog.
• Ensure the following data sources are available: `sourcetype=docker:events`, Docker daemon logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install Splunk Connect for Docker or configure Docker logging driver to forward to Splunk HEC. Collect Docker events via `docker events --format '{{json .}}'`. Alert when a container restarts >3 times in 15 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:events" action="die"
| eval exit_code=exitCode
| where exit_code != "0"
| stats count as crashes by container_name, image, exit_code
| where crashes > 3
| sort -crashes
```

Understanding this SPL

**Container Crash Loops** — Containers restarting repeatedly indicate application bugs, misconfiguration, or dependency failures. Crash loops consume resources and never reach healthy state.

Documented **Data sources**: `sourcetype=docker:events`, Docker daemon logs. **App/TA** (typical add-on context): Splunk Connect for Docker, Docker events via syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **exit_code** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where exit_code != "0"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by container_name, image, exit_code** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where crashes > 3` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (container, image, crashes, exit code), Bar chart by container, Timeline.

## SPL

```spl
index=containers sourcetype="docker:events" action="die"
| eval exit_code=exitCode
| where exit_code != "0"
| stats count as crashes by container_name, image, exit_code
| where crashes > 3
| sort -crashes
```

## Visualization

Table (container, image, crashes, exit code), Bar chart by container, Timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
