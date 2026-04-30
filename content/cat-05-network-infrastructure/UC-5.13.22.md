<!-- AUTO-GENERATED from UC-5.13.22.json — DO NOT EDIT -->

---
id: "5.13.22"
title: "Assurance Issue Trending Over Time"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.22 · Assurance Issue Trending Over Time

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We draw a chart showing how many network problems exist over time — day by day, week by week. When the number goes up, things are getting worse. When it goes down, fixes are working. Spikes in the chart usually mean something changed that broke things, and the chart helps your team find what that was and prove whether their fixes actually helped.*

---

## Description

Tracks the volume and priority distribution of Assurance issues over time, showing whether the backlog is growing, shrinking, or oscillating — and whether P1/P2 spikes correlate with changes, maintenance windows, or recurring infrastructure problems that haven't been properly root-caused.

## Value

UC-5.13.21 shows today's backlog. This UC shows the *story* — are there more issues this week than last? Did that firmware push reduce P2 issues? Is the same 'AP Unreachable' issue recurring every Tuesday? The trend line answers the three questions your operations manager asks in every weekly meeting: (1) Is it getting better or worse? (2) What caused that spike? (3) Is our remediation effort working? Since Catalyst Center's own Assurance window is 7 days, Splunk provides the only long-term issue trend for quarterly reviews and year-over-year comparison.

## Implementation

Same `issue` input as UC-5.13.21. No additional configuration. Use `dc(issueId)` not `count` for unique issue trending. Place below UC-5.13.21's summary table on the Issue Triage dashboard.

## Detailed Implementation

### Prerequisites
- UC-5.13.21 (Issue Summary) must be operational — same `issue` data feed.
- Retain **30–90+ days** of issue data for meaningful trending. The `issue` sourcetype scales with active issue count (~1.7 MB/day for 30 active issues), so long retention is affordable.
- Agree with operations on the trending granularity:
  - `span=1h`: for incident investigation (high detail, noisy for weekly views)
  - `span=4h`: for weekly views (balanced — 42 data points per week)
  - `span=1d`: for monthly/quarterly views (cleaner lines, one point per day)
  - `span=1w`: for annual comparison (52 points per year)

### Step 1 — Configure data collection
Same `issue` input as UC-5.13.21. No additional configuration.

Confirm sufficient history:
```spl
index=catalyst sourcetype="cisco:dnac:issue" earliest=-30d
| stats earliest(_time) as first latest(_time) as last dc(issueId) as total_issues
| eval days=round((last-first)/86400,1)
| table first, last, days, total_issues
```
If `days < 7`, wait until enough data accumulates for meaningful trending.

### Step 2 — Create the search and dashboard panel
```spl
index=catalyst sourcetype="cisco:dnac:issue"
| timechart span=4h dc(issueId) as unique_issues by priority
```

Why `dc(issueId)` not `count`: the `issue` API returns every active issue on each poll. `count` gives event count (= active_issues × polls_in_bucket), which inflates with poll frequency. `dc(issueId)` gives the actual number of unique issues observed in each time bucket — the operationally meaningful metric. Example: 10 active issues polled 4 times in a 4-hour bucket → `count = 40` (misleading), `dc(issueId) = 10` (accurate).

Why `span=4h`: balances detail (enough resolution to see intra-day spikes) with readability (not too noisy for 7–30 day views). A 7-day view at `span=4h` produces 42 data points — readable as a line chart. A 30-day view at `span=4h` produces 180 points — still usable but consider `span=1d` for cleaner executive presentation.

Why `by priority`: produces separate series for P1, P2, P3, P4. A growing P1 count is a very different signal from a growing P4 count. The stacked area chart makes the priority mix immediately visible. When P1 grows while P3/P4 stay flat, the network is developing new high-impact problems.

For active-only trending (excluding resolved issues the TA might still report):
```spl
index=catalyst sourcetype="cisco:dnac:issue" status!="RESOLVED"
| timechart span=4h dc(issueId) as active_issues by priority
```

For issue resolution rate overlay (are we closing faster than opening?):
```spl
index=catalyst sourcetype="cisco:dnac:issue"
| eval is_resolved=if(status="RESOLVED",1,0)
| timechart span=1d dc(issueId) as total dc(eval(if(status="RESOLVED",issueId,null()))) as resolved dc(eval(if(status!="RESOLVED",issueId,null()))) as active
| eval resolution_rate=round(resolved*100/total,1)
```

For week-over-week comparison (executive dashboard):
```spl
index=catalyst sourcetype="cisco:dnac:issue"
| eval week=if(_time > relative_time(now(), "-7d@d"), "This week", "Last week")
| eval plot_time=if(week="Last week", _time + 604800, _time)
| timechart span=4h dc(issueId) as unique_issues by week
```

This is a dashboard panel, not an alert. For alerting on issue count spikes, use UC-5.13.27 (Issue Volume Anomaly Detection). Schedule weekly for the operations review.

### Step 3 — Validate
(a) Run the search over the last 7 days. The stacked area should show a recognisable pattern: typically more issues during business hours (more clients connected, more change activity) and fewer on weekends (reduced load and fewer human-initiated changes).

(b) Compare the average daily `unique_issues` count with the count shown in **Catalyst Center > Assurance > Issues**. They should be in the same range — though Catalyst Center shows the current snapshot while this timechart shows historical unique issues per time bucket.

(c) Known incident check: if your team responded to a network event last week, there should be a visible spike in the chart at that time. If the spike is absent, the poll interval may be too wide (900s) to capture short-lived events.

(d) Verify `dc(issueId)` is materially different from `count`: run `| stats count, dc(issueId) as unique` over the same window. If `count ≈ unique`, the TA may be de-duplicating already (good). If `count >> unique` (typical), the `dc()` is essential for accurate trending.

(e) Check that all priority values appear: `| stats dc(issueId) by priority`. If P1 is always 0, that's good (no critical issues) — but verify with the Catalyst Center UI to confirm no P1 issues are being missed.

(f) Vendor UI parity: open **Catalyst Center > Assurance > Issues** and compare the priority breakdown with the Splunk chart for the same time period. Directional agreement expected.

### Step 4 — Operationalize
Dashboard placement (on the "Issue Triage" dashboard, below UC-5.13.21's summary table):
- Full-width stacked area chart: `unique_issues` by priority over the selected time range.
- Time-picker presets: "Last 24 hours" (incident review), "Last 7 days" (weekly ops), "Last 30 days" (monthly review), "Last 90 days" (quarterly).
- Colour coding: P1 red, P2 orange, P3 yellow, P4 grey — consistent with UC-5.13.21.
- Annotations: overlay maintenance windows and change events from `catalyst_maintenance_windows` or `index=catalyst sourcetype="cisco:dnac:audit:logs"` so viewers can correlate spikes with known activity.

Interpretation guide (add to dashboard documentation or tooltip):
- **Steady decline over weeks**: remediation is outpacing new issues — the team is reducing the backlog.
- **Steady incline over weeks**: the network is degrading, Assurance is detecting more issues, or issues are not being resolved. Investigate root causes with UC-5.13.25 (Recurring Issues).
- **Sharp spike that recovers**: transient event (maintenance window, change, or upstream failure). Correlate with the audit log (UC-5.13.46) for the change that caused it.
- **Flat line at a persistently high volume**: chronic backlog of unresolved issues. These need Problem Management attention, not more alerting. Feed into UC-5.13.25.
- **P1/P2 growing while P3/P4 are flat**: genuine new high-impact problems emerging, not just reclassified informational issues.
- **P4 growing while P1–P3 are flat**: Assurance is adding informational detections (common after Catalyst Center upgrades). Not operationally concerning — consider filtering P4 from the operational chart.

Weekly operations review:
- Compare this week vs last week: `| timechart span=1d dc(issueId) | eval week=if(_time>relative_time(now(),"-7d@d"),"this","last")`.
- Key questions: did the total issue count go up or down? Did the P1/P2 share change? Did any new issue names appear (cross-reference with UC-5.13.21 table)?

Monthly capacity review:
- Export the 30-day trend as CSV for the capacity review deck.
- Overlay with device count growth (from UC-5.13.51) and client count growth (from UC-5.13.40) to normalise issue volume against fleet size. A growing issue count is less alarming if the fleet is also growing proportionally.

### Step 5 — Troubleshooting

- **Chart shows a flat high line with no variation** — you're using `count` instead of `dc(issueId)`. The same issues are being counted on every poll. Switch to `dc(issueId)`.

- **Chart shows zero issues for extended periods** — the `issue` input stopped running. Check `index=_internal sourcetype=splunkd "TA_cisco_catalyst" ERROR` for the gap period. Or the network genuinely had zero active issues (rare but possible for a small, well-managed fleet).

- **Spike to very high numbers after TA or Catalyst Center upgrade** — the API may have returned historical/resolved issues on the first poll after the upgrade. Narrow to `status!="RESOLVED"` if the TA doesn't filter resolved issues. Or the Assurance engine added new detection categories in the upgrade, genuinely increasing the issue count.

- **P4 dominates the chart making other priorities invisible** — filter P4 out for the operational view: `| where priority IN ("P1","P2","P3")`. Show P4 in a separate informational chart for the weekly review.

- **Issue count in Splunk doesn't match Catalyst Center** — the GUI shows the *current* snapshot; this timechart shows *historical* unique issues per time bucket. They measure different things. The timechart value for the most recent bucket should approximate the GUI count.

- **Resolution rate appears negative or > 100%** — if using the resolution rate overlay, ensure the resolved count uses the same `issueId` field. A resolved issue that was opened in a previous time bucket creates a mismatch. Use per-day buckets for resolution rate stability.

- **Chart shows different patterns for different time ranges** — expected. The `span=4h` with a 7-day view shows 42 data points. The same `span=4h` with a 30-day view shows 180 data points. The pattern shape may change as you zoom out because short spikes are averaged within longer observation windows.

- **Stale data during weekends** — if the TA runs but no new issues appear (weekends with no operational problems), the chart shows flat lines, not gaps. This is correct — it represents stable issue counts, not missing data.

- **Want to compare two arbitrary time periods** — use the week-over-week variant from Step 2 with adjusted `relative_time()` offsets. This is useful for before/after comparison around a major change.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue"
| timechart span=4h dc(issueId) as unique_issues by priority
```

## Visualization

(1) Stacked area chart: `unique_issues` by `priority` over time (P1 red, P2 orange, P3 yellow, P4 grey). (2) Stat panel: total unique issues today vs 7-day average vs 30-day average — showing improvement or degradation. (3) Change-window annotations from `catalyst_maintenance_windows` or audit log events. (4) Optional week-over-week overlay for executive comparison.

## Known False Positives

**Issue re-counting across poll cycles inflating trend volume.** If using raw `count` instead of `dc(issueId)`, the same active issue is counted in every poll, making the trend appear flat-high even when the actual backlog is small. Distinguish by comparing `count` vs `dc(issueId)` — if `count >> dc(issueId)`, the inflation is the explanation. This UC's default SPL uses `dc(issueId)` which avoids this.

**P4 informational issues dominating the chart.** P4 issues (sync status, recommendations) can outnumber P1–P3 combined, making the stacked area appear alarming when the operational issues are stable. Distinguish by hiding P4 in the chart or showing it as a muted colour. Suppress with `| where priority IN ("P1","P2","P3")` for operational dashboards.

**Catalyst Center upgrade adding new issue detection categories.** After an upgrade, Assurance may detect new issue types it previously didn't, creating an apparent spike in the trend. Distinguish by checking `| stats earliest(_time) as first_seen by name` for issue names that appeared coincident with the upgrade. Annotate the trend chart with the upgrade date.

**Issue backlog growing during holidays.** If no one resolves issues during a holiday period, the backlog grows — not because more issues are appearing, but because fewer are being closed. Distinguish by checking `| timechart dc(eval(if(status="RESOLVED",issueId,null()))) as resolved` alongside the open count.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Issues endpoint](https://developer.cisco.com/docs/catalyst-center/#!issues)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Splunk timechart command reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Timechart)
