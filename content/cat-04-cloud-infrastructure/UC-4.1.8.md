<!-- AUTO-GENERATED from UC-4.1.8.json — DO NOT EDIT -->

---
id: "4.1.8"
title: "GuardDuty Finding Ingestion"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.1.8 · GuardDuty Finding Ingestion

## Description

GuardDuty provides ML-powered threat detection for AWS accounts. Centralizing findings in Splunk enables correlation with other security data.

## Value

GuardDuty provides ML-powered threat detection for AWS accounts. Centralizing findings in Splunk enables correlation with other security data.

## Implementation

Enable GuardDuty in all regions. Configure CloudWatch Events rule to forward findings to an SNS topic or S3. Ingest via Splunk_TA_aws. Alert on High/Critical findings (severity ≥7).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch:guardduty`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable GuardDuty in all regions. Configure CloudWatch Events rule to forward findings to an SNS topic or S3. Ingest via Splunk_TA_aws. Alert on High/Critical findings (severity ≥7).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch:guardduty"
| spath output=severity path=detail.severity
| spath output=finding_type path=detail.type
| where severity >= 7
| table _time finding_type severity detail.title detail.description
| sort -severity
```

Understanding this SPL

**GuardDuty Finding Ingestion** — GuardDuty provides ML-powered threat detection for AWS accounts. Centralizing findings in Splunk enables correlation with other security data.

Documented **Data sources**: `sourcetype=aws:cloudwatch:guardduty`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch:guardduty. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch:guardduty". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Extracts structured paths (JSON/XML) with `spath`.
• Filters the current rows with `where severity >= 7` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **GuardDuty Finding Ingestion**): table _time finding_type severity detail.title detail.description
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table by severity, Bar chart (finding types), Trend line (findings over time), Single value.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch:guardduty"
| spath output=severity path=detail.severity
| spath output=finding_type path=detail.type
| where severity >= 7
| table _time finding_type severity detail.title detail.description
| sort -severity
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  where (match(lower(IDS_Attacks.severity), "high|critical|severe")
         OR (isnum(IDS_Attacks.severity) AND IDS_Attacks.severity >= 7))
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src span=1h
| sort -count
```

## Visualization

Table by severity, Bar chart (finding types), Trend line (findings over time), Single value.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
