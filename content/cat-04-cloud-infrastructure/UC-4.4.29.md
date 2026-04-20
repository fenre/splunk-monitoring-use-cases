---
id: "4.4.29"
title: "Multi-Cloud Backup Recovery Testing"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.4.29 · Multi-Cloud Backup Recovery Testing

## Description

Untested restores fail when needed; tracking drill outcomes across AWS Backup, Azure Backup, and GCP proves RPO/RTO.

## Value

Untested restores fail when needed; tracking drill outcomes across AWS Backup, Azure Backup, and GCP proves RPO/RTO.

## Implementation

Tag restore jobs with `drill=true` in application metadata. Quarterly dashboard of success rate and restore duration percentiles. Alert on any failed table-top restore.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, Azure Backup logs, GCP Backup for GKE / Database exports.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch:events` (Backup), `sourcetype=mscs:azure:diagnostics` (Backup), `sourcetype=google:gcp:pubsub:message` (gkebackup, sqladmin).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Tag restore jobs with `drill=true` in application metadata. Quarterly dashboard of success rate and restore duration percentiles. Alert on any failed table-top restore.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
(index=aws sourcetype="aws:cloudwatch:events" detail-type="Restore Job State Change")
 OR (index=azure sourcetype="mscs:azure:diagnostics" Category="AzureBackupReport" OperationName="Restore")
 OR (index=gcp sourcetype="google:gcp:pubsub:message" "Restore" OR "restoreBackup")
| eval ok=if(match(_raw,"(?i)(FAILED|ERROR|PARTIAL)"),0,1)
| eval provider=case(index="aws","aws", index="azure","azure", index="gcp","gcp",1=1,"unknown")
| eval app_name=coalesce(detail.resourceArn, BackupItemName, resource.labels.project_id, "unknown")
| stats count(eval(ok=1)) as success, count(eval(ok=0)) as failed by app_name, provider
| where failed>0
```

Understanding this SPL

**Multi-Cloud Backup Recovery Testing** — Untested restores fail when needed; tracking drill outcomes across AWS Backup, Azure Backup, and GCP proves RPO/RTO.

Documented **Data sources**: `sourcetype=aws:cloudwatch:events` (Backup), `sourcetype=mscs:azure:diagnostics` (Backup), `sourcetype=google:gcp:pubsub:message` (gkebackup, sqladmin). **App/TA** (typical add-on context): `Splunk_TA_aws`, Azure Backup logs, GCP Backup for GKE / Database exports. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws, azure, gcp; **sourcetype**: aws:cloudwatch:events, mscs:azure:diagnostics, google:gcp:pubsub:message. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, index=azure, index=gcp, sourcetype="aws:cloudwatch:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **ok** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **provider** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **app_name** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by app_name, provider** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where failed>0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (app, provider, success/fail), Bar chart (drill outcomes by quarter), Line chart (restore duration trend).

## SPL

```spl
(index=aws sourcetype="aws:cloudwatch:events" detail-type="Restore Job State Change")
 OR (index=azure sourcetype="mscs:azure:diagnostics" Category="AzureBackupReport" OperationName="Restore")
 OR (index=gcp sourcetype="google:gcp:pubsub:message" "Restore" OR "restoreBackup")
| eval ok=if(match(_raw,"(?i)(FAILED|ERROR|PARTIAL)"),0,1)
| eval provider=case(index="aws","aws", index="azure","azure", index="gcp","gcp",1=1,"unknown")
| eval app_name=coalesce(detail.resourceArn, BackupItemName, resource.labels.project_id, "unknown")
| stats count(eval(ok=1)) as success, count(eval(ok=0)) as failed by app_name, provider
| where failed>0
```

## Visualization

Table (app, provider, success/fail), Bar chart (drill outcomes by quarter), Line chart (restore duration trend).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
