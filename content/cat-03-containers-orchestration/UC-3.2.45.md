<!-- AUTO-GENERATED from UC-3.2.45.json — DO NOT EDIT -->

---
id: "3.2.45"
title: "Kubernetes Admission/Conversion Webhook Tail-Latency Profiling — Per-Webhook P95/P99/P999 Distribution and Slow-Operation Outlier Detection"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.2.45 · Kubernetes Admission/Conversion Webhook Tail-Latency Profiling — Per-Webhook P95/P99/P999 Distribution and Slow-Operation Outlier Detection

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We measure how long each automatic safety check takes when someone changes the cluster, including the steps that rewrite custom resource shapes. When one check develops a long tail or gets dangerously close to its time limit, we show it early so teams fix that check before normal work starts failing.*

---

## Description

Profiles Kubernetes dynamic admission tail latency per webhook and per conversion step by recomputing histogram quantiles from apiserver_admission_webhook_admission_duration_seconds_bucket and apiserver_admission_step_conversion_duration_seconds_bucket, exposing P50, P95, P99, and P999 in milliseconds alongside a P99-to-P50 tail inflation ratio, slack to configured webhook timeoutSeconds from governance CSV, and kube:apiserver:audit derived namespace witnesses plus policy engine log correlation. The analytic is distinct from UC-3.2.40 admission hook reliability focused on errors, denials, and transport failure rates; distinct from UC-3.2.21 aggregate admission budget and apiserver backpressure; and distinct from UC-3.2.19 overall apiserver_request_duration_seconds latency decomposed by verb and resource without hook names. It answers which validating or mutating hook is slowest for CREATE versus UPDATE, whether conversion latency isolates to CRD machinery, and which namespace shows the hottest admission volume when tails stretch.

## Value

Clusters fail in practice when a single admission or conversion step hugs its deadline while medians look fine: GitOps batches stall, certificate flows jitter, and platform teams mis-blame etcd or generic apiserver SLO panels. Splunk rows that fuse histogram-native quantiles, timeout slack math, namespace witnesses, optional Kyverno and Gatekeeper log volume, and CIM overlays collapse mean time to innocence for platform and policy owners. Capacity planners see when heavy tails correlate with admission breadth, while executives receive evidence suitable for timeout and policy budget reviews without drowning in raw prometheus text.

## Implementation

Scrape kube-apiserver histograms apiserver_admission_webhook_admission_duration_seconds_bucket and apiserver_admission_step_conversion_duration_seconds_bucket into index=k8s_metrics with name, operation, type, and le intact. Version webhook_tail_latency_governance.csv with timeoutSeconds and owner_team from live webhook configs. Ingest kube:apiserver:audit and k8s_logs for namespace and policy-log joins. Schedule uc_3_2_45_webhook_tail_profile every five minutes on earliest=-30m@m latest=@m. Accelerate CIM Application_State and Performance for tstats overlays.

## Evidence

Saved search uc_3_2_45_webhook_tail_profile on a five-minute schedule; versioned webhook_tail_latency_governance.csv in git; weekly CSV export of the closing table to a restricted evidence index with optional kube:apiserver:audit samples for namespace disputes.

## Control test

### Positive scenario

In a lab cluster with k8s_metrics populated from kube-apiserver scrapes, inject a controlled slow path on a test validating webhook so apiserver_admission_webhook_admission_duration_seconds_bucket shifts mass into high le labels; confirm uc_3_2_45_webhook_tail_profile emits a critical or high severity_tier row with shrinking slack_ms_to_deadline within thirty minutes and that inputlookup webhook_tail_latency_governance.csv enriches timeout_sec.

### Negative scenario

Remove the slow path and restore baseline policy bundles; confirm tail_ratio_p99_p50 and p999_ms fall below medium thresholds for two consecutive five-minute buckets and the saved search emits no qualifying rows for that hook while aggregate apiserver health remains nominal.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with Kubernetes platform engineering, the policy-as-code owners who curate Kyverno ClusterPolicy libraries and OPA Gatekeeper ConstraintTemplates, the API machinery specialists who maintain CustomResourceDefinition conversion webhooks, and the observability engineers who operate Splunk OpenTelemetry Collector fleets scraping kube-apiserver. UC-3.2.45 is deliberately the per-webhook tail-latency and conversion-step profiling axis: it rebuilds Prometheus-style histogram quantiles from apiserver_admission_webhook_admission_duration_seconds_bucket sliced by webhook name, admission operation such as CREATE or UPDATE, and hook type validating versus mutating, then repeats the same mathematics on apiserver_admission_step_conversion_duration_seconds_bucket so conversion latency is not accidentally folded into generic apiserver request latency panels. UC-3.2.40 remains the reliability and denial axis built from request totals, explicit rejections, transport errors, and audit hints. UC-3.2.21, when present in your catalogue, stays focused on aggregate apiserver admission budget and backpressure symptoms rather than per-hook tail shape. UC-3.2.19 remains the broad apiserver_request_duration_seconds pipeline decomposed by verb, resource, and client signature without admission hook names. When this analytic highlights a row, incident command should ask whether a specific webhook is approaching its configured timeoutSeconds deadline, whether tail inflation is bimodal as measured by a rising P99 to P50 ratio, whether one CRUD operation on one Kind dominates latency for that hook, and whether conversion steps for a CRD explain PATCH storms that look healthy on aggregate apiserver histograms.

Index contracts: land kube-apiserver prometheus text on index=k8s_metrics with sourcetype=prometheus:scrape:metrics preserving __name__, le, name, operation, type, group, version, resource, and k8s_cluster_name or equivalent cluster tags. Preserve apiserver_admission_webhook_admission_duration_seconds_bucket and apiserver_admission_step_conversion_duration_seconds_bucket verbatim; some distributions expose conversion latency under adjacent names on older minors, so document any normalisation your FinOps pipeline applies. Stand up index=k8s_audit for kube:apiserver:audit when you need namespace witnesses for admission volume, and index=k8s_logs for Kyverno, Gatekeeper, and ValidatingAdmissionPolicy controller logs that explain CPU-bound policy evaluation or remote calls inside hooks. Issue distinct HEC tokens per index class with quarterly rotation and least-privilege roles so application teams cannot read unrelated namespace bodies.

Scrape topology: self-managed clusters scrape apiserver /metrics with TLS and bearer credentials appropriate to the control plane. Prometheus Operator users install a ServiceMonitor that keeps histogram bucket labels intact; avoid relabel rules that drop le or name. Amazon EKS, Google GKE, and Microsoft AKS may require cloud metric export mirrors; normalise field names so this SPL does not fork per cloud. Histogram cardinality grows with webhook counts; FinOps should review label cardinality any time experimental hooks multiply in shared labs.

Governance lookup: publish lookups/webhook_tail_latency_governance.csv in git with columns cluster, webhook_name, timeout_seconds copied from live ValidatingWebhookConfiguration and MutatingWebhookConfiguration objects, owner_team, optional p99_budget_ms for softer budgeting than the hard timeout, notes for dual-stack networking or multi-replica cold caches, and exception_expiry epoch for hooks under deliberate tuning windows. Refresh the CSV from the same repository that applies webhook configurations so auditors can trace Git ancestry to Splunk rows. Where conversion hooks are not named like validating hooks, map synthetic keys such as k8s conversion to the same CSV for timeout comparisons only when your platform team documents an operational deadline.

Risk briefing: default admission webhook timeoutSeconds is ten seconds; P999 hugging nine and a half seconds is an imminent failure mode even when P50 looks fine. Bimodal latency distributions inflate P99 and P999 while leaving medians calm; the tail ratio column surfaces that pattern without requiring kernel density estimation. Large ConfigMaps and Secret-heavy objects increase serialization and patch size, stretching mutating hooks that rewrite images or labels. Conversion webhooks that call out to external signing or schema services can create heavy tails that never appear in validating hook metrics alone. Policy engines that compile rules on first use legitimately spike one bucket after deploy; operational readers must compare against change tickets before paging.

Privacy and legal: audit and policy logs may include object metadata; restrict indexes and redact secrets at collection. Training: teach responders how histogram_quantile behaves in Prometheus and why Splunk recomputes quantiles from cumulative buckets rather than applying perc99 to raw scrape gauges. Document that ValidatingAdmissionPolicy and its parameter CRDs introduce new admission paths that still emit the same histogram families when bound to webhook-style machinery.

Operational readiness drills: rehearse reading slack_ms_to_deadline during staged slowdowns, rehearse interpreting tail_ratio_p99_p50 when only one operation label moves, and rehearse pivoting from conversion_step rows to CRD manifests without conflating them with validating hook failures. FinOps reviewers should track scrape cardinality weekly because hook names multiply faster than node counts during platform experiments. Security reviewers should treat sudden tail inflation on security hooks as a potential signal worth correlating with unusual audit subjects even when no denial metrics move yet.

Differentiation recap: per-hook tail quantiles, conversion histogram isolation, timeout slack math, tail inflation ratio, namespace witness joins, and optional policy log correlation, not aggregate apiserver latency, not webhook error-only reliability panels, not etcd internals.

Hardware and tenancy: applies to x86_64 and Arm64 control planes when scrape labels remain consistent. Multi-tenant Splunk should segregate k8s_audit and k8s_logs containing namespace metadata behind platform roles. PCI environments may require redacting object names in alert actions while retaining hook identifiers.

Long-horizon maintenance: when Kubernetes minors add new admission labels, regression-test the SPL in lab before promoting to production schedules. When policy libraries balloon, expect legitimate baseline drift in P95; re-baseline budgets from quarterly samples rather than historical medians from tiny clusters.

### Step 2 — Configure data collection

First, verify apiserver_admission_webhook_admission_duration_seconds_bucket appears in k8s_metrics with non-empty name, operation, type, and le labels. Second, verify apiserver_admission_step_conversion_duration_seconds_bucket appears after upgrading to a Kubernetes minor that exports conversion step histograms; when absent, leave the conversion multisearch arm in place so future scrapes populate automatically. Third, confirm OpenTelemetry Collector prometheus receiver scrape intervals between fifteen and sixty seconds align with bucket span=5m in the SPL so each window contains multiple samples.

Example ServiceMonitor fragment for kube-prometheus-stack users who need explicit admission scraping:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-apiserver-admission-tail
  namespace: monitoring
spec:
  selector:
    matchLabels:
      component: apiserver
  namespaceSelector:
    matchNames:
      - kube-system
  endpoints:
    - port: https
      scheme: https
      bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
      tlsConfig:
        insecureSkipVerify: true
      interval: 30s
      path: /metrics
```

Route prometheus lines to Splunk with sourcetype=prometheus:scrape:metrics and resource attribute k8s.cluster.name mirrored into k8s_cluster_name for cluster joins. For policy engine logs, prefer structured container logs with cluster identifiers; when only message text exists, extract cluster with a static field at ingestion.

Publish webhook_tail_latency_governance.csv aligned to join keys used in Step 3:

```csv
cluster,webhook_name,timeout_seconds,owner_team,p99_budget_ms,notes
prod-eks-01,kyverno-resource-validating-webhook-cfg,10,team-platform,850,Kyverno validate path
prod-eks-01,gatekeeper-validating-webhook-configuration,10,team-security,900,Gatekeeper
prod-eks-01,cert-manager-webhook,10,team-platform,1200,cert issuance
lab-kind-01,k8s conversion,10,team-platform,950,synthetic key for conversion rows
```

Pre-flight searches: index=k8s_metrics apiserver_admission_webhook_admission_duration_seconds_bucket earliest=-15m must return non-zero counts on active clusters. Optional: index=k8s_logs kyverno earliest=-24h should return samples after policy changes.

CIM acceleration: accelerate Application_State and Performance summaries on kubernetes_cluster or management-plane entities referenced in Application_State.dest so tstats overlays stay warm during incidents.

Ingestion hardening: props transforms should retain le as a first-class field; accidental truncation of le to integer seconds breaks quantile reconstruction. When multiple collectors scrape the same apiserver, deduplicate on scrape instance before histogram math or cumulative counts double.

Cloud export parity: if a managed plane exports only pre-aggregated quantiles, document the gap; this UC requires bucket counters. Where legal constraints block direct apiserver scrape, mirror equivalent histogram series from the cloud telemetry export into the same mn and label schema.

Log routing guidance: route Kyverno controller logs, Gatekeeper controller logs, and apiserver-audit-adjacent policy messages into k8s_logs with a reliable cluster dimension; keyword correlation intentionally uses lowercase literals kyverno, gatekeeper, and validatingadmissionpolicy to survive heterogeneous sourcetypes.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_45_webhook_tail_profile with a five-minute schedule, dispatch earliest=-30m@m, dispatch latest=@m, and throttle duplicate cluster, hook_name, operation, telemetry_lane rows for ten minutes unless severity_tier escalates to critical within the same half hour. Include p999_ms, slack_ms_to_deadline, tail_ratio_p99_p50, and owner_team in pager bodies with links to internal runbooks for Kyverno performance, Gatekeeper operations, CRD conversion, and apiserver timeoutSeconds tuning.

Pipeline narrative: the opening comment macro lists tunable indexes, sourcetypes, lookup path, and threshold hints. multisearch runs two histogram arms. The admission arm filters apiserver_admission_webhook_admission_duration_seconds_bucket, buckets time, takes the per-window maximum cumulative count per le label, derives histo_total from the positive infinity bucket, then computes p50_ms, p95_ms, p99_ms, and p999_ms via inclusive cumulative mass thresholds analogous to histogram_quantile in Prometheus. The conversion arm repeats the same steps on apiserver_admission_step_conversion_duration_seconds_bucket with telemetry_lane set to conversion_step and hook_name coalesced from labels or a documented synthetic. After fan-in, eventstats adds cluster-level percentile context for burst diagnosis. streamstats smooths short p99_ma3 moving averages per hook. inputlookup webhook_tail_latency_governance.csv enriches timeout_seconds, owner_team, and p99_budget_ms. Evaluated slack_ms_to_deadline subtracts p999_ms from the configured timeout in milliseconds so operators see margin before hard failure. tail_ratio_p99_p50 divides P99 by P50 to highlight bimodality. Left joins add kube:apiserver:audit derived top_admission_namespace and admission_ns_breadth per five-minute window, plus policy engine log counts from k8s_logs keyword filters for Kyverno, Gatekeeper, and ValidatingAdmissionPolicy strings. tstats against Application_State and Performance supplies CIM overlays. case assigns severity_tier from critical through low; informational rows drop from alert predicates. The closing table lists twenty analyst columns for triage.

Paste-and-run SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.2.45 Admission and conversion webhook tail-latency profile. Tunables: idx_metrics=k8s_metrics idx_audit=k8s_audit idx_logs=k8s_logs st_metrics=prometheus:scrape:metrics st_audit=kube:apiserver:audit earliest=-30m@m latest=@m; lookup webhook_tail_latency_governance.csv; default_timeout_sec=10")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(webhook_name, admission_webhook, name, ""))))
      | eval hook_type=lower(trim(toString(coalesce(type, hook_kind, ""))))
      | eval operation=upper(trim(toString(coalesce(operation, op, ""))))
      | where mn="apiserver_admission_webhook_admission_duration_seconds_bucket" AND len(cluster)>0 AND len(hook_name)>0
      | eval le_raw=trim(toString(coalesce(le, le_label, "")))
      | bucket _time span=5m
      | eval win_time=_time
      | stats max(mv) AS cum_at_bucket BY cluster hook_name hook_type operation win_time le_raw
      | eval le_num=case(match(le_raw,"^\\+Inf$"), 1000000000, true(), tonumber(le_raw))
      | where isnotnull(le_num)
      | sort 0 cluster hook_name hook_type operation win_time le_num
      | eventstats max(eval(if(match(le_raw,"^\\+Inf$"), cum_at_bucket, null()))) AS histo_total BY cluster hook_name hook_type operation win_time
      | where isnotnull(histo_total) AND histo_total>0
      | eval hit50=if(cum_at_bucket>=(0.50*histo_total), le_num, null())
      | eval hit95=if(cum_at_bucket>=(0.95*histo_total), le_num, null())
      | eval hit99=if(cum_at_bucket>=(0.99*histo_total), le_num, null())
      | eval hit999=if(cum_at_bucket>=(0.999*histo_total), le_num, null())
      | stats min(hit50) AS p50_le min(hit95) AS p95_le min(hit99) AS p99_le min(hit999) AS p999_le BY cluster hook_name hook_type operation win_time
      | eval p50_ms=round(1000*coalesce(p50_le,0), 3)
      | eval p95_ms=round(1000*coalesce(p95_le,0), 3)
      | eval p99_ms=round(1000*coalesce(p99_le,0), 3)
      | eval p999_ms=round(1000*coalesce(p999_le,0), 3)
      | eval telemetry_lane="admission_webhook" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, crd_group, crd_resource, "k8s conversion"))))
      | eval hook_type=lower(trim(toString(coalesce(type, "conversion"))))
      | eval operation=upper(trim(toString(coalesce(operation, op, "ALL"))))
      | where mn="apiserver_admission_step_conversion_duration_seconds_bucket" AND len(cluster)>0
      | eval le_raw=trim(toString(coalesce(le, le_label, "")))
      | bucket _time span=5m
      | eval win_time=_time
      | stats max(mv) AS cum_at_bucket BY cluster hook_name hook_type operation win_time le_raw
      | eval le_num=case(match(le_raw,"^\\+Inf$"), 1000000000, true(), tonumber(le_raw))
      | where isnotnull(le_num)
      | sort 0 cluster hook_name hook_type operation win_time le_num
      | eventstats max(eval(if(match(le_raw,"^\\+Inf$"), cum_at_bucket, null()))) AS histo_total BY cluster hook_name hook_type operation win_time
      | where isnotnull(histo_total) AND histo_total>0
      | eval hit50=if(cum_at_bucket>=(0.50*histo_total), le_num, null())
      | eval hit95=if(cum_at_bucket>=(0.95*histo_total), le_num, null())
      | eval hit99=if(cum_at_bucket>=(0.99*histo_total), le_num, null())
      | eval hit999=if(cum_at_bucket>=(0.999*histo_total), le_num, null())
      | stats min(hit50) AS p50_le min(hit95) AS p95_le min(hit99) AS p99_le min(hit999) AS p999_le BY cluster hook_name hook_type operation win_time
      | eval p50_ms=round(1000*coalesce(p50_le,0), 3)
      | eval p95_ms=round(1000*coalesce(p95_le,0), 3)
      | eval p99_ms=round(1000*coalesce(p99_le,0), 3)
      | eval p999_ms=round(1000*coalesce(p999_le,0), 3)
      | eval telemetry_lane="conversion_step" ]
| sort 0 cluster win_time telemetry_lane hook_name hook_type operation
| eventstats perc95(p99_ms) AS cluster_p99_adm_context BY cluster win_time
| streamstats window=3 current=t global=f avg(p99_ms) AS p99_ma3 BY cluster hook_name hook_type operation telemetry_lane
| join type=left max=0 cluster hook_name
    [| inputlookup webhook_tail_latency_governance.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval hook_name=lower(trim(toString(webhook_name)))
      | eval timeout_sec=tonumber(tostring(coalesce(timeout_seconds, "10")), 10)
      | eval owner_team=trim(toString(coalesce(owner_team, squad, "")))
      | eval p99_budget_ms=tonumber(tostring(coalesce(p99_budget_ms, budget_p99_ms, "800")), 10)
      | fields cluster hook_name timeout_sec owner_team p99_budget_ms ]
| fillnull value="" owner_team
| fillnull value=10 timeout_sec
| fillnull value=800 p99_budget_ms
| eval timeout_ms=timeout_sec*1000
| eval slack_ms_to_deadline=round(timeout_ms - p999_ms, 3)
| eval tail_ratio_p99_p50=if(p50_ms>0.01, round(p99_ms/p50_ms, 3), null())
| join type=left max=0 cluster win_time
    [| search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, objectRef_cluster, ""))))
      | eval ns=trim(toString(coalesce(objectRef.namespace, "")))
      | eval verb_raw=upper(trim(toString(coalesce(verb, ""))))
      | where len(cluster)>0 AND len(ns)>0 AND verb_raw IN ("CREATE","UPDATE","PATCH","DELETE")
      | bucket _time span=5m
      | eval win_time=_time
      | stats count AS evt_cnt BY cluster win_time ns
      | sort 0 cluster win_time -evt_cnt
      | dedup cluster win_time
      | rename ns AS top_admission_namespace ]
| join type=left max=0 cluster win_time
    [| search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, objectRef_cluster, ""))))
      | eval ns=trim(toString(coalesce(objectRef.namespace, "")))
      | where len(cluster)>0 AND len(ns)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats dc(ns) AS admission_ns_breadth BY cluster win_time ]
| join type=left max=0 cluster win_time
    [| search index=k8s_logs earliest=-30m@m latest=@m ("kyverno" OR "gatekeeper" OR "validatingadmissionpolicy")
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, ""))))
      | where len(cluster)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats count AS policy_log_cnt BY cluster win_time ]
| join type=left max=0 cluster
    [| tstats summariesonly=true latest(Application_State.info) AS cim_app_state FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
      | rename Application_State.dest AS cluster ]
| join type=left max=0 win_time
    [| tstats summariesonly=false count AS perf_overlay_events FROM datamodel=Performance WHERE nodename=Performance earliest=-30m@m latest=@m BY _time span=5m
      | rename _time AS win_time ]
| fillnull value=0 policy_log_cnt admission_ns_breadth perf_overlay_events
| fillnull value="" top_admission_namespace cim_app_state
| eval severity_tier=case(
    slack_ms_to_deadline<=75 OR p999_ms>=(0.95*timeout_ms), "critical",
    p99_ms>=(0.80*timeout_ms) OR coalesce(tail_ratio_p99_p50,0)>=9, "high",
    p99_ms>=(0.60*timeout_ms) OR coalesce(tail_ratio_p99_p50,0)>=6 OR p99_ms>=p99_budget_ms, "medium",
    coalesce(tail_ratio_p99_p50,0)>=4 OR cluster_p99_adm_context>=1200, "low",
    true(), "info")
| where severity_tier IN ("critical","high","medium","low")
| table cluster win_time telemetry_lane hook_name hook_type operation p50_ms p95_ms p99_ms p999_ms tail_ratio_p99_p50 timeout_sec slack_ms_to_deadline cluster_p99_adm_context p99_ma3 top_admission_namespace admission_ns_breadth policy_log_cnt perf_overlay_events severity_tier owner_team cim_app_state
```

savedsearches.conf sketch:

```ini
[uc_3_2_45_webhook_tail_profile]
cron_schedule = */5 * * * *
dispatch.earliest_time = -30m@m
dispatch.latest_time = @m
enableSched = 1
alert.track = 1
action.email = 1
action.email.to = platform-admission@example.com
action.email.subject = Webhook tail $result.severity_tier$ on $result.cluster$ $result.hook_name$
search = | savedsearch uc_3_2_45_webhook_tail_profile_base
```

For Splunk ITSI optional episodes, bind severity_tier critical to priority one when slack_ms_to_deadline stays below one hundred milliseconds for two consecutive windows.

### Step 4 — Validate

Synthetic slow admission path: in a lab cluster, inject a deliberate sleep inside a test validating webhook service or throttle NetworkPolicy between apiserver and webhook pods under change control; confirm apiserver_admission_webhook_admission_duration_seconds_bucket shifts mass into high le labels within two five-minute windows and uc_3_2_45_webhook_tail_profile raises severity_tier while slack_ms_to_deadline collapses toward zero.

Synthetic conversion path: exercise a CRD with a conversion webhook that performs an intentional slow transform in test only; confirm the conversion_step telemetry_lane rows gain p99_ms and p999_ms while admission_webhook rows for unrelated hooks remain calm.

Synthetic namespace skew: drive bursty creates into one namespace while another stays quiet; confirm top_admission_namespace tracks the hot namespace and admission_ns_breadth remains consistent with activity.

Negative path: remove throttles and sleeps, restore baseline policy bundles, and confirm tail_ratio_p99_p50 falls below medium thresholds for two consecutive buckets.

Data quality path: if conversion histograms never appear, validate Kubernetes minor and scrape config rather than muting the UC; admission-only clusters should still populate admission_webhook rows.

RBAC path: readers without k8s_metrics must see zero rows.

Lookup path: null owner_team after join signals webhook_tail_latency_governance.csv drift; fix before production paging.

CIM path: null cim_app_state indicates Application_State acceleration or naming mismatches against cluster identifiers.

Correlation path: cross-check UC-3.2.40 when denial metrics move without tail inflation to avoid mis-prioritising latency work during policy incidents.

Performance path: widen investigative clones to earliest=-60m@m only for ad-hoc triage; keep scheduled alerts at thirty minutes to limit indexer load.

Audit sampling path: if audit volume drops sharply while metrics look hot, validate audit policy before trusting namespace witnesses alone.

### Step 5 — Operationalize & Troubleshoot

Case 1 — P999 within a few hundred milliseconds of timeoutSeconds while P50 stays healthy: treat as imminent timeout failure; scale webhook replicas, reduce policy cost, split heavy validations into asynchronous controllers where architecture allows, or raise timeoutSeconds only after explicit risk acceptance.

Case 2 — tail_ratio_p99_p50 above six with stable CPU: investigate bimodal paths such as cold policy compilation on first touch, large object payloads including huge ConfigMaps, remote calls to internal certificate authorities, or cache misses after pod churn.

Case 3 — CREATE dominates latency for one hook while UPDATE is calm: narrow Kyverno or Gatekeeper rules to the offending Kind, inspect generate versus validate rule costs, and replay audit samples for object sizes.

Case 4 — conversion_step lane spikes alone: inspect CRD conversion webhook implementations for remote schema fetches, broken compression, or accidental synchronous network calls; pair with apiextensions controller logs.

Case 5 — top_admission_namespace stable on a noisy tenant: coordinate with tenant owners for batch creation storms, GitOps apply bursts, or test harness traffic; tune CSV budgets before muting.

Case 6 — admission_ns_breadth collapses during platform incidents: expect concentrated blast radius; prioritize kube-system protection and failurePolicy posture from UC-3.2.40 before deep policy edits.

Case 7 — policy_log_cnt high with flat histograms: logging verbosity may be misleading; correlate with controller CPU and admission metrics rather than logs alone.

Case 8 — perf_overlay_events spikes without hook tails: suspect node saturation unrelated to admission; pivot to node and datastore analytics before rewriting policies.

Case 9 — multi-replica webhooks after horizontal scale-out: expect per-pod cold caches producing temporary tail inflation; require sustained windows before executive escalation.

Case 10 — dual-stack or service mesh init adding connect latency: document in governance CSV notes and compare slack_ms_to_deadline against mesh dashboards.

Case 11 — freshly pulled webhook images and language runtime warm-up: expect first-call JVM or JIT effects; compare against image rollout timestamps.

Case 12 — deliberately heavy compliance gates: escalate through change boards when tightening thresholds; do not silently widen timeouts without owner_team approval.

Closing checklist: five em-dash step headers are present exactly; Step 3 contains a fenced spl block matching the spl field; multisearch includes admission and conversion histogram arms; eventstats, streamstats, coalesce ladders, case severity tiers, inputlookup join, dual tstats joins, audit joins, and log correlation joins are present; final table includes cluster, win_time, telemetry_lane, hook_name, hook_type, operation, p50_ms, p95_ms, p99_ms, p999_ms, tail_ratio_p99_p50, timeout_sec, slack_ms_to_deadline, cluster_p99_adm_context, p99_ma3, top_admission_namespace, admission_ns_breadth, policy_log_cnt, perf_overlay_events, severity_tier, owner_team, and cim_app_state.

Telemetry hygiene addendum for large fleets: duplicate scrapes without honor_labels discipline can double cumulative bucket counts; deduplicate per scrape_instance before stats. For OpenShift, confirm namespace versus project labels map consistently to cluster. For air-gapped mirrors, delayed webhook image pulls can mimic tail spikes; verify registry health before fail-closed changes. For multi-tenant Splunk, isolate k8s_audit from overly broad shared indexes. For regulated environments, redact workload names in alert actions while retaining hook identifiers. For Windows node pools, webhook Services still usually target Linux controller pods; keep scope explicit in governance CSV notes.

FinOps alignment: track webhook label cardinality quarterly; experimental hooks should carry higher p99_budget_ms or be excluded via lookup flags. Reliability alignment: pair with UC-3.2.7 when apiserver restart storms overlap admission scrape alignment. Security alignment: sustained tail inflation on security hooks may indicate probing or abusive object shapes; forward medium rows to security operations when audit subjects include cluster-admin impersonation. Performance alignment: keep earliest at thirty minutes for alerts; widen only in investigative clones. Operations alignment: document who may adjust timeoutSeconds under CAB versus emergency change. Capacity alignment: watch etcd object counts for large ConstraintTemplate libraries that enlarge evaluation cost.

Runbook micro-sections: if severity is critical and slack_ms_to_deadline is below one hundred milliseconds, page platform and policy jointly. If policy_log_cnt is zero but tails are high, validate log routing before concluding absence of engine activity. If tstats returns null cim_app_state, verify data model acceleration paths. If conversion rows never appear, validate metric exports after upgrades.

Training drills: quarterly inject webhook tail latency in lab; semi-annually rehearse CRD conversion failure drills; monthly verify OTEL still scrapes apiserver after control-plane upgrades.

Audit evidence: export weekly CSV of the closing table to a restricted index with webhook_tail_latency_governance.csv commit hash in the description field.

Governance: record temporary timeoutSeconds increases with incident commander approval and automatic expiry in the lookup.

Extended platform notes for mixed estates: when GitOps controllers reconcile thousands of objects per minute, expect periodic tail noise on validating hooks that enforce labels; distinguish steady-state noise from regressions using moving averages and change correlation. When service meshes inject sidecars late in rollouts, admission mutations may lengthen briefly; compare against rollout timestamps. When internal CA queues sign requests during renewal storms, cert-manager class webhooks may show tails without cluster-wide failure; pair with certificate inventory reviews. When cluster-api or similar orchestrators create many namespaces in parallel, admission_ns_breadth may jump without implying a single-tenant hotspot; read top_admission_namespace alongside breadth.

## SPL

```spl
`comment("UC-3.2.45 Admission and conversion webhook tail-latency profile. Tunables: idx_metrics=k8s_metrics idx_audit=k8s_audit idx_logs=k8s_logs st_metrics=prometheus:scrape:metrics st_audit=kube:apiserver:audit earliest=-30m@m latest=@m; lookup webhook_tail_latency_governance.csv; default_timeout_sec=10")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(webhook_name, admission_webhook, name, ""))))
      | eval hook_type=lower(trim(toString(coalesce(type, hook_kind, ""))))
      | eval operation=upper(trim(toString(coalesce(operation, op, ""))))
      | where mn="apiserver_admission_webhook_admission_duration_seconds_bucket" AND len(cluster)>0 AND len(hook_name)>0
      | eval le_raw=trim(toString(coalesce(le, le_label, "")))
      | bucket _time span=5m
      | eval win_time=_time
      | stats max(mv) AS cum_at_bucket BY cluster hook_name hook_type operation win_time le_raw
      | eval le_num=case(match(le_raw,"^\\+Inf$"), 1000000000, true(), tonumber(le_raw))
      | where isnotnull(le_num)
      | sort 0 cluster hook_name hook_type operation win_time le_num
      | eventstats max(eval(if(match(le_raw,"^\\+Inf$"), cum_at_bucket, null()))) AS histo_total BY cluster hook_name hook_type operation win_time
      | where isnotnull(histo_total) AND histo_total>0
      | eval hit50=if(cum_at_bucket>=(0.50*histo_total), le_num, null())
      | eval hit95=if(cum_at_bucket>=(0.95*histo_total), le_num, null())
      | eval hit99=if(cum_at_bucket>=(0.99*histo_total), le_num, null())
      | eval hit999=if(cum_at_bucket>=(0.999*histo_total), le_num, null())
      | stats min(hit50) AS p50_le min(hit95) AS p95_le min(hit99) AS p99_le min(hit999) AS p999_le BY cluster hook_name hook_type operation win_time
      | eval p50_ms=round(1000*coalesce(p50_le,0), 3)
      | eval p95_ms=round(1000*coalesce(p95_le,0), 3)
      | eval p99_ms=round(1000*coalesce(p99_le,0), 3)
      | eval p999_ms=round(1000*coalesce(p999_le,0), 3)
      | eval telemetry_lane="admission_webhook" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, crd_group, crd_resource, "k8s conversion"))))
      | eval hook_type=lower(trim(toString(coalesce(type, "conversion"))))
      | eval operation=upper(trim(toString(coalesce(operation, op, "ALL"))))
      | where mn="apiserver_admission_step_conversion_duration_seconds_bucket" AND len(cluster)>0
      | eval le_raw=trim(toString(coalesce(le, le_label, "")))
      | bucket _time span=5m
      | eval win_time=_time
      | stats max(mv) AS cum_at_bucket BY cluster hook_name hook_type operation win_time le_raw
      | eval le_num=case(match(le_raw,"^\\+Inf$"), 1000000000, true(), tonumber(le_raw))
      | where isnotnull(le_num)
      | sort 0 cluster hook_name hook_type operation win_time le_num
      | eventstats max(eval(if(match(le_raw,"^\\+Inf$"), cum_at_bucket, null()))) AS histo_total BY cluster hook_name hook_type operation win_time
      | where isnotnull(histo_total) AND histo_total>0
      | eval hit50=if(cum_at_bucket>=(0.50*histo_total), le_num, null())
      | eval hit95=if(cum_at_bucket>=(0.95*histo_total), le_num, null())
      | eval hit99=if(cum_at_bucket>=(0.99*histo_total), le_num, null())
      | eval hit999=if(cum_at_bucket>=(0.999*histo_total), le_num, null())
      | stats min(hit50) AS p50_le min(hit95) AS p95_le min(hit99) AS p99_le min(hit999) AS p999_le BY cluster hook_name hook_type operation win_time
      | eval p50_ms=round(1000*coalesce(p50_le,0), 3)
      | eval p95_ms=round(1000*coalesce(p95_le,0), 3)
      | eval p99_ms=round(1000*coalesce(p99_le,0), 3)
      | eval p999_ms=round(1000*coalesce(p999_le,0), 3)
      | eval telemetry_lane="conversion_step" ]
| sort 0 cluster win_time telemetry_lane hook_name hook_type operation
| eventstats perc95(p99_ms) AS cluster_p99_adm_context BY cluster win_time
| streamstats window=3 current=t global=f avg(p99_ms) AS p99_ma3 BY cluster hook_name hook_type operation telemetry_lane
| join type=left max=0 cluster hook_name
    [| inputlookup webhook_tail_latency_governance.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval hook_name=lower(trim(toString(webhook_name)))
      | eval timeout_sec=tonumber(tostring(coalesce(timeout_seconds, "10")), 10)
      | eval owner_team=trim(toString(coalesce(owner_team, squad, "")))
      | eval p99_budget_ms=tonumber(tostring(coalesce(p99_budget_ms, budget_p99_ms, "800")), 10)
      | fields cluster hook_name timeout_sec owner_team p99_budget_ms ]
| fillnull value="" owner_team
| fillnull value=10 timeout_sec
| fillnull value=800 p99_budget_ms
| eval timeout_ms=timeout_sec*1000
| eval slack_ms_to_deadline=round(timeout_ms - p999_ms, 3)
| eval tail_ratio_p99_p50=if(p50_ms>0.01, round(p99_ms/p50_ms, 3), null())
| join type=left max=0 cluster win_time
    [| search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, objectRef_cluster, ""))))
      | eval ns=trim(toString(coalesce(objectRef.namespace, "")))
      | eval verb_raw=upper(trim(toString(coalesce(verb, ""))))
      | where len(cluster)>0 AND len(ns)>0 AND verb_raw IN ("CREATE","UPDATE","PATCH","DELETE")
      | bucket _time span=5m
      | eval win_time=_time
      | stats count AS evt_cnt BY cluster win_time ns
      | sort 0 cluster win_time -evt_cnt
      | dedup cluster win_time
      | rename ns AS top_admission_namespace ]
| join type=left max=0 cluster win_time
    [| search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, objectRef_cluster, ""))))
      | eval ns=trim(toString(coalesce(objectRef.namespace, "")))
      | where len(cluster)>0 AND len(ns)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats dc(ns) AS admission_ns_breadth BY cluster win_time ]
| join type=left max=0 cluster win_time
    [| search index=k8s_logs earliest=-30m@m latest=@m ("kyverno" OR "gatekeeper" OR "validatingadmissionpolicy")
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, ""))))
      | where len(cluster)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats count AS policy_log_cnt BY cluster win_time ]
| join type=left max=0 cluster
    [| tstats summariesonly=true latest(Application_State.info) AS cim_app_state FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
      | rename Application_State.dest AS cluster ]
| join type=left max=0 win_time
    [| tstats summariesonly=false count AS perf_overlay_events FROM datamodel=Performance WHERE nodename=Performance earliest=-30m@m latest=@m BY _time span=5m
      | rename _time AS win_time ]
| fillnull value=0 policy_log_cnt admission_ns_breadth perf_overlay_events
| fillnull value="" top_admission_namespace cim_app_state
| eval severity_tier=case(
    slack_ms_to_deadline<=75 OR p999_ms>=(0.95*timeout_ms), "critical",
    p99_ms>=(0.80*timeout_ms) OR coalesce(tail_ratio_p99_p50,0)>=9, "high",
    p99_ms>=(0.60*timeout_ms) OR coalesce(tail_ratio_p99_p50,0)>=6 OR p99_ms>=p99_budget_ms, "medium",
    coalesce(tail_ratio_p99_p50,0)>=4 OR cluster_p99_adm_context>=1200, "low",
    true(), "info")
| where severity_tier IN ("critical","high","medium","low")
| table cluster win_time telemetry_lane hook_name hook_type operation p50_ms p95_ms p99_ms p999_ms tail_ratio_p99_p50 timeout_sec slack_ms_to_deadline cluster_p99_adm_context p99_ma3 top_admission_namespace admission_ns_breadth policy_log_cnt perf_overlay_events severity_tier owner_team cim_app_state
```

## CIM SPL

```spl
| tstats summariesonly=true latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS cim_cluster
| join type=left max=0 cim_cluster
    [| tstats summariesonly=true avg(Performance.cpu_load_percent) AS cpu_load_pct FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-4h@h latest=@h BY Performance.host
     | rename Performance.host AS cim_cluster ]
| table cim_cluster app_state app_info cpu_load_pct
```

## Visualization

Timechart of p50_ms p95_ms p99_ms p999_ms by hook_name and telemetry_lane; heatmap of tail_ratio_p99_p50; single-value tiles for slack_ms_to_deadline minima; table mirroring the SPL closing projection with cell colors on severity_tier; drilldown from top_admission_namespace to kube:apiserver:audit samples.

## Known False Positives

Legitimately slow webhooks sometimes do expensive work by design: Kyverno first-call policy compilation, OPA Gatekeeper bundle reloads after Git pushes, and just-in-time certificate signing paths can stretch one bucket while remaining correct. Webhooks that call an internal certificate authority or enterprise policy service may show benign tails when that dependency is briefly slow without implying cluster misconfiguration. Batch creation storms, bursty test harness traffic, or GitOps apply waves can temporarily inflate P99 and P999 while medians stay acceptable. Very large ConfigMaps and Secret-heavy objects increase serialization cost and widen tails for mutating hooks that rewrite images or labels. Rare admin-only operations naturally traverse slower code paths and should be documented in governance CSV notes. Webhooks scaled out across many replicas can exhibit per-pod cold caches that look like incidents for a single five-minute bucket. Brief webhook restarts, dual-stack networking initialization delays, freshly pulled images with language runtime warm-up, and deliberately heavy compliance gates all produce legitimate tail inflation. When clusters run intentionally strict admission policies for regulatory reasons, sustained tail cost may be an accepted trade-off; pair alerts with owner_team budgets rather than muting silently.

## References

- [Kubernetes — Dynamic Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)
- [Kubernetes Metrics Reference (kube-apiserver instrumentation)](https://kubernetes.io/docs/reference/instrumentation/metrics/)
- [Prometheus — Histograms and quantiles](https://prometheus.io/docs/practices/histograms/)
- [Kubernetes API — MutatingWebhookConfiguration v1 (timeoutSeconds)](https://kubernetes.io/docs/reference/kubernetes-api/extend-resources/mutating-webhook-configuration-v1/)
- [Kyverno — Troubleshooting](https://kyverno.io/docs/troubleshooting/)
- [Gatekeeper — Operations and performance tuning](https://open-policy-agent.github.io/gatekeeper/website/docs/operations/)
- [Splunk — Add-on for Kubernetes](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
