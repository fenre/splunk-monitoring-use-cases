<!-- AUTO-GENERATED from UC-5.13.36.json — DO NOT EDIT -->

---
id: "5.13.36"
title: "Advisory Trending and New Advisory Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.36 · Advisory Trending and New Advisory Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Vulnerability &middot; **Wave:** Walk &middot; **Status:** Verified

*We track how many security weaknesses affect your network over time — week by week, month by month. When the number goes down after your team patches devices, you can prove the investment worked. When it goes up, you know new vulnerabilities are appearing faster than fixes are being applied.*

---

## Description

Tracks the number and severity distribution of active security advisories over time, revealing whether the vulnerability exposure is growing (new advisories outpacing remediation), shrinking (firmware campaigns reducing exposure), or stable — the trend that drives the quarterly vulnerability management review.

## Value

UC-5.13.34 shows today's advisory snapshot. This UC shows the trajectory. A fleet with 15 active advisories today is fine if it was 30 last month (remediation is working). It's alarming if it was 5 last month (new exposures outpacing patches). The trend line answers the executive question: 'Is our vulnerability posture improving or degrading?' and proves that firmware investment is actually reducing exposure. For NIST RA-5, it demonstrates ongoing vulnerability scanning and remediation as a continuous process.

## Implementation

Same `securityadvisory` input as UC-5.13.34. Retain 90+ days. Use `timechart span=1w dc(advisoryId)` for weekly trending.

## Detailed Implementation

### Prerequisites
- UC-5.13.34 (PSIRT Overview) must be operational — same `securityadvisory` data feed.
- Retain **90+ days** of advisory data for meaningful trending. Advisory data is lightweight (~2.7 MB/day for a fleet with 20 advisories × 200 affected devices) so long retention is affordable.
- This UC serves the quarterly vulnerability management review — the audience is security leadership, not the day-to-day operations team.
- Agree with security leadership on the reporting cadence: monthly for operational review, quarterly for executive/compliance review.

### Step 1 — Configure data collection
Same `securityadvisory` input as UC-5.13.34. No additional configuration.

Confirm sufficient history:
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" earliest=-90d
| stats earliest(_time) as first latest(_time) as last
| eval days=round((last-first)/86400,1)
| table first, last, days
```

### Step 2 — Create the search and dashboard panel
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory"
| where deviceCount > 0
| timechart span=1w dc(advisoryId) as active_advisories by severity
```

Why `where deviceCount > 0`: counts only advisories that affect your fleet. Advisories with no affected devices are noise in the trend — they exist in the Cisco PSIRT database but don't represent exposure for YOUR network.

Why `span=1w`: weekly granularity smooths daily poll timing differences and produces clean lines for monthly/quarterly views. A 90-day view at `span=1w` produces 13 data points — readable and meaningful for trend analysis.

Why `dc(advisoryId)`: counts unique advisories per week. An advisory that persists across 4 weeks shows as 1 per week in each, not cumulative. The trend shows the active exposure count at each point in time, which is the operationally meaningful metric.

Why `by severity`: separate series for CRITICAL, HIGH, MEDIUM, LOW. The relative growth between series tells a story: if CRITICAL is growing while MEDIUM is shrinking, new critical vulnerabilities are being published faster than you're patching — a warning signal.

For remediation rate analysis (are we patching faster than new advisories appear?):
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory"
| stats earliest(_time) as first_seen latest(_time) as last_seen latest(deviceCount) as current_affected by advisoryId, severity
| eval was_active=if(current_affected > 0, "Still active", "Remediated")
| stats count by severity, was_active
```

For affected-device-count trending (total exposure over time):
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory"
| where deviceCount > 0
| timechart span=1w sum(deviceCount) as total_exposed by severity
```
This shows whether the total number of vulnerable device-advisory pairs is growing or shrinking — a declining line means firmware campaigns are reducing exposure.

Schedule: monthly (cron `0 7 1 * *`), output to PDF for the security review. Also quarterly for the executive report.

### Step 3 — Validate
(a) Run the trend over 90 days. The shape should reflect your organisation's firmware upgrade cadence: dips after upgrade campaigns, spikes when Cisco publishes new advisory batches (Cisco typically publishes security advisories in bi-annual bundles in March and September, plus ad-hoc publications for critical zero-days).

(b) Compare the most recent week's `active_advisories` with UC-5.13.34's current count. They should match.

(c) Cross-reference firmware campaign dates with dips in the trend. If you pushed IOS-XE 17.9.4a to 200 devices last month, advisories affecting 17.6.x and 17.3.x should show declining device counts.

(d) Compare the CRITICAL series with known zero-day publications. The 2023 IOS-XE Web UI vulnerability (CVE-2023-20198) would show as a spike in October 2023.

(e) Vendor UI parity: compare the overall trend direction with **Catalyst Center > Security Advisories > Summary**.

### Step 4 — Operationalize
- Quarterly security review: show the 90-day trend. A declining CRITICAL line = security posture improving. A growing line = exposure increasing. This is the metric that drives firmware investment decisions.
- Annotate the chart with firmware campaign dates: "17.9.4a push completed March 15 — 200 devices upgraded." The correlation between the push and the advisory count decline is the ROI evidence.
- For NIST RA-5 / SI-2: the trend demonstrates ongoing vulnerability scanning and remediation as a continuous process, not a one-time activity.

Runbook (owner: Security Operations Manager):
1. Monthly: review the advisory trend. Is the CRITICAL count going up or down?
2. If up: are these new Cisco publications (check publication dates) or are old advisories not being patched? If the latter, escalate firmware campaign urgency.
3. If down: which firmware campaigns contributed? Document the ROI.
4. Quarterly: prepare the executive vulnerability management report including the trend chart, remediation velocity metrics (from UC-5.13.38), and open advisory exceptions.

### Step 5 — Troubleshooting

- **Trend shows steady increase over months** — new Cisco advisories are being published faster than you're patching. This is a firmware upgrade capacity problem. Increase the firmware campaign cadence or invest in automated SWIM distribution.

- **Trend shows sudden spike** — Cisco published a batch of advisories (common during the bi-annual security advisory bundles). Check the Cisco PSIRT portal for the publication batch. A spike of 10+ advisories in one week is typically a bundle publication, not a fleet degradation.

- **Trend shows sudden drop to 0** — either all advisories were remediated (verify with `| stats dc(advisoryId)`) or the `securityadvisory` input stopped running (check `index=_internal`). A genuine drop to 0 is the ideal state.

- **`deviceCount > 0` filter removes all data** — your fleet may not be affected by any current advisories. This is the ideal state — your firmware is current. Continue monitoring monthly for newly published advisories.

- **Advisory count in the trend disagrees with Catalyst Center** — time window and deduplication differences. The timechart shows weekly unique advisory counts; the GUI shows the current snapshot. They measure different things.

- **Trend doesn't show remediation impact after firmware push** — the advisory-device mapping updates within 24 hours of firmware upgrade. If you pushed firmware on Friday, the Sunday advisory poll should show reduced deviceCount. If not, the upgrade may not have changed the affected firmware version (e.g., you upgraded to 17.9.3 but the advisory is fixed in 17.9.4a).

- **`severity` values changed between Catalyst Center versions** — Cisco may reclassify advisory severity based on new exploitation information. This shifts events between series in the chart — not a data error, but a genuine reclassification.

- **No data for some weeks** — data gap in the `securityadvisory` input. Check `index=_internal` for errors during those weeks. Document gaps for the compliance record.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory"
| where deviceCount > 0
| timechart span=1w dc(advisoryId) as active_advisories by severity
```

## Visualization

(1) Stacked area chart: `dc(advisoryId)` by severity over time (CRITICAL red, HIGH orange, MEDIUM yellow). (2) Line overlay: total affected device count trend. (3) Stat panel: advisory count this month vs last month vs 3 months ago. (4) Annotations: mark firmware campaign dates to show remediation impact.

## Known False Positives

**PSIRT database update generating apparent new advisory detections.** When Catalyst Center updates its PSIRT database, previously unknown advisories may appear for the first time even though the vulnerabilities are not new. Distinguish by checking the advisory's `publicationDate` — if it was published months ago but just detected, the PSIRT database was recently updated. Suppress by alerting on advisories where `publicationDate` is within the last 30 days as genuinely new, and treating older publications as database-update catches.

**Advisory reclassification changing severity between polls.** Cisco may update the severity of a published PSIRT (e.g., upgrading from HIGH to CRITICAL after exploitation is confirmed). Catalyst Center reflects this change. Distinguish by checking whether the `severity` changed for the same `advisoryId` between consecutive polls. Do not suppress — severity upgrades are operationally important.

**Same advisory appearing for different device UUIDs as more devices are scanned.** The initial scan may not cover all devices; subsequent polls include additional affected devices for the same advisory. Distinguish by tracking `dc(deviceId)` per `advisoryId` over time — an increasing count is normal as the scan completes. Suppress by waiting for the full scan to complete (typically 24 hours) before considering the advisory trending stable.

**Advisory with zero affected devices remaining in the feed.** After all affected devices are patched, the advisory may remain in the feed with `deviceCount=0` until Catalyst Center removes it. Distinguish by checking `deviceCount=0`. Suppress by filtering `| where deviceCount>0` for active advisory dashboards.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
- [Cisco PSIRT Security Advisories](https://sec.cloudapps.cisco.com/security/center/publicationListing.x)
