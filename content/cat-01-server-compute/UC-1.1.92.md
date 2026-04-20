---
id: "1.1.92"
title: "Auditd Daemon Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.92 · Auditd Daemon Health

## Description

Auditd daemon failure results in loss of security audit trail, creating compliance and forensic gaps.

## Value

Auditd daemon failure results in loss of security audit trail, creating compliance and forensic gaps.

## Implementation

Monitor auditd process status and audit event flow. Create alerts when no audit events are received for 5+ minutes. Include daemon status checks and restart recommendations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, linux_audit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor auditd process status and audit event flow. Create alerts when no audit events are received for 5+ minutes. Include daemon status checks and restart recommendations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_audit host=*
| stats count as audit_events, max(_time) as last_event by host
| where audit_events == 0 OR (now() - last_event) > 300
```

Understanding this SPL

**Auditd Daemon Health** — Auditd daemon failure results in loss of security audit trail, creating compliance and forensic gaps.

Documented **Data sources**: `sourcetype=syslog, linux_audit`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where audit_events == 0 OR (now() - last_event) > 300` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Auditd Daemon Health** — Auditd daemon failure results in loss of security audit trail, creating compliance and forensic gaps.

Documented **Data sources**: `sourcetype=syslog, linux_audit`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Processes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Single Value

## SPL

```spl
index=os sourcetype=linux_audit host=*
| stats count as audit_events, max(_time) as last_event by host
| where audit_events == 0 OR (now() - last_event) > 300
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

## Visualization

Alert, Single Value

## References

- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
