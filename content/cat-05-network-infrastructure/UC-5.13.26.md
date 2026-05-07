<!-- AUTO-GENERATED from UC-5.13.26.json — DO NOT EDIT -->

---
id: "5.13.26"
title: "Issue Distribution by Device and Site"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.26 · Issue Distribution by Device and Site

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We rank the noisiest network devices and the buildings they sit in by how many problems each one has. The devices and locations with the most problems show up at the top, so your team knows exactly where to send engineers first — instead of guessing where the trouble is.*

---

## Description

Maps active Assurance issues to specific devices and sites, ranking by issue concentration to identify problem hotspots — the noisiest devices and the most troubled locations — so operations sends engineers to the exact trouble spots instead of guessing.

## Value

UC-5.13.21 tells you what issues exist; this UC tells you *where they cluster*. A device with 15 unique issues is either failing catastrophically or misconfigured. A site with 40 issues across 10 devices has a systemic infrastructure problem (power, cooling, upstream). Ranking by concentration focuses remediation on the highest-impact locations and devices. The `issue_types` dimension distinguishes a device with 15 instances of one issue (persistent known problem) from 15 different issue types (broad failure — likely failing hardware).

## Implementation

Same `issue` input as UC-5.13.21. Use `dc(issueId)` for unique issue count and `dc(name)` for issue type breadth. Enrich with `catalyst_site_lookup`. Schedule weekly.

## Detailed Implementation

### Prerequisites
- UC-5.13.21 (Issue Summary) must be operational — same `issue` data feed.
- `deviceName` (or `deviceId`) must be populated in issue events. Some issue types (global/control-plane) may not have a device association — handle with `| eval deviceName=coalesce(deviceName, "(no device)")`.
- `siteId` populated for site-level distribution. Use `catalyst_site_lookup` for human-readable site names (UC-5.13.5 or UC-5.13.51).
- This is a **walk-tier** dimensional breakdown for operations, not real-time alerting. The audience is the weekly operations review.

### Step 1 — Configure data collection
Same `issue` input as UC-5.13.21. No additional configuration.

Confirm device-level issue data is available:
```spl
index=catalyst sourcetype="cisco:dnac:issue" status!="RESOLVED" earliest=-7d
| stats dc(deviceName) as devices_with_issues dc(issueId) as total_issues
```
If `devices_with_issues = 0`, all issues are global/control-plane issues without device associations.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:issue" status!="RESOLVED"
| stats dc(issueId) as unique_issues dc(name) as issue_types by deviceName, siteId
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site_label=coalesce(siteName, siteId)
| sort -unique_issues
| head 20
```

Why `dc(issueId)` not `count`: `count` inflates with poll frequency (same issue counted every 15 minutes). `dc(issueId)` gives the actual number of distinct active issues per device. A device with `dc(issueId) = 15` genuinely has 15 different active problems.

Why `dc(name) as issue_types`: distinguishes concentrated vs distributed problems.
- `unique_issues=15, issue_types=1`: one persistent issue type across 15 instances (e.g., 15 clients failing onboarding on the same switch). One root cause.
- `unique_issues=15, issue_types=12`: 12 different problem types (connectivity, performance, onboarding, compliance). The device is broadly failing — likely hardware issue or severe misconfiguration.

Why `status != "RESOLVED"`: focuses on active issues. Including resolved would show historical hotspots.

For site-level distribution (which sites have the most issues):
```spl
index=catalyst sourcetype="cisco:dnac:issue" status!="RESOLVED"
| stats dc(issueId) as site_issues dc(deviceName) as affected_devices dc(name) as issue_types by siteId
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site_label=coalesce(siteName, siteId)
| sort -site_issues
| head 20
```

For historical hotspot analysis (30-day view including resolved):
```spl
index=catalyst sourcetype="cisco:dnac:issue" earliest=-30d
| stats dc(issueId) as total_issues dc(name) as issue_types dc(eval(if(status="RESOLVED",issueId,null()))) as resolved by deviceName
| eval unresolved=total_issues-resolved
| eval resolution_rate=round(resolved*100/total_issues,1)
| sort -total_issues
| head 20
```

For the scatter plot (unique_issues vs issue_types — identify broadly-failing devices):
```spl
index=catalyst sourcetype="cisco:dnac:issue" status!="RESOLVED"
| stats dc(issueId) as unique_issues dc(name) as issue_types by deviceName
| where unique_issues > 3
```
Devices in the top-right quadrant (many issues AND many types) are the highest priority.

For priority-weighted ranking:
```spl
index=catalyst sourcetype="cisco:dnac:issue" status!="RESOLVED"
| eval weight=case(priority="P1",4, priority="P2",3, priority="P3",2, 1==1,1)
| stats dc(issueId) as unique_issues sum(weight) as weighted_score by deviceName, siteId
| sort -weighted_score
| head 20
```

Schedule as Report: weekly (cron `0 7 * * 1`). The site variant monthly for regional operations.

### Step 3 — Validate
(a) Pick the top device from the results. Open **Catalyst Center > Assurance > Issues** and filter by that device name. The issue count should match `unique_issues` within one poll cycle.

(b) Verify `issue_types` makes sense: a device with `unique_issues=5, issue_types=5` has 5 different problems. A device with `unique_issues=5, issue_types=1` has one type detected 5 separate times — different root cause investigation.

(c) Cross-reference with UC-5.13.1 (Device Health): do the top issue-generators also have the lowest health scores? If yes, consistent. If a device has many issues but high health, investigate — the issues may be P4 informational.

(d) Sum `unique_issues` across the top 20. Often 80% of issues come from 20% of devices (Pareto principle). If the concentration is lower, the problems are more distributed.

(e) Vendor UI parity: open **Catalyst Center > Assurance > Issues** and sort by device. The top devices should appear in both views.

(f) Check for null-device issues: `| where isnull(deviceName) | stats dc(issueId)`. These are global issues — report separately.

### Step 4 — Operationalize
Dashboard placement (on the "Issue Triage" dashboard or a dedicated "Issue Hotspots" dashboard):
- Table: top 20 devices by unique_issues, with site_label, issue_types. Colour-code: unique_issues > 10 = red, 5–10 = orange, < 5 = yellow.
- Treemap: sites as parent rectangles, devices as child rectangles, sized by unique_issues.
- Scatter plot: unique_issues (x) vs issue_types (y). Top-right = broadly failing.
- Drilldown: click a device → filter UC-5.13.21 to that `deviceName`.

Runbook (owner: Operations, weekly review):
1. Review the top 20 noisiest devices.
2. For devices with high `unique_issues` AND high `issue_types` (many distinct problems):
   - Check hardware health: `show environment all`, `show inventory`, `show platform`.
   - Check firmware: is it known-buggy? Cross-reference with UC-5.13.34 (PSIRTs).
   - If hardware degraded: plan RMA. If firmware: plan upgrade.
3. For devices with high `unique_issues` but low `issue_types` (one recurring problem):
   - This is a persistent issue. Feed into UC-5.13.25 (Recurring Issues) for Problem Management.
   - Common: a switch where all clients fail onboarding → RADIUS policy or VLAN configuration issue.
4. For the top 5 noisiest sites: check whether issues concentrate on one device (device problem) or spread across many (site problem — power, cooling, upstream link, DHCP).
5. Track week-over-week: are the same devices at the top? If yes, remediation isn't working — escalate.

Capacity planning:
- Sites with consistently high issue concentration need infrastructure investment.
- Track `site_issues / affected_devices` ratio: > 3 means each device has multiple problems (systemic). Near 1 means one issue per device (distributed).

### Step 5 — Troubleshooting

- **`deviceName` is null for many issues** — some Assurance issue types (global, control-plane) aren't tied to a specific device. Group nulls: `| eval deviceName=coalesce(deviceName, "(no device)")`. Report separately.

- **Same device appears at the top every week** — chronic unresolved issues. Escalate to Problem Management (UC-5.13.25).

- **`siteId` is null** — devices not assigned to a site in Catalyst Center. Filter with `| where isnotnull(siteId)`.

- **Issue count much higher in Splunk than the GUI** — `dc(issueId)` across a long time range captures issues that were resolved and re-opened. Narrow to `earliest=-1h` for exact parity with the GUI's current view.

- **Treemap is too dense** — with 200+ sites, filter to `| head 20` or use the site-level variant.

- **Device with high issue count but no user complaints** — issues may be P4 informational. Check priority: `| stats count by priority` for that device.

- **Cross-product issues inflate device counts** — an ISE failure generates onboarding issues for dozens of devices. The root cause is ISE. Check `category="Onboarding"` and correlate with UC-5.13.14/UC-5.13.68.

- **Search is slow** — narrow to `earliest=-24h` for the active snapshot. Use summary indexing for monthly historical views.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" status!="RESOLVED"
| stats dc(issueId) as unique_issues dc(name) as issue_types by deviceName, siteId
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site_label=coalesce(siteName, siteId)
| sort -unique_issues
| head 20
```

## Visualization

(1) Table: deviceName, site_label, unique_issues, issue_types — top 20 sorted by unique_issues. (2) Treemap: site (parent) → device (child), sized by unique_issues. (3) Scatter: unique_issues (x) vs issue_types (y) — top-right quadrant = broadly failing. (4) Bar chart: top 10 sites by total unique_issues.

## Known False Positives

**Single device with a persistent issue inflating that device's issue count.** A device with an unresolved bug generates an issue event every poll. `dc(issueId)` handles this — it counts unique issues, not poll events.

**Lab or PoC devices generating issues that are not operationally relevant.** Suppress with a `catalyst_excluded_devices` lookup.

**Site hierarchy change reassigning devices to different siteId values.** When the hierarchy is reorganised, issues shift between siteIds. Track by `deviceName` (stable) when investigating anomalies.

**Cross-product issues showing the correlating device as the source.** ISE authentication failures may be attributed to a device rather than ISE. Check `category` — cross-product issues often have specific category names.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Issues endpoint](https://developer.cisco.com/docs/catalyst-center/#!issues)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Catalyst Center Site Topology API](https://developer.cisco.com/docs/catalyst-center/#!get-site-topology)
