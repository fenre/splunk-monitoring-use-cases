<!-- AUTO-GENERATED from UC-5.13.46.json — DO NOT EDIT -->

---
id: "5.13.46"
title: "Configuration Change Audit Trail"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.46 · Configuration Change Audit Trail

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Audit, Change &middot; **Wave:** Crawl &middot; **Status:** Verified

*We keep a focused record of every configuration change made through the network management system — who changed what and when. This lets your change management team verify each change was approved, and gives auditors proof that no unauthorised modifications slipped through the process.*

---

## Description

Isolates configuration change events (PUT/POST/DELETE operations) from the full audit log, providing a dedicated change audit trail that shows every template push, policy modification, device provisioning action, and setting change — the evidence trail that change management and compliance auditors require for NIST CM-3 and SOX ITGC.

## Value

The full audit log (UC-5.13.45) includes read operations (GETs) that are noise for change management. This UC filters to state-changing operations only, producing a clean change trail that answers the three questions auditors always ask: 'What was changed?' (auditDescription), 'Who changed it?' (auditUserName), 'When was it changed?' (_time). For SOX ITGC, each row in this report should map to an approved change ticket — rows without tickets are potential ITGC findings that require documentation and corrective action.

## Implementation

Same `audit_logs` input as UC-5.13.45. Filter to `auditRequestType IN ("PUT","POST","DELETE")` for state-changing operations only. Schedule daily for change management review. Monthly CSV export for SOX evidence.

## Detailed Implementation

### Prerequisites
- UC-5.13.45 (Audit Log Overview) must be operational — same `audit_logs` data feed.
- For SOX ITGC compliance, maintain a `change_records` lookup mapping ITSM change ticket IDs to auditUserName, start_time, end_time. This enables approved-vs-unapproved change classification.
- For NIST CM-3, document the change management policy: who is authorised to make changes, during what hours, and with what approval process.

### Step 1 — Configure data collection
Same `audit_logs` input as UC-5.13.45. No additional configuration.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false auditRequestType IN ("PUT","POST","DELETE")
| table _time, auditUserName, auditRequestType, auditDescription
| sort -_time
```

Why filter to `PUT/POST/DELETE`: GET operations are read-only and don't change state. State-changing operations are the ones that require change management tracking. This is the clean change trail.

Why `isSystemEvent=false`: excludes automated Catalyst Center internal operations (certificate rotation, RRM adjustment) that are not human-initiated changes.

For change-ticket correlation (SOX ITGC):
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false auditRequestType IN ("PUT","POST","DELETE")
| lookup change_records auditUserName OUTPUT change_id, approval_status
| eval change_status=if(isnotnull(change_id), "Approved: ".change_id, "UNAPPROVED")
| table _time, auditUserName, auditRequestType, auditDescription, change_status
| sort -_time
```

For daily change summary:
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false auditRequestType IN ("PUT","POST","DELETE")
| stats count as changes dc(auditDescription) as unique_operations by auditUserName
| sort -changes
```

Schedule as Report: daily (cron `0 7 * * *`), output to dashboard and PDF. Monthly CSV export for SOX evidence folder.

### Step 3 — Validate
(a) Make a deliberate configuration change in Catalyst Center. Verify it appears in the filtered results within 5 minutes with the correct `auditRequestType` and `auditDescription`.

(b) Verify GET operations are excluded: `| stats count by auditRequestType` should show only PUT/POST/DELETE.

(c) Cross-reference with **Catalyst Center > System > Audit Logs** filtered to modifications.

(d) For SOX: verify the change-ticket correlation produces meaningful `change_status` values. Each approved change should match a ticket.

(e) Vendor UI parity: compare the change trail with **Catalyst Center > System > Audit Logs** for the same time window, filtered to non-read operations.

### Step 4 — Operationalize
Dashboard (on the "Administration & Audit" dashboard, below UC-5.13.45):
- Table: the change trail (this search) — the primary evidence panel.
- Timechart: change volume over 30 days.
- Per-user bar chart: changes by user for accountability.
- SOX column: change_status (Approved/UNAPPROVED) colour-coded.

Compliance evidence workflow:
- **Daily**: security team reviews changes from the previous 24 hours.
- **Monthly**: CSV export with change-ticket correlation for SOX ITGC workpapers.
- **Pre-audit**: generate the 90-day change trail with approval status for assessor review.

Runbook (owner: Change Management):
1. Review the daily change trail.
2. For each change: verify a corresponding ITSM change ticket exists.
3. Changes without tickets: investigate with the user. Emergency? Forgotten ticket? Unauthorised?
4. Document each unapproved change and corrective action.
5. For bulk operations (100+ events with same `auditParentId`): document as one approved change.

### Step 5 — Troubleshooting

- **No PUT/POST/DELETE events** — either no configuration changes occurred, or the `auditRequestType` field has different values. Check `| stats values(auditRequestType)` for the actual strings used.

- **`auditDescription` doesn't identify what was changed** — some audit events have generic descriptions. Cross-reference with UC-5.13.32 (Compliance Drift Detection) for the specific configuration delta that resulted from the change.

- **Change-ticket correlation produces many false 'UNAPPROVED'** — the lookup time-window matching may be too strict. Widen the window to ±2 hours around the change time.

- **System events appearing despite filter** — verify `isSystemEvent` field is boolean, not a string. Some TA versions may emit `"false"` (string) instead of `false` (boolean). Adjust: `| where isSystemEvent=false OR isSystemEvent="false"`.

- **Same change appears multiple times** — the API may return duplicate events. Deduplicate with `| dedup _time, auditUserName, auditDescription`.

- **Audit trail required for a specific device** — search `auditDescription="*<deviceName>*"` to find all changes related to a specific device. If `auditDescription` doesn't contain device names, cross-reference change times with UC-5.13.32 (Compliance Drift) for the affected devices.

- **Want to alert on specific sensitive operations** — filter `auditDescription` with regex for sensitive keywords: `template`, `credential`, `certificate`, `user`, `role`, `policy`, `password`.

- **Retention too short for annual audits** — extend `catalyst` index retention to 365+ days. Audit log data is ~50 KB/day — the cost is negligible.

Additional operational context for Configuration Change Audit Trail:

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
index=catalyst sourcetype="cisco:dnac:audit:logs" isSystemEvent=false auditRequestType IN ("PUT","POST","DELETE")
| table _time, auditUserName, auditRequestType, auditDescription
| sort -_time
```

## Visualization

(1) Table: _time, auditUserName, auditRequestType, auditDescription — the change trail. (2) Timechart: `| timechart span=1d count by auditRequestType` over 30 days. (3) Bar chart: changes per user for accountability. (4) Correlation column: join with ITSM change records to flag unapproved changes.

## Known False Positives

**Automated Catalyst Center operations appearing as changes.** Catalyst Center may perform automated configuration adjustments (RRM optimisation, certificate renewal) that show as PUT operations. Distinguish by checking `isSystemEvent` — automated operations should be `true`. The default SPL filters `isSystemEvent=false`, which excludes these.

**Bulk template push generating many change events.** A single approved change (push template to 100 devices) generates 100+ audit events. Distinguish by checking whether they share the same `auditParentId` (parent operation). For SOX evidence, document the bulk operation as one approved change covering all generated events.

**TA configuration changes appearing in the trail.** Modifying the TA's input settings (changing poll interval, adding new inputs) generates audit events on the Catalyst Center side. Distinguish by checking `auditDescription` for TA-related operations. These are legitimate Splunk-side changes, not network configuration changes.

**Same change logged multiple times.** Some Catalyst Center operations involve multiple API calls that each generate a separate audit event. Distinguish by checking `auditParentId` — related events share a parent ID. Group by `auditParentId` for a one-row-per-operation view.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Audit Log API](https://developer.cisco.com/docs/catalyst-center/#!get-audit-log-records)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [NIST SP 800-53 Rev. 5 — CM-3 Configuration Change Control](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM-3)
