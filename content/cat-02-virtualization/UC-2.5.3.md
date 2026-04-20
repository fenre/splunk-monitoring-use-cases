---
id: "2.5.3"
title: "IGEL UMS Server Health Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.5.3 · IGEL UMS Server Health Monitoring

## Description

The IGEL UMS server is the central management plane for all IGEL endpoints. If UMS goes down or enters an error state, administrators cannot push policies, update firmware, or manage device configurations. Monitoring the built-in health endpoint provides immediate alerting on database connectivity failures, HA issues, or service degradation.

## Value

The IGEL UMS server is the central management plane for all IGEL endpoints. If UMS goes down or enters an error state, administrators cannot push policies, update firmware, or manage device configurations. Monitoring the built-in health endpoint provides immediate alerting on database connectivity failures, HA issues, or service degradation.

## Implementation

Create a scripted input that polls `https://[server]:[port]/ums/check-status` every 60 seconds. The endpoint returns JSON with a `status` field (values: `init`, `ok`, `warn`, `err`) and optional `message` describing the issue. Parse the response and index as events. Alert immediately on `err` status (database connection failure, device communication port not ready). Alert on `warn` status (HA update mode, cloud gateway disconnection, certificate sync issues). Also alert if no health check event has been received in 5 minutes (endpoint unreachable).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input polling UMS check-status endpoint.
• Ensure the following data sources are available: `index=endpoint` `sourcetype="igel:ums:health"` fields `ums_server`, `status`, `message`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that polls `https://[server]:[port]/ums/check-status` every 60 seconds. The endpoint returns JSON with a `status` field (values: `init`, `ok`, `warn`, `err`) and optional `message` describing the issue. Parse the response and index as events. Alert immediately on `err` status (database connection failure, device communication port not ready). Alert on `warn` status (HA update mode, cloud gateway disconnection, certificate sync issues). Also alert if no health check event …

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=endpoint sourcetype="igel:ums:health"
| stats latest(status) as current_status, latest(message) as message, latest(_time) as last_check by ums_server
| eval status_age_min=round((now()-last_check)/60,0)
| where current_status!="ok" OR status_age_min > 5
| table ums_server, current_status, message, status_age_min
```

Understanding this SPL

**IGEL UMS Server Health Monitoring** — The IGEL UMS server is the central management plane for all IGEL endpoints. If UMS goes down or enters an error state, administrators cannot push policies, update firmware, or manage device configurations. Monitoring the built-in health endpoint provides immediate alerting on database connectivity failures, HA issues, or service degradation.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:ums:health"` fields `ums_server`, `status`, `message`. **App/TA** (typical add-on context): Custom scripted input polling UMS check-status endpoint. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: endpoint; **sourcetype**: igel:ums:health. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=endpoint, sourcetype="igel:ums:health". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ums_server** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **status_age_min** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where current_status!="ok" OR status_age_min > 5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **IGEL UMS Server Health Monitoring**): table ums_server, current_status, message, status_age_min


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (current status with color coding), Timeline (status changes over time), Table (all UMS servers with status).

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
index=endpoint sourcetype="igel:ums:health"
| stats latest(status) as current_status, latest(message) as message, latest(_time) as last_check by ums_server
| eval status_age_min=round((now()-last_check)/60,0)
| where current_status!="ok" OR status_age_min > 5
| table ums_server, current_status, message, status_age_min
```

## Visualization

Single value (current status with color coding), Timeline (status changes over time), Table (all UMS servers with status).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
