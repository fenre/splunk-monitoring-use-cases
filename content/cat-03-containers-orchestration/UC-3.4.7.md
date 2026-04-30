<!-- AUTO-GENERATED from UC-3.4.7.json — DO NOT EDIT -->

---
id: "3.4.7"
title: "Registry Image Tag Retention and Orphan Cleanup"
status: "verified"
criticality: "low"
splunkPillar: "Observability"
---

# UC-3.4.7 · Registry Image Tag Retention and Orphan Cleanup

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Compliance &middot; **Wave:** Crawl &middot; **Status:** Verified

*Just as a library periodically removes books that nobody has borrowed in years to make room for new ones, we track which software packages in our storage have not been used and flag them for cleanup.*

---

## Description

Inventories container image tags across Harbor projects to identify repositories with excessive tag counts, stale tags (pushed >90 days ago), and orphan tags (never pulled or not pulled in 90+ days), then tracks garbage collection effectiveness by trending daily freed storage — enabling platform teams to tune retention policies and reclaim wasted registry storage before quota exhaustion.

## Value

Container registries accumulate tags relentlessly — every CI/CD pipeline push adds a new tag, but few are ever deleted. A repository with 500 tags where 400 have never been pulled wastes storage quota, slows Harbor API responses, and makes vulnerability scanning take longer. Monitoring tag retention gives platform teams the evidence to set per-project retention rules, justify automated cleanup policies, and prove to finance that storage growth is controlled. Without this visibility, registry storage costs grow linearly with build frequency, and stale images with known CVEs persist indefinitely.

## Implementation

Poll Harbor's Repository and Artifact API endpoints daily via Splunk REST API Modular Input into index=containers. Build two search variants: tag inventory with orphan/stale classification and retention flags, and garbage collection effectiveness trend with 7-day SMA. Alert when any repository enters CRITICAL retention status or when GC effectiveness drops to LOW.

## Detailed Implementation

### Prerequisites
- **Harbor** 2.5+ registry with **tag retention rules** configured (or planned) at the project level. **Harbor**'s tag retention feature allows defining rules per repository or per project specifying how many tags to keep, which tags to retain (by pattern or recency), and the retention schedule.
- **Splunk REST API Modular Input** (`rest_ta`) configured to poll two Harbor API endpoints:
  — **`/api/v2.0/projects/{name}/repositories`** — returns the list of repositories within each project with artifact counts
  — **`/api/v2.0/projects/{name}/repositories/{name}/artifacts`** — returns individual artifacts (tags) with digests, push times, pull times, sizes, and scan status
  Configure the polling interval to **daily** (86400 seconds) since the tag inventory changes slowly.
- **Harbor garbage collection** API endpoint **`/api/v2.0/system/gc`** — returns GC execution records including status, freed space, deleted blob counts, and duration. Configure a second `rest_ta` input polling this endpoint **daily**.
- **Splunk HEC** token for **`index=containers`** with **`sourcetype=harbor:repositories`** as default; secondary tokens for **`sourcetype=harbor:gc`** and **`sourcetype=harbor:audit`**.
- **Harbor RBAC**: the API user needs the **ProjectAdmin** role for listing artifacts across all projects, or a custom **read-only** role scoped to repository listing. Store credentials in the Splunk **credential store** via `rest_ta` configuration.
- **Pagination handling**: Harbor's artifact list API returns paginated results (default page size 10, max 100). The `rest_ta` input must be configured to **follow pagination** links in the `Link` response header to capture the complete tag inventory. For large registries (>10,000 artifacts total), consider using a **scripted input** with explicit **pagination** logic.
- **License estimate**: a registry with 500 repositories averaging 50 tags each generates approximately **25,000 artifact records** per daily poll (~5 MB/day). GC records add negligible volume.
- Splunk RBAC: users running retention analysis searches need **`srchIndexesAllowed`** including `containers`; assign via a **`registry_admin`** role.

### Step 1 — Configure data collection
(1) **Repository and artifact inventory**: configure the `rest_ta` input:
— **URL**: `https://<harbor-host>/api/v2.0/projects/{project}/repositories/{repo}/artifacts?page_size=100&with_tag=true&with_scan_overview=true`
— **Interval**: 86400 seconds (daily)
— **Sourcetype**: `harbor:repositories`
— **Index**: `containers`
— **Response handler**: JSON array — each element represents one artifact (tag) and becomes one Splunk event

Key fields extracted from each artifact record:
— **`tags[].name`** (the tag name, e.g., `v1.2.3`, `latest`, `sha-abc123`)
— **`push_time`** (ISO 8601 timestamp when the artifact was pushed)
— **`pull_time`** (ISO 8601 timestamp of the last pull — null if never pulled)
— **`size`** (artifact size in bytes — the compressed layer size)
— **`digest`** (the content-addressable SHA256 digest)
— **`scan_overview`** (vulnerability scan summary if scanning is enabled)

(2) **Garbage collection records**: configure a second `rest_ta` input:
— **URL**: `https://<harbor-host>/api/v2.0/system/gc`
— **Interval**: 86400 seconds (daily)
— **Sourcetype**: `harbor:gc`
— **Index**: `containers`

GC records include:
— **`job_status`** (Success, Error, Pending, Running)
— **`freed_space`** (bytes freed by the GC run)
— **`deleted_blobs_count`** (number of **orphan blob**s removed)
— **`creation_time`** and **`update_time`** (GC job timestamps)
— **`schedule`** (the GC schedule — None, Daily, Weekly, Custom)

(3) **Audit log correlation**: Harbor audit logs capture **DELETE_ARTIFACT** events generated by **tag retention rules** and **manual deletions**. These provide attribution (who deleted, which policy triggered) that the inventory API does not.

(4) **Project-to-team mapping lookup**: create **`harbor_project_owners.csv`** mapping `project_name` to `team`, `cost_center`, and `retention_policy_name`. This enables the tag retention dashboard to show which teams have the most orphan tags and which retention policies need tuning.

### Step 2 — Create the search and alert
The primary SPL inventories all artifacts and classifies them:
— **Orphan tags**: never pulled OR last pulled > 90 days ago. These tags exist in the registry but are not actively used by any cluster.
— **Stale tags**: pushed > 90 days ago. These may still be pulled (e.g., a production tag pinned to a specific version) but represent older software versions.
— **`retention_flag`** classification:
- **CRITICAL**: repository has > 200 tags AND orphan percentage > 50% — this repository urgently needs retention rules
- **WARN**: repository has > 100 tags OR orphan percentage > 30% — **retention policy** should be reviewed
- **OK**: within acceptable bounds

The GC effectiveness variant tracks how much storage **garbage collection** frees daily, using a **7-day SMA** to identify trends:
— **HIGH effectiveness**: daily freed storage exceeds 2× the SMA — indicates a burst of deletions (possibly from retention rule changes)
— **LOW effectiveness**: daily freed storage drops below 30% of the SMA — may indicate GC is not running or nothing to clean up
— **NORMAL**: within expected bounds

Schedule the tag inventory analysis daily at **08:00** and alert when any repository enters CRITICAL retention status. Schedule the GC effectiveness trend daily and alert on LOW effectiveness sustained for 3+ days (may indicate GC scheduling issues).

### Step 3 — Validate
(a) Verify artifact collection: `index=containers sourcetype="harbor:repositories" earliest=-2d | stats dc(digest) as unique_artifacts, dc(repo) as repositories`. Should match the approximate count visible in the Harbor UI.
(b) Test orphan detection: find a tag that has never been pulled in the Harbor UI, verify it appears with `is_orphan=1` in the search results.
(c) Verify GC records: `index=containers sourcetype="harbor:gc" earliest=-7d | stats count, latest(job_status) as last_status, sum(freed_space) as total_freed`. Should show recent GC runs.
(d) Cross-validate tag counts: compare the per-repository `tag_count` from the search with the counts shown in the Harbor UI for the top 5 repositories.
(e) Test retention flag logic: identify a repository with >100 tags in the Harbor UI and verify it appears with `retention_flag=WARN` or `CRITICAL` in the search results.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **single-value tiles** — total repositories monitored, total tags, total orphan tags, orphan percentage, total reclaimable storage (GB), repos in CRITICAL.
- Row B: **bar chart** of top 20 repositories by tag count, stacked by category (orphan, stale, active) — visually identifies the worst offenders.
- Row C: **line chart** of daily GC freed storage with **7-day SMA** overlay — shows whether cleanup is keeping pace with tag creation.
- Row D: **retention flag table** — project, repo, tag_count, orphan_tags, stale_tags, orphan_pct, total_size_mb, oldest_tag_days, retention_flag. Sorted by retention_flag (CRITICAL first), then tag_count.
- **Alerting**: CRITICAL retention flag → Slack `#registry-ops` with repository details; GC LOW effectiveness for 3+ days → email to registry admin team; total orphan storage exceeds **100 GB** → weekly capacity planning report.
- **Runbook** (owner: platform registry team): (1) for CRITICAL repos: review and configure **tag retention rules** in Harbor project settings, (2) for repos with many stale tags: determine if a blanket "keep last N" rule is safe or if specific tags need pinning, (3) for GC issues: check Harbor jobservice logs for GC errors: `kubectl logs -n harbor deploy/harbor-jobservice --tail=100 | grep gc`, (4) for storage pressure: trigger a manual GC run and monitor freed space.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **treemap** showing repositories sized by total storage consumption and colored by orphan percentage — large red tiles immediately identify repositories that waste the most storage. Pair with a **time series** showing the ratio of tags created vs tags deleted per week.
- **Alert design**: include `project`, `repo`, `tag_count`, `orphan_tags`, `orphan_pct`, `total_size_mb`, `retention_flag`, and `oldest_tag_days` in the alert payload. For GC alerts include `daily_freed_mb`, `sma_freed`, and `gc_effectiveness`.
- **Retention rule scope verification** — Harbor retention rules use **glob patterns** to match repositories. Verify the rule scope matches the intended repositories by reviewing the rule configuration in the Harbor UI.
- **Artifact count mismatch with Harbor UI** — the `rest_ta` may not paginate correctly. Verify all pages are fetched by checking the `Link` header handling in the `rest_ta` configuration. Harbor's default page size is 10; set `page_size=100` to reduce pagination issues.
- **Pull time always null** — Harbor only records pull times for registry pulls (Docker/containerd). If images are accessed via Harbor's chartmuseum or Helm charts, pull times may not be tracked. Consider these as potential orphans but with lower confidence.
- **GC freed space is zero** — Harbor GC only removes blobs that are no longer referenced by any manifest. If tags are deleted but their **shared layers** are still referenced by other tags, GC frees no space. This is expected behavior, not an error. Track **unique blob count** alongside tag count for more accurate storage reclamation estimates.
- **Tag retention rules not deleting tags** — Harbor tag retention rules run as scheduled jobs. Check the job log: `kubectl logs -n harbor deploy/harbor-core --tail=100 | grep retention`. Verify the rule scope matches the intended repositories (some rules use regex patterns that may not match).

## SPL

```spl
`comment("--- Registry Tag Inventory — Repos with Excessive or Stale Tags ---")`
index=containers sourcetype="harbor:repositories"
| eval repo=coalesce(repository_name, name)
| eval project=coalesce(project_name, mvindex(split(repo, "/"), 0))
| eval push_epoch=strptime(coalesce(push_time, creation_time), "%Y-%m-%dT%H:%M:%S")
| eval pull_epoch=strptime(coalesce(pull_time, ""), "%Y-%m-%dT%H:%M:%S")
| eval age_days=round((now() - push_epoch) / 86400, 0)
| eval last_pull_days=if(isnotnull(pull_epoch), round((now() - pull_epoch) / 86400, 0), -1)
| eval size_mb=round(coalesce(size, 0) / 1048576, 1)
| eval is_orphan=if(last_pull_days > 90 OR last_pull_days=-1, 1, 0)
| eval is_stale=if(age_days > 90, 1, 0)
| stats count as tag_count,
    sum(is_orphan) as orphan_tags,
    sum(is_stale) as stale_tags,
    sum(size_mb) as total_size_mb,
    max(age_days) as oldest_tag_days,
    min(age_days) as newest_tag_days
    by repo, project
| eval orphan_pct=round(100 * orphan_tags / max(tag_count, 1), 1)
| eval retention_flag=case(
    tag_count > 200 AND orphan_pct > 50, "CRITICAL",
    tag_count > 100 OR orphan_pct > 30, "WARN",
    1=1, "OK")
| sort -tag_count
| head 50
| table project repo tag_count orphan_tags stale_tags orphan_pct total_size_mb oldest_tag_days newest_tag_days retention_flag

`comment("--- Garbage Collection Effectiveness — Freed Storage Trend ---")`
index=containers sourcetype="harbor:gc"
| eval gc_status=coalesce(job_status, status)
| eval freed_mb=round(coalesce(freed_space, deleted_size, 0) / 1048576, 1)
| eval duration_min=round(coalesce(duration, 0) / 60, 1)
| eval deleted_blobs=coalesce(deleted_blobs_count, deleted, 0)
| bin _time span=1d
| stats latest(gc_status) as last_status,
    sum(freed_mb) as daily_freed_mb,
    sum(deleted_blobs) as daily_deleted_blobs,
    avg(duration_min) as avg_gc_duration_min
    by _time
| trendline sma7(daily_freed_mb) as sma_freed
| eval gc_effectiveness=case(daily_freed_mb > sma_freed * 2, "HIGH", daily_freed_mb < sma_freed * 0.3, "LOW", 1=1, "NORMAL")
| table _time last_status daily_freed_mb sma_freed daily_deleted_blobs avg_gc_duration_min gc_effectiveness

`comment("--- Tag Age Distribution — Histogram for Retention Policy Tuning ---")`
index=containers sourcetype="harbor:repositories"
| eval repo=coalesce(repository_name, name)
| eval project=coalesce(project_name, mvindex(split(repo, "/"), 0))
| eval push_epoch=strptime(coalesce(push_time, creation_time), "%Y-%m-%dT%H:%M:%S")
| eval age_days=round((now() - push_epoch) / 86400, 0)
| eval size_mb=round(coalesce(size, 0) / 1048576, 1)
| eval age_bucket=case(
    age_days <= 7, "0-7d",
    age_days <= 30, "8-30d",
    age_days <= 90, "31-90d",
    age_days <= 180, "91-180d",
    age_days <= 365, "181-365d",
    1=1, "365d+")
| stats count as tags, sum(size_mb) as total_mb by project, age_bucket
| xyseries project age_bucket tags
| addtotals fieldname=total_tags
| sort -total_tags
```

## Visualization

Bar chart of tag counts by repo, stacked by orphan/stale/active; GC freed-storage trend line; single-value tiles (total orphan tags, total reclaimable GB, worst repo); retention flag table with drilldown.

## Known False Positives

**pinned_production_tags** — Long-lived production tags (e.g., specific release versions pinned in deployment manifests) may appear as stale because they were pushed months ago, but they are actively referenced by running workloads. Cross-reference with Kubernetes pod image references to distinguish actively deployed tags from truly orphaned ones.

**shared_base_image_layers** — Multiple tags sharing the same base image layers inflate per-tag size calculations because Harbor reports the compressed layer size per artifact. The total reclaimable storage from deleting orphan tags is often significantly less than the sum of their reported sizes due to layer deduplication.

**ci_cd_build_cache_tags** — CI/CD systems that use build cache tags (e.g., `buildcache-<hash>`) create many tags that are only pulled by the CI system itself. These appear as orphans because no production workload pulls them, but they serve an important build performance function. Exclude known CI cache tag patterns from orphan classification.

**immutable_tag_policies** — Some organizations enforce immutable tag policies where tags are never overwritten or deleted for audit and compliance reasons. Repositories under such policies will always appear in the retention report with high tag counts. Tag these repositories in the project-to-team lookup as `retention_exempt=true`.

**gc_scheduling_gap** — Harbor GC must be explicitly configured and scheduled. A new Harbor deployment may have no GC schedule configured, causing the GC effectiveness search to show zero freed storage indefinitely. This is a configuration gap, not a collection error. The first remediation step is to configure a GC schedule.

**multi_architecture_manifests** — A single logical tag (e.g., `v1.0`) with multi-architecture support (amd64, arm64) creates multiple artifact records in Harbor. The tag inventory may count these as separate artifacts, inflating the tag count above the actual number of logical versions.

## References

- [Harbor — Tag Retention Rules](https://goharbor.io/docs/latest/administration/tag-retention-rules/)
- [Harbor — Garbage Collection](https://goharbor.io/docs/latest/administration/garbage-collection/)
- [Harbor — Artifact Management API](https://goharbor.io/docs/latest/build-customize-contribute/configure-swagger/)
- [Splunk REST API Modular Input (rest_ta)](https://splunkbase.splunk.com/app/1546)
- [Splunk trendline Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Trendline)
