<!-- AUTO-GENERATED from UC-3.6.2.json — DO NOT EDIT -->

---
id: "3.6.2"
title: "Container Image Vulnerability Trending"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.6.2 · Container Image Vulnerability Trending

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Vulnerability, Security, Compliance &middot; **Wave:** Crawl &middot; **Status:** Verified

*Each day we chart how many known security flaws exist across all our software packages, tracking whether the number is going up or down over weeks, so management can tell if the team is fixing problems faster than new ones appear.*

---

## Description

Tracks **critical** and **high** CVE counts per container image and across the entire registry over 30-day windows, computing 7-day moving averages and directional trends (rising, falling, stable) to answer whether patch management and base-image updates are reducing the vulnerability backlog or if new discoveries are outpacing remediation.

## Value

A single point-in-time scan tells you what is vulnerable now, but only a trend tells you whether your security posture is improving. Rising critical CVE counts signal that remediation is falling behind new discoveries — evidence that warrants increasing patch cadence, shifting base images, or escalating to engineering leadership before compliance deadlines arrive.

## Implementation

Ingest Trivy and Grype scan results via HEC into index=containers. Build two search variants: a 30-day aggregate trend with 7-day SMA for critical/high CVE counts and directional classification, and a per-image weekly trajectory analysis that labels each image as IMPROVING, DEGRADING, STABLE, or NEW. Alert when the cluster-wide critical CVE trend direction is RISING for 3+ consecutive days or when any image's trajectory is DEGRADING.

## Detailed Implementation

### Prerequisites
- **Trivy** 0.45+ or **Grype** 0.70+ integrated into **CI/CD pipeline**s with **daily scheduled re-scans** of the entire registry so trend data reflects both newly pushed images and newly discovered CVEs against existing images.
- **Harbor** 2.6+ with **scan-on-push** enabled and a scheduled scan policy running nightly against all artifacts — trending requires consistent daily scan cadence to produce meaningful slopes.
- **Splunk HEC** token for **`index=containers`** with default **`sourcetype=trivy:scan`**; secondary stream for **`sourcetype=grype:scan`**; **Splunk Connect for Kubernetes** providing **`sourcetype=kube:container:status`** and **`sourcetype=kube:deployment:status`** for running-image context.
- At least **14 days of historical scan data** in **`index=containers`** before the trend searches produce meaningful 7-day SMAs; 30 days is ideal for the primary search. Set index **retention** to at least **90 days** for vulnerability trend analysis.
- **Splunk REST API Modular Input** (**rest_ta**, **Splunkbase 1546**) on a **heavy forwarder** if using the **Harbor vulnerability API** polling path from UC-3.4.2.
- **RBAC**: Splunk users running trend searches need **`srchIndexesAllowed`** including `containers`; assign via a custom role (**`vuln_analyst`**).
- **License estimate**: vulnerability trending adds no new data beyond UC-3.4.2 — the same **scan reports** feed both point-in-time and trend searches.

### Step 1 — Configure data collection
(1) **Consistent scan cadence**: the quality of trend analysis depends on scanning the same images at regular intervals. Configure a **nightly scheduled scan** in **Harbor** (Project → Configuration → **Scan schedule** → set cron `0 2 * * *`) that re-scans all artifacts in the project. This ensures that new CVEs published overnight appear in the next day's scan results even for images that were not rebuilt.

(2) **CI/CD pipeline scans**: every `docker build` in the CI/CD pipeline should trigger a scan and POST results to **Splunk HEC** as **`sourcetype=trivy:scan`** or **`sourcetype=grype:scan`** (see UC-3.4.2 Step 1 for detailed setup). The pipeline scan captures vulnerabilities introduced by code changes and dependency updates, while the **nightly scheduled scan** captures newly published CVEs against existing images.

(3) **Image lifecycle metadata**: collect **`sourcetype=kube:deployment:status`** to map image references to namespaces and deployment owners. This allows the trending dashboard to filter by team ownership — a "my images" view shows each team only their vulnerability trajectory.

(4) **Scan-result normalization**: reuse the field-extraction logic from UC-3.4.2 — the **`coalesce`** chains handle **Trivy**'s `VulnerabilityID`, `Severity`, `PkgName`, `InstalledVersion`, `FixedVersion`, `Target` and **Grype**'s `id`, `severity`, `package.name`, `package.version`, `fix.versions{}`, `artifact_name`.

(5) **CVE exceptions lookup**: reference the **`cve_exceptions.csv`** lookup from UC-3.4.2 to exclude accepted-risk CVEs from trending counts — this prevents known-accepted risks from distorting the trend direction.

### Step 2 — Create the search and alert
The primary SPL computes **daily aggregate vulnerability counts** by severity tier across all scanned images. The **`trendline sma7`** command smooths daily fluctuations to reveal the underlying direction: a 7-day **simple moving average** for both **critical** and **high** CVE counts.

The **`critical_direction`** field compares today's critical count against the SMA: if today exceeds the SMA by more than 20%, the direction is `RISING`; if today is more than 20% below the SMA, it is `FALLING`; otherwise `STABLE`. The 20% threshold prevents noise from triggering direction changes on small daily fluctuations.

The **`fix_ratio`** field measures what percentage of critical/high CVEs have available patches — a high fix ratio means the team can act immediately; a low ratio means new discoveries are in packages without upstream fixes.

The per-image variant uses **`streamstats`** to compare each image's weekly critical/high count against the prior week. A delta > 3 flags the image as `DEGRADING` (more critical/high CVEs than last week), delta < -3 as `IMPROVING` (successful remediation), otherwise `STABLE`. The **`sparkline`** column provides an inline visual of the weekly trajectory.

Schedule the **aggregate trend search** daily at **07:00** over **`-30d`** and alert when `critical_direction=RISING` for **3 consecutive days** (use `| eventstats count(eval(critical_direction="RISING")) as rising_streak` over the last 3 rows). Schedule the **per-image trajectory** weekly and alert when any production image has trajectory `DEGRADING` with `current_crit_high > 5`.

### Step 3 — Validate
(a) Verify **scan data consistency**: `index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan") | bin _time span=1d | stats dc(Target) as images_scanned by _time | sort _time`. The `images_scanned` count should be roughly consistent day-to-day; gaps indicate missed scheduled scans.
(b) Cross-check with Harbor: in the **Harbor UI** → **Projects** → select a project → **Artifacts** → check the vulnerability summary column. Compare critical/high counts with Splunk: `index=containers sourcetype="trivy:scan" Target="<image>" earliest=-1d | stats dc(eval(if(Severity="CRITICAL", VulnerabilityID, null()))) as critical`. Counts should match within ±5%.
(c) Test **trend direction**: push a deliberately vulnerable base image (e.g., `debian:stretch` with known critical CVEs) daily for 3 days. The trend search should show `critical_direction=RISING` by day 3.
(d) Verify **per-image trajectory**: rebuild an image with updated base (e.g., upgrade from `alpine:3.14` to `alpine:3.19`), scan, and confirm the trajectory search labels it as `IMPROVING` in the next weekly run.
(e) Confirm **sparkline rendering**: the `sparkline()` function requires at least 3 data points (3 weeks) to render meaningfully; verify with `| stats **sparkline**(weekly_crit_high) as spark by image_base`.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **dual-axis line chart** — critical CVE count as bars (left axis) with **7-day SMA** as a trend line (right axis) over 30 days; a rising SMA line is the primary signal that remediation is falling behind.
- Row B: **single-value tiles** — critical CVE trend direction (RISING=red, STABLE=yellow, FALLING=green), **fix ratio** %, images scanned today, images with DEGRADING trajectory.
- Row C: **stacked area chart** of critical/high/medium CVE counts over 30 days — shows whether severity composition is shifting.
- Row D: **per-image trajectory table** — columns: image_base, current_crit_high, trend, last_delta, sparkline. Drilldown opens the image's full CVE detail (UC-3.4.2).
- **Alerting**: critical trend `RISING` for 3+ days → email to **engineering leads** and **AppSec**; any production image trajectory `DEGRADING` with > 5 critical/high → **Jira** ticket; fix ratio below 50% → weekly escalation to security management.
- **Runbook** (owner: AppSec weekly review): (1) identify the top 5 images contributing most to the rising trend, (2) check whether the increase is from new CVE publications (same images, new CVEs) or from new images introduced with existing vulnerabilities, (3) for new CVEs: check **NVD** advisories and vendor patches; for new images: escalate to the owning team, (4) update **`cve_exceptions.csv`** for accepted risks with expiry dates.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: pair the 30-day trend chart with a **waterfall chart** showing weekly CVE additions vs. remediations to decompose the net change; add a **team ownership treemap** sized by `current_crit_high` and colored by `trajectory` so leadership sees which teams carry the most risk; use **conditional formatting** on the trajectory table to highlight DEGRADING rows in red.
- **Alert design**: include `critical_direction`, `critical_cves`, `critical_sma_7d`, `fix_ratio`, and the top 3 DEGRADING images with their `current_crit_high` and `last_delta` in the alert payload; add a **deep-link** to the trending dashboard filtered to the current 30-day window.
- **Trend shows RISING but scan count dropped** — fewer images scanned means the denominator shrunk while the numerator stayed constant; check whether the nightly scheduled scan completed: `index=containers sourcetype="harbor:webhook" event_type="SCANNING_COMPLETED" earliest=-24h | stats count`. Zero results mean the scan job failed.
- **All images show NEW trajectory** — the `streamstats` window requires at least 2 weekly data points; new images without prior scan history are labeled `NEW` by design. Wait for the second weekly scan cycle.
- **Sparkline column is empty** — requires at least 3 data points at the `span=7d` granularity (21 days of data). Verify **retention** and scan cadence.
- **Fix ratio is 100% but critical count is rising** — new CVEs are being discovered in packages that have upstream patches available, but the patches are not being applied. Escalate to engineering with the **patch-priority list** from UC-3.4.2.
- **Grype and Trivy produce different trends for the same image** — expected due to different vulnerability database update schedules; standardize on a single scanner for trending or use the `scanner` field to filter to one source for consistent trend lines.

## SPL

```spl
`comment("--- Image Vulnerability Trending — Critical/High CVE Counts Over 30 Days ---")`
index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan")
| eval cve_id=coalesce(VulnerabilityID, id, vulnerability)
| eval severity=upper(coalesce(Severity, severity, "UNKNOWN"))
| eval image_ref=coalesce(Target, artifact_name, image, "unknown")
| eval image_base=mvindex(split(image_ref, ":"), 0)
| eval cvss_score=tonumber(coalesce('CVSS.nvd.V3Score', 'cvss.value', cvss_v3_score, "0"))
| eval fixed_ver=coalesce(FixedVersion, fix.versions{}, "none")
| eval has_fix=if(fixed_ver!="none" AND fixed_ver!="", 1, 0)
| eval scan_date=strftime(_time, "%Y-%m-%d")
| bin _time span=1d
| stats dc(eval(if(severity="CRITICAL", cve_id, null()))) as critical_cves,
    dc(eval(if(severity="HIGH", cve_id, null()))) as high_cves,
    dc(eval(if(severity="MEDIUM", cve_id, null()))) as medium_cves,
    dc(cve_id) as total_cves,
    dc(eval(if(has_fix=1 AND severity IN ("CRITICAL","HIGH"), cve_id, null()))) as fixable_crit_high,
    dc(image_ref) as images_scanned,
    avg(cvss_score) as avg_cvss
    by _time
| eval fix_ratio=round(100 * fixable_crit_high / max(1, critical_cves + high_cves), 1)
| trendline sma7(critical_cves) as critical_sma_7d
| trendline sma7(high_cves) as high_sma_7d
| eval critical_direction=case(
    critical_cves > critical_sma_7d * 1.2, "RISING",
    critical_cves < critical_sma_7d * 0.8, "FALLING",
    1=1, "STABLE")
| table _time critical_cves high_cves medium_cves total_cves fixable_crit_high fix_ratio images_scanned avg_cvss critical_sma_7d critical_direction

`comment("--- Per-Image Vulnerability Trajectory — Improving vs Degrading ---")`
index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan")
| eval cve_id=coalesce(VulnerabilityID, id, vulnerability)
| eval severity=upper(coalesce(Severity, severity))
| eval image_base=mvindex(split(coalesce(Target, artifact_name, image, "unknown"), ":"), 0)
| eval is_crit_high=if(severity IN ("CRITICAL","HIGH"), 1, 0)
| bin _time span=7d
| stats dc(eval(if(is_crit_high=1, cve_id, null()))) as weekly_crit_high,
    dc(cve_id) as weekly_total
    by image_base, _time
| sort image_base _time
| streamstats window=2 current=f last(weekly_crit_high) as prev_crit_high by image_base
| eval delta=weekly_crit_high - prev_crit_high
| eval trajectory=case(
    isnull(prev_crit_high), "NEW",
    delta > 3, "DEGRADING",
    delta < -3, "IMPROVING",
    1=1, "STABLE")
| stats latest(weekly_crit_high) as current_crit_high,
    latest(trajectory) as trend,
    latest(delta) as last_delta,
    sparkline(weekly_crit_high) as sparkline
    by image_base
| sort -current_crit_high
| head 50
| table image_base current_crit_high trend last_delta sparkline
```

## Visualization

Dual-axis line chart (critical CVEs + 7-day SMA over 30 days), stacked area by severity tier, per-image trajectory sparklines, single-value tiles (critical trend direction, fix ratio, images degrading), treemap of current critical CVE distribution by image.

## Known False Positives

**cve_database_refresh_spike** — When Trivy or Grype update their vulnerability databases (typically daily), a batch of newly published CVEs appears across all images simultaneously, creating an artificial spike in the trending chart. The spike reflects new discoveries in the NVD, not changes in the images themselves. Compare the spike date with the scanner's database update timestamp and annotate the trend chart accordingly.

**scheduled_scan_gap** — If the nightly Harbor scheduled scan fails or is delayed (due to maintenance windows, resource contention, or job queue backlog), the trending chart shows a gap or zero-count day that artificially lowers the moving average. When the next scan runs, the accumulated counts create a false spike. Verify scan completion via `sourcetype=harbor:webhook event_type=SCANNING_COMPLETED` and interpolate missing days.

**base_image_mass_update** — When a team upgrades the base image across multiple images simultaneously (e.g., alpine 3.14 → 3.19), the per-image trajectory labels all affected images as IMPROVING in the same week, creating a misleading impression of broad remediation when only one base-image change drove the improvement. Group trending by base image tag to separate base-image effects from application-level fixes.

**scanner_version_drift** — Upgrading the scanner version (e.g., Trivy 0.45 → 0.50) can change CVE detection logic, adding or removing CVE matches for the same image. This creates a step change in the trend that does not reflect actual vulnerability changes. Note scanner version in scan metadata and annotate trend charts at upgrade boundaries.

**end_of_life_image_noise** — Images built on end-of-life OS distributions (e.g., Debian Stretch, Ubuntu 18.04) accumulate CVEs indefinitely because no patches will ever be released. These images inflate the DEGRADING trajectory count and should be flagged for retirement rather than patched. Filter by base OS EOL status using a lookup.

**test_image_churn** — Development and test pipelines that rebuild images frequently with experimental dependencies create high-frequency scan results that dominate the trending chart. Filter by image tag patterns (exclude `dev-*`, `test-*`, `snapshot-*`) or namespace to isolate production image trends.

## References

- [Trivy — Container Image Vulnerability Scanner](https://aquasecurity.github.io/trivy/)
- [Grype — Container Image Vulnerability Scanner](https://github.com/anchore/grype)
- [Harbor — Vulnerability Scanning Policies](https://goharbor.io/docs/2.10.0/administration/vulnerability-scanning/)
- [Splunk trendline Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Trendline)
- [NVD — National Vulnerability Database](https://nvd.nist.gov/)
