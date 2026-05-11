<!-- AUTO-GENERATED from UC-3.2.1.json — DO NOT EDIT -->

---
id: "3.2.1"
title: "Kubernetes Pod Container Restart Churn and Rolling Restart-Rate Anomalies"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.1 · Kubernetes Pod Container Restart Churn and Rolling Restart-Rate Anomalies

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We count how often the small programs inside our cloud boxes stop and start again, because steady little stops can wear a service down even when everything still looks green. When the pattern spikes or breaks the rules we set for important spaces, we raise a clear signal so teams fix it early.*

---

## Description

Tracks rising container restart churn using kube-state-metrics cumulative counter kube_pod_container_status_restarts_total interpreted as short-window deltas and hourly rollups, compares each cluster to a rolling median baseline, highlights percentile-style deviations such as a fleet that historically sat near half a restart per hour jumping toward eight, surfaces quiet restarters that stay below CrashLoopBackOff thresholds yet sustain a few restarts every hour with healthy probes between attempts, correlates Kubernetes API events for OOMKilled, BackOff, liveness failures, graceful kills, eviction, and preemption signals, detects bursts where several pods tied to the same controller restart inside a few minutes after a likely configuration push, and enforces namespace-tier restart budgets including zero-tolerance slices for platform namespaces while forecasting how quickly a namespace exhausts its hourly allowance.

## Value

Operations teams gain an early warning that is orthogonal to waiting-reason dashboards: workloads can remain Ready while containers oscillate, which erodes SLO error budgets and burns incident attention before customers file tickets. Product and finance stakeholders see fewer surprise outages caused by slow leaks of reliability margin, and platform owners receive evidence-backed narratives that separate noisy batch estates from customer-facing clusters. Audit and engineering leadership retain timestamped exports that show budget math, burst signatures, and correlated event reasons without conflating this signal with image pull stalls or probe-only analytics owned elsewhere.

## Implementation

Land kube-state-metrics scrapes on k8s_metrics, ship kube events to k8s, publish pod_inventory.csv with namespace tier and restart budgets, schedule uc_3_2_1_kube_restart_churn every five minutes with earliest=-6h, wire severities to paging macros, and rehearse a lab Deployment that toggles a failing command to produce bounded deltas before production rollout.

## Evidence

Saved search uc_3_2_1_kube_restart_churn, versioned pod_inventory.csv, weekly CSV export of alert rows to a restricted evidence index, and dashboard panels tied to the closing table command with lookup commit hashes recorded.

## Control test

### Positive scenario

In namespace qa-restart-churn deploy a Deployment whose container exits zero after thirty seconds on a loop, wait for kube_pod_container_status_restarts_total to climb across two five-minute tstats spans, execute uc_3_2_1_kube_restart_churn, and expect non-zero restarts_per_hour with severity at least warning when pod_inventory marks the namespace as production tier.

### Negative scenario

Run a stable nginx Deployment with no command overrides in the same namespace for one hour and confirm cumulative restarts remain flat so restarts_window stays near zero and the saved search emits no critical rows.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the Kubernetes platform site reliability group, the observability engineers who operate Splunk OpenTelemetry Collector DaemonSets, and the service owners who maintain pod_inventory.csv as the authoritative mapping between namespaces, controllers, paging teams, and restart budgets. This use case deliberately concentrates on container restart churn expressed as deltas of kube-state-metrics counter kube_pod_container_status_restarts_total, not on kubelet waiting reasons that require CrashLoopBackOff semantics, and not on registry pull failures that keep containers from starting. UC-3.2.10 remains the right home for exponential backoff state machines tied to waiting_reason labels. UC-3.2.14 remains the supply-chain lane for ErrImagePull and ImagePullBackOff dwell analytics. UC-3.2.43 stays focused on probe failure taxonomies without turning this search into another probe dashboard. UC-3.1.13 documents dockerd-side restart loops on hosts that are not orchestrated by Kubernetes, which is a different process model than kubelet-managed containers on nodes. Keeping those boundaries crisp avoids duplicate incidents and preserves trust when severity fires.

Platform telemetry prerequisites begin with kube-state-metrics deployed with the pod metric family enabled so kube_pod_container_status_restarts_total appears with stable namespace, pod, container, and uid labels plus any cluster label your Prometheus relabel_config or OpenTelemetry transform adds. Scrape intervals of thirty seconds are typical; fifteen seconds tightens rolling-window fidelity at license cost. Splunk indexes should split responsibilities: k8s_metrics for Prometheus text or normalized metric events, k8s for Kubernetes API events and optional container logs, and k8s_audit when you must attribute a burst of restarts to a GitOps actor or kubectl change. HEC tokens require vault storage, quarterly rotation, and index-time role boundaries so developer tenants cannot read kube-system adjacent fields they should not see.

The counter is cumulative for the lifetime of a kubelet-managed container. That means naive max() snapshots without time ordering mistake long-lived pods for healthy pods. The analytics path therefore time-buckets with tstats, sorts by cluster namespace pod container and time, applies streamstats to derive bucket-to-bucket deltas, and rolls a twelve-bucket sum to approximate an hourly restart count when your span is five minutes. Baselines use eventstats median calculations per cluster on the hourly rate field so a fleet that historically hovered near half a restart per hour can surface a multiplicative deviation when the same median jumps toward eight restarts per hour without waiting for CrashLoopBackOff semantics to appear.

Governance artifact pod_inventory.csv is mandatory for this UC because restart budgets are not universal constants. Columns should include cluster, namespace, pod when you need pod-specific overrides, container when sidecars deserve separate budgets, owner_kind such as Deployment or StatefulSet, owner_name such as checkout-api, namespace_tier such as customer-prod or batch-elt, owner_team for paging, restart_budget_per_hour as a numeric allowance, and optional maintenance_mode to suppress pages during approved change windows. Refresh the lookup on every namespace onboarding ticket and version it in git so evidence packs replay with the same thresholds.

CIM alignment uses Application_State for coarse workload posture overlays and Performance for node CPU saturation joins during incident review when you suspect cgroup throttling or noisy neighbors amplify restart churn. Accelerate those data models on a schedule your search head cluster can sustain; this UC’s primary detection path remains kube-native metrics and events rather than CIM alone.

Risk and licensing notes: high-cardinality labels inflate metric volume; drop experimental labels at scrape time when safe. Burst detection uses distinct pod counts per controller slice and time bucket; ensure owner_name is populated or bursts will under-count in loosely owned namespaces.

Differentiation recap: restart churn here measures how often containers actually restart, including quiet oscillators that recover quickly between attempts, while CrashLoopBackOff analytics waits for kubelet backoff state. Image pull failures precede meaningful restart counters. Docker daemon loops on bare metal are out of scope for this JSON.

SLO posture: express restart burn as a rolling fraction of restart_budget_per_hour per namespace_tier, then stack rank clusters for weekly reliability reviews. When customer namespaces consume more than seventy percent of the hourly budget for three consecutive evaluation windows, open a proactive ticket even if severity stayed at warning so product teams see drift before paging.

### Step 2 — Configure data collection

Deploy kube-state-metrics with RBAC that can list and watch pods and owners. If you use Prometheus Operator, attach a ServiceMonitor that scrapes port http-metrics every thirty seconds and preserves labels required for Splunk extractions. If you use Splunk OpenTelemetry Collector, configure a prometheus receiver scrape_configs entry that discovers the kube-state-metrics Service in kube-system or your observability namespace and forwards to a splunk_hec exporter that sets index k8s_metrics and sourcetype prometheus:scrape:metrics consistently.

Concrete ServiceMonitor sketch:

apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-restarts
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kube-state-metrics
  endpoints:
    - port: http-metrics
      interval: 30s
      path: /metrics

Concrete Splunk HEC exporter sketch for metrics:

exporters:
  splunk_hec/k8s_metrics:
    token: ${SPLUNK_HEC_TOKEN}
    endpoint: https://splunk.example.com:8088/services/collector
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics

Ship Kubernetes events with a kubernetes_events or k8s_events receiver into index k8s and sourcetype kube:events so BackOff, OOMKilled, Killing, Failed, Unhealthy, Evicted, and preemption narratives are available for join correlation within a two-hour trailing window. Normalize cluster fields early so tstats BY cluster matches pod_inventory.csv cluster strings exactly.

props.conf discipline: ensure metric events extract metric_name, Value, namespace, pod, container, and cluster with consistent spellings. If your pipeline stores prometheus:scrape:metrics as raw text without indexed metric_name, add transforms or metric-schema rules until tstats predicates on kube_pod_container_status_restarts_total remain selective.

Validation searches before alerting: index=k8s_metrics kube_pod_container_status_restarts_total earliest=-15m should return samples; index=k8s sourcetype=kube:events earliest=-15m should return event traffic; inputlookup pod_inventory.csv should show non-zero row counts for production namespaces. Skew between scrapes and events should stay under sixty seconds for meaningful last_restart_event_time correlation.

### Step 3 — Create the search and alert

Save the detection SPL as uc_3_2_1_kube_restart_churn with schedule every five minutes and time window earliest=-6h latest=now to keep enough history for twelve five-minute buckets in streamstats while limiting scan cost. Map severity to routing: critical pages platform on-call, warning routes to owner_team from pod_inventory, info feeds dashboards only unless namespace_tier marks customer impact. Throttle duplicate critical alerts per cluster, namespace, and pod for forty-five minutes unless deviation_factor doubles again within the throttle window.

Macro tunables belong in a shared macros.conf stanza: burst_pod_floor default five pods in the same owner_name and bucket, restart_budget_per_hour defaults per namespace_tier, and kube_system_zero_tolerance flag forcing critical on the first hourly restart in kube-system.

Fenced SPL for runbooks must match the spl JSON field aside from newline normalization:

```spl
`comment("UC-3.2.1 Kubernetes container restart churn from kube-state-metrics kube_pod_container_status_restarts_total. Requires indexed metric_name or equivalent and Value or _value field; coalesce arms tolerate OTel versus legacy scrape shapes. Tunables: burst_pod_floor=5; earliest=-6h; span=5m; pod_inventory.csv")`
| tstats latest(Value) AS restart_cumulative WHERE (index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-6h@5m latest=now (metric_name="kube_pod_container_status_restarts_total" OR MetricName="kube_pod_container_status_restarts_total" OR metricName="kube_pod_container_status_restarts_total") BY _time span=5m cluster namespace pod container
| eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "unknown-cluster")))
| eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, "")))
| eval pod=trim(toString(coalesce(pod, pod_name, k8s_pod, "")))
| eval container=trim(toString(coalesce(container, container_name, "")))
| sort 0 cluster namespace pod container _time
| streamstats current=f window=2 global=f last(restart_cumulative) AS prev_cumulative BY cluster namespace pod container
| eval restarts_window=if(isnull(prev_cumulative), 0, max(restart_cumulative-prev_cumulative, 0))
| streamstats current=t window=12 global=f sum(restarts_window) AS restarts_rolling_1h BY cluster namespace pod container
| eval restarts_per_hour=round(coalesce(restarts_rolling_1h, restarts_window*12), 3)
| eventstats median(restarts_per_hour) AS baseline_per_hour BY cluster
| eval baseline_per_hour=round(coalesce(baseline_per_hour, 0), 4)
| eval deviation_factor=case(baseline_per_hour>0.05, round(restarts_per_hour/baseline_per_hour, 2), restarts_per_hour>0, 99, true(), 0)
| join type=left max=0 cluster namespace pod container [
    | inputlookup pod_inventory.csv
    | eval cluster=trim(toString(coalesce(cluster, k8s_cluster, "")))
    | eval namespace=trim(toString(namespace))
    | eval pod=trim(toString(pod))
    | eval container=trim(toString(container))
    | eval owner_kind=trim(toString(coalesce(owner_kind, workload_kind, controller_kind, "Unknown")))
    | eval owner_name=trim(toString(coalesce(owner_name, workload_name, controller_name, deployment, "")))
    | eval namespace_tier=trim(toString(coalesce(namespace_tier, env_tier, tier, "standard")))
    | eval owner_team=trim(toString(coalesce(owner_team, squad, pagerduty_service, on_call_team, "")))
    | eval restart_budget_per_hour=tonumber(coalesce(restart_budget_per_hour, budget_rph, max_rph, "999"), 10)
    | fields cluster namespace pod container owner_kind owner_name namespace_tier owner_team restart_budget_per_hour ]
| eval owner_kind=coalesce(owner_kind, "Unknown")
| eval owner_name=coalesce(owner_name, "unassigned")
| eval namespace_tier=coalesce(namespace_tier, "standard")
| eval owner_team=coalesce(owner_team, "platform-unowned")
| eval restart_budget_per_hour=coalesce(restart_budget_per_hour, 999)
| eventstats dc(eval(if(restarts_window>0, pod, null()))) AS pods_restarting_same_slice BY cluster owner_name _time
| eval burst_after_config_push=if(pods_restarting_same_slice>=5 AND restarts_window>0, 1, 0)
| join type=left max=0 cluster namespace pod [
    search index=k8s sourcetype="kube:events" earliest=-2h latest=now
    | eval msg=lower(trim(toString(coalesce(message, Message, ""))))
    | eval rp=trim(toString(coalesce(reason, Reason, "")))
    | eval pod_ev=trim(toString(coalesce(involvedObject.name, involvedObject_name, pod, "")))
    | eval ns_ev=trim(toString(coalesce(metadata.namespace, namespace, "")))
    | eval cl_ev=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, "")))
    | where match(msg, "oomkilled|back-off|liveness probe failed|killed.*grace|preempt|evicted|failed") OR match(lower(rp), "backoff|failed|warning|unhealthy")
    | eval last_restart_reason=case(
        match(msg, "oomkilled"), "OOMKilled_event",
        match(msg, "liveness probe failed"), "LivenessProbeFailed_event",
        match(msg, "back-off"), "BackOff_event",
        match(msg, "preempt"), "Preempted_event",
        match(msg, "evicted"), "Evicted_event",
        match(msg, "killed"), "Killed_grace_event",
        true(), rp)
    | stats latest(_time) AS last_restart_event_time latest(last_restart_reason) AS last_restart_reason BY cl_ev ns_ev pod_ev
    | rename cl_ev AS cluster ns_ev AS namespace pod_ev AS pod ]
| eval lying_low_churn=if(restarts_per_hour>=3 AND restarts_per_hour<=7 AND deviation_factor<8 AND NOT match(coalesce(last_restart_reason,""), "OOMKilled"), 1, 0)
| eval severity=case(
    (namespace="kube-system" OR match(namespace_tier, "(?i)platform|control-plane")) AND restarts_per_hour>=1, "critical",
    restarts_per_hour>restart_budget_per_hour, "critical",
    burst_after_config_push=1 AND restarts_per_hour>=1, "critical",
    deviation_factor>=16 AND restarts_per_hour>=4, "critical",
    lying_low_churn=1, "warning",
    deviation_factor>=8 OR restarts_per_hour>=8, "warning",
    restarts_per_hour>=0.5 AND deviation_factor>=3, "warning",
    restarts_per_hour>0, "info",
    true(), "info")
| where restarts_per_hour>0.01 OR burst_after_config_push=1 OR match(severity, "critical|warning")
| dedup cluster namespace pod container sortby -_time
| table cluster namespace owner_kind owner_name pod container restarts_window restarts_per_hour baseline_per_hour deviation_factor last_restart_reason last_restart_event_time namespace_tier owner_team severity
```

Paging actions should embed cluster, namespace, owner_kind, owner_name, pod, container, restarts_per_hour, baseline_per_hour, deviation_factor, burst_after_config_push, namespace_tier, owner_team, and severity in the JSON payload for chat bridges. Provide drilldown searches to kube:events and to container logs filtered on the pod for the last sixty minutes.

Forecasting restart budget burn for leadership reviews: schedule a non-paging report version that adds a per-namespace sum of restarts_per_hour divided by restart_budget_per_hour to express percent of hourly allowance consumed, then extrapolate linearly across business hours to show projected exhaustion when the current slope persists. That narrative complements instantaneous alerts without duplicating UC-3.2.10.

### Step 4 — Validate

Synthetic churn pod: in namespace qa-restart-churn create a Deployment whose container sleeps then exits non-zero on a short loop so kube_pod_container_status_restarts_total increases across at least two five-minute buckets. Execute uc_3_2_1_kube_restart_churn and expect positive restarts_window, non-zero restarts_per_hour, and severity at least warning when pod_inventory marks the namespace as production tier for lab realism.

Synthetic burst: patch five distinct pod templates under the same owner_name within five minutes or scale a Deployment above five replicas with the same failing command and confirm pods_restarting_same_slice crosses the burst floor with burst_after_config_push set.

Synthetic quiet oscillator: command sequence that exits zero after a brief unhealthy window without entering CrashLoopBackOff on your cluster should still produce three to seven hourly restarts when tuned; confirm lying_low_churn flags warning rather than hiding the row.

Negative control: stable nginx with no overrides should yield restarts_window near zero for sixty minutes and no critical rows.

Tear-down: delete lab objects, confirm saved search result count returns to zero, and archive validation notes with kube-state-metrics chart version and collector digest.

### Step 5 — Operationalize & Troubleshoot

Case 1 — lying-low restarter oscillating three to seven times per hour

Investigate cgroup memory and CPU limits first, then application-level retry storms. Collect kubectl logs for the previous instance, compare against liveness timings, and tune backoff or fix the underlying exception rather than muting the alert.

Case 2 — burst-of-restarts after a configuration push

Correlate kube_audit or GitOps commit metadata with the alert minute. Roll back the offending ConfigMap or Deployment, validate ReplicaSet generation regresses, and re-run the search to confirm burst clears.

Case 3 — OOMKilled-driven churn

Raise memory limits or fix leaks; verify last_restart_reason shows OOMKilled_event and cross-check assign-memory-resource guidance. Pair with node memory pressure metrics before blaming the application alone.

Case 4 — liveness probe flap killing containers

Widen timeouts or split startup versus liveness probes. Compare event text containing liveness probe failed with application readiness timelines.

Case 5 — image rollout that legitimately restarts pods once

Expect a short spike in restarts_window. Suppress only when change records show an approved rollout window and replicas converge healthy within two scrape intervals.

Case 6 — batch namespace with acceptable churn

Confirm pod_inventory restart_budget_per_hour reflects intentional churn. Downgrade routing to informational dashboards for those namespaces.

Case 7 — kube-system restart budget breach

Treat as platform incident: cordon suspect nodes, review DaemonSet and DNS pods, and escalate to cluster administrators before application teams.

Case 8 — eviction-driven churn on a drained node

Follow UC-3.2.33 drain guidance; verify Evicted_event correlation and node status before paging service owners.

Case 9 — preempt-driven churn on Spot pools

Align disruption budgets and pod disruption budgets; downgrade when cloud provider preemption notices align with timestamps.

Case 10 — cluster-wide restart-rate anomaly

When median baseline_per_hour is low but deviation_factor spikes across many namespaces, suspect control plane or networking incidents rather than a single bad Deployment.

Case 11 — correlated application container versus sidecar restart

Use pod_inventory container-level rows to see if the mesh proxy restarts while the app container stays stable; route to mesh owners when sidecar alone churns.

Case 12 — single pod stuck restarting silently without loud events

Deep dive with kubectl describe and previous logs; expand event join window temporarily and verify scrape gaps are not masking reasons.

Governance: quarterly replay a historical incident through the SPL after kube-state-metrics upgrades because label names occasionally shift. Document rex or field-alias adjustments in the same change ticket as scraper upgrades.

Performance: if Job Inspector shows excessive scan cost, materialize five-minute summaries of kube_pod_container_status_restarts_total into a summary index keyed by cluster namespace pod container, then point tstats at the summary for alerting while retaining raw scrapes for tuning.

Evidence pack: archive weekly CSV exports with lookup commit hash, burst threshold version, and collector image digest so auditors can replay deviation math without guesswork.


## SPL

```spl
`comment("UC-3.2.1 Kubernetes container restart churn from kube-state-metrics kube_pod_container_status_restarts_total. Requires indexed metric_name or equivalent and Value or _value field; coalesce arms tolerate OTel versus legacy scrape shapes. Tunables: burst_pod_floor=5; earliest=-6h; span=5m; pod_inventory.csv")`
| tstats latest(Value) AS restart_cumulative WHERE (index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-6h@5m latest=now (metric_name="kube_pod_container_status_restarts_total" OR MetricName="kube_pod_container_status_restarts_total" OR metricName="kube_pod_container_status_restarts_total") BY _time span=5m cluster namespace pod container
| eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "unknown-cluster")))
| eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, "")))
| eval pod=trim(toString(coalesce(pod, pod_name, k8s_pod, "")))
| eval container=trim(toString(coalesce(container, container_name, "")))
| sort 0 cluster namespace pod container _time
| streamstats current=f window=2 global=f last(restart_cumulative) AS prev_cumulative BY cluster namespace pod container
| eval restarts_window=if(isnull(prev_cumulative), 0, max(restart_cumulative-prev_cumulative, 0))
| streamstats current=t window=12 global=f sum(restarts_window) AS restarts_rolling_1h BY cluster namespace pod container
| eval restarts_per_hour=round(coalesce(restarts_rolling_1h, restarts_window*12), 3)
| eventstats median(restarts_per_hour) AS baseline_per_hour BY cluster
| eval baseline_per_hour=round(coalesce(baseline_per_hour, 0), 4)
| eval deviation_factor=case(baseline_per_hour>0.05, round(restarts_per_hour/baseline_per_hour, 2), restarts_per_hour>0, 99, true(), 0)
| join type=left max=0 cluster namespace pod container [
    | inputlookup pod_inventory.csv
    | eval cluster=trim(toString(coalesce(cluster, k8s_cluster, "")))
    | eval namespace=trim(toString(namespace))
    | eval pod=trim(toString(pod))
    | eval container=trim(toString(container))
    | eval owner_kind=trim(toString(coalesce(owner_kind, workload_kind, controller_kind, "Unknown")))
    | eval owner_name=trim(toString(coalesce(owner_name, workload_name, controller_name, deployment, "")))
    | eval namespace_tier=trim(toString(coalesce(namespace_tier, env_tier, tier, "standard")))
    | eval owner_team=trim(toString(coalesce(owner_team, squad, pagerduty_service, on_call_team, "")))
    | eval restart_budget_per_hour=tonumber(coalesce(restart_budget_per_hour, budget_rph, max_rph, "999"), 10)
    | fields cluster namespace pod container owner_kind owner_name namespace_tier owner_team restart_budget_per_hour ]
| eval owner_kind=coalesce(owner_kind, "Unknown")
| eval owner_name=coalesce(owner_name, "unassigned")
| eval namespace_tier=coalesce(namespace_tier, "standard")
| eval owner_team=coalesce(owner_team, "platform-unowned")
| eval restart_budget_per_hour=coalesce(restart_budget_per_hour, 999)
| eventstats dc(eval(if(restarts_window>0, pod, null()))) AS pods_restarting_same_slice BY cluster owner_name _time
| eval burst_after_config_push=if(pods_restarting_same_slice>=5 AND restarts_window>0, 1, 0)
| join type=left max=0 cluster namespace pod [
    search index=k8s sourcetype="kube:events" earliest=-2h latest=now
    | eval msg=lower(trim(toString(coalesce(message, Message, ""))))
    | eval rp=trim(toString(coalesce(reason, Reason, "")))
    | eval pod_ev=trim(toString(coalesce(involvedObject.name, involvedObject_name, pod, "")))
    | eval ns_ev=trim(toString(coalesce(metadata.namespace, namespace, "")))
    | eval cl_ev=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, "")))
    | where match(msg, "oomkilled|back-off|liveness probe failed|killed.*grace|preempt|evicted|failed") OR match(lower(rp), "backoff|failed|warning|unhealthy")
    | eval last_restart_reason=case(
        match(msg, "oomkilled"), "OOMKilled_event",
        match(msg, "liveness probe failed"), "LivenessProbeFailed_event",
        match(msg, "back-off"), "BackOff_event",
        match(msg, "preempt"), "Preempted_event",
        match(msg, "evicted"), "Evicted_event",
        match(msg, "killed"), "Killed_grace_event",
        true(), rp)
    | stats latest(_time) AS last_restart_event_time latest(last_restart_reason) AS last_restart_reason BY cl_ev ns_ev pod_ev
    | rename cl_ev AS cluster ns_ev AS namespace pod_ev AS pod ]
| eval lying_low_churn=if(restarts_per_hour>=3 AND restarts_per_hour<=7 AND deviation_factor<8 AND NOT match(coalesce(last_restart_reason,""), "OOMKilled"), 1, 0)
| eval severity=case(
    (namespace="kube-system" OR match(namespace_tier, "(?i)platform|control-plane")) AND restarts_per_hour>=1, "critical",
    restarts_per_hour>restart_budget_per_hour, "critical",
    burst_after_config_push=1 AND restarts_per_hour>=1, "critical",
    deviation_factor>=16 AND restarts_per_hour>=4, "critical",
    lying_low_churn=1, "warning",
    deviation_factor>=8 OR restarts_per_hour>=8, "warning",
    restarts_per_hour>=0.5 AND deviation_factor>=3, "warning",
    restarts_per_hour>0, "info",
    true(), "info")
| where restarts_per_hour>0.01 OR burst_after_config_push=1 OR match(severity, "critical|warning")
| dedup cluster namespace pod container sortby -_time
| table cluster namespace owner_kind owner_name pod container restarts_window restarts_per_hour baseline_per_hour deviation_factor last_restart_reason last_restart_event_time namespace_tier owner_team severity
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state count AS ev FROM datamodel=Application_State WHERE nodename=Application_State earliest=-4h@h latest=@h BY Application_State.dest Application_State.app
| rename Application_State.dest AS k8s_node Application_State.app AS workload_key
| join type=left k8s_node [
    | tstats summariesonly=t avg(Performance.cpu_load_percent) AS cpu_avg FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-4h@h latest=@h BY Performance.host
    | rename Performance.host AS k8s_node ]
| where app_state!="running" OR cpu_avg>92
```

## Visualization

Primary table matching the closing SPL projection; timechart of restarts_per_hour by namespace; overlay of cluster baseline_per_hour; burst heatmap by owner_name; single value of deviation_factor max per cluster.

## Known False Positives

Rolling image refreshes triggered by kubectl set image or GitOps syncs legitimately restart Pods once per ReplicaSet wave; expect a short-lived rise in restarts_window that should collapse within one or two scrape intervals after the rollout stabilizes, and compare timestamps against kube_audit subjects if you ingest API audit JSON. Horizontal Pod Autoscaler scale-in events can delete Pods that still had low restart counters while siblings keep running; the churn concentrates on removed Pods rather than signaling application pathology, so join HPAs only when restarts climb on remaining replicas. Voluntary evictions during node-pressure or priority preemption reorder work without a bad container image; pair eviction messages with node conditions before paging application teams, and read UC-3.2.33 for drain choreography so you do not confuse cordon-and-drain turbulence with spontaneous app failure. Spot and preemptible pools inject deliberate instance loss; bursts that align with cloud preemption notices and node disappearance should downgrade severity unless customer-tier namespaces lack PDB coverage. Batch and CI namespaces may intentionally burn higher restart budgets during chaos drills or data-loader Jobs; pod_inventory.csv should mark those tiers with generous restart_budget_per_hour values so the alert respects expected churn. Cluster upgrades that recycle DaemonSets can elevate kube-system counters briefly; keep platform namespaces on strict budgets but allow maintenance windows via lookup flags such as maintenance_mode=1 with reviewer approval. Dual scrapers emitting duplicate kube-state-metrics samples occasionally double deltas until deduplication lands; watch for mirrored _time rows with identical restart_cumulative values. Short scrape outages followed by catch-up scrapes can synthesize a synthetic spike; require two consecutive intervals above threshold or compare against kube-state-metrics scrape interval metadata when available.

## References

- [kube-state-metrics pod metrics including container restart counter](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/pod-metrics.md)
- [Kubernetes pod lifecycle and restart behavior](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Kubernetes kubelet node agent reference](https://kubernetes.io/docs/reference/node/)
- [Kubernetes debug running pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)
- [Assign memory resources and diagnose OOM](https://kubernetes.io/docs/tasks/configure-pod-container/assign-memory-resource/)
- [Kubernetes Event v1 API reference](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/)
- [Splunk Add-on for Kubernetes overview](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
- [OpenTelemetry Kubernetes collector documentation](https://opentelemetry.io/docs/platforms/kubernetes/getting-started/)
- [kubectl describe command reference](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#describe)
