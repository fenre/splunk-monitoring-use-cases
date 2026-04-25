<!-- AUTO-GENERATED from UC-4.1.60.json — DO NOT EDIT -->

---
id: "4.1.60"
title: "Security Hub Alert Aggregation"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.60 · Security Hub Alert Aggregation

## Description

Security Hub rolls up Config, GuardDuty, Inspector, and partner findings; aggregating by account and severity prioritizes remediation queues.

## Value

Security Hub rolls up Config, GuardDuty, Inspector, and partner findings; aggregating by account and severity prioritizes remediation queues.

## Implementation

Send Security Hub custom actions or EventBridge rules to Firehose/HEC. Normalize `Severity` and `ComplianceStatus`. Auto-ticket CRITICAL/HIGH. Deduplicate by finding ID across updates. Feed executive dashboards with counts by standard (CIS, PCI).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:firehose` or `sourcetype=aws:cloudwatch:events` (Security Hub findings), EventBridge to Splunk.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Send Security Hub custom actions or EventBridge rules to Firehose/HEC. Normalize `Severity` and `ComplianceStatus`. Auto-ticket CRITICAL/HIGH. Deduplicate by finding ID across updates. Feed executive dashboards with counts by standard (CIS, PCI).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="Security Hub Findings - Imported"
| spath path=detail.findings{}
| mvexpand detail.findings{} limit=500
| spath input=detail.findings{} output=sev path=Severity.Label
| spath input=detail.findings{} output=title path=Title
| stats count by sev, title, account
| sort -count
```

Understanding this SPL

**Security Hub Alert Aggregation** — Security Hub rolls up Config, GuardDuty, Inspector, and partner findings; aggregating by account and severity prioritizes remediation queues.

Documented **Data sources**: `sourcetype=aws:firehose` or `sourcetype=aws:cloudwatch:events` (Security Hub findings), EventBridge to Splunk. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
• Extracts structured paths (JSON/XML) with `spath`.
• Extracts structured paths (JSON/XML) with `spath`.
• `stats` rolls up events into metrics; results are split **by sev, title, account** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Alerts.Alerts
  where match(Alerts.app, "(?i)security|hub|firehose|findings")
  by Alerts.severity Alerts.signature span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Security Hub Alert Aggregation** — Security Hub rolls up Config, GuardDuty, Inspector, and partner findings; aggregating by account and severity prioritizes remediation queues.

Documented **Data sources**: `sourcetype=aws:firehose` or `sourcetype=aws:cloudwatch:events` (Security Hub findings), EventBridge to Splunk. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Intrusion_Detection.IDS_Attacks` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (findings by severity), Table (title, account, count), Single value (open critical).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="Security Hub Findings - Imported"
| spath path=detail.findings{}
| mvexpand detail.findings{} limit=500
| spath input=detail.findings{} output=sev path=Severity.Label
| spath input=detail.findings{} output=title path=Title
| stats count by sev, title, account
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Alerts.Alerts
  where match(Alerts.app, "(?i)security|hub|firehose|findings")
  by Alerts.severity Alerts.signature span=1h
| sort -count
```

## Visualization

Bar chart (findings by severity), Table (title, account, count), Single value (open critical).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
