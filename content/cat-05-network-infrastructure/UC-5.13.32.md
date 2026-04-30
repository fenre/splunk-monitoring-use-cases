<!-- AUTO-GENERATED from UC-5.13.32.json — DO NOT EDIT -->

---
id: "5.13.32"
title: "Compliance Drift Detection (Was Compliant, Now Not)"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.32 · Compliance Drift Detection (Was Compliant, Now Not)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Compliance, Change &middot; **Wave:** Run &middot; **Status:** Verified

*We catch the exact moment a network device's settings change from 'approved' to 'unapproved.' If the change was planned, we match it to the change ticket. If it was not planned, we flag it as a potential unauthorised modification that needs investigation — this is what auditors care about most, because it is the difference between controlled change management and untracked modifications.*

---

## Description

Detects the exact moment a device drifts from COMPLIANT to NON_COMPLIANT, identifying configuration changes that occurred between compliance poll cycles — the strongest signal of unauthorised modification, failed change procedures, or accidental rollback. For NIST CM-3 (Configuration Change Control), this is the detective control that catches unauthorised changes. For SOX ITGC, a compliance drift event without a corresponding change ticket is a potential control failure.

## Value

UC-5.13.28 tells you how many devices are non-compliant *now*. This UC tells you which devices *just became* non-compliant — meaning someone or something changed the configuration since the last check. A device that was compliant at 10:00 and non-compliant at 11:00 had its configuration modified during that hour. The drift detection is more operationally actionable than a static non-compliance count because it identifies *new* problems rather than chronic known exceptions. For SOX ITGC, each drift event should map to an approved change ticket — drift events without tickets are potential ITGC findings that require documentation and corrective action.

## Implementation

Same `compliance` input as UC-5.13.28. Uses `streamstats` to compare consecutive polls per device per compliance type. Schedule hourly (matching the compliance poll interval). Route drift events to the change management team.

## Detailed Implementation

### Prerequisites
- UC-5.13.28 (Compliance Status Overview) must be operational — same `compliance` data feed.
- The compliance input must poll frequently enough (default 3600s / 1 hour) to detect drift in a timely manner. The precision of drift detection is bounded by the poll interval — changes between polls are detected on the next cycle, so MTTR for drift detection ≈ poll interval.
- For SOX ITGC compliance: identify which devices are financially-relevant. Maintain a `sox_in_scope_devices` lookup (deviceName → in_scope, business_unit, application) for filtering.
- For CM-3 correlation: have access to `index=catalyst sourcetype="cisco:dnac:audit:logs"` (UC-5.13.46) and/or ITSM change records for change-vs-drift reconciliation.
- This is a **run-tier** UC using `streamstats` which is computationally expensive. Not suitable for real-time dashboards with auto-refresh — schedule as hourly report instead.

### Step 1 — Configure data collection
Same `compliance` input as UC-5.13.28. No additional configuration.

For drift detection accuracy, ensure the compliance input runs consistently (no gaps). Gaps in polling create false drift events when the input resumes — a device that was COMPLIANT before the gap and COMPLIANT after may appear to have drifted if the gap spans a template update.

Verify consecutive poll data exists per device:
```spl
index=catalyst sourcetype="cisco:dnac:compliance" earliest=-24h
| stats count by deviceName, complianceType
| where count >= 2
| stats count as devices_with_history
```
If `devices_with_history` > 0, drift detection can work.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:compliance"
| sort deviceName, complianceType, _time
| streamstats current=f last(complianceStatus) as prev_status last(_time) as prev_time by deviceName, complianceType
| where complianceStatus="NON_COMPLIANT" AND prev_status="COMPLIANT"
| eval drift_hours=round((_time-prev_time)/3600,1)
| table _time, deviceName, complianceType, prev_status, complianceStatus, drift_hours
```

Why `streamstats current=f last(complianceStatus) as prev_status`: for each event, this captures the *previous* event's status for the same device + compliance type pair. When `prev_status=COMPLIANT` and `complianceStatus=NON_COMPLIANT`, a state transition (drift) occurred between those two polls. The `current=f` flag ensures the current event's own status isn't used as the 'previous' — it looks backward.

Why `sort deviceName, complianceType, _time` before `streamstats`: ensures events are in strict chronological order per device per type. Without this sort, `streamstats` may compare non-adjacent events (if events arrived out-of-order due to indexing pipeline lag), producing false drift detections.

Why `drift_hours`: shows how much time passed between the last COMPLIANT check and the first NON_COMPLIANT check. If `drift_hours ≈ 1` (one poll interval), the change happened within the last hour. If `drift_hours > 24`, there may have been a polling gap — investigate.

Why this is a **run-tier** UC: `streamstats` processes events sequentially. For a large fleet over a long time range (2,000 devices × 5 compliance types × 30 days × 24 polls/day = 7.2M events), the search can take 2–5 minutes. It's appropriate for scheduled hourly analysis, not real-time auto-refreshing dashboards.

For change-record correlation (CM-3 / SOX ITGC — the core audit value):
```spl
<base drift search above>
| lookup change_records deviceName OUTPUT change_id, change_status, approved_by
| eval drift_classification=case(
    isnotnull(change_id) AND change_status="APPROVED", "Approved change: ".change_id,
    isnotnull(change_id) AND change_status!="APPROVED", "UNAPPROVED change: ".change_id,
    1==1, "NO TICKET — INVESTIGATE")
| table _time, deviceName, complianceType, drift_classification, change_id
```
Rows classified as "NO TICKET — INVESTIGATE" are the highest-priority findings.

For SOX-scoped device filtering:
```spl
<base drift search>
| lookup sox_in_scope_devices deviceName OUTPUT in_scope, business_unit
| where in_scope="yes"
```

Schedule as Alert: `0 * * * *` (hourly, matching the compliance poll cadence), time range `-3h to now` (covers 3 poll cycles for transition detection). Trigger when `drift_classification="NO TICKET — INVESTIGATE"`. Route to the change management / security team.

### Step 3 — Validate
(a) Intentional test: in a lab, make a manual CLI change on a compliant device (e.g., add an unauthorised ACL entry). Wait for the next two compliance polls (2 hours). The drift search should show that device transitioning from COMPLIANT to NON_COMPLIANT.

(b) Run over the last 7 days. Each drift event should correspond to either a known change (approved template push) or an investigation-worthy event (unauthorised modification). If there are drift events with no explanation, the UC is catching problems that were previously invisible.

(c) Cross-reference with `index=catalyst sourcetype="cisco:dnac:audit:logs"` for the drifted devices — was there a configuration change logged in the same time window? The audit log (UC-5.13.46) should show who made the change.

(d) For SOX environments: verify that SOX-scoped devices are correctly identified by the `sox_in_scope_devices` lookup and that unapproved drift events generate the expected alerts.

(e) Verify `drift_hours` makes sense: most values should be near 1 (one poll interval). Values significantly larger indicate polling gaps that need investigation.

(f) Vendor UI parity: compare drift events with **Catalyst Center > Compliance** change history for the affected devices (if available in your Catalyst Center version).

### Step 4 — Operationalize
Alerting:
- **Change Management team**: receives all drift events with change-record correlation.
- **Security Operations**: receives only *unapproved* drift events (those classified as "NO TICKET — INVESTIGATE").
- **SOX/Audit team**: receives drift events for financially-relevant devices.
- Alert payload should include: `_time`, `deviceName`, `complianceType`, `drift_classification`, `change_id` (if matched).

Runbook (owner: Change Management):
1. Receive drift alert. Note `deviceName`, `complianceType`, `_time`.
2. Check ITSM for an approved change record covering that device and time.
3. **If approved change exists**: annotate the drift event as 'expected — CHG-XXXX.' No further action.
4. **If NO approved change**:
   - Check audit log: `index=catalyst sourcetype="cisco:dnac:audit:logs" earliest=-4h | search "*<deviceName>*"`. Who made the change?
   - If a user is identified: investigate — intentional (needs retroactive change record) or accidental?
   - If no user identified: the change may have been made via direct CLI access bypassing Catalyst Center. Escalate to security operations.
5. Remediate: push the golden template from Catalyst Center to restore compliance.
6. Document the event, root cause, and corrective action in the compliance evidence folder.

Compliance evidence (CM-3 / SOX ITGC):
- Monthly drift report: all drift events with classification (Approved / Unapproved / Investigated).
- Each unapproved event should have an investigation outcome and corrective action.
- Track unapproved drift events over time. Declining count = improving change discipline.

### Step 5 — Troubleshooting

- **Many false drift events after TA restart** — when the TA restarts after a gap, `streamstats` compares the first post-restart event with the last pre-restart event, which may span hours or days. Filter with `| where drift_hours < 4` to exclude transitions spanning gaps.

- **Mass drift after golden template update** — expected. The template change makes all devices NON_COMPLIANT until the new template is pushed. Document with the template change date and change ticket. These are 'expected drift,' not unauthorised changes.

- **`streamstats` search is very slow** — processing millions of compliance events sequentially is expensive. Solutions: (a) narrow to `-24h` for the alert; (b) pre-aggregate: `| stats latest(complianceStatus) as status by deviceName, complianceType, _time` before `streamstats`; (c) use summary indexing for weekly reports.

- **Drift events for EOX compliance type** — EOX status changes on lifecycle milestone dates are not configuration changes. Filter `| where complianceType != "EOX"` for configuration-drift-only analysis.

- **No drift events ever detected** — either no devices have changed compliance status (ideal), or the compliance input hasn't run long enough to have consecutive polls for comparison. Check `| stats count by deviceName, complianceType | where count >= 2` for devices with sufficient history.

- **Same device shows drift every poll cycle** — the device is oscillating between COMPLIANT and NON_COMPLIANT. Root cause: an unstable golden template (references a volatile element like a timestamp or DHCP timer), or the device auto-reverts its configuration (backup restore job). Investigate the oscillation pattern.

- **Change-record correlation misses matches** — the `change_records` lookup time windows may not align with drift event timestamps. Widen the matching window to ±4 hours. Also check that `deviceName` in the lookup matches the Splunk event format exactly (case sensitivity, FQDN vs short name).

- **`prev_status` is null for the first event per device** — expected. The first event has no predecessor. The `where prev_status="COMPLIANT"` filter naturally excludes these null-predecessor rows.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance"
| sort deviceName, complianceType, _time
| streamstats current=f last(complianceStatus) as prev_status last(_time) as prev_time by deviceName, complianceType
| where complianceStatus="NON_COMPLIANT" AND prev_status="COMPLIANT"
| eval drift_hours=round((_time-prev_time)/3600,1)
| table _time, deviceName, complianceType, prev_status, complianceStatus, drift_hours
```

## Visualization

(1) Table: _time, deviceName, complianceType, prev_status → complianceStatus, drift_hours — showing the transition timestamp. (2) Single value: drift events in the last 24h (red ≥ 1). (3) Timeline panel showing drift events as markers. (4) Correlation: drilldown to `index=catalyst sourcetype="cisco:dnac:audit:logs"` for the change that caused the drift.

## Known False Positives

**Golden template update causing mass drift detection.** When the golden template is changed, all devices are re-evaluated. Devices compliant under the old template 'drift' to NON_COMPLIANT under the new one. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:audit:logs"` for template changes. Suppress by allowing a 24-hour grace period after template updates.

**Planned configuration push triggering temporary drift.** During a staged deployment, devices transition through NON_COMPLIANT between receiving the push and the next compliance check. Distinguish by correlating with ITSM change records. Suppress by requiring drift to persist for 2+ consecutive polls.

**Compliance status oscillation due to API timing.** If the compliance check and the TA poll don't align precisely, a device may appear to flip between COMPLIANT and NON_COMPLIANT across consecutive polls. Distinguish by checking whether the drift reverses on the next poll.

**EOX compliance type triggering drift on lifecycle milestone dates.** When a device reaches its End-of-Life date, EOX compliance flips from COMPLIANT to NON_COMPLIANT — a lifecycle event, not a configuration change. Filter with `| where complianceType != "EOX"` for configuration-drift-only analysis.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Compliance endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-compliance-status)
- [NIST SP 800-53 Rev. 5 — CM-3 Configuration Change Control](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM-3)
- [SOX ITGC — Change Management Controls](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201)
