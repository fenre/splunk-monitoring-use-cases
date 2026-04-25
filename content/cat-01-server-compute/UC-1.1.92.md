<!-- AUTO-GENERATED from UC-1.1.92.json — DO NOT EDIT -->

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
Monitor auditd process status and audit event flow. Create alerts when no audit events are received for 5+ minutes. Include daemon status checks and restart recommendations (`systemctl status auditd` on Linux).

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
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where audit_events == 0 OR (now() - last_event) > 300` — typically the threshold or rule expression for this monitoring goal.

There is no faithful CIM/tstats equivalent for “absence of linux_audit events per host” without a summary index or entity model; keep this as raw `linux_audit` SPL.


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

## Visualization

Alert, Single Value

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
