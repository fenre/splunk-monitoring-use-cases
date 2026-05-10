<!-- AUTO-GENERATED from UC-3.2.40.json — DO NOT EDIT -->

---
id: "3.2.40"
title: "Kubernetes Admission Webhook Latency, Timeouts, and Denials (Out-of-Tree Webhook Reliability Axis)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.40 · Kubernetes Admission Webhook Latency, Timeouts, and Denials (Out-of-Tree Webhook Reliability Axis)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the extra safety gates that outside tools attach to every cluster change. When those gates get slow, sick, or too strict, ordinary work stops—we surface that early so teams fix the gate before everything piles up.*

---

## Description

Monitors out-of-tree Kubernetes dynamic admission reliability: mutating and validating webhooks implemented by operators such as Kyverno, OPA Gatekeeper, Cosign policy controllers, cert-manager, AWS Load Balancer Controller, Argo CD, and custom CRD hooks. The analytic multisearches apiserver_admission_webhook_request_total for error share, apiserver_admission_webhook_rejection_count for explicit denials, apiserver_admission_webhook_admission_duration_seconds_sum and count for average hook latency plus apiserver_admission_webhook_admission_duration_seconds_bucket tail witnesses, joins kube:apiserver:audit narratives for failed calling webhook and timeout strings, enriches kube_mutatingwebhookconfiguration_info and kube_validatingwebhookconfiguration_info for hook kind context, applies governance from webhook_policy_governance.csv, and optionally overlays Splunk CIM Application_State via tstats. It targets failure modes—ten second timeouts, five-xx transport failures, policy regressions, p99-class slowness proxied by budgets, failurePolicy=Fail availability traps, kube-system blast radius, mutation conflicts, and namespaceSelector misses—without duplicating UC-3.2.22 PSA, UC-3.2.7 control-plane synthesis, UC-3.2.19 generic apiserver latency, or UC-3.2.12 RBAC analytics.

## Value

Clusters fail in practice when admission hooks are unhealthy: GitOps cannot sync, certificates cannot renew, workloads cannot roll, and incident recovery itself may be blocked when kube-system paths are covered by a failing hook. Splunk rows that fuse Prometheus admission metrics, audit denial narratives, kube-state webhook metadata, and signed governance lookups collapse mean time to innocence for platform and application security teams during policy incidents. Executives receive evidence suitable for error-budget reviews because latency and denial budgets are expressed per hook with owner_team routing, while SREs retain paste-and-run SPL that respects managed-cloud and self-managed scrape differences across Amazon EKS, Google GKE, and Microsoft AKS estates.

## Implementation

Provision k8s_metrics and k8s_audit with distinct HEC tokens; scrape kube-apiserver prometheus metrics including apiserver_admission_webhook_* series and kube-state-metrics webhook info; ship kube:apiserver:audit with depth for failing admission paths; publish webhook_policy_governance.csv in git; deploy Splunk OTEL Collector prometheus and filelog receivers; save uc_3_2_40_webhook_reliability every five minutes over earliest=-30m@m latest=@m; route critical kube-system-touching hooks to platform policy bridges with owner_team enrichment.

## Evidence

Saved search uc_3_2_40_webhook_reliability with five-minute schedule; versioned webhook_policy_governance.csv in git; weekly CSV export of the closing table to a restricted evidence index with audit hash samples.

## Control test

### Positive scenario

In a lab cluster with metrics and audit landing in Splunk, scale a failurePolicy=Fail webhook Deployment to zero and attempt a guarded create; confirm apiserver_admission_webhook_request_total shows errors for that hook, audit records failed calling webhook or timeout text, and uc_3_2_40_webhook_reliability emits a medium or higher severity_tier row within ten minutes when webhook_policy_governance.csv lists the hook as production.

### Negative scenario

Restore the webhook pod, confirm err_rate_pct and audit_hint_cnt fall below thresholds for two consecutive five-minute buckets, and verify the saved search returns no qualifying rows for that hook while UC-3.2.7 remains healthy.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the Kubernetes platform engineering lead, the policy-as-code owners for Kyverno and Gatekeeper, the GitOps and ingress teams that operate cert-manager and AWS Load Balancer Controller webhooks, and the observability engineers who run Splunk OpenTelemetry Collector across clusters. UC-3.2.40 is deliberately the out-of-tree dynamic admission reliability axis: mutating and validating webhooks implemented by operators and controllers outside the core Kubernetes binary—Kyverno, OPA Gatekeeper, Cosign policy controllers, cert-manager admission, AWS LBC, Argo CD, and bespoke CRD webhooks—rather than in-tree Pod Security Admission covered by UC-3.2.22, rather than aggregate apiserver liveness in UC-3.2.7, rather than generic apiserver request latency in UC-3.2.19, and rather than RBAC misconfiguration analytics in UC-3.2.12. When this alert fires, incident command should suspect the admission pipeline: a webhook that times out at the default ten second boundary, returns five-xx because its operator pod is down or its TLS material is wrong, denies valid objects after a policy regression, runs hot enough that every create or update pays more than roughly one second inside the hook, or is configured with failurePolicy=Fail while its workload is not running—any of which can cripple cluster convergence. Additional catastrophic classes include webhooks whose rules unintentionally match kube-system objects, namespaceSelector misconfigurations that broaden scope, and two mutating hooks fighting over the same field.

Index and sourcetype contracts: designate index=k8s_metrics for prometheus:scrape:metrics lines scraped from kube-apiserver and kube-state-metrics, preserving labels on apiserver_admission_webhook_request_total, apiserver_admission_webhook_admission_duration_seconds_bucket, apiserver_admission_webhook_rejection_count, kube_mutatingwebhookconfiguration_info, and kube_validatingwebhookconfiguration_info. Stand up index=k8s_audit for kube:apiserver:audit with sufficient depth that failing admission paths retain responseStatus messages mentioning webhooks, timeouts, and policy denials; RequestResponse on create, update, and patch for workload APIs is strongly recommended in regulated tiers. Issue distinct HEC tokens per index class with quarterly rotation and least-privilege roles so application developers cannot read full audit bodies for unrelated namespaces.

Scrape topology: vanilla Kubernetes exposes apiserver metrics on the control-plane scrape target; Prometheus Operator users need a ServiceMonitor or static scrape config that reaches apiserver /metrics with TLS and bearer token appropriate to the platform. Amazon EKS, Google GKE, and Microsoft AKS may surface some admission telemetry only through cloud metric exports—mirror those series into the same k8s_metrics schema with a normalised cluster label so this SPL does not fork per cloud. kube-state-metrics must be new enough to expose validating and mutating webhook configuration info series; upgrade kube-state-metrics when those lines are absent in lab.

Governance lookup: publish lookups/webhook_policy_governance.csv under version control with columns cluster, webhook_name, owner_team, expected_failure_policy (fail or ignore), touches_kube_system_risk (1 when the webhook configuration can intercept kube-system objects or cluster-scoped resources critical to recovery), slo_p99_ms_budget (per-hook latency budget in milliseconds, default one thousand), optional exception_expiry epoch, and notes for Kyverno generate rules versus validate rules. Refresh the CSV from the same repository that applies ValidatingWebhookConfiguration and MutatingWebhookConfiguration objects so auditors can trace Git commit ancestry to Splunk rows.

Risk briefing: default admission webhook timeoutSeconds is ten seconds; at that boundary the apiserver fails the request even when the webhook is merely slow, which surfaces as user-visible errors and elevated apiserver_admission_webhook_request_total error labels rather than a neat pod CrashLoop on the webhook workload. TLS errors between apiserver and webhook Service endpoints present as five-xx style failures in metrics and as failed calling webhook strings in audit. Policy regressions increase apiserver_admission_webhook_rejection_count without necessarily raising operator CPU. Two mutating webhooks rewriting the same field can create oscillating patches or opaque merge errors—pair this UC with change records when GitOps bumps policy libraries.

Privacy and legal: audit bodies may include object specs; restrict indexes and redact secrets at collection. Licensing: high-cardinality webhook names are acceptable compared to pod labels but still warrant FinOps review when clusters host hundreds of experimental hooks in shared labs.

Training: teach responders the difference between failurePolicy=Fail (apiserver blocks when the hook is unreachable) and Ignore (requests proceed when the hook errors), and why Ignore is sometimes chosen for non-critical hooks even though it trades safety for availability. Document that UC-3.2.13 certificate inventory complements this UC when TLS expiry is the root cause.

Differentiation recap: out-of-tree webhook pipeline health with Prometheus and audit corroboration, not PSA denials, not control-plane-only synthesis, not RBAC, not generic apiserver SLO panels without admission labels.

### Step 2 — Configure data collection

First, ensure kube-apiserver metrics reach Splunk with labels intact. OpenTelemetry Collector prometheus receiver jobs should scrape the apiserver Service or control-plane endpoint with relabel rules that keep name, operation, code, le, and hook-identifying labels as indexed or search-time fields where your props transforms allow. Second, scrape kube-state-metrics for kube_mutatingwebhookconfiguration_info and kube_validatingwebhookconfiguration_info so analysts can map Prometheus hook names to configuration kinds without kubectl during incidents.

Example ServiceMonitor fragment for apiserver metrics when your platform team already runs kube-prometheus-stack:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-apiserver-admission-metrics
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

Audit policy should retain enough detail to see webhook failures. A minimal illustrative rule block:

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - "RequestReceived"
rules:
  - level: RequestResponse
    verbs: ["create", "update", "patch", "delete"]
    resources:
      - group: ""
        resources: ["pods", "services", "configmaps", "secrets"]
      - group: "apps"
        resources: ["deployments", "replicasets", "statefulsets", "daemonsets"]
```

OpenTelemetry Collector routing should land prometheus lines on index=k8s_metrics with sourcetype=prometheus:scrape:metrics and audit JSON on index=k8s_audit with sourcetype=kube:apiserver:audit, sharing a consistent k8s_cluster_name resource attribute.

Publish webhook_policy_governance.csv aligned to the join keys used in Step 3:

```csv
cluster,webhook_name,owner_team,expected_failure_policy,touches_kube_system_risk,slo_p99_ms_budget,notes
prod-eks-01,kyverno-resource-validating-webhook-cfg,team-platform,fail,1,800,Kyverno validate+mutate cluster-critical
prod-eks-01,cert-manager-webhook,team-platform,fail,0,1200,TLS issuance path
lab-gke-01,gatekeeper-validating-webhook-configuration,team-security,fail,0,1000,OPA Gatekeeper
```

Pre-flight searches: index=k8s_metrics apiserver_admission_webhook_request_total earliest=-15m must be non-zero on active clusters; index=k8s_audit failed calling webhook earliest=-24h should return sample rows after a deliberate deny test in lab.

CIM acceleration: accelerate Application_State and Performance on management hosts or kubernetes_cluster entities referenced in Application_State.dest so the tstats arm stays warm for executive overlays described in cimSpl.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_40_webhook_reliability with a five-minute schedule, dispatch earliest=-30m@m, dispatch latest=now, and throttle duplicate cluster and webhook_name rows for ten minutes unless severity_tier escalates from medium to critical within the same half hour. Include owner_team from the governance lookup in pager descriptions and attach deep links to internal runbooks for Kyverno, Gatekeeper, cert-manager, and cloud load balancer webhooks.

Pipeline narrative: the opening comment macro records tunable index names, sourcetypes, time window, and lookup path. multisearch fans four metric arms—apiserver_admission_webhook_request_total for volume and five-xx share by hook name and operation, apiserver_admission_webhook_rejection_count for explicit denials, apiserver_admission_webhook_admission_duration_seconds_sum and _count for average admission latency in milliseconds as an operational proxy for slow hooks, and apiserver_admission_webhook_admission_duration_seconds_bucket for high le buckets that act as a tail-latency witness when cumulative buckets are scraped. After fan-in stats by cluster, hook_name, operation, and five-minute bucket, err_rate_pct estimates webhook-side error share. A left join overlays audit counts from kube:apiserver:audit where responseStatus messages reference webhook, admission, denied, or timeout substrings and a rex extracts hook names from failed calling webhook text. A second join maps kube_mutatingwebhookconfiguration_info and kube_validatingwebhookconfiguration_info to classify mutating versus validating sidecars. eventstats computes cluster-level perc95(admit_latency_ms) for burst context. streamstats provides a short moving average lat_ma3 to smooth single-scrape spikes. inputlookup webhook_policy_governance.csv enriches owner_team, expected_failure_policy, touches_kube_system_risk, and per-hook slo_p99_ms_budget. A tstats join against Application_State supplies optional cim_state_info for correlation when kubernetes entities are modeled in CIM. case() assigns severity_tier from critical through low; rows at info are dropped for paging efficiency. The closing table lists fifteen analyst columns for triage.

Paste-and-run SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.2.40 Out-of-tree admission webhook reliability. Tunables: idx_metrics=k8s_metrics idx_audit=k8s_audit st_metrics=prometheus:scrape:metrics st_audit=kube:apiserver:audit; earliest=-30m@m latest=@m; lookup webhook_policy_governance.csv keys cluster+webhook_name; default_p99_budget_ms=1000")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | eval code=trim(toString(coalesce(code, status_code, http_status, "")))
      | where mn="apiserver_admission_webhook_request_total" AND len(cluster)>0 AND len(hook_name)>0
      | eval is_5xx=if(match(code, "^5[0-9]{2}$"), 1, 0)
      | bucket _time span=5m
      | stats sum(mv) AS req_total sum(eval(if(is_5xx==1, mv, 0))) AS err_5xx BY cluster hook_name op _time
      | eval rej_obs=0
      | eval admit_avg_ms=0
      | eval tail_bucket_sig=0
      | eval audit_hint_cnt=0 ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | where mn="apiserver_admission_webhook_rejection_count" AND len(cluster)>0 AND len(hook_name)>0
      | bucket _time span=5m
      | stats sum(mv) AS rej_obs BY cluster hook_name op _time
      | eval req_total=0
      | eval err_5xx=0
      | eval admit_avg_ms=0
      | eval tail_bucket_sig=0
      | eval audit_hint_cnt=0 ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | where (mn="apiserver_admission_webhook_admission_duration_seconds_sum" OR mn="apiserver_admission_webhook_admission_duration_seconds_count") AND len(cluster)>0 AND len(hook_name)>0
      | bucket _time span=5m
      | stats sum(eval(if(mn=="apiserver_admission_webhook_admission_duration_seconds_sum", mv, 0))) AS dur_sum sum(eval(if(mn=="apiserver_admission_webhook_admission_duration_seconds_count", mv, 0))) AS dur_cnt BY cluster hook_name op _time
      | eval admit_avg_ms=if(dur_cnt>0, round(1000*dur_sum/dur_cnt, 3), 0)
      | eval req_total=0
      | eval err_5xx=0
      | eval rej_obs=0
      | eval tail_bucket_sig=0
      | eval audit_hint_cnt=0 ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | eval le_raw=trim(tostring(coalesce(le, le_label, "")))
      | where mn="apiserver_admission_webhook_admission_duration_seconds_bucket" AND len(cluster)>0 AND len(hook_name)>0 AND match(le_raw, "^((\\+)?Inf|30|\\+Inf)$")
      | bucket _time span=5m
      | stats max(mv) AS tail_bucket_sig BY cluster hook_name op _time
      | eval req_total=0
      | eval err_5xx=0
      | eval rej_obs=0
      | eval admit_avg_ms=0
      | eval audit_hint_cnt=0 ]
| stats sum(req_total) AS req_total sum(err_5xx) AS err_5xx sum(rej_obs) AS rej_obs max(admit_avg_ms) AS admit_avg_ms max(tail_bucket_sig) AS tail_bucket_sig BY cluster hook_name op _time
| eval err_rate_pct=if(req_total>0, round(100.0*err_5xx/req_total, 4), 0)
| eval admit_latency_ms=coalesce(if(admit_avg_ms>0, admit_avg_ms, null()), if(tail_bucket_sig>0, 1200, null()), 0)
| join type=left max=0 cluster hook_name
    [| search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, objectRef_cluster, ""))))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")), 10)
      | eval resp_msg=lower(toString(coalesce('responseStatus.message', responseStatus.message, responseStatus_message, "")))
      | rex field=_raw max_match=0 "(?i)failed calling webhook[^:]*:\\s*(?<rex_hook>[a-z0-9][a-z0-9\\.\\-]+/[a-z0-9][a-z0-9\\.\\-]*)"
      | eval hook_name=lower(trim(toString(coalesce(rex_hook, ""))))
      | where resp_code>=400 AND match(resp_msg, "webhook|admission|denied|timeout")
      | where len(cluster)>0 AND len(hook_name)>1
      | stats count AS audit_hint_cnt BY cluster hook_name ]
| join type=left max=0 cluster hook_name
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | where like(mn, "kube_mutatingwebhookconfiguration_info") OR like(mn, "kube_validatingwebhookconfiguration_info")
      | rex field=_raw max_match=0 "(?im)hook_name\\s*=\\s*\\\"(?<whn>[^\\\"]+)\\\""
      | eval hook_name=lower(trim(toString(coalesce(whn, ""))))
      | eval wh_kind=if(like(mn, "mutating"), "mutating", "validating")
      | where len(cluster)>0 AND len(hook_name)>0
      | stats latest(wh_kind) AS wh_kind BY cluster hook_name ]
| fillnull value=0 audit_hint_cnt
| eventstats perc95(admit_latency_ms) AS cluster_p95_ms BY cluster _time
| streamstats window=3 current=t global=f avg(admit_latency_ms) AS lat_ma3 BY cluster hook_name
| join type=left max=0 cluster hook_name
    [| inputlookup webhook_policy_governance.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval hook_name=lower(trim(toString(webhook_name)))
      | eval owner_team=trim(toString(coalesce(owner_team, squad, policy_owner, "")))
      | eval expected_failure_policy=lower(trim(toString(coalesce(expected_failure_policy, failure_policy_expected, ""))))
      | eval touches_kube_system_risk=tonumber(tostring(coalesce(touches_kube_system_risk, kube_system_touch, "0")), 10)
      | eval slo_p99_ms_budget=tonumber(tostring(coalesce(slo_p99_ms_budget, p99_budget_ms, "1000")), 10)
      | fields cluster hook_name owner_team expected_failure_policy touches_kube_system_risk slo_p99_ms_budget ]
| fillnull value="" owner_team expected_failure_policy
| fillnull value=1000 slo_p99_ms_budget
| fillnull value=0 touches_kube_system_risk
| join type=left max=0 cluster
    [| tstats summariesonly=t latest(Application_State.info) AS cim_state_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
      | rename Application_State.dest AS cluster ]
| eval budget_ms=coalesce(slo_p99_ms_budget, 1000)
| eval severity_tier=case(
    touches_kube_system_risk=1 AND (err_rate_pct>=1 OR admit_latency_ms>=budget_ms OR rej_obs>=3), "critical",
    err_rate_pct>=2 OR like(lower(coalesce(cim_state_info, "")), "%down%"), "critical",
    admit_latency_ms>=budget_ms OR rej_obs>=5, "high",
    admit_latency_ms>=round(budget_ms*0.7,0) OR err_rate_pct>=0.5 OR audit_hint_cnt>=10, "medium",
    audit_hint_cnt>=3 OR rej_obs>=1, "low",
    true(), "info")
| where severity_tier IN ("critical","high","medium","low")
| eval wh_sidecar=coalesce(wh_kind, "unknown")
| table cluster hook_name op wh_sidecar admit_latency_ms cluster_p95_ms err_rate_pct rej_obs audit_hint_cnt severity_tier owner_team expected_failure_policy touches_kube_system_risk lat_ma3 cim_state_info
```

savedsearches.conf sketch:

```ini
[uc_3_2_40_webhook_reliability]
cron_schedule = */5 * * * *
dispatch.earliest_time = -30m@m
dispatch.latest_time = now
enableSched = 1
alert.track = 1
action.email = 1
action.email.to = platform-policy@example.com
action.email.subject = Admission webhook $result.severity_tier$ on $result.cluster$ hook $result.hook_name$
search = | savedsearch uc_3_2_40_webhook_reliability_base
```

### Step 4 — Validate

Synthetic timeout path: in a disposable namespace, scale the Kyverno or Gatekeeper webhook Deployment to zero while leaving failurePolicy=Fail on a hook that guards that namespace; attempt a guarded create and confirm kube:apiserver:audit shows a four-xx response with webhook timeout language within one minute, apiserver_admission_webhook_request_total increments error labels for that hook name, and uc_3_2_40_webhook_reliability returns at least a medium row when the governance lookup marks the hook as production-critical.

Synthetic denial path: deploy a ConfigMap or pod that violates an intentional test policy; confirm apiserver_admission_webhook_rejection_count rises for the validating hook and audit shows a structured denial message; verify severity_tier respects slo_p99_ms_budget when latency remains low.

Synthetic latency path: inject sleep inside a test webhook service or throttle NetworkPolicy between apiserver and webhook pods in lab only; confirm admit_latency_ms crosses budget_ms and cluster_p95_ms follows.

Negative path: restore the webhook pod, remove throttles, and confirm err_rate_pct and rej_obs fall below alert predicates within two five-minute buckets.

RBAC path: readers without k8s_metrics or k8s_audit must see zero rows.

Correlation path: cross-check UC-3.2.7 for apiserver-wide outages that could distort webhook metrics versus true hook failure.

Data quality path: if kube-state-metrics lacks webhook info series, wh_sidecar remains unknown without failing the search; upgrade kube-state-metrics and revalidate.

Lookup path: rows with null owner_team after join indicate webhook_policy_governance.csv gaps to fix before production paging.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Webhook timeout at ten seconds: inspect apiserver to webhook Service connectivity, Endpoint slices, and mutatingwebhookconfiguration timeoutSeconds; temporarily scale webhook pods; consider splitting heavy validation across async controllers only when architecture allows.

Case 2 — Five-xx or TLS handshake errors: rotate webhook serving certificates with cert-manager or internal PKI, verify caBundle on ValidatingWebhookConfiguration objects, and pair UC-3.2.13 when expiry is imminent.

Case 3 — Surge in apiserver_admission_webhook_rejection_count after GitOps upgrade: roll back the policy bundle, replay audit samples to identify the denying rule, and open a defect against the policy repo.

Case 4 — admit_latency_ms above one second budget: profile webhook controller CPU and etcd read latency for policy CRDs, add caching, reduce JSON patch complexity, or shard high-volume namespaces.

Case 5 — failurePolicy=Fail with webhook pods not running: treat as cluster-breaking; prioritize pod scheduling and PDB conflicts before blaming applications; escalate to platform policy on-call.

Case 6 — Webhook rules touch kube-system unintentionally: narrow objectSelector and namespaceSelector, exclude kube-system in policy configuration, and rehearse recovery where core-dns or metrics-server updates were blocked.

Case 7 — namespaceSelector misses causing broader scope than intended: diff webhook YAML against architecture diagrams; fix label selectors; document exceptions in webhook_policy_governance.csv.

Case 8 — Two mutating webhooks overwrite the same field: order webhooks explicitly where Kubernetes allows, merge policies into one hook, or remove redundant mutations discovered via audit diff.

Case 9 — Cloud provider constraints on admission webhooks: review Amazon EKS, Google GKE, and Microsoft AKS guidance on private clusters, network policies, and control-plane to worker reachability for webhook Services.

Case 10 — Argo CD or GitOps sync hooks interacting with admission: verify sync waves and resource ordering; transient denials during apply storms may need retry logic rather than pager storms—tune severity using audit_hint_cnt thresholds.

Case 11 — AWS Load Balancer Controller or ingress webhooks denying Services: correlate with cloud API throttling; ensure webhook queues are healthy; check controller logs alongside Prometheus series.

Case 12 — Cosign or image policy webhook denying pulls during registry outages: distinguish registry availability from policy logic; route to supply-chain team when signatures are valid but metadata fetches stall.

Closing checklist: five em-dash step headers present; Step 3 fenced SPL matches spl; multisearch includes request_total, rejection_count, duration sum/count, and duration bucket arms; joins include audit, kube-state webhook info, governance lookup, and tstats Application_State; eventstats and streamstats present; case assigns severity_tier; final table has fifteen columns including cluster, hook_name, op, wh_sidecar, admit_latency_ms, cluster_p95_ms, err_rate_pct, rej_obs, audit_hint_cnt, severity_tier, owner_team, expected_failure_policy, touches_kube_system_risk, lat_ma3, cim_state_info; monitoringType lists Reliability and Availability; cimModels lists Application_State and Performance.


Telemetry hygiene addendum for large fleets: when redundant collectors scrape the same apiserver without honor_labels discipline, deduplicate on scrape_instance before stats or risk doubled err_rate_pct. For OpenShift, confirm project versus namespace labels map to cluster consistently. For air-gapped mirrors, webhook image pulls may lag and mimic outage—correlate with UC image pull analytics before fail-closed changes. For multi-tenant Splunk, isolate k8s_audit from broad shared indexes. For PCI environments, redact workload names in alert actions while retaining hook_name identifiers. For Windows node pools, webhook Services still target Linux controller pods in most designs—keep scope explicit in governance CSV notes.

FinOps alignment: track cardinality of hook_name labels quarterly; rare experimental hooks should carry higher slo_p99_ms_budget or be excluded via lookup flags. Reliability alignment: pair with UC-3.2.7 when apiserver restart storms overlap webhook metrics. Security alignment: denial bursts may indicate attack probes—forward medium rows to security operations when audit subjects include cluster-admin impersonation. Performance alignment: keep earliest at thirty minutes for alerts; widen only in investigative clones. Operations alignment: document who may flip failurePolicy under CAB versus emergency change. Capacity alignment: watch etcd object counts for large ConstraintTemplate libraries that slow Gatekeeper.

Runbook micro-sections: if severity is critical and touches_kube_system_risk=1, page platform and policy jointly. If err_rate_pct is zero but audit_hint_cnt is high, validate audit sampling versus metrics scrape gaps. If wh_sidecar is unknown, upgrade kube-state-metrics and enrich CSV. If tstats returns null cim_state_info, verify data model acceleration and entity naming.

Training drills: quarterly inject webhook latency in lab; semi-annually rehearse cert rotation for a production-like webhook; monthly verify OTEL still scrapes apiserver after control-plane upgrades.

Audit evidence: export weekly CSV of the closing table to a restricted index with webhook_policy_governance.csv commit hash in the description field.

Governance: record temporary failurePolicy=Ignore changes with incident commander approval and automatic expiry in the lookup.



## SPL

```spl
`comment("UC-3.2.40 Out-of-tree admission webhook reliability. Tunables: idx_metrics=k8s_metrics idx_audit=k8s_audit st_metrics=prometheus:scrape:metrics st_audit=kube:apiserver:audit; earliest=-30m@m latest=@m; lookup webhook_policy_governance.csv keys cluster+webhook_name; default_p99_budget_ms=1000")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | eval code=trim(toString(coalesce(code, status_code, http_status, "")))
      | where mn="apiserver_admission_webhook_request_total" AND len(cluster)>0 AND len(hook_name)>0
      | eval is_5xx=if(match(code, "^5[0-9]{2}$"), 1, 0)
      | bucket _time span=5m
      | stats sum(mv) AS req_total sum(eval(if(is_5xx==1, mv, 0))) AS err_5xx BY cluster hook_name op _time
      | eval rej_obs=0
      | eval admit_avg_ms=0
      | eval tail_bucket_sig=0
      | eval audit_hint_cnt=0 ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | where mn="apiserver_admission_webhook_rejection_count" AND len(cluster)>0 AND len(hook_name)>0
      | bucket _time span=5m
      | stats sum(mv) AS rej_obs BY cluster hook_name op _time
      | eval req_total=0
      | eval err_5xx=0
      | eval admit_avg_ms=0
      | eval tail_bucket_sig=0
      | eval audit_hint_cnt=0 ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | where (mn="apiserver_admission_webhook_admission_duration_seconds_sum" OR mn="apiserver_admission_webhook_admission_duration_seconds_count") AND len(cluster)>0 AND len(hook_name)>0
      | bucket _time span=5m
      | stats sum(eval(if(mn=="apiserver_admission_webhook_admission_duration_seconds_sum", mv, 0))) AS dur_sum sum(eval(if(mn=="apiserver_admission_webhook_admission_duration_seconds_count", mv, 0))) AS dur_cnt BY cluster hook_name op _time
      | eval admit_avg_ms=if(dur_cnt>0, round(1000*dur_sum/dur_cnt, 3), 0)
      | eval req_total=0
      | eval err_5xx=0
      | eval rej_obs=0
      | eval tail_bucket_sig=0
      | eval audit_hint_cnt=0 ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | eval le_raw=trim(tostring(coalesce(le, le_label, "")))
      | where mn="apiserver_admission_webhook_admission_duration_seconds_bucket" AND len(cluster)>0 AND len(hook_name)>0 AND match(le_raw, "^((\\+)?Inf|30|\\+Inf)$")
      | bucket _time span=5m
      | stats max(mv) AS tail_bucket_sig BY cluster hook_name op _time
      | eval req_total=0
      | eval err_5xx=0
      | eval rej_obs=0
      | eval admit_avg_ms=0
      | eval audit_hint_cnt=0 ]
| stats sum(req_total) AS req_total sum(err_5xx) AS err_5xx sum(rej_obs) AS rej_obs max(admit_avg_ms) AS admit_avg_ms max(tail_bucket_sig) AS tail_bucket_sig BY cluster hook_name op _time
| eval err_rate_pct=if(req_total>0, round(100.0*err_5xx/req_total, 4), 0)
| eval admit_latency_ms=coalesce(if(admit_avg_ms>0, admit_avg_ms, null()), if(tail_bucket_sig>0, 1200, null()), 0)
| join type=left max=0 cluster hook_name
    [| search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, objectRef_cluster, ""))))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")), 10)
      | eval resp_msg=lower(toString(coalesce('responseStatus.message', responseStatus.message, responseStatus_message, "")))
      | rex field=_raw max_match=0 "(?i)failed calling webhook[^:]*:\\s*(?<rex_hook>[a-z0-9][a-z0-9\\.\\-]+/[a-z0-9][a-z0-9\\.\\-]*)"
      | eval hook_name=lower(trim(toString(coalesce(rex_hook, ""))))
      | where resp_code>=400 AND match(resp_msg, "webhook|admission|denied|timeout")
      | where len(cluster)>0 AND len(hook_name)>1
      | stats count AS audit_hint_cnt BY cluster hook_name ]
| join type=left max=0 cluster hook_name
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | where like(mn, "kube_mutatingwebhookconfiguration_info") OR like(mn, "kube_validatingwebhookconfiguration_info")
      | rex field=_raw max_match=0 "(?im)hook_name\\s*=\\s*\\\"(?<whn>[^\\\"]+)\\\""
      | eval hook_name=lower(trim(toString(coalesce(whn, ""))))
      | eval wh_kind=if(like(mn, "mutating"), "mutating", "validating")
      | where len(cluster)>0 AND len(hook_name)>0
      | stats latest(wh_kind) AS wh_kind BY cluster hook_name ]
| fillnull value=0 audit_hint_cnt
| eventstats perc95(admit_latency_ms) AS cluster_p95_ms BY cluster _time
| streamstats window=3 current=t global=f avg(admit_latency_ms) AS lat_ma3 BY cluster hook_name
| join type=left max=0 cluster hook_name
    [| inputlookup webhook_policy_governance.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval hook_name=lower(trim(toString(webhook_name)))
      | eval owner_team=trim(toString(coalesce(owner_team, squad, policy_owner, "")))
      | eval expected_failure_policy=lower(trim(toString(coalesce(expected_failure_policy, failure_policy_expected, ""))))
      | eval touches_kube_system_risk=tonumber(tostring(coalesce(touches_kube_system_risk, kube_system_touch, "0")), 10)
      | eval slo_p99_ms_budget=tonumber(tostring(coalesce(slo_p99_ms_budget, p99_budget_ms, "1000")), 10)
      | fields cluster hook_name owner_team expected_failure_policy touches_kube_system_risk slo_p99_ms_budget ]
| fillnull value="" owner_team expected_failure_policy
| fillnull value=1000 slo_p99_ms_budget
| fillnull value=0 touches_kube_system_risk
| join type=left max=0 cluster
    [| tstats summariesonly=t latest(Application_State.info) AS cim_state_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
      | rename Application_State.dest AS cluster ]
| eval budget_ms=coalesce(slo_p99_ms_budget, 1000)
| eval severity_tier=case(
    touches_kube_system_risk=1 AND (err_rate_pct>=1 OR admit_latency_ms>=budget_ms OR rej_obs>=3), "critical",
    err_rate_pct>=2 OR like(lower(coalesce(cim_state_info, "")), "%down%"), "critical",
    admit_latency_ms>=budget_ms OR rej_obs>=5, "high",
    admit_latency_ms>=round(budget_ms*0.7,0) OR err_rate_pct>=0.5 OR audit_hint_cnt>=10, "medium",
    audit_hint_cnt>=3 OR rej_obs>=1, "low",
    true(), "info")
| where severity_tier IN ("critical","high","medium","low")
| eval wh_sidecar=coalesce(wh_kind, "unknown")
| table cluster hook_name op wh_sidecar admit_latency_ms cluster_p95_ms err_rate_pct rej_obs audit_hint_cnt severity_tier owner_team expected_failure_policy touches_kube_system_risk lat_ma3 cim_state_info
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS cim_cluster
| join type=left max=0 cim_cluster
    [| tstats summariesonly=t avg(Performance.cpu_load_percent) AS cpu_load_pct avg(Performance.mem_used_percent) AS mem_used_pct FROM datamodel=Performance WHERE nodename=Performance.CPU OR nodename=Performance.Memory earliest=-4h@h latest=@h BY Performance.host
     | rename Performance.host AS cim_cluster ]
| table cim_cluster app_state app_info cpu_load_pct mem_used_pct
```

## Visualization

Severity-colored table mirroring the closing SPL projection; timechart of admit_latency_ms and err_rate_pct by hook_name; single-value tiles for critical and high severity counts; drilldown from audit_hint_cnt to raw kube:apiserver:audit JSON; companion panel for touches_kube_system_risk equals one.

## Known False Positives

Planned webhook operator upgrades restart pods and can produce short five-xx bursts and missing Endpoint events that look like outages; require two consecutive windows or correlate with change tickets before paging production bridges. Transient TLS handshake failures during cert-manager or internal PKI rotation are common for tens of seconds when caBundle updates race controller restarts; pair with certificate notAfter telemetry from UC-3.2.13 before declaring hook death. DNS-01 ACME challenges for cert-manager webhook certificates may legitimately take more than thirty seconds while public DNS propagates; suppress latency alerts on cert-manager hooks during documented issuance windows. Gatekeeper constraint template library reloads and Kyverno policy library syncs temporarily increase admission latency while caches warm; treat single-bucket spikes as benign when GitOps commits show only library bumps. Network blips between apiserver and webhook Services on large clusters create correlated timeouts during AZ maintenance; cross-check cloud provider status and node-to-control-plane routing before fail-closed policy changes. Namespace-scoped validating hooks that intentionally deny misconfigured pods in test namespaces will raise rejection counts by design; mark those namespaces or hooks with exception_expiry in webhook_policy_governance.csv or lower severity. Webhooks configured with failurePolicy=Ignore may still increment rejection metrics when policies deny requests while allowing the request to continue on hook transport errors—read expected_failure_policy before treating rejections as blocking incidents. Managed Kubernetes control planes sometimes restart apiserver instances during transparent maintenance, which can look like webhook instability when metrics scrape aligns with restart; verify with UC-3.2.7 before blaming Kyverno. High-cardinality audit sampling or Metadata-only audit policies can hide webhook messages while metrics look healthy; never silence this UC on metrics alone when audit volume drops unexpectedly.

## References

- [Kubernetes — Dynamic Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)
- [Kyverno documentation](https://kyverno.io/docs/)
- [OPA Gatekeeper documentation](https://open-policy-agent.github.io/gatekeeper/website/docs/)
- [Kubernetes API — MutatingWebhookConfiguration v1 (timeoutSeconds)](https://kubernetes.io/docs/reference/kubernetes-api/extend-resources/mutating-webhook-configuration-v1/)
- [cert-manager — Webhook concepts](https://cert-manager.io/docs/concepts/webhook/)
- [Kubernetes SIG Auth — Admission signals and SLO guidance](https://github.com/kubernetes/community/blob/master/sig-auth/signals/admission/README.md)
- [Amazon EKS — Troubleshooting](https://docs.aws.amazon.com/eks/latest/userguide/troubleshooting.html)
- [Google GKE — API server authentication overview](https://cloud.google.com/kubernetes-engine/docs/concepts/api-server-authentication)
- [Microsoft AKS — Security best practices](https://learn.microsoft.com/en-us/azure/aks/best-practices-security)
- [Splunk — Add-on for Kubernetes](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
