<!-- AUTO-GENERATED from UC-3.1.7.json — DO NOT EDIT -->

---
id: "3.1.7"
title: "Container Sprawl"
criticality: "low"
splunkPillar: "Observability"
---

# UC-3.1.7 · Container Sprawl

## Description

Stopped containers and dangling images waste disk space. In development environments, sprawl can consume all available storage.

## Value

Stopped containers and dangling images waste disk space. In development environments, sprawl can consume all available storage.

## Implementation

Scripted input: `docker ps -a --format '{{json .}}'` and `docker system df`. Run daily. Report on stopped containers >7 days and total disk reclamation possible.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input.
• Ensure the following data sources are available: `docker ps -a`, `docker images`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input: `docker ps -a --format '{{json .}}'` and `docker system df`. Run daily. Report on stopped containers >7 days and total disk reclamation possible.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:ps"
| where status="exited"
| eval days_stopped = round((now() - strptime(finished_at, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where days_stopped > 7
| stats count by host
```

Understanding this SPL

**Container Sprawl** — Stopped containers and dangling images waste disk space. In development environments, sprawl can consume all available storage.

Documented **Data sources**: `docker ps -a`, `docker images`. **App/TA** (typical add-on context): Custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:ps. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:ps". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where status="exited"` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **days_stopped** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_stopped > 7` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Docker data, spot-check a few events against the Docker engine on the host and the container list you expect. Compare with known good and bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Single value (reclaimable space), Bar chart by host.

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=containers sourcetype="docker:ps"
| where status="exited"
| eval days_stopped = round((now() - strptime(finished_at, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where days_stopped > 7
| stats count by host
```

## Visualization

Table, Single value (reclaimable space), Bar chart by host.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
