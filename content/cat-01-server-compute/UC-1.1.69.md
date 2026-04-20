---
id: "1.1.69"
title: "SUID/SGID Binary Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.69 · SUID/SGID Binary Changes

## Description

Unauthorized SUID/SGID binary modifications enable privilege escalation attacks.

## Value

Unauthorized SUID/SGID binary modifications enable privilege escalation attacks.

## Implementation

Monitor /proc/fs/pstore or auditctl for SUID/SGID attribute changes. Create alerts on any changes to SUID/SGID binaries. Maintain a whitelist of expected SUID/SGID files for comparison.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=linux_audit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor /proc/fs/pstore or auditctl for SUID/SGID attribute changes. Create alerts on any changes to SUID/SGID binaries. Maintain a whitelist of expected SUID/SGID files for comparison.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_audit type=EXECVE "suid" OR "sgid"
| stats count by host, name, comm
| where count > 0
```

Understanding this SPL

**SUID/SGID Binary Changes** — Unauthorized SUID/SGID binary modifications enable privilege escalation attacks.

Documented **Data sources**: `sourcetype=linux_audit`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, name, comm** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Table

## SPL

```spl
index=os sourcetype=linux_audit type=EXECVE "suid" OR "sgid"
| stats count by host, name, comm
| where count > 0
```

## Visualization

Alert, Table

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
