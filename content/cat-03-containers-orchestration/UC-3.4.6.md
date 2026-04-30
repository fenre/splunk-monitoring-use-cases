<!-- AUTO-GENERATED from UC-3.4.6.json — DO NOT EDIT -->

---
id: "3.4.6"
title: "Registry Replication Lag and Consistency"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.4.6 · Registry Replication Lag and Consistency

## Description

Monitors Harbor registry replication execution duration, failure rates, and artifact lag across sites by polling the **Replication Executions API** and scraping **Harbor metrics**, then classifies replication health as CRITICAL, HIGH, MEDIUM, or LOW based on duration thresholds and failure percentages — enabling multi-site container platform teams to detect degraded replication before image pull failures cascade across clusters.

## Value

Container registries replicate images across sites for disaster recovery, geo-locality, and regulatory data residency. When replication falls behind, clusters in remote sites pull stale or missing image tags and fail deployments. A 30-minute replication delay that coincides with a production rollout means half the fleet runs the new version while the other half cannot pull it. Monitoring replication execution duration and failure rates gives the platform team the evidence to fix network bottlenecks, resize the jobservice worker pool, and prove that cross-site SLAs are being met.

## Implementation

Poll Harbor's /api/v2.0/replication/executions endpoint via Splunk REST API Modular Input every 5 minutes into index=containers. Build two search variants: hourly execution monitoring with failure rate and severity classification, and 7-day lag trend with SMA. Alert when any execution enters CRITICAL (failed) or HIGH (>30 min and partial failures) severity.

## Detailed Implementation

Prerequisites
• **Harbor** 2.5+ registry deployment with at least one **replication policy** configured — replication policies define the source registry, destination registry, resource filter (repositories, tags), trigger mode (manual, scheduled, event-based), and bandwidth limit. Each execution of a policy produces a record accessible via the **Replication Executions API**.
• **Splunk REST API Modular Input** (`rest_ta`) configured to poll **`/api/v2.0/replication/executions`** every 5 minutes. The endpoint returns paginated JSON containing `id`, `policy_id`, `status` (InProgress, Succeed, Failed, Stopped), `trigger` (manual, schedule, event_based), `start_time`, `end_time`, `total`, `failed`, `succeed`, and `in_progress` counts.
• For **per-task detail**, configure a second input polling **`/api/v2.0/replication/executions/{id}/tasks`** — this provides artifact-level status, error messages (e.g., **"denied: requested access to the resource is denied"**), and individual task duration. Use a scripted input or the **Splunk Add-on Builder** to paginate and correlate tasks with their parent execution.
• **Harbor metrics** endpoint (`/metrics`) exposed and scraped by the **Splunk OpenTelemetry Collector** with the **Prometheus receiver**. Key metrics: `harbor_replication_status` (gauge per policy), `harbor_task_queue_latency` (histogram), and custom replication timing metrics if configured.
• **Splunk HEC** token for **`index=containers`** with **`sourcetype=harbor:replication`** as default; secondary tokens for **`sourcetype=harbor:metrics`** and **`sourcetype=kube:container:logs`**.
• **Network requirements**: the Splunk collector needs HTTPS access to both the **source** and **target** Harbor instances' API endpoints. If registries span data centers, ensure the **cross-site network link** bandwidth and latency are monitored (via **`sourcetype=otel:metrics`** infrastructure metrics) to correlate replication lag with network conditions.
• **Harbor RBAC**: the API user needs the **ProjectAdmin** role or a custom role with `list` permission on **replication executions** and **replication policies**. Store credentials in the Splunk **credential store** via `rest_ta` configuration.
• **License estimate**: a registry with 10 replication policies executing hourly generates approximately 240 execution records/day (~100 KB) plus per-task details (~500 KB/day for 50 artifacts/execution).

Step 1 — Configure data collection
(1) **REST API polling**: configure the `rest_ta` input with the following settings:
— **URL**: `https://<harbor-host>/api/v2.0/replication/executions?page_size=50&sort=-start_time`
— **Interval**: 300 seconds (5 minutes)
— **Sourcetype**: `harbor:replication`
— **Index**: `containers`
— **Authentication**: Basic auth with the **Harbor admin** or a dedicated **replication-monitor** user
— **Response handler**: JSON array — each element becomes one Splunk event. Configure the handler to extract `id`, `policy_id`, `status`, `trigger`, `start_time`, `end_time`, `total`, `failed`, `succeed`.

(2) **Execution-to-policy mapping**: the execution record contains only `policy_id`, not the **policy name** or source/target registry URLs. Create a **lookup** (`harbor_replication_policies.csv`) mapping `policy_id` to `policy_name`, `src_registry`, `dest_registry`, and `description`. Populate this lookup from **`/api/v2.0/replication/policies`** — this endpoint changes infrequently, so a daily scheduled search or manual update suffices.

(3) **Per-task detail collection**: for high-fidelity monitoring, configure a **scripted input** that iterates over recent execution IDs and fetches **`/api/v2.0/replication/executions/{id}/tasks`**. Each task record includes `src_resource` (source repository:tag), `dst_resource` (destination), `status`, `start_time`, `end_time`, and `job_id`. Index these as **`sourcetype=harbor:replication:task`** for drill-down from execution-level summaries to individual artifact failures.

(4) **Harbor container logs**: collect **`sourcetype=kube:container:logs`** from the `harbor-core` and `harbor-jobservice` pods. Jobservice logs contain replication worker pool utilization, retry attempts, and detailed error messages (e.g., **"context deadline exceeded"**, **"connection refused"**, **"blob unknown to registry"**). These logs provide root-cause detail that the API execution records do not.

(5) **Infrastructure metrics for correlation**: collect **cross-site network metrics** (latency, bandwidth, packet loss) via the **OTel Collector's hostmetrics receiver** or a network monitoring tool. Replication lag often correlates directly with **WAN link degradation** — this correlation is essential for distinguishing Harbor-side issues from network-side issues.

Step 2 — Create the search and alert
The primary SPL processes **execution records** to compute hourly statistics per replication policy. The **`lag_severity`** classification:
— **CRITICAL**: the execution status is **Failed** — no artifacts were replicated
— **HIGH**: execution duration exceeds **30 minutes** AND has partial failures (failed_pct > 0) — some artifacts were replicated but with errors
— **MEDIUM**: execution duration exceeds **10 minutes** — slow but no failures (yet)
— **LOW**: normal operation

The second SPL variant computes a **7-day lag trend** using 4-hour bins and a **7-point SMA** (each point is a 4-hour average, so the SMA spans approximately 28 hours). The **SPIKE** flag triggers when the current average lag exceeds **2× the SMA** AND exceeds **300 seconds** (5 minutes absolute floor).

Key **field normalization** considerations:
— The `start_time` and `end_time` fields from the Harbor API use **ISO 8601** format (`2024-01-15T10:30:00.000Z`). The `strptime` in the SPL handles this format.
— The `trigger` field values differ between Harbor versions: v2.5 uses `manual`/`scheduled`/`event_based`; v2.8+ uses `MANUAL`/`SCHEDULED`/`EVENT_BASED`. The `coalesce` and `lower` functions normalize these differences.
— For executions still **in progress**, `end_time` is null. The SPL computes duration as `now() - start_ts` for these, giving a real-time lag estimate.

Schedule the hourly monitoring search every **15 minutes** over **`-2h`** (overlapping to catch delayed execution records). Alert when `has_critical=1` or `avg_fail_pct > 20`. Schedule the 7-day trend search daily at **06:00**.

Step 3 — Validate
(a) Trigger a **manual replication** in Harbor UI: Administration → Replications → select a policy → **Replicate**. Within 5 minutes, verify: `index=containers sourcetype="harbor:replication" status="Succeed" earliest=-10m`.
(b) Create a **failure scenario**: configure a replication policy to a non-existent or unreachable target registry. Trigger it manually. Verify: `index=containers sourcetype="harbor:replication" status="Failed" earliest=-10m`.
(c) Verify **duration calculation**: compare the `duration_sec` computed by the SPL with the actual execution duration shown in the Harbor UI. Account for timezone differences between Harbor's `start_time`/`end_time` (UTC) and Splunk's `_time`.
(d) Validate the **lookup**: `| inputlookup harbor_replication_policies.csv | table policy_id policy_name src_registry dest_registry`. Should return all configured policies.
(e) Confirm the **severity classification**: create test events with known durations and failure rates to verify the `case()` logic produces correct severity levels.

Step 4 — Operationalize dashboards and runbooks
• Row A: **single-value tiles** — total policies monitored, policies in CRITICAL, max lag (seconds), average failure rate (%), last successful full replication timestamp.
• Row B: **line chart** of average and maximum replication duration per policy over 7 days with **SMA overlay** — identifies chronic lag versus transient spikes.
• Row C: **stacked bar chart** of execution status (Succeed, Failed, InProgress, Stopped) per policy per day — shows the ratio of failures over time.
• Row D: **severity-colored table** — policy_name, src_registry, dest_registry, last_status, last_duration, avg_duration, fail_rate, severity. Red rows for CRITICAL, orange for HIGH.
• **Alerting**: CRITICAL execution → Slack `#platform-ops` + PagerDuty P2; HIGH severity sustained for 2+ hours → P3; SPIKE in trend → Slack notification; failure rate > 20% for any policy → daily digest email.
• **Runbook** (owner: platform registry team): (1) check Harbor jobservice worker pool: `kubectl logs -n harbor deploy/harbor-jobservice --tail=100 | grep replication`, (2) verify **network connectivity** between registries: `curl -v https://<target-registry>/v2/`, (3) check **storage** at target registry: disk space, I/O latency, (4) review per-task errors for specific artifact failures, (5) for **"blob unknown"** errors: trigger garbage collection at the source registry before retrying.

Step 5 — Visualization, alert design, and troubleshooting
• **Visualization**: use a **Sankey diagram** or flow visualization showing the replication flow from source registry → policy → target registry with color-coded paths (green for healthy, red for failing) — this quickly identifies which cross-site links are degraded.
• **Alert design**: include `policy_name`, `src_registry`, `dest_registry`, `execution_status`, `duration_sec`, `failed_count`, `total_count`, and `lag_severity` in the alert payload. For trend alerts include the `deviation_pct` and `trend_flag`.
• **Execution records missing** — the `rest_ta` may not paginate correctly if `page_size` is too small for high-volume replication. Increase `page_size` to 100 and verify all executions appear.
• **Duration always shows as in-progress** — if `end_time` is consistently null, the execution may be stuck. Check Harbor jobservice for **deadlocked workers**: `kubectl logs deploy/harbor-jobservice | grep -i "timeout\|deadlock"`.
• **Lag spikes correlate with specific times** — scheduled replication policies that overlap create **resource contention** in the jobservice worker pool. Stagger replication schedules to distribute load.
• **Replication succeeds but images unavailable at target** — Harbor marks execution as Succeed when artifacts are pushed, but the target registry may need time to index them. Add a **validation delay** (5–10 minutes after execution completes) before alerting on missing images.

## SPL

```spl
`comment("--- Harbor Replication Execution Monitoring — Lag and Failure Detection ---")`
index=containers sourcetype="harbor:replication"
| eval policy_name=coalesce(policy_name, policy_id, "unknown")
| eval trigger=coalesce(trigger, trigger_type, "manual")
| eval exec_status=coalesce(status, execution_status)
| eval start_ts=strptime(coalesce(start_time, _time), "%Y-%m-%dT%H:%M:%S")
| eval end_ts=strptime(coalesce(end_time, ""), "%Y-%m-%dT%H:%M:%S")
| eval duration_sec=if(isnotnull(end_ts), end_ts - start_ts, now() - start_ts)
| eval failed_pct=if(total > 0, round(100 * failed / total, 1), 0)
| eval lag_severity=case(
    exec_status="Failed", "CRITICAL",
    duration_sec > 1800 AND failed_pct > 0, "HIGH",
    duration_sec > 600, "MEDIUM",
    1=1, "LOW")
| bin _time span=1h
| stats count as executions,
    sum(eval(if(exec_status="Failed",1,0))) as failed_executions,
    avg(duration_sec) as avg_duration_sec,
    max(duration_sec) as max_duration_sec,
    avg(failed_pct) as avg_fail_pct,
    values(lag_severity) as severities
    by _time, policy_name
| eval has_critical=if(mvfind(severities, "CRITICAL") >= 0, 1, 0)
| table _time policy_name executions failed_executions avg_duration_sec max_duration_sec avg_fail_pct has_critical

`comment("--- Cross-Site Replication Lag Trend — 7-Day View ---")`
index=containers sourcetype="harbor:replication"
| eval policy_name=coalesce(policy_name, policy_id)
| eval start_ts=strptime(coalesce(start_time, _time), "%Y-%m-%dT%H:%M:%S")
| eval end_ts=strptime(coalesce(end_time, ""), "%Y-%m-%dT%H:%M:%S")
| eval duration_sec=if(isnotnull(end_ts), end_ts - start_ts, now() - start_ts)
| bin _time span=4h
| stats avg(duration_sec) as avg_lag,
    max(duration_sec) as max_lag,
    count as repl_count
    by _time, policy_name
| trendline sma7(avg_lag) as sma_lag
| eval deviation_pct=round(100 * (avg_lag - sma_lag) / max(sma_lag, 1), 1)
| eval trend_flag=case(avg_lag > sma_lag * 2 AND avg_lag > 300, "SPIKE", 1=1, "NORMAL")
| table _time policy_name avg_lag max_lag sma_lag deviation_pct repl_count trend_flag

`comment("--- Per-Task Artifact Failure Detail — Drill-Down from Execution ---")`
index=containers sourcetype="harbor:replication"
| eval policy_name=coalesce(policy_name, policy_id, "unknown")
| eval exec_status=coalesce(status, execution_status)
| eval start_ts=strptime(coalesce(start_time, _time), "%Y-%m-%dT%H:%M:%S")
| eval end_ts=strptime(coalesce(end_time, ""), "%Y-%m-%dT%H:%M:%S")
| eval duration_sec=if(isnotnull(end_ts), end_ts - start_ts, now() - start_ts)
| where exec_status="Failed" OR failed > 0
| eval failed_pct=if(total > 0, round(100 * failed / total, 1), 0)
| stats count as failed_executions,
    avg(duration_sec) as avg_fail_duration,
    sum(failed) as total_failed_artifacts,
    sum(total) as total_artifacts,
    latest(exec_status) as last_status
    by policy_name
| eval overall_fail_pct=round(100 * total_failed_artifacts / max(total_artifacts, 1), 1)
| sort -total_failed_artifacts
| table policy_name failed_executions avg_fail_duration total_failed_artifacts total_artifacts overall_fail_pct last_status
```

## Visualization

Line chart of avg/max replication duration by policy, stacked bar of execution status, severity-colored table, single-value tiles (max lag, failed %, policies in CRITICAL), sparklines per policy.

## Known False Positives

**scheduled_overlap_contention** — When multiple replication policies execute simultaneously on the same Harbor jobservice, worker pool contention increases execution duration for all policies. This creates artificial lag spikes that do not indicate network or registry health problems. Stagger replication schedules and correlate lag spikes with concurrent execution counts.

**large_artifact_skew** — A single multi-gigabyte container image (such as ML training images or monolithic legacy applications) can dominate the execution duration, making the average lag appear high even though all other artifacts replicate quickly. Examine per-task detail to identify outlier artifacts and consider separate policies for large images.

**garbage_collection_windows** — Harbor garbage collection temporarily locks blob storage, causing concurrent replication tasks to fail with transient errors or timeout. These failures are expected during scheduled GC windows. Correlate replication failures with GC execution times from harbor-core logs.

**network_maintenance_windows** — Planned WAN maintenance between registry sites causes temporary replication failures that self-resolve after the maintenance window. Cross-reference with change management records and suppress alerts during documented maintenance periods.

**event_based_burst** — Event-based replication policies trigger on every image push, creating bursts of small replication executions during active CI/CD hours. The sheer volume of executions may appear as increased failure rate when individual transient network errors affect a small percentage. Aggregate by policy and time window rather than individual execution.

**target_registry_capacity** — When the target registry's storage approaches capacity, replication tasks fail with disk-full errors that look like replication failures but are actually a storage provisioning issue. Monitor target registry storage quotas (UC-3.4.3) alongside replication health.

## References

- [Harbor — Replication Management API](https://goharbor.io/docs/latest/administration/configuring-replication/)
- [Harbor — Metrics with Prometheus](https://goharbor.io/docs/latest/administration/metrics/)
- [Harbor — Architecture Overview](https://goharbor.io/docs/latest/install-config/harbor-ha-helm/)
- [Splunk REST API Modular Input (rest_ta)](https://splunkbase.splunk.com/app/1546)
- [Splunk trendline Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Trendline)
