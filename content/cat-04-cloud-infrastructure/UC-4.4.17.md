---
id: "4.4.17"
title: "Cloud Quota and Service Limit Utilization"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.4.17 · Cloud Quota and Service Limit Utilization

## Description

Hitting account or region quotas (e.g. EC2 instance limit, VPCs, EBS volumes) blocks provisioning and causes runtime failures. Proactive tracking supports limit increase requests.

## Value

Hitting account or region quotas (e.g. EC2 instance limit, VPCs, EBS volumes) blocks provisioning and causes runtime failures. Proactive tracking supports limit increase requests.

## Implementation

Poll Service Quotas (or equivalent) for key limits (EC2, EBS, VPC, Lambda concurrency). Ingest current usage and quota value. Alert when utilization exceeds 80%. Dashboard all quotas with trend.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, Service Quotas API, Azure quotas, GCP quotas.
• Ensure the following data sources are available: AWS Service Quotas API, Trusted Advisor (limits), Azure usage and quotas, GCP quota API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll Service Quotas (or equivalent) for key limits (EC2, EBS, VPC, Lambda concurrency). Ingest current usage and quota value. Alert when utilization exceeds 80%. Dashboard all quotas with trend.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:service_quotas"
| eval usage_pct=round(usage/value*100, 1)
| where usage_pct > 80
| table quota_name region usage value usage_pct
| sort -usage_pct
```

Understanding this SPL

**Cloud Quota and Service Limit Utilization** — Hitting account or region quotas (e.g. EC2 instance limit, VPCs, EBS volumes) blocks provisioning and causes runtime failures. Proactive tracking supports limit increase requests.

Documented **Data sources**: AWS Service Quotas API, Trusted Advisor (limits), Azure usage and quotas, GCP quota API. **App/TA** (typical add-on context): `Splunk_TA_aws`, Service Quotas API, Azure quotas, GCP quotas. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:service_quotas. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:service_quotas". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **usage_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where usage_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Cloud Quota and Service Limit Utilization**): table quota_name region usage value usage_pct
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (quota, usage %, limit), Gauge per critical quota, Bar chart (top near-limit quotas).

## SPL

```spl
index=aws sourcetype="aws:service_quotas"
| eval usage_pct=round(usage/value*100, 1)
| where usage_pct > 80
| table quota_name region usage value usage_pct
| sort -usage_pct
```

## Visualization

Table (quota, usage %, limit), Gauge per critical quota, Bar chart (top near-limit quotas).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
