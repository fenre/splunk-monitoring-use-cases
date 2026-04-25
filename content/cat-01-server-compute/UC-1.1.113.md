<!-- AUTO-GENERATED from UC-1.1.113.json — DO NOT EDIT -->

---
id: "1.1.113"
title: "SETUID Audit and Tracking"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.113 · SETUID Audit and Tracking

## Description

SETUID binary execution enables privilege escalation requiring tracking for security monitoring.

## Value

SETUID binary execution enables privilege escalation requiring tracking for security monitoring.

## Implementation

Configure auditctl rules monitoring EXECVE syscalls with setuid. Create alerts on SETUID binary execution by unexpected users. Baseline expected SETUID usage per host.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=linux_audit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure auditctl rules monitoring EXECVE syscalls with setuid. Create alerts on SETUID binary execution by unexpected users. Baseline expected SETUID usage per host.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_audit type=EXECVE exe="*" AND suid
| stats count by host, exe, user
| where count > threshold
```

Understanding this SPL

**SETUID Audit and Tracking** — SETUID binary execution enables privilege escalation requiring tracking for security monitoring.

Documented **Data sources**: `sourcetype=linux_audit`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, exe, user** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > threshold` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Alert

## SPL

```spl
index=os sourcetype=linux_audit type=EXECVE exe="*" AND suid
| stats count by host, exe, user
| where count > threshold
```

## Visualization

Table, Alert

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
