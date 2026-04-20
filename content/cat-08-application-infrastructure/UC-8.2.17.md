---
id: "8.2.17"
title: "Python WSGI Worker Pool Exhaustion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.17 · Python WSGI Worker Pool Exhaustion

## Description

Gunicorn/uWSGI `active workers`, `listening queue`, and `timeout` worker kills indicate saturation or slow upstream (DB).

## Value

Gunicorn/uWSGI `active workers`, `listening queue`, and `timeout` worker kills indicate saturation or slow upstream (DB).

## Implementation

Enable `--statsd` or JSON access/error with worker fields. Alert on backlog growth or worker timeouts. Scale workers or fix slow queries.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Structured app logs, stats endpoint.
• Ensure the following data sources are available: `gunicorn:json` `workers`, `req`, `timeout`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable `--statsd` or JSON access/error with worker fields. Alert on backlog growth or worker timeouts. Scale workers or fix slow queries.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="gunicorn:json"
| where worker_timeout > 0 OR active_workers >= max_workers OR backlog > 10
| stats sum(worker_timeout) as timeouts, max(backlog) as max_backlog by host, app_name
| where timeouts > 0 OR max_backlog > 10
```

Understanding this SPL

**Python WSGI Worker Pool Exhaustion** — Gunicorn/uWSGI `active workers`, `listening queue`, and `timeout` worker kills indicate saturation or slow upstream (DB).

Documented **Data sources**: `gunicorn:json` `workers`, `req`, `timeout`. **App/TA** (typical add-on context): Structured app logs, stats endpoint. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: application; **sourcetype**: gunicorn:json. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=application, sourcetype="gunicorn:json". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where worker_timeout > 0 OR active_workers >= max_workers OR backlog > 10` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by host, app_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where timeouts > 0 OR max_backlog > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (backlog and active workers), Table (apps with timeouts), Single value (total worker timeouts 1h).

## SPL

```spl
index=application sourcetype="gunicorn:json"
| where worker_timeout > 0 OR active_workers >= max_workers OR backlog > 10
| stats sum(worker_timeout) as timeouts, max(backlog) as max_backlog by host, app_name
| where timeouts > 0 OR max_backlog > 10
```

## Visualization

Line chart (backlog and active workers), Table (apps with timeouts), Single value (total worker timeouts 1h).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
