---
id: "3.1.19"
title: "Container Log Driver Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.19 · Container Log Driver Health

## Description

When the logging driver backs up or errors, application logs are dropped—blinding security and operations during incidents.

## Value

When the logging driver backs up or errors, application logs are dropped—blinding security and operations during incidents.

## Implementation

Monitor daemon for log driver write failures, buffer overflow, and remote endpoint timeouts. Correlate with missing log volume in Splunk for the same container IDs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Docker daemon logs, Splunk Connect for Docker.
• Ensure the following data sources are available: `sourcetype=docker:daemon`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor daemon for log driver write failures, buffer overflow, and remote endpoint timeouts. Correlate with missing log volume in Splunk for the same container IDs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:daemon" ("log driver" OR "failed to log" OR "splunk" OR "fluentd")
| search (level="error" OR level="warn")
| stats count by host, msg
| sort -count
```

Understanding this SPL

**Container Log Driver Health** — When the logging driver backs up or errors, application logs are dropped—blinding security and operations during incidents.

Documented **Data sources**: `sourcetype=docker:daemon`. **App/TA** (typical add-on context): Docker daemon logs, Splunk Connect for Docker. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:daemon. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:daemon". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by host, msg** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, error, count), Timeline, Single value (log driver errors/hour).

## SPL

```spl
index=containers sourcetype="docker:daemon" ("log driver" OR "failed to log" OR "splunk" OR "fluentd")
| search (level="error" OR level="warn")
| stats count by host, msg
| sort -count
```

## Visualization

Table (host, error, count), Timeline, Single value (log driver errors/hour).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
