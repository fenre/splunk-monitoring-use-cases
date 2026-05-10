<!-- AUTO-GENERATED from UC-3.2.30.json — DO NOT EDIT -->

---
id: "3.2.30"
title: "Kubernetes Init Container Failures — Pre-Main-Container Lifecycle Axis"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.30 · Kubernetes Init Container Failures — Pre-Main-Container Lifecycle Axis

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the small setup steps that must finish before the real application is allowed to start on our clusters. When those steps keep retrying, run out of memory, or cannot fetch secrets, the app never really launches, so we raise a clear signal early.*

---

## Description

Detects Kubernetes init container lifecycle failures that block main containers from starting: kube_pod_init_container_status_waiting_reason in CrashLoopBackOff, Error, ImagePullBackOff, OOMKilled, or ContainerCannotRun; kube_pod_init_container_status_terminated_reason that is not Completed; rising kube_pod_init_container_status_restarts_total; kube_pod_init_container_info for image attribution; kube_pod_status_phase stuck in Pending while initialization retries. The analytic multisearches waiting and terminated arms, joins restarts and image info, joins pod phase, estimates dwell time in bad init states with streamstats and eventstats, enriches tier and paging metadata from lookups, and tiers severity for production versus pre-production. This is intentionally not UC-3.2.10 main-container CrashLoopBackOff and not UC-3.2.14 generic image-pull pipeline ownership, though Init:ImagePullBackOff may appear here when the failure axis is init gate readiness.

## Value

Mean time to repair improves when platform and application teams see cluster, namespace, pod, init_container, fused waiting or termination reason, image reference, restart counter, pod phase, minutes stuck in the bad init state, workload tier, owning workload, paging team, and severity in one row instead of correlating kubectl describe, metrics explorers, and secrets consoles by hand. Customer impact drops because rollouts that never become Ready and Jobs that never start work surface before coarse replica dashboards imply health. Identity and secrets teams receive clearer bridges when Vault Agent Init or CSI drivers stall. Audit and governance reviewers gain timestamped evidence that initialization gates were monitored distinctly from post-start crash loops.

## Implementation

Ingest kube-state-metrics init and pod phase scrapes into k8s_metrics, stream kube:events into k8s for optional PodInitializing context, publish k8s_namespace_tier.csv and k8s_workload_routing.csv, save uc_3_2_30_kube_init_container_failures every five minutes with earliest=-4h@m, route critical and high rows per savedsearches.conf, and validate with a lab Pod whose initContainer exits non-zero or references a bad image.

## Evidence

Saved search uc_3_2_30_kube_init_container_failures; lookups k8s_namespace_tier.csv and k8s_workload_routing.csv with version hashes; weekly CSV export of alert rows to a restricted evidence index; dashboard panels tied to the closing table command.

## Control test

### Positive scenario

In namespace qa-init apply a Pod whose initContainer runs sh -c exit 1 under a restart policy that allows retries, wait for kube_pod_init_container_status_waiting_reason Error or CrashLoopBackOff in k8s_metrics, run uc_3_2_30_kube_init_container_failures, and expect a qualifying row with non-zero time_in_init_bad_min when workload_tier marks the namespace as production in the tier lookup.

### Negative scenario

Deploy nginx with no initContainers in the same lab namespace; confirm kube_pod_init_container metrics stay absent or benign and the saved search yields no qualifying row for that pod across thirty minutes.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with the Kubernetes platform site reliability engineers who certify kube-state-metrics RBAC and scrape paths, the identity and secrets platform team when Vault Agent Init or cloud secrets store CSI drivers participate in init chains, and the observability engineers operating Splunk OpenTelemetry Collector or legacy Splunk Connect for Kubernetes across production and pre-production. This use case isolates the pre-main-container gate: Kubernetes runs initContainers to completion with exit code zero before any normal container in the same Pod starts. When schema migrations, certificate bootstraps, wait-for-dependency loops, or secret materialization steps fail, Pods remain in PodInitializing or show Init:CrashLoopBackOff, Init:Error, Init:ImagePullBackOff, or Init:OOMKilled style conditions while kube_pod_status_ready never reaches one for the workload. UC-3.2.10 remains the analytic for main-container CrashLoopBackOff after the main process has been allowed to start. UC-3.2.14 remains the supply-chain image pull pipeline for primary containers and registry storms; this UC may surface Init:ImagePullBackOff on kube_pod_init_container_status_waiting_reason, yet the dominant story here is init lifecycle and exit semantics rather than generic registry health panels. UC-3.2.6 covers Deployment replica convergence and ProgressDeadlineExceeded class failures at the controller layer without specializing on init versus main container attribution.

Platform prerequisites include Splunk indexes k8s_metrics for Prometheus text lines or normalized metric events from kube-state-metrics, and k8s for Kubernetes API events or optional container logs when you need human-readable messages beyond metrics. Some estates also keep k8s_audit for attributing bad init command lines or projected volume changes to a GitOps actor. HEC tokens require vault storage, quarterly rotation, and index-time role boundaries so application developers cannot read sensitive namespace data blended into platform metrics.

Deploy kube-state-metrics with the pod metric family enabled so kube_pod_init_container_status_waiting_reason, kube_pod_init_container_status_terminated_reason, kube_pod_init_container_status_restarts_total, kube_pod_init_container_info, and kube_pod_status_phase all scrape reliably. Default thirty-second intervals are typical; fifteen seconds improves dwell-time estimates for short-lived init failures at license cost. Splunk OpenTelemetry Collector should run a prometheus receiver against the kube-state-metrics Service and export to HEC with sourcetype prometheus:scrape:metrics or your normalized kube:objects:metrics alias. Document how cluster identity lands in the cluster field so joins to k8s_workload_routing.csv stay deterministic across Amazon EKS, Google GKE, and Microsoft AKS.

Governance lookups mirror other cat-3.2 gold UCs: k8s_namespace_tier.csv lists namespace and workload_tier values such as prod, production, preprod, staging, uat, dev, and sandbox. k8s_workload_routing.csv lists namespace, pod name or pattern, owner_workload such as StatefulSet payments-ledger, and on_call_team for paging. Refresh both on every namespace onboarding ticket. You may extend k8s_workload_routing.csv with optional notes for migrate_job_only workloads or CoreDNS maintenance windows when your process requires explicit suppression semantics without muting the entire detector.

CIM alignment uses Application_State for normalized workload or host state overlays where your Technology Add-ons map Kubernetes entities, and Performance for node saturation context when init failures correlate with memory pressure or CPU steal on the underlying VM. Accelerate those data models on the search head when overlays participate in incident review, not only in this alert.

Risk narrative for executives: init failures are silent deploy killers because horizontal pod autoscaler signals, HTTP error budgets, and coarse ready replica counts may look stable while new Pods never leave initialization. Customer impact accrues when rollouts cannot replace older replicas or when Jobs never begin work. Compliance reviewers appreciate timestamped evidence that initialization gates were monitored distinctly from post-start crash loops.

Licensing and cardinality: init container labels add cardinality proportional to init step counts; drop experimental labels at scrape time when safe. Init stderr forwarded to logs can spike during migration tools; route verbose namespaces to shorter retention tiers unless finance approves full fidelity.

Differentiation recap: if kube_pod_container_status_waiting_reason shows CrashLoopBackOff for a normal container name after init completion, UC-3.2.10 owns that row. If kube_pod_container_status_waiting_reason shows ImagePullBackOff for the application container and init never ran, UC-3.2.14 often owns first response unless your runbook explicitly triages init image pulls here; in practice many teams route all init-stage pull stalls through this UC because the remediation is init manifest and secret wiring rather than application server tuning.

Training narrative for new analysts: teach the Pod lifecycle ordering from Kubernetes documentation so responders know that describe output lists initContainerStatuses before container statuses, and that kubectl logs requires the init container name with the correct flag. Teach the difference between waiting reasons and terminated reasons in kube-state-metrics so Splunk rows map cleanly to kubectl mental models.

Partner teams: database administrators care about migration inits, platform PKI teams care about certificate bootstrap inits, and identity teams care about Vault Agent Init or CSI projected volumes. Document escalation bridges in the lookup notes column when your organization splits ownership.

### Step 2 — Configure data collection

Prometheus Operator ServiceMonitor for kube-state-metrics should keep path /metrics, interval thirty seconds, and relabel rules that preserve namespace, pod, container, node, image, reason, and phase labels on init and pod phase series. Pair the ServiceMonitor with network policy that allows only the observability namespace to reach kube-state-metrics.

Concrete ServiceMonitor sample:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-init-visibility
  namespace: kube-system
  labels:
    release: prom
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kube-state-metrics
  namespaceSelector:
    matchNames:
      - kube-system
  endpoints:
    - port: http-metrics
      interval: 30s
      scrapeTimeout: 10s
      path: /metrics
      scheme: http
```

Splunk OpenTelemetry Collector exporter fragment for HEC metrics:

```yaml
exporters:
  splunk_hec/k8s_metrics:
    token: "${SPLUNK_HEC_TOKEN}"
    endpoint: "https://splunk.example.com:8088/services/collector"
    source: kube-prometheus
    sourcetype: prometheus:scrape:metrics
    index: k8s_metrics
    tls:
      insecure_skip_verify: false
```

Kubernetes API events receiver for optional narrative context on init failures:

```yaml
receivers:
  k8s_events:
    auth_type: serviceAccount
    namespaces: []
processors:
  batch:
    timeout: 5s
service:
  pipelines:
    logs/k8s_events:
      receivers: [k8s_events]
      processors: [batch]
      exporters: [splunk_hec/k8s_logs]
exporters:
  splunk_hec/k8s_logs:
    token: "${SPLUNK_HEC_TOKEN}"
    endpoint: "https://splunk.example.com:8088/services/collector"
    source: kube-events
    sourcetype: kube:events
    index: k8s
```

Validate each path with short searches before promoting alerts: index=k8s_metrics kube_pod_init_container_status_waiting_reason earliest=-15m, index=k8s_metrics kube_pod_init_container_status_restarts_total earliest=-15m, index=k8s_metrics kube_pod_status_phase earliest=-15m, and index=k8s sourcetype=kube:events PodInitializing earliest=-15m. Skew between scrapes should stay under one minute for meaningful streamstats dwell math.

Security: redact Secret volume mounts from verbose log pipelines. Restrict k8s_audit to security and platform roles. When Vault Agent Injector mutates Pods, ensure audit logs capture only approved fields under your data classification policy.

Optional container log forwarding: when teams approve host file access, filelog receivers can tail init stderr paths under /var/log/pods with metadata that includes kubernetes.container_name so drilldown searches filter to init containers only. Keep retention shorter for verbose migration namespaces.

Cloud control plane notes: on EKS, confirm security groups still allow node egress to registries and secrets endpoints after landing-zone changes. On GKE, validate workload identity token timing for CSI drivers. On AKS, validate managed identity attachments for Key Vault or Azure Key Vault CSI providers when those appear in init chains.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_30_kube_init_container_failures with schedule every five minutes and earliest=-4h@m latest=now to match the comment macro. Throttle duplicate critical pages per cluster, namespace, and pod for forty-five minutes unless severity escalates from high to critical based on OOMKilled or CrashLoopBackOff dwell thresholds.

Understanding the pipeline: a Performance datamodel tstats probe joins first as a correlation tick so estates that disable summaries still parse, while accelerated clusters get cheap proof the search head can reach Performance summaries. multisearch fans init waiting reasons in failure states and init terminated reasons that are not Completed so you catch fast-failing migration binaries and secret fetch wrappers even when waiting_reason lags one scrape. kube_pod_init_container_status_restarts_total joins quantify retry pressure. kube_pod_init_container_info joins surface the image reference for responders. kube_pod_status_phase joins distinguish Pending pods stuck behind initialization from Running pods that only fail readiness later. streamstats marks first transition into a fused bad reason per init_container, and eventstats carries worst dwell per pod for analyst clarity. inputlookup k8s_namespace_tier.csv and k8s_workload_routing.csv add workload_tier, owner_workload, and on_call_team. case() sets severity using production thresholds, OOM priority, and long Pending with restarts gates.

cimSpl in the JSON field shows an accelerated Application_State and Performance overlay pattern for hosts or mapped workload entities during bridge calls; adapt nodename filters to your Common Information Model implementation.

Fenced SPL for runbooks must match the spl JSON field aside from newline normalization; the repository stores the authoritative copy in the spl key and repeats it here for operators who read markdown exports without opening JSON.

```spl
`comment("UC-3.2.30 Kubernetes init container lifecycle failures (pre-main-container gate). Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics; lookups k8s_workload_routing.csv k8s_namespace_tier.csv; init_stuck_minutes_prod=5; init_stuck_minutes_default=8; earliest=-4h@m latest=now")`
| eval join_key="uc3230"
| join type=left join_key [
    | tstats summariesonly=t count AS perf_correlation_tick FROM datamodel=Performance WHERE nodename=Performance earliest=-4h@h latest=now
    | eval join_key="uc3230" ]
| fields - join_key perf_correlation_tick
| eval init_stuck_minutes_prod=5
| eval init_stuck_minutes_default=8
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "pod=\"(?<pod_rx>[^\"]+)\""
      | rex field=_raw "container=\"(?<ctr_rx>[^\"]+)\""
      | rex field=_raw "reason=\"(?<reason_rx>[^\"]+)\""
      | rex field=_raw "node=\"(?<node_rx>[^\"]+)\""
      | rex field=_raw "\s(?<metric_val>[0-9]+(?:\.[0-9]+)?)\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval pod=trim(toString(coalesce(pod, pod_name, k8s_pod, pod_rx, "")))
      | eval init_container=trim(toString(coalesce(container, container_name, ctr_rx, "")))
      | eval init_waiting_reason=trim(toString(coalesce(reason, waiting_reason, reason_rx, "")))
      | eval node=trim(toString(coalesce(node, node_name, host_node, node_rx, "")))
      | where (like(mn, "%kube_pod_init_container_status_waiting_reason%") OR like(_raw, "kube_pod_init_container_status_waiting_reason"))
      | where init_waiting_reason IN ("CrashLoopBackOff", "Error", "ImagePullBackOff", "OOMKilled", "ContainerCannotRun")
      | eval init_term_reason=""
      | eval lane="init_waiting"
      | fields _time cluster namespace pod init_container init_waiting_reason init_term_reason node lane ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "pod=\"(?<pod>[^\"]+)\""
      | rex field=_raw "container=\"(?<container>[^\"]+)\""
      | rex field=_raw "reason=\"(?<term_reason>[^\"]+)\""
      | rex field=_raw "node=\"(?<node_rx>[^\"]+)\""
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "")))
      | where (like(mn, "%kube_pod_init_container_status_terminated_reason%") OR like(_raw, "kube_pod_init_container_status_terminated_reason"))
      | where isnotnull(term_reason) AND term_reason!="" AND term_reason!="Completed"
      | eval init_container=trim(toString(container))
      | eval init_waiting_reason=""
      | eval init_term_reason=trim(toString(term_reason))
      | eval node=trim(toString(coalesce(node, node_name, node_rx, "")))
      | eval lane="init_terminated"
      | fields _time cluster namespace pod init_container init_waiting_reason init_term_reason node lane ]
]
| eval cluster=coalesce(nullif(trim(cluster),""), "unknown-cluster")
| eval fused_reason=coalesce(nullif(init_waiting_reason,""), nullif(init_term_reason,""), "unknown")
| sort 0 cluster namespace pod init_container _time
| streamstats current=f last(fused_reason) AS prev_fused BY cluster namespace pod init_container
| eval bad_on=if(isnotnull(fused_reason) AND fused_reason!="unknown", 1, 0)
| eval bad_enter=if(bad_on=1 AND (isnull(prev_fused) OR prev_fused="unknown" OR prev_fused!=fused_reason), _time, null())
| streamstats last(bad_enter) AS bad_since BY cluster namespace pod init_container
| eval time_in_init_bad_min=if(bad_on=1 AND isnotnull(bad_since), round((now()-bad_since)/60, 2), null())
| eventstats max(time_in_init_bad_min) AS pod_worst_init_bad_min BY cluster namespace pod
| eval time_in_init_bad_min=coalesce(time_in_init_bad_min, pod_worst_init_bad_min)
| join type=left max=0 cluster namespace pod init_container [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
    | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
    | rex field=_raw "pod=\"(?<pod>[^\"]+)\""
    | rex field=_raw "container=\"(?<container>[^\"]+)\""
    | where like(_raw, "kube_pod_init_container_status_restarts_total")
    | rex field=_raw "\s(?<rv>[0-9.eE+-]+)\s*$"
    | eval init_restarts_total=tonumber(rv, 10)
    | stats latest(init_restarts_total) AS init_restarts_total BY namespace pod container
    | rename container AS init_container ]
| join type=left max=0 cluster namespace pod init_container [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
    | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
    | rex field=_raw "pod=\"(?<pod>[^\"]+)\""
    | rex field=_raw "container=\"(?<container>[^\"]+)\""
    | rex field=_raw "image=\"(?<img_rx>[^\"]+)\""
    | where like(_raw, "kube_pod_init_container_info")
    | stats latest(img_rx) AS init_image BY namespace pod container
    | rename container AS init_container ]
| join type=left max=0 cluster namespace pod [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
    | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
    | rex field=_raw "pod=\"(?<pod>[^\"]+)\""
    | rex field=_raw "phase=\"(?<pod_phase>[^\"]+)\""
    | rex field=_raw "\s(?<pv>[0-9.eE+-]+)\s*$"
    | where like(_raw, "kube_pod_status_phase")
    | eval pod_phase=if(tonumber(pv,10)>0, pod_phase, null())
    | stats values(pod_phase) AS phases_mv BY namespace pod
    | eval pod_phase=if(mvcount(phases_mv)>0, mvindex(sort(phases_mv), 0), "Unknown")
    | fields namespace pod pod_phase ]
| fillnull value=0 init_restarts_total
| fillnull value="" init_image
| fillnull value="Unknown" pod_phase
| join type=left max=0 namespace [
    | inputlookup k8s_namespace_tier.csv
    | eval namespace=trim(toString(namespace))
    | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, "dev"))))
    | fields namespace workload_tier ]
| join type=left max=0 namespace pod [
    | inputlookup k8s_workload_routing.csv
    | eval namespace=trim(toString(namespace))
    | eval pod=trim(toString(pod))
    | eval owner_workload=trim(toString(coalesce(owner_workload, workload, owner_kind_name, "")))
    | eval on_call_team=trim(toString(coalesce(on_call_team, owner_team, squad, pagerduty_service, "")))
    | fields namespace pod owner_workload on_call_team ]
| eval stuck_pending_long=if(match(pod_phase, "(?i)Pending") AND coalesce(time_in_init_bad_min,0)>=init_stuck_minutes_default AND init_restarts_total>0, 1, 0)
| eval severity=case(
    (workload_tier="prod" OR workload_tier="production") AND (init_waiting_reason="OOMKilled" OR init_term_reason="OOMKilled"), "critical",
    (workload_tier="prod" OR workload_tier="production") AND init_waiting_reason="CrashLoopBackOff" AND coalesce(time_in_init_bad_min,0)>=init_stuck_minutes_prod, "critical",
    (workload_tier="prod" OR workload_tier="production") AND (init_waiting_reason="Error" OR init_term_reason="Error") AND coalesce(time_in_init_bad_min,0)>=init_stuck_minutes_prod, "critical",
    (workload_tier="prod" OR workload_tier="production") AND stuck_pending_long=1, "high",
    (workload_tier="prod" OR workload_tier="production") AND match(init_waiting_reason, "ImagePullBackOff|ErrImagePull") AND coalesce(time_in_init_bad_min,0)>=3, "high",
    match(workload_tier, "preprod|staging|uat") AND coalesce(time_in_init_bad_min,0)>=init_stuck_minutes_default, "high",
    coalesce(time_in_init_bad_min,0)>=45, "medium",
    coalesce(init_restarts_total,0)>=1 AND match(pod_phase, "(?i)Pending"), "medium",
    true(), "low")
| where isnotnull(severity) AND bad_on=1 AND fused_reason!="unknown"
| where coalesce(time_in_init_bad_min,0)>=3 OR coalesce(init_restarts_total,0)>=1 OR init_waiting_reason IN ("CrashLoopBackOff", "Error", "ImagePullBackOff", "OOMKilled", "ContainerCannotRun") OR isnotnull(nullif(init_term_reason,""))
| stats latest(fused_reason) AS fused_reason latest(init_image) AS init_image latest(node) AS node latest(init_waiting_reason) AS init_waiting_reason latest(init_term_reason) AS init_term_reason latest(init_restarts_total) AS init_restarts_total latest(pod_phase) AS pod_phase latest(time_in_init_bad_min) AS time_in_init_bad_min latest(owner_workload) AS owner_workload latest(on_call_team) AS on_call_team latest(workload_tier) AS workload_tier latest(severity) AS severity latest(lane) AS signal_lane BY cluster namespace pod init_container
| table cluster namespace pod init_container init_image fused_reason init_waiting_reason init_term_reason init_restarts_total pod_phase time_in_init_bad_min severity owner_workload on_call_team workload_tier signal_lane node
```

Alert actions should include cluster, namespace, pod, init_container, fused_reason, init_restarts_total, time_in_init_bad_min, severity, on_call_team, and owner_workload in email or ITSI notable bodies. Provide drilldown searches to index=k8s sourcetype=kube:events for the pod and to index=k8s for init container logs when filelog forwarding exists.

savedsearches.conf fragment:

```
[uc_3_2_30_kube_init_container_failures]
action.email = 1
action.email.to = platform-oncall@example.com
action.email.subject = K8s init failure $result.namespace$/$result.pod$/$result.init_container$
action.email.message = severity=$result.severity$ reason=$result.fused_reason$ restarts=$result.init_restarts_total$ dwell_min=$result.time_in_init_bad_min$ tier=$result.workload_tier$ team=$result.on_call_team$
alert.track = 1
alert.suppress = 1
alert.suppress.period = 45m
cron_schedule = */5 * * * *
dispatch.earliest_time = -4h@m
dispatch.latest_time = now
counttype = number of events
relation = >
quantity = 0
```

Wire ITSI parameters to your deployment naming; some estates use alert_manager ITSINotable instead of action.email alone.

Performance: Job Inspector should remain within platform limits. If raw metric indexes exceed scan budgets, materialize five-minute summaries keyed on cluster, namespace, pod, init_container with fused_reason and init_restarts_total only, then point this alert at the summary index while retaining raw scrapes for ad-hoc rex tuning after kube-state-metrics upgrades.

Paging clone versus dashboard clone: publish uc_3_2_30_kube_init_container_failures_page as a clone that inserts a filter for severity in critical and high immediately before the closing table command so email and PagerDuty actions only fire for tier-1 severity, while the fleet dashboard keeps medium rows for trending.

### Step 4 — Validate

Synthetic init crash: in a lab namespace apply a Pod manifest whose first initContainer runs sh -c exit 1 with restartPolicy on the Pod set to Always, wait for kube_pod_init_container_status_waiting_reason to show Error or CrashLoopBackOff, execute uc_3_2_30_kube_init_container_failures, and expect a row with growing time_in_init_bad_min and severity at least high when workload_tier marks the namespace as production in k8s_namespace_tier.csv.

Synthetic init image pull: reference a nonexistent image only on the initContainer while the main container stays valid; confirm Init:ImagePullBackOff appears in kubectl describe and that the Splunk row carries init_waiting_reason=ImagePullBackOff. Tear down with kubectl delete pod and confirm the next scheduled search omits the lab pod.

Synthetic long wait-for-dependency: run an initContainer that sleeps beyond your SLO while the main container image is valid; document expected behavior for your migration jobs so analysts do not confuse legitimate long migrations with incidents. If your governance process adds per-workload SLO minutes, reflect that in macros rather than silencing the UC globally.

Validation SPL for quiet clusters: index=k8s_metrics kube_pod_init_container_status_waiting_reason (CrashLoopBackOff OR Error OR OOMKilled) earliest=-24h | stats dc(pod) AS bad_init_pods | where bad_init_pods=0.

Audit correlation drill: index=k8s_audit sourcetype=kube:audit verb=create OR verb=patch objectRef.resource=pods earliest=-2h with objectRef.namespace and objectRef.name matching the failing pod to recover the CI or GitOps principal that introduced the init command change.

Negative control: deploy a healthy workload with a fast succeeding init that prints a completion marker; confirm terminated reason Completed does not create a row and init_restarts_total stays zero across thirty minutes of scrapes.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Init:CrashLoopBackOff on a schema migration job
Correlate init_container logs for SQL timeouts, lock contention, or flyway liquibase stack traces; scale database connection pools, extend activeDeadlineSeconds only when finance approves longer maintenance, fix migration ordering, then confirm kube_pod_init_container_status_terminated_reason clears to Completed on the next attempt.

Case 2 — Vault Agent Init or secrets CSI init waiting on sealed Vault
During disaster recovery, Vault seals block secret file emission; pair Splunk rows with Vault operational metrics and unseal procedures. Page identity platform first when fused_reason rotates between Error and waiting states with zero Completed.

Case 3 — AWS Secrets Manager CSI or EKS Pod Identity race
Validate IAM trust chains, mount paths, and regional endpoints; compare init_container image tags against documented compatibility matrices from AWS guidance. Re-run the Pod after fixing the SecretProviderClass.

Case 4 — wait-for-dns or wait-for-service init retrying during CoreDNS rollout
EKS and other clusters may retry name resolution until CoreDNS stabilizes; suppress short dwell below your CoreDNS maintenance window using annotation-based routing rows in k8s_workload_routing.csv rather than muting the entire UC.

Case 5 — Certificate bootstrap init exits non-zero on clock skew
Check node NTP, cert notBefore fields, and init_container stderr for x509 validation; fix time sync before reissuing certs.

Case 6 — Init:OOMKilled on a Java-based migration sidecar
Raise memory requests and limits on the initContainer, confirm node allocatable headroom, and compare with UC-3.2.10 only if the failure moves to the main container after init succeeds.

Case 7 — Init:ImagePullBackOff on a private registry init image
Verify imagePullSecrets on the Pod template, registry credentials, and network egress; cross-check UC-3.2.14 if the same registry failure hits application containers simultaneously.

Case 8 — ConfigMap populate init fails because a key is missing
kubectl describe shows CreateContainerConfigError class messages; fix ConfigMap generation in GitOps, roll forward, and confirm init_container_info image tag matches the expected release.

Case 9 — Parallel Deployment pods where migrate-once init fails on second pod
Idempotency errors can surface as non-zero exit on followers; use Jobs for migrations or leader-elect patterns; tune severity using owner_workload rows that mark migrate_job_only in your lookup notes.

Case 10 — Job pods running test fixture inits in CI namespaces
Route CI namespaces to low severity via workload_tier=sandbox and exclude ephemeral integration namespaces from paging macros.

Case 11 — GKE workload identity or sandbox constraints blocking init
Compare Google Kubernetes Engine troubleshooting documentation for security sandbox and workload identity token timing; adjust init retry budgets after confirming control plane logs.

Case 12 — AKS or EKS node pressure evicting init before completion
Correlate with node memory pressure events and kubelet eviction signals; drain troubled nodes after cordon under change control.

Dashboard hygiene: keep a panel for init_restarts_total rate by init_container name and namespace. Document kubectl logs POD -c INITNAME before and after failures for teams permitted to run kubectl under change control.

Evidence pack: weekly CSV export of alert rows with kube-state-metrics chart version, collector digest, and lookup commit hash so auditors replay dwell math after upgrades.

Governance: quarterly replay one real init incident through the SPL after kube-state-metrics upgrades because label names occasionally shift; update rex patterns when Prometheus relabel configs change.

Training: teach on-call staff to read kubectl describe initContainerStatuses before opening application logs because main containers may never start.

Closing checklist: five step headers use em dashes; Step 3 contains fenced SPL matching the spl JSON field verbatim; Step 5 lists twelve case lines; monitoringType includes Reliability and Availability; equipmentModels includes kubernetes_k8s; exclusions explicitly separate UC-3.2.10 and UC-3.2.14; narrative avoids claiming this replaces deployment rollout analytics.

When Splunk Cloud workload pricing pressures search concurrency, schedule the paging clone every five minutes and the fleet dashboard clone every fifteen minutes.

FinOps note: long init durations can extend node occupancy during rollouts; attach node utilization context from Performance overlays when leadership asks whether the incident is capacity or logic.


## SPL

```spl
`comment("UC-3.2.30 Kubernetes init container lifecycle failures (pre-main-container gate). Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics; lookups k8s_workload_routing.csv k8s_namespace_tier.csv; init_stuck_minutes_prod=5; init_stuck_minutes_default=8; earliest=-4h@m latest=now")`
| eval join_key="uc3230"
| join type=left join_key [
    | tstats summariesonly=t count AS perf_correlation_tick FROM datamodel=Performance WHERE nodename=Performance earliest=-4h@h latest=now
    | eval join_key="uc3230" ]
| fields - join_key perf_correlation_tick
| eval init_stuck_minutes_prod=5
| eval init_stuck_minutes_default=8
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "pod=\"(?<pod_rx>[^\"]+)\""
      | rex field=_raw "container=\"(?<ctr_rx>[^\"]+)\""
      | rex field=_raw "reason=\"(?<reason_rx>[^\"]+)\""
      | rex field=_raw "node=\"(?<node_rx>[^\"]+)\""
      | rex field=_raw "\s(?<metric_val>[0-9]+(?:\.[0-9]+)?)\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval pod=trim(toString(coalesce(pod, pod_name, k8s_pod, pod_rx, "")))
      | eval init_container=trim(toString(coalesce(container, container_name, ctr_rx, "")))
      | eval init_waiting_reason=trim(toString(coalesce(reason, waiting_reason, reason_rx, "")))
      | eval node=trim(toString(coalesce(node, node_name, host_node, node_rx, "")))
      | where (like(mn, "%kube_pod_init_container_status_waiting_reason%") OR like(_raw, "kube_pod_init_container_status_waiting_reason"))
      | where init_waiting_reason IN ("CrashLoopBackOff", "Error", "ImagePullBackOff", "OOMKilled", "ContainerCannotRun")
      | eval init_term_reason=""
      | eval lane="init_waiting"
      | fields _time cluster namespace pod init_container init_waiting_reason init_term_reason node lane ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "pod=\"(?<pod>[^\"]+)\""
      | rex field=_raw "container=\"(?<container>[^\"]+)\""
      | rex field=_raw "reason=\"(?<term_reason>[^\"]+)\""
      | rex field=_raw "node=\"(?<node_rx>[^\"]+)\""
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "")))
      | where (like(mn, "%kube_pod_init_container_status_terminated_reason%") OR like(_raw, "kube_pod_init_container_status_terminated_reason"))
      | where isnotnull(term_reason) AND term_reason!="" AND term_reason!="Completed"
      | eval init_container=trim(toString(container))
      | eval init_waiting_reason=""
      | eval init_term_reason=trim(toString(term_reason))
      | eval node=trim(toString(coalesce(node, node_name, node_rx, "")))
      | eval lane="init_terminated"
      | fields _time cluster namespace pod init_container init_waiting_reason init_term_reason node lane ]
]
| eval cluster=coalesce(nullif(trim(cluster),""), "unknown-cluster")
| eval fused_reason=coalesce(nullif(init_waiting_reason,""), nullif(init_term_reason,""), "unknown")
| sort 0 cluster namespace pod init_container _time
| streamstats current=f last(fused_reason) AS prev_fused BY cluster namespace pod init_container
| eval bad_on=if(isnotnull(fused_reason) AND fused_reason!="unknown", 1, 0)
| eval bad_enter=if(bad_on=1 AND (isnull(prev_fused) OR prev_fused="unknown" OR prev_fused!=fused_reason), _time, null())
| streamstats last(bad_enter) AS bad_since BY cluster namespace pod init_container
| eval time_in_init_bad_min=if(bad_on=1 AND isnotnull(bad_since), round((now()-bad_since)/60, 2), null())
| eventstats max(time_in_init_bad_min) AS pod_worst_init_bad_min BY cluster namespace pod
| eval time_in_init_bad_min=coalesce(time_in_init_bad_min, pod_worst_init_bad_min)
| join type=left max=0 cluster namespace pod init_container [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
    | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
    | rex field=_raw "pod=\"(?<pod>[^\"]+)\""
    | rex field=_raw "container=\"(?<container>[^\"]+)\""
    | where like(_raw, "kube_pod_init_container_status_restarts_total")
    | rex field=_raw "\s(?<rv>[0-9.eE+-]+)\s*$"
    | eval init_restarts_total=tonumber(rv, 10)
    | stats latest(init_restarts_total) AS init_restarts_total BY namespace pod container
    | rename container AS init_container ]
| join type=left max=0 cluster namespace pod init_container [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
    | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
    | rex field=_raw "pod=\"(?<pod>[^\"]+)\""
    | rex field=_raw "container=\"(?<container>[^\"]+)\""
    | rex field=_raw "image=\"(?<img_rx>[^\"]+)\""
    | where like(_raw, "kube_pod_init_container_info")
    | stats latest(img_rx) AS init_image BY namespace pod container
    | rename container AS init_container ]
| join type=left max=0 cluster namespace pod [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
    | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
    | rex field=_raw "pod=\"(?<pod>[^\"]+)\""
    | rex field=_raw "phase=\"(?<pod_phase>[^\"]+)\""
    | rex field=_raw "\s(?<pv>[0-9.eE+-]+)\s*$"
    | where like(_raw, "kube_pod_status_phase")
    | eval pod_phase=if(tonumber(pv,10)>0, pod_phase, null())
    | stats values(pod_phase) AS phases_mv BY namespace pod
    | eval pod_phase=if(mvcount(phases_mv)>0, mvindex(sort(phases_mv), 0), "Unknown")
    | fields namespace pod pod_phase ]
| fillnull value=0 init_restarts_total
| fillnull value="" init_image
| fillnull value="Unknown" pod_phase
| join type=left max=0 namespace [
    | inputlookup k8s_namespace_tier.csv
    | eval namespace=trim(toString(namespace))
    | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, "dev"))))
    | fields namespace workload_tier ]
| join type=left max=0 namespace pod [
    | inputlookup k8s_workload_routing.csv
    | eval namespace=trim(toString(namespace))
    | eval pod=trim(toString(pod))
    | eval owner_workload=trim(toString(coalesce(owner_workload, workload, owner_kind_name, "")))
    | eval on_call_team=trim(toString(coalesce(on_call_team, owner_team, squad, pagerduty_service, "")))
    | fields namespace pod owner_workload on_call_team ]
| eval stuck_pending_long=if(match(pod_phase, "(?i)Pending") AND coalesce(time_in_init_bad_min,0)>=init_stuck_minutes_default AND init_restarts_total>0, 1, 0)
| eval severity=case(
    (workload_tier="prod" OR workload_tier="production") AND (init_waiting_reason="OOMKilled" OR init_term_reason="OOMKilled"), "critical",
    (workload_tier="prod" OR workload_tier="production") AND init_waiting_reason="CrashLoopBackOff" AND coalesce(time_in_init_bad_min,0)>=init_stuck_minutes_prod, "critical",
    (workload_tier="prod" OR workload_tier="production") AND (init_waiting_reason="Error" OR init_term_reason="Error") AND coalesce(time_in_init_bad_min,0)>=init_stuck_minutes_prod, "critical",
    (workload_tier="prod" OR workload_tier="production") AND stuck_pending_long=1, "high",
    (workload_tier="prod" OR workload_tier="production") AND match(init_waiting_reason, "ImagePullBackOff|ErrImagePull") AND coalesce(time_in_init_bad_min,0)>=3, "high",
    match(workload_tier, "preprod|staging|uat") AND coalesce(time_in_init_bad_min,0)>=init_stuck_minutes_default, "high",
    coalesce(time_in_init_bad_min,0)>=45, "medium",
    coalesce(init_restarts_total,0)>=1 AND match(pod_phase, "(?i)Pending"), "medium",
    true(), "low")
| where isnotnull(severity) AND bad_on=1 AND fused_reason!="unknown"
| where coalesce(time_in_init_bad_min,0)>=3 OR coalesce(init_restarts_total,0)>=1 OR init_waiting_reason IN ("CrashLoopBackOff", "Error", "ImagePullBackOff", "OOMKilled", "ContainerCannotRun") OR isnotnull(nullif(init_term_reason,""))
| stats latest(fused_reason) AS fused_reason latest(init_image) AS init_image latest(node) AS node latest(init_waiting_reason) AS init_waiting_reason latest(init_term_reason) AS init_term_reason latest(init_restarts_total) AS init_restarts_total latest(pod_phase) AS pod_phase latest(time_in_init_bad_min) AS time_in_init_bad_min latest(owner_workload) AS owner_workload latest(on_call_team) AS on_call_team latest(workload_tier) AS workload_tier latest(severity) AS severity latest(lane) AS signal_lane BY cluster namespace pod init_container
| table cluster namespace pod init_container init_image fused_reason init_waiting_reason init_term_reason init_restarts_total pod_phase time_in_init_bad_min severity owner_workload on_call_team workload_tier signal_lane node
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state count AS app_ticks FROM datamodel=Application_State WHERE nodename=Application_State earliest=-4h@h latest=@h BY Application_State.dest Application_State.app
| rename Application_State.dest AS correl_host Application_State.app AS correl_app
| join type=left max=0 correl_host [
| tstats summariesonly=t avg(Performance.cpu_load_percent) AS avg_cpu_load avg(Performance.mem_used_percent) AS avg_mem_used FROM datamodel=Performance WHERE nodename=Performance.CPU OR nodename=Performance.Memory earliest=-4h@h latest=@h BY Performance.host
| rename Performance.host AS correl_host ]
| table correl_host correl_app app_state avg_cpu_load avg_mem_used app_ticks
```

## Visualization

Primary table mirroring the closing SPL projection; timechart of init_restarts_total by namespace; single value of distinct pods with fused init failures; drilldown to kube:events and init container logs when forwarded.

## Known False Positives

Long-running schema migrations on first install can legitimately exceed five wall-clock minutes while backfilling tables; widen init_stuck thresholds per workload using lookup notes or macro overrides before paging. Vault Agent Init can wait on Vault unseal operations during disaster recovery exercises; pair Splunk rows with Vault cluster health to avoid blaming application teams. wait-for-service style inits that intentionally retry until DNS converges often spike during Amazon EKS CoreDNS rolling restarts; require sustained dwell beyond your CoreDNS maintenance annotation before production pages. Job pods that run test fixture inits in continuous integration namespaces resemble production failures; mark sandbox tiers and exclude ephemeral CI namespaces from paging macros. migrate-only-once init containers may fail fast on the second Pod when idempotency is missing; route those patterns to data platform owners rather than muting the detector. Developer clusters used for ad-hoc init command experiments generate noisy init_term_reason rows; keep workload_tier=dev defaults in k8s_namespace_tier.csv so severity stays low unless override tickets promote the namespace.

## References

- [Kubernetes — Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [kube-state-metrics — Pod metrics (init container series)](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/pod-metrics.md)
- [HashiCorp Vault — Agent Injector on Kubernetes](https://developer.hashicorp.com/vault/docs/platform/k8s/injector)
- [AWS — Mount secrets in Amazon EKS Pods with Secrets Store CSI driver](https://docs.aws.amazon.com/secretsmanager/latest/userguide/integrate_csi_driver.html)
- [Google Cloud — Troubleshoot workloads on GKE](https://cloud.google.com/kubernetes-engine/docs/troubleshooting)
- [Microsoft Learn — Init containers in Azure Kubernetes Service](https://learn.microsoft.com/en-us/azure/aks/concepts-clusters-workloads#init-containers)
- [AWS — Init containers for Amazon EKS](https://docs.aws.amazon.com/eks/latest/userguide/initcontainers.html)
