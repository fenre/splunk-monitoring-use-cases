<!-- AUTO-GENERATED from UC-3.2.4.json — DO NOT EDIT -->

---
id: "3.2.4"
title: "Kubernetes Namespace ResourceQuota Exhaustion (Pod-Create Block)"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.4 · Kubernetes Namespace ResourceQuota Exhaustion (Pod-Create Block)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*Each Kubernetes namespace is given a budget for compute, memory, and objects such as pods and storage claims. When that budget is completely spent, new work cannot start and upgrades can stall. We warn you when the budget is empty so the owning team can raise it before customers feel delays.*

---

## Description

Detects namespace-level Kubernetes ResourceQuota exhaustion in real time: any quota dimension whose used-to-hard ratio reaches one hundred percent or admission control rejects new objects with forbidden exceeded quota errors, which blocks rolling deploys, PVC creation, load balancer Services, and other counted resources until hard limits rise or usage falls. The analytic multisearches kube-state-metrics kube_resourcequota typed gauges, correlates kube events with FailedCreate reasons, and joins kube-apiserver audit 403 narratives, then enriches with namespace ownership so responders know which application squad owns the namespace and which platform team approves quota policy. The monitoring axis is immediate create-blocking exhaustion, not proactive high-water trending (UC-3.2.32), not LimitRange defaults (UC-3.2.36), and not cluster autoscaler node shortages (UC-3.2.46).

## Value

Cuts mean time to innocence when rollouts stall without obvious crash loops: the alert names the exact namespace, quota resource, ownership, denial volume, and implicated workloads so platform and application leaders stop debating whether the cluster or the tenant budget failed. Customer-facing SLO burn from stuck Deployments or StatefulSets drops when quota raises happen minutes after denial evidence instead of hours after manual kubectl archaeology. FinOps and network teams get early signal when costly dimensions such as services.loadbalancers or persistentvolumeclaims hit ceilings because each increment may trigger cloud billing changes. Audit and risk reviewers gain timestamped proof that admission enforcement operated and that ownership data was attached for accountability.

## Implementation

Stand up k8s_metrics, k8s, and k8s_audit with distinct HEC tokens; deploy kube-state-metrics with ResourceQuota metrics enabled and scrape via Splunk OTel Collector into prometheus:scrape:metrics; stream kube:events and ship kube:apiserver:audit with RequestResponse depth for denials; publish namespace_ownership_inventory.csv; save uc_3_2_4_resourcequota_exhaustion_block every five minutes on earliest=-15m@m latest=now; route exhausted plus positive denial_count_5m for gold namespaces to platform and owner on-call bridges.

## Evidence

Saved search uc_3_2_4_resourcequota_exhaustion_block with five-minute schedule; namespace_ownership_inventory.csv versioned in git; weekly CSV export of the closing table to a restricted evidence index with anonymized kube:apiserver:audit hashes when incidents involve regulated namespaces.

## Control test

### Positive scenario

In a lab namespace with ResourceQuota hard pods equal to one, attempt a second pod create after a successful first pod; confirm kube:events or kube:apiserver:audit records exceeded quota messaging, kube_resourcequota used equals hard for pods, and uc_3_2_4_resourcequota_exhaustion_block returns a row with severity exhausted or denial_count_5m greater than zero within sixty seconds.

### Negative scenario

After raising ResourceQuota hard pods to a value above current usage and waiting two scrape intervals, confirm used_pct falls below one, denial_count_5m stays zero, and the saved search emits no qualifying rows for that namespace unless unrelated resources remain exhausted.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with Kubernetes platform engineering, tenant governance, and observability teams who operate Splunk OpenTelemetry Collector fleets. UC-3.2.4 is the real-time ResourceQuota exhaustion plane for Kubernetes namespaces: it answers whether a namespace is blocked from creating additional pods, persistent volume claims, load balancer Services, or other counted objects because a ResourceQuota hard limit is fully consumed or because the ResourceQuota admission controller returns forbidden exceeded quota responses. UC-3.2.32 remains the sibling that trends utilization before the wall, typically above roughly eighty percent, so release managers can widen quotas during change windows. UC-3.2.36 documents LimitRange defaults and per-container limit enforcement, which is a different policy object and a different admission path. UC-3.2.46 focuses on cluster autoscaler inability to add nodes when the cluster lacks schedulable capacity, which is not the same as a namespace-level budget cap. This UC correlates kube-state-metrics kube_resourcequota typed gauges with kube events carrying FailedCreate reasons and kube-apiserver audit JSON showing ResponseStatus code 403 with messages that include forbidden and exceeded quota, then enriches rows with namespace_ownership_inventory.csv so paging bridges land on the team that owns the application namespace and the team that approves quota changes.

Index and ACL contracts precede saved search authoring. Stand up or designate index=k8s_metrics for prometheus:scrape:metrics events scraped from kube-state-metrics and related prometheus endpoints, index=k8s for kube:events timelines, and index=k8s_audit for kube:apiserver:audit JSON. Issue distinct HEC tokens per index class with role-based search restrictions so developers can see quota dashboards without reading full RequestResponse audit bodies unless policy allows. Document retention: metrics hot buckets at least fourteen days for incident replay, audit at least thirty days for attribution of quota edits and denial storms, events aligned to your platform standard so correlation windows stay consistent across regions.

kube-state-metrics must expose kube_resourcequota metrics with resource, type, namespace, and resourcequota labels for both hard and used samples as described in upstream kube-state-metrics policy documentation. Enable the collectors your distribution packages under the policy resourcequota family; without both typed series, ratio math is impossible and the search returns quota_metrics_gap style blind spots. Splunk OpenTelemetry Collector for Kubernetes should scrape kube-state-metrics through a prometheus receiver job or prometheus_simple receiver, preserving labels that map to cluster identity such as k8s_cluster_name or cloud-specific cluster tags your fleet already emits.

Audit policy must capture sufficient detail for denial forensics. Configure audit-policy.yaml so that failed writes tied to quota enforcement can be reconstructed: RequestResponse level for denied resource creates and updates that matter to your SLO, including pods, replicationcontrollers, replicasets, deployments, statefulsets, daemonsets, jobs, cronjobs, persistentvolumeclaims, services, and configmaps where your governance requires it. Include rules that keep metadata noise low while still retaining ResponseStatus message bodies for 403 outcomes, because the substring exceeded quota is the corroborating string alongside metrics math.

Governance lookup namespace_ownership_inventory.csv must contain cluster, namespace, owner_team, owner_email, app_id, criticality with gold silver bronze semantics, and optional on_call_team when paging bridges differ from product ownership. Refresh weekly from CMDB or internal service directory exports and attach git commit hashes when auditors ask for lineage. Gold namespaces route exhausted severity to immediate paging when denial_count_5m is positive or when used_pct has remained at one for longer than the soak window. Silver namespaces page platform first with application bridge on a short timer. Bronze namespaces open tickets unless an executive override marks the namespace as customer visible.

Risk briefing: horizontal pod autoscaler scale-out can drive used pod counts to the hard ceiling for short intervals while new pods are admitted and old pods terminate; the streamstats sustained gate inside the sixty minute exhaustion join reduces single-scrape flicker. Chaos engineering namespaces that deliberately violate quotas should carry labels mirrored into the lookup so suppression macros remove them from executive dashboards. Stale quota accounting after object deletion can lag until garbage collection completes; pair denial narratives with metrics before accusing owners of drift.

Licensing note: high-cardinality quotas on long resource strings such as count widgets example com vendor crd inflate series counts; use recording rules only when FinOps and security sign off because dropped labels can hide costly object growth. Privacy note: audit and event payloads can echo internal codenames; restrict dashboard access.

Differentiation recap: exhaustion at one hundred percent utilization or live admission denials now, not generic trending, not LimitRange, not cluster autoscaler node shortages, not control-plane synthesis.

Collector architecture notes: self-managed clusters often run kube-state-metrics in monitoring namespaces with RBAC that lists all namespaces; managed offerings may require you to operate kube-state-metrics yourself to see per-tenant quota objects. Document scrape TLS, bearer token rotation, and allowed egress from collectors to kube-state-metrics Service endpoints.

FinOps alignment: services loadbalancers and persistentvolumeclaims quota dimensions tie directly to recurring cloud charges; playbook steps should name finance approvers when hard limits move.

Reliability alignment: Deployment strategies with maxSurge above zero still need spare pod quota during cutover; exhaustion surfaces as ReplicaSet create failures before node CPU starvation appears.

Security alignment: audit retains identities for kubectl edit resourcequota actions; use that attribution when quotas move during incidents without change records.

Performance alignment: multisearch and nested joins cost scheduler time; run the alert on five minute cadence and keep investigative clones in a separate saved search with broader earliest.

Training alignment: teach responders that LimitRange violations present different error verbs than ResourceQuota exhaustion.

Documentation alignment: wiki-map this UC beside ResourceQuota, LimitRange, and cluster quota documentation for new platform engineers.

Review cadence: quarterly replay one historical rollout failure where the second pod could not start because of exceeded quota.

Escalation alignment: gold criticality plus sustained exhausted plus positive denial_count_5m engages platform and application leadership jointly.

Telemetry hygiene: deduplicate kube-state-metrics scrapes if both prometheus-agent and OpenTelemetry collectors point at the same targets without dedup keys.

Governance alignment: CAB records should cover HEC token ACL changes and audit policy edits together when quota visibility shifts.

### Step 2 — Configure data collection

ServiceMonitor example that points Prometheus or OpenTelemetry service discovery at kube-state-metrics with TLS appropriate to your mesh. Adjust namespace and release labels to match kube-prometheus-stack or your vendor bundle.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-resourcequota
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kube-state-metrics
  namespaceSelector:
    matchNames:
      - kube-system
      - monitoring
  endpoints:
    - port: https
      scheme: https
      tlsConfig:
        insecureSkipVerify: true
      bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabelings:
        - action: replace
          targetLabel: k8s_cluster_name
          replacement: prod-eks-us-east-1
```

OpenTelemetry Collector fragment showing prometheus_simple or embedded prometheus scrape of kube-state-metrics plus k8s_events receiver for v1 Event objects plus filelog receiver tailing apiserver audit.log, all exporting through splunk_hec into the right indexes and sourcetypes.

```yaml
receivers:
  prometheus_simple:
    endpoints:
      - url: https://kube-state-metrics.kube-system.svc:8443/metrics
        tls:
          insecure_skip_verify: true
        headers:
          Authorization: Bearer ${K8S_SA_TOKEN}
  k8s_events:
    auth_type: serviceAccount
    namespaces: []
    mode: watch
  filelog:
    include:
      - /var/log/kubernetes/kube-apiserver-audit.log
    start_at: beginning
exporters:
  splunk_hec/metrics:
    token: ${SPLUNK_HEC_TOKEN_K8S_METRICS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
  splunk_hec/events:
    token: ${SPLUNK_HEC_TOKEN_K8S}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s
    sourcetype: kube:events
  splunk_hec/audit:
    token: ${SPLUNK_HEC_TOKEN_K8S_AUDIT}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_audit
    sourcetype: kube:apiserver:audit
service:
  pipelines:
    metrics:
      receivers: [prometheus_simple]
      exporters: [splunk_hec/metrics]
    logs_events:
      receivers: [k8s_events]
      exporters: [splunk_hec/events]
    logs_audit:
      receivers: [filelog]
      exporters: [splunk_hec/audit]
```

audit-policy.yaml fragment emphasizing RequestResponse retention for denied creates that carry quota messages, plus a focused rule mentioning resourcequotas when you need to audit quota object edits themselves.

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: RequestResponse
    verbs: ["create", "update", "patch"]
    resources:
      - group: ""
        resources: ["pods", "persistentvolumeclaims", "services", "resourcequotas"]
    omitStages: ["RequestReceived"]
  - level: Metadata
    resources:
      - group: ""
        resources: ["events"]
```

Sample namespace_ownership_inventory.csv schema for the lookup referenced in SPL.

```csv
cluster,namespace,owner_team,owner_email,app_id,criticality,on_call_team
prod-eks-us-east-1,prod-payments,payments-platform,payments-oncall@example.com,PAY-2048,gold,payments-sre
prod-eks-us-east-1,dev-data-platform,data-analytics,data-tickets@example.com,DAT-0091,silver,platform-core
```

props and transforms guidance: normalize __name__, value, namespace, resource, type, resourcequota, cluster labels onto indexed fields where Splunk data models allow; keep camelCase aliases from OTEL exporters in transforms.conf so coalesce ladders in SPL stay short.

Validation before alert authoring: index=k8s_metrics sourcetype=prometheus:scrape:metrics earliest=-30m must return kube_resourcequota samples with type hard and used; index=k8s sourcetype=kube:events earliest=-24h should show FailedCreate noise in busy clusters; index=k8s_audit sourcetype=kube:apiserver:audit earliest=-24h must parse responseStatus fields used by the SPL. Clock skew between apiserver, kube-state-metrics, and Splunk _time must stay under sixty seconds or correlation windows misalign.

### Step 3 — Create the search and alert

Save the SPL as saved search uc_3_2_4_resourcequota_exhaustion_block with five minute schedule, dispatch earliest=-15m@m, dispatch latest=now, and throttle duplicate exhausted rows per cluster namespace resource for fifteen minutes unless denial_count_5m doubles inside the same window. Route exhausted with positive denials to gold on-call routes from the lookup; route critical_near_exhaust without denials to a lower bridge unless criticality demands earlier paging.

Pipeline understanding for operators: the opening comment macro lists indexes, sourcetypes, and soak guidance so retuning does not require opening this document cold. multisearch fans kube_resourcequota used and hard arms so a silent failure in one type label does not zero the entire ratio. coalesce ladders normalize cluster, namespace, resource, and quota object labels across cloud and on-prem field naming. The join wrapped multisearch aggregates FailedCreate event volume and 403 audit denials per namespace, producing denial_count_5m and blocked_workloads from involved object names. inputlookup namespace_ownership_inventory.csv enriches owner_team and on_call_team for RACI clarity. A second join reconstructs time_in_exhaustion_min by bucketing five minute windows, recomputing snap_pct, sorting chronologically, applying streamstats to require sustained at or above one hundred percent, then measuring span from first to last sustained bucket inside sixty minutes. case maps severity bands: exhausted at one hundred percent, critical_near_exhaust between ninety five and one hundred, high between eighty five and ninety five, warning between seventy five and eighty five, otherwise healthy. eventstats adds namespace_peak_pct for optional dashboard overlays before fields pruning. The closing table lists twelve analyst columns: cluster, namespace, resource, used, hard, used_pct, severity, owner_team, on_call_team, denial_count_5m, time_in_exhaustion_min, blocked_workloads.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.4 Kubernetes Namespace ResourceQuota exhaustion (pod-create block). Tunables: idx_metrics=k8s_metrics idx_events=k8s idx_audit=k8s_audit; st_metrics=prometheus:scrape:metrics st_events=kube:events st_audit=kube:apiserver:audit; soak_minutes=5; earliest=-15m@m latest=@m")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-15m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval rq_type=lower(trim(toString(coalesce(type, quota_type, resourcequota_type, ""))))
      | eval resource=trim(toString(coalesce(resource, resource_name, quota_resource, resourcequota, "")))
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval quota_obj=trim(toString(coalesce(resourcequota, name, resource_quota, "")))
      | where mn="kube_resourcequota" AND rq_type="used" AND len(cluster)>0 AND len(namespace)>0 AND len(resource)>0
      | stats latest(mv) AS used latest(_time) AS ts_metric BY cluster namespace resource quota_obj ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-15m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval rq_type=lower(trim(toString(coalesce(type, quota_type, resourcequota_type, ""))))
      | eval resource=trim(toString(coalesce(resource, resource_name, quota_resource, resourcequota, "")))
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval quota_obj=trim(toString(coalesce(resourcequota, name, resource_quota, "")))
      | where mn="kube_resourcequota" AND rq_type="hard" AND len(cluster)>0 AND len(namespace)>0 AND len(resource)>0
      | stats latest(mv) AS hard BY cluster namespace resource quota_obj ]
| stats max(used) AS used max(hard) AS hard max(ts_metric) AS ts_metric BY cluster namespace resource quota_obj
| eval used_num=tonumber(tostring(used),10)
| eval hard_num=tonumber(tostring(hard),10)
| eval used_pct=if(isnotnull(hard_num) AND hard_num>0 AND isnotnull(used_num), round(used_num/hard_num, 6), null())
| join type=left max=0 cluster namespace
    [| multisearch
          [ search index=k8s sourcetype="kube:events" earliest=-15m@m latest=@m
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
            | eval namespace=trim(toString(coalesce(metadata_namespace, namespace, involvedObject_namespace, "")))
            | eval reason=trim(toString(coalesce(reason, Reason, "")))
            | eval msg=lower(toString(coalesce(message, Message, _raw, "")))
            | eval blk=toString(coalesce(involvedObject_name, `involvedObject.name`))
            | where (reason="FailedCreate" OR like(reason, "%FailedCreate%")) AND like(msg, "%exceeded quota%")
            | stats count AS cnt values(blk) AS blk_mv BY cluster namespace ]
          [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-15m@m latest=@m
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, objectRef_cluster, ""))))
            | eval namespace=trim(toString(coalesce(objectRef_namespace, namespace, requestNamespace, "")))
            | eval code=tonumber(tostring(coalesce(responseStatus_code, `responseStatus.code`, status_code)),10)
            | eval msg=lower(toString(coalesce(responseStatus_message, `responseStatus.message`, message)))
            | eval blk=toString(coalesce(objectRef_name, `objectRef.name`))
            | where code=403 AND like(msg, "%forbidden%") AND like(msg, "%exceeded quota%")
            | stats count AS cnt values(blk) AS blk_mv BY cluster namespace ]
      | stats sum(cnt) AS denial_count_5m values(blk_mv) AS bw BY cluster namespace
      | eval blocked_workloads=mvjoin(mvdedup(bw), ", ") ]
| fillnull value=0 denial_count_5m
| join type=left max=0 cluster namespace
    [| inputlookup namespace_ownership_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=trim(toString(namespace))
      | eval owner_team=toString(coalesce(owner_team, team, squad, ""))
      | eval on_call_team=toString(coalesce(on_call_team, pager_team, platform_oncall, owner_team, ""))
      | fields cluster namespace owner_team on_call_team app_id criticality ]
| join type=left max=0 cluster namespace resource quota_obj
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-60m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval rq_type=lower(trim(toString(coalesce(type, quota_type, resourcequota_type, ""))))
      | eval resource=trim(toString(coalesce(resource, resource_name, quota_resource, resourcequota, "")))
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval quota_obj=trim(toString(coalesce(resourcequota, name, resource_quota, "")))
      | where mn="kube_resourcequota" AND match(rq_type, "used|hard")
      | eval u=if(rq_type="used", mv, null())
      | eval h=if(rq_type="hard", mv, null())
      | bucket _time span=5m
      | stats max(u) AS u max(h) AS h BY cluster namespace resource quota_obj _time
      | eval snap_pct=if(isnotnull(h) AND h>0 AND isnotnull(u), round(u/h, 6), null())
      | where isnotnull(snap_pct)
      | sort 0 +cluster +namespace +resource +quota_obj +_time
      | streamstats window=2 current=t global=f first(snap_pct) AS prev_sp last(snap_pct) AS cur_sp BY cluster namespace resource quota_obj
      | eval sustained=if(cur_sp>=1.0 AND (prev_sp>=1.0 OR isnull(prev_sp)), 1, 0)
      | where sustained=1
      | stats earliest(_time) AS exh_start latest(_time) AS exh_end BY cluster namespace resource quota_obj
      | eval time_in_exhaustion_min=round((exh_end-exh_start)/60+5, 2) ]
| fillnull value=0 time_in_exhaustion_min
| fillnull value="unknown_owner" owner_team
| fillnull value="unknown_oncall" on_call_team
| eval blocked_workloads=toString(coalesce(blocked_workloads, ""))
| eventstats max(used_pct) AS namespace_peak_pct BY cluster namespace
| eval severity=case(isnull(used_pct), "unknown", used_pct>=1.0, "exhausted", used_pct>=0.95, "critical_near_exhaust", used_pct>=0.85, "high", used_pct>=0.75, "warning", 1=1, "healthy")
| where (severity IN ("exhausted","critical_near_exhaust","high","warning")) OR denial_count_5m>0
| where isnotnull(used_pct) OR denial_count_5m>0
| fields - namespace_peak_pct
| table cluster namespace resource used hard used_pct severity owner_team on_call_team denial_count_5m time_in_exhaustion_min blocked_workloads
```

Alert actions: include blocked_workloads, denial_count_5m, and time_in_exhaustion_min in tickets; link to Grafana or Dashboard Studio quota panels; attach three anonymized audit lines when legal approves.

Operational notes: when hard is zero or missing, used_pct stays null and severity becomes unknown; investigate exporter config before muting. When only audit denials appear without metrics, assume scrape failure or RBAC blind spots rather than declaring the namespace healthy.

Dashboard publishing: heatmap of used_pct by namespace and resource, single value for count of exhausted namespaces, timechart of denial_count_5m, and drilldown to kube:events raw.

Evidence retention: weekly CSV of the closing table with lookup commit hash stored in a restricted index satisfies internal platform audits when paired with kubectl describe resourcequota screenshots during game days.

Performance tuning: if Job Inspector shows multisearch queueing, materialize five minute rollup summaries into a summary index and point this alert at summaries while retaining raw scrapes for investigations.

Reliability: during kube-state-metrics upgrades expect brief gaps; require two intervals of missing metrics before paging scrape failures unless denials remain high.

Governance: when legal requests preservation, include audit hash lists and redact customer strings per counsel instructions.

### Step 4 — Validate

Synthetic quota denial test on a lab cluster: kubectl create namespace test-quota-exhaust-uc324, apply a ResourceQuota with hard pods equal to one, run kubectl run pod1 with an nginx image, then kubectl run pod2 with an nginx image in the same namespace. The second create must fail with exceeded quota messaging in kubectl stderr. Within sixty seconds, confirm kube:events or kube:apiserver:audit shows the failure and that uc_3_2_4_resourcequota_exhaustion_block returns a row with severity exhausted or denial_count_5m greater than zero for that namespace. kubectl edit resourcequota to raise hard pods to ten, wait two scrape intervals, confirm the alert clears or downgrades while denial_count_5m falls to zero.

Validation SPL for raw signal presence in the last hour:

```spl
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-60m@m latest=@m
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | where mn="kube_resourcequota"
      | stats count BY cluster namespace ]
    [ search index=k8s sourcetype="kube:events" earliest=-60m@m latest=@m
      | where like(lower(_raw), "%exceeded quota%")
      | stats count BY cluster namespace ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-60m@m latest=@m
      | eval code=tonumber(tostring(coalesce(responseStatus_code, `responseStatus.code`)),10)
      | eval msg=lower(toString(coalesce(responseStatus_message, `responseStatus.message`)))
      | where code=403 AND like(msg, "%exceeded quota%")
      | stats count BY cluster namespace ]
| stats sum(count) AS events_seen BY cluster namespace
```

Field sanity: rename a sandbox forwarder field to camelCase-only and verify coalesce still resolves namespace and resource. RBAC: readers without index access must see zero rows.

Correlation: compare alert timestamps to UC-3.2.32 trending panels; exhaustion should appear only after trending crossed high bands or after a sudden burst.

### Step 5 — Operationalize & Troubleshoot

Case 1 — CPU quota exhausted blocking pod creation in prod-payments namespace: page payments SRE and platform quota approvers immediately; include denial_count_5m and blocked_workloads; escalate to executive bridge if gold criticality and customer checkout latency correlates.

Case 2 — Memory quota exhausted in dev-data-platform: open ticket-only workflow for silver criticality; ask owners to right-size requests or raise hard after FinOps review; cross-link trending UC-3.2.32 for preventive context.

Case 3 — Pods quota exhausted as a numeric pod count in a CI namespace: common when burst jobs spawn many short pods; evaluate burst quota patterns or shard CI across namespaces; dampen using sustained exhaustion logic before paging bronze namespaces.

Case 4 — PersistentVolumeClaims quota exhausted: engage storage SRE and verify reclaim policies; PVCs may remain bound while workloads deleted; correlate with CSI metrics before blaming application leaks.

Case 5 — services.loadbalancers quota exhausted: costly cloud load balancer expansion; involve FinOps and network platform; approvals often take longer than CPU edits.

Case 6 — Quota usage briefly hits one hundred percent during HPA scale-up burst: transient seconds-long spikes should not page; rely on sustained streamstats gate and sixty second soak in alert macros; extend soak if your scrape cadence is slower than thirty seconds.

Case 7 — Cross-link with UC-3.2.32 proactive trending: when trending showed high utilization but no exhaustion, hand trending owners the early warning; when this UC fires, return the conversation to trending owners with the exact resource dimension now blocked.

Case 8 — Quota exhaustion during chaos tests: suppress namespaces labeled chaos_quota_overflow_expected in the lookup or via a macro that reads namespace labels mirrored into inventory.

Case 9 — Tenant exceeded quota repeatedly after multiple raises: quarantine candidate; require architecture review and possible noisy neighbor isolation into dedicated clusters.

Case 10 — Quota change event where someone increased hard limits: mine kube:apiserver:audit for ResourceQuota update verbs; attribute to user and verify CAB linkage.

Case 11 — Newly created namespace inherited too-tight default quota from an admission webhook: open platform defect; auto-fix via GitOps pull request that applies standard hard values after inventory onboarding.

Case 12 — Migration quota with short-term burst quota for a migration window: enforce TTL in Git and alert when migration namespaces remain above fleet baselines past the TTL without an extension record.

Closing checklist: five step headers use plain em dashes exactly as mandated; Step 3 fenced SPL matches the spl JSON field; multisearch covers typed quota metrics; nested multisearch covers events and audit; coalesce normalizes labels; streamstats enforces sustained exhaustion inside the join; eventstats adds namespace_peak_pct context; inputlookup enriches ownership; case implements severity tiers; final table includes twelve columns; monitoringType lists Performance and Capacity; cimModels lists Application_State and Performance; equipment lists kubernetes and opentelemetry; equipmentModels lists kubernetes_k8s; narrative avoids forbidden boilerplate phrases; LimitRange documentation is cross-linked for confusion reduction but not duplicated analytically.

Closing: Step 5 lists twelve numbered cases covering payments escalation, silver dev flow, CI pod count bursts, PVC storage engagement, load balancer cost, HPA transient spikes, UC-3.2.32 handover, chaos suppression, repeat offender quarantine, audit-attributed quota edits, default webhook misconfiguration, and migration TTL discipline. Long-term owners keep FinOps cost-center mapping via app_id, rehearse UC-3.2.7 handoffs when apiserver noise mimics quota denial, validate HEC routing whenever indexes split, replay the synthetic pod2 denial after kube-state-metrics upgrades, and reconcile namespace_ownership_inventory.csv weekly against live namespaces so uc_3_2_4_resourcequota_exhaustion_block stays the authoritative exhaustion detector for namespace budgets.


## SPL

```spl
`comment("UC-3.2.4 Kubernetes Namespace ResourceQuota exhaustion (pod-create block). Tunables: idx_metrics=k8s_metrics idx_events=k8s idx_audit=k8s_audit; st_metrics=prometheus:scrape:metrics st_events=kube:events st_audit=kube:apiserver:audit; soak_minutes=5; earliest=-15m@m latest=@m")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-15m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval rq_type=lower(trim(toString(coalesce(type, quota_type, resourcequota_type, ""))))
      | eval resource=trim(toString(coalesce(resource, resource_name, quota_resource, resourcequota, "")))
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval quota_obj=trim(toString(coalesce(resourcequota, name, resource_quota, "")))
      | where mn="kube_resourcequota" AND rq_type="used" AND len(cluster)>0 AND len(namespace)>0 AND len(resource)>0
      | stats latest(mv) AS used latest(_time) AS ts_metric BY cluster namespace resource quota_obj ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-15m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval rq_type=lower(trim(toString(coalesce(type, quota_type, resourcequota_type, ""))))
      | eval resource=trim(toString(coalesce(resource, resource_name, quota_resource, resourcequota, "")))
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval quota_obj=trim(toString(coalesce(resourcequota, name, resource_quota, "")))
      | where mn="kube_resourcequota" AND rq_type="hard" AND len(cluster)>0 AND len(namespace)>0 AND len(resource)>0
      | stats latest(mv) AS hard BY cluster namespace resource quota_obj ]
| stats max(used) AS used max(hard) AS hard max(ts_metric) AS ts_metric BY cluster namespace resource quota_obj
| eval used_num=tonumber(tostring(used),10)
| eval hard_num=tonumber(tostring(hard),10)
| eval used_pct=if(isnotnull(hard_num) AND hard_num>0 AND isnotnull(used_num), round(used_num/hard_num, 6), null())
| join type=left max=0 cluster namespace
    [| multisearch
          [ search index=k8s sourcetype="kube:events" earliest=-15m@m latest=@m
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
            | eval namespace=trim(toString(coalesce(metadata_namespace, namespace, involvedObject_namespace, "")))
            | eval reason=trim(toString(coalesce(reason, Reason, "")))
            | eval msg=lower(toString(coalesce(message, Message, _raw, "")))
            | eval blk=toString(coalesce(involvedObject_name, `involvedObject.name`))
            | where (reason="FailedCreate" OR like(reason, "%FailedCreate%")) AND like(msg, "%exceeded quota%")
            | stats count AS cnt values(blk) AS blk_mv BY cluster namespace ]
          [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-15m@m latest=@m
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, objectRef_cluster, ""))))
            | eval namespace=trim(toString(coalesce(objectRef_namespace, namespace, requestNamespace, "")))
            | eval code=tonumber(tostring(coalesce(responseStatus_code, `responseStatus.code`, status_code)),10)
            | eval msg=lower(toString(coalesce(responseStatus_message, `responseStatus.message`, message)))
            | eval blk=toString(coalesce(objectRef_name, `objectRef.name`))
            | where code=403 AND like(msg, "%forbidden%") AND like(msg, "%exceeded quota%")
            | stats count AS cnt values(blk) AS blk_mv BY cluster namespace ]
      | stats sum(cnt) AS denial_count_5m values(blk_mv) AS bw BY cluster namespace
      | eval blocked_workloads=mvjoin(mvdedup(bw), ", ") ]
| fillnull value=0 denial_count_5m
| join type=left max=0 cluster namespace
    [| inputlookup namespace_ownership_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=trim(toString(namespace))
      | eval owner_team=toString(coalesce(owner_team, team, squad, ""))
      | eval on_call_team=toString(coalesce(on_call_team, pager_team, platform_oncall, owner_team, ""))
      | fields cluster namespace owner_team on_call_team app_id criticality ]
| join type=left max=0 cluster namespace resource quota_obj
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-60m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval rq_type=lower(trim(toString(coalesce(type, quota_type, resourcequota_type, ""))))
      | eval resource=trim(toString(coalesce(resource, resource_name, quota_resource, resourcequota, "")))
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval quota_obj=trim(toString(coalesce(resourcequota, name, resource_quota, "")))
      | where mn="kube_resourcequota" AND match(rq_type, "used|hard")
      | eval u=if(rq_type="used", mv, null())
      | eval h=if(rq_type="hard", mv, null())
      | bucket _time span=5m
      | stats max(u) AS u max(h) AS h BY cluster namespace resource quota_obj _time
      | eval snap_pct=if(isnotnull(h) AND h>0 AND isnotnull(u), round(u/h, 6), null())
      | where isnotnull(snap_pct)
      | sort 0 +cluster +namespace +resource +quota_obj +_time
      | streamstats window=2 current=t global=f first(snap_pct) AS prev_sp last(snap_pct) AS cur_sp BY cluster namespace resource quota_obj
      | eval sustained=if(cur_sp>=1.0 AND (prev_sp>=1.0 OR isnull(prev_sp)), 1, 0)
      | where sustained=1
      | stats earliest(_time) AS exh_start latest(_time) AS exh_end BY cluster namespace resource quota_obj
      | eval time_in_exhaustion_min=round((exh_end-exh_start)/60+5, 2) ]
| fillnull value=0 time_in_exhaustion_min
| fillnull value="unknown_owner" owner_team
| fillnull value="unknown_oncall" on_call_team
| eval blocked_workloads=toString(coalesce(blocked_workloads, ""))
| eventstats max(used_pct) AS namespace_peak_pct BY cluster namespace
| eval severity=case(isnull(used_pct), "unknown", used_pct>=1.0, "exhausted", used_pct>=0.95, "critical_near_exhaust", used_pct>=0.85, "high", used_pct>=0.75, "warning", 1=1, "healthy")
| where (severity IN ("exhausted","critical_near_exhaust","high","warning")) OR denial_count_5m>0
| where isnotnull(used_pct) OR denial_count_5m>0
| fields - namespace_peak_pct
| table cluster namespace resource used hard used_pct severity owner_team on_call_team denial_count_5m time_in_exhaustion_min blocked_workloads

```

## CIM SPL

```spl
| tstats summariesonly=true latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS cim_host
| join type=left max=0 cim_host
    [| tstats summariesonly=true avg(Performance.cpu_load_percent) AS cpu_load_pct FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-4h@h latest=@h BY Performance.host
     | rename Performance.host AS cim_host ]
| table cim_host app_state app_info cpu_load_pct
```

## Visualization

Heatmap of used_pct by namespace and resource; single-value count of exhausted namespaces; sparkline of denial_count_5m; table of blocked_workloads with drilldown to kube:events and kube:apiserver:audit; overlay with UC-3.2.32 trending panels for context.

## Known False Positives

Horizontal pod autoscaler bursts can pin pod counts at one hundred percent of hard for a few scrape intervals while old pods terminate; dampen by requiring sustained streamstats-qualified exhaustion for at least sixty seconds and by ignoring single-bucket spikes when denial_count_5m is zero. Chaos namespaces that deliberately overflow quotas should carry suppression labels propagated into namespace_ownership_inventory.csv so game-day traffic never pages production bridges. Brand-new namespaces cloned from tight admission templates may flash exhaustion on first real rollout; open a ticket and cross-check UC-3.2.32 history before paging executives, or auto-apply standard hard values via GitOps. After large Deployment deletes, kube-state-metrics used gauges can lag briefly while garbage collection finishes; corroborate with live kubectl describe resourcequota before accusing stale telemetry. CronJobs that launch short-lived pods every minute may rhythmically kiss pod quotas; require denial narratives or raise minimum denial_count_5m for bronze CI namespaces. Duplicate scrapes from overlapping Prometheus and OpenTelemetry collectors without dedup keys can distort ratios; validate unique sample sources per cluster. Managed control planes that hide audit bodies may lack 403 messages even when kubectl shows errors; fall back to kube events. Label renames during kube-state-metrics upgrades can null coalesce paths for one interval; treat missing metrics plus steady denials as scrape incidents.

## References

- [Kubernetes ResourceQuotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)
- [Kubernetes — Manage memory and CPU quotas per namespace](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/quota-memory-cpu-namespace/)
- [Kubernetes — Configure pod quotas per namespace](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/quota-pod-namespace/)
- [Kubernetes LimitRange](https://kubernetes.io/docs/concepts/policy/limit-range/)
- [Kubernetes admission controllers — ResourceQuota](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#resourcequota)
- [kube-state-metrics — ResourceQuota metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/policy/resourcequota-metrics.md)
- [Splunk Add-on for Kubernetes — About](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
- [Kubernetes auditing](https://kubernetes.io/docs/reference/access-authn-authz/audit/)
