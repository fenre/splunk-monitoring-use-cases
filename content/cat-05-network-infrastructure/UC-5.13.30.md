<!-- AUTO-GENERATED from UC-5.13.30.json — DO NOT EDIT -->

---
id: "5.13.30"
title: "Compliance Status Trending"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.30 · Compliance Status Trending

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We draw a simple day-by-day picture of how many network devices pass or fail their configuration checks, so you can show auditors that standards were held steady over months and years — not just on the day of the audit. When the line dips, we explain why and show how quickly it recovered, proving your team stays on top of things continuously.*

---

## Description

Tracks the compliance posture over time as a stacked area chart and compliance percentage line, demonstrating to auditors that configuration standards are continuously monitored and that violations are remediated promptly — not just at point-in-time assessment snapshots.

## Value

Auditors ask: 'How do you know your devices were compliant *between* assessments?' This UC answers that question with a continuous daily trend line. A compliance percentage that holds at 95%+ for 90 days is the strongest evidence for NIST CM-6 and PCI 1.1.1 that your configuration baseline is enforced as an ongoing process, not a one-time project. Dips in the trend correspond to template pushes, firmware campaigns, or drift events — and the recovery slope proves your remediation process works. Each dip has a story: 'On March 15 we updated the golden template, compliance dropped to 72%, and by March 18 all devices were re-pushed — demonstrated in the trend.' Without this trend, your compliance narrative is 'we checked on audit day and it was fine' — with it, you show 365 days of continuous enforcement.

## Implementation

Same `compliance` input as UC-5.13.28. Retain 90–365 days for audit evidence. The `timechart span=1d` produces daily compliance snapshots. Handle zero-denominator days with `if((compliant+non_compliant)>0, ..., null())`. Schedule daily CSV export for the GRC evidence folder.

## Detailed Implementation

### Prerequisites
- UC-5.13.28 (Compliance Status Overview) must be operational — same `compliance` data feed.
- Index retention: set `frozenTimePeriodInSecs` for the `catalyst` index to cover your compliance reporting period. NIST AU-11 recommends retaining audit records per your organisation's retention policy — typically **1–3 years** for CM-6 evidence. PCI DSS 10.7 requires at least **12 months** of audit trail history. Compliance data is ~400 bytes/device/poll × 24 polls/day × 365 days × 2,000 devices ≈ 2.8 GB/year — affordable for any Splunk deployment.
- Agree with the compliance team on the SLO: what percentage counts as 'compliant'? 95%? 98%? 100%? Document this as the reference line on the chart. The SLO should be achievable given your maintenance schedule — if you push templates weekly and each push creates a 24-hour compliance dip, a 100% SLO is impossible.
- For assessor readiness, prepare a compliance narrative template that explains each dip in the trend: what caused it, when it was remediated, and what change ID approved the change.

### Step 1 — Configure data collection
Same `compliance` input as UC-5.13.28. No additional configuration.

For the trend to be useful as audit evidence, verify continuous data collection with no gaps:
```spl
index=catalyst sourcetype="cisco:dnac:compliance" earliest=-90d
| timechart span=1d count
| where count = 0
```
Zero-count days are data gaps that will show as holes in the trend. Each gap must be documented with a root cause (TA outage, Catalyst Center maintenance, Splunk maintenance) for the audit narrative. Zero gaps in a 90-day period is the target.

Verify compliance status distribution:
```spl
index=catalyst sourcetype="cisco:dnac:compliance" earliest=-24h
| stats count by complianceStatus
```
You should see COMPLIANT (majority), NON_COMPLIANT (some), and possibly ERROR, IN_PROGRESS, NOT_APPLICABLE.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:compliance"
| where complianceStatus IN ("COMPLIANT","NON_COMPLIANT")
| timechart span=1d count(eval(complianceStatus="COMPLIANT")) as compliant count(eval(complianceStatus="NON_COMPLIANT")) as non_compliant
| eval compliance_pct=if((compliant+non_compliant)>0, round(compliant*100/(compliant+non_compliant),1), null())
```

Why filter to `IN ("COMPLIANT","NON_COMPLIANT")`: excludes ERROR, IN_PROGRESS, and NOT_APPLICABLE statuses that would inflate the denominator without representing genuine compliance evaluations. The percentage should measure only devices that were actually evaluated against the golden template — not devices whose evaluation failed (ERROR), is still running (IN_PROGRESS), or doesn't apply (NOT_APPLICABLE for device types without golden templates).

Why `if((compliant+non_compliant)>0, ..., null())`: prevents division by zero on days with no compliance data (holidays, TA outages). A null percentage is visually distinct from 0% in the chart — it shows a gap rather than a false 'zero compliance' day. This distinction is critical for audit evidence: a gap ("no data that day") is very different from 0% ("every device was non-compliant that day").

Why `span=1d`: daily granularity is appropriate for compliance trending. Compliance posture changes slowly — a device that drifts out of compliance today will still be non-compliant tomorrow unless someone fixes it. Hourly granularity would show within-day noise from poll timing (devices being evaluated at different hours) without adding operational value. Daily snaps are what auditors review.

Why this is the key audit evidence UC: auditors don't want to see today's compliance percentage — they want to see that it was MAINTAINED at an acceptable level over the entire assessment period. A 95% compliance rate today is meaningless if it was 60% last month and nobody noticed. This trend proves sustained monitoring and prompt remediation.

For the assessor evidence export:
```spl
<base search above>
| eval date=strftime(_time, "%Y-%m-%d")
| table date, compliant, non_compliant, compliance_pct
```
Schedule as CSV export: monthly to the GRC evidence folder with filename `compliance_trend_YYYY-MM.csv`.

For per-compliance-type trending (showing RUNNING_CONFIG vs IMAGE separately):
```spl
index=catalyst sourcetype="cisco:dnac:compliance"
| where complianceStatus IN ("COMPLIANT","NON_COMPLIANT")
| timechart span=1d count(eval(complianceStatus="COMPLIANT")) as compliant count(eval(complianceStatus="NON_COMPLIANT")) as non_compliant by complianceType
```
This breaks the trend into policy families — useful when the overall trend dips but you need to know if it's a configuration template issue (RUNNING_CONFIG) or a firmware issue (IMAGE).

Schedule as Report: daily (cron `0 6 * * *`), output to dashboard. Monthly CSV/PDF export for the GRC evidence folder.

### Step 3 — Validate
(a) Run the search over the last 30 days. The `compliance_pct` line should be relatively stable (typically 90–100% for a well-managed fleet). Sudden dips should correspond to known events.

(b) Compare today's `compliance_pct` with UC-5.13.28's current snapshot. They should agree within 1–2 percentage points (daily average vs point-in-time).

(c) Check for data gaps: `| where isnull(compliance_pct)`. Each gap should be documented with a root cause for the assessor narrative. Target: zero unexplained gaps.

(d) Verify the SLO reference line: the `compliance_pct` should be above the agreed SLO (e.g., 95%) on most days. Days below the SLO are potential audit findings that need documented remediation.

(e) Cross-reference dips with UC-5.13.29 (Non-Compliant Device Alerting) — every dip should have a corresponding alert and remediation record. If a dip occurred but no alert fired, the alerting threshold (UC-5.13.29) may be too conservative.

(f) Vendor UI parity: compare the compliance trend shape with **Catalyst Center > Compliance** for the same period. Exact values won't match (different aggregation methods) but the trend direction should agree.

### Step 4 — Operationalize
Dashboard placement (on the "Compliance Posture" dashboard, below UC-5.13.28's donut chart):
- Full-width stacked area chart: `compliant` (green) vs `non_compliant` (red) with `compliance_pct` line overlay.
- SLO reference line at 95% (or your agreed target). Use Dashboard Studio annotation or `| eval slo=95` with a secondary series.
- Time-picker presets: "Last 30 days" (monthly review), "Last 90 days" (quarterly audit), "Last 365 days" (annual assessment).
- Annotations: template change dates, maintenance windows, audit dates — each as a vertical marker with a label. These annotations are the narrative that explains every dip.

Compliance evidence workflow:
- **Daily**: scheduled search runs at 6 AM, updates the dashboard.
- **Monthly**: CSV export to GRC evidence folder with date-stamped filename (`compliance_trend_2026-04.csv`).
- **Pre-audit**: generate the 90-day or 365-day trend PDF and include in the evidence pack for CM-6 (NIST) / 1.1.1 (PCI).
- **During audit**: give assessors read-only dashboard access via a `compliance_auditor` Splunk role with `srchIndexesAllowed = catalyst` and a search filter scoped to compliance sourcetypes.

Runbook (owner: Compliance team, daily review):
1. Review the daily trend. If `compliance_pct` dropped below the SLO yesterday, investigate with UC-5.13.29 (which devices became non-compliant?) and UC-5.13.31 (which compliance type failed?).
2. For planned dips (template updates, firmware campaigns): document the change ID, expected duration, and recovery timeline in the compliance narrative. Example: "On April 15, golden template v3.2 was deployed (CHG-2026-0412). Compliance dropped to 78% as devices were re-evaluated. By April 17, all devices were re-pushed and compliance recovered to 97%."
3. For unplanned dips (configuration drift, unauthorised changes): escalate to change management per UC-5.13.32 (Drift Detection). Document the root cause, remediation steps, and prevention plan.
4. Track `compliance_pct` month-over-month. A declining trend (even above the SLO) indicates growing technical debt that will eventually breach the SLO.
5. For quarterly assessor meetings: prepare the trend PDF with annotations, the monthly CSVs, and the dip narratives. This package answers the auditor's core question: "How do I know you were compliant between my visits?"

### Step 5 — Troubleshooting

- **Compliance_pct is always 100%** — either all devices are genuinely compliant (verify in **Catalyst Center > Compliance**), or the `complianceStatus` field values don't match the filter. Check `| stats values(complianceStatus)` for the actual strings. Also check: if no golden templates are assigned, all devices may be NOT_APPLICABLE (excluded from the trend), producing 100% among the zero that are actually evaluated.

- **Large dip that doesn't recover within 48 hours** — a golden template change made many devices permanently non-compliant. The template may need to be pushed to the affected devices, or the template itself may need revision if it's incompatible with some device types.

- **Data gaps (null `compliance_pct` days)** — TA outage, compliance input disabled, or Catalyst Center maintenance. Document each gap with a root cause for auditors. Re-enable the input and verify recovery. For the evidence narrative: "Data gap on April 20 due to scheduled Splunk maintenance (MTX-2026-0420). Collection resumed April 21 at 06:00. The gap does not affect compliance posture — it reflects a monitoring interruption, not a compliance failure."

- **Compliance_pct oscillates day-to-day** — devices are flipping between COMPLIANT and NON_COMPLIANT due to an unstable golden template or intermittent compliance check failures. Investigate with `| stats count by complianceStatus, deviceName | where count > 50` to find the oscillating devices. Root cause: the template may reference a volatile element (e.g., DHCP lease timer that changes hourly).

- **Denominator is too small (few devices evaluated)** — only a subset of devices have COMPLIANT/NON_COMPLIANT status while most are NOT_APPLICABLE. This happens when golden templates are assigned to only a subset of device families. Expand template assignment in **Catalyst Center > Design > Templates** for comprehensive compliance coverage.

- **Trend shows improvement that the assessor disputes** — ensure the search time range matches the assessment period. Show the assessor the raw daily CSV data alongside the chart. The data is the evidence — the chart is the presentation.

- **CSV export missing for a month** — the `outputcsv` command requires `schedule_search` capability on the scheduling user. Verify permissions. Also check the scheduled search run history in Settings → Search & Reports.

- **Chart shows both `compliant` and `non_compliant` counts growing simultaneously** — the device fleet is growing (more devices onboarded). The stacked area accurately reflects the increasing population. Use `compliance_pct` (the line) as the primary metric, not absolute counts. A growing fleet with constant `compliance_pct` means new devices are being configured to comply from day one — a positive signal.

- **Assessor wants to see remediation velocity** — supplement the trend with UC-5.13.29 (alert-to-ticket time) and UC-5.13.24 (Issue Resolution Time) to show how quickly non-compliance events are remediated after detection.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance"
| where complianceStatus IN ("COMPLIANT","NON_COMPLIANT")
| timechart span=1d count(eval(complianceStatus="COMPLIANT")) as compliant count(eval(complianceStatus="NON_COMPLIANT")) as non_compliant
| eval compliance_pct=if((compliant+non_compliant)>0, round(compliant*100/(compliant+non_compliant),1), null())
```

## Visualization

(1) Stacked area chart: `compliant` (green) vs `non_compliant` (red) over time — the visual narrative of compliance posture. (2) Line overlay: `compliance_pct` on a secondary y-axis (0–100%) with an SLO reference line at 95%. (3) Stat panel: current compliance_pct, 30-day average, 90-day average. (4) Annotations: overlay template change dates, maintenance windows, and audit dates for assessor context.

## Known False Positives

**Golden template update creating a step change in the compliance trend.** When the golden template is updated, the ratio of COMPLIANT to NON_COMPLIANT devices may shift dramatically on the day of the update — this is an expected and intentional step change, not an anomaly. Distinguish by checking whether the trend shows a sharp, one-time shift corresponding to a template change in the audit log. Suppress by annotating the trend chart with template change dates.

**Compliance re-scan cadence affecting trend smoothness.** The compliance API polls hourly by default. Changes in compliance status may appear as step functions rather than smooth trends. `span=1d` smooths this into daily snapshots which are appropriate for compliance trending. No suppression needed.

**Device batch onboarding creating a temporary dip in the compliance ratio.** When many new devices are added to Catalyst Center, they may initially show as NON_COMPLIANT until configurations are pushed. Distinguish by checking whether the device count (`compliant + non_compliant`) increased in the same period. Suppress by tracking new devices separately and allowing a 48-hour onboarding grace period.

**Seasonal compliance audit preparation changing compliance behaviour.** Before a compliance audit, teams may run additional compliance checks or update templates, creating temporary turbulence in the trend. Distinguish by correlating with audit preparation schedules. No suppression needed — this is expected pre-audit activity.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Compliance endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-compliance-status)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [NIST SP 800-53 Rev. 5 — CM-6 Configuration Settings](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM-6)
