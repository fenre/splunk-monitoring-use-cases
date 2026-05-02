<!-- AUTO-GENERATED from UC-5.13.66.json — DO NOT EDIT -->

---
id: "5.13.66"
title: "Event Notification Delivery Failure Tracking"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.66 · Event Notification Delivery Failure Tracking

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the watcher — making sure the real-time notification pipeline between the network management system and our monitoring system is actually working. If the connection breaks silently, we catch it within hours instead of discovering days later that no alerts were coming through.*

---

## Description

Monitors the Catalyst Center event notification pipeline for delivery failures — events that Catalyst Center attempted to send via webhook but that didn't arrive in Splunk, indicating HEC endpoint issues, certificate problems, firewall changes, or Catalyst Center platform problems that silently break the real-time alerting pathway.

## Value

A silent failure in the webhook pipeline is the worst kind of monitoring gap — you think real-time alerting is active, but events aren't actually arriving. This UC catches pipeline failures by monitoring for gaps in event volume (no events for > 2 hours when events are expected) and checking HEC health (`index=_internal component=HttpInputDataHandler`). Without this meta-monitoring, a broken webhook could go undetected for days, during which all the real-time alerting UCs (UC-5.13.65, UC-5.13.61) are blind.

## Implementation

**Primary data:** `index=catalyst` `sourcetype=cisco:dnac:event:notification` (HEC as in UC-5.13.64). **HEC health:** In parallel, monitor `index=_internal` `source=*metrics.log* OR source=*splunkd.log*` for HEC 4xx/5xx, connection errors, or token failures (tune to your log volume). If HEC is on a forwarder, also watch `metrics.log` for `group=per_source_metrics` and `per_sourcetype` throughput. **Catalyst Center side:** if the product exposes webhook **delivery** status in the admin UI, align drops with Splunk gaps. For this UC’s SPL: hourly bucketing and statistical drop detection flag "quiet" hours; tune `stdev` when volume is very low. **Catalyst Center** webhook URL remains `https://<splunk>:8088/services/collector/event` with the Splunk HEC `Authorization` header. Document maintenance windows (Catalyst or Splunk) so the alert can be suppressed.

## Detailed Implementation

### Prerequisites
- UC-5.13.64 complete: HEC token, webhook destination, and event notification subscriptions active.
- Baseline established: at least 7 days of `cisco:dnac:event:notification` data in `index=catalyst` to establish normal delivery patterns.
- Access to Splunk internal logs (`index=_internal`) for HEC health monitoring.
- Access to Catalyst Center System > Settings > External Services for webhook destination health.

### Step 1 — Configure delivery monitoring
Event notification delivery monitoring requires checking two independent data paths:
1. **Splunk HEC health:** Monitor `index=_internal sourcetype=splunkd source="*httpinput*"` for HEC ingestion metrics and errors.
2. **Event volume baseline:** Establish expected event volume patterns from historical data to detect delivery gaps.

Key monitoring points:
- HEC endpoint availability: HTTP 200 responses from HEC indicate successful delivery.
- Event volume per hour: compare current volume to the historical baseline for the same day-of-week and hour.
- Delivery latency: delta between Catalyst Center `timestamp` and Splunk `_time`.
- HEC token health: authentication failures indicate token rotation or misconfiguration.

### Step 2 — Create the search and alert

```spl
index=catalyst sourcetype="cisco:dnac:event:notification"
| bin _time span=1h
| stats count as current_count by _time
| eventstats avg(count) as baseline_avg stdev(count) as baseline_stdev
| eval lower_bound=max(baseline_avg - 2*baseline_stdev, 1)
| eval delivery_gap=if(current_count < lower_bound, "GAP", "OK")
| where delivery_gap="GAP"
| eval gap_severity=case(current_count=0, "Complete Gap", current_count < lower_bound/2, "Severe Drop", 1==1, "Below Baseline")
```

#### Understanding this SPL:
- **`bin _time span=1h`**: Groups events into hourly buckets for volume comparison.
- **`eventstats avg(count) ... stdev(count)`**: Computes the historical average and standard deviation across all hourly buckets in the search window. The baseline includes weekdays and weekends.
- **`lower_bound=max(baseline_avg - 2*baseline_stdev, 1)`**: Sets the minimum expected volume at 2 standard deviations below the mean, with a floor of 1 event/hour. This accounts for natural volume variation.
- **`delivery_gap="GAP"`**: Flags hours where the volume falls below the lower bound.
- **`gap_severity`**: Categorizes the gap — "Complete Gap" (zero events) is more urgent than "Below Baseline" (some events but fewer than expected).

For HEC-level monitoring: `index=_internal sourcetype=splunkd source="*httpinput*" | stats count by log_level | where log_level="ERROR"` — catches HEC endpoint failures regardless of the Catalyst Center source.

### Step 3 — Validate
- **Intentional gap test:** Temporarily disable the webhook destination in Catalyst Center (System > Settings > External Services > Destinations) and verify the gap detection fires within 2 hours. Re-enable and verify events resume.
- **Baseline accuracy:** Run the baseline SPL over 14+ days and verify the `baseline_avg` and `baseline_stdev` are reasonable. If the baseline includes known outage periods, exclude them.
- **HEC health check:** Run `index=_internal sourcetype=splunkd source="*httpinput*" earliest=-24h | stats count by log_level` — there should be zero ERROR entries.
- **Vendor UI parity:** cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.
### Step 4 — Operationalize
- **Dashboard:** Timechart showing event volume per hour with the baseline overlay (upper and lower bounds). Highlight gaps in red. Add a single-value tile for "Hours Since Last Event" as a quick health indicator.
- **Alert:** Scheduled hourly; trigger when `delivery_gap="GAP"` and `gap_severity IN ("Complete Gap", "Severe Drop")`. Route to the Splunk admin team, not the network team (delivery failures are infrastructure issues, not network issues).
- **Escalation:** If the gap persists for 4+ hours, escalate to the Catalyst Center admin to check webhook destination health.

### Step 5 — Troubleshoot
- **Complete gap (zero events for 2+ hours):** Check Catalyst Center webhook destination status. Verify network connectivity from Catalyst Center to the HEC endpoint (firewall rules, DNS, TLS certificate validity). Test HEC: `curl -k https://<hec>:8088/services/collector/event -H "Authorization: Splunk <token>" -d '{"event":"test"}'`.
- **Severe drop (some events but much fewer than baseline):** Catalyst Center may have silently dropped some event subscriptions. Check the subscription list in System > Settings > External Services > Events > Notifications.
- **HEC authentication errors:** The HEC token may have been rotated. Update the Catalyst Center webhook destination with the new token.
- **Events arriving with increasing latency:** HEC endpoint under load. Check `index=_internal source="*httpinput*" group=queue` for queue depth. Consider scaling HEC capacity or adding indexer clustering.
- If data is not arriving for `cisco:dnac:event:notification`, check that the `event_notification` input is enabled in the TA configuration and that the Catalyst Center API credentials have not expired.

Additional operational context for Event Notification Delivery Failure Tracking:

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
index=catalyst sourcetype="cisco:dnac:event:notification" | bin _time span=1h | stats count as received_events by _time | eventstats avg(received_events) as avg_events stdev(received_events) as stdev_events | where received_events < (avg_events - 2*stdev_events) OR received_events=0 | eval gap_type=if(received_events=0, "Complete delivery gap", "Unusual drop in notifications") | table _time received_events avg_events gap_type
```

## Visualization

Time series of `received_events` with `avg_events` band, table of `gap_type` and timestamps, combine with a panel of HEC error count from _internal on the same dashboard.

## Known False Positives

**Low event volume during quiet periods appearing as delivery failure.** Nights, weekends, and change freezes naturally produce fewer events. If the delivery health check uses a fixed minimum threshold, quiet periods may trigger a false delivery failure alert. Distinguish by comparing the event volume against a time-of-day and day-of-week baseline rather than a flat threshold. Suppress by using time-aware baselines for the delivery health check.

**Catalyst Center webhook destination configuration changed.** If the webhook destination URL, authentication, or TLS certificate is changed, events generated between the old and new configuration may fail delivery. Distinguish by checking `index=catalyst sourcetype="cisco:dnac:audit:logs"` for webhook configuration changes. Suppress by allowing a 15-minute grace period after webhook configuration changes.

**Splunk HEC token rotation causing temporary authentication failures.** When the HEC token is rotated, events sent with the old token fail authentication. Distinguish by checking `index=_internal sourcetype=splunkd source="*httpinput*"` for authentication failures coinciding with the HEC token rotation. Suppress by coordinating HEC token rotation with Catalyst Center webhook credential updates.

**Network path issue between Catalyst Center and Splunk HEC endpoint.** Firewall changes, routing issues, or TLS certificate mismatches on the HEC endpoint can cause delivery failures. Distinguish by checking whether the delivery failures affect all event types uniformly (path issue) or only specific types (configuration issue). Do not suppress — investigate and resolve the network path issue.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Event Management API — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!get-notifications)
