<!-- AUTO-GENERATED from UC-2.1.46.json — DO NOT EDIT -->

---
id: "2.1.46"
title: "vCenter Alarm Acknowledgment Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.46 · vCenter Alarm Acknowledgment Tracking

## Description

Track alarms that remain unacknowledged for extended periods. Unacknowledged alarms indicate ignored issues — either operational gaps or alarm fatigue. Ensures critical alerts receive follow-up and supports SLA tracking for incident response.

## Value

Track alarms that remain unacknowledged for extended periods. Unacknowledged alarms indicate ignored issues — either operational gaps or alarm fatigue. Ensures critical alerts receive follow-up and supports SLA tracking for incident response.

## Implementation

Splunk_TA_vmware collects AlarmStatusChangedEvent. Parse acknowledged field if present; otherwise infer from event sequence. Alert when red/yellow alarms remain unacknowledged >4 hours. Maintain lookup of alarm ownership for escalation. Correlate with incident tickets.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:events` (AlarmStatusChangedEvent).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Splunk_TA_vmware collects AlarmStatusChangedEvent. Parse acknowledged field if present; otherwise infer from event sequence. Alert when red/yellow alarms remain unacknowledged >4 hours. Maintain lookup of alarm ownership for escalation. Correlate with incident tickets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:events" event_type="AlarmStatusChangedEvent"
| eval alarm_id = coalesce(alarm, alarm_name)
| stats latest(_time) as last_change, latest(new_status) as status, latest(acknowledged) as ack, latest(alarm_name) as alarm_name, latest(entity) as entity by alarm_id
| where status="red" OR status="yellow"
| eval hours_unack = round((now() - last_change) / 3600, 1)
| where ack!="true" AND hours_unack > 4
| sort -hours_unack
| table alarm_name, entity, status, last_change, hours_unack, ack
```

Understanding this SPL

**vCenter Alarm Acknowledgment Tracking** — Track alarms that remain unacknowledged for extended periods. Unacknowledged alarms indicate ignored issues — either operational gaps or alarm fatigue. Ensures critical alerts receive follow-up and supports SLA tracking for incident response.

Documented **Data sources**: `sourcetype=vmware:events` (AlarmStatusChangedEvent). **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **alarm_id** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by alarm_id** so each row reflects one combination of those dimensions.
• Filters the current rows with `where status="red" OR status="yellow"` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **hours_unack** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where ack!="true" AND hours_unack > 4` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **vCenter Alarm Acknowledgment Tracking**): table alarm_name, entity, status, last_change, hours_unack, ack

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (unacknowledged alarms, age), Timeline (alarm state changes), Single value (count unacknowledged >4h).

## SPL

```spl
index=vmware sourcetype="vmware:events" event_type="AlarmStatusChangedEvent"
| eval alarm_id = coalesce(alarm, alarm_name)
| stats latest(_time) as last_change, latest(new_status) as status, latest(acknowledged) as ack, latest(alarm_name) as alarm_name, latest(entity) as entity by alarm_id
| where status="red" OR status="yellow"
| eval hours_unack = round((now() - last_change) / 3600, 1)
| where ack!="true" AND hours_unack > 4
| sort -hours_unack
| table alarm_name, entity, status, last_change, hours_unack, ack
```

## Visualization

Table (unacknowledged alarms, age), Timeline (alarm state changes), Single value (count unacknowledged >4h).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
