<!-- AUTO-GENERATED from UC-3.6.3.json — DO NOT EDIT -->

---
id: "3.6.3"
title: "Deployment Velocity Trending"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.6.3 · Deployment Velocity Trending

## Description

Measures **Kubernetes** deployment rollout velocity per namespace and cluster by counting daily `ScalingReplicaSet` events, computing 7-day moving averages and deviation percentages, and classifying deployment patterns as SURGE, FREEZE, or NORMAL — combined with success/failure rate trending that reveals whether delivery cadence is producing stable or problematic releases.

## Value

Deployment velocity is the heartbeat of a platform team's delivery health: a sudden surge often correlates with incident-driven hotfixes or release train deadlines that increase change-failure risk, while an unexpected freeze signals blocked pipelines, broken CI, or organizational friction. Trending velocity alongside success rates gives engineering leadership the metrics to balance speed against stability.

## Implementation

Collect Kubernetes events (ScalingReplicaSet, SuccessfulCreate, ProgressDeadlineExceeded) and deployment status updates via Splunk Connect for Kubernetes into index=containers. Build two search variants: 30-day deployment velocity trend with 7-day SMA and surge/freeze classification, and per-namespace success/failure rate analysis. Alert on SURGE or FREEZE velocity patterns and when any namespace success rate drops below 90%.

## Detailed Implementation

Prerequisites
• **Kubernetes** 1.24+ cluster with deployment workloads across multiple namespaces — the trending analysis requires at least **14 days** of event history to produce meaningful 7-day SMAs; 30 days is ideal.
• **Splunk Connect for Kubernetes** deployed to collect **`sourcetype=kube:events`** (event stream), **`sourcetype=kube:deployment:status`** (deployment object updates), and **`sourcetype=kube:audit`** (API server audit logs). Alternative: **Splunk OpenTelemetry Collector** with the **`k8s_events`** receiver and **`k8sobjects`** receiver.
• **Kubernetes audit logging** enabled at the API server level with policy capturing `create`, `update`, and `patch` operations on `deployments.apps` resources at the **RequestResponse** or **Metadata** audit level — this provides the **user identity** behind each deployment change.
• **Splunk HEC** token for **`index=containers`** with sourcetype routing for events, deployment status, and audit logs.
• Optional: **ArgoCD** 2.6+ with **notifications** configured to send sync events to Splunk HEC as **`sourcetype=argocd:events`** — this enriches deployment velocity with **GitOps context** (commit hash, sync status, health status).
• Splunk RBAC: users running velocity searches need **`srchIndexesAllowed`** including `containers`; assign via a custom role (**`platform_analyst`**).
• **License estimate**: deployment events generate ~2–5 KB per rollout; a cluster with 50 daily deployments produces ~5–10 MB/day of deployment-related events.

Step 1 — Configure data collection
(1) **Kubernetes event collection**: ensure **`sourcetype=kube:events`** captures events with reasons **ScalingReplicaSet** (deployment controller scaling up/down replica sets during rollout), **SuccessfulCreate** (new pod created), **NewReplicaSetAvailable** (rollout complete), **ProgressDeadlineExceeded** (rollout failed — stuck or unhealthy), **FailedCreate** (pod creation failure), and **BackOff** (crash-loop after deployment). These events carry `involvedObject.name` (the ReplicaSet name, from which the **deployment name** is derived by stripping the trailing hash).

(2) **Deployment status collection**: collect **`sourcetype=kube:deployment:status`** via the OTel **`k8sobjects`** receiver watching Deployment objects. Key fields: **`metadata.name`**, **`metadata.namespace`**, **`status.replicas`**, **`status.readyReplicas`**, **`status.updatedReplicas`**, **`status.observedGeneration`**. A change in **`observedGeneration`** signals a new rollout.

(3) **API audit logs**: collect **`sourcetype=kube:audit`** to capture who initiated each deployment change. Key fields: **`user.username`**, **`verb`** (create/update/patch), **`objectRef.resource`** (deployments), **`objectRef.namespace`**, **`objectRef.name`**. This enables per-user deployment velocity tracking for DORA metric attribution.

(4) **ArgoCD integration** (optional): configure ArgoCD **notifications** with a webhook template targeting **Splunk HEC**. Events include `sync.status` (Synced, OutOfSync), `health.status` (Healthy, Degraded, Progressing), `revision` (git commit), and `source.repoURL`. This provides **GitOps provenance** for each deployment.

(5) **Namespace ownership lookup**: create **`namespace_owners.csv`** with columns `namespace`, `team`, `service_tier` (production/staging/development) to route velocity alerts to the correct team and filter dashboards by ownership.

Step 2 — Create the search and alert
The primary SPL counts distinct deployments per day from **ScalingReplicaSet** events. The **deployment name** is extracted from the ReplicaSet name by stripping the trailing random hash (the last segment after the final hyphen). The **`timechart`** with `by ns` shows per-namespace contribution to daily velocity.

The **`trendline sma7`** computes a 7-day simple moving average of the cluster-wide daily deployment count. The **`velocity_flag`** classifies each day:
— **SURGE**: more than 2× the 7-day average (unusual spike in deployments — often correlates with **release trains**, incident **hotfix storms**, or automated **scaling events**)
— **FREEZE**: less than 30% of the 7-day average AND fewer than 5 deployments (pipeline blockage or organizational pause)
— **NORMAL**: within expected bounds

The success/failure variant tracks deployment outcomes by namespace. A namespace with a `success_rate` below 90% likely has **broken CI/CD pipelines**, **misconfigured resource limits**, or **failing health checks** that cause `ProgressDeadlineExceeded` events.

Schedule the velocity trend daily at **08:00** over **`-30d`** and alert on SURGE or FREEZE flags. Schedule the success/failure search daily and alert when any production namespace (filtered via the **`namespace_owners`** lookup) drops below 90% success rate.

Step 3 — Validate
(a) Cross-check with `kubectl`: `kubectl get events --all-namespaces --field-selector reason=ScalingReplicaSet --sort-by=.lastTimestamp | tail -20` — count the events from today and compare with the Splunk search output for the same day.
(b) Trigger a test deployment: `kubectl set image deployment/nginx nginx=nginx:latest -n default` and verify the event appears in Splunk within 1–2 minutes.
(c) Test a **failed deployment**: create a deployment with a non-existent image tag (`kubectl set image deployment/nginx nginx=nginx:nonexistent`) and confirm `ProgressDeadlineExceeded` or `BackOff` events surface in the failure search.
(d) Verify **namespace coverage**: `index=containers sourcetype="kube:events" reason="ScalingReplicaSet" earliest=-24h | stats dc(namespace) as ns_count`. Should match the number of namespaces with active deployments.
(e) If ArgoCD is configured: `index=containers sourcetype="argocd:events" earliest=-24h | stats count by sync_status`. Should show Synced/OutOfSync counts.

Step 4 — Operationalize dashboards and runbooks
• Row A: **line chart** with daily deployment count and **7-day SMA** overlay over 30 days — the SMA reveals the **delivery cadence** trend.
• Row B: **single-value tiles** — today's deployment count, deviation % from SMA, velocity flag (SURGE in red, FREEZE in blue, NORMAL in green), number of namespaces with deployments today.
• Row C: **stacked area chart** of deployments by namespace over 30 days — shows which namespaces drive the most deployment activity.
• Row D: **namespace health table** — columns: ns, total_successes, total_failures, success_rate, avg_daily_deploys, peak_daily_deploys, health, trend sparkline. Red rows for POOR health.
• **Alerting**: SURGE flag → Slack `#platform-ops` (informational — investigate whether the spike is a release train or incident response); FREEZE flag → Slack + email to engineering leads (investigate pipeline blockage); namespace success_rate < 90% → **PagerDuty** P3 to the owning team; sustained FREEZE > 3 days → escalation to engineering management.
• **Runbook** (owner: platform engineering): (1) for SURGE — check if correlates with a release window, if not check for automated scaling or runaway CI triggers, (2) for FREEZE — check CI/CD pipeline status, recent infrastructure changes, or deployment freezes, (3) for low success rate — check ProgressDeadlineExceeded events for affected deployments and review resource limits, health checks, and image availability.

Step 5 — Visualization, alert design, and troubleshooting
• **Visualization**: use a **calendar heatmap** (Dashboard Studio custom viz or HTML panel) showing daily deployment count as cell color intensity — reveals weekly patterns (e.g., low weekends, peak Tuesdays) and anomalous days; pair with a **DORA metrics panel** showing deployment frequency, change failure rate (failures / total), and mean time to recovery derived from the time between a `ProgressDeadlineExceeded` event and the next `NewReplicaSetAvailable` event for the same deployment.
• **Alert design**: include `velocity_flag`, `cluster_total`, `sma_7d`, `deviation_pct`, and the top 3 namespaces by deployment count in the alert payload; for success-rate alerts include `ns`, `total_failures`, `success_rate`, and the most recent failure event message.
• **ScalingReplicaSet events missing** — Kubernetes events have a default TTL of 1 hour; if the event collector polls less frequently than every 60 minutes, events may age out. Increase the collector's poll frequency or configure the API server's `--event-ttl` flag.
• **Deployment count is inflated** — a single deployment update generates multiple ScalingReplicaSet events (one for the new ReplicaSet scaling up, one for the old scaling down). The `dc(deployment)` aggregation handles this by counting unique deployments, not events.
• **ArgoCD events not arriving** — verify the notification template and HEC endpoint; check ArgoCD controller logs for webhook delivery errors.
• **All deployments show as failures** — the failure reasons list may not match your cluster's event patterns; check `index=containers sourcetype="kube:events" | stats count by reason | sort -count` to discover the actual reason values and adjust the search.

## SPL

```spl
`comment("--- Deployment Velocity — Daily/Weekly Rollouts by Namespace Over 30 Days ---")`
index=containers sourcetype="kube:events" reason="ScalingReplicaSet"
| eval ns=coalesce(namespace, object_namespace, involvedObject.namespace, "unknown")
| eval deployment=coalesce(involvedObject.name, object_name, "unknown")
| eval deployment=mvindex(split(deployment, "-"), 0, mvcount(split(deployment, "-")) - 2)
| bin _time span=1d
| stats dc(deployment) as unique_deploys,
    count as rollout_events,
    dc(ns) as namespaces_touched
    by _time, ns
| timechart span=1d sum(unique_deploys) as daily_deployments by ns limit=15
| addtotals fieldname=cluster_total
| trendline sma7(cluster_total) as sma_7d
| eval deviation_pct=round(100 * (cluster_total - sma_7d) / max(sma_7d, 1), 1)
| eval velocity_flag=case(
    cluster_total > sma_7d * 2, "SURGE",
    cluster_total < sma_7d * 0.3 AND cluster_total < 5, "FREEZE",
    1=1, "NORMAL")
| fields _time cluster_total sma_7d deviation_pct velocity_flag *

`comment("--- Deployment Success/Failure Rate by Team Namespace ---")`
index=containers (sourcetype="kube:events" OR sourcetype="kube:deployment:status")
| eval reason=coalesce(reason, event_reason)
| eval ns=coalesce(namespace, object_namespace, involvedObject.namespace)
| eval deployment=coalesce(involvedObject.name, object_name, deployment_name)
| eval is_success=if(reason IN ("ScalingReplicaSet", "SuccessfulCreate", "NewReplicaSetAvailable"), 1, 0)
| eval is_failure=if(reason IN ("ProgressDeadlineExceeded", "FailedCreate", "BackOff", "ReplicaSetCreateError"), 1, 0)
| bin _time span=1d
| stats sum(is_success) as successes,
    sum(is_failure) as failures,
    dc(deployment) as unique_deploys
    by ns, _time
| stats sum(successes) as total_successes,
    sum(failures) as total_failures,
    avg(unique_deploys) as avg_daily_deploys,
    max(unique_deploys) as peak_daily_deploys,
    sparkline(sum(unique_deploys)) as trend
    by ns
| eval success_rate=round(100 * total_successes / max(1, total_successes + total_failures), 1)
| eval health=case(
    success_rate >= 99, "EXCELLENT",
    success_rate >= 95, "GOOD",
    success_rate >= 90, "FAIR",
    1=1, "POOR")
| sort -total_failures
| table ns total_successes total_failures success_rate avg_daily_deploys peak_daily_deploys health trend

`comment("--- Deployment Attribution — Who Deployed What and When ---")`
index=containers sourcetype="kube:audit" verb IN ("create","update","patch") objectRef.resource="deployments"
| eval deployer=coalesce('user.username', 'user.groups{}', "unknown")
| eval ns=coalesce('objectRef.namespace', namespace)
| eval deployment='objectRef.name'
| eval deploy_time=strftime(_time, "%Y-%m-%d %H:%M")
| stats count as deploy_actions, dc(deployment) as unique_deploys, values(deployment) as deployments, latest(deploy_time) as last_deploy by deployer, ns
| sort -deploy_actions
| head 30
| table deployer ns unique_deploys deploy_actions last_deploy deployments
```

## Visualization

Line chart with 7-day SMA overlay, stacked area by namespace, velocity sparklines, single-value tiles (daily total, deviation %, surge/freeze count), namespace health table with success rate.

## Known False Positives

**hpa_scaling_noise** — HorizontalPodAutoscaler-driven scaling generates ScalingReplicaSet events that are not code deployments but resource adjustments. These inflate the velocity count during load spikes. Filter by excluding events where the deployment's `observedGeneration` did not change between consecutive events — HPA scaling does not increment the generation counter.

**cronjob_deployment_churn** — CronJob-managed workloads create and destroy pods on schedule, generating deployment-like events that inflate the velocity count. Exclude namespaces or deployments known to contain only CronJobs via the namespace_owners lookup.

**ci_environment_rebuild** — Development and staging namespaces may have automated pipelines that rebuild and redeploy every commit, producing artificially high deployment counts that skew the cluster-wide SMA. Filter the production-velocity alert to production-tier namespaces only using the service_tier field from the namespace_owners lookup.

**rollback_double_count** — A failed deployment followed by a rollback generates two sets of ScalingReplicaSet events (the failed rollout and the rollback), counting as two deployments when only one intentional change occurred. Correlate with ProgressDeadlineExceeded events and count the rollback as part of the same deployment lifecycle.

**weekend_freeze_pattern** — Organizations that do not deploy on weekends will consistently trigger the FREEZE flag on Saturdays and Sundays. Adjust the FREEZE threshold to exclude weekends or use a weekday-only SMA by filtering `| where strftime(_time, "%u") < 6`.

**namespace_migration_surge** — When workloads are migrated between namespaces (e.g., during cluster consolidation or namespace reorganization), both the source and destination namespaces show deployment activity that inflates the velocity count. Correlate with namespace lifecycle events and suppress during planned migration windows.

## References

- [Kubernetes — Deployments Rolling Update Strategy](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-update-deployment)
- [Kubernetes — Events API Reference](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/)
- [DORA Metrics — Deployment Frequency](https://dora.dev/guides/dora-metrics-four-keys/)
- [Splunk Connect for Kubernetes](https://github.com/splunk/splunk-connect-for-kubernetes)
- [ArgoCD — Notifications and Webhook Configuration](https://argo-cd.readthedocs.io/en/stable/operator-manual/notifications/)
