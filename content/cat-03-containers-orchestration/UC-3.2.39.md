<!-- AUTO-GENERATED from UC-3.2.39.json — DO NOT EDIT -->

---
id: "3.2.39"
title: "Kubernetes Warning Event Storm — Statistical Anomaly Axis"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.39 · Kubernetes Warning Event Storm — Statistical Anomaly Axis

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch for unusual bursts of cluster warning messages before small problems turn into big outages. When the warning traffic pattern jumps far above its own normal rhythm, we raise a clear signal so people can investigate early.*

---

## Description

Detects cluster-wide statistical anomalies in Kubernetes API Event volume for type Warning before individual failure-mode detectors narrow the story. The analytic unions kube:events style feeds with eventrouter or kube-events-exporter sourcetypes, buckets counts into five-minute tumbling windows, compares each cluster-namespace-reason-kind slice to a trailing baseline mean and standard deviation from roughly the prior twenty-six hours excluding the most recent fifty minutes to reduce leakage from the current spike, derives a z-score and warnings-per-second cadence, highlights reasons that often precede control-plane or data-plane pain (FailedSync, FailedMount, NetworkNotReady, NodeNotReady, FailedKillPod, ContainerGCFailed, ImageGCFailed), flags fleet-relative hot spots with per-time eventstats on warning rate, and enriches ownership from cluster_platform_routing.csv. This UC deliberately stays at the anomaly altitude: it does not prove a specific CrashLoopBackOff, ImagePullBackOff, or FailedScheduling root cause—those are owned by sibling workload and scheduler UCs—and instead answers whether the cluster is shouting warnings faster than its own history suggests is normal.

## Value

Warning storms are an early, distribution-level signal that something fundamental shifted—etcd or apiserver latency, kubelet health, CNI readiness, garbage collection pressure, or multi-tenant workload churn—minutes before narrow detectors fire. Platform leaders gain a single evidence row that names cluster, namespace, reason, involved object kind, baseline statistics, z-score, short-term burst delta, fleet-relative rate, and severity so bridges shorten during ambiguous incidents. FinOps and SRE stakeholders reduce duplicate investigations when application teams open tickets during cluster-wide noise because this control separates fleet-wide statistical breaches from local workload bugs. Multi-cluster operators can compare fleet_eps_p90 overlays to catch one noisy tenant cluster without normalizing away legitimate regional incidents.

## Implementation

Land Warning Kubernetes Events in k8s or k8s_events with consistent cluster labels across kube:events and any eventrouter or events-exporter sourcetype; publish lookups/cluster_platform_routing.csv with suppress_eventstorm_dev for lab clusters; save uc_3_2_39_k8s_warning_eventstorm_statistical as a five-minute scheduled search on earliest=-35m@m latest=@m; route critical and high rows to platform on-call with throttle per cluster and basis_key; retain weekly CSV snapshots of the closing table for reliability reviews.

## Evidence

Saved search uc_3_2_39_k8s_warning_eventstorm_statistical on a five-minute schedule; lookups/cluster_platform_routing.csv versioned in git; weekly CSV export of the closing table to a restricted evidence index with HEC source type receipts for kube:events and any parallel router feed.

## Control test

### Positive scenario

In a lab cluster, temporarily throttle apiserver watch traffic or cordon several nodes under change control so Warning events for FailedSync, NetworkNotReady, or NodeNotReady exceed the moving baseline within thirty minutes; confirm uc_3_2_39_k8s_warning_eventstorm_statistical returns at least one medium or high row with z_score above the tuned gate and top_reason_watch equal to one for the injected reason family.

### Negative scenario

During a steady window with no maintenance, single-feed kube:events ingestion, and representative baseline history, confirm warn_cnt stays near baseline_avg such that abs(z_score) remains below Z_CRIT for production namespaces across four consecutive five-minute runs and the alert search emits zero qualifying rows when suppress_eventstorm_dev is respected for lab clusters.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with the Kubernetes platform SRE who certifies RBAC for event watchers, the observability engineer who operates Splunk OpenTelemetry Collector or Splunk Connect for Kubernetes, and the incident commander who approves paging thresholds. UC-3.2.39 occupies a deliberately high altitude: statistical anomaly detection on Kubernetes Warning Event volume and its distribution across reason, namespace, and involved object kind in five-minute tumbling windows. It is not a replacement for UC-3.2.10 CrashLoopBackOff kubelet waiting-reason detection, any ImagePullBackOff deep dive, UC-3.2.2 generic Pending narratives, UC-3.2.46 Cluster Autoscaler refusal analytics, UC-3.2.7 four-pillar control-plane synthesis, or UC-3.2.34 CoreDNS resolver metrics. Those siblings answer specific failure modes; this UC answers whether the cluster-wide warning narrative is behaving like itself compared with roughly the last day of history and whether the fleet is an outlier at the same timestamp.

Operational prerequisites begin with trustworthy time. API Events carry firstTimestamp, lastTimestamp, and series semantics that vary by server version; your Splunk TIME_PREFIX and TIME_FORMAT configuration must map the forwarded JSON or log line to _time with skew under thirty seconds versus apiserver clocks. When collectors buffer during network partitions, replay spikes can look like incident onset; monitor forwarder lag dashboards and delay alert actions when lag exceeds two minutes for this index class.

Indexing layout: dedicate k8s_events or reuse k8s for kube:events and kube:objects:events with sourcetype discipline. If you deploy kubernetes-events-exporter or eventrouter, land those sourcetypes in the same index class so multisearch arms stay colocated for disk scheduling. Issue distinct HEC tokens per environment with least-privilege search roles so tenant developers cannot read kube-system narratives unless policy allows. Retain at least fourteen days of hot buckets for baseline stability and thirty days when finance expects quarter-close evidence packs.

Field normalization is the highest-risk prerequisite. Warning appears as type, Type, or literal Warning inside _raw depending on exporter. Reason strings appear as reason, Reason, involvedObject.reason, or nested event.reason paths. Namespace may appear only on metadata.namespace or involvedObject.namespace; cluster-scoped objects should collapse to a sentinel namespace label such as cluster_scoped so stats do not fragment. Cluster identity must coalesce cloud-specific tags (eks_cluster_name, gke_cluster_name, aks_cluster_name) with neutral cluster_name. If any arm of multisearch leaves cluster empty, drop those rows in production alerts—they cannot route ownership.

Governance lookup cluster_platform_routing.csv must include cluster, on_call_team, fleet_tier, suppress_eventstorm_dev. Dev, sandbox, and single-node lab clusters should set suppress_eventstorm_dev=1 so statistical curiosity does not page overnight. Production gold estates set fleet_tier=gold so ITSI or alert actions can escalate faster on the same z_score when finance policy demands.

Risk briefing for leaders: a quiet baseline with very low baseline_sd can explode z_score during harmless single-digit count increases; MIN_WARN_CNT and Z_CRIT exist to keep the alert away from Poisson noise. Conversely, a very chatty namespace (continuous low-grade warnings) inflates baseline_avg and hides genuine multiplicative growth; burst_delta and fleet_anomaly_flag provide second and third opinions. Always treat this UC as triage signal, not verdict.

Capacity and licensing: duplicate feeds (kube:events plus eventrouter) double counts unless you standardize on one feed per cluster; prefer a single authoritative stream and keep the second sourcetype only during migrations with documented deduplication plans. High-cardinality object names are not indexed dimensions in this UC by design—only kind, namespace, and reason—to keep search fan-out bounded.

Security and privacy: Events can include image names, volume handles, and service account references. Restrict dashboard drilldowns and email actions to roles cleared for infrastructure metadata. Redact customer tenant strings at HEC time if legal requires it, while preserving reason and kind for statistical integrity.

Finally, align with change management: threshold edits belong in the same change record as updates to cluster_platform_routing.csv. Quarterly rehearsal of a synthetic warning storm in lab validates end-to-end paging without touching production quorum.

### Step 2 — Configure data collection

Deploy Splunk OpenTelemetry Collector with k8s_events receiver in watch mode across namespaces material to platform operations, or install Splunk Connect for Kubernetes object/event inputs with equivalent RBAC. The ServiceAccount needs get, list, and watch on events in the watched namespaces; platform teams often grant cluster-wide watch with audit review. For Amazon EKS, wire IRSA annotations; for GKE, workload identity; for AKS, managed identity bindings. Document token rotation alongside HEC token rotation.

If you adopt kubernetes-events-exporter, configure kubeconfig in-cluster, route sinks to Splunk HEC, and normalize sourcetype to kubernetes_events_exporter or kube_events_exporter consistently. If you still operate Heptio-style eventrouter, keep kubernetes:eventrouter sourcetype stable across chart upgrades.

Example OTel collector fragment for events only (adjust endpoints and tokens):

```yaml
receivers:
  k8s_events:
    auth_type: serviceAccount
    namespaces: []
exporters:
  splunk_hec/k8s_events:
    token: ${SPLUNK_HEC_TOKEN_K8S_EVENTS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_events
    sourcetype: kube:events
processors:
  batch:
    timeout: 5s
service:
  pipelines:
    logs/k8s_events:
      receivers: [k8s_events]
      processors: [batch]
      exporters: [splunk_hec/k8s_events]
```

props.conf guidance: for kube:events JSON, set KV_MODE=json if fields are not auto extracted; for router formats, add FIELDALIAS-type maps to evt_type when vendor nests fields. transforms.conf can stamp cluster from HEC metadata when collectors add an indexed field cluster_name at ingest.

Create lookups/cluster_platform_routing.csv with representative rows:

```csv
cluster,fleet_tier,on_call_team,suppress_eventstorm_dev
prod-eks-us-east-1,gold,platform-kubernetes-core,0
lab-kind-local,silver,platform-lab,1
```

Validation searches before alert authoring:

index=k8s_events sourcetype=kube:events earliest=-15m | stats count by cluster type reason
index=k8s_events sourcetype IN ("kubernetes:eventrouter*","kubernetes_events_exporter") earliest=-15m | stats count by cluster sourcetype

Confirm Warning appears in type or Type with non-zero counts. If only Normal arrives, RBAC or namespace filters are too tight.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_39_k8s_warning_eventstorm_statistical with schedule */5 * * * * and dispatch earliest=-35m@m, dispatch latest=@m. Throttle duplicate pages per cluster, namespace, evt_reason, and obj_kind for twenty minutes unless severity escalates from medium to critical. Include z_score, warn_eps, and burst_delta in the notification body. Wire critical rows to PagerDuty and medium rows to Slack or email per local policy.

Pipeline narrative: the opening comment lists Z_CRIT, MIN_WARN_CNT, and window bounds. multisearch unions kube:events style events with router or exporter feeds so migrations do not blind the alert. After union, stats sums warn_cnt per five-minute bucket and dimensional keys. streamstats computes burst_delta against the prior bucket for the same key. join pulls baseline_avg, baseline_sd, and baseline_p95 from historical buckets excluding the recent fifty minutes so the current storm does not inflate its own baseline. z_score divides deviation by a safe standard deviation floor. eventstats derives fleet_eps_p90 per _time for cross-cluster rate comparison. inputlookup cluster_platform_routing.csv adds on_call_team, fleet_tier, and suppression flags. case assigns critical, high, medium, low severity with emphasis on the watch-listed reasons that precede systemic incidents. The closing table retains twelve analyst-facing columns for drilldowns.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.39 Kubernetes Warning event storm statistical anomaly axis. Tunables: Z_CRIT=3.25 MIN_WARN_CNT=22 baseline window -26h@-50m; current window -35m@m..@m; multisearch unions kube:events with router or exporter lanes.")`
| multisearch
    [ search (index=k8s OR index=k8s_events OR index=k8s_logs) earliest=-35m@m latest=@m
        (sourcetype="kube:events" OR sourcetype="kube:objects:events")
      | eval evt_type=upper(trim(toString(coalesce(type, Type, `object.type`, eventType, ""))))
      | where evt_type="WARNING"
      | eval evt_reason=trim(toString(coalesce(reason, Reason, involvedObject.reason, `involvedObject.reason`, "unknown_reason")))
      | eval obj_kind=lower(trim(toString(coalesce(involvedObject.kind, objectKind, involvedObject_kind, kind, "unknown_kind"))))
      | eval namespace=lower(trim(toString(coalesce(metadata.namespace, namespace, involvedObject.namespace, `involvedObject.namespace`, "cluster_scoped"))))
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, source_cluster, resource_cluster, ""))))
      | where len(cluster)>0
      | eval feed="kube_api_events"
      | bucket _time span=5m aligntime=@m
      | stats count AS warn_cnt BY _time cluster namespace evt_reason obj_kind feed ]
    [ search (index=k8s OR index=k8s_events OR index=k8s_logs) earliest=-35m@m latest=@m
        (sourcetype="kubernetes:eventrouter" OR sourcetype="kubernetes:eventrouter*" OR sourcetype="kube:events:router" OR sourcetype="kubernetes_events_exporter" OR sourcetype="kube_events_exporter")
      | eval evt_type=upper(trim(toString(coalesce(type, Type, eventType, `event.type`, ""))))
      | where evt_type="WARNING" OR match(_raw, "(?i)\\bWarning\\b")
      | eval evt_reason=trim(toString(coalesce(reason, Reason, `event.reason`, object_reason, "unknown_reason")))
      | eval obj_kind=lower(trim(toString(coalesce(involvedObject.kind, `event.involvedObject.kind`, kind, "unknown_kind"))))
      | eval namespace=lower(trim(toString(coalesce(metadata.namespace, namespace, `event.metadata.namespace`, "cluster_scoped"))))
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, source_cluster, resource_cluster, ""))))
      | where len(cluster)>0
      | eval feed="router_or_exporter"
      | bucket _time span=5m aligntime=@m
      | stats count AS warn_cnt BY _time cluster namespace evt_reason obj_kind feed ]
| stats sum(warn_cnt) AS warn_cnt BY _time cluster namespace evt_reason obj_kind
| sort 0 cluster namespace evt_reason obj_kind + _time
| streamstats window=2 current=t global=f last(warn_cnt) AS prior_bucket_warn_cnt BY cluster namespace evt_reason obj_kind
| eval burst_delta=warn_cnt-coalesce(prior_bucket_warn_cnt,0)
| eval warn_eps=round(warn_cnt/300, 4)
| join type=left max=0 cluster namespace evt_reason obj_kind
    [| search (index=k8s OR index=k8s_events OR index=k8s_logs) earliest=-26h@m latest=-50m@m
        ((sourcetype="kube:events" OR sourcetype="kube:objects:events")
         OR (sourcetype="kubernetes:eventrouter" OR sourcetype="kubernetes:eventrouter*" OR sourcetype="kube:events:router" OR sourcetype="kubernetes_events_exporter" OR sourcetype="kube_events_exporter"))
      | eval evt_type=upper(trim(toString(coalesce(type, Type, eventType, `object.type`, `event.type`, ""))))
      | where evt_type="WARNING" OR match(_raw, "(?i)\\bWarning\\b")
      | eval evt_reason=trim(toString(coalesce(reason, Reason, involvedObject.reason, `involvedObject.reason`, `event.reason`, object_reason, "unknown_reason")))
      | eval obj_kind=lower(trim(toString(coalesce(involvedObject.kind, objectKind, involvedObject_kind, kind, `event.involvedObject.kind`, "unknown_kind"))))
      | eval namespace=lower(trim(toString(coalesce(metadata.namespace, namespace, involvedObject.namespace, `involvedObject.namespace`, `event.metadata.namespace`, "cluster_scoped"))))
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, source_cluster, resource_cluster, ""))))
      | where len(cluster)>0
      | bucket _time span=5m aligntime=@m
      | stats count AS hist_slice_cnt BY cluster namespace evt_reason obj_kind _time
      | stats avg(hist_slice_cnt) AS baseline_avg stdev(hist_slice_cnt) AS baseline_sd perc95(hist_slice_cnt) AS baseline_p95 BY cluster namespace evt_reason obj_kind ]
| fillnull value=0 baseline_avg
| eval baseline_sd_safe=if(isnull(baseline_sd) OR baseline_sd<0.0001, 0.0001, baseline_sd)
| eval z_score=round((warn_cnt-baseline_avg)/baseline_sd_safe, 3)
| eventstats perc90(warn_eps) AS fleet_eps_p90 BY _time
| eval fleet_anomaly_flag=if(warn_eps>(1.25*coalesce(fleet_eps_p90,0)) AND coalesce(fleet_eps_p90,0)>0, 1, 0)
| join type=left max=0 cluster
    [| inputlookup cluster_platform_routing.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval on_call_team=trim(toString(coalesce(on_call_team, squad, platform_team, "platform_eventstorm")))
      | eval fleet_tier=lower(trim(toString(coalesce(fleet_tier, estate_tier, "standard"))))
      | eval suppress_eventstorm_dev=tonumber(tostring(coalesce(suppress_eventstorm_dev, "0")), 10)
      | fields cluster on_call_team fleet_tier suppress_eventstorm_dev ]
| fillnull value="platform_eventstorm" on_call_team
| fillnull value="standard" fleet_tier
| fillnull value=0 suppress_eventstorm_dev
| eval top_reason_watch=if(match(evt_reason, "^(FailedSync|FailedMount|NetworkNotReady|NodeNotReady|FailedKillPod|ContainerGCFailed|ImageGCFailed)$"), 1, 0)
| eval Z_CRIT=3.25
| eval MIN_WARN_CNT=22
| eval severity=case(
    abs(z_score)>=5.5 AND warn_cnt>=60 AND top_reason_watch==1, "critical",
    abs(z_score)>=Z_CRIT AND warn_cnt>=MIN_WARN_CNT AND top_reason_watch==1 AND fleet_anomaly_flag==1, "critical",
    abs(z_score)>=Z_CRIT AND warn_cnt>=MIN_WARN_CNT AND top_reason_watch==1, "high",
    abs(z_score)>=Z_CRIT AND warn_cnt>=MIN_WARN_CNT, "medium",
    fleet_anomaly_flag==1 AND warn_cnt>=(MIN_WARN_CNT+8), "medium",
    true(), "low")
| where match(severity, "critical|high|medium") AND (suppress_eventstorm_dev==0 OR severity=="critical")
| table _time cluster namespace evt_reason obj_kind warn_cnt baseline_avg baseline_sd baseline_p95 z_score warn_eps burst_delta fleet_eps_p90 fleet_anomaly_flag severity top_reason_watch on_call_team fleet_tier
```

savedsearches.conf sketch:

```ini
[uc_3_2_39_k8s_warning_eventstorm_statistical]
action.email = 1
action.email.to = platform-event-anomaly@example.com
action.email.subject = K8s Warning storm $result.severity$ on $result.cluster$ / $result.namespace$ / $result.evt_reason$
action.email.message = z=$result.z_score$ warn_cnt=$result.warn_cnt$ eps=$result.warn_eps$ burst_delta=$result.burst_delta$ fleet_flag=$result.fleet_anomaly_flag$
alert.track = 1
cron_schedule = */5 * * * *
dispatch.earliest_time = -35m@m
dispatch.latest_time = now
enableSched = 1
alert.suppress = 1
alert.suppress.period = 1200s
```

### Step 4 — Validate

Positive path A — inject a controlled warning burst in lab: apply a temporary NetworkPolicy or cordon several nodes under change control so kubelet and node controllers emit NetworkNotReady or NodeNotReady warnings; within thirty minutes confirm warn_cnt exceeds baseline_avg with z_score above Z_CRIT and top_reason_watch equals one.

Positive path B — dual-feed migration: for ten minutes only, enable eventrouter alongside kube:events and verify warn_cnt does not silently double by comparing feed-specific stats searches; after validation disable the duplicate feed or add dedup keys.

Negative path — steady production hour: run the search across four consecutive intervals and confirm zero rows when MIN_WARN_CNT and Z_CRIT are at defaults and suppress_eventstorm_dev is honored for lab clusters.

Lag guard: compare max(_time) from raw events to now(); if lag exceeds one hundred twenty seconds, pause alert actions and open a collector incident.

Synthetic dashboard QA: visualize baseline_p95 versus warn_cnt for the top three reasons; if baseline_p95 is always zero while warn_cnt is non-zero, historical window or sourcetype filters are wrong.

### Step 5 — Operationalize & Troubleshoot

Case 1 — z_score high but only from baseline_sd near zero
Widen MIN_WARN_CNT slightly, require burst_delta positive for two buckets, or set a floor on baseline_sd_safe in a local macro after reviewing Poisson behavior for that namespace.

Case 2 — fleet_anomaly_flag never triggers
Confirm multiple clusters land in the same Splunk index; if each cluster is siloed per index, compute fleet_eps_p90 inside a summary index that merges clusters with a common summary macro.

Case 3 — eventrouter migration doubled counts
Remove parallel feeds or hash dedup on involvedObject.uid when present; document the cutover minute in the runbook.

Case 4 — kube-system dominates rows every upgrade
Annotate upgrade windows and require sustained breach after upgrade end before paging gold fleet_tier clusters.

Case 5 — CSI snapshot namespaces spike weekly
Add namespace suppression or downgrade medium to informational when snapshot_controller=known_good in the lookup.

Case 6 — GitOps reconciliation storm
Correlate with Argo CD or Flux sync latency metrics; route to GitOps owners when reasons are apply failures rather than node health.

Case 7 — cross-region failover drill duplicates anomalies
Partition eventstats by region label in a forked macro so east and west fleets do not pollute each other’s perc90.

Case 8 — chaos engineering week
Set chaos_active on cluster rows for the drill calendar span; auto-clear the flag with a time-based lookup column expiry.

Case 9 — etcd or apiserver latency without obvious node reasons
Open UC-3.2.7 control-plane synthesis after capturing this UC’s row as the time anchor; do not silence the warning storm UC until control-plane health is ruled in or out.

Case 10 — CNI upgrades with NetworkNotReady warnings
Pair with network team maintenance records; dampen when CNI chart version changes match the spike window.

Case 11 — batch cron at 00:00 UTC
Add time-of-day guard macros or namespace allowlists for finance batch namespaces when burst_delta is predictable.

Case 12 — Splunk search skew from clock drift
Fix NTP on forwarders and apiserver hosts; re-run validation when drift exceeds one second consistently.

Governance: archive weekly CSV outputs with the cluster_platform_routing.csv commit hash. Training: teach responders that severity medium still deserves a ticket when customer impact is suspected even if pages are suppressed. Performance: if Job Inspector shows join violations, materialize hourly warning counts per basis_key into a summary index and point the alert at the summary while keeping raw searches for investigations.

Closing checklist: five step headers use em dashes exactly; Step 3 includes fenced SPL matching the spl field; Step 5 lists twelve case lines; knownFalsePositives covers upgrades, leader elections, cron batch waves, GitOps storms, CSI snapshots, chaos drills, failover drills, and lab noise; references span Kubernetes Events documentation, Event v1 API, eventrouter, kubernetes-events-exporter, kube-state-metrics event metrics, kubectl get, GKE workload status, EKS logging and monitoring, and Azure Monitor container insights; monitoringType lists Reliability and Availability; cimModels lists Application_State and Alerts; equipmentModels lists kubernetes_k8s.


## SPL

```spl
`comment("UC-3.2.39 Kubernetes Warning event storm statistical anomaly axis. Tunables: Z_CRIT=3.25 MIN_WARN_CNT=22 baseline window -26h@-50m; current window -35m@m..@m; multisearch unions kube:events with router or exporter lanes.")`
| multisearch
    [ search (index=k8s OR index=k8s_events OR index=k8s_logs) earliest=-35m@m latest=@m
        (sourcetype="kube:events" OR sourcetype="kube:objects:events")
      | eval evt_type=upper(trim(toString(coalesce(type, Type, `object.type`, eventType, ""))))
      | where evt_type="WARNING"
      | eval evt_reason=trim(toString(coalesce(reason, Reason, involvedObject.reason, `involvedObject.reason`, "unknown_reason")))
      | eval obj_kind=lower(trim(toString(coalesce(involvedObject.kind, objectKind, involvedObject_kind, kind, "unknown_kind"))))
      | eval namespace=lower(trim(toString(coalesce(metadata.namespace, namespace, involvedObject.namespace, `involvedObject.namespace`, "cluster_scoped"))))
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, source_cluster, resource_cluster, ""))))
      | where len(cluster)>0
      | eval feed="kube_api_events"
      | bucket _time span=5m aligntime=@m
      | stats count AS warn_cnt BY _time cluster namespace evt_reason obj_kind feed ]
    [ search (index=k8s OR index=k8s_events OR index=k8s_logs) earliest=-35m@m latest=@m
        (sourcetype="kubernetes:eventrouter" OR sourcetype="kubernetes:eventrouter*" OR sourcetype="kube:events:router" OR sourcetype="kubernetes_events_exporter" OR sourcetype="kube_events_exporter")
      | eval evt_type=upper(trim(toString(coalesce(type, Type, eventType, `event.type`, ""))))
      | where evt_type="WARNING" OR match(_raw, "(?i)\\bWarning\\b")
      | eval evt_reason=trim(toString(coalesce(reason, Reason, `event.reason`, object_reason, "unknown_reason")))
      | eval obj_kind=lower(trim(toString(coalesce(involvedObject.kind, `event.involvedObject.kind`, kind, "unknown_kind"))))
      | eval namespace=lower(trim(toString(coalesce(metadata.namespace, namespace, `event.metadata.namespace`, "cluster_scoped"))))
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, source_cluster, resource_cluster, ""))))
      | where len(cluster)>0
      | eval feed="router_or_exporter"
      | bucket _time span=5m aligntime=@m
      | stats count AS warn_cnt BY _time cluster namespace evt_reason obj_kind feed ]
| stats sum(warn_cnt) AS warn_cnt BY _time cluster namespace evt_reason obj_kind
| sort 0 cluster namespace evt_reason obj_kind + _time
| streamstats window=2 current=t global=f last(warn_cnt) AS prior_bucket_warn_cnt BY cluster namespace evt_reason obj_kind
| eval burst_delta=warn_cnt-coalesce(prior_bucket_warn_cnt,0)
| eval warn_eps=round(warn_cnt/300, 4)
| join type=left max=0 cluster namespace evt_reason obj_kind
    [| search (index=k8s OR index=k8s_events OR index=k8s_logs) earliest=-26h@m latest=-50m@m
        ((sourcetype="kube:events" OR sourcetype="kube:objects:events")
         OR (sourcetype="kubernetes:eventrouter" OR sourcetype="kubernetes:eventrouter*" OR sourcetype="kube:events:router" OR sourcetype="kubernetes_events_exporter" OR sourcetype="kube_events_exporter"))
      | eval evt_type=upper(trim(toString(coalesce(type, Type, eventType, `object.type`, `event.type`, ""))))
      | where evt_type="WARNING" OR match(_raw, "(?i)\\bWarning\\b")
      | eval evt_reason=trim(toString(coalesce(reason, Reason, involvedObject.reason, `involvedObject.reason`, `event.reason`, object_reason, "unknown_reason")))
      | eval obj_kind=lower(trim(toString(coalesce(involvedObject.kind, objectKind, involvedObject_kind, kind, `event.involvedObject.kind`, "unknown_kind"))))
      | eval namespace=lower(trim(toString(coalesce(metadata.namespace, namespace, involvedObject.namespace, `involvedObject.namespace`, `event.metadata.namespace`, "cluster_scoped"))))
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, source_cluster, resource_cluster, ""))))
      | where len(cluster)>0
      | bucket _time span=5m aligntime=@m
      | stats count AS hist_slice_cnt BY cluster namespace evt_reason obj_kind _time
      | stats avg(hist_slice_cnt) AS baseline_avg stdev(hist_slice_cnt) AS baseline_sd perc95(hist_slice_cnt) AS baseline_p95 BY cluster namespace evt_reason obj_kind ]
| fillnull value=0 baseline_avg
| eval baseline_sd_safe=if(isnull(baseline_sd) OR baseline_sd<0.0001, 0.0001, baseline_sd)
| eval z_score=round((warn_cnt-baseline_avg)/baseline_sd_safe, 3)
| eventstats perc90(warn_eps) AS fleet_eps_p90 BY _time
| eval fleet_anomaly_flag=if(warn_eps>(1.25*coalesce(fleet_eps_p90,0)) AND coalesce(fleet_eps_p90,0)>0, 1, 0)
| join type=left max=0 cluster
    [| inputlookup cluster_platform_routing.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval on_call_team=trim(toString(coalesce(on_call_team, squad, platform_team, "platform_eventstorm")))
      | eval fleet_tier=lower(trim(toString(coalesce(fleet_tier, estate_tier, "standard"))))
      | eval suppress_eventstorm_dev=tonumber(tostring(coalesce(suppress_eventstorm_dev, "0")), 10)
      | fields cluster on_call_team fleet_tier suppress_eventstorm_dev ]
| fillnull value="platform_eventstorm" on_call_team
| fillnull value="standard" fleet_tier
| fillnull value=0 suppress_eventstorm_dev
| eval top_reason_watch=if(match(evt_reason, "^(FailedSync|FailedMount|NetworkNotReady|NodeNotReady|FailedKillPod|ContainerGCFailed|ImageGCFailed)$"), 1, 0)
| eval Z_CRIT=3.25
| eval MIN_WARN_CNT=22
| eval severity=case(
    abs(z_score)>=5.5 AND warn_cnt>=60 AND top_reason_watch==1, "critical",
    abs(z_score)>=Z_CRIT AND warn_cnt>=MIN_WARN_CNT AND top_reason_watch==1 AND fleet_anomaly_flag==1, "critical",
    abs(z_score)>=Z_CRIT AND warn_cnt>=MIN_WARN_CNT AND top_reason_watch==1, "high",
    abs(z_score)>=Z_CRIT AND warn_cnt>=MIN_WARN_CNT, "medium",
    fleet_anomaly_flag==1 AND warn_cnt>=(MIN_WARN_CNT+8), "medium",
    true(), "low")
| where match(severity, "critical|high|medium") AND (suppress_eventstorm_dev==0 OR severity=="critical")
| table _time cluster namespace evt_reason obj_kind warn_cnt baseline_avg baseline_sd baseline_p95 z_score warn_eps burst_delta fleet_eps_p90 fleet_anomaly_flag severity top_reason_watch on_call_team fleet_tier
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS cim_host
| join type=left max=0 cim_host
    [| tstats summariesonly=t count AS alert_events FROM datamodel=Alerts WHERE nodename=Alerts earliest=-4h@h latest=@h BY Alerts.signature Alerts.severity
     | stats sum(alert_events) AS alert_events BY Alerts.signature
     | eval cim_host="fleet_aggregate"
     | fields cim_host alert_events ]
| where isnotnull(app_state)
| table cim_host app_state app_info alert_events
```

## Visualization

Heatmap of z_score by namespace and reason, timechart of warn_cnt versus baseline_avg for top clusters, single value of fleet_anomaly_flag count, table matching the closing SPL projection with drilldown to raw events in the same five-minute bucket.

## Known False Positives

Planned control-plane upgrades and kubelet rollouts legitimately raise NodeNotReady and NodeReady churn pairs; annotate maintenance windows in cluster_platform_routing.csv or require two consecutive anomalous buckets after the declared window before paging executives. Controller-manager and scheduler leader-election churn during upgrades emits bursts of Warning events that resemble incidents; pair timestamps with vendor maintenance tickets and suppress fleet_anomaly_flag-only medium rows when apiserver audit mutate traffic shows only expected lease rotations. Batch cron waves at clock boundaries (for example 00:00 hourly) can spike FailedSync or mount warnings when thousands of Jobs start together; add a cron_guard macro that dampens severity for namespaces listed as batch_senders in the lookup. GitOps engines that reapply large manifests after a stash or rollback create short Warning storms from reconciliation controllers; correlate with Git commit rate or Argo CD sync counters before opening sev-one bridges. Scheduled CSI snapshot controllers sometimes emit many volume attach or mount warnings during snapshot cut-overs; exclude snapshotter namespaces when snapshot_policy=managed appears in your routing table. Controlled chaos experiments (Chaos Mesh, LitmusChaos, Gremlin) intentionally stress nodes and network paths; set suppress_eventstorm_dev or a chaos_active flag on participating clusters for the drill duration. Regional failover drills and active-active traffic shifts can duplicate events across paired clusters; compare warn_eps to fleet_eps_p90 only inside the same region label to avoid false cross-region anomalies. Development and lab clusters with artificial load generators routinely exceed production z-scores; keep suppress_eventstorm_dev=1 on those rows unless critical severity fires. Finally, first-time ingestion of a second event feed (adding eventrouter beside kube:events) can double counts until deduplication keys are applied; treat baseline_avg shifts after feed changes as a configuration incident, not a platform outage.

## References

- [Kubernetes — Events in cluster](https://kubernetes.io/docs/concepts/overview/working-with-objects/kubernetes-events/)
- [Kubernetes API reference — Event v1](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/)
- [vmware-archive eventrouter (Kubernetes events to sinks)](https://github.com/vmware-archive/eventrouter)
- [resmoio kubernetes-events-exporter](https://github.com/resmoio/kubernetes-events-exporter)
- [kube-state-metrics — cluster event metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/cluster/event-metrics.md)
- [kubectl reference — get (list events)](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_get/)
- [Google Cloud — GKE workload status and events](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-status)
- [Amazon EKS — Logging and monitoring overview](https://docs.aws.amazon.com/eks/latest/userguide/logging-monitoring.html)
- [Microsoft Learn — Azure Monitor container insights](https://learn.microsoft.com/en-us/azure/azure-monitor/containers/container-insights-overview)
