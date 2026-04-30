<!-- AUTO-GENERATED from UC-5.13.67.json — DO NOT EDIT -->

---
id: "5.13.67"
title: "Event Notification Correlation with TA Poll Data"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.67 · Event Notification Correlation with TA Poll Data

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Operational, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*We cross-check the real-time alerts against the regular polling data to make sure nothing is falling through the cracks between the two systems. This helps your team act on facts instead of guesses.*

---

## Description

Correlates real-time webhook event notifications with the TA's polled issue data to verify comprehensive coverage and identify events that only appear in one data stream.

## Value

Running both push (webhook) and pull (TA polling) channels provides defense-in-depth. Correlation validates that both pipelines are capturing the same events.

## Implementation

**Push path:** HEC to `index=catalyst` `sourcetype=cisco:dnac:event:notification` (UC-5.13.64). **Pull path:** TA `issue` input → `cisco:dnac:issue` (UC-5.13.21), Intent API `GET /dna/intent/api/v1/issues`.

**Correlation key:** The SPL assumes a shared identifier `eventId` on webhook events can join to `issueId` in TA issue events (`| rename issueId as eventId`). If your Catalyst Center payload uses a different name (`id`, `eventUuid`), update the `join` and `rename` to match. If no stable shared ID exists, use secondary correlation: `last(deviceId) + strftime` window or `left` time-based join within ±5m — that alternative is not in the base SPL here.

**HEC setup:** Webhook to `https://<splunk>:8088/services/collector/event`, `Authorization: Splunk <HEC-token>`, `sourcetype=cisco:dnac:event:notification`.

## Detailed Implementation

### Prerequisites
- UC-5.13.64 complete: `cisco:dnac:event:notification` events arriving via HEC webhook.
- TA-polled data flowing: `cisco:dnac:issue` or other TA-polled sourcetypes available in `index=catalyst`.
- Both data paths covering the same Catalyst Center instance (same cluster of devices).
- Understand the timing difference: event notifications arrive in real-time; TA poll data arrives on the configured interval (default 900 seconds / 15 minutes).

### Step 1 — Configure data collection
This UC does not require additional data collection — it correlates two existing data sources:
- **Event notifications:** `sourcetype=cisco:dnac:event:notification` — delivered in real-time via webhook.
- **TA poll data:** `sourcetype=cisco:dnac:issue` (or `cisco:dnac:devicehealth`, `cisco:dnac:compliance`, etc.) — polled at 900-second intervals.

Correlation challenge: the two data paths have fundamentally different timing characteristics. An event notification may arrive 5-15 minutes before the TA polls the corresponding issue. Time-based joins must account for this gap.

Key fields for correlation:
- Event notification: `eventType`, `eventSeverity`, `timestamp`, `description`, `instanceId`.
- TA poll data (issues): `name`, `priority`, `status`, `deviceId`, `issueId`.
- Correlation: `eventType` ↔ `name` (partial match), or by `deviceName`/`deviceId` with a time window.

### Step 2 — Create the search and alert

```spl
index=catalyst sourcetype="cisco:dnac:event:notification"
| eval source_type="webhook"
| append [search index=catalyst sourcetype="cisco:dnac:issue" | eval source_type="ta_poll"]
| bin _time span=15m
| stats count(eval(source_type="webhook")) as webhook_count count(eval(source_type="ta_poll")) as poll_count values(source_type) as data_sources by _time
| eval coverage=case(webhook_count>0 AND poll_count>0, "Both", webhook_count>0, "Webhook Only", poll_count>0, "Poll Only", 1==1, "Gap")
| where coverage!="Both"
| sort _time
```

#### Understanding this SPL:
- **`append`**: Combines event notification and TA poll data into a single result set. Each event is tagged with its `source_type`.
- **`bin _time span=15m`**: Aligns both data sources to 15-minute windows matching the TA poll interval. This is the minimum resolution for meaningful correlation.
- **`stats count(eval(...))`**: Counts events from each source per time window. Both counts should be >0 in each window if both data paths are healthy.
- **`coverage=case(...)`**: Identifies windows where only one data source has events ("Webhook Only" or "Poll Only") or neither ("Gap"). "Both" indicates healthy dual-source coverage.
- **`where coverage!="Both"`**: Surfaces time windows with incomplete coverage for investigation.

### Step 3 — Validate
- **Normal operation:** Over a 24-hour period, the majority of 15-minute windows should show "Both" coverage. "Webhook Only" windows are expected immediately after a network event (before the TA polls). "Poll Only" may occur during quiet periods with no webhook-triggering events.
- **Cross-reference:** Pick a specific network event (e.g., device going offline) and verify it appears in both the event notification and the TA issue data. The event notification `timestamp` should precede the TA issue `_time` by 0-15 minutes.

### Step 4 — Operationalize
- **Dashboard:** Stacked timechart showing webhook vs poll event counts per 15-minute window. Add a single-value tile for "Coverage Rate" (percentage of windows with "Both" sources).
- **Alert:** Trigger when 4+ consecutive 15-minute windows show "Webhook Only" or "Poll Only" — this indicates a sustained failure in one data path.
- **Post-incident analysis:** Compare event notification arrival time with TA poll detection time to quantify the alerting speed improvement from webhooks.

### Step 5 — Troubleshoot
- **All windows show "Webhook Only":** The TA is not collecting data. Check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors. Verify the TA modular inputs are enabled and the API credentials are valid.
- **All windows show "Poll Only":** The webhook is not delivering events. Check Catalyst Center webhook destination health and HEC endpoint availability (see UC-5.13.66).
- **Correlation mismatch:** Event notification `eventType` names don't align with TA issue `name` values. The correlation is by device/time, not by event type mapping. Use `| bin _time span=15m` on both sources and correlate by `deviceName` or `managementIpAddress`.
- **Time window too narrow:** If the TA poll interval is >900s (e.g., 1800s for some inputs), increase the `bin span` to match.
- **No event notification events arriving:** verify the HEC token is enabled and the webhook destination is configured in Catalyst Center; check for endpoint timeout or API error in Splunk HEC logs.

Additional operational context for Event Notification Correlation with TA Poll Data:

For month-over-month comparison:
- Export the primary search results monthly as CSV to a `catalyst_monthly_snapshots` directory. Compare current month vs previous month to identify trends, improvements, and regressions.
- Track the key metric from this UC over 90 days with `| timechart span=1w` for the quarterly operations review.

For SLA alignment:
- Define the acceptable threshold for this UC's primary metric in your SLA documentation.
- Schedule a weekly check against the SLA target. Breaches should generate tickets in your ITSM with a link to this UC's dashboard panel for investigation context.

Cross-reference with related UCs:
- When this UC flags an issue, always cross-reference with UC-5.13.1 (Device Health) and UC-5.13.16 (Network Health) to assess the broader impact.
- For compliance-related findings, connect to UC-5.13.28-33 for the compliance posture context.
- For security-related findings, connect to UC-5.13.34-39 for PSIRT advisory exposure.

Runbook integration:
- Document the response procedure for each alert from this UC in your operations runbook.
- Include: who to contact, what to check first, typical root causes, and escalation criteria.
- Review and update the runbook quarterly based on actual alert outcomes (was the runbook helpful? did it miss common scenarios?).

Additional troubleshooting:
- If the search returns unexpected results, check `| fieldsummary` on the base data to verify field names and types match the SPL.
- If data is not arriving for the expected sourcetype, verify the TA input is enabled and check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors from the modular input.
- If field values changed after a Catalyst Center upgrade, compare `| fieldsummary` from before and after the upgrade to identify renamed or restructured fields.
- If the search is slow, narrow the time range to `earliest=-20m` for a real-time snapshot, or use summary indexing for historical analysis.
- For vendor UI parity, cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:event:notification" eventType="NETWORK" | join type=left eventId [search index=catalyst sourcetype="cisco:dnac:issue" | rename issueId as eventId] | eval data_source=if(isnotnull(priority),"Both webhook + TA","Webhook only") | stats count by eventType, data_source | eval coverage_status=if(data_source="Both webhook + TA","Full coverage","Webhook-only — check TA input")
```

## Visualization

Table of `data_source` distribution, pie of Full coverage vs Webhook-only, optional Sankey in a third-party or Splunk visualization app to compare webhook and polled streams.

## Known False Positives

**Event notification and TA poll data not aligning due to different data paths.** Event notifications arrive via webhook (real-time) while TA poll data arrives on the poll interval (15 minutes). The join may miss correlations where the event notification arrives between polls. Distinguish by comparing timestamps: if the event notification `_time` is between two poll cycles, the join will not find a matching poll event. Suppress by widening the join time window or using `| bin _time span=15m` on both data sources.

**Event notification for an issue that Assurance has not yet detected via poll.** Some events (e.g., device unreachable) arrive via webhook before the TA polls the issues API. The correlation shows an event notification with no matching issue. Distinguish by checking whether the matching issue appears in the next poll cycle. Suppress by allowing a 15-minute grace period for the correlation.

**Duplicate event notifications from Catalyst Center webhook retries.** If Splunk HEC responds slowly, Catalyst Center may retry the webhook, delivering duplicate events. The correlation may match the same poll data to multiple notification events. Distinguish by deduplicating notifications: `| stats count by eventType, timestamp, description | where count>1`. Suppress by deduplicating before the join.

**Event notification subscription not covering all event types.** If only certain event types are subscribed in Catalyst Center's event notification configuration, the correlation will only work for those types. Issues detected by TA polling but not subscribed as events will not appear in the correlation. Distinguish by comparing the `eventType` values in notifications to the `name` values in issues. No SPL suppression — configure additional event subscriptions in Catalyst Center.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Issues API — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!issues)
