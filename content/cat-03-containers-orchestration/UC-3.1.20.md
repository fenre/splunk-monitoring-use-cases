---
id: "3.1.20"
title: "Docker Registry Mirror Health"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.1.20 · Docker Registry Mirror Health

## Description

Registry mirrors reduce pull latency and hub rate limits; a stale or failing mirror causes random image pull delays across the fleet.

## Value

Registry mirrors reduce pull latency and hub rate limits; a stale or failing mirror causes random image pull delays across the fleet.

## Implementation

Log `Registry Mirrors` from `docker info` and probe mirror `/v2/` with auth-less ping where allowed. Alert on daemon errors referencing mirrors or failed probes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Docker daemon config audit, mirror HTTP checks.
• Ensure the following data sources are available: `sourcetype=docker:info`, `sourcetype=docker:daemon`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Log `Registry Mirrors` from `docker info` and probe mirror `/v2/` with auth-less ping where allowed. Alert on daemon errors referencing mirrors or failed probes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="http:check" check_type="registry_mirror"
| where status!=200 OR response_time_ms>2000
| table _time mirror_url host status response_time_ms
```

Understanding this SPL

**Docker Registry Mirror Health** — Registry mirrors reduce pull latency and hub rate limits; a stale or failing mirror causes random image pull delays across the fleet.

Documented **Data sources**: `sourcetype=docker:info`, `sourcetype=docker:daemon`. **App/TA** (typical add-on context): Docker daemon config audit, mirror HTTP checks. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: http:check. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="http:check". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where status!=200 OR response_time_ms>2000` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Docker Registry Mirror Health**): table _time mirror_url host status response_time_ms


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (mirror, status, latency), Map or bar by region, Timeline of failures.

## SPL

```spl
index=containers sourcetype="http:check" check_type="registry_mirror"
| where status!=200 OR response_time_ms>2000
| table _time mirror_url host status response_time_ms
```

## Visualization

Table (mirror, status, latency), Map or bar by region, Timeline of failures.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
