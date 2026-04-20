---
id: "9.4.3"
title: "Break-Glass Account Usage"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.4.3 · Break-Glass Account Usage

## Description

Break-glass accounts provide emergency access and should rarely be used. Any usage requires immediate investigation and documentation.

## Value

Break-glass accounts provide emergency access and should rarely be used. Any usage requires immediate investigation and documentation.

## Implementation

Tag break-glass accounts in PAM. Create critical alert for any break-glass access. Require documented reason within 24 hours. Send notifications to security team and management. Track usage frequency for trend reporting.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk_TA_cyberark, custom alert.
• Ensure the following data sources are available: PAM vault events for break-glass accounts.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Tag break-glass accounts in PAM. Create critical alert for any break-glass access. Require documented reason within 24 hours. Send notifications to security team and management. Track usage frequency for trend reporting.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=pam sourcetype="cyberark:vault"
| search account_type="break_glass" OR account IN ("emergency_admin","firecall_*")
| table _time, user, account, target, action
| sort -_time
```

Understanding this SPL

**Break-Glass Account Usage** — Break-glass accounts provide emergency access and should rarely be used. Any usage requires immediate investigation and documentation.

Documented **Data sources**: PAM vault events for break-glass accounts. **App/TA** (typical add-on context): Splunk_TA_cyberark, custom alert. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: pam; **sourcetype**: cyberark:vault. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=pam, sourcetype="cyberark:vault". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Break-Glass Account Usage**): table _time, user, account, target, action
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (break-glass uses this month — target: 0), Table (usage history), Timeline (break-glass events).

## SPL

```spl
index=pam sourcetype="cyberark:vault"
| search account_type="break_glass" OR account IN ("emergency_admin","firecall_*")
| table _time, user, account, target, action
| sort -_time
```

## Visualization

Single value (break-glass uses this month — target: 0), Table (usage history), Timeline (break-glass events).

## Known False Positives

Planned maintenance, backups, or batch jobs can drive metrics outside normal bands — correlate with change management windows.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
