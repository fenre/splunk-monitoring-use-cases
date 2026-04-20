---
id: "8.6.13"
title: "HashiCorp Nomad Job and Allocation Status"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.6.13 · HashiCorp Nomad Job and Allocation Status

## Description

Failed allocations and job deployment health indicate Nomad scheduler and workload availability. Failed allocations mean tasks are not running; deployment failures block rollouts.

## Value

Failed allocations and job deployment health indicate Nomad scheduler and workload availability. Failed allocations mean tasks are not running; deployment failures block rollouts.

## Implementation

Poll Nomad `/v1/jobs` and `/v1/allocations` via scripted input every 5 minutes. Parse JobID, TaskGroup, ClientStatus, DesiredStatus, CreateIndex. Forward to Splunk via HEC. Alert when ClientStatus==failed or allocations are pending/running when desired is stop. Track deployment status (job version, allocation placement). Correlate with node availability.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Nomad HTTP API).
• Ensure the following data sources are available: Nomad `/v1/jobs`, `/v1/allocations`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll Nomad `/v1/jobs` and `/v1/allocations` via scripted input every 5 minutes. Parse JobID, TaskGroup, ClientStatus, DesiredStatus, CreateIndex. Forward to Splunk via HEC. Alert when ClientStatus==failed or allocations are pending/running when desired is stop. Track deployment status (job version, allocation placement). Correlate with node availability.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=nomad sourcetype="nomad:allocations"
| where ClientStatus=="failed" OR (DesiredStatus=="run" AND ClientStatus!="running")
| stats count by JobID, TaskGroup, ClientStatus
| sort -count
```

Understanding this SPL

**HashiCorp Nomad Job and Allocation Status** — Failed allocations and job deployment health indicate Nomad scheduler and workload availability. Failed allocations mean tasks are not running; deployment failures block rollouts.

Documented **Data sources**: Nomad `/v1/jobs`, `/v1/allocations`. **App/TA** (typical add-on context): Custom (Nomad HTTP API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: nomad; **sourcetype**: nomad:allocations. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=nomad, sourcetype="nomad:allocations". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where ClientStatus=="failed" OR (DesiredStatus=="run" AND ClientStatus!="running")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by JobID, TaskGroup, ClientStatus** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (failed allocations by job), Single value (failed allocation count), Status grid (job × allocation status), Timeline (allocation events).

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
index=nomad sourcetype="nomad:allocations"
| where ClientStatus=="failed" OR (DesiredStatus=="run" AND ClientStatus!="running")
| stats count by JobID, TaskGroup, ClientStatus
| sort -count
```

## Visualization

Table (failed allocations by job), Single value (failed allocation count), Status grid (job × allocation status), Timeline (allocation events).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
