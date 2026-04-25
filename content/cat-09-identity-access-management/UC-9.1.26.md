<!-- AUTO-GENERATED from UC-9.1.26.json — DO NOT EDIT -->

---
id: "9.1.26"
title: "Certificate Template Abuse (ESC Attacks)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.26 · Certificate Template Abuse (ESC Attacks)

## Description

Misconfigured templates (ESC1/ESC8) allow domain escalation via certificate requests. Monitoring issuance and template edits reduces exposure.

## Value

Misconfigured templates (ESC1/ESC8) allow domain escalation via certificate requests. Monitoring issuance and template edits reduces exposure.

## Implementation

Enable CA and template auditing. Maintain lookup mapping template OIDs to ESC categories (per SpecterOps research). Alert on enrollment to high-risk templates and on template ACL/schema changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, AD CS logs.
• Ensure the following data sources are available: Certificate Services (4886, 4887, 4888), AD CS template change auditing (5136 on `CN=Certificate Templates`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable CA and template auditing. Maintain lookup mapping template OIDs to ESC categories (per SpecterOps research). Alert on enrollment to high-risk templates and on template ACL/schema changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4886
| search Requester!="" Template_OID=*
| lookup cert_template_risk Template_OID OUTPUT risk_esc
| where risk_esc IN ("ESC1","ESC8")
| table _time, Requester, Template_OID, risk_esc, ComputerName
```

Understanding this SPL

**Certificate Template Abuse (ESC Attacks)** — Misconfigured templates (ESC1/ESC8) allow domain escalation via certificate requests. Monitoring issuance and template edits reduces exposure.

Documented **Data sources**: Certificate Services (4886, 4887, 4888), AD CS template change auditing (5136 on `CN=Certificate Templates`). **App/TA** (typical add-on context): `Splunk_TA_windows`, AD CS logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where risk_esc IN ("ESC1","ESC8")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Certificate Template Abuse (ESC Attacks)**): table _time, Requester, Template_OID, risk_esc, ComputerName


Step 3 — Validate
Compare with Event Viewer on domain controllers (or exported Security logs) and with Active Directory Users and Computers for the same objects and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (risky enrollments), Bar chart (requests by template), Timeline.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4886
| search Requester!="" Template_OID=*
| lookup cert_template_risk Template_OID OUTPUT risk_esc
| where risk_esc IN ("ESC1","ESC8")
| table _time, Requester, Template_OID, risk_esc, ComputerName
```

## Visualization

Table (risky enrollments), Bar chart (requests by template), Timeline.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
