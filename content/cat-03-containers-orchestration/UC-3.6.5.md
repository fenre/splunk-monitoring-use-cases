<!-- AUTO-GENERATED from UC-3.6.5.json — DO NOT EDIT -->

---
id: "3.6.5"
title: "Kubernetes Event Error Rate Trending"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.6.5 · Kubernetes Event Error Rate Trending

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault, Performance, Reliability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We count the daily warning messages that our computer systems produce and chart the trend over weeks, so the team can tell whether problems are increasing, decreasing, or staying the same.*

---

## Description

Tracks the daily rate of Kubernetes **Warning** events across the cluster, computing 7-day moving averages and deviation percentages to surface rising error trends, then breaks down warnings by **reason** (OOMKilling, BackOff, FailedScheduling, FailedMount, ImagePullBackOff) and namespace to classify the root-cause category and prioritize platform engineering attention.

## Value

Kubernetes Warning events are the cluster's distress signals — individually they are noise, but a rising daily rate reveals systemic issues that point-in-time monitoring misses. A 50% week-over-week increase in BackOff events signals degrading application stability; a spike in FailedScheduling indicates resource exhaustion. Trending these signals gives platform teams the evidence to justify capacity increases, identify deployment regressions, and prove that remediation efforts are working.

## Implementation

Collect Kubernetes Warning events via Splunk Connect for Kubernetes or OTel k8s_events receiver into index=containers. Build two search variants: 30-day daily warning rate trend with 7-day SMA and spike/drop classification, and per-reason/namespace breakdown with severity tiers. Alert when daily warnings exceed 2× the 7-day SMA or when high-severity reasons (OOMKilling, FailedScheduling, NodeNotReady) show sustained increases.

## Detailed Implementation

### Prerequisites
- **Kubernetes** 1.24+ cluster with the **API server** configured to retain events for at least **1 hour** (default) — for longer retention, increase the `--event-ttl` flag or use a dedicated event **exporter**.
- **Splunk Connect for Kubernetes** deployed to collect **`sourcetype=kube:events`** from the **Kubernetes** **API server**. Alternative: **Splunk OpenTelemetry Collector** with the **`k8s_events`** receiver which uses a **watch stream** rather than polling, ensuring no events are missed due to TTL expiry.
- **Splunk HEC** token for **`index=containers`** with **`sourcetype=kube:events`** as default; secondary streams for **`sourcetype=kube:container:status`** and **`sourcetype=otel:metrics`** for correlation context.
- At least **14 days** of historical event data for meaningful 7-day SMA trending; **30 days** is ideal for the primary search. Set **index retention** to at least 90 days for trend analysis.
- Splunk RBAC: users running event trend searches need **`srchIndexesAllowed`** including `containers`; assign via a custom role (**`platform_analyst`**).
- **Kubernetes RBAC**: the **event collector**'s **ServiceAccount** needs `get`, `list`, `watch` on **events** in all namespaces.
- **License estimate**: Warning event volume varies widely by cluster health — a healthy 200-pod cluster generates 100–500 Warning events/day (~200 KB); an unstable cluster may generate 10,000+ events/day (~5 MB).

### Step 1 — Configure data collection
(1) **Event stream collection**: the **`k8s_events`** receiver in the OTel Collector uses a **watch API** that streams events in real-time, avoiding the gap between the Kubernetes API event **TTL** (default 1 hour) and the collector's poll interval. This is preferred over the polling approach used by older **Splunk Connect for Kubernetes** versions.

Key event fields to validate in the collection:
— **`type`** (Normal or **Warning** — the search filters on Warning)
— **`reason`** (the machine-readable cause: BackOff, OOMKilling, FailedScheduling, Unhealthy, FailedMount, FailedPulling, Evicted, NodeNotReady, etc.)
— **`message`** (free-text description with specific details like container name, resource values, error messages)
— **`involvedObject.name`** (the pod, node, or other resource that generated the event)
— **`involvedObject.kind`** (Pod, Node, ReplicaSet, PersistentVolumeClaim, etc.)
— **`source.component`** (the Kubernetes component that generated the event: kubelet, scheduler, controller-manager)
— **`count`** (how many times this identical event occurred — important for deduplication)

(2) **Event deduplication**: Kubernetes deduplicates identical events by incrementing the `count` field rather than creating new event objects. The collector may see the same event with an increasing count. The SPL uses `count` to count event instances, which produces accurate totals even with Kubernetes-level deduplication.

(3) **Node-level correlation**: collect **`sourcetype=kube:node:metrics`** or **kube-state-metrics** `kube_node_status_condition` to correlate Warning events with node health conditions (**DiskPressure**, **MemoryPressure**, **PIDPressure**, **NetworkUnavailable**). A cluster of Warning events concentrated on pods running on nodes with health conditions indicates infrastructure problems rather than application issues.

(4) **Namespace exclusion**: create **`excluded_namespaces.csv`** (from UC-3.6.1) to exclude system namespaces from alerting while still including them in the overall trend chart for completeness.

### Step 2 — Create the search and alert
The primary SPL counts daily **Warning** events cluster-wide and computes a **7-day SMA** to smooth daily variance. The **`trend_flag`** classification:
— **SPIKE**: daily warnings exceed 2× the 7-day SMA AND exceed 50 (absolute floor prevents alerting on small clusters where a handful of events cause a large percentage spike)
— **DROP**: daily warnings drop to less than 30% of the SMA when the SMA is above 20 (may indicate a data collection gap or a successful remediation)
— **NORMAL**: within expected bounds

The breakdown variant groups Warning events by **`reason`** and **`namespace`**, then classifies severity:
— **HIGH**: OOMKilling, FailedScheduling, NodeNotReady, Evicted — these indicate resource exhaustion or node failures
— **MEDIUM**: BackOff, FailedMount, FailedAttachVolume, Unhealthy, FailedPulling, ImagePullBackOff, FreeDiskSpaceFailed — these indicate application or configuration issues
— **LOW**: all other Warning reasons — typically informational

The **`sparkline`** column provides an inline visual of the daily count trend per reason+namespace, making it easy to spot rising patterns.

Schedule the cluster-wide trend daily at **07:00** over **`-30d`** and alert on SPIKE or sustained increase (deviation_pct > 50 for 3+ consecutive days). Schedule the breakdown search daily and alert when any HIGH severity reason shows a **peak_daily** exceeding 2× its **avg_daily**.

### Step 3 — Validate
(a) Verify event collection: `index=containers sourcetype="kube:events" type="Warning" earliest=-1h | stats count`. Should be non-zero for any production cluster.
(b) Cross-check with `kubectl`: `kubectl get events --all-namespaces --field-selector type=Warning | wc -l` — account for the 1-hour **event TTL** when comparing.
(c) Test a Warning event: deploy a pod with a non-existent image tag: `kubectl run warn-test --image=nonexistent:latest` — this generates FailedPulling and ImagePullBackOff Warning events. Verify they appear: `index=containers sourcetype="kube:events" reason="FailedPulling" earliest=-5m`.
(d) Verify **trend calculation**: the 30-day search should show a **line chart** with the SMA smoothing daily fluctuations. If data is sparse, push additional test events to validate.
(e) Confirm **reason classification**: `index=containers sourcetype="kube:events" type="Warning" earliest=-7d | stats count by reason | sort -count | head 10`. The top reasons should map to the severity classification in the SPL.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **line chart** of daily warning count with **7-day SMA** overlay over 30 days — the trend direction is the primary signal.
- Row B: **single-value tiles** — today's warning count, deviation %, trend flag (SPIKE=red, NORMAL=green), top reason today, namespaces affected today.
- Row C: **stacked area chart** of daily warnings by reason over 7 days — shows which reason categories contribute most to the total.
- Row D: **reason+namespace breakdown table** — reason, ns, total_events, avg_daily, peak_daily, severity, last_example, trend sparkline. Sorted by total events, red rows for HIGH severity.
- **Alerting**: SPIKE flag → **Slack** `#platform-ops`; HIGH severity reason sustained increase → **PagerDuty** P3; OOMKilling or NodeNotReady > 10 in 1h → P2; sustained deviation > 50% for 3 days → **weekly escalation**.
- **Runbook** (owner: platform engineering): (1) identify the top reasons from the breakdown, (2) for OOMKilling: check memory limits and investigate leaks (UC-3.6.4), (3) for FailedScheduling: check node capacity and resource quotas (UC-3.6.4), (4) for BackOff: check pod logs for crash causes (UC-3.6.1), (5) for FailedMount: check PVC status and storage provisioner health.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **calendar heatmap** showing daily warning count as cell intensity over 30 days — reveals weekly patterns and anomalous days at a glance; pair with a **reason distribution pie chart** showing the proportion of each reason category; add a **namespace contribution bar chart** showing which namespaces generate the most warnings.
- **Alert design**: include `daily_warnings`, `sma_7d`, `deviation_pct`, `trend_flag`, `unique_reasons`, and the top 3 reasons by count in the alert payload; for breakdown alerts include `reason`, `ns`, `total_events`, `severity`, and `last_example`.
- **Event count is always zero** — the event collector may not have permission to list events; check the **ServiceAccount**'s **ClusterRole**: `kubectl get clusterrolebinding | grep <service-account>`.
- **Warning count drops to zero suddenly** — likely a data collection gap rather than cluster improvement. Check the collector pod health: `kubectl get pods -n <collector-ns>` and verify HEC connectivity.
- **Same event counted multiple times** — Kubernetes increments the `count` field on repeated identical events. If the collector captures each count update as a separate event, use `| dedup involvedObject.uid, reason, message` or sum the `count` field instead of counting rows.
- **Weekly aggregation variant** — the third SPL variant uses **`autoregress`** to compute **week-over-week** change percentages, classifying weeks as **DEGRADING** (>50% increase), **IMPROVING** (>30% decrease), or **STABLE**. This provides a higher-level view suitable for **weekly engineering reviews** and **capacity planning meetings** where daily noise would overwhelm the signal.
- **High warning rate from system namespaces** — kube-system and monitoring namespaces naturally generate more Warning events due to frequent pod scheduling and resource management. Use the namespace exclusion lookup to focus alerts on application namespaces.

## SPL

```spl
`comment("--- Kubernetes Warning Event Rate — 30-Day Trend with Reason Breakdown ---")`
index=containers sourcetype="kube:events" type="Warning"
| eval ns=coalesce(namespace, object_namespace, involvedObject.namespace, "unknown")
| eval reason=coalesce(reason, event_reason, "unknown")
| eval component=coalesce(source.component, reporting_component, source_component, "unknown")
| eval object_kind=coalesce(involvedObject.kind, object_kind, "unknown")
| bin _time span=1d
| stats count as daily_warnings,
    dc(reason) as unique_reasons,
    dc(ns) as affected_namespaces
    by _time
| trendline sma7(daily_warnings) as sma_7d
| eval deviation_pct=round(100 * (daily_warnings - sma_7d) / max(sma_7d, 1), 1)
| eval trend_flag=case(
    daily_warnings > sma_7d * 2 AND daily_warnings > 50, "SPIKE",
    daily_warnings < sma_7d * 0.3 AND sma_7d > 20, "DROP",
    1=1, "NORMAL")
| table _time daily_warnings sma_7d deviation_pct unique_reasons affected_namespaces trend_flag

`comment("--- Warning Event Breakdown by Reason and Namespace ---")`
index=containers sourcetype="kube:events" type="Warning"
| eval ns=coalesce(namespace, object_namespace, involvedObject.namespace, "unknown")
| eval reason=coalesce(reason, event_reason)
| eval object_name=coalesce(involvedObject.name, object_name)
| eval object_kind=coalesce(involvedObject.kind, object_kind)
| eval message_short=substr(coalesce(message, ""), 1, 150)
| bin _time span=1d
| stats count as daily_count,
    dc(object_name) as affected_objects,
    latest(message_short) as example_message
    by reason, ns, _time
| stats sum(daily_count) as total_events,
    avg(daily_count) as avg_daily,
    max(daily_count) as peak_daily,
    latest(affected_objects) as current_affected,
    latest(example_message) as last_example,
    sparkline(sum(daily_count)) as trend
    by reason, ns
| eval severity=case(
    reason IN ("OOMKilling","FailedScheduling","NodeNotReady","Evicted"), "HIGH",
    reason IN ("BackOff","FailedMount","FailedAttachVolume","Unhealthy"), "MEDIUM",
    reason IN ("FailedPulling","ImagePullBackOff","FreeDiskSpaceFailed"), "MEDIUM",
    1=1, "LOW")
| sort -total_events
| head 50
| table reason ns total_events avg_daily peak_daily current_affected severity last_example trend

`comment("--- Weekly Warning Trend Aggregation with Week-over-Week Change ---")`
index=containers sourcetype="kube:events" type="Warning"
| eval ns=coalesce(namespace, object_namespace, involvedObject.namespace, "unknown")
| eval reason=coalesce(reason, event_reason, "unknown")
| eval object_kind=coalesce(involvedObject.kind, object_kind, "unknown")
| eval object_name=coalesce(involvedObject.name, object_name, "unknown")
| bin _time span=1w
| stats count as weekly_warnings,
    dc(reason) as unique_reasons,
    dc(ns) as affected_namespaces,
    dc(object_name) as affected_objects
    by _time
| autoregress weekly_warnings as prev_week p=1
| eval wow_change=round(100 * (weekly_warnings - prev_week) / max(prev_week, 1), 1)
| eval wow_flag=case(wow_change > 50, "DEGRADING", wow_change < -30, "IMPROVING", 1=1, "STABLE")
| table _time weekly_warnings prev_week wow_change unique_reasons affected_namespaces affected_objects wow_flag
```

## Visualization

Line chart of daily warnings with 7-day SMA overlay, stacked area by reason, namespace heatmap, severity-colored reason table with sparklines, single-value tiles (trend direction, deviation %, top reason).

## Known False Positives

**event_ttl_gap** — Kubernetes events have a default TTL of 1 hour, meaning events generated during collector downtime are permanently lost. A gap in event collection creates an artificial dip in the trend chart followed by a return to normal that may look like a spike. Cross-reference collector pod uptime with trend anomalies to identify collection gaps.

**node_lifecycle_churn** — Autoscaler node additions and removals generate bursts of Warning events (NodeNotReady, FailedAttachVolume, Taint-related scheduling warnings) that reflect normal cluster scaling behavior, not application problems. Correlate with autoscaler events and suppress during scale-up/down windows.

**webhook_timeout_noise** — Admission webhooks that occasionally timeout generate Warning events from the API server that affect the cluster-wide trend without indicating application issues. These events originate from `source.component=apiserver` rather than `kubelet` or `scheduler`. Filter by component to separate infrastructure warnings from application warnings.

**count_field_inflation** — Kubernetes deduplicates identical events by incrementing the count field. If the event collector treats each count update as a new event, the daily warning count is inflated by repetition rather than distinct incidents. Use `| dedup involvedObject.uid reason message` or sum the `count` field for accurate trending.

**development_namespace_noise** — Development and testing namespaces with active experimentation generate high Warning event volumes (failed pulls, OOMKills from undersized limits, scheduling conflicts) that dominate the cluster-wide trend. Use the namespace exclusion or ownership lookup to separate production trend from development noise.

**controller_retry_amplification** — Kubernetes controllers retry failed operations with exponential backoff, generating a new Warning event on each retry attempt. A single underlying failure can produce dozens of Warning events over minutes, inflating the daily count disproportionately to the actual number of distinct issues.

## References

- [Kubernetes — Events API Reference](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/)
- [Kubernetes — Debug Pods and ReplicaSets](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)
- [Kubernetes — Node Problem Detector](https://kubernetes.io/docs/tasks/debug/debug-cluster/node-problem-detector/)
- [Splunk Connect for Kubernetes](https://github.com/splunk/splunk-connect-for-kubernetes)
- [Splunk trendline Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Trendline)
