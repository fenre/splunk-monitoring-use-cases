<!-- AUTO-GENERATED from UC-8.8.1.json — DO NOT EDIT -->

---
id: "8.8.1"
title: "RPA Bot Execution Health and Queue Depth Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.8.1 · RPA Bot Execution Health and Queue Depth Monitoring

## Description

Hourly aggregation of robot run counts, derived failure rates from normalized status text, average duration, and peak queue depth per bot and process so unhealthy automations stand out before business SLAs miss.

## Value

Operations managers keep invoice, claims, and onboarding robots from silently piling up exceptions that force expensive manual clearing teams, which protects customer promises and frees people for work that still needs a human touch.

## Implementation

Land Orchestrator job logs and Automation Anywhere Bot Insight JSON on `index=rpa`. Map vendor-specific success and fault codes into the coalesced `status_norm` field at index time for consistency. Start alerts on failure_rate and queue_depth, then add seasonality baselines per process_name for finance month-end peaks.

## Detailed Implementation

Prerequisites
• API credentials scoped read-only on Orchestrator and Control Room; outbound HTTPS from modular input hosts.
• Field extractions aligning `duration_seconds`, `queue_depth`, and identity fields (`bot_name`, `process_name`) across both vendor sourcetypes.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use supported modular inputs or HTTP Poller scripts calling Orchestrator OData endpoints (`/odata/Jobs`). For Automation Anywhere, ingest Bot Insight webhooks or API CSV drops. Normalize timestamps to UTC and deduplicate retries using a vendor-supplied correlation id where available.

Step 2 — Create the search and alert
Run the following SPL (adjust failure_rate and queue thresholds by process criticality):

```spl
index=rpa sourcetype IN ("uipath:orchestrator","automation_anywhere:bot_insight")
| eval status_norm=lower(coalesce(State, bot_status, status, ""))
| eval failure=if(status_norm IN ("faulted","failed","error","stopped"),1,0)
| bin _time span=1h
| stats count as executions sum(failure) as failures avg(duration_seconds) as avg_duration max(queue_depth) as max_queue by bot_name process_name _time
| eval failure_rate=round(if(executions>0,(failures/executions)*100,0),1)
| where failure_rate > 10 OR max_queue > 50
| sort - failure_rate
```

Understanding this SPL

**RPA Bot Execution Health and Queue Depth Monitoring** consolidates heterogeneous vendor fields via `coalesce`, derives a Boolean failure marker, then rolls up throughput and backlog indicators hourly.

**Pipeline walkthrough**

• `lower` avoids case mismatch between UiPath "Faulted" and lowercase API exports.
• `bin _time span=1h` stabilizes alerting versus per-event noise.
• `stats` aligns counts, failures, durations, and queue extremes in one pass.
• `failure_rate` guards against alerting on trivial single-run samples when paired with contextual review.

Step 3 — Validate
Pick an hour flagged in results and reconcile counts with Orchestrator Job Details or Automation Anywhere dashboards. Confirm `duration_seconds` matches vendor UI durations (divide if milliseconds were ingested). Validate queue metrics against live queue inspectors during the incident.

Step 4 — Operationalize
Maintain a roster mapping `process_name` to business queue owners. Tie high failure_rate incidents to screenshot evidence stored in ticketing. Extend the search with lookups for maintenance calendars so planned downtime suppresses paging. Consider visualizations: Dual-axis time chart, Table with contextual links to vendor portals, Gauge for queue SLA.

## SPL

```spl
index=rpa sourcetype IN ("uipath:orchestrator","automation_anywhere:bot_insight")
| eval status_norm=lower(coalesce(State, bot_status, status, ""))
| eval failure=if(status_norm IN ("faulted","failed","error","stopped"),1,0)
| bin _time span=1h
| stats count as executions sum(failure) as failures avg(duration_seconds) as avg_duration max(queue_depth) as max_queue by bot_name process_name _time
| eval failure_rate=round(if(executions>0,(failures/executions)*100,0),1)
| where failure_rate > 10 OR max_queue > 50
| sort - failure_rate
```

## Visualization

Time chart (failure_rate and max_queue by hour), Table (bot_name, process_name, executions, failure_rate), Single value (worst queue_depth).

## Known False Positives

Vendor platform upgrades transiently flip jobs into "stopped" states, benign credential rotations fail once until secrets refresh, regression-test environments replay historical queues, and large holiday batch jobs legitimately deepen queues without SLA breach.

## References

- [Splunk Lantern — Use Case Explorer: IT Modernization](https://lantern.splunk.com/Splunk_Platform/UCE)
- [UiPath Orchestrator API Documentation](https://docs.uipath.com/orchestrator/reference/api-references)
