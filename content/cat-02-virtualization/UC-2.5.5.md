<!-- AUTO-GENERATED from UC-2.5.5.json — DO NOT EDIT -->

---
id: "2.5.5"
title: "IGEL OS Endpoint Syslog Error Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.5.5 · IGEL OS Endpoint Syslog Error Monitoring

## Description

IGEL OS endpoints forward syslog messages via rsyslog with TLS encryption to centralized collectors. Monitoring for error and critical severity messages across the fleet surfaces hardware failures, driver issues, network connectivity problems, and application crashes that users may not report until they become workflow-blocking.

## Value

IGEL OS endpoints forward syslog messages via rsyslog with TLS encryption to centralized collectors. Monitoring for error and critical severity messages across the fleet surfaces hardware failures, driver issues, network connectivity problems, and application crashes that users may not report until they become workflow-blocking.

## Implementation

Configure IGEL OS syslog forwarding via UMS profile: System > Logging > Remote mode = Client, with TLS enabled and CA certificate at `/wfs/ca-certs/ca.pem`. Point to Splunk TCP/TLS input on port 6514. Create a props.conf entry for `sourcetype=igel:os:syslog` to parse syslog priority into `severity` and `facility` fields. Alert on cluster patterns (same error across many devices = systemic issue, repeated errors on one device = hardware fault). Exclude known benign messages via a lookup filter.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk syslog input (TCP/TLS) receiving IGEL OS rsyslog.
• Ensure the following data sources are available: `index=endpoint` `sourcetype="igel:os:syslog"` fields `host`, `severity`, `facility`, `process`, `message`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure IGEL OS syslog forwarding via UMS profile: System > Logging > Remote mode = Client, with TLS enabled and CA certificate at `/wfs/ca-certs/ca.pem`. Point to Splunk TCP/TLS input on port 6514. Create a props.conf entry for `sourcetype=igel:os:syslog` to parse syslog priority into `severity` and `facility` fields. Alert on cluster patterns (same error across many devices = systemic issue, repeated errors on one device = hardware fault). Exclude known benign messages via a lookup filter.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=endpoint sourcetype="igel:os:syslog" (severity="err" OR severity="crit" OR severity="alert" OR severity="emerg")
| bin _time span=1h
| stats count as error_count, dc(host) as affected_devices, values(process) as processes by severity, _time
| where error_count > 10
| table _time, severity, error_count, affected_devices, processes
```

Understanding this SPL

**IGEL OS Endpoint Syslog Error Monitoring** — IGEL OS endpoints forward syslog messages via rsyslog with TLS encryption to centralized collectors. Monitoring for error and critical severity messages across the fleet surfaces hardware failures, driver issues, network connectivity problems, and application crashes that users may not report until they become workflow-blocking.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:os:syslog"` fields `host`, `severity`, `facility`, `process`, `message`. **App/TA** (typical add-on context): Splunk syslog input (TCP/TLS) receiving IGEL OS rsyslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: endpoint; **sourcetype**: igel:os:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=endpoint, sourcetype="igel:os:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by severity, _time** so each row reflects one combination of those dimensions.
• Filters the current rows with `where error_count > 10` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **IGEL OS Endpoint Syslog Error Monitoring**): table _time, severity, error_count, affected_devices, processes

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (error count by severity), Table (top errors by frequency), Bar chart (affected devices by error type).

## SPL

```spl
index=endpoint sourcetype="igel:os:syslog" (severity="err" OR severity="crit" OR severity="alert" OR severity="emerg")
| bin _time span=1h
| stats count as error_count, dc(host) as affected_devices, values(process) as processes by severity, _time
| where error_count > 10
| table _time, severity, error_count, affected_devices, processes
```

## Visualization

Timechart (error count by severity), Table (top errors by frequency), Bar chart (affected devices by error type).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
