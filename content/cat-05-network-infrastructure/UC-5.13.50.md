<!-- AUTO-GENERATED from UC-5.13.50.json — DO NOT EDIT -->

---
id: "5.13.50"
title: "Audit Log Completeness and Gap Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.50 · Audit Log Completeness and Gap Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Audit, Operational &middot; **Wave:** Walk &middot; **Status:** Verified

*We make sure the audit trail is continuous and complete — catching any gaps where logging stopped, which could mean something was tampered with or the recording system had a problem. A complete, unbroken record is what auditors need to trust that nothing was hidden during the periods between their visits.*

---

## Description

Detects gaps or unusual drops in audit log event volume that may indicate logging failure, data collection outage, or potential log tampering — ensuring the audit trail is continuous and tamper-evident for compliance and forensic investigations. An audit trail with gaps is worse than no audit trail because it creates a false sense of coverage.

## Value

A 4-hour gap in audit logs could mean the TA crashed (benign but needs fixing), the Catalyst Center API went down (operational issue), or an attacker disabled logging before making unauthorised changes (critical security event). Without this UC, you discover the gap days later during a review — by which time the forensic evidence may be lost. For NIST AU-3 (Content of Audit Records), this UC ensures the continuous stream of audit events is maintained. For AU-6 (Audit Review), it flags anomalous drops that warrant manual investigation. The distinction between 'Complete Gap' and 'Below Baseline' helps triage: a complete gap is always urgent; a below-baseline hour may be a legitimate quiet period.

## Implementation

Same `audit_logs` input as UC-5.13.45. Monitor hourly event volume with `eventstats` baseline. Alert on complete gaps (0 events for > 2 consecutive hours). Route to the Splunk admin team, not the network team — this is a collection health issue.

## Detailed Implementation

### Prerequisites
- UC-5.13.45 (Audit Log Overview) must be operational — same `audit_logs` data feed.
- At least **14 days** of historical audit log data to establish reliable hourly baselines.
- This UC monitors the **collection pipeline**, not the network. Route alerts to the **Splunk admin team**, not the network operations team. A complete gap means the TA or forwarder needs attention.
- Understand that audit log volume is inherently variable — business hours produce more events than nights/weekends. The `eventstats` baseline accounts for this.

### Step 1 — Configure data collection
Same `audit_logs` input as UC-5.13.45. No additional configuration.

For freshness monitoring (simpler than statistical baseline):
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs"
| stats latest(_time) as last_event
| eval hours_since=round((now()-last_event)/3600,1)
| where hours_since > 2
```
This fires when no audit events have been received for > 2 hours — a simpler but less nuanced check than the statistical approach.

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs"
| bin _time span=1h
| stats count as hourly_count by _time
| eventstats avg(hourly_count) as baseline stdev(hourly_count) as stdev_count
| eval expected_min=max(baseline - 2*stdev_count, 0)
| eval gap_status=case(hourly_count=0, "Complete Gap", hourly_count < expected_min AND expected_min > 0, "Below Baseline", 1==1, "Normal")
| where gap_status != "Normal"
| eval hours_ago=round((now()-_time)/3600,1)
| sort _time
```

Why `Complete Gap` vs `Below Baseline`: complete gaps (zero events) are more severe — they indicate collection failure or potential tampering. Below-baseline hours may be legitimate quiet periods (overnight, weekend). The distinction helps triage.

Why `max(baseline - 2*stdev_count, 0)`: prevents negative minimums. When the baseline is very low (e.g., 2 events/hour), `baseline - 2*stdev` could go negative, which would never trigger. The `max(..., 0)` ensures the floor is zero.

Why `hours_ago`: provides urgency context. A gap from 2 hours ago needs immediate investigation. A gap from 3 days ago should still be documented but is less urgent.

Schedule as Alert: `0 * * * *` (hourly), time range `-14d to now`, trigger on `gap_status="Complete Gap"` for the most recent 4 hours. Throttle for 4 hours.

### Step 3 — Validate
(a) Intentional test: temporarily disable the `audit_logs` input for 2–3 hours, then re-enable. The gap detection should flag the missing hours within the next scheduled run.

(b) Run over the last 14 days. Complete gaps should correspond to known TA outages or Catalyst Center maintenance windows. Document each gap.

(c) Below-baseline hours should correspond to known quiet periods (holidays, weekends, overnight). If weekday business hours appear as below-baseline, the threshold may be too tight or the baseline period includes atypical days.

(d) Verify the freshness check works independently: if `hours_since > 2` fires, there's a collection problem regardless of the statistical baseline.

(e) Cross-reference gaps with `index=_internal sourcetype=splunkd "TA_cisco_catalyst"` for the same time period to determine whether the gap was caused by the TA (fixable) or the Catalyst Center API (external).

### Step 4 — Operationalize
Dashboard (on the "Catalyst Center Data Collection Health" dashboard, alongside UC-5.13.74):
- Timechart: hourly log count with baseline ± 2σ bands. Gap hours in red.
- Table: detected gaps with gap_status, _time, hours_ago.
- Single value: 'Hours since last audit event' (green < 1, yellow 1–2, red > 2).

Alerting:
- Complete gap for > 2 consecutive hours → Splunk admin team (not network team).
- Include diagnostic steps in the alert: check TA input status, check `index=_internal` for errors, check Catalyst Center API availability.

Compliance evidence (NIST AU-3 / AU-6):
- Monthly completeness report: list all detected gaps with root cause and corrective action.
- Target: zero unexplained gaps per month.
- Attestation: 'The audit log collection pipeline was monitored continuously. All detected gaps were investigated and resolved within [N] hours.'

Runbook (owner: Splunk Admin team):
1. Receive gap alert. Note the gap time range.
2. Check TA input status: TA → Inputs → is Audit Logs enabled?
3. Check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst" ERROR` for the gap period. Common errors:
   - `403 Forbidden` → service account RBAC changed. Re-check SUPER-ADMIN-ROLE.
   - `Connection refused` → Catalyst Center is down or network issue. Verify API reachability.
   - `SSL certificate verify failed` → certificate changed. Update trust or disable SSL verification.
   - `429 Too Many Requests` → API throttling. Reduce poll frequency for other inputs.
4. Restart the input if needed (disable/re-enable in the TA UI).
5. After restoration: verify events resume in the next poll cycle.
6. Document the gap, root cause, and resolution for the compliance evidence folder.

### Step 5 — Troubleshooting

- **Frequent complete gaps** — the `audit_logs` input is unstable. Check Heavy Forwarder health (disk, memory, CPU). Check the TA version for known bugs. Consider increasing the poll interval from 300s to 600s to reduce API load.

- **All hours flagged as below baseline** — the baseline window includes atypical days (holiday, outage). Extend to 14+ days or use time-of-day-aware baselines.

- **Overnight hours always flagged** — legitimate low activity at night. Use `| eventstats avg(hourly_count) as baseline by date_hour, date_wday` for time-aware baselines.

- **Gap corresponds to Catalyst Center upgrade** — expected. Document the gap with the Catalyst Center maintenance ticket reference.

- **Gap corresponds to Splunk maintenance** — expected. Document with the Splunk maintenance ticket.

- **`hours_since` freshness check fires constantly** — the threshold is too tight for your environment's activity level. Increase from 2 to 4 hours if audit events are very sparse.

- **Tampering suspected** — if a gap coincides with a compliance drift event (UC-5.13.32) or an after-hours change (UC-5.13.49) that's not in the audit trail, escalate to security operations immediately. This is the highest-priority finding from this UC.

- **Audit log volume suddenly increases dramatically** — investigate whether new automated processes, integrations, or users are generating audit events. High volume is not a problem for this UC but may indicate unexpected API usage.

Additional operational context for Audit Log Completeness and Gap Detection:

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
index=catalyst sourcetype="cisco:dnac:audit:logs"
| bin _time span=1h
| stats count as hourly_count by _time
| eventstats avg(hourly_count) as baseline stdev(hourly_count) as stdev_count
| eval expected_min=max(baseline - 2*stdev_count, 0)
| eval gap_status=case(hourly_count=0, "Complete Gap", hourly_count < expected_min AND expected_min > 0, "Below Baseline", 1==1, "Normal")
| where gap_status != "Normal"
| eval hours_ago=round((now()-_time)/3600,1)
| sort _time
```

## Visualization

(1) Timechart: hourly log count with baseline ± 2σ bands. Gap hours highlighted in red. (2) Table: gap hours with gap_status and hours_ago. (3) Single value: 'Hours since last audit event' (red > 2). (4) Alert: complete gap for 2+ consecutive hours.

## Known False Positives

**Holidays and change freezes producing genuinely quiet audit periods.** During organisational holidays or change freeze periods, no administrative activity occurs, producing legitimately low or zero audit log volume. Distinguish by checking whether the gap corresponds to a known holiday or change freeze. Suppress by maintaining a `holidays` lookup and excluding holiday periods from gap detection.

**Catalyst Center platform maintenance or restart.** During platform maintenance (upgrade, backup, restart), the audit log API is unavailable. Distinguish by checking whether the gap coincides with platform maintenance visible in pre/post-maintenance audit entries. Suppress by annotating gaps with maintenance window records.

**TA poll failure or Splunk forwarder issue.** The audit log gap may be caused by a Splunk data collection pipeline failure rather than an actual gap on Catalyst Center. Distinguish by checking `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for collection errors during the gap period. Fix the TA/forwarder issue rather than treating it as an audit completeness problem.

**Low-activity period falling below the statistical threshold.** Overnight or weekend periods with minimal administrative activity may produce counts below the 2σ threshold without indicating a true gap. Distinguish by comparing with the same time window in previous weeks. Suppress by using time-of-day-aware baselines: `| eventstats avg(hourly_count) as baseline by date_hour, date_wday`.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Audit Log API](https://developer.cisco.com/docs/catalyst-center/#!get-audit-log-records)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [NIST SP 800-53 Rev. 5 — AU-3 Content of Audit Records](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AU-3)
