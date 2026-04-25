<!-- AUTO-GENERATED from UC-4.1.52.json — DO NOT EDIT -->

---
id: "4.1.52"
title: "ECR Image Scan Findings"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.52 · ECR Image Scan Findings

## Description

ECR image scan finds CVEs in container images. Critical/high findings in production images require immediate remediation or rollback.

## Value

ECR image scan finds CVEs in container images. Critical/high findings in production images require immediate remediation or rollback.

## Implementation

Enable ECR image scanning (enhanced or basic). Send scan completion events to EventBridge; forward to Splunk. Alert on CRITICAL/HIGH in repos tagged as production. Block deployment in pipeline when findings exceed threshold.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: ECR scan findings via EventBridge (ECR Image Scan), or Security Hub.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable ECR image scanning (enhanced or basic). Send scan completion events to EventBridge; forward to Splunk. Alert on CRITICAL/HIGH in repos tagged as production. Block deployment in pipeline when findings exceed threshold.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:ecr:scan" severity="CRITICAL" OR severity="HIGH"
| table _time repositoryName imageTag severity findingName
| sort -_time
```

Understanding this SPL

**ECR Image Scan Findings** — ECR image scan finds CVEs in container images. Critical/high findings in production images require immediate remediation or rollback.

Documented **Data sources**: ECR scan findings via EventBridge (ECR Image Scan), or Security Hub. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:ecr:scan. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:ecr:scan". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **ECR Image Scan Findings**): table _time repositoryName imageTag severity findingName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (repo, tag, severity, CVE), Bar chart (findings by repo), Trend line (findings over time).

## SPL

```spl
index=aws sourcetype="aws:ecr:scan" severity="CRITICAL" OR severity="HIGH"
| table _time repositoryName imageTag severity findingName
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  where match(lower(IDS_Attacks.severity), "high|critical")
  by IDS_Attacks.signature IDS_Attacks.src span=1d
| sort -count
```

## Visualization

Table (repo, tag, severity, CVE), Bar chart (findings by repo), Trend line (findings over time).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
