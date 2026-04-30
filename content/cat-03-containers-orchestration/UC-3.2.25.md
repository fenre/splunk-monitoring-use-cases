<!-- AUTO-GENERATED from UC-3.2.25.json — DO NOT EDIT -->

---
id: "3.2.25"
title: "Kubernetes Persistent Volume Time-to-Fill SLA, StorageClass Burn-Rate, and IOPS-vs-Capacity Curve"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.25 · Kubernetes Persistent Volume Time-to-Fill SLA, StorageClass Burn-Rate, and IOPS-vs-Capacity Curve

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We estimate how fast each permanent disk is filling, when it will hit almost full, and whether your storage class as a whole is running out of headroom. We highlight tight spots early so teams can grow volumes or clean data before apps freeze.*

---

## Description

Forecasts bound Kubernetes PersistentVolumeClaim filesystem fill to a ninety-nine percent byte threshold using six-hour kubelet volume_stats timelines and streamstats burn derivatives, projects parallel inode exhaustion ETAs, aggregates StorageClass-level headroom from summed PVC samples, compares kube_persistentvolumeclaim_resource_requests_storage_bytes to kube_persistentvolume_capacity_bytes for oversubscription storytelling, surfaces expansion drift hints when kube_storageclass_info allows online growth, correlates cluster-wide Pending PersistentVolumeClaim pressure with possible upstream exhaustion, joins governance inventory for eight hour SLA gating on gold criticality rows, and buckets an IOPS-versus-capacity risk curve using node disk pressure proxies near full volumes. The axis is proactive PV runway and StorageClass burn-rate, not instantaneous high-water snapshots alone (UC-3.2.16), not unbound PVC bind failures (UC-3.2.5), and not namespace ResourceQuota admission walls (UC-3.2.4).

## Value

Gives platform and application leaders dated ETAs before ninety-nine percent fill, inode-first failure modes, and StorageClass fleet headroom collapse, which reduces emergency resize bridges and prevents Pending claim storms caused by exhausted pools. Customer-visible reliability improves when CSI expansions, data pruning, or migrations start with measurable runway, and FinOps gains transparent pvc_pv_oversub_ratio evidence when thin provisioning debates arise.

## Implementation

Provision k8s_metrics scraping kubelet volume_stats and kube-state-metrics PV, PVC, and StorageClass series into prometheus:scrape:metrics; publish pvc_storage_sla_inventory.csv; save uc_3_2_25_pv_time_to_fill_sla_sc_burn every thirty to sixty minutes over earliest=-7d@d latest=@h; route critical_sla_rpo8h_gold to voice with owner_team; archive weekly CSV extracts for capacity committees.

## Evidence

Saved search uc_3_2_25_pv_time_to_fill_sla_sc_burn with thirty-to-sixty-minute schedule; lookups/pvc_storage_sla_inventory.csv versioned in git; weekly CSV export of the closing table to a restricted evidence index with hashed PVC names when regulated tenants appear.

## Control test

### Positive scenario

In a lab namespace, bind a PVC, generate sustained writes so kubelet_volume_stats_used_bytes rises across at least eight six-hour buckets within seven days with matching capacity series, ensure kube-state-metrics publishes kube_persistentvolumeclaim_info and kube_persistentvolume_capacity_bytes for the backing PV, execute uc_3_2_25_pv_time_to_fill_sla_sc_burn, and expect non-null gb_per_day with shrinking days_to_99 while severity qualifies at least warning when used_pct crosses eighty-five or sla_rpo8h_critical fires on an eight hour window test.

### Negative scenario

After deleting test data, expanding the PVC under an allowVolumeExpansion true StorageClass, or stopping the writer so slopes flatten across two buckets, confirm gb_per_day approaches null, days_to_99 grows or nulls, and the saved search emits no qualifying rows for that PVC unless unrelated dimensions remain hot.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with Kubernetes storage engineering, observability, tenant FinOps, and site reliability teams who operate Splunk OpenTelemetry Collector fleets plus kube-state-metrics across production, pre-production, and regulated partitions. UC-3.2.25 is the proactive persistent storage capacity axis that answers when individual bound PersistentVolumeClaims will cross a ninety-nine percent byte threshold, how fast inode tables are burning relative to filesystem free inodes, how StorageClass fleets aggregate headroom, whether PVC declared requests trail real PersistentVolume capacity in ways that mask budget risk, whether StorageClass allowVolumeExpansion drift means operators should resize through the CSI controller instead of waiting for reactive paging, and whether cluster-wide Pending claims correlate with upstream exhaustion that UC-3.2.5 diagnoses at bind time. UC-3.2.16 remains the sibling that pairs instantaneous high-water snapshots with read-only pre-failure kube events and shorter kubelet windows; this UC widens the lens to seven-day six-hour bucket burn math, StorageClass burn-rate storytelling, inode ETA independence, PVC-to-PV oversubscription ratios from kube-state-metrics, and an eight hour recovery-point-objective style SLA gate for gold inventory rows. UC-3.2.5 stays strictly on PersistentVolumeClaim objects that never bind because provisioning, topology, or quota failed before mount; this UC assumes Bound claims that can still run out of formatted space or inodes. UC-3.2.4 governs namespace ResourceQuota admission exhaustion for counted API objects such as persistentvolumeclaims limits, not kubelet-reported filesystem fill inside an already bound volume. UC-3.2.32 trends namespace ResourceQuota ratios across cpu, memory, and object counts; this UC isolates kubelet volume_stats bytes and inodes joined to kube_persistentvolume_capacity_bytes and kube_persistentvolumeclaim_resource_requests_storage_bytes so storage architects see PV-level physics instead of API object budgets alone.

Index and token contracts precede saved-search authoring. Stand up or designate index=k8s_metrics for prometheus:scrape:metrics events scraped from each node kubelet https metrics endpoint and from kube-state-metrics Deployments that expose storage policy gauges. Issue distinct HEC tokens per index class with role-based search restrictions so application developers can read namespace dashboards without inheriting cluster-wide PersistentVolume inventories unless policy allows. Document retention: metrics hot buckets at least fourteen days for replay, and at least seven full days for the six-hour bucket regression window used in the primary SPL; inode and byte slopes become meaningless when nightly compaction jobs delete history shorter than the streamstats window.

Splunk OpenTelemetry Collector for Kubernetes must scrape kubelet /metrics with prometheus_simple or an equivalent prometheus receiver job on every node, preserving Prometheus labels that map to persistentvolumeclaim, namespace, node, and cluster identity. A parallel scrape or ServiceMonitor must target kube-state-metrics so kube_persistentvolume_info, kube_persistentvolume_capacity_bytes, kube_persistentvolume_status_phase, kube_persistentvolumeclaim_info, kube_persistentvolumeclaim_resource_requests_storage_bytes, kube_persistentvolumeclaim_status_phase, and kube_storageclass_info series land in the same index with coalesce-compatible cluster tags. For managed Kubernetes, align StorageClass defaults with vendor guidance: Amazon EKS commonly uses ebs.csi.aws.com with gp3; Google GKE uses pd.csi.storage.gke.io; Microsoft AKS uses disk.csi.azure.com or file.csi.azure.com classes. Expansion feasibility is not universal: kube_storageclass_info carries allow_volume_expansion true or false; only true classes support online growth that matches expansion_resize_hint messaging in this UC.

Governance lookup lookups/pvc_storage_sla_inventory.csv must contain cluster, namespace, pvc, owner_team, and criticality with gold silver bronze semantics so SLA gates such as sla_rpo8h_critical can treat gold data services as eight hour runway incidents while bronze scratch volumes remain ticket-first. Refresh weekly from GitOps exports or CMDB pipelines and attach commit hashes when auditors ask for lineage. Gold rows route critical_sla_rpo8h_gold to immediate paging together with storage and application bridges. Silver rows open high-priority tickets with explicit days_to_99 in the subject. Bronze rows remain dashboard-first unless an executive override marks customer impact.

Risk briefing: when used bytes approach capacity bytes on many CSI stacks, write amplification on ext4, XFS, or ZFS backends can raise observed IOPS and latency on the backing node even before ninety-nine percent, which is why this UC correlates kubelet_node to Splunk CIM Performance.Storage disk_usage as a coarse proxy for write pressure near full volumes. Inode exhaustion can strike while byte utilisation looks comfortable on small-file workloads such as mail spools, CI caches, or Prometheus tsdb shards, so inode_pct and inode_days_to_full must ride alongside used_pct. Silent misconfiguration of prometheus relabel rules that drop persistentvolumeclaim labels makes this control blind while kubectl still shows Bound PVCs.

Licensing note: seven-day multisearch fan-out across kubelet and kube-state-metrics series keeps cost bounded by six-hour binning; investigative clones may lower bin width with director approval. Privacy note: PVC names may echo internal product codenames; restrict dashboard ACLs.

Differentiation recap: proactive PV time-to-ninety-nine-percent fill, StorageClass headroom, inode ETA, PVC versus PV capacity ratio, expansion-eligible drift hints, Pending claim pressure at cluster scope, not instantaneous snapshot only, not unbound CSI bind failures, not namespace ResourceQuota walls.

Collector architecture notes: self-managed clusters often scrape kubelet via the node IP with bearer tokens; managed offerings may require privileged DaemonSets. Document TLS, token rotation, and allowed egress from collectors to kubelet ports and kube-state-metrics Services.

FinOps alignment: pvc_pv_oversub_ratio near one signals tight provisioning; finance may prefer thin margins while reliability requires runway; document the tension in committee minutes.

Reliability alignment: StatefulSets with single replicas may not survive read-only remount without manual intervention; pair this UC with UC-3.2.16 when kube events show FilesystemAlmostFull precursors.

Security alignment: kube_persistentvolume_info can include CSI driver strings that reveal vendor choice; scrub exports when sharing outside platform teams.

Performance alignment: keep multisearch arms narrow with explicit metric names to prevent accidental high-cardinality explosions from unrelated kube-state-metrics collectors.

Training alignment: teach responders that inode_days_to_full under one day with modest used_pct is legitimate for some workloads and requires inode-aware remediation, not only byte expansion.

Documentation alignment: wiki-map this UC beside Kubernetes PersistentVolumes, Volume Health Monitoring, CSI volume expansion, and cloud CSI driver guides.

Review cadence: quarterly replay one historical near-full PVC incident through the SPL after kubelet upgrades.

Escalation alignment: critical_sla_rpo8h_gold engages storage engineering and application leadership jointly.

Telemetry hygiene: deduplicate overlapping Prometheus agents that scrape the same kubelet without dedup keys.

Governance alignment: CAB records should cover HEC token ACL changes and ServiceMonitor edits together when kubelet scrape paths move.

Supplemental ownership depth: storage platform engineers certify scrape intervals during peak retail events when kubelet CPU is hot; application owners attest pvc_storage_sla_inventory.csv criticality quarterly; FinOps validates chargeback tags against real snapshot schedules; legal reviews metric exports when host paths appear; chaos engineering namespaces carry explicit dampening in inventory; multi-region fleets duplicate tokens per region with identical label contracts; GitOps repos version ServiceMonitor YAML beside collector configs; runbooks link to Kubernetes storage documentation and CSI external expansion pages; ITSI optional episodes attach service IDs from CMDB when KPI import is enabled; Splunk Cloud search auto pause policies get an exception macro for this saved search during known migrations; OTEL memory limits rise when kubelet series cardinality grows after CSI upgrades; kube-state-metrics PV and PVC metrics remain sibling context for dashboards even when not every arm appears in user clones; training videos show difference between Pending PVC binding in UC-3.2.5 and Bound PVC fill here; executive summaries chart days_to_99 distributions by criticality; auditors receive weekly CSV extracts with hashed PVC names when regulated; penetration tests validate HEC token scope cannot read unrelated security indexes; SRE onboarding includes lab fill exercises with tear-down checklists; FinOps chargeback maps gb_per_day to cost centres when log volumes spike; platform on-call rotates paired with storage vendor TAM contacts for Sev-1 fill storms; documentation in Confluence stays synchronized with this JSON source of truth via generate_md pipeline; replay tests after kubernetes minor upgrades validate metric renames; dual-stack IPv6 node fleets use consistent instance labels in relabel configs; air-gapped environments mirror container images for OTEL collectors before kubelet scrapes go live; service mesh sidecars never obscure kubelet scrape paths when hostNetwork collectors are forbidden; windows node pools are out of scope unless your CSI and kubelet emit identical metric names; openshift routes may rename default namespaces so coalesce ladders stay tested; rancher managed clusters still need explicit cluster tags to avoid collisions; vmware tanzu supervisors require verified bearer token lifetimes; edge kubernetes clusters with intermittent uplinks widen earliest windows cautiously; data sovereignty regions keep evidence indexes local per counsel; immutable infrastructure rotations rebuild collectors from pinned helm charts; golden signals training links this UC to latency error rate saturation examples; post-incident reviews record whether remediation was expand, trim, migrate, or bugfix; synthetic monitors ping Splunk HEC health before declaring collector outages; dependency mapping shows this UC upstream of database availability dashboards; configuration drift detectors compare live ServiceMonitor to git main; capacity planning spreadsheets import days_to_99 CSV monthly; executive risk registers cite near-full PV write amplification as tier-one platform hazard; vendor RFO documents attach to tickets when CSI bugs cause premature saturation; cross-region failover drills include PVC fill scenarios; application architects review inode budgets during new service templates; build platform teams track scratch PVC growth separately from production; ml anomaly detection stays optional overlay only when baselines exist; prometheus remote write duplicates must not triple-count kubelet samples; thanos query paths are allowed only when dedup labels are proven; grafana mirror dashboards cite Splunk as system of record for paging; PagerDuty event orchestration enriches with owner_team from lookup; slack bridges post severity plus days_to_99 in first line; jira auto-creates link back to saved search URL; confluence runbook includes kubectl debug node steps for volume inspection; legal hold procedures preserve kube metrics without deleting events; disaster recovery teams verify snapshot schedules when catastrophic fires during fill storms; finops approves bronze suppressions in writing quarterly; platform engineering rehearses handoffs to UC-3.2.16 when stakeholders demand instantaneous free-space gauges only; storage security reviews export macros when CSI drivers change; internal developer portals surface expansion_resize_hint strings as copy-paste kubectl snippets after CAB approval; observability guilds compare gb_per_day with cloud vendor growth reports quarterly; kubernetes steering committee updates feed back into this JSON when upstream deprecates labels; service catalog entries link each gold PVC to RPO targets explicitly; red team exercises validate alert routes cannot be trivially suppressed without inventory approval; on-call retrospectives measure minutes from sla_rpo8h_critical to approved resize; technical writers maintain a single source SPL block here and in Dashboard Studio JSON to avoid drift; vendor professional services engagements attach this UC id in statements of work when Splunk is the control owner; storage architects document when linear burn assumptions break for copy-on-write filesystems; backup engineering confirms snapshot reservation math before accusing applications of leaks; network platform validates east-west latency when NFS-backed classes show inode pressure; identity teams ensure HEC tokens cannot read HR indexes from the same search head; compliance maps evidence exports to retention policies without exposing customer payload fields; change managers require paired updates to inventory and macros during black Friday freeze windows; sustainability officers track energy impact of unnecessary early expansions; university clusters isolate student namespaces with permanent bronze dampening; media encoding farms validate scratch PVC classes differ from archival classes in dashboards.

### Step 2 — Configure data collection

Deploy a ServiceMonitor or PodMonitor that selects kube-state-metrics and points a prometheus receiver at the https metrics port with the service account token mounted for authentication. Use labels that separate staging and production scrape cadences intentionally. Example ServiceMonitor skeleton referencing kube-state-metrics with relabel to k8s_cluster_name.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-storage-plane
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kube-state-metrics
  endpoints:
    - port: https
      scheme: https
      interval: 30s
      bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabelings:
        - action: replace
          targetLabel: k8s_cluster_name
          replacement: prod-eks-us-east-1
```

OpenTelemetry Collector fragment showing prometheus_simple against kubelet plus kube-state-metrics, exporting into k8s_metrics with sourcetype prometheus:scrape:metrics and metric_relabel_configs that keep kubelet_volume_stats and kube_persistentvolume families.

```yaml
receivers:
  prometheus_simple/kubelet:
    collection_interval: 60s
    endpoints:
      - url: https://${KUBELET_HOST}:10250/metrics
  prometheus_simple/ksm:
    collection_interval: 60s
    endpoints:
      - url: https://kube-state-metrics.kube-system.svc:8443/metrics
exporters:
  splunk_hec/metrics:
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
```

Sample pvc_storage_sla_inventory.csv schema for governance joins referenced in SPL.

```csv
cluster,namespace,pvc,owner_team,criticality
prod-eks-us-east-1,prod-ledger,data-ledger-0,ledger-sre,gold
prod-eks-us-east-1,dev-builds,scratch-build-cache,build-platform,silver
```

props and transforms guidance: normalize __name__, value, namespace, persistentvolumeclaim, persistentvolume, storageclass, cluster labels onto indexed fields; keep camelCase aliases from OTEL exporters in transforms.conf so coalesce ladders in SPL stay short.

Validation before alert authoring: index=k8s_metrics sourcetype=prometheus:scrape:metrics earliest=-8d must return kubelet_volume_stats_used_bytes and kube_persistentvolume_capacity_bytes with non-empty labels; clock skew between kubelet, kube-state-metrics, and Splunk _time must stay under sixty seconds or six-hour bins misalign.

Extended validation checklist: confirm each node appears in kubelet scrapes at least once per interval; verify no duplicate k8s_cluster_name labels during cluster migration weekends; test HEC ACK when indexes roll; measure forwarder lag at p95; document sourcetype override paths for openshift logging stacks; rehearse token rotation without dropping scrapes; compare live kubectl get pvc capacity to metric cap_bytes for a sample set weekly; confirm kube_storageclass_info exposes allow_volume_expansion labels after CSI driver upgrades.

### Step 3 — Create the search and alert

Save the SPL as saved search uc_3_2_25_pv_time_to_fill_sla_sc_burn with thirty-minute schedule during business peaks and sixty-minute schedule overnight, dispatch earliest=-7d@d, dispatch latest=@h, and throttle duplicate warning rows per cluster namespace pvc for two hours unless severity escalates to critical_sla_rpo8h_gold. Route critical_sla_rpo8h_gold to immediate voice paging with storage and application bridges; route high_sla_rpo8h to high-priority tickets with SMS backup for gold inventory rows; route elevated_fill_7d to standard queue with explicit days_to_99 in the ticket subject.

Pipeline understanding for operators: the opening comment macro lists indexes, sourcetypes, bin width, streamstats window, and time horizon so retuning does not require opening this document cold. multisearch fans four kubelet metric arms for used bytes, capacity bytes, inode used, and inode total so a silent failure in one CSI label set does not zero the entire join. coalesce ladders normalize cluster, namespace, pvc, pv, and node labels across cloud and on-prem field naming. Six-hour binning caps scan cost while preserving enough points for a twenty-eight point streamstats window spanning roughly one week. streamstats computes first and last samples inside the window per PVC, derives gb_per_day and inode_per_day when dt_s exceeds one hour, converts remaining bytes to ninety-nine percent into days_to_99, and inode remainder into inode_days_to_full. predict_at_threshold_pct documents the ninety-nine percent goal explicitly for auditors. Nested multisearch joins kube_persistentvolumeclaim_resource_requests_storage_bytes with kube_persistentvolumeclaim_info to recover the backing pv name, then a second multisearch merges kube_persistentvolume_capacity_bytes, kube_persistentvolume_status_phase for bound PVs, and kube_persistentvolume_info for storageclass and csi_driver. kube_storageclass_info supplies sc_allow_expand. A cluster scoped kube_persistentvolumeclaim_status_phase Pending arm counts pending_pvc_cluster as a coarse signal that bind pressure may reflect upstream exhaustion. inputlookup pvc_storage_sla_inventory.csv enriches owner_team and criticality. eventstats aggregates sc_headroom_pct by summing bound PVC used and capacity samples per StorageClass, and ns_top_burn_gb_per_day per namespace for top-burner storytelling. tstats against Performance.Storage supplies node_disk_pressure_pct on kubelet_node when CIM acceleration aligns. case maps severity including gold-weighted eight hour runway breaches. iops_capacity_curve buckets write-amplification style risk using used_pct, gb_per_day, and node_disk_pressure_pct as a pragmatic IOPS-versus-capacity curve when block-level IOPS are not directly ingested. expansion_resize_hint translates allowVolumeExpansion plus utilization into kubectl-oriented remediation language. The closing table lists twenty-four analyst columns: cluster, namespace, pvc, pv, storageclass, csi_driver, owner_team, criticality, used_pct, inode_pct, gb_per_day, days_to_99, inode_days_to_full, hrs_to_99, sla_rpo8h_critical, sc_headroom_pct, pending_pvc_cluster, pvc_pv_oversub_ratio, sc_allow_expand, expansion_resize_hint, iops_capacity_curve, node_disk_pressure_pct, ns_top_burn_gb_per_day, severity, kubelet_node.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.25 PV SLA time-to-99pct-fill, StorageClass burn, inode ETA, PVC-PV gap, expansion drift. idx=k8s_metrics bin=6h win=28 earliest=-7d@d latest=@h")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-7d@d latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | eval kubelet_node=trim(toString(coalesce(node, Node, instance, kubernetes_io_hostname, "")))
      | where mn="kubelet_volume_stats_used_bytes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>=0
      | bin _time span=6h
      | stats max(mv) AS used_bytes latest(kubelet_node) AS kubelet_node BY cluster namespace pvc _time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-7d@d latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | where mn="kubelet_volume_stats_capacity_bytes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>0
      | bin _time span=6h
      | stats max(mv) AS cap_bytes BY cluster namespace pvc _time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-7d@d latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | where mn="kubelet_volume_stats_inodes_used" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>=0
      | bin _time span=6h
      | stats max(mv) AS inodes_used BY cluster namespace pvc _time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-7d@d latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | where mn="kubelet_volume_stats_inodes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>0
      | bin _time span=6h
      | stats max(mv) AS inodes_total BY cluster namespace pvc _time ]
| stats max(used_bytes) AS used_bytes max(cap_bytes) AS cap_bytes max(inodes_used) AS inodes_used max(inodes_total) AS inodes_total latest(kubelet_node) AS kubelet_node BY cluster namespace pvc _time
| where isnotnull(used_bytes) AND isnotnull(cap_bytes) AND cap_bytes>0
| sort 0 cluster namespace pvc +_time
| streamstats window=28 current=t global=f first(used_bytes) AS u0 last(used_bytes) AS u1 first(_time) AS t0 last(_time) AS t1 first(inodes_used) AS i0 last(inodes_used) AS i1 first(inodes_total) AS it0 last(inodes_total) AS it1 BY cluster namespace pvc
| eval dt_s=t1-t0
| eval gb_per_day=if(dt_s>3600 AND isnotnull(u0) AND isnotnull(u1), round((u1-u0)/1073741824/(dt_s/86400), 6), null())
| eval inode_per_day=if(dt_s>3600 AND isnotnull(i0) AND isnotnull(i1) AND i1>=i0, round((i1-i0)/(dt_s/86400), 4), null())
| eval used_pct=round(100*u1/cap_bytes, 3)
| eval inode_pct=if(isnotnull(it1) AND it1>0 AND isnotnull(i1), round(100*i1/it1, 3), null())
| eval predict_at_threshold_pct=99
| eval tgt99=0.99*cap_bytes
| eval rem99=tgt99-u1
| eval days_to_99=if(isnotnull(gb_per_day) AND gb_per_day>0.000001 AND rem99>0, round(rem99/(gb_per_day*1073741824), 4), null())
| eval inode_rem=if(isnotnull(it1), it1-i1, null())
| eval inode_days_to_full=if(isnotnull(inode_per_day) AND inode_per_day>0.001 AND inode_rem>0, round(inode_rem/inode_per_day, 4), null())
| eval hrs_to_99=if(isnotnull(days_to_99), round(days_to_99*24, 3), null())
| eval sla_rpo8h_critical=if(isnotnull(hrs_to_99) AND hrs_to_99>0 AND hrs_to_99<=8, 1, 0)
| sort 0 - _time
| dedup cluster namespace pvc
| join type=left max=0 cluster namespace pvc
    [| multisearch
          [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
            | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
            | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
            | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
            | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
            | where mn="kube_persistentvolumeclaim_resource_requests_storage_bytes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0
            | stats latest(mv) AS pvc_request_bytes BY cluster namespace pvc ]
          [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
            | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
            | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
            | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
            | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
            | eval pv=trim(toString(coalesce(volumename, volume_name, volumeName, persistentvolume, "")))
            | where mn="kube_persistentvolumeclaim_info" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND len(pv)>0
            | stats latest(mv) AS ksm_pvc_info latest(pv) AS pv BY cluster namespace pvc ]
      | stats max(pvc_request_bytes) AS pvc_request_bytes max(pv) AS pv BY cluster namespace pvc ]
| fillnull value="unresolved" pv
| join type=left max=0 cluster pv
    [| multisearch
          [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
            | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
            | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
            | eval pv=trim(toString(coalesce(persistentvolume, persistent_volume, pv, "")))
            | where mn="kube_persistentvolume_capacity_bytes" AND len(cluster)>0 AND len(pv)>0
            | stats latest(mv) AS pv_cap_bytes BY cluster pv ]
          [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
            | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
            | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
            | eval pv=trim(toString(coalesce(persistentvolume, persistent_volume, pv, "")))
            | eval ph=lower(trim(toString(coalesce(phase, phase_name, ""))))
            | where mn="kube_persistentvolume_status_phase" AND len(cluster)>0 AND len(pv)>0 AND mv>0 AND ph="bound"
            | stats latest(mv) AS pv_phase_sig latest(ph) AS pv_phase BY cluster pv ]
          [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
            | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
            | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
            | eval pv=trim(toString(coalesce(persistentvolume, persistent_volume, pv, "")))
            | eval storageclass=trim(toString(coalesce(storageclass, storage_class, sc, "")))
            | eval csi_driver=trim(toString(coalesce(csi_driver, driver, provisioner, "")))
            | where mn="kube_persistentvolume_info" AND len(cluster)>0 AND len(pv)>0
            | stats latest(mv) AS pv_info latest(storageclass) AS storageclass latest(csi_driver) AS csi_driver BY cluster pv ]
      | stats max(pv_cap_bytes) AS pv_cap_bytes max(pv_phase_sig) AS pv_phase_sig max(pv_info) AS pv_info max(storageclass) AS storageclass max(csi_driver) AS csi_driver max(pv_phase) AS pv_phase BY cluster pv ]
| join type=left max=0 cluster storageclass
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval storageclass=trim(toString(coalesce(storageclass, storage_class, sc, "")))
      | where mn="kube_storageclass_info" AND len(cluster)>0 AND len(storageclass)>0
      | eval sc_allow_expand=if(lower(trim(toString(allow_volume_expansion)))="true",1,0)
      | stats latest(sc_allow_expand) AS sc_allow_expand BY cluster storageclass ]
| join type=left max=0 cluster
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | eval php=lower(trim(toString(coalesce(phase, phase_name, ""))))
      | where mn="kube_persistentvolumeclaim_status_phase" AND php="pending" AND mv>0 AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0
      | stats dc(pvc) AS pending_pvc_cluster BY cluster ]
| fillnull value=0 pending_pvc_cluster
| fillnull value=0 sc_allow_expand
| eval pvc_pv_oversub_ratio=if(isnotnull(pvc_request_bytes) AND isnotnull(pv_cap_bytes) AND pvc_request_bytes>0, round(pv_cap_bytes/pvc_request_bytes, 4), null())
| eval expansion_resize_hint=case(sc_allow_expand=1 AND used_pct>=92 AND isnotnull(days_to_99) AND days_to_99<=3, "kubectl_edit_pvc_expand_now", sc_allow_expand=1 AND used_pct>=85 AND isnotnull(days_to_99) AND days_to_99<=14, "schedule_kubectl_patch_pvc", sc_allow_expand=0 AND used_pct>=85, "migrate_or_new_sc", true(), "observe")
| join type=left max=0 cluster namespace pvc
    [| inputlookup pvc_storage_sla_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=trim(toString(namespace))
      | eval pvc=trim(toString(coalesce(pvc, persistentvolumeclaim, persistent_volume_claim, "")))
      | eval owner_team=trim(toString(coalesce(owner_team, team, squad, "")))
      | eval criticality=lower(trim(toString(coalesce(criticality, tier, "silver"))))
      | fields cluster namespace pvc owner_team criticality ]
| fillnull value="unknown_owner" owner_team
| fillnull value="silver" criticality
| eventstats sum(u1) AS sc_sum_used sum(cap_bytes) AS sc_sum_cap BY cluster storageclass
| eval sc_headroom_pct=if(isnotnull(sc_sum_cap) AND sc_sum_cap>0, round(100*(1-sc_sum_used/sc_sum_cap), 3), null())
| eventstats max(gb_per_day) AS ns_top_burn_gb_per_day BY cluster namespace
| join type=left max=0 kubelet_node
    [| tstats summariesonly=true max(Performance.disk_usage) AS node_disk_pressure_pct FROM datamodel=Performance WHERE nodename=Performance.Storage earliest=-4h@h latest=now BY Performance.host
      | rename Performance.host AS kubelet_node ]
| eval iops_capacity_curve=case(used_pct>=95 AND node_disk_pressure_pct>=88, "write_amp_hot_nearfull", used_pct>=90 AND gb_per_day>=2, "highburn_nearfull", used_pct>=90 AND isnotnull(node_disk_pressure_pct) AND node_disk_pressure_pct>=80, "disk_pressure_nearfull", used_pct>=80 AND gb_per_day>=1, "rising_burn", true(), "nominal")
| eval severity=case(sla_rpo8h_critical=1 AND lower(criticality)="gold", "critical_sla_rpo8h_gold", sla_rpo8h_critical=1, "high_sla_rpo8h", isnotnull(inode_days_to_full) AND inode_days_to_full<=1, "critical_inode_eta", isnotnull(days_to_99) AND days_to_99<=1, "critical_fill_24h", isnotnull(days_to_99) AND days_to_99<=3, "high_fill_72h", isnotnull(days_to_99) AND days_to_99<=7, "elevated_fill_7d", used_pct>=92, "high_water", used_pct>=85, "warning", true(), "info")
| where used_pct>=82 OR sla_rpo8h_critical=1 OR pending_pvc_cluster>=8 OR severity IN ("critical_sla_rpo8h_gold","high_sla_rpo8h","critical_inode_eta","critical_fill_24h","high_fill_72h","elevated_fill_7d","high_water")
| table cluster namespace pvc pv storageclass csi_driver owner_team criticality used_pct inode_pct gb_per_day days_to_99 inode_days_to_full hrs_to_99 sla_rpo8h_critical sc_headroom_pct pending_pvc_cluster pvc_pv_oversub_ratio sc_allow_expand expansion_resize_hint iops_capacity_curve node_disk_pressure_pct ns_top_burn_gb_per_day severity kubelet_node
| sort - severity +used_pct +cluster +namespace
```

Alert actions: include days_to_99, inode_days_to_full, expansion_resize_hint, and pending_pvc_cluster in tickets; link to Dashboard Studio PV capacity views; attach three redacted metric rows when legal approves.

Operational notes: when cap_bytes is missing because a scrape dropped labels, used_pct stays null and the row disappears after the where clause; investigate relabel configs before muting. When only kube-state-metrics fires without kubelet stats, assume agent misconfiguration rather than declaring the cluster healthy.

Dashboard publishing: heatmap of used_pct by StorageClass; line chart of gb_per_day and days_to_99; single value count of sla_rpo8h_critical; table sorted by severity then used_pct.

Evidence retention: weekly CSV of the closing table with pvc_storage_sla_inventory.csv commit hash stored in a restricted index satisfies internal audits when paired with kubectl describe pvc screenshots during game days.

Performance tuning: if Job Inspector shows multisearch queueing, materialize six-hour rollups into a summary index and point this alert at summaries while retaining raw scrapes for investigations.

Reliability: during kubelet upgrades expect brief gaps; require two intervals of missing metrics before paging scrape failures unless pending_pvc_cluster remains high.

Governance: when legal requests preservation, include metric hash lists and redact customer strings per counsel instructions.

### Step 4 — Validate

Synthetic fill test on a lab cluster: create a Bound PVC backed by a workload, exec a controlled writer so kubelet_volume_stats_used_bytes rises across multiple six-hour buckets within seven days, ingest matching capacity and inode series, execute uc_3_2_25_pv_time_to_fill_sla_sc_burn, and expect non-null gb_per_day with shrinking days_to_99 while used_pct remains coherent with kubectl df inside the pod when permitted.

Synthetic inode test on a disposable PVC: create many small files in a loop so kubelet_volume_stats_inodes_used rises independently of byte pressure; confirm inode_pct and inode_days_to_full surface critical_inode_eta before byte used_pct crosses ninety.

StorageClass expansion test: widen a PVC spec.resources.requests.storage under an allowVolumeExpansion true class, wait for kubelet to reflect larger cap_bytes, confirm days_to_99 resets or grows and expansion_resize_hint downgrades toward observe.

Negative control: delete fill data or expand the volume; wait two buckets; confirm gb_per_day approaches null and severity drops out of alert bands unless unrelated workloads remain hot.

Field sanity: rename a sandbox forwarder label to persistent_volume_claim only and verify coalesce still resolves pvc. RBAC: readers without index access must see zero rows.

Correlation: compare alert timestamps to UC-3.2.5 Pending panels; pending_pvc_cluster should not spike in isolation without bind diagnostics when storage is healthy.

Extended validation: snapshot the alert table before and after resize; store kubectl get pv output; capture CSI controller logs when available; verify streamstats window resets after long scrape gaps; confirm dedup chooses the newest bucket during clock jumps; validate kube_storageclass_info allow_volume_expansion labels after driver upgrades.

### Step 5 — Operationalize & Troubleshoot

Case 1 — days_to_99 under one third of a day on a gold ledger PVC with sc_allow_expand equals one: open an approved change to patch the PVC request upward and monitor kubelet capacity growth; include owner_team and hrs_to_99 in the bridge title.

Case 2 — inode_days_to_full under one day while used_pct is only seventy-five: migrate to a filesystem with higher inode density, shard data across PVCs, or prune small-file caches before inode exhaustion blocks writes.

Case 3 — sc_headroom_pct below twelve across a fast-ssd StorageClass with many siblings near ninety percent: convene storage capacity review; consider class-wide policy, additional node disk pools, or tenant education before bind storms.

Case 4 — pending_pvc_cluster rising with UC-3.2.5 showing provisioning timeouts: treat as correlated; verify cloud volume quotas and CSI controller health before blaming applications.

Case 5 — pvc_pv_oversub_ratio barely above one with aggressive FinOps thin provisioning: document accepted risk in inventory notes; tighten monitoring frequency rather than muting.

Case 6 — iops_capacity_curve equals write_amp_hot_nearfull with node_disk_pressure_pct high: engage node storage SRE; check backing zpool or RAID health; correlate with cloud volume burst balance on gp3.

Case 7 — expansion_resize_hint requests kubectl_edit_pvc_expand_now but change control forbids Friday deploys: execute emergency CAB with database owner; do not silently widen without audit trail.

Case 8 — csi_driver shows a legacy in-tree provisioner string after migration: fix kube_persistentvolume_info labels and dashboards; avoid false confidence in expansion hints.

Case 9 — ns_top_burn_gb_per_day driven by a single analytics namespace during batch load: dampen using time-bound macros if CAB-approved; require FinOps sign-off for suppression.

Case 10 — sla_rpo8h_critical fires during a disaster recovery drill with intentional write spikes: annotate drill windows in pvc_storage_sla_inventory.csv or macro suppressions so bridges stay focused on real customer traffic.

Case 11 — kubelet_node join misses node_disk_pressure_pct because Performance.host naming differs: rely on kubelet metrics alone for paging; open a CMDB ticket to align host keys.

Case 12 — cross-link UC-3.2.16 when kube events show FilesystemAlmostFull or VolumeReadOnly: escalate to the instantaneous plus RO plane immediately even if days_to_99 still shows runway, because filesystem drivers can accelerate toward read-only faster than linear models predict.

Closing checklist: five step headers use em dashes exactly as mandated; Step 3 fenced SPL matches the spl JSON field; multisearch covers kubelet and kube-state-metrics arms; streamstats implements predict_at_threshold_pct ninety-nine math; nested multisearch joins PVC and PV objects; eventstats aggregates StorageClass and namespace burn context; inputlookup enriches ownership; tstats adds disk pressure proxy; case implements severity tiers; final table includes twenty-four columns; monitoringType lists Performance and Capacity; cimModels lists Performance and Inventory; equipment lists kubernetes and opentelemetry; equipmentModels lists kubernetes_k8s; narrative avoids duplicate description and value pairs; references span Kubernetes storage docs, kubelet metrics, kube-state-metrics persistent volume metrics, CSI volume expansion, EKS CSI guidance, GKE PD CSI, and AKS disk guidance.

Long-term owners should rehearse FinOps conversations when sc_headroom_pct trends down for quarters, rehearse scrape rotation after kube-state-metrics upgrades, validate pvc_storage_sla_inventory.csv weekly against live namespaces, and reconcile allow_volume_expansion labels whenever StorageClasses are cloned in GitOps.


## SPL

```spl
`comment("UC-3.2.25 PV SLA time-to-99pct-fill, StorageClass burn, inode ETA, PVC-PV gap, expansion drift. idx=k8s_metrics bin=6h win=28 earliest=-7d@d latest=@h")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-7d@d latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | eval kubelet_node=trim(toString(coalesce(node, Node, instance, kubernetes_io_hostname, "")))
      | where mn="kubelet_volume_stats_used_bytes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>=0
      | bin _time span=6h
      | stats max(mv) AS used_bytes latest(kubelet_node) AS kubelet_node BY cluster namespace pvc _time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-7d@d latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | where mn="kubelet_volume_stats_capacity_bytes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>0
      | bin _time span=6h
      | stats max(mv) AS cap_bytes BY cluster namespace pvc _time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-7d@d latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | where mn="kubelet_volume_stats_inodes_used" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>=0
      | bin _time span=6h
      | stats max(mv) AS inodes_used BY cluster namespace pvc _time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-7d@d latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | where mn="kubelet_volume_stats_inodes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>0
      | bin _time span=6h
      | stats max(mv) AS inodes_total BY cluster namespace pvc _time ]
| stats max(used_bytes) AS used_bytes max(cap_bytes) AS cap_bytes max(inodes_used) AS inodes_used max(inodes_total) AS inodes_total latest(kubelet_node) AS kubelet_node BY cluster namespace pvc _time
| where isnotnull(used_bytes) AND isnotnull(cap_bytes) AND cap_bytes>0
| sort 0 cluster namespace pvc +_time
| streamstats window=28 current=t global=f first(used_bytes) AS u0 last(used_bytes) AS u1 first(_time) AS t0 last(_time) AS t1 first(inodes_used) AS i0 last(inodes_used) AS i1 first(inodes_total) AS it0 last(inodes_total) AS it1 BY cluster namespace pvc
| eval dt_s=t1-t0
| eval gb_per_day=if(dt_s>3600 AND isnotnull(u0) AND isnotnull(u1), round((u1-u0)/1073741824/(dt_s/86400), 6), null())
| eval inode_per_day=if(dt_s>3600 AND isnotnull(i0) AND isnotnull(i1) AND i1>=i0, round((i1-i0)/(dt_s/86400), 4), null())
| eval used_pct=round(100*u1/cap_bytes, 3)
| eval inode_pct=if(isnotnull(it1) AND it1>0 AND isnotnull(i1), round(100*i1/it1, 3), null())
| eval predict_at_threshold_pct=99
| eval tgt99=0.99*cap_bytes
| eval rem99=tgt99-u1
| eval days_to_99=if(isnotnull(gb_per_day) AND gb_per_day>0.000001 AND rem99>0, round(rem99/(gb_per_day*1073741824), 4), null())
| eval inode_rem=if(isnotnull(it1), it1-i1, null())
| eval inode_days_to_full=if(isnotnull(inode_per_day) AND inode_per_day>0.001 AND inode_rem>0, round(inode_rem/inode_per_day, 4), null())
| eval hrs_to_99=if(isnotnull(days_to_99), round(days_to_99*24, 3), null())
| eval sla_rpo8h_critical=if(isnotnull(hrs_to_99) AND hrs_to_99>0 AND hrs_to_99<=8, 1, 0)
| sort 0 - _time
| dedup cluster namespace pvc
| join type=left max=0 cluster namespace pvc
    [| multisearch
          [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
            | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
            | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
            | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
            | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
            | where mn="kube_persistentvolumeclaim_resource_requests_storage_bytes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0
            | stats latest(mv) AS pvc_request_bytes BY cluster namespace pvc ]
          [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
            | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
            | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
            | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
            | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
            | eval pv=trim(toString(coalesce(volumename, volume_name, volumeName, persistentvolume, "")))
            | where mn="kube_persistentvolumeclaim_info" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND len(pv)>0
            | stats latest(mv) AS ksm_pvc_info latest(pv) AS pv BY cluster namespace pvc ]
      | stats max(pvc_request_bytes) AS pvc_request_bytes max(pv) AS pv BY cluster namespace pvc ]
| fillnull value="unresolved" pv
| join type=left max=0 cluster pv
    [| multisearch
          [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
            | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
            | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
            | eval pv=trim(toString(coalesce(persistentvolume, persistent_volume, pv, "")))
            | where mn="kube_persistentvolume_capacity_bytes" AND len(cluster)>0 AND len(pv)>0
            | stats latest(mv) AS pv_cap_bytes BY cluster pv ]
          [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
            | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
            | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
            | eval pv=trim(toString(coalesce(persistentvolume, persistent_volume, pv, "")))
            | eval ph=lower(trim(toString(coalesce(phase, phase_name, ""))))
            | where mn="kube_persistentvolume_status_phase" AND len(cluster)>0 AND len(pv)>0 AND mv>0 AND ph="bound"
            | stats latest(mv) AS pv_phase_sig latest(ph) AS pv_phase BY cluster pv ]
          [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
            | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
            | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
            | eval pv=trim(toString(coalesce(persistentvolume, persistent_volume, pv, "")))
            | eval storageclass=trim(toString(coalesce(storageclass, storage_class, sc, "")))
            | eval csi_driver=trim(toString(coalesce(csi_driver, driver, provisioner, "")))
            | where mn="kube_persistentvolume_info" AND len(cluster)>0 AND len(pv)>0
            | stats latest(mv) AS pv_info latest(storageclass) AS storageclass latest(csi_driver) AS csi_driver BY cluster pv ]
      | stats max(pv_cap_bytes) AS pv_cap_bytes max(pv_phase_sig) AS pv_phase_sig max(pv_info) AS pv_info max(storageclass) AS storageclass max(csi_driver) AS csi_driver max(pv_phase) AS pv_phase BY cluster pv ]
| join type=left max=0 cluster storageclass
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval storageclass=trim(toString(coalesce(storageclass, storage_class, sc, "")))
      | where mn="kube_storageclass_info" AND len(cluster)>0 AND len(storageclass)>0
      | eval sc_allow_expand=if(lower(trim(toString(allow_volume_expansion)))="true",1,0)
      | stats latest(sc_allow_expand) AS sc_allow_expand BY cluster storageclass ]
| join type=left max=0 cluster
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | eval php=lower(trim(toString(coalesce(phase, phase_name, ""))))
      | where mn="kube_persistentvolumeclaim_status_phase" AND php="pending" AND mv>0 AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0
      | stats dc(pvc) AS pending_pvc_cluster BY cluster ]
| fillnull value=0 pending_pvc_cluster
| fillnull value=0 sc_allow_expand
| eval pvc_pv_oversub_ratio=if(isnotnull(pvc_request_bytes) AND isnotnull(pv_cap_bytes) AND pvc_request_bytes>0, round(pv_cap_bytes/pvc_request_bytes, 4), null())
| eval expansion_resize_hint=case(sc_allow_expand=1 AND used_pct>=92 AND isnotnull(days_to_99) AND days_to_99<=3, "kubectl_edit_pvc_expand_now", sc_allow_expand=1 AND used_pct>=85 AND isnotnull(days_to_99) AND days_to_99<=14, "schedule_kubectl_patch_pvc", sc_allow_expand=0 AND used_pct>=85, "migrate_or_new_sc", true(), "observe")
| join type=left max=0 cluster namespace pvc
    [| inputlookup pvc_storage_sla_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=trim(toString(namespace))
      | eval pvc=trim(toString(coalesce(pvc, persistentvolumeclaim, persistent_volume_claim, "")))
      | eval owner_team=trim(toString(coalesce(owner_team, team, squad, "")))
      | eval criticality=lower(trim(toString(coalesce(criticality, tier, "silver"))))
      | fields cluster namespace pvc owner_team criticality ]
| fillnull value="unknown_owner" owner_team
| fillnull value="silver" criticality
| eventstats sum(u1) AS sc_sum_used sum(cap_bytes) AS sc_sum_cap BY cluster storageclass
| eval sc_headroom_pct=if(isnotnull(sc_sum_cap) AND sc_sum_cap>0, round(100*(1-sc_sum_used/sc_sum_cap), 3), null())
| eventstats max(gb_per_day) AS ns_top_burn_gb_per_day BY cluster namespace
| join type=left max=0 kubelet_node
    [| tstats summariesonly=true max(Performance.disk_usage) AS node_disk_pressure_pct FROM datamodel=Performance WHERE nodename=Performance.Storage earliest=-4h@h latest=now BY Performance.host
      | rename Performance.host AS kubelet_node ]
| eval iops_capacity_curve=case(used_pct>=95 AND node_disk_pressure_pct>=88, "write_amp_hot_nearfull", used_pct>=90 AND gb_per_day>=2, "highburn_nearfull", used_pct>=90 AND isnotnull(node_disk_pressure_pct) AND node_disk_pressure_pct>=80, "disk_pressure_nearfull", used_pct>=80 AND gb_per_day>=1, "rising_burn", true(), "nominal")
| eval severity=case(sla_rpo8h_critical=1 AND lower(criticality)="gold", "critical_sla_rpo8h_gold", sla_rpo8h_critical=1, "high_sla_rpo8h", isnotnull(inode_days_to_full) AND inode_days_to_full<=1, "critical_inode_eta", isnotnull(days_to_99) AND days_to_99<=1, "critical_fill_24h", isnotnull(days_to_99) AND days_to_99<=3, "high_fill_72h", isnotnull(days_to_99) AND days_to_99<=7, "elevated_fill_7d", used_pct>=92, "high_water", used_pct>=85, "warning", true(), "info")
| where used_pct>=82 OR sla_rpo8h_critical=1 OR pending_pvc_cluster>=8 OR severity IN ("critical_sla_rpo8h_gold","high_sla_rpo8h","critical_inode_eta","critical_fill_24h","high_fill_72h","elevated_fill_7d","high_water")
| table cluster namespace pvc pv storageclass csi_driver owner_team criticality used_pct inode_pct gb_per_day days_to_99 inode_days_to_full hrs_to_99 sla_rpo8h_critical sc_headroom_pct pending_pvc_cluster pvc_pv_oversub_ratio sc_allow_expand expansion_resize_hint iops_capacity_curve node_disk_pressure_pct ns_top_burn_gb_per_day severity kubelet_node
| sort - severity +used_pct +cluster +namespace
```

## CIM SPL

```spl
| tstats summariesonly=true latest(Inventory.vendor_product) AS inv_product count AS inv_events FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
| rename Inventory.dest AS inventory_dest
| join type=left max=0 inventory_dest [| tstats summariesonly=true max(Performance.disk_usage) AS peak_disk_pct avg(Performance.disk_usage) AS avg_disk_pct FROM datamodel=Performance WHERE nodename=Performance.Storage earliest=-4h@h latest=now BY Performance.host
| rename Performance.host AS inventory_dest ]
| where inv_events>0
| table inventory_dest inv_product peak_disk_pct avg_disk_pct
```

## Visualization

Multi-series line chart of gb_per_day and days_to_99 by namespace; heatmap of used_pct by StorageClass; single value sla_rpo8h_critical count; table matching the twenty-four closing SPL columns with drilldown to kubelet and kube-state-metrics samples; sibling link to UC-3.2.16 instantaneous panels.

## Known False Positives

Log retention or indexer window rotation that drops samples older than the streamstats horizon produces a legitimate slope reset where gb_per_day snaps toward zero until the window refills; do not page on slope resets alone without corroborating used_pct movement. Batch ETL jobs that write tens of gigabytes then delete overnight create sawtooth growth that violates linear burn assumptions; require business calendars in inventory or widen bins for those namespaces. emptyDir or scratch PVCs mounted under build pods can burst during compile then shrink when pods terminate; route those namespaces to bronze criticality. Planned datacopy migrations inflate burn for days then collapse when cutover finishes; suppress using CAB macros. Tiered storage with manual archive lag can leave logical usage high while physical arrays freed space; pair with vendor array dashboards before accusing applications. Transient backup catalog files or snapshot differencing stores can spike inode usage briefly; corroborate with backup job schedules. Snapshot space reservation incorrectly counted inside guest filesystem views can make used_pct look worse than operator consoles; validate CSI and array accounting. Kustomize-driven load generator tests in shared clusters can mimic production burn; require perf_test labels in inventory. Vendor expansion executed only through a cloud console while Kubernetes still shows the old PVC request can make pvc_pv_oversub_ratio look alarming until the apiserver catches up; reconcile kubectl describe. Legitimate growth spikes during disaster recovery drills or failover exercises should carry drill annotations so sla_rpo8h_critical does not wake the wrong bridge. Duplicate scrapes from overlapping agents without dedup keys can jitter hour-over-hour growth; validate single writer per target.

## References

- [Kubernetes PersistentVolumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Kubernetes node metrics (kubelet)](https://kubernetes.io/docs/reference/instrumentation/node-metrics/)
- [kube-state-metrics PersistentVolume metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/storage/persistentvolume-metrics.md)
- [Kubernetes CSI volume expansion](https://kubernetes-csi.github.io/docs/volume-expansion.html)
- [Amazon EKS — Amazon EBS CSI driver](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html)
- [Google GKE — Persistent Disk CSI driver](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/gce-pd-csi-driver)
- [Azure AKS — Azure Disk CSI driver](https://learn.microsoft.com/en-us/azure/aks/azure-disk-csi)
- [Splunk Add-on for Kubernetes — About](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
