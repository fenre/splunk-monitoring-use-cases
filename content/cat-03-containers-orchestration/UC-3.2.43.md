<!-- AUTO-GENERATED from UC-3.2.43.json — DO NOT EDIT -->

---
id: "3.2.43"
title: "Kubernetes Readiness/Liveness/Startup Probe Failures — Probe-State Axis"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.43 · Kubernetes Readiness/Liveness/Startup Probe Failures — Probe-State Axis

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the health checks that our cloud uses to decide whether a program is truly ready to serve traffic, before the system gives up and starts looping restarts. When those checks fail in waves, we raise a clear signal early so teams fix timing or dependencies sooner.*

---

## Description

Detects repeated readiness, liveness, and startup probe failures at the kubelet probe-event layer before workloads tip into CrashLoopBackOff: Kubernetes Unhealthy events whose messages name probe failures, kubelet counters kubelet_probe_failed or prober_probe_total with result failed, readiness gate flapping from kube_pod_container_status_ready and kube_pod_status_ready transitions, timeout versus HTTP 5xx hints parsed from event text, and tier-aware severity after joins to namespace tier and workload routing lookups. This is intentionally not UC-3.2.10 main-container CrashLoopBackOff, not UC-3.2.30 init container gates, and not UC-3.2.41 service zero-ready endpoints as the primary signal.

## Value

Mean time to repair improves when platform and application teams see cluster, namespace, pod, container, probe class, unhealthy event counts, kubelet probe scrape hits, readiness flaps, timeout and 5xx hints, last event time, workload tier, owning workload, paging team, severity, and an evidence snippet in one row while the main process may still be running. Customer impact drops because rolling updates, dependency brownouts, and mis-tuned timeoutSeconds or periodSeconds surface before service endpoints drain and before restart backoff dominates dashboards.

## Implementation

Ingest Unhealthy Kubernetes events and kubelet probe counters into Splunk, scrape kube-state-metrics readiness gauges, publish k8s_namespace_tier.csv and k8s_workload_routing.csv, save uc_3_2_43_k8s_probe_failure_wave every five minutes with earliest=-4h@m latest=now, route critical and high rows per savedsearches.conf, and validate with a lab Deployment whose readiness path is deliberately wrong.

## Evidence

Saved search uc_3_2_43_k8s_probe_failure_wave; lookups k8s_namespace_tier.csv and k8s_workload_routing.csv with version hashes; weekly CSV export of alert rows to a restricted evidence index; dashboard panels tied to the closing table command.

## Control test

### Positive scenario

In namespace qa-probes deploy a Pod whose readinessProbe httpGet path is wrong while the container stays Running, wait for Unhealthy events with readiness probe failed text in index=k8s, run uc_3_2_43_k8s_probe_failure_wave, and expect a qualifying row with unhealthy_event_hits at least two when workload_tier marks the namespace as production in k8s_namespace_tier.csv.

### Negative scenario

Deploy nginx with a correct readiness and liveness probe in the same lab namespace; confirm no sustained Unhealthy probe failure pattern and the saved search yields no qualifying row for that pod across thirty minutes.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the Kubernetes platform site reliability engineers who certify kubelet and kube-state-metrics scrape paths, the observability engineers operating Splunk OpenTelemetry Collector or in-cluster Prometheus, and application owners who approve probe timing on customer-facing workloads. This use case isolates the probe-state axis: the kubelet evaluates startup, readiness, and liveness probes and emits Unhealthy events with explicit probe failure text before the main container necessarily enters CrashLoopBackOff. UC-3.2.10 remains the analytic for kube_pod_container_status_waiting_reason CrashLoopBackOff and exponential restart backoff after the failure has cascaded into the main container restart loop. UC-3.2.30 remains the pre-main-container gate for init container waiting and termination reasons. UC-3.2.41 remains the service-discovery layer where Endpoints or EndpointSlices show zero ready backends; that symptom often follows sustained readiness failure but this UC deliberately fires earlier on kubelet probe evidence so responders tune probes, dependencies, and concurrency before service routing empties. Keeping those boundaries crisp prevents duplicate tickets and preserves analyst trust when multiple monitors light during the same incident.

You need three telemetry families in Splunk before scheduling the alert. First, Kubernetes API events in index k8s with sourcetype kube:events or kube:objects:events where Reason equals Unhealthy and the message text names readiness, liveness, or startup probe failures. Those strings match what kubectl describe surfaces and align with upstream kubelet event generation. Second, Prometheus text lines or normalized metric events in k8s_metrics carrying kubelet-scraped counters: kubelet_probe_failed on Kubernetes 1.27 and newer clusters, and on older kubelets the prober_probe_total series with label result equal to failed. Collect these from the kubelet metrics endpoint or from agents that scrape kubelet /metrics with RBAC that allows node metrics reads. Third, kube-state-metrics gauges for kube_pod_container_status_ready and kube_pod_status_ready with condition true so you can quantify readiness gate flapping as the ready bit transitions across scrapes. Splunk roles must separate platform metrics from application logs under your data classification policy, and HEC tokens require vault storage with quarterly rotation.

Deploy kube-state-metrics with pod and container readiness series enabled. Document how cluster identity lands in the cluster field so joins stay deterministic across Amazon EKS, Google GKE, and Microsoft AKS. Governance lookups mirror other cat-3.2 gold use cases: k8s_namespace_tier.csv lists namespace and workload_tier values such as prod, production, preprod, staging, uat, dev, and sandbox. k8s_workload_routing.csv lists namespace, pod name or documented pattern, owner_workload such as Deployment checkout-api, and on_call_team for paging. Refresh both on every namespace onboarding ticket. Optional extension columns can record recent changes to timeoutSeconds, periodSeconds, or failureThreshold when GitOps auditors want Splunk rows to align with manifest diffs without opening the repository.

CIM alignment uses Application_State for normalized workload or service state overlays where your Technology Add-ons map Kubernetes entities, and Performance for node saturation context when probe timeouts correlate with CPU steal, memory pressure, or disk latency on the underlying VM. Accelerate those data models on the search head when overlays participate in incident review, not only in this alert. Risk framing for executives: probe failure waves are early brownout signals because ingress error rates and coarse replica counts may still look acceptable while the kubelet repeatedly marks containers not ready or kills containers after liveness failure. Customer impact accrues when retries amplify on dependencies or when rolling updates stall behind readiness gates. Compliance reviewers appreciate timestamped evidence that probe discipline was monitored distinctly from post-start crash loops and distinctly from service endpoint bookkeeping.

Licensing and cardinality: kubelet probe counters add cardinality proportional to probe types and container counts; drop experimental labels at scrape time only after security review. Event volume spikes during bad deploys when failureThreshold is low and periodSeconds is aggressive; tune retention per namespace tier. Training narrative for new analysts: teach the ordering of startup versus readiness versus liveness from Kubernetes documentation, teach that HTTP probes return codes matter for readiness while exec probes surface different failure text, and teach that kubectl logs may still show a living process while probes fail on a different port or path.

Differentiation recap relative to siblings: if kube_pod_container_status_waiting_reason shows CrashLoopBackOff for a normal container after init completion, UC-3.2.10 owns that row. If failures reference init container names or kube_pod_init_container metrics dominate, UC-3.2.30 owns first response. If kube_endpoint_address_available is zero while this search shows only mild probe noise, UC-3.2.41 may still deserve a bridge ticket but should not subsume kubelet probe tuning work tracked here.

Partner teams: application owners own probe path and timeout semantics; platform owns scrape reliability and RBAC; identity teams own secret hydration delays that surface as startup probe failures; database teams own backup windows that pause HTTP listeners referenced in known false positives.

Operational risk when collectors drop kubelet scrapes: metric_probe_hits may fall while events continue; keep alert logic dual-arm so Unhealthy events alone cannot be ignored as scraping noise and metrics alone cannot be ignored as event pipeline lag.

### Step 2 — Configure data collection

Scrape kube-state-metrics from the standard ClusterRole-backed Deployment with ServiceMonitor interval thirty seconds and scrapeTimeout ten seconds on path /metrics, matching patterns documented in sibling gold use cases. Network policy should allow only the observability namespace to reach kube-state-metrics. Separately scrape kubelet metrics from each node or use a DaemonSet agent that reads the kubelet summary API and metrics path consistent with your cloud provider guidance, because kubelet_probe_failed and prober_probe_total do not originate from kube-state-metrics. On managed Kubernetes, confirm cloud IAM, workload identity, or bootstrap credentials still allow metric reads after landing-zone changes.

Concrete ServiceMonitor skeleton for kube-state-metrics:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-probe-readiness
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

Ship Kubernetes API events to index k8s with sourcetype kube:events or kube:objects:events. Preserve involvedObject.name, metadata.namespace, reason, and message fields for the multisearch arm. props.conf should set TIME_PREFIX and TIME_FORMAT to Kubernetes RFC3339 timestamps on event firstTimestamp or lastTimestamp so stream ordering matches kubectl. Validate with short searches before alert authoring: index=k8s Unhealthy "probe failed" earliest=-30m, index=k8s_metrics kubelet_probe_failed OR prober_probe_total earliest=-30m, index=k8s_metrics kube_pod_container_status_ready earliest=-30m.

For Google GKE, validate that node pools and autopilot constraints still expose kubelet metrics paths your collector expects. For Amazon EKS, validate security groups and IRSA roles after cluster upgrades. For Azure AKS, validate managed Prometheus or Azure Monitor label mappings if you migrate scrape agents; extend coalesce lists in the SPL after migrations rather than silencing the alert.

Security: redact Secret-derived URLs from event messages at collection when possible. Restrict k8s_audit to security and platform roles when correlating manifest changes to probe timing.

Optional enrichment: maintain a small CSV keyed by namespace, workload, and git commit hash of the last probe timing change so post-incident reviews tie Splunk rows to configuration intent without blaming the wrong team.

Clock skew beyond one minute breaks streamstats ordering on readiness flaps; enforce NTP on forwarders and container hosts.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_43_k8s_probe_failure_wave with schedule every five minutes and dispatch window earliest=-4h@m latest=now to tolerate scrape delay and event batching. Throttle duplicate critical pages per cluster, namespace, and pod for forty-five minutes unless severity escalates from high to critical based on liveness-class events or sustained timeout hints. Create a paging clone that filters severity to critical and high only for production workload tiers, and keep a fleet dashboard clone that retains medium rows for engineering visibility.

Understanding the pipeline: an optional Performance datamodel tstats probe establishes correlation readiness on estates that accelerate Performance summaries. multisearch fans Kubernetes Unhealthy probe events and kubelet probe counter scrapes so Job Inspector traces stay readable. A follow-on join recomputes readiness flapping using kube_pod_container_status_ready and kube_pod_status_ready with streamstats transitions. inputlookup joins add workload tier and paging metadata. case() assigns severity with higher priority for production liveness storms and timeout-class event text.

cimSpl in the JSON field documents an accelerated Application_State and Performance overlay pattern for hosts or mapped workload identities during bridge calls; adapt nodename filters to your Common Information Model implementation.

Fenced SPL for runbooks must match the spl JSON field aside from newline normalization:

```spl
`comment("UC-3.2.43 Kubernetes readiness/liveness/startup probe failure waves at kubelet layer before CrashLoopBackOff. Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics kube:events kube:objects:events; lookups k8s_namespace_tier.csv k8s_workload_routing.csv; earliest=-4h@m latest=now")`
| eval join_key="uc3243"
| join type=left join_key [
    | tstats summariesonly=t count AS perf_correlation_tick FROM datamodel=Performance WHERE nodename=Performance earliest=-4h@h latest=now
    | eval join_key="uc3243" ]
| fields - join_key perf_correlation_tick
| multisearch [
    [ search index=k8s (sourcetype="kube:events" OR sourcetype="kube:objects:events") earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | eval msg_raw=toString(coalesce(message, Message, ""))
      | eval msg=lower(msg_raw)
      | where rs="Unhealthy"
      | where match(msg, "readiness probe failed") OR match(msg, "liveness probe failed") OR match(msg, "startup probe failed")
      | eval probe_class=case(
          match(msg, "readiness probe failed"), "readiness",
          match(msg, "liveness probe failed"), "liveness",
          match(msg, "startup probe failed"), "startup",
          true(), "unknown")
      | eval pod=trim(toString(coalesce(involvedObject.name, involvedObject_name, pod, "")))
      | eval namespace=trim(toString(coalesce(metadata.namespace, namespace, "")))
      | eval container=trim(toString(coalesce(container, containerName, "")))
      | eval container=if(len(container)<1, "_", container)
      | eval signal_lane="kube_event_unhealthy_probe"
      | eval timeout_hint=if(match(msg, "context deadline exceeded") OR match(msg, "i/o timeout") OR match(msg, "timeout"), 1, 0)
      | eval http_5xx_hint=if(match(msg, "statuscode: 5") OR match(msg, "http 5"), 1, 0)
      | fields _time cluster namespace pod container probe_class signal_lane timeout_hint http_5xx_hint msg_raw ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "pod=\"(?<pod_rx>[^\"]+)\""
      | rex field=_raw "container=\"(?<ctr_rx>[^\"]+)\""
      | rex field=_raw "probe_type=\"(?<probe_type_lbl>[^\"]+)\""
      | rex field=_raw "result=\"(?<result_lbl>[^\"]+)\""
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval pod=trim(toString(coalesce(pod, pod_name, k8s_pod, pod_rx, "")))
      | eval container=trim(toString(coalesce(container, container_name, ctr_rx, "")))
      | eval container=if(len(container)<1, "_", container)
      | where (like(mn, "%kubelet_probe_failed%")) OR (like(mn, "%prober_probe_total%") AND result_lbl="failed")
      | eval probe_class=coalesce(nullif(trim(probe_type_lbl),""), "prober_metric")
      | eval signal_lane="kubelet_probe_counter"
      | eval timeout_hint=0
      | eval http_5xx_hint=0
      | eval msg_raw=printf("%s=%s", mn, toString(mval))
      | fields _time cluster namespace pod container probe_class signal_lane timeout_hint http_5xx_hint msg_raw ]
]
| eval cluster=coalesce(nullif(trim(cluster),""), "default-cluster")
| stats count AS lane_rows sum(eval(if(signal_lane="kube_event_unhealthy_probe",1,0))) AS unhealthy_event_hits sum(eval(if(signal_lane="kubelet_probe_counter",1,0))) AS metric_probe_hits max(timeout_hint) AS saw_timeout max(http_5xx_hint) AS saw_http_5xx max(eval(if(signal_lane="kube_event_unhealthy_probe",_time,null()))) AS last_unhealthy_event_time values(probe_class) AS probe_class_mv values(msg_raw) AS evidence_mv BY cluster namespace pod container
| eval evidence_snippet=substr(mvjoin(evidence_mv, " | "), 1, 420)
| join type=left max=0 cluster namespace pod container [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
    | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
    | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
    | rex field=_raw "pod=\"(?<pod>[^\"]+)\""
    | rex field=_raw "container=\"(?<container>[^\"]+)\""
    | rex field=_raw "condition=\"(?<cond>[^\"]+)\""
    | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
    | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
    | eval container=trim(toString(coalesce(container, container_name, "")))
    | eval ready_val=null()
    | eval lane_tag=""
    | where (like(mn, "%kube_pod_container_status_ready%") AND cond="true") OR (like(mn, "%kube_pod_status_ready%") AND cond="true")
    | eval lane_tag=if(like(mn, "%kube_pod_container_status_ready%"), "container_ready", "pod_ready")
    | eval container=if(lane_tag="pod_ready" AND len(container)<1, "_pod_", container)
    | eval container=if(len(container)<1, "_", container)
    | eval ready_val=if(tonumber(mval,10)>0,1,0)
    | sort 0 cluster namespace pod container _time
    | streamstats current=f last(ready_val) AS prev_ready BY cluster namespace pod container
    | eval flip=if(isnotnull(prev_ready) AND prev_ready!=ready_val,1,0)
    | stats sum(flip) AS readiness_flips BY cluster namespace pod container ]
| fillnull value=0 readiness_flips
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
| eval probe_class_primary=coalesce(mvindex(probe_class_mv,0), "mixed")
| eval severity=case(
    (workload_tier="prod" OR workload_tier="production") AND probe_class_primary="liveness" AND unhealthy_event_hits>=3, "critical",
    (workload_tier="prod" OR workload_tier="production") AND saw_timeout=1 AND unhealthy_event_hits>=2, "critical",
    (workload_tier="prod" OR workload_tier="production") AND unhealthy_event_hits>=4, "high",
    (workload_tier="prod" OR workload_tier="production") AND metric_probe_hits>=8, "high",
    match(workload_tier, "preprod|staging|uat") AND unhealthy_event_hits>=3, "high",
    readiness_flips>=6, "high",
    unhealthy_event_hits>=2, "medium",
    metric_probe_hits>=4, "medium",
    readiness_flips>=4, "medium",
    true(), "low")
| where match(severity, "critical|high|medium|low")
| where unhealthy_event_hits>=2 OR metric_probe_hits>=3 OR readiness_flips>=4 OR (unhealthy_event_hits>=1 AND metric_probe_hits>=1)
| table cluster namespace pod container probe_class_primary severity unhealthy_event_hits metric_probe_hits readiness_flips saw_timeout saw_http_5xx last_unhealthy_event_time workload_tier owner_workload on_call_team evidence_snippet
```

Example savedsearches.conf fragment:

```
[uc_3_2_43_k8s_probe_failure_wave]
action.email = 1
action.email.to = platform-oncall@example.com
action.email.subject = K8s probe wave $result.namespace$/$result.pod$/$result.container$
action.email.message = severity=$result.severity$ probe=$result.probe_class_primary$ ev=$result.unhealthy_event_hits$ metrics=$result.metric_probe_hits$ flips=$result.readiness_flips$ snippet=$result.evidence_snippet$
cron_schedule = */5 * * * *
dispatch.earliest_time = -4h@m
dispatch.latest_time = now
counttype = number of events
relation = >
quantity = 0
alert.track = 1
alert.suppress = 1
alert.suppress.period = 45m
```

Wire ITSI notable parameters to your deployment naming when episodes should bind cluster, namespace, pod, and container entities for customer-facing services.

Performance: if join costs grow, summarize kubelet probe counters and Unhealthy events into five-minute metrics indexes keyed on cluster, namespace, pod, and container before alerting while retaining raw scrapes for ad-hoc rex tuning after kubelet upgrades.

### Step 4 — Validate

Synthetic readiness failure: in a lab namespace deploy an nginx Deployment with readinessProbe httpGet path /ready on port eighty while the server only serves /, wait for Unhealthy events with readiness probe failed text, confirm k8s_metrics shows kube_pod_container_status_ready toggling if the probe oscillates, run uc_3_2_43_k8s_probe_failure_wave, and expect a qualifying row with unhealthy_event_hits at least two when the workload tier lookup marks the namespace as production. Tear down by fixing the probe path and confirm the next interval drops the row.

Synthetic liveness failure: configure a livenessProbe that targets a blocked port or returns 500 while the process stays alive; confirm Unhealthy mentions liveness probe failed and severity respects the liveness-heavy branch for production tiers. Negative control: a healthy Deployment with generous timeoutSeconds and stable dependencies should not produce sustained unhealthy_event_hits across thirty minutes.

Metric path validation: on a 1.26 cluster confirm prober_probe_total result failed appears in Splunk when kubelet_probe_failed is absent; on 1.27 or newer confirm kubelet_probe_failed increments during deliberate probe failure drills. kubectl describe pod should narrate the same probe class as Splunk evidence_snippet.

Audit correlation: index=k8s_audit sourcetype=kube:audit verb=patch objectRef.resource=deployments earliest=-2h with objectRef.namespace matching the failing workload to recover the principal that changed probe fields.

Field sanity: compare Splunk-extracted namespace and pod with kubectl get pod -n and ensure cluster label matches your CMDB cluster id. Skew between metrics and events should remain under ninety seconds for meaningful flapping math.

Replay hygiene: after kube-state-metrics upgrades, verify kube_pod_status_ready label shapes still match rex arms; after kubelet upgrades, verify Unhealthy message strings remain compatible with match filters.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Readiness probe fails on dependency outage while the process stays up
Correlate application logs for downstream timeouts, validate Service DNS and NetworkPolicy paths, temporarily widen timeoutSeconds only with owner approval, and restore dependency health before closing.

Case 2 — Liveness probe too aggressive during JVM garbage-collection pauses
Brief probe failures during stop-the-world events can precede restarts; compare node CPU steal and cgroup pressure, tune periodSeconds and failureThreshold, and pair with UC-3.2.10 only if waiting_reason becomes CrashLoopBackOff.

Case 3 — Startup probe still running while readiness is evaluated too early
Separate startupProbe from readinessProbe per Kubernetes guidance, raise startupProbe.failureThreshold for slow-start services, and document warm-up SLO minutes in the workload catalog.

Case 4 — HTTP readiness returns 503 during intentional graceful shutdown
SIGTERM-aware apps may return failed on health endpoints by design; coordinate drain labels with ingress controllers and annotate maintenance windows in lookups rather than muting kubelet evidence globally.

Case 5 — Recently patched timeoutSeconds causing flap after GitOps merge
Diff deployment manifests against alert timestamps, revert or split canary namespaces, and attach audit user from kube_audit to the incident record.

Case 6 — Startup probe failure during Vault Agent post-unseal checks
Identity platform delays can block health files; pair Splunk rows with Vault cluster health before blaming application teams, and route to identity on-call when messages mention secret or token paths.

Case 7 — Database backup window pauses health endpoints
Maintenance procedures that deliberately freeze HTTP listeners should carry scheduled suppression rows in k8s_workload_routing.csv notes or parallel maintenance calendars.

Case 8 — .NET JIT compilation first-request latency fails HTTP probes
Warm-up endpoints or increase startupProbe initialDelaySeconds; compare cold-start metrics with probe timestamps before reopening sev-one bridges.

Case 9 — Feature flag toggles dependency checks that flap readiness
Align feature flag change logs with Splunk rows; stabilize probe dependencies or decouple readiness from experimental code paths.

Case 10 — Exec probe binary missing after image slimming
Describe events may mention executable not found; rebuild images or fix command paths, then confirm kubelet counters quiet across three scrapes.

Case 11 — GKE or EKS node image upgrade shifts kubelet metric labels
Replay one hour of metrics after upgrades; update rex arms when Prometheus relabel configs rename namespace or pod labels.

Case 12 — AKS managed Prometheus migration duplicates scrape streams
Deduplicate by source or host before trusting metric_probe_hits thresholds; keep a single authoritative scrape path per node class.

Dashboard hygiene: keep panels for Unhealthy probe counts by namespace, kubelet_probe_failed rate by probe_type, and readiness flips from kube_pod_container_status_ready. Document kubectl get events --field-selector involvedObject.name workflows for teams permitted to run kubectl under change control.

Governance: quarterly replay a historical probe incident through the SPL after kubelet minor upgrades because message text occasionally shifts. Evidence pack: weekly CSV export of alert rows with kube-state-metrics chart version, collector digest, and lookup commit hash so auditors replay dwell math without guessing which label shape was live.

FinOps note: aggressive probes increase kubelet work and log volume; attach scrape cadence decisions to license review decks when finance questions observability cost.

Training: teach on-call staff that evidence_snippet may truncate long messages; use drilldown searches for full message text when legal holds require verbatim copies.

Escalation: when severity is critical for liveness-class rows, engage the service owner and platform jointly because kubelet kills may begin before ingress dashboards move.

Closing checklist: five step headers use em dash punctuation as contracted; Step 3 contains fenced SPL matching the spl JSON field; Step 5 lists twelve case lines; monitoringType includes Reliability and Availability; equipmentModels includes kubernetes_k8s; exclusions explicitly separate UC-3.2.10, UC-3.2.30, and UC-3.2.41; narrative avoids claiming this replaces ingress-only analytics.

Appendix — Probe timing change forensics
When GitOps stores Deployment manifests, correlate alert _time to merge timestamps and image tags. Capture timeoutSeconds, periodSeconds, successThreshold, and failureThreshold in a change ticket appendix so reviewers know whether flap came from application regression or configuration drift.

Appendix — Dual-stack clusters
If kube_pod_status_ready splits across address families, confirm clients use the same family your probes exercise; IPv6-only listeners with IPv4 probes mimic outage patterns unrelated to dependency health.

Appendix — Service mesh sidecars
Sidecars can answer health checks on admin ports while application containers fail readiness; kubectl describe and container name hints in events should guide whether to tune app container probes versus mesh bootstrap readiness.

Appendix — Summary indexing option
Materialize five-minute rollups of unhealthy_event_hits and readiness_flips per cluster namespace pod container when raw k8s index volume stresses Job Inspector, while keeping raw events for compliance holds.

Appendix — Evidence signing posture
When auditors require non-repudiation, archive alert CSV snapshots to an evidence index with restricted roles and document retention alongside lookup versions referenced in the alert body.

Appendix — Node not-ready interaction
If nodes transition NotReady, probes may fail without application defects; correlate with node conditions and cloud provider maintenance before paging application owners.

Appendix — Collector failure drills
Simulate HEC outage to confirm alerts do not page on stale zero-metrics alone when dual-arm thresholds are tuned; document expected behavior in the runbook.

Appendix — Language-runtime specifics
Ruby and Python apps may spike CPU during boot; pair startupProbe budgets with language-specific boot profilers when owners dispute probe fairness.

Appendix — Ingress correlation without conflating UC-3.2.41
Ingress 502 and 503 panels may lag probe failures; use this UC as the upstream signal and UC-3.2.41 only when endpoint readiness aggregates show zero backends.

Appendix — Windows node caveats
Windows kubelet event text may differ; fork SPL match clauses only after collecting representative Unhealthy messages from Windows labs.

Appendix — Quarterly review agenda
Review severity case thresholds, namespace tier coverage, routing lookup freshness, and kubelet minor version notes from Kubernetes release changelogs affecting probe metrics.

Appendix — Customer communication
When incidents touch customer-visible services, attach probe_class_primary and evidence_snippet excerpts to status page updates without leaking secret material from messages.

Appendix — Synthetic monitoring complement
External synthetics may stay green while internal probes fail; teach stakeholders that this UC is kubelet-authoritative and complements but does not replace edge synthetics.

Appendix — Cost of silence
Document one historical brownout where probe waves preceded endpoint drain to justify continued license spend on kubelet scrapes.

Appendix — Runbook link hygiene
Deep link saved searches and dashboard tokens for namespace and pod to reduce copy-paste errors during incidents.

Appendix — Post-incident template
Require answers for probe path correctness, dependency SLO, timeout budget, failureThreshold rationale, and whether startupProbe covered warm-up before closing root cause.

Appendix — Multi-cluster federation
Normalize cluster names across fleets so joins from k8s_workload_routing.csv remain injective; duplicate rows per cluster when workload names collide.

Appendix — Autopilot and security profiles
Restricted security profiles may block exec probes; validate probe type choices against platform policy before blaming applications.

Appendix — Final differentiation restatement
CrashLoopBackOff analytics remain UC-3.2.10, init gates remain UC-3.2.30, service endpoint books remain UC-3.2.41; this UC owns kubelet probe waves beforehand.


## SPL

```spl
`comment("UC-3.2.43 Kubernetes readiness/liveness/startup probe failure waves at kubelet layer before CrashLoopBackOff. Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics kube:events kube:objects:events; lookups k8s_namespace_tier.csv k8s_workload_routing.csv; earliest=-4h@m latest=now")`
| eval join_key="uc3243"
| join type=left join_key [
    | tstats summariesonly=t count AS perf_correlation_tick FROM datamodel=Performance WHERE nodename=Performance earliest=-4h@h latest=now
    | eval join_key="uc3243" ]
| fields - join_key perf_correlation_tick
| multisearch [
    [ search index=k8s (sourcetype="kube:events" OR sourcetype="kube:objects:events") earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | eval msg_raw=toString(coalesce(message, Message, ""))
      | eval msg=lower(msg_raw)
      | where rs="Unhealthy"
      | where match(msg, "readiness probe failed") OR match(msg, "liveness probe failed") OR match(msg, "startup probe failed")
      | eval probe_class=case(
          match(msg, "readiness probe failed"), "readiness",
          match(msg, "liveness probe failed"), "liveness",
          match(msg, "startup probe failed"), "startup",
          true(), "unknown")
      | eval pod=trim(toString(coalesce(involvedObject.name, involvedObject_name, pod, "")))
      | eval namespace=trim(toString(coalesce(metadata.namespace, namespace, "")))
      | eval container=trim(toString(coalesce(container, containerName, "")))
      | eval container=if(len(container)<1, "_", container)
      | eval signal_lane="kube_event_unhealthy_probe"
      | eval timeout_hint=if(match(msg, "context deadline exceeded") OR match(msg, "i/o timeout") OR match(msg, "timeout"), 1, 0)
      | eval http_5xx_hint=if(match(msg, "statuscode: 5") OR match(msg, "http 5"), 1, 0)
      | fields _time cluster namespace pod container probe_class signal_lane timeout_hint http_5xx_hint msg_raw ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "pod=\"(?<pod_rx>[^\"]+)\""
      | rex field=_raw "container=\"(?<ctr_rx>[^\"]+)\""
      | rex field=_raw "probe_type=\"(?<probe_type_lbl>[^\"]+)\""
      | rex field=_raw "result=\"(?<result_lbl>[^\"]+)\""
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval pod=trim(toString(coalesce(pod, pod_name, k8s_pod, pod_rx, "")))
      | eval container=trim(toString(coalesce(container, container_name, ctr_rx, "")))
      | eval container=if(len(container)<1, "_", container)
      | where (like(mn, "%kubelet_probe_failed%")) OR (like(mn, "%prober_probe_total%") AND result_lbl="failed")
      | eval probe_class=coalesce(nullif(trim(probe_type_lbl),""), "prober_metric")
      | eval signal_lane="kubelet_probe_counter"
      | eval timeout_hint=0
      | eval http_5xx_hint=0
      | eval msg_raw=printf("%s=%s", mn, toString(mval))
      | fields _time cluster namespace pod container probe_class signal_lane timeout_hint http_5xx_hint msg_raw ]
]
| eval cluster=coalesce(nullif(trim(cluster),""), "default-cluster")
| stats count AS lane_rows sum(eval(if(signal_lane="kube_event_unhealthy_probe",1,0))) AS unhealthy_event_hits sum(eval(if(signal_lane="kubelet_probe_counter",1,0))) AS metric_probe_hits max(timeout_hint) AS saw_timeout max(http_5xx_hint) AS saw_http_5xx max(eval(if(signal_lane="kube_event_unhealthy_probe",_time,null()))) AS last_unhealthy_event_time values(probe_class) AS probe_class_mv values(msg_raw) AS evidence_mv BY cluster namespace pod container
| eval evidence_snippet=substr(mvjoin(evidence_mv, " | "), 1, 420)
| join type=left max=0 cluster namespace pod container [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
    | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
    | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
    | rex field=_raw "pod=\"(?<pod>[^\"]+)\""
    | rex field=_raw "container=\"(?<container>[^\"]+)\""
    | rex field=_raw "condition=\"(?<cond>[^\"]+)\""
    | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
    | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
    | eval container=trim(toString(coalesce(container, container_name, "")))
    | eval ready_val=null()
    | eval lane_tag=""
    | where (like(mn, "%kube_pod_container_status_ready%") AND cond="true") OR (like(mn, "%kube_pod_status_ready%") AND cond="true")
    | eval lane_tag=if(like(mn, "%kube_pod_container_status_ready%"), "container_ready", "pod_ready")
    | eval container=if(lane_tag="pod_ready" AND len(container)<1, "_pod_", container)
    | eval container=if(len(container)<1, "_", container)
    | eval ready_val=if(tonumber(mval,10)>0,1,0)
    | sort 0 cluster namespace pod container _time
    | streamstats current=f last(ready_val) AS prev_ready BY cluster namespace pod container
    | eval flip=if(isnotnull(prev_ready) AND prev_ready!=ready_val,1,0)
    | stats sum(flip) AS readiness_flips BY cluster namespace pod container ]
| fillnull value=0 readiness_flips
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
| eval probe_class_primary=coalesce(mvindex(probe_class_mv,0), "mixed")
| eval severity=case(
    (workload_tier="prod" OR workload_tier="production") AND probe_class_primary="liveness" AND unhealthy_event_hits>=3, "critical",
    (workload_tier="prod" OR workload_tier="production") AND saw_timeout=1 AND unhealthy_event_hits>=2, "critical",
    (workload_tier="prod" OR workload_tier="production") AND unhealthy_event_hits>=4, "high",
    (workload_tier="prod" OR workload_tier="production") AND metric_probe_hits>=8, "high",
    match(workload_tier, "preprod|staging|uat") AND unhealthy_event_hits>=3, "high",
    readiness_flips>=6, "high",
    unhealthy_event_hits>=2, "medium",
    metric_probe_hits>=4, "medium",
    readiness_flips>=4, "medium",
    true(), "low")
| where match(severity, "critical|high|medium|low")
| where unhealthy_event_hits>=2 OR metric_probe_hits>=3 OR readiness_flips>=4 OR (unhealthy_event_hits>=1 AND metric_probe_hits>=1)
| table cluster namespace pod container probe_class_primary severity unhealthy_event_hits metric_probe_hits readiness_flips saw_timeout saw_http_5xx last_unhealthy_event_time workload_tier owner_workload on_call_team evidence_snippet
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state count AS app_ticks FROM datamodel=Application_State WHERE nodename=Application_State earliest=-4h@h latest=@h BY Application_State.dest Application_State.app
| rename Application_State.dest AS correl_host
| join type=left max=0 correl_host [
| tstats summariesonly=t avg(Performance.cpu_load_percent) AS avg_cpu_load avg(Performance.mem_used_percent) AS avg_mem_used FROM datamodel=Performance WHERE nodename=Performance.CPU OR nodename=Performance.Memory earliest=-4h@h latest=@h BY Performance.host
| rename Performance.host AS correl_host ]
| where app_state!="running" OR avg_cpu_load>90 OR avg_mem_used>92
| table correl_host app_state avg_cpu_load avg_mem_used app_ticks
```

## Visualization

Primary table mirroring the closing SPL projection; timechart of unhealthy_event_hits by namespace; overlay of readiness_flips; single value of distinct pods with liveness-class events; drilldown to kube events and container logs for the same pod and minute.

## Known False Positives

Brief readiness failures during heavy JVM garbage-collection pauses are common when stop-the-world events exceed probe timeouts; widen thresholds or tune garbage-collection ergonomics before paging production. Intentional graceful-shutdown paths may return failed for readiness or liveness while SIGTERM handlers drain connections; pair Splunk rows with maintenance annotations rather than treating every row as a defect. Slow-start applications during Vault post-unseal or secret hydration windows can fail startup probes until identity platforms stabilize; route identity on-call when messages reference unseal or token semantics. Database backup jobs that pause HTTP listeners on purpose resemble outages; require maintenance calendar correlation. .NET just-in-time compilation and first-request warm-up can fail HTTP probes on cold pods; use startupProbe budgets or warm-up sidecars. Feature-flag flips that change dependency health checks may flap readiness without infrastructure failure; compare flag change logs to alert timestamps. Scheduled maintenance that deliberately returns 503 on health endpoints should carry suppression metadata in routing lookups. Blue-green or canary cuts can generate short probe failure bursts; require sustained dwell or combine event and kubelet counter arms before sev-one pages. Test clusters running chaos experiments on probes will flood the search; keep workload_tier dev defaults in k8s_namespace_tier.csv so severity stays low unless promoted namespaces override.

## References

- [Kubernetes — Configure liveness, readiness, and startup probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Kubernetes — Pod lifecycle: container probes](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes)
- [Kubernetes — Metrics for Kubernetes system components](https://kubernetes.io/docs/reference/instrumentation/metrics/)
- [Google Kubernetes Engine — Troubleshooting](https://cloud.google.com/kubernetes-engine/docs/troubleshooting)
- [Amazon EKS — Troubleshooting](https://docs.aws.amazon.com/eks/latest/userguide/troubleshooting.html)
- [Azure Kubernetes Service — Troubleshooting](https://learn.microsoft.com/en-us/azure/aks/troubleshooting)
- [Datadog — Kubernetes monitoring documentation](https://docs.datadoghq.com/containers/kubernetes/)
- [Splunk Docs — Splunk Add-on for Kubernetes](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
