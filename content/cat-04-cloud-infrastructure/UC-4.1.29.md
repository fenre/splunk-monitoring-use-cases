---
id: "4.1.29"
title: "EC2 Spot Instance Interruption Notices"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.29 · EC2 Spot Instance Interruption Notices

## Description

Spot interruptions cause instance termination with short notice. Tracking enables graceful shutdown, workload migration, and capacity planning.

## Value

Spot interruptions cause instance termination with short notice. Tracking enables graceful shutdown, workload migration, and capacity planning.

## Implementation

Create EventBridge rule for EC2 Spot Instance Interruption Warning. Forward to SNS or Lambda for Splunk ingestion. Alert on every interruption; use for fleet metrics and hybrid/on-demand fallback decisions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch Events (EC2 Spot Instance Interruption Warning), EventBridge.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create EventBridge rule for EC2 Spot Instance Interruption Warning. Forward to SNS or Lambda for Splunk ingestion. Alert on every interruption; use for fleet metrics and hybrid/on-demand fallback decisions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="EC2 Spot Instance Interruption Warning"
| table _time detail.instance-id detail.instance-action detail.spot-instance-request-id
| sort -_time
```

Understanding this SPL

**EC2 Spot Instance Interruption Notices** — Spot interruptions cause instance termination with short notice. Tracking enables graceful shutdown, workload migration, and capacity planning.

Documented **Data sources**: CloudWatch Events (EC2 Spot Instance Interruption Warning), EventBridge. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch:events. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **EC2 Spot Instance Interruption Notices**): table _time detail.instance-id detail.instance-action detail.spot-instance-request-id
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (instance, action, time), Timeline (interruptions by AZ), Bar chart (interruptions by instance type).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="EC2 Spot Instance Interruption Warning"
| table _time detail.instance-id detail.instance-action detail.spot-instance-request-id
| sort -_time
```

## Visualization

Table (instance, action, time), Timeline (interruptions by AZ), Bar chart (interruptions by instance type).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
