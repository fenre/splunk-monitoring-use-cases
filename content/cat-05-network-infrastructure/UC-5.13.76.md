<!-- AUTO-GENERATED from UC-5.13.76.json — DO NOT EDIT -->

---
id: "5.13.76"
title: "Catalyst Center Alert to Splunk On-Call/SOAR Routing"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-5.13.76 · Catalyst Center Alert to Splunk On-Call/SOAR Routing

## Description

Routes critical Catalyst Center alerts (P1/P2 issues and severity 1-2 events) to Splunk On-Call (VictorOps) or Splunk SOAR for automated incident creation and on-call escalation.

## Value

Manual alert triage introduces delay. Automated routing to On-Call/SOAR ensures critical network issues reach the right engineer within seconds.

## Implementation

Save the SPL as an alert with the following alert actions:

**For Splunk On-Call (VictorOps):**
1. Install the Splunk On-Call (VictorOps) app for Splunk
2. Configure the alert action to create an incident with:
   - Routing key: `network-ops`
   - Message type: `CRITICAL` for P1/severity-1, `WARNING` for P2/severity-2
   - Entity ID: `catalyst-center-$deviceName$`

**For Splunk SOAR:**
1. Configure the HEC connection from Splunk to SOAR
2. Set the alert to trigger a SOAR playbook that:
   - Creates a ServiceNow incident
   - Pages the network on-call team
   - Runs initial diagnostics (ping, show commands via Catalyst Center Command Runner API)

Schedule the alert to run every 5 minutes with a 5-minute window.

## Detailed Implementation

Prerequisites
• UC-5.13.23 (issues and/or event notifications) with `cisco:dnac:issue` and optional `cisco:dnac:event:notification` on `index=catalyst`.
• Splunk On-Call app or SOAR app installed; credentials and routing keys provisioned.

Step 1 — Field validation
- Sample: `sourcetype="cisco:dnac:issue"` — confirm `priority`, `status`, `name`, `deviceName`, `siteId`.
- Sample: `sourcetype="cisco:dnac:event:notification"` — confirm `eventSeverity`, `description` (values 1–4 or string per your TA); adjust `eventSeverity<=2` if your schema uses strings.

Step 2 — Saved search / alert
- **Schedule:** every 5 minutes, **time range:** last 5 minutes, **trigger:** number of results > 0.
- **Throttle / dedup:** use `dedup` on `issueId` or `eventId` or use ITSI/SOAR-side deduplication to avoid storms during flapping conditions.

Step 3 — On-Call action
- Map `severity` token to VictorOps message type; pass `routing_key=network-ops` (or per-team keys by `siteId` via `lookup`).
- Set **Entity** to `catalyst-center-$deviceName$` for merge in VictorOps timeline.

Step 4 — SOAR playbook (optional)
- Ingest alert via HEC with JSON containing `alert_source`, `severity`, `deviceName`, `siteId`.
- Playbook steps: create ticket, page, call **Catalyst Center Command Runner** `POST /dna/intent/api/v1/network-device-poller/cli/read` (see current API docs for path/auth) with approved read-only commands — only after change-control approval.

Step 5 — Baseline SPL

```spl
index=catalyst ((sourcetype="cisco:dnac:issue" (priority="P1" OR priority="P2") status!="RESOLVED") OR (sourcetype="cisco:dnac:event:notification" eventSeverity<=2)) | eval alert_source=case(sourcetype="cisco:dnac:issue","Assurance Issue: ".name, sourcetype="cisco:dnac:event:notification","Event: ".description, 1==1,"Unknown") | eval severity=case(priority="P1" OR eventSeverity=1,"critical", priority="P2" OR eventSeverity=2,"high", 1==1,"medium") | table _time alert_source severity deviceName siteId
```

## SPL

```spl
index=catalyst ((sourcetype="cisco:dnac:issue" (priority="P1" OR priority="P2") status!="RESOLVED") OR (sourcetype="cisco:dnac:event:notification" eventSeverity<=2)) | eval alert_source=case(sourcetype="cisco:dnac:issue","Assurance Issue: ".name, sourcetype="cisco:dnac:event:notification","Event: ".description, 1==1,"Unknown") | eval severity=case(priority="P1" OR eventSeverity=1,"critical", priority="P2" OR eventSeverity=2,"high", 1==1,"medium") | table _time alert_source severity deviceName siteId
```

## Visualization

Alert-driven: no primary chart; optional supporting table in a runbook dashboard showing last 20 routed events with dedup key on deviceName+issueId.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
