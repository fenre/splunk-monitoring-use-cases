---
id: "4.1.21"
title: "ALB/NLB Access Logs and 5xx Errors"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.21 · ALB/NLB Access Logs and 5xx Errors

## Description

Load balancer 5xx and target failures indicate backend or LB misconfiguration. Access logs enable traffic analysis and security forensics.

## Value

Load balancer 5xx and target failures indicate backend or LB misconfiguration. Access logs enable traffic analysis and security forensics.

## Implementation

Enable access logging for ALB/NLB to S3. Ingest via Splunk_TA_aws S3 input. Collect CloudWatch metrics (RequestCount, TargetResponseTime, HTTPCode_Target_5XX_Count). Alert on 5xx rate >1%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: S3 bucket with ALB/NLB access logs, CloudWatch LB metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable access logging for ALB/NLB to S3. Ingest via Splunk_TA_aws S3 input. Collect CloudWatch metrics (RequestCount, TargetResponseTime, HTTPCode_Target_5XX_Count). Alert on 5xx rate >1%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:elb:accesslogs" elb_status_code>=500
| stats count by target_port, elb_status_code, request_url
| sort -count
```

Understanding this SPL

**ALB/NLB Access Logs and 5xx Errors** — Load balancer 5xx and target failures indicate backend or LB misconfiguration. Access logs enable traffic analysis and security forensics.

Documented **Data sources**: S3 bucket with ALB/NLB access logs, CloudWatch LB metrics. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:elb:accesslogs. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:elb:accesslogs". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by target_port, elb_status_code, request_url** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (status, target, count), Line chart (5xx over time), Bar chart by target.

## SPL

```spl
index=aws sourcetype="aws:elb:accesslogs" elb_status_code>=500
| stats count by target_port, elb_status_code, request_url
| sort -count
```

## Visualization

Table (status, target, count), Line chart (5xx over time), Bar chart by target.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
