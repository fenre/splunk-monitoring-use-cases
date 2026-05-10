<!-- AUTO-GENERATED from UC-3.2.21.json — DO NOT EDIT -->

---
id: "3.2.21"
title: "Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis)"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.2.21 · Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis)

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the cluster gatekeepers that double-check every change. When those checks take too long, the front door starts turning people away and everyday tools time out—we show which gatekeeper is eating the clock before everything grinds to a halt.*

---

## Description

Detects when cumulative admission and validation webhook latency consumes enough of the kube-apiserver request path that the control plane begins shedding work: Priority and Fairness queues deepen, clients observe 429 TooManyRequests and 504 GatewayTimeout on apiserver_request_total, kubectl surfaces i/o timeout and context deadline exceeded, and downstream controllers show workqueue growth or scheduler stalls. The analytic fuses apiserver_admission_webhook_request_total call volume per hook with apiserver_admission_webhook_admission_duration_seconds histogram math for P50, P95, and P99 milliseconds per webhook name and mutating versus validating type, compares observed P99 to timeoutSeconds policy intent, estimates the share of apiserver wall time attributable to webhook admission using apiserver_admission_webhook_admission_duration_seconds_sum against apiserver_request_duration_seconds_sum at the cluster grain, overlays apiserver_admission_step_admission_duration_seconds for full admission pipeline cost, surfaces apiserver_admission_webhook_rejection_count with error_type apiserver_internal_error as the apiserver abandoning slow hooks, and correlates rising 429 and 504 codes on apiserver_request_total with webhook-heavy windows. UC-3.2.40 remains webhook errors, transport failures, and denial reliability. UC-3.2.45 remains pure latency distribution profiling without budget and shedding semantics. UC-3.2.19 remains verb-resource-client request pipeline latency without webhook attribution. UC-3.2.7 remains four-pillar control-plane synthesis.

## Value

Tail latency inside admission webhooks is invisible in a generic apiserver latency panel until clients already time out. Quantifying per-hook share of wall time, comparing P99 to configured timeoutSeconds, and correlating with 429 and 504 shedding gives platform owners evidence to right-size policy engines, split hot namespaces, cache policy bundles, or raise concurrency before incident command burns hours blaming etcd. Capacity reviewers receive a defensible story linking webhook seconds consumed to API Priority and Fairness pressure and to FinOps conversations about control-plane headroom on large clusters.

## Implementation

Scrape kube-apiserver prometheus metrics into k8s_metrics with webhook and admission step series intact; publish k8s_webhook_latency_budget.csv with per-hook P99 milliseconds budget and owner; accelerate CIM Application_State and Performance for cluster entities; save uc_3_2_21_webhook_budget_backpressure every five minutes on earliest=-30m@m latest=@m; route critical rows to platform API reliability with links to UC-3.2.19 APF tuning and UC-3.2.40 hook health.

## Evidence

Saved search uc_3_2_21_webhook_budget_backpressure on a five-minute schedule; versioned k8s_webhook_latency_budget.csv in git; weekly CSV export of the closing table to a restricted evidence index with optional controller-manager log excerpts referencing timeout strings.

## Control test

### Positive scenario

In a lab cluster with k8s_metrics populated from kube-apiserver scrapes, inject controlled latency into a mutating or validating webhook path under change control; confirm apiserver_admission_webhook_admission_duration_seconds quantiles rise, frac_wall_pct increases when apiserver_request_duration_seconds_sum is non-zero, apiserver_request_total shows 429 or 504 increments in the same windows under sufficient load, and uc_3_2_21_webhook_budget_backpressure returns a medium or higher severity_tier row with owner_team enriched from k8s_webhook_latency_budget.csv.

### Negative scenario

Remove the latency injection and restore normal admission throughput; confirm p99_ms falls below budget_ms for two consecutive five-minute buckets, shed_rpm returns toward zero, and the saved search emits no qualifying rows while UC-3.2.19 overall pipeline posture remains interpretable.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with Kubernetes platform engineering, the policy-as-code owners operating Kyverno or OPA Gatekeeper, and observability engineers running Splunk OpenTelemetry Collector across clusters. UC-3.2.21 isolates a single axis: webhook latency cumulatively consuming apiserver request budget and manifesting as shedding and client timeouts, not webhook unavailability as the primary story (UC-3.2.40), not percentile-only latency profiling (UC-3.2.45), and not verb-resource-client decomposition without admission attribution (UC-3.2.19). When this alert fires, suspect admission path stalls: a validating hook whose P99 approaches timeoutSeconds, a mutating hook that serializes large object graphs on every pod update, a policy engine cold start after upgrade, or a webhook that performs synchronous calls to external certificate or license endpoints. The apiserver still returns 200 on many paths while Priority and Fairness rejects burst traffic and long hooks push concurrent request seats to exhaustion, so symptoms include rising apiserver_flowcontrol_rejected_requests_total in raw metrics (even when not every field is in the closing table), 429 and 504 labels on apiserver_request_total, and user-visible context deadline exceeded from controllers.

Index contracts: designate index=k8s_metrics for sourcetype=prometheus:scrape:metrics events scraped from kube-apiserver with labels __name__, name or hook identifier, operation, type for mutating versus validating, le for histogram buckets, code on apiserver_request_total, error_type on apiserver_admission_webhook_rejection_count, verb where present, and k8s_cluster_name or equivalent cluster tags. Issue HEC tokens with least privilege; separate platform metrics from application logs.

Scrape topology: reach apiserver /metrics with TLS and bearer token appropriate to your distribution. Prometheus Operator users install a ServiceMonitor that keeps high-cardinality hook name labels unless FinOps policy strips them; this UC requires name-level attribution, so do not drop the name label on admission webhook series. Amazon EKS, Google GKE, and Microsoft AKS may require cloud metric export parity—normalize exported series into the same mn and label conventions so the SPL does not fork per cloud.

Governance lookup: maintain lookups/k8s_webhook_latency_budget.csv in git with columns cluster, webhook_name, hook_type (mutating, validating, or any), p99_budget_ms (integer milliseconds aligned to engineering SLO), owner_team, notes for timeoutSeconds policy reference, optional suppress_lab (1 for noisy lab hooks). Refresh the CSV when ValidatingWebhookConfiguration and MutatingWebhookConfiguration objects change.

Risk briefing: default admission webhook timeoutSeconds is ten seconds; P99 near that boundary is a production incident even when error counters look quiet because the apiserver is spending whole seconds inside hooks. apiserver_admission_webhook_rejection_count with error_type apiserver_internal_error indicates the apiserver gave up waiting, which is distinct from policy denial rejections. API Priority and Fairness may reject clients that would have succeeded with shorter admission chains; pair investigations with UC-3.2.19 when FlowSchema tuning is on the table.

Training: teach responders how mutating hooks run before validating hooks in the admission chain, why a slow mutator shifts work for later validators, and why controller-runtime based operators can amplify admission load during mass object updates. Document kubectl verbosity limits when reproducing timeouts so incident traffic does not worsen saturation.

Privacy: prometheus labels may include namespace or object hints in some distributions; restrict indexes when regulated.

### Step 2 — Configure data collection

First, verify kube-apiserver exposes apiserver_admission_webhook_request_total, apiserver_admission_webhook_admission_duration_seconds_*, apiserver_admission_step_admission_duration_seconds_*, apiserver_request_duration_seconds_* , apiserver_request_total, and apiserver_admission_webhook_rejection_count in a lab scrape before enabling alerts.

Second, configure OpenTelemetry Collector prometheus receiver scrape intervals between fifteen and sixty seconds; align five-minute bucket spans in the SPL with at least two samples per bucket on busy clusters.

Example ServiceMonitor fragment:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-apiserver-webhook-budget-metrics
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

Sample k8s_webhook_latency_budget.csv:

```csv
cluster,webhook_name,hook_type,p99_budget_ms,owner_team,notes,suppress_lab
prod-eks-01,kyverno-resource-validating-webhook-cfg,validating,750,team-platform,Kyverno validate cluster-wide,0
prod-eks-01,cert-manager-webhook,mutating,1200,team-platform,TLS issuance mutating path,0
lab-kind-01,gatekeeper-validating-webhook-configuration,validating,900,team-security,OPA Gatekeeper lab,1
```

props.conf should extract __name__, name, operation, type, le, code, error_type, verb, and cluster tags as indexed or default fields where possible.

Pre-flight searches: index=k8s_metrics apiserver_admission_webhook_request_total earliest=-15m must be non-zero on active clusters; index=k8s_metrics apiserver_request_total code=504 OR code=429 earliest=-24h should occasionally return rows during deliberate load tests.

CIM acceleration: accelerate Application_State and Performance on management hosts or kubernetes cluster entities so tstats overlays resolve during incidents.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_21_webhook_budget_backpressure with a five-minute schedule, dispatch earliest=-30m@m, dispatch latest=@m, and throttle duplicate cluster and webhook_name rows for ten minutes unless severity_tier escalates to critical within the same half hour. Include p99_ms, frac_wall_pct, and shed_rpm in pager bodies.

Pipeline narrative: the opening comment macro lists tunables. multisearch fans seven metric arms: apiserver_admission_webhook_request_total for call volume by hook name, operation, and type; apiserver_admission_webhook_admission_duration_seconds_sum and _count for average hook latency milliseconds; apiserver_admission_webhook_admission_duration_seconds_bucket for histogram quantiles P50, P95, P99 per hook; apiserver_admission_webhook_rejection_count filtered toward apiserver_internal_error; apiserver_request_total for 429 and 504 shedding rates by cluster window; apiserver_admission_step_admission_duration_seconds_sum and _count for admission pipeline average milliseconds at cluster grain; apiserver_request_duration_seconds_sum for cluster wall-time denominator used with webhook sum to estimate frac_wall_pct. After fusion with stats by cluster hook_name hook_type win_time, synthetic rows _cluster_shed_, _cluster_step_, and _cluster_wall_ hold cluster-level shed totals, admission-step averages, and wall-clock denominator sums; eventstats max of shed_seed, step_seed, and wall_seed broadcasts shed_rpm_cluster, step_avg_ms_cluster, and apiserver_wall_cluster onto every row in the same cluster and win_time before those aggregate marker rows are filtered out; a follow-on eventstats derives cluster-level p95 of hook P99 for burst context. streamstats smooths hook_avg_ms into avg_ma3. inputlookup k8s_webhook_latency_budget.csv enriches p99_budget_ms and owner_team. join tstats Application_State supplies cim_app_state. case assigns severity_tier from critical through low based on P99 versus budget, frac_wall_pct, shed_rpm, and internal rejections. The closing table lists sixteen analyst columns.

Paste-and-run SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.2.21 Webhook latency-driven apiserver budget exhaustion. Tunables: index=k8s_metrics sourcetype=prometheus:scrape:metrics earliest=-30m@m latest=@m; lookup k8s_webhook_latency_budget.csv; shed_rpm_warn=5 frac_wall_warn=35")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | eval hook_type=lower(trim(toString(coalesce(type, hook_kind, webhook_type, ""))))
      | where mn="apiserver_admission_webhook_request_total" AND len(cluster)>0 AND len(hook_name)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats sum(mv) AS calls_5m BY cluster hook_name hook_type op win_time
      | eval wh_sum_sec=0
      | eval wh_cnt=0
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval internal_rej=0
      | eval shed_rpm=0
      | eval step_avg_ms=0
      | eval apiserver_wall_sec=0
      | eval lane="volume" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | eval hook_type=lower(trim(toString(coalesce(type, hook_kind, webhook_type, ""))))
      | where (mn="apiserver_admission_webhook_admission_duration_seconds_sum" OR mn="apiserver_admission_webhook_admission_duration_seconds_count") AND len(cluster)>0 AND len(hook_name)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats sum(eval(if(mn=="apiserver_admission_webhook_admission_duration_seconds_sum", mv, 0))) AS wh_sum_sec sum(eval(if(mn=="apiserver_admission_webhook_admission_duration_seconds_count", mv, 0))) AS wh_cnt BY cluster hook_name hook_type op win_time
      | eval calls_5m=0
      | eval hook_avg_ms=if(wh_cnt>0, round(1000*wh_sum_sec/wh_cnt, 3), 0)
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval internal_rej=0
      | eval shed_rpm=0
      | eval step_avg_ms=0
      | eval apiserver_wall_sec=0
      | eval lane="avg" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | eval hook_type=lower(trim(toString(coalesce(type, hook_kind, webhook_type, ""))))
      | eval le_raw=trim(toString(coalesce(le, le_label, "")))
      | where mn="apiserver_admission_webhook_admission_duration_seconds_bucket" AND len(cluster)>0 AND len(hook_name)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats max(mv) AS cum_at_le BY cluster hook_name hook_type op win_time le_raw
      | eval le_num=case(match(le_raw,"^\\+Inf$"), 1000000000, true(), tonumber(le_raw))
      | where isnotnull(le_num)
      | sort 0 cluster hook_name hook_type op win_time le_num
      | eventstats max(eval(if(match(le_raw,"^\\+Inf$"), cum_at_le, null()))) AS histo_total BY cluster hook_name hook_type op win_time
      | where isnotnull(histo_total) AND histo_total>0
      | eval hit50=if(cum_at_le>=(0.50*histo_total), le_num, null())
      | eval hit95=if(cum_at_le>=(0.95*histo_total), le_num, null())
      | eval hit99=if(cum_at_le>=(0.99*histo_total), le_num, null())
      | stats min(hit50) AS p50_le min(hit95) AS p95_le min(hit99) AS p99_le BY cluster hook_name hook_type op win_time
      | eval p50_ms=round(1000*coalesce(p50_le,0), 3)
      | eval p95_ms=round(1000*coalesce(p95_le,0), 3)
      | eval p99_ms=round(1000*coalesce(p99_le,0), 3)
      | eval calls_5m=0
      | eval wh_sum_sec=0
      | eval wh_cnt=0
      | eval hook_avg_ms=0
      | eval internal_rej=0
      | eval shed_rpm=0
      | eval step_avg_ms=0
      | eval apiserver_wall_sec=0
      | eval lane="histo" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | eval hook_type=lower(trim(toString(coalesce(type, hook_kind, webhook_type, ""))))
      | eval et=lower(trim(toString(coalesce(error_type, err_type, ""))))
      | where mn="apiserver_admission_webhook_rejection_count" AND len(cluster)>0 AND len(hook_name)>0 AND like(et, "%apiserver_internal_error%")
      | bucket _time span=5m
      | eval win_time=_time
      | stats sum(mv) AS internal_rej BY cluster hook_name hook_type op win_time
      | eval calls_5m=0
      | eval wh_sum_sec=0
      | eval wh_cnt=0
      | eval hook_avg_ms=0
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval shed_rpm=0
      | eval step_avg_ms=0
      | eval apiserver_wall_sec=0
      | eval lane="rej" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval code=trim(tostring(coalesce(code, status_code, http_status, "")))
      | where mn="apiserver_request_total" AND len(cluster)>0 AND (code="429" OR code="504")
      | bucket _time span=5m
      | eval win_time=_time
      | stats sum(mv) AS shed_rpm BY cluster win_time
      | eval hook_name="_cluster_shed_"
      | eval hook_type="na"
      | eval op="na"
      | eval calls_5m=0
      | eval wh_sum_sec=0
      | eval wh_cnt=0
      | eval hook_avg_ms=0
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval internal_rej=0
      | eval step_avg_ms=0
      | eval apiserver_wall_sec=0
      | eval lane="shed" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | where (mn="apiserver_admission_step_admission_duration_seconds_sum" OR mn="apiserver_admission_step_admission_duration_seconds_count") AND len(cluster)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats sum(eval(if(mn=="apiserver_admission_step_admission_duration_seconds_sum", mv, 0))) AS step_sum sum(eval(if(mn=="apiserver_admission_step_admission_duration_seconds_count", mv, 0))) AS step_cnt BY cluster win_time
      | eval step_avg_ms=if(step_cnt>0, round(1000*step_sum/step_cnt, 3), 0)
      | eval hook_name="_cluster_step_"
      | eval hook_type="na"
      | eval op="na"
      | eval calls_5m=0
      | eval wh_sum_sec=0
      | eval wh_cnt=0
      | eval hook_avg_ms=0
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval internal_rej=0
      | eval shed_rpm=0
      | eval apiserver_wall_sec=0
      | eval lane="step" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | where mn="apiserver_request_duration_seconds_sum" AND len(cluster)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats sum(mv) AS apiserver_wall_sec BY cluster win_time
      | eval hook_name="_cluster_wall_"
      | eval hook_type="na"
      | eval op="na"
      | eval calls_5m=0
      | eval wh_sum_sec=0
      | eval wh_cnt=0
      | eval hook_avg_ms=0
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval internal_rej=0
      | eval shed_rpm=0
      | eval step_avg_ms=0
      | eval lane="wall" ]
| stats sum(calls_5m) AS calls_5m sum(wh_sum_sec) AS wh_sum_sec sum(wh_cnt) AS wh_cnt max(hook_avg_ms) AS hook_avg_ms max(p50_ms) AS p50_ms max(p95_ms) AS p95_ms max(p99_ms) AS p99_ms sum(internal_rej) AS internal_rej max(shed_rpm) AS shed_rpm max(step_avg_ms) AS step_avg_ms max(apiserver_wall_sec) AS apiserver_wall_sec BY cluster hook_name hook_type op win_time
| eval shed_seed=if(hook_name=="_cluster_shed_", shed_rpm, null())
| eval step_seed=if(hook_name=="_cluster_step_", step_avg_ms, null())
| eval wall_seed=if(hook_name=="_cluster_wall_", apiserver_wall_sec, null())
| eventstats max(shed_seed) AS shed_rpm_cluster BY cluster win_time
| eventstats max(step_seed) AS step_avg_ms_cluster BY cluster win_time
| eventstats max(wall_seed) AS apiserver_wall_cluster BY cluster win_time
| eval shed_rpm=coalesce(shed_rpm_cluster, 0)
| eval step_avg_ms=coalesce(step_avg_ms_cluster, 0)
| eval hook_avg_ms=coalesce(if(hook_avg_ms>0, hook_avg_ms, null()), if(wh_cnt>0, round(1000*wh_sum_sec/wh_cnt, 3), null()), 0)
| eval frac_wall_pct=if(apiserver_wall_cluster>0 AND wh_sum_sec>0 AND hook_name!="_cluster_shed_" AND hook_name!="_cluster_step_" AND hook_name!="_cluster_wall_", round(100*wh_sum_sec/apiserver_wall_cluster, 3), null())
| where hook_name!="_cluster_shed_" AND hook_name!="_cluster_step_" AND hook_name!="_cluster_wall_"
| eventstats perc95(p99_ms) AS cluster_hook_p99_p95 BY cluster win_time
| streamstats window=3 current=t global=f avg(hook_avg_ms) AS avg_ma3 BY cluster hook_name hook_type
| join type=left max=0 cluster hook_name
    [| inputlookup k8s_webhook_latency_budget.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval hook_name=lower(trim(toString(webhook_name)))
      | eval p99_budget_ms=tonumber(tostring(coalesce(p99_budget_ms, budget_ms, "1000")), 10)
      | eval owner_team=trim(toString(coalesce(owner_team, squad, "platform_webhooks")))
      | fields cluster hook_name p99_budget_ms owner_team ]
| fillnull value=1000 p99_budget_ms
| fillnull value="platform_webhooks" owner_team
| join type=left max=0 cluster
    [| tstats summariesonly=t latest(Application_State.info) AS cim_app_state FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
      | rename Application_State.dest AS cluster ]
| eval budget_ms=coalesce(p99_budget_ms, 1000)
| eval severity_tier=case(
    shed_rpm>=20 AND p99_ms>=budget_ms, "critical",
    internal_rej>=3 OR (p99_ms>=budget_ms AND coalesce(frac_wall_pct,0)>=45), "critical",
    p99_ms>=round(0.95*budget_ms,0) OR coalesce(frac_wall_pct,0)>=35 OR shed_rpm>=5, "high",
    p95_ms>=round(0.85*budget_ms,0) OR cluster_hook_p99_p95>=budget_ms OR shed_rpm>=2, "medium",
    avg_ma3>=round(0.75*budget_ms,0) OR coalesce(frac_wall_pct,0)>=20, "low",
    true(), "info")
| where severity_tier IN ("critical","high","medium","low")
| table cluster win_time hook_name hook_type op calls_5m avg_ma3 p50_ms p95_ms p99_ms budget_ms frac_wall_pct shed_rpm step_avg_ms internal_rej severity_tier owner_team cim_app_state
```

savedsearches.conf sketch:

```ini
[uc_3_2_21_webhook_budget_backpressure]
cron_schedule = */5 * * * *
dispatch.earliest_time = -30m@m
dispatch.latest_time = @m
enableSched = 1
alert.track = 1
action.email = 1
action.email.to = platform-api@example.com
action.email.subject = Webhook budget $result.severity_tier$ on $result.cluster$ hook $result.hook_name$
```

### Step 4 — Validate

Synthetic slow webhook: in a lab namespace, inject intentional sleep in a test webhook Service or throttle NetworkPolicy between apiserver and webhook pods under change control; confirm apiserver_admission_webhook_admission_duration_seconds_bucket quantiles rise within two five-minute windows, frac_wall_pct increases against apiserver_request_duration_seconds_sum, and uc_3_2_21_webhook_budget_backpressure emits at least a medium row before user-visible timeouts.

Synthetic shedding: drive bursty admission traffic while a slow hook is active; confirm apiserver_request_total with code 429 or 504 increments in the same win_time buckets as elevated webhook latency; verify shed_rpm moves with severity_tier.

Synthetic internal error rejection: simulate apiserver timeout toward a hook that returns late; confirm apiserver_admission_webhook_rejection_count with apiserver_internal_error appears if your Kubernetes version labels that path.

Negative path: remove throttle or restore webhook performance; confirm p99_ms falls below budget_ms for two consecutive buckets and severity_tier returns to info rows filtered out.

Data quality probe: verify histogram positive-infinity buckets exist for apiserver_admission_webhook_admission_duration_seconds_bucket; without +Inf cumulative counts, quantile math collapses.

RBAC probe: readers without k8s_metrics must see zero rows.

CIM probe: null cim_app_state indicates missing acceleration or entity naming drift; fix before executive overlays.

### Step 5 — Operationalize & Troubleshoot

Case 1 — P99_ms at ninety-five percent of budget_ms with rising shed_rpm: treat as imminent outage; scale webhook pods, reduce synchronous external calls, split policies, or temporarily narrow webhook rules under CAB.

Case 2 — High frac_wall_pct for one Kyverno or Gatekeeper hook: profile policy compilation and cache warm paths; move heavy checks to background reporting only when architecture allows.

Case 3 — Mutating hook latency spikes only on CREATE: inspect object size storms and ConfigMap volume mounts; large payloads penalize JSON patch generation.

Case 4 — Validating hook spikes after operator upgrade: expect cold-cache penalty for one or two buckets; require sustained elevation before paging or correlate with change record.

Case 5 — shed_rpm high but hook P99 normal: pivot to UC-3.2.19 for APF and etcd saturation; webhook attribution may be a red herring when list storms dominate.

Case 6 — internal_rej rising without user complaints: still dangerous; apiserver is giving up on hooks—capture audit and apiserver logs for timeout strings.

Case 7 — Controller-manager workqueue depth grows with this UC firing: admission latency starves reconciliation loops; fix hooks before restarting controllers blindly.

Case 8 — Scheduler pending pods rises while admission slow: verify scheduler profiles and events; ensure not mis-attributing node capacity issues—cross-check UC-3.2.7.

Case 9 — cert-manager or external CA signing latency inside webhook: network path to PKI may dominate; distinguish from policy logic using hook implementation metrics from the operator namespace.

Case 10 — GitOps apply storm multiplies admission calls: throttle concurrent applies, shard repositories, or raise temporary budgets in k8s_webhook_latency_budget.csv with expiry notes.

Case 11 — Managed cloud control-plane maintenance: single-bucket spikes during provider windows may be benign; cross-check provider status before fail-closed changes.

Case 12 — Lookup gaps: rows defaulting owner_team platform_webhooks signal CSV drift; fix k8s_webhook_latency_budget.csv before production paging.

Operational cadence: weekly review top hooks by frac_wall_pct, monthly reconcile budgets with timeoutSeconds in git, quarterly rehearse slow-hook drills in lab, archive CSV exports of the closing table to a restricted evidence index.

FinOps note: hook name cardinality matters; FinOps should review label cardinality budgets quarterly.

Closing checklist: five em-dash step headers present exactly; Step 3 fenced SPL matches spl field; multisearch includes seven arms; eventstats (including cluster-level broadcast from aggregate marker rows), streamstats, coalesce, case, inputlookup, and tstats present; final table includes sixteen columns; monitoringType lists Performance and Capacity; cimModels lists Performance and Application_State; differentiation from UC-3.2.40, UC-3.2.45, and UC-3.2.19 is explicit in Step 1 and description.



## SPL

```spl
`comment("UC-3.2.21 Webhook latency-driven apiserver budget exhaustion. Tunables: index=k8s_metrics sourcetype=prometheus:scrape:metrics earliest=-30m@m latest=@m; lookup k8s_webhook_latency_budget.csv; shed_rpm_warn=5 frac_wall_warn=35")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | eval hook_type=lower(trim(toString(coalesce(type, hook_kind, webhook_type, ""))))
      | where mn="apiserver_admission_webhook_request_total" AND len(cluster)>0 AND len(hook_name)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats sum(mv) AS calls_5m BY cluster hook_name hook_type op win_time
      | eval wh_sum_sec=0
      | eval wh_cnt=0
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval internal_rej=0
      | eval shed_rpm=0
      | eval step_avg_ms=0
      | eval apiserver_wall_sec=0
      | eval lane="volume" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | eval hook_type=lower(trim(toString(coalesce(type, hook_kind, webhook_type, ""))))
      | where (mn="apiserver_admission_webhook_admission_duration_seconds_sum" OR mn="apiserver_admission_webhook_admission_duration_seconds_count") AND len(cluster)>0 AND len(hook_name)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats sum(eval(if(mn=="apiserver_admission_webhook_admission_duration_seconds_sum", mv, 0))) AS wh_sum_sec sum(eval(if(mn=="apiserver_admission_webhook_admission_duration_seconds_count", mv, 0))) AS wh_cnt BY cluster hook_name hook_type op win_time
      | eval calls_5m=0
      | eval hook_avg_ms=if(wh_cnt>0, round(1000*wh_sum_sec/wh_cnt, 3), 0)
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval internal_rej=0
      | eval shed_rpm=0
      | eval step_avg_ms=0
      | eval apiserver_wall_sec=0
      | eval lane="avg" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | eval hook_type=lower(trim(toString(coalesce(type, hook_kind, webhook_type, ""))))
      | eval le_raw=trim(toString(coalesce(le, le_label, "")))
      | where mn="apiserver_admission_webhook_admission_duration_seconds_bucket" AND len(cluster)>0 AND len(hook_name)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats max(mv) AS cum_at_le BY cluster hook_name hook_type op win_time le_raw
      | eval le_num=case(match(le_raw,"^\\+Inf$"), 1000000000, true(), tonumber(le_raw))
      | where isnotnull(le_num)
      | sort 0 cluster hook_name hook_type op win_time le_num
      | eventstats max(eval(if(match(le_raw,"^\\+Inf$"), cum_at_le, null()))) AS histo_total BY cluster hook_name hook_type op win_time
      | where isnotnull(histo_total) AND histo_total>0
      | eval hit50=if(cum_at_le>=(0.50*histo_total), le_num, null())
      | eval hit95=if(cum_at_le>=(0.95*histo_total), le_num, null())
      | eval hit99=if(cum_at_le>=(0.99*histo_total), le_num, null())
      | stats min(hit50) AS p50_le min(hit95) AS p95_le min(hit99) AS p99_le BY cluster hook_name hook_type op win_time
      | eval p50_ms=round(1000*coalesce(p50_le,0), 3)
      | eval p95_ms=round(1000*coalesce(p95_le,0), 3)
      | eval p99_ms=round(1000*coalesce(p99_le,0), 3)
      | eval calls_5m=0
      | eval wh_sum_sec=0
      | eval wh_cnt=0
      | eval hook_avg_ms=0
      | eval internal_rej=0
      | eval shed_rpm=0
      | eval step_avg_ms=0
      | eval apiserver_wall_sec=0
      | eval lane="histo" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval hook_name=lower(trim(toString(coalesce(name, webhook, admission_webhook, ""))))
      | eval op=lower(trim(toString(coalesce(operation, op, ""))))
      | eval hook_type=lower(trim(toString(coalesce(type, hook_kind, webhook_type, ""))))
      | eval et=lower(trim(toString(coalesce(error_type, err_type, ""))))
      | where mn="apiserver_admission_webhook_rejection_count" AND len(cluster)>0 AND len(hook_name)>0 AND like(et, "%apiserver_internal_error%")
      | bucket _time span=5m
      | eval win_time=_time
      | stats sum(mv) AS internal_rej BY cluster hook_name hook_type op win_time
      | eval calls_5m=0
      | eval wh_sum_sec=0
      | eval wh_cnt=0
      | eval hook_avg_ms=0
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval shed_rpm=0
      | eval step_avg_ms=0
      | eval apiserver_wall_sec=0
      | eval lane="rej" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval code=trim(tostring(coalesce(code, status_code, http_status, "")))
      | where mn="apiserver_request_total" AND len(cluster)>0 AND (code="429" OR code="504")
      | bucket _time span=5m
      | eval win_time=_time
      | stats sum(mv) AS shed_rpm BY cluster win_time
      | eval hook_name="_cluster_shed_"
      | eval hook_type="na"
      | eval op="na"
      | eval calls_5m=0
      | eval wh_sum_sec=0
      | eval wh_cnt=0
      | eval hook_avg_ms=0
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval internal_rej=0
      | eval step_avg_ms=0
      | eval apiserver_wall_sec=0
      | eval lane="shed" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | where (mn="apiserver_admission_step_admission_duration_seconds_sum" OR mn="apiserver_admission_step_admission_duration_seconds_count") AND len(cluster)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats sum(eval(if(mn=="apiserver_admission_step_admission_duration_seconds_sum", mv, 0))) AS step_sum sum(eval(if(mn=="apiserver_admission_step_admission_duration_seconds_count", mv, 0))) AS step_cnt BY cluster win_time
      | eval step_avg_ms=if(step_cnt>0, round(1000*step_sum/step_cnt, 3), 0)
      | eval hook_name="_cluster_step_"
      | eval hook_type="na"
      | eval op="na"
      | eval calls_5m=0
      | eval wh_sum_sec=0
      | eval wh_cnt=0
      | eval hook_avg_ms=0
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval internal_rej=0
      | eval shed_rpm=0
      | eval apiserver_wall_sec=0
      | eval lane="step" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | where mn="apiserver_request_duration_seconds_sum" AND len(cluster)>0
      | bucket _time span=5m
      | eval win_time=_time
      | stats sum(mv) AS apiserver_wall_sec BY cluster win_time
      | eval hook_name="_cluster_wall_"
      | eval hook_type="na"
      | eval op="na"
      | eval calls_5m=0
      | eval wh_sum_sec=0
      | eval wh_cnt=0
      | eval hook_avg_ms=0
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval internal_rej=0
      | eval shed_rpm=0
      | eval step_avg_ms=0
      | eval lane="wall" ]
| stats sum(calls_5m) AS calls_5m sum(wh_sum_sec) AS wh_sum_sec sum(wh_cnt) AS wh_cnt max(hook_avg_ms) AS hook_avg_ms max(p50_ms) AS p50_ms max(p95_ms) AS p95_ms max(p99_ms) AS p99_ms sum(internal_rej) AS internal_rej max(shed_rpm) AS shed_rpm max(step_avg_ms) AS step_avg_ms max(apiserver_wall_sec) AS apiserver_wall_sec BY cluster hook_name hook_type op win_time
| eval shed_seed=if(hook_name=="_cluster_shed_", shed_rpm, null())
| eval step_seed=if(hook_name=="_cluster_step_", step_avg_ms, null())
| eval wall_seed=if(hook_name=="_cluster_wall_", apiserver_wall_sec, null())
| eventstats max(shed_seed) AS shed_rpm_cluster BY cluster win_time
| eventstats max(step_seed) AS step_avg_ms_cluster BY cluster win_time
| eventstats max(wall_seed) AS apiserver_wall_cluster BY cluster win_time
| eval shed_rpm=coalesce(shed_rpm_cluster, 0)
| eval step_avg_ms=coalesce(step_avg_ms_cluster, 0)
| eval hook_avg_ms=coalesce(if(hook_avg_ms>0, hook_avg_ms, null()), if(wh_cnt>0, round(1000*wh_sum_sec/wh_cnt, 3), null()), 0)
| eval frac_wall_pct=if(apiserver_wall_cluster>0 AND wh_sum_sec>0 AND hook_name!="_cluster_shed_" AND hook_name!="_cluster_step_" AND hook_name!="_cluster_wall_", round(100*wh_sum_sec/apiserver_wall_cluster, 3), null())
| where hook_name!="_cluster_shed_" AND hook_name!="_cluster_step_" AND hook_name!="_cluster_wall_"
| eventstats perc95(p99_ms) AS cluster_hook_p99_p95 BY cluster win_time
| streamstats window=3 current=t global=f avg(hook_avg_ms) AS avg_ma3 BY cluster hook_name hook_type
| join type=left max=0 cluster hook_name
    [| inputlookup k8s_webhook_latency_budget.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval hook_name=lower(trim(toString(webhook_name)))
      | eval p99_budget_ms=tonumber(tostring(coalesce(p99_budget_ms, budget_ms, "1000")), 10)
      | eval owner_team=trim(toString(coalesce(owner_team, squad, "platform_webhooks")))
      | fields cluster hook_name p99_budget_ms owner_team ]
| fillnull value=1000 p99_budget_ms
| fillnull value="platform_webhooks" owner_team
| join type=left max=0 cluster
    [| tstats summariesonly=t latest(Application_State.info) AS cim_app_state FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
      | rename Application_State.dest AS cluster ]
| eval budget_ms=coalesce(p99_budget_ms, 1000)
| eval severity_tier=case(
    shed_rpm>=20 AND p99_ms>=budget_ms, "critical",
    internal_rej>=3 OR (p99_ms>=budget_ms AND coalesce(frac_wall_pct,0)>=45), "critical",
    p99_ms>=round(0.95*budget_ms,0) OR coalesce(frac_wall_pct,0)>=35 OR shed_rpm>=5, "high",
    p95_ms>=round(0.85*budget_ms,0) OR cluster_hook_p99_p95>=budget_ms OR shed_rpm>=2, "medium",
    avg_ma3>=round(0.75*budget_ms,0) OR coalesce(frac_wall_pct,0)>=20, "low",
    true(), "info")
| where severity_tier IN ("critical","high","medium","low")
| table cluster win_time hook_name hook_type op calls_5m avg_ma3 p50_ms p95_ms p99_ms budget_ms frac_wall_pct shed_rpm step_avg_ms internal_rej severity_tier owner_team cim_app_state
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS cim_cluster
| join type=left max=0 cim_cluster
    [| tstats summariesonly=t avg(Performance.cpu_load_percent) AS cpu_pct FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-4h@h latest=@h BY Performance.host
     | rename Performance.host AS cim_cluster ]
| table cim_cluster app_state app_info cpu_pct
```

## Visualization

Timechart of p50_ms p95_ms p99_ms and avg_ma3 by hook_name; single-value tiles for shed_rpm and max frac_wall_pct; severity-colored table mirroring the SPL closing projection; companion panel listing hooks sorted by wh_sum_sec over apiserver_wall_sec.

## Known False Positives

Legitimately slow hooks exist by design: Kyverno may compile policies on first invocation; OPA Gatekeeper may reload constraint templates after Git sync; cert-manager or corporate CA webhooks may wait on external signing round trips; license or entitlement checks may call outside the cluster; cold caches after upgrade or image rollouts routinely elevate P99 for one or two scrape windows; webhooks scaled to zero briefly during voluntary disruption budgets mirror latency spikes without sustained budget burn; path MTU or asymmetric routing can inflate round-trip time so the symptom looks webhook-bound while the root cause is network; teams sometimes set timeoutSeconds deliberately high for batch jobs, which masks tail risk until concurrent admission storms arrive; rare huge ConfigMap or Secret admissions stress JSON patch paths and look like chronic slowness; in-cluster API calls during certificate rotation may stall hooks; operator-driven mass updates create admission bursts that resemble chronic regression; compliance gates may intentionally block with long-running validations; brief startup probe failures on webhook pods can look like latency cliffs until readiness stabilizes. Require sustained elevation across multiple five-minute buckets, corroborate with shed_rpm or internal_rej, and cross-check change records before paging production bridges.

## References

- [Kubernetes — Dynamic Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)
- [Kubernetes Metrics Reference (kube-apiserver)](https://kubernetes.io/docs/reference/instrumentation/metrics/)
- [kube-state-metrics — README](https://github.com/kubernetes/kube-state-metrics/blob/main/README.md)
- [Kubernetes — API Priority and Fairness](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/)
- [Kubernetes API — MutatingWebhookConfiguration v1](https://kubernetes.io/docs/reference/kubernetes-api/extend-resources/mutating-webhook-configuration-v1/)
- [Kubernetes SIG Auth — Admission signals](https://github.com/kubernetes/community/blob/master/sig-auth/signals/admission/README.md)
- [controller-runtime — Manager and metrics](https://github.com/kubernetes-sigs/controller-runtime/blob/main/pkg/manager/manager.go)
- [Splunk — Add-on for Kubernetes](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
