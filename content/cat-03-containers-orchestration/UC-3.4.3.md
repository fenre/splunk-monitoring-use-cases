<!-- AUTO-GENERATED from UC-3.4.3.json — DO NOT EDIT -->

---
id: "3.4.3"
title: "Storage Quota Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.4.3 · Storage Quota Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Availability, Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We measure how full the team's shared storage space is getting, alerting them when it is nearly full so they can clean up old files before new work gets blocked.*

---

## Description

Monitors **Harbor** project-level storage **quota usage** against configured limits by scraping `harbor_project_quota_usage_byte` and `harbor_project_quota_byte` metrics, computing usage percentages, growth rates, and days-to-full projections — surfacing projects approaching exhaustion before failed pushes break CI/CD pipelines.

## Value

A full registry quota silently blocks every image push in the affected project, halting CI/CD pipelines, deployment rollouts, and disaster-recovery replication without an obvious error beyond a cryptic HTTP 413. Proactive monitoring gives platform teams days or weeks of lead time to tune retention policies, archive old tags, or expand quotas before developers hit a wall.

## Implementation

Scrape Harbor's Prometheus metrics endpoint for project quota usage and limits using the Splunk OTel Collector or rest_ta. Build two search variants: real-time quota status by project with alert tiers, and 30-day growth rate trending with full-date projection. Alert when any project exceeds 85% usage or when projected growth exceeds the quota within 14 days.

## Detailed Implementation

### Prerequisites
- **Harbor** 2.6+ with **project-level quotas** configured (Project → Configuration → **Project Quotas** → set storage limit per project); the **Prometheus metrics** endpoint must be enabled in `harbor.yml` (`metric.enabled: true`, default port **9090**).
- **Splunk OpenTelemetry Collector** deployed as a **DaemonSet** via the `splunk-otel-collector-chart` **Helm chart** with the **Prometheus receiver** configured to scrape the **Harbor metrics endpoint** at `/metrics` on port 9090. Alternatively, use **rest_ta** (**Splunkbase 1546**) to poll the Harbor **project quota API**: `GET /api/v2.0/quotas`.
- **Splunk HEC** token for **`index=containers`** with default **`sourcetype=harbor:metrics`**; secondary stream for **`sourcetype=harbor:webhook`** (QUOTA_EXCEED events) and **`sourcetype=harbor:audit`** for administrative quota changes.
- **Harbor robot account** with project-level **read** scope on each monitored project — never reuse admin credentials for metric collection.
- **Kubernetes PersistentVolume monitoring**: if Harbor uses a **Kubernetes PersistentVolumeClaim** for storage, collect `kubelet_volume_stats_used_bytes` and `kubelet_volume_stats_capacity_bytes` via the OTel Collector's **kubelet stats receiver** as **`sourcetype=kube:metrics`** for the underlying filesystem view.
- Splunk RBAC: users running quota searches need **`srchIndexesAllowed`** including `containers`; assign via a custom role (**`registry_operator`**).
- **License estimate**: Harbor emits ~50 metric time series per project at 60s intervals; a 20-project registry generates ~2 MB/day of quota metrics.

### Step 1 — Configure data collection
(1) **Prometheus scraping** (recommended): add the **Harbor metrics endpoint** as a scrape target in the OTel Collector Prometheus receiver config. Harbor exposes these key quota metrics:
— **`harbor_project_quota_usage_byte`** (gauge: current storage used per project)
— **`harbor_project_quota_byte`** (gauge: configured quota limit per project)
— **`harbor_project_repo_count`** (gauge: number of repositories in each project)
— **`harbor_system_storage_free_byte`** (gauge: total free storage on the Harbor backend — shared across all projects)
Each metric is labeled with **`project_name`**. Verify the endpoint is reachable: `curl -s http://<harbor>:9090/metrics | grep harbor_project_quota`.

(2) **REST API polling** (alternative): configure **rest_ta** to poll `GET /api/v2.0/quotas` every **300 seconds**. The response includes per-project storage **`used`** and **`hard`** (limit) values plus repository and tag counts. Map to **`sourcetype=harbor:audit`** in `index=containers`.

(3) **Quota-exceed webhook**: subscribe to the **`QUOTA_EXCEED`** and **`QUOTA_WARNING`** webhook events in Harbor (same endpoint as UC-3.4.1). These fire when a push attempt would exceed the project quota, providing **real-time** notification of quota-blocked pushes.

(4) **Kubernetes PV monitoring**: if the Harbor **backing storage** is a Kubernetes PersistentVolume, collect **`kubelet_volume_stats_used_bytes`** and **`kubelet_volume_stats_capacity_bytes`** to monitor the underlying filesystem independently of Harbor's per-project quota view. A full PV blocks all projects regardless of individual quota settings.

(5) **Retention policy inventory**: create a lookup **`retention_policies.csv`** with columns `project`, `retention_rule`, `last_run`, `images_retained` to correlate quota growth with retention policy effectiveness.

### Step 2 — Create the search and alert
The primary SPL computes per-project **usage percentage** by dividing `quota_usage_byte` by `quota_byte`. The **`alert_tier`** classification provides escalation boundaries: **CRITICAL** (≥ 95%), **WARNING** (≥ 85%), **APPROACHING** (≥ 70%), and **HEALTHY** (< 70%).

The **`days_to_full`** field provides a rough linear projection based on current usage and the project's average daily consumption rate over the last 30 days. This is deliberately conservative — actual growth may be non-linear around release cycles.

The growth-rate variant uses **`streamstats`** to compute daily storage deltas per project, then projects 30 days forward using the average daily growth rate. The **`growth_direction`** classification flags fast-growing projects that will hit their quota within the projection window.

Schedule the quota-status search every **1 hour** and alert when any project reaches **CRITICAL** or **WARNING** tier. Schedule the growth-rate search **daily at 08:00** over **`-30d`** and alert when any project's **`projected_30d_gb`** exceeds its configured quota limit.

### Step 3 — Validate
(a) Cross-check with **Harbor UI**: navigate to **Administration → Project Quotas** and compare the usage/limit values with the Splunk search output. Values should match within the scrape interval.
(b) Test a quota-exceed scenario: set a project quota to a small value (e.g., 100 MB), push images until the limit is reached, and verify (i) the SPL shows `alert_tier=CRITICAL`, (ii) the QUOTA_EXCEED webhook arrives, and (iii) the push returns HTTP 413.
(c) Verify **PV monitoring**: `index=containers sourcetype="kube:metrics" metric_name="kubelet_volume_stats_used_bytes" | stats latest(value) by pod_name` — should include the Harbor data PVC.
(d) Confirm **growth trending**: the 30-day search should show a **line chart** with daily usage values and projected growth. If values are flat, push a few large images to create visible growth.
(e) Verify **retention correlation**: if a tag retention policy ran recently, the daily growth should show a negative delta (storage reclaimed) on that day.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **horizontal bar chart** of usage vs. limit per project — bars color-coded by **alert tier** (red/orange/yellow/green) with the limit shown as a reference line.
- Row B: **single-value tiles** — projects at CRITICAL, total registry storage used (all projects combined), average days-to-full, system-level free storage remaining.
- Row C: **growth trend line** per project over 30 days (line chart) with a dashed **projected line** extending 30 days forward — immediate visual for when each project hits its limit.
- Row D: **sortable table** — columns: project, usage_gb, limit_gb, usage_pct, remaining_gb, repo_count, days_to_full, growth_direction. Drilldown opens per-project image list.
- **Alerting**: project at CRITICAL (≥ 95%) → Slack `#registry-ops` + PagerDuty P3; project at WARNING (≥ 85%) → email to project owner; growth projection exceeds quota within 14 days → weekly digest to platform team.
- **Runbook** (owner: platform engineering on-call): (1) identify the project and check repo_count — high counts suggest a retention policy may be too lenient, (2) review **tag retention rules** in Harbor (Project → Tag Retention) and adjust, (3) for immediate relief: manually delete untagged artifacts via `harbor-cli artifact delete`, (4) if quota is genuinely insufficient: coordinate a quota increase via change request.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **gauge chart** per project showing usage percentage with color bands at 70/85/95% thresholds for an executive-friendly view; pair with a **capacity planning table** that combines current usage, growth rate, and projected full date so stakeholders can see exactly when action is needed; add a **stacked area chart** of usage by project over time to show which projects dominate storage consumption.
- **Alert design**: include `project`, `usage_gb`, `limit_gb`, `usage_pct`, `remaining_gb`, `days_to_full`, and `growth_direction` in every alert payload; for CRITICAL alerts add the top 5 largest repositories in the project from `harbor_project_repo_count` context; include a direct link to the Harbor project settings page for immediate quota adjustment.
- **Quota metrics show zero for all projects** — quotas may not be configured; verify in Harbor UI (Administration → Project Quotas) that limits are set. Harbor returns `0` for the limit when quotas are disabled (unlimited).
- **Usage exceeds limit but no QUOTA_EXCEED webhook** — the webhook fires only on **push attempts** that would exceed the limit, not when usage organically crosses the threshold via new CVE database updates. Use the metric-based alert as the primary detection, not webhooks.
- **PV usage does not match Harbor quota sum** — the PV includes non-project data (system databases, trivy cache, redis data). The PV metric is a supplementary view, not a direct comparison to project quotas.
- **Growth rate is negative but alert still fires** — tag retention ran and reclaimed storage, but the alert evaluates current usage_pct which remains above threshold. The alert is correct — reclaimed space was not enough.
- **days_to_full shows very large number** — the project's growth rate is near zero or negative; the linear projection is not meaningful for idle projects. Filter the dashboard to show only projects with `growth_direction=GROWING` or `GROWING_FAST`.

## SPL

```spl
`comment("--- Registry Storage Quota — Usage vs Limit by Project ---")`
index=containers (sourcetype="harbor:metrics" OR sourcetype="harbor:audit")
| eval metric=coalesce(metric_name, name)
| eval project=coalesce(project_name, project, label_project_name, "unknown")
| eval usage_bytes=if(match(metric, "quota_usage_byte"), tonumber(value), null())
| eval limit_bytes=if(match(metric, "quota_byte"), tonumber(value), null())
| eval repo_count=if(match(metric, "repo_count"), tonumber(value), null())
| stats latest(usage_bytes) as usage_bytes,
    latest(limit_bytes) as limit_bytes,
    latest(repo_count) as repo_count,
    latest(_time) as last_seen
    by project
| eval usage_gb=round(usage_bytes / 1073741824, 2)
| eval limit_gb=round(limit_bytes / 1073741824, 2)
| eval usage_pct=round(100 * usage_bytes / limit_bytes, 1)
| eval remaining_gb=round((limit_bytes - usage_bytes) / 1073741824, 2)
| eval alert_tier=case(
    usage_pct >= 95, "CRITICAL",
    usage_pct >= 85, "WARNING",
    usage_pct >= 70, "APPROACHING",
    1=1, "HEALTHY")
| eval days_to_full=if(usage_pct < 100, round(remaining_gb / max(usage_gb / 30, 0.001), 0), 0)
| sort -usage_pct
| table project usage_gb limit_gb usage_pct remaining_gb repo_count alert_tier days_to_full last_seen

`comment("--- Storage Growth Rate Trending — 30-Day Projection ---")`
index=containers sourcetype="harbor:metrics"
| where match(metric_name, "harbor_project_quota_usage_byte")
| eval project=coalesce(project_name, label_project_name)
| eval usage_gb=round(tonumber(value) / 1073741824, 2)
| bin _time span=1d
| stats latest(usage_gb) as daily_usage_gb by project, _time
| sort project _time
| streamstats window=7 avg(daily_usage_gb) as avg_7d by project
| streamstats window=2 current=f last(daily_usage_gb) as prev_day_gb by project
| eval daily_growth_gb=daily_usage_gb - prev_day_gb
| stats latest(daily_usage_gb) as current_gb,
    latest(avg_7d) as avg_7d_gb,
    avg(daily_growth_gb) as avg_daily_growth_gb,
    max(daily_growth_gb) as peak_daily_growth_gb
    by project
| eval projected_30d_gb=round(current_gb + (avg_daily_growth_gb * 30), 2)
| eval growth_direction=case(
    avg_daily_growth_gb > 0.5, "GROWING_FAST",
    avg_daily_growth_gb > 0, "GROWING",
    avg_daily_growth_gb < -0.1, "SHRINKING",
    1=1, "STABLE")
| sort -avg_daily_growth_gb
| join type=left project [search index=containers sourcetype="harbor:metrics"
    | where match(metric_name, "harbor_project_quota_byte")
    | eval project=coalesce(project_name, label_project_name)
    | eval limit_gb=round(tonumber(value) / 1073741824, 2)
    | stats latest(limit_gb) as quota_limit_gb by project]
| eval exceeds_quota=if(projected_30d_gb > quota_limit_gb, "YES", "NO")
| sort -avg_daily_growth_gb
| table project current_gb avg_7d_gb avg_daily_growth_gb peak_daily_growth_gb projected_30d_gb quota_limit_gb exceeds_quota growth_direction
```

## Visualization

Horizontal bar chart (usage vs limit by project, color-coded by alert tier), growth trend line per project over 30 days, single-value tiles (projects at CRITICAL, total registry storage used, average days-to-full), sortable project table.

## Known False Positives

**retention_reclaim_overshoot** — When Harbor runs a tag retention policy followed by garbage collection, storage usage drops sharply, then the next batch of CI/CD pushes refills the reclaimed space. The growth-rate search may flag this project as GROWING_FAST even though the net change over a week is near zero. Use a 7-day moving average rather than daily delta for growth classification.

**replication_double_count** — Projects using Harbor replication to a secondary registry consume quota on both the source and destination projects. The source project appears to grow faster than expected because replicated artifacts count against the source quota until the next garbage collection cycle clears unreferenced blobs.

**trivy_database_cache** — The Trivy vulnerability database cache stored in the Harbor data volume contributes to PV-level usage metrics but is not counted against project quotas. PV usage may appear higher than the sum of project quotas due to this shared cache. Distinguish by comparing PV usage with the sum of `harbor_project_quota_usage_byte` values.

**untagged_artifact_accumulation** — Continuous image rebuilds in CI/CD pipelines replace tagged artifacts but leave behind untagged manifests and layers that consume quota until garbage collection runs. A project may appear to grow steadily despite having the same number of tagged images. Verify by checking untagged artifact count in Harbor UI.

**quota_limit_change_step** — When an administrator increases a project's quota limit, the usage_pct drops instantly without any actual storage reclamation. The growth-rate search may misinterpret this as a SHRINKING trend. Correlate with `sourcetype=harbor:audit operation=update resource_type=quota` to identify administrative quota changes.

**blob_dedup_variance** — Harbor uses content-addressable storage where identical layers across images are stored once. Project quota accounting may show different effective usage than the physical storage consumed because deduplication savings are applied at the storage level, not the quota level.

## References

- [Harbor Administration — Project Quotas](https://goharbor.io/docs/2.10.0/administration/configure-project-quotas/)
- [Harbor Metrics — Prometheus Endpoint](https://goharbor.io/docs/2.10.0/administration/metrics/)
- [Harbor Administration — Tag Retention Rules](https://goharbor.io/docs/2.10.0/administration/tag-retention-rules/)
- [Splunk OpenTelemetry Collector for Kubernetes](https://github.com/signalfx/splunk-otel-collector-chart)
- [Splunk REST API Modular Input (Splunkbase 1546)](https://splunkbase.splunk.com/app/1546)
