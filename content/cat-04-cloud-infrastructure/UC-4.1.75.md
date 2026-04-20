---
id: "4.1.75"
title: "AWS Backup Job Status"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.1.75 · AWS Backup Job Status

## Description

Centralized backup vault jobs must complete on schedule; failed jobs leave RPO gaps across EC2, EFS, and databases.

## Value

Centralized backup vault jobs must complete on schedule; failed jobs leave RPO gaps across EC2, EFS, and databases.

## Implementation

Parse job states COMPLETED, FAILED, EXPIRED. Alert on FAILED. Track partial completion for large resources. Cross-check with UC-4.4.29 restore drills for end-to-end assurance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch:events` (Backup Job State Change), Backup notifications.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse job states COMPLETED, FAILED, EXPIRED. Alert on FAILED. Track partial completion for large resources. Cross-check with UC-4.4.29 restore drills for end-to-end assurance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="Backup Job State Change"
| eval ok=if(detail.state="COMPLETED",1,0)
| stats count(eval(ok=0)) as failed, count as total by detail.backupVaultArn, detail.resourceArn
| where failed>0
```

Understanding this SPL

**AWS Backup Job Status** — Centralized backup vault jobs must complete on schedule; failed jobs leave RPO gaps across EC2, EFS, and databases.

Documented **Data sources**: `sourcetype=aws:cloudwatch:events` (Backup Job State Change), Backup notifications. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **ok** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by detail.backupVaultArn, detail.resourceArn** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where failed>0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (vault, resource, status), Timeline (job outcomes), Single value (failed jobs 24h).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="Backup Job State Change"
| eval ok=if(detail.state="COMPLETED",1,0)
| stats count(eval(ok=0)) as failed, count as total by detail.backupVaultArn, detail.resourceArn
| where failed>0
```

## Visualization

Table (vault, resource, status), Timeline (job outcomes), Single value (failed jobs 24h).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
