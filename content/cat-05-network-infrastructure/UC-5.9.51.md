<!-- AUTO-GENERATED from UC-5.9.51.json — DO NOT EDIT -->

---
id: "5.9.51"
title: "Splunk On-Call Incident Routing"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.51 · Splunk On-Call Incident Routing

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Run &middot; **Status:** Verified

*We automatically wake up the on-call engineer when a critical network problem is detected, so important issues get fixed at 3 AM instead of waiting until someone checks their dashboard in the morning.*

---

## Description

Routes critical ThousandEyes alerts to Splunk On-Call for automated incident creation and on-call engineer notification. Bridges the gap between ThousandEyes network alerting and your incident management workflow, ensuring network issues page the right team at the right time.

## Value

ThousandEyes alerts in Splunk are only useful if someone acts on them. Most NOC teams use Splunk On-Call (or PagerDuty) for incident management. This UC ensures critical ThousandEyes alerts automatically create incidents in On-Call, which pages the on-call engineer via phone/SMS/push notification. Without this integration, ThousandEyes alerts sit in a Splunk dashboard that nobody is watching at 3 AM. With it, a BGP hijack detection (UC-5.9.11) or a critical web application outage (UC-5.9.34) wakes up the right person immediately.

## Implementation

Create a Splunk saved search that triggers on critical ThousandEyes alerts and uses the VictorOps/On-Call alert action to create incidents. Map ThousandEyes alert severity to On-Call incident severity.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.19 apply — Alerts Stream input configured (HEC-pushed via OTel), `stream_index` macro pointing to `index=thousandeyes_metrics`.
- **Splunk On-Call (formerly VictorOps) integration configured.** Install the Splunk On-Call alert action from Splunkbase. In Splunk: **Settings → Alert Actions** — verify "VictorOps" or "Splunk On-Call" appears. Configure the integration with your Splunk On-Call API key and REST endpoint URL.
  - If using Splunk On-Call Cloud, the REST endpoint is: `https://alert.victorops.com/integrations/generic/20131114/alert/<api_key>/<routing_key>`.
  - If using PagerDuty instead of Splunk On-Call, install the PagerDuty alert action and substitute PagerDuty configuration in the steps below.
- **On-Call routing keys defined.** In Splunk On-Call: **Settings → Routing Keys** → create routing keys that map ThousandEyes alert categories to the correct on-call team:
  - `thousandeyes-critical` → Network Operations on-call rotation (for critical severity alerts).
  - `thousandeyes-network` → Network team (for latency, loss, jitter alerts).
  - `thousandeyes-dns` → DNS/infrastructure team (for DNS resolution failures).
  - `thousandeyes-web` → Application/SRE team (for HTTP, Page Load, API test failures).
  Each routing key should have an escalation policy: page primary on-call, escalate to secondary after 15 minutes if unacknowledged.
- **On-Call schedules configured.** Ensure on-call schedules exist for each team that will receive ThousandEyes alerts. Test that on-call members can receive notifications (push, SMS, phone call).
- **ThousandEyes alert rules configured.** This UC routes ThousandEyes alerts to Splunk On-Call. The alert CONTENT comes from ThousandEyes alert rules (configured in ThousandEyes UI). If alert rules are too sensitive, On-Call will be overwhelmed with pages. Tune ThousandEyes alert rules first (UC-5.9.19).
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics` (for alert data via HEC). User needs `schedule_search` capability to create scheduled alerts.

### Step 1 — Configure the alert action
Create a saved search with an On-Call alert action. This saved search runs on a schedule, detects active critical ThousandEyes alerts, and forwards them to Splunk On-Call for incident management.

**Saved search — Critical ThousandEyes Alert to On-Call:**
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" severity="critical" state="active"
| dedup alert.rule.name, alert.test.name
| table _time, alert.rule.name, alert.test.name, severity, thousandeyes.permalink
```

**Understanding this SPL**

`sourcetype="cisco:thousandeyes:alerts"` — filters to ThousandEyes alert data specifically (not metrics or events).

`severity="critical" state="active"` — only routes CRITICAL and ACTIVE alerts to On-Call. This is the key noise filter. Do NOT route all severities to On-Call — that causes alert fatigue and page storms.

`dedup alert.rule.name, alert.test.name` — prevents duplicate pages for the same alert rule + test combination. Without this, a single persistent alert would page the on-call every 5 minutes.

`thousandeyes.permalink` — the ThousandEyes URL for the alert. This is the MOST important field in the On-Call incident — it gives the on-call engineer direct access to the ThousandEyes UI with full context (test results, timeline, path visualization).

**Schedule:** cron `*/5 * * * *`, time range `-10m to now`. Every 5 minutes, check the last 10 minutes for new critical alerts. The overlap (10-minute window with 5-minute schedule) ensures no alerts are missed.

**Alert condition:** Number of results > 0.

**Alert action configuration (Splunk UI — Settings → Searches, Reports, and Alerts → New Alert):**
- Alert action: VictorOps / Splunk On-Call.
- Routing key: `thousandeyes-critical`.
- Message type: CRITICAL.
- Entity ID: `ThousandEyes-$result.alert.rule.name$-$result.alert.test.name$` (unique identifier for dedup in On-Call).
- Entity display name: `$result.alert.rule.name$`.
- State message: `ThousandEyes CRITICAL alert: $result.alert.test.name$ triggered rule "$result.alert.rule.name$". Investigate: $result.thousandeyes.permalink$`.

**Additional saved searches for tiered routing (optional but recommended):**

**Network alerts to network team:**
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" (severity="major" OR severity="critical") state="active"
| search alert.rule.name="*latency*" OR alert.rule.name="*loss*" OR alert.rule.name="*jitter*" OR alert.rule.name="*network*"
| dedup alert.rule.name, alert.test.name
| table _time, alert.rule.name, alert.test.name, severity, thousandeyes.permalink
```
Routing key: `thousandeyes-network`.

**Web/HTTP alerts to application team:**
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" (severity="major" OR severity="critical") state="active"
| search alert.rule.name="*http*" OR alert.rule.name="*page load*" OR alert.rule.name="*transaction*" OR alert.rule.name="*api*"
| dedup alert.rule.name, alert.test.name
| table _time, alert.rule.name, alert.test.name, severity, thousandeyes.permalink
```
Routing key: `thousandeyes-web`.

### Step 2 — Configure On-Call routing
In Splunk On-Call (app.victorops.com):

**2a. Escalation policy for `thousandeyes-critical`:**
1. Step 1: Page the primary on-call engineer for the network team rotation.
2. Wait 15 minutes. If unacknowledged:
3. Step 2: Page the secondary on-call AND the team lead.
4. Wait 15 minutes. If still unacknowledged:
5. Step 3: Page the entire network team and the NOC manager.

**2b. On-Call schedules:**
- Map each routing key to the appropriate on-call rotation.
- Configure notification methods: push notification first, SMS after 2 minutes, phone call after 5 minutes.

**2c. Transmogrifier rules (optional):**
In On-Call, create transmogrifier rules to enrich ThousandEyes incidents:
- Add annotation: "ThousandEyes alert — click permalink for full context."
- Set incident priority based on the test name (production tests = P1, staging tests = P3).

### Step 3 — Validate
(a) **End-to-end test.** Temporarily lower a ThousandEyes alert threshold to trigger a critical alert (e.g., set latency threshold to 1 ms for a test that normally shows 50 ms). Wait for the Splunk saved search to fire (up to 10 minutes). Verify:
  1. Splunk saved search triggers (check **Activity → Triggered Alerts**).
  2. On-Call receives the incident (check On-Call timeline).
  3. On-call engineer receives notification (push/SMS/phone).
  4. Incident contains the ThousandEyes permalink.
Reset the threshold immediately after testing.

(b) **Dedup verification.** Ensure the same alert doesn't create duplicate On-Call incidents. The `entity_id` field in the alert action should deduplicate: same `alert.rule.name` + `alert.test.name` = same incident (updated, not duplicated).

(c) **Escalation test.** Let a test incident go unacknowledged for 15 minutes to verify the escalation policy works correctly.

(d) **Alert suppression during maintenance.** Verify that you can suppress On-Call pages during planned maintenance (e.g., On-Call's maintenance mode or Splunk's alert suppression).

(e) **Routing key validation.** For each routing key (`thousandeyes-critical`, `thousandeyes-network`, `thousandeyes-web`), verify it routes to the correct on-call rotation by creating a test incident.

### Step 4 — Operationalize
**Incident response flow** (documented in On-Call runbook and team wiki):
1. **On-Call pages the on-call engineer.** Notification includes: alert rule name, test name, severity, and ThousandEyes permalink.
2. **Engineer acknowledges within 15 minutes.** Acknowledgement stops the escalation timer. If unacknowledged, escalation policy pages the next level.
3. **Engineer clicks the ThousandEyes permalink.** This opens the ThousandEyes UI showing the full alert context: what triggered, when, which agents are affected, and the current state.
4. **Engineer investigates using the relevant UC.** Based on the alert type:
   - Latency/loss/jitter alert → follow UC-5.9.1 (latency), UC-5.9.2 (loss), UC-5.9.3 (jitter) runbooks.
   - HTTP availability alert → follow UC-5.9.34 runbook.
   - DNS alert → follow UC-5.9.5/5.9.6 runbooks.
   - Page Load/Transaction alert → follow UC-5.9.37/5.9.41 runbooks.
5. **Engineer resolves or escalates.** If resolved, close the On-Call incident with resolution notes. If escalation needed, use On-Call's reroute feature to send to the appropriate team.

**On-Call incident quality metrics (monthly review):**
- Total ThousandEyes incidents created.
- Mean time to acknowledge (MTTA).
- Mean time to resolve (MTTR).
- False positive rate (incidents that required no action).
- Escalation rate (incidents that escalated beyond primary on-call).

**Runbook** (owner: Splunk admin / NOC manager):
1. **On-Call incidents with missing fields** — Ensure the Splunk search output includes all fields referenced in the alert action (`$result.field_name$`). The most common issue is `thousandeyes.permalink` being null — verify the ThousandEyes Alerts Stream includes permalink in the data.
2. **Too many incidents (alert storm).** — (a) Raise the severity filter from `severity="critical"` to also exclude `severity="major"`. (b) Add stronger dedup: `dedup alert.test.name` (one incident per test, not per rule). (c) Add a duration filter: `| where duration_seconds > 300` (only page for alerts lasting > 5 minutes). (d) Review ThousandEyes alert rules — overly sensitive rules cause On-Call overload.
3. **No incidents ever created.** — (a) Verify the Splunk saved search runs: **Settings → Searches, Reports, and Alerts** → find the search → check "Last Run" and "Next Scheduled Run". (b) Verify the VictorOps alert action is configured correctly (API key, routing key). (c) Manually run the search to check if it returns results.

### Step 5 — Troubleshooting

- **No incidents created in On-Call** — (a) Check the Splunk saved search: does it return results when run manually? If no, the alert data may not be flowing (check UC-5.9.19). (b) Check the alert action: is VictorOps/On-Call configured with the correct API key? (c) Check the routing key: does it exist in On-Call? A typo in the routing key silently drops the incident.

- **Too many incidents (alert fatigue)** — Tune the search: (a) only `severity="critical"` (not major/minor). (b) Add `| where duration_seconds > 300` to filter transient spikes. (c) Increase `dedup` scope. (d) Use On-Call's transmogrifier to auto-acknowledge known false positives.

- **Incidents missing the ThousandEyes permalink** — The `thousandeyes.permalink` field may be named differently in your app version. Run `| fieldsummary` on alert data to find the correct field name. Common alternatives: `permalink`, `alert.permalink`, `thousandeyes.alert.permalink`.

- **On-Call shows incident but nobody gets notified** — (a) Check the on-call schedule: is someone assigned for the current time? (b) Check the assigned person's notification settings (push, SMS, phone). (c) Check On-Call's notification log for delivery failures.

- **All common troubleshooting** — See UC-5.9.19 Step 5 for alert data issues, and UC-5.9.1 Step 5 for general app troubleshooting.

## SPL

```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" severity="critical" state="active"
| dedup alert.rule.name, alert.test.name
| table _time, alert.rule.name, alert.test.name, severity, thousandeyes.permalink
| sort -_time
```

## Visualization

(1) Table: recent incidents routed to On-Call. (2) Timeline: incident creation timestamps. (3) Single value: active incidents from ThousandEyes alerts.

## Known False Positives

**Alert noise → incident noise.** If ThousandEyes alert rules aren't well-tuned (UC-5.9.46), noisy alerts become noisy incidents, causing on-call fatigue. Tune ThousandEyes alerting BEFORE routing to On-Call.

**Duplicate incidents.** Multiple ThousandEyes agents may fire the same alert for the same network issue, creating multiple On-Call incidents. Use dedup in the Splunk search or incident deduplication rules in On-Call.

**Incidents for transient issues.** Brief network blips may trigger alerts that clear within minutes. Consider adding a delay or requiring consecutive alert rounds before creating an On-Call incident.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [Splunk On-Call (VictorOps) alert action](https://docs.splunk.com/Documentation/OnCall)
- [Splunk alert actions documentation](https://docs.splunk.com/Documentation/Splunk/latest/Alert/Setupalertactions)
