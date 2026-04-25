<!-- AUTO-GENERATED from UC-4.1.31.json — DO NOT EDIT -->

---
id: "4.1.31"
title: "CloudWatch Alarm State Changes"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.1.31 · CloudWatch Alarm State Changes

## Description

Alarm state transitions (OK → ALARM, INSUFFICIENT_DATA) provide a consolidated view of metric-based issues. Centralizing in Splunk enables correlation with other data.

## Value

Alarm state transitions (OK → ALARM, INSUFFICIENT_DATA) provide a consolidated view of metric-based issues. Centralizing in Splunk enables correlation with other data.

## Implementation

Create EventBridge rule for CloudWatch Alarm State Change. Send to SNS topic; ingest via Splunk_TA_aws or HEC. Filter for state=ALARM. Correlate alarm name with resource tags for ownership.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch Events (Alarm state change), SNS subscription.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create EventBridge rule for CloudWatch Alarm State Change. Send to SNS topic; ingest via Splunk_TA_aws or HEC. Filter for state=ALARM. Correlate alarm name with resource tags for ownership.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="CloudWatch Alarm State Change" detail.state.value="ALARM"
| table _time detail.alarmName detail.state.value detail.newStateReason
| sort -_time
```

Understanding this SPL

**CloudWatch Alarm State Changes** — Alarm state transitions (OK → ALARM, INSUFFICIENT_DATA) provide a consolidated view of metric-based issues. Centralizing in Splunk enables correlation with other data.

Documented **Data sources**: CloudWatch Events (Alarm state change), SNS subscription. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch:events. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **CloudWatch Alarm State Changes**): table _time detail.alarmName detail.state.value detail.newStateReason
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (alarm, state, reason), Timeline (alarms over time), Single value (active alarms).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="CloudWatch Alarm State Change" detail.state.value="ALARM"
| table _time detail.alarmName detail.state.value detail.newStateReason
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Alerts.Alerts
  where match(Alerts.app, "(?i)cloudwatch|metric") OR match(Alerts.alert_name, "(?i)alarm|threshold")
  by Alerts.severity Alerts.alert_name span=1h
| sort -count
```

## Visualization

Table (alarm, state, reason), Timeline (alarms over time), Single value (active alarms).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
