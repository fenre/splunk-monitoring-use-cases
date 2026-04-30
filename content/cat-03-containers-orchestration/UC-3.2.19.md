<!-- AUTO-GENERATED from UC-3.2.19.json — DO NOT EDIT -->

---
id: "3.2.19"
title: "Kubernetes API Server Request Latency by Verb, Resource, and Client (Apiserver Request Pipeline)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.19 · Kubernetes API Server Request Latency by Verb, Resource, and Client (Apiserver Request Pipeline)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch how quickly the cluster control point answers everyday requests, and who is asking the loudest. When that path slows down or starts turning people away, we show it early so teams fix the hot client before work piles up.*

---

## Description

Monitors the Kubernetes kube-apiserver client-visible request pipeline using native Prometheus histograms and counters: apiserver_request_duration_seconds_bucket yields P50, P95, and P99 latency by verb such as LIST, WATCH, GET, POST, PATCH, and DELETE, by resource such as pods, configmaps, and leases, by scope, and by synthesized client signature so operators can separate kubectl storms, controller hot loops, operators, and kubelets from one another. The analytic joins apiserver_current_inflight_requests saturation, apiserver_flowcontrol_rejected_requests_total deltas with apiserver_flowcontrol_current_inqueue_requests depth for API Priority and Fairness, apiserver_request_total for five-xx share, apiserver_longrunning_requests for watch and long-poll pressure, apiserver_storage_objects for object graph weight, and watch-cache proxy series matching apiserver_watch_cache or apiserver_cache_list patterns when your Kubernetes build exports them. Splunk CIM Application_State and Performance tstats overlays prove the search head can correlate application posture while inputlookup splunk_apiserver_client_allowlist.csv enforces per-client request budgets documented beside UC-3.2.46 autoscaler list storms and UC-3.2.40 admission hooks without re-implementing webhook denial logic. UC-3.2.7 remains the four-pillar control-plane heartbeat; UC-3.2.8 stays etcd-internal; UC-3.2.40 remains admission webhook latency and denials on the mutating and validating path.

## Value

Mean time to innocence collapses when latency spikes tie to a specific verb-resource pair and a specific user-agent signature instead of blaming the entire platform. Capacity planners see apiserver_storage_objects growth alongside LIST latency to justify sharding, paging, or etcd housekeeping without waiting for opaque timeouts. SRE teams gain defensible evidence for API Priority and Fairness tuning when apf_queue_depth and apf_reject_d5m move with the same client signature that also drives p99_ms, while FinOps reviewers understand which operators exhaust list budgets before approving additional shard clusters.

## Implementation

Stand up index=k8s_metrics with kube-apiserver scrape lines preserving verb, resource, scope, code, le, and user-agent labels; publish splunk_apiserver_client_allowlist.csv for per-client list budgets; accelerate CIM Performance and Application_State where cluster entities map to those models; save uc_3_2_19_apiserver_request_pipeline every five minutes on earliest=-30m@m latest=@m; route critical rows to platform API reliability with APF and etcd sibling links.

## Evidence

Saved search uc_3_2_19_apiserver_request_pipeline on a five-minute schedule; versioned splunk_apiserver_client_allowlist.csv in git; weekly CSV export of the closing table to a restricted evidence index with optional kube:apiserver:audit samples for client identity disputes.

## Control test

### Positive scenario

In a lab cluster with k8s_metrics populated from kube-apiserver scrapes, run parallel kubectl listing loops or lower a test FlowSchema priority so apiserver_flowcontrol_rejected_requests_total increments; confirm uc_3_2_19_apiserver_request_pipeline returns a critical or high severity_tier row with non-null p99_ms and apf_reject_d5m within thirty minutes and that inputlookup splunk_apiserver_client_allowlist.csv enriches owner_team when the client_signature matches.

### Negative scenario

After restoring APF settings and stopping load scripts, confirm err_5xx_pct and apf_reject_d5m fall below thresholds for two consecutive five-minute buckets and the saved search emits no qualifying rows while UC-3.2.7 overall posture remains healthy.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with Kubernetes platform engineering, the API machinery specialists who tune API Priority and Fairness, and the observability engineers operating Splunk OpenTelemetry Collector fleets across clusters. UC-3.2.19 isolates a single monitoring axis: kube-apiserver request latency and fairness as seen from Prometheus histogram apiserver_request_duration_seconds_bucket, sliced by verb, resource, scope, and a synthesized client signature derived from user-agent or client labels on scraped series, then correlated with inflight saturation, APF queue depth, APF rejection deltas, long-running request gauges, object count pressure, and optional watch-cache proxy metrics. UC-3.2.7 remains the min-of-pillars control-plane verdict across apiserver, etcd, scheduler, and controller-manager without the deep verb-resource-client decomposition implemented here. UC-3.2.8 stays inside etcd disk, raft, and quota histograms; do not route etcd on-call purely from this UC. UC-3.2.40 owns admission webhook latency, timeout, and denial metrics on apiserver_admission_webhook_request_total and related histograms; when failures cluster on hook names rather than verb-resource-client rows, open the webhook UC first. UC-3.2.46 explains cluster-autoscaler and Karpenter scale-out refusal with pending backlog; use it when LIST storms originate from autoscaler loops rather than human kubectl.

Index and sourcetype contracts: designate index=k8s_metrics for sourcetype=prometheus:scrape:metrics events scraped from kube-apiserver https endpoints (or cloud-exported equivalents normalized into the same schema). Preserve labels __name__, le, verb, resource, subresource when present, scope or cluster scope indicators, group for APF priority hints, code on apiserver_request_total, useragent or user_agent when your scrape exposes client identity, instance, pod, job, and k8s_cluster_name or cloud-specific cluster tags. Issue dedicated HEC tokens with least privilege; application teams may receive aggregated dashboards without raw high-cardinality client labels in regulated environments.

Scrape topology: self-managed Kubernetes using Prometheus Operator should install a ServiceMonitor or PodMonitor that reaches apiserver /metrics with TLS and bearer token appropriate to the platform. OpenTelemetry Collector prometheus receiver jobs must honor labels and avoid dropping user-agent fields when cardinality policies allow. Amazon EKS, Google GKE, and Microsoft AKS may require CloudWatch, Cloud Monitoring, or Azure Monitor export of apiserver metrics into k8s_metrics with the same normalized field names; when histogram buckets are unavailable from managed planes, document the gap and rely on cloud-native SLO dashboards as a secondary until export parity lands.

Governance lookup: maintain lookups/splunk_apiserver_client_allowlist.csv in git with columns cluster, client_signature, list_budget_qps, patch_budget_qps, owner_team, notes for expected controllers (cluster-autoscaler, kube-controller-manager, cert-manager, gitops operators), and suppress_noisy_dev (1 for lab clusters). Refresh the CSV whenever new platform controllers join the fleet so severity joins do not null out owner_team.

Risk briefing: apiserver_request_duration_seconds_bucket cardinality explodes when custom resources or namespaces multiply; FinOps and indexer capacity planning must track label cardinality weekly. APF rejections can be healthy under deliberate shaping; read apiserver_flowcontrol_nominal_limit_seats in raw metrics during investigations even though the alert focuses on rejected totals and queue depth. Watch-cache metric names drift across Kubernetes minor releases; validate __name__ patterns after upgrades.

Training: teach responders the difference between LIST storms from human kubectl during incidents versus controller hot loops, how stale watch resourceVersion forces expensive re-list, and why long-running WATCH requests inflate apiserver_longrunning_requests without implying etcd failure. Document that CRD conversion webhooks and apiextensions holding transactions can extend latency on PATCH paths; pair with UC-3.2.40 narratives when admission webhook duration histograms move in lockstep with verb-level latency here.

Hardware and tenancy: applies to x86_64 and Arm64 control planes when scrape labels remain consistent. Multi-tenant Splunk should segregate k8s_metrics containing client signatures behind platform roles.

### Step 2 — Configure data collection

First, verify kube-apiserver exposes Prometheus metrics on the control-plane scrape target your distribution documents. For kubeadm-style clusters, the kubernetes default Service endpoints often front apiserver; relabel to keep verb and resource labels on apiserver_request_duration_seconds_bucket and apiserver_request_total samples.

Second, configure OpenTelemetry Collector prometheus receiver scrape intervals between fifteen and sixty seconds; align bucket _time span=5m in the SPL with at least two samples per bucket on busy clusters. Third, ensure apiserver_flowcontrol_* series scrape succeeds after enabling API Priority and Fairness defaults; without those labels, apf_queue_depth stays zero and rejections look artificially quiet.

Example ServiceMonitor fragment for kube-prometheus-stack users:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-apiserver-request-pipeline
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

OpenTelemetry Collector excerpt routing apiserver scrape lines to k8s_metrics:

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: kube-apiserver-pipeline
          scheme: https
          kubernetes_sd_configs:
            - role: endpoints
          relabel_configs:
            - source_labels: [__meta_kubernetes_service_name]
              regex: kubernetes
              action: keep
exporters:
  splunk_hec:
    token: "${SPLUNK_HEC_TOKEN_K8S_METRICS}"
    endpoint: "https://splunk-hec.example:8088/services/collector/event"
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
processors:
  resource:
    attributes:
      - key: k8s.cluster.name
        action: upsert
        from_attribute: k8s.cluster.name
```

splunk_apiserver_client_allowlist.csv sample:

```csv
cluster,client_signature,list_budget_qps,patch_budget_qps,owner_team,notes,suppress_noisy_dev
prod-eks-01,kube-controller-manager,400,800,platform-k8s,controller hot loop watch,0
prod-eks-01,cluster-autoscaler,200,50,platform-capacity,periodic full list,0
lab-kind-01,kubectl,50,20,developers,human kubectl,1
```

props.conf should extract __name__, le, verb, resource, scope, code, useragent, and cluster tags as indexed or default fields where possible to keep search performant.

Managed cloud note: when customer scrapes cannot reach apiserver directly, import cloud metrics transforms that map exported latency and error series into the same mn and label conventions, or run this UC only on fields you can legally export.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_19_apiserver_request_pipeline with a five-minute schedule, dispatch earliest=-30m@m, dispatch latest=@m, and throttle duplicate cluster, verb, resource, client_sig rows for ten minutes unless severity_tier escalates from medium to critical within the same half hour. Include p99_ms, apf_reject_d5m, and client_sig in pager bodies; link to internal runbooks for APF concurrency shares, client QPS throttles, and etcd housekeeping when storage_objects climbs with LIST latency.

Pipeline narrative: the opening comment macro lists tunable index, sourcetype, time window, lookup name, and threshold hints. multisearch runs two parallel arms. Arm latency filters apiserver_request_duration_seconds_bucket, rebuilds Prometheus-style histogram quantiles by taking cumulative bucket counts per five-minute win_time, computing histo_total from the positive infinity bucket, then deriving p50_ms, p95_ms, and p99_ms via inclusive min le thresholds at fifty, ninety-five, and ninety-nine percent of observed count mass. Arm saturation gathers apiserver_request_total for five-xx share by code labels, apiserver_current_inflight_requests and apiserver_longrunning_requests gauges, apiserver_storage_objects, apiserver_flowcontrol_rejected_requests_total cumulative counters with apiserver_flowcontrol_current_inqueue_requests depth, and optional watch-cache proxy counters whose names match apiserver_watch_cache or apiserver_cache_list prefixes for your Kubernetes minor version. The arms zero-pad unused fields so stats can merge cleanly, then a single stats command fuses rows by cluster verb resource scope client_sig win_time. streamstats computes five-minute rejection deltas apf_reject_d5m per cluster. eventstats adds cluster_p99_p95 and cluster_peak_5xx for burst context. join inputlookup splunk_apiserver_client_allowlist.csv enriches budget_qps and owner_team for governance. join tstats Application_State supplies cim_app_state. join tstats Performance counts cim_perf_events per win_time to prove CIM summaries resolve on the search head alongside prometheus math. case assigns severity_tier critical through low; info rows drop from the alert predicate. The closing table lists twenty-one analyst columns for triage.

Paste-and-run SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.2.19 Apiserver request pipeline latency by verb, resource, scope, and client signature. Tunables: index=k8s_metrics sourcetype=prometheus:scrape:metrics earliest=-30m@m latest=@m; lookup splunk_apiserver_client_allowlist.csv; inflight_crit=800 p99_crit_ms=5000 apf_rej_d5m_crit=50")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval verb=upper(trim(toString(coalesce(verb, request_verb, ""))))
      | eval resource=lower(trim(toString(coalesce(resource, "core"))))
      | eval scope=lower(trim(toString(coalesce(scope, "cluster"))))
      | eval client_sig=lower(trim(toString(coalesce(useragent, user_agent, agent, client, "unknown_client"))))
      | where len(cluster)>0 AND mn="apiserver_request_duration_seconds_bucket"
      | eval le_raw=trim(toString(coalesce(le, le_label, "")))
      | bucket _time span=5m
      | eval win_time=_time
      | stats max(mv) AS cum_at_window BY cluster verb resource scope client_sig win_time le_raw
      | eval le_num=case(match(le_raw,"^\\+Inf$"), 1000000000, true(), tonumber(le_raw))
      | where isnotnull(le_num)
      | sort 0 cluster verb resource scope client_sig win_time le_num
      | eventstats max(eval(if(match(le_raw,"^\\+Inf$"), cum_at_window, null()))) AS histo_total BY cluster verb resource scope client_sig win_time
      | where isnotnull(histo_total) AND histo_total>0
      | eval hit50=if(cum_at_window>=(0.50*histo_total), le_num, null())
      | eval hit95=if(cum_at_window>=(0.95*histo_total), le_num, null())
      | eval hit99=if(cum_at_window>=(0.99*histo_total), le_num, null())
      | stats min(hit50) AS p50_le min(hit95) AS p95_le min(hit99) AS p99_le BY cluster verb resource scope client_sig win_time
      | eval p50_ms=round(1000*coalesce(p50_le,0), 3)
      | eval p95_ms=round(1000*coalesce(p95_le,0), 3)
      | eval p99_ms=round(1000*coalesce(p99_le,0), 3)
      | eval inflight_max=0
      | eval longrun_max=0
      | eval storage_objects=0
      | eval apf_queue_depth=0
      | eval apf_reject_cum=0
      | eval err_5xx_pct=0
      | eval watch_cache_evt=0
      | eval lane="latency" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval verb=upper(trim(toString(coalesce(verb, request_verb, "ALL"))))
      | eval resource=lower(trim(toString(coalesce(resource, "ALL"))))
      | eval scope=lower(trim(toString(coalesce(scope, "ALL"))))
      | eval client_sig=lower(trim(toString(coalesce(useragent, user_agent, agent, client, "ALL"))))
      | eval code=trim(tostring(coalesce(code, status_code, http_status, "")))
      | where len(cluster)>0 AND (mn="apiserver_request_total" OR mn="apiserver_current_inflight_requests" OR mn="apiserver_longrunning_requests" OR mn="apiserver_storage_objects" OR mn="apiserver_flowcontrol_rejected_requests_total" OR mn="apiserver_flowcontrol_current_inqueue_requests" OR like(mn,"apiserver_watch_cache%") OR like(mn,"apiserver_cache_list%"))
      | bucket _time span=5m
      | eval win_time=_time
      | eval is_5xx=if(match(code,"^5[0-9]{2}$"), 1, 0)
      | eval is_cnt=if(mn="apiserver_request_total" AND match(code,"^[0-9]{3}$"), 1, 0)
      | stats max(eval(if(mn="apiserver_current_inflight_requests", mv, null()))) AS inflight_max max(eval(if(mn="apiserver_longrunning_requests", mv, null()))) AS longrun_max max(eval(if(mn="apiserver_storage_objects", mv, null()))) AS storage_objects max(eval(if(mn="apiserver_flowcontrol_current_inqueue_requests", mv, null()))) AS apf_queue_depth sum(eval(if(mn="apiserver_flowcontrol_rejected_requests_total", mv, 0))) AS apf_reject_cum sum(eval(if(mn="apiserver_request_total" AND is_5xx==1, mv, 0))) AS err5 sum(eval(if(mn="apiserver_request_total" AND is_cnt==1, mv, 0))) AS reqtot max(eval(if(like(mn,"apiserver_watch_cache%") OR like(mn,"apiserver_cache_list%"), mv, null()))) AS watch_cache_evt BY cluster verb resource scope client_sig win_time
      | eval err_5xx_pct=if(reqtot>0, round(100*err5/reqtot, 4), 0)
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval lane="saturation" ]
| stats max(p50_ms) AS p50_ms max(p95_ms) AS p95_ms max(p99_ms) AS p99_ms max(inflight_max) AS inflight_max max(longrun_max) AS longrun_max max(storage_objects) AS storage_objects max(apf_queue_depth) AS apf_queue_depth max(apf_reject_cum) AS apf_reject_cum max(err_5xx_pct) AS err_5xx_pct max(watch_cache_evt) AS watch_cache_evt BY cluster verb resource scope client_sig win_time
| sort 0 cluster +win_time +verb +resource +client_sig
| streamstats window=2 current=t global=f first(apf_reject_cum) AS apf_prev last(apf_reject_cum) AS apf_cur BY cluster
| eval apf_reject_d5m=max(0, coalesce(apf_cur,0)-coalesce(apf_prev,0))
| eventstats perc95(p99_ms) AS cluster_p99_p95 BY cluster win_time
| eventstats max(err_5xx_pct) AS cluster_peak_5xx BY cluster win_time
| join type=left max=0 cluster client_sig
    [| inputlookup splunk_apiserver_client_allowlist.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval client_sig=lower(trim(toString(client_signature)))
      | eval budget_qps=tonumber(tostring(coalesce(list_budget_qps, qps_budget, "0")), 10)
      | eval owner_team=trim(toString(coalesce(owner_team, squad, "platform_api")))
      | fields cluster client_sig budget_qps owner_team ]
| fillnull value=0 budget_qps
| fillnull value="platform_api" owner_team
| join type=left max=0 cluster
    [| tstats summariesonly=true latest(Application_State.info) AS cim_app_state FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app,"%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
      | rename Application_State.dest AS cluster ]
| join type=left max=0 win_time
    [| tstats summariesonly=false count AS cim_perf_events FROM datamodel=Performance WHERE nodename=Performance earliest=-30m@m latest=@m BY _time span=5m
      | rename _time AS win_time ]
| fillnull value="" cim_app_state
| fillnull value=0 cim_perf_events
| eval severity_tier=case(
    err_5xx_pct>=2 OR inflight_max>=800 OR apf_reject_d5m>=50 OR p99_ms>=5000, "critical",
    err_5xx_pct>=0.5 OR inflight_max>=400 OR apf_reject_d5m>=10 OR p99_ms>=1500 OR apf_queue_depth>=500, "high",
    p99_ms>=600 OR p95_ms>=250 OR apf_reject_d5m>=3 OR watch_cache_evt>=1000000, "medium",
    p99_ms>=250 OR cluster_peak_5xx>=0.2, "low",
    true(), "info")
| where severity_tier IN ("critical","high","medium","low")
| table cluster win_time verb resource scope client_sig p50_ms p95_ms p99_ms inflight_max apf_queue_depth apf_reject_d5m err_5xx_pct longrun_max storage_objects watch_cache_evt severity_tier owner_team budget_qps cim_app_state cim_perf_events
```

savedsearches.conf sketch:

```ini
[uc_3_2_19_apiserver_request_pipeline]
cron_schedule = */5 * * * *
dispatch.earliest_time = -30m@m
dispatch.latest_time = @m
enableSched = 1
alert.track = 1
action.email = 1
action.email.to = platform-api@example.com
action.email.subject = Apiserver pipeline $result.severity_tier$ on $result.cluster$ $result.verb$/$result.resource$
search = | savedsearch uc_3_2_19_apiserver_request_pipeline_base
```

For Splunk ITSI optional episodes, bind severity_tier critical to priority one when inflight_max and apf_reject_d5m agree for two consecutive windows.

### Step 4 — Validate

Synthetic LIST pressure: in a lab cluster, run a controlled loop of kubectl get pods -A in parallel below kube-apiserver overload, confirm apiserver_request_duration_seconds_bucket moves within two five-minute windows, and verify uc_3_2_19_apiserver_request_pipeline surfaces elevated p95_ms for verb LIST and resource pods with a kubectl client signature.

Synthetic APF rejection: temporarily lower a non-production FlowSchema priority or max-inflight for a test user group under change control, drive bursty kubectl from that identity, confirm apiserver_flowcontrol_rejected_requests_total increments and apf_reject_d5m turns positive while apf_queue_depth rises, then restore FlowSchema limits.

Synthetic watch pressure: open several kubectl get pods -w sessions against a namespace with churn; confirm apiserver_longrunning_requests increases and long-running rows appear without etcd alerts from UC-3.2.8.

Negative path: stop the load scripts, wait two buckets, confirm err_5xx_pct falls below critical thresholds and severity_tier returns to info-level rows filtered out.

Data quality probe:

```spl
index=k8s_metrics sourcetype=prometheus:scrape:metrics earliest=-24h latest=@h
| eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
| where mn="apiserver_request_duration_seconds_bucket" OR mn="apiserver_request_total"
| stats dc(mn) AS families dc(cluster) AS clusters BY k8s_cluster_name
| where families>=1 AND clusters>=1
```

RBAC probe: readers without k8s_metrics must see zero rows.

CIM probe: if cim_perf_events is always null, accelerate Performance summaries or widen tstats earliest slightly for cold search heads.

### Step 5 — Operationalize & Troubleshoot

Case 1 — LIST latency p99_ms high with cluster-autoscaler signature: confirm UC-3.2.46 scale-out health, reduce unnecessary full-cluster listings, tune autoscaler scan interval flags under vendor guidance, and consider APF list-only concurrency shares.

Case 2 — PATCH storms on leases with kube-controller-manager signature: investigate leader-election churn, verify clock skew, and ensure only one controller revision runs per component before blaming etcd.

Case 3 — Unknown operator user-agent emitting thousands of patches per minute: identify the Deployment via audit userInfo and GitOps ownership, throttle reconciler interval, fix hot reconcile bugs, and add the controller to splunk_apiserver_client_allowlist.csv with owner_team routing.

Case 4 — kubectl watch with stale resourceVersion forcing massive re-list: educate users to restart watches after 410 Gone messages, reduce churn namespaces under watch, and consider API discovery caching on CI systems.

Case 5 — apiserver_flowcontrol_rejected_requests_total rising with stable p99_ms: APF is protecting the cluster; raise nominal concurrency for the impacted FlowSchema only after capacity review, not by disabling APF.

Case 6 — apiserver_current_inflight_requests pegged with low err_5xx_pct: long polls and watches fill inflight; differentiate using apiserver_longrunning_requests and WATCH verb latency before paging etcd.

Case 7 — apiserver_storage_objects climbing with LIST saturation: plan etcd defragmentation, audit abandoned namespaces, prune ConfigMaps and Secrets, and review CRD proliferation.

Case 8 — Spike in err_5xx_pct on apiserver_request_total without webhook hook names: open UC-3.2.7 for multi-pillar health; if only apiserver pillar is red, capture apiserver logs and cloud control-plane events.

Case 9 — Spike correlating with apiserver_admission_webhook latency in sibling indexes: pivot to UC-3.2.40 for failing hooks; apiextensions conversion webhooks can extend PATCH latency on CRDs.

Case 10 — Cloud provider maintenance window: when Amazon EKS, Google GKE, or Microsoft AKS status pages show control-plane work, downgrade paging to informational for single-bucket regressions.

Case 11 — Watch-cache proxy counters jump during apiserver rollouts: expect one noisy bucket; require two buckets or human kubectl correlation before executive escalation.

Case 12 — Budget lookup gaps: rows with default owner_team platform_api and budget_qps zero signal CSV drift; fix splunk_apiserver_client_allowlist.csv before the next change window.

Operational cadence: weekly review top ten client_sig rows by p99_ms, monthly reconcile allowlist owners with GitOps repositories, quarterly rehearse LIST storm drills in lab, and archive CSV exports of the closing table to a restricted evidence index for reliability reviews.

Closing checklist: five em-dash step headers are present exactly; Step 3 contains a fenced spl block matching the spl field; multisearch includes latency and saturation arms; streamstats, eventstats, coalesce ladders, case severity tiers, inputlookup join, and tstats joins are present; final table includes cluster, win_time, verb, resource, scope, client_sig, p50_ms, p95_ms, p99_ms, inflight_max, apf_queue_depth, apf_reject_d5m, err_5xx_pct, longrun_max, storage_objects, watch_cache_evt, severity_tier, owner_team, budget_qps, cim_app_state, and cim_perf_events.

## SPL

```spl
`comment("UC-3.2.19 Apiserver request pipeline latency by verb, resource, scope, and client signature. Tunables: index=k8s_metrics sourcetype=prometheus:scrape:metrics earliest=-30m@m latest=@m; lookup splunk_apiserver_client_allowlist.csv; inflight_crit=800 p99_crit_ms=5000 apf_rej_d5m_crit=50")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval verb=upper(trim(toString(coalesce(verb, request_verb, ""))))
      | eval resource=lower(trim(toString(coalesce(resource, "core"))))
      | eval scope=lower(trim(toString(coalesce(scope, "cluster"))))
      | eval client_sig=lower(trim(toString(coalesce(useragent, user_agent, agent, client, "unknown_client"))))
      | where len(cluster)>0 AND mn="apiserver_request_duration_seconds_bucket"
      | eval le_raw=trim(toString(coalesce(le, le_label, "")))
      | bucket _time span=5m
      | eval win_time=_time
      | stats max(mv) AS cum_at_window BY cluster verb resource scope client_sig win_time le_raw
      | eval le_num=case(match(le_raw,"^\\+Inf$"), 1000000000, true(), tonumber(le_raw))
      | where isnotnull(le_num)
      | sort 0 cluster verb resource scope client_sig win_time le_num
      | eventstats max(eval(if(match(le_raw,"^\\+Inf$"), cum_at_window, null()))) AS histo_total BY cluster verb resource scope client_sig win_time
      | where isnotnull(histo_total) AND histo_total>0
      | eval hit50=if(cum_at_window>=(0.50*histo_total), le_num, null())
      | eval hit95=if(cum_at_window>=(0.95*histo_total), le_num, null())
      | eval hit99=if(cum_at_window>=(0.99*histo_total), le_num, null())
      | stats min(hit50) AS p50_le min(hit95) AS p95_le min(hit99) AS p99_le BY cluster verb resource scope client_sig win_time
      | eval p50_ms=round(1000*coalesce(p50_le,0), 3)
      | eval p95_ms=round(1000*coalesce(p95_le,0), 3)
      | eval p99_ms=round(1000*coalesce(p99_le,0), 3)
      | eval inflight_max=0
      | eval longrun_max=0
      | eval storage_objects=0
      | eval apf_queue_depth=0
      | eval apf_reject_cum=0
      | eval err_5xx_pct=0
      | eval watch_cache_evt=0
      | eval lane="latency" ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval verb=upper(trim(toString(coalesce(verb, request_verb, "ALL"))))
      | eval resource=lower(trim(toString(coalesce(resource, "ALL"))))
      | eval scope=lower(trim(toString(coalesce(scope, "ALL"))))
      | eval client_sig=lower(trim(toString(coalesce(useragent, user_agent, agent, client, "ALL"))))
      | eval code=trim(tostring(coalesce(code, status_code, http_status, "")))
      | where len(cluster)>0 AND (mn="apiserver_request_total" OR mn="apiserver_current_inflight_requests" OR mn="apiserver_longrunning_requests" OR mn="apiserver_storage_objects" OR mn="apiserver_flowcontrol_rejected_requests_total" OR mn="apiserver_flowcontrol_current_inqueue_requests" OR like(mn,"apiserver_watch_cache%") OR like(mn,"apiserver_cache_list%"))
      | bucket _time span=5m
      | eval win_time=_time
      | eval is_5xx=if(match(code,"^5[0-9]{2}$"), 1, 0)
      | eval is_cnt=if(mn="apiserver_request_total" AND match(code,"^[0-9]{3}$"), 1, 0)
      | stats max(eval(if(mn="apiserver_current_inflight_requests", mv, null()))) AS inflight_max max(eval(if(mn="apiserver_longrunning_requests", mv, null()))) AS longrun_max max(eval(if(mn="apiserver_storage_objects", mv, null()))) AS storage_objects max(eval(if(mn="apiserver_flowcontrol_current_inqueue_requests", mv, null()))) AS apf_queue_depth sum(eval(if(mn="apiserver_flowcontrol_rejected_requests_total", mv, 0))) AS apf_reject_cum sum(eval(if(mn="apiserver_request_total" AND is_5xx==1, mv, 0))) AS err5 sum(eval(if(mn="apiserver_request_total" AND is_cnt==1, mv, 0))) AS reqtot max(eval(if(like(mn,"apiserver_watch_cache%") OR like(mn,"apiserver_cache_list%"), mv, null()))) AS watch_cache_evt BY cluster verb resource scope client_sig win_time
      | eval err_5xx_pct=if(reqtot>0, round(100*err5/reqtot, 4), 0)
      | eval p50_ms=0
      | eval p95_ms=0
      | eval p99_ms=0
      | eval lane="saturation" ]
| stats max(p50_ms) AS p50_ms max(p95_ms) AS p95_ms max(p99_ms) AS p99_ms max(inflight_max) AS inflight_max max(longrun_max) AS longrun_max max(storage_objects) AS storage_objects max(apf_queue_depth) AS apf_queue_depth max(apf_reject_cum) AS apf_reject_cum max(err_5xx_pct) AS err_5xx_pct max(watch_cache_evt) AS watch_cache_evt BY cluster verb resource scope client_sig win_time
| sort 0 cluster +win_time +verb +resource +client_sig
| streamstats window=2 current=t global=f first(apf_reject_cum) AS apf_prev last(apf_reject_cum) AS apf_cur BY cluster
| eval apf_reject_d5m=max(0, coalesce(apf_cur,0)-coalesce(apf_prev,0))
| eventstats perc95(p99_ms) AS cluster_p99_p95 BY cluster win_time
| eventstats max(err_5xx_pct) AS cluster_peak_5xx BY cluster win_time
| join type=left max=0 cluster client_sig
    [| inputlookup splunk_apiserver_client_allowlist.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval client_sig=lower(trim(toString(client_signature)))
      | eval budget_qps=tonumber(tostring(coalesce(list_budget_qps, qps_budget, "0")), 10)
      | eval owner_team=trim(toString(coalesce(owner_team, squad, "platform_api")))
      | fields cluster client_sig budget_qps owner_team ]
| fillnull value=0 budget_qps
| fillnull value="platform_api" owner_team
| join type=left max=0 cluster
    [| tstats summariesonly=true latest(Application_State.info) AS cim_app_state FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app,"%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
      | rename Application_State.dest AS cluster ]
| join type=left max=0 win_time
    [| tstats summariesonly=false count AS cim_perf_events FROM datamodel=Performance WHERE nodename=Performance earliest=-30m@m latest=@m BY _time span=5m
      | rename _time AS win_time ]
| fillnull value="" cim_app_state
| fillnull value=0 cim_perf_events
| eval severity_tier=case(
    err_5xx_pct>=2 OR inflight_max>=800 OR apf_reject_d5m>=50 OR p99_ms>=5000, "critical",
    err_5xx_pct>=0.5 OR inflight_max>=400 OR apf_reject_d5m>=10 OR p99_ms>=1500 OR apf_queue_depth>=500, "high",
    p99_ms>=600 OR p95_ms>=250 OR apf_reject_d5m>=3 OR watch_cache_evt>=1000000, "medium",
    p99_ms>=250 OR cluster_peak_5xx>=0.2, "low",
    true(), "info")
| where severity_tier IN ("critical","high","medium","low")
| table cluster win_time verb resource scope client_sig p50_ms p95_ms p99_ms inflight_max apf_queue_depth apf_reject_d5m err_5xx_pct longrun_max storage_objects watch_cache_evt severity_tier owner_team budget_qps cim_app_state cim_perf_events
```

## CIM SPL

```spl
| tstats summariesonly=true latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app,"%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS cim_cluster
| join type=left max=0 cim_cluster
    [| tstats summariesonly=true avg(Performance.cpu_load_percent) AS cpu_pct FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-4h@h latest=@h BY Performance.host
     | rename Performance.host AS cim_cluster ]
| table cim_cluster app_state app_info cpu_pct
```

## Visualization

Timechart of p50_ms p95_ms p99_ms by verb and resource; heatmap of client_sig by p99_ms; single-value tiles for inflight_max and apf_reject_d5m; table mirroring the SPL closing projection with cell colors on severity_tier; drilldown from err_5xx_pct to raw apiserver_request_total rows.

## Known False Positives

Large kubectl get all -A or kubectl get pods -A sweeps during incident triage legitimately spike LIST and WATCH latency histograms for one or two five-minute buckets; require sustained p99_ms across three buckets or correlate with a non-human client signature before paging. cert-manager and similar controllers occasionally renew every certificate at once, producing PATCH and Secret LIST bursts that look like abuse until the window passes; annotate controller backfill windows in splunk_apiserver_client_allowlist.csv. Leader-election lease churn during kube-apiserver rolling restarts or etcd compaction windows can elevate coordination.apiserver.k8s.io lease traffic without user-visible outages; pair with change tickets and UC-3.2.7 posture before declaring a client bug. Scheduled audit-export or security scanning jobs that list the full object graph mirror cluster-autoscaler periodic full-list behavior; mark those service accounts in the allowlist with high budget_qps or informational severity. Very large clusters beyond roughly one thousand nodes may show elevated baseline LIST latency during reconciler-loop iterations; tune thresholds per cluster size class in cluster_platform_routing.csv notes rather than using tiny-cluster defaults. Cluster-autoscaler heartbeats that hit pods with tight intervals are expected; exclude known autoscaler signatures from critical tiers when UC-3.2.46 confirms healthy scale-out. Watch cache invalidation during apiserver restart inflates apiserver_cache_list or watch-cache counters temporarily; treat single-bucket spikes as benign when apiserver_current_inflight_requests is normal. Intentional flow-control rejection during admission storms or load tests raises apiserver_flowcontrol_rejected_requests_total by design; verify maintenance flags before blaming production regressions. Cloud provider transparent control-plane maintenance on Amazon EKS, Google GKE, or Microsoft AKS can reshape scrape alignment; cross-check provider health dashboards when only saturation_plane rows move.

## References

- [Kubernetes Metrics Reference (kube-apiserver instrumentation)](https://kubernetes.io/docs/reference/instrumentation/metrics/)
- [Kubernetes API Priority and Fairness](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/)
- [Kubernetes Cluster Components (request path overview)](https://kubernetes.io/docs/concepts/overview/components/)
- [Kubernetes API Concepts (efficiency, throttling, pagination)](https://kubernetes.io/docs/reference/using-api/api-concepts/)
- [Amazon EKS Troubleshooting (control plane signals)](https://docs.aws.amazon.com/eks/latest/userguide/troubleshooting.html)
- [Google GKE Cluster Architecture (control plane scaling context)](https://cloud.google.com/kubernetes-engine/docs/concepts/cluster-architecture)
- [Microsoft AKS Scale the Cluster (control plane limits)](https://learn.microsoft.com/en-us/azure/aks/scale-cluster)
- [Kubernetes SIG Instrumentation working group (SLO and measurement context)](https://github.com/kubernetes/community/blob/master/sig-instrumentation/README.md)
