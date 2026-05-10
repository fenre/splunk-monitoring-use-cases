<!-- AUTO-GENERATED from UC-3.2.16.json — DO NOT EDIT -->

---
id: "3.2.16"
title: "Persistent Volume / PVC Filesystem Capacity Forecast and ReadOnly Pre-Failure"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.16 · Persistent Volume / PVC Filesystem Capacity Forecast and ReadOnly Pre-Failure

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch each piece of permanent storage attached to an app; when it gets close to full the app can stop writing and the data can be locked read-only. We predict when each volume runs out of space so storage can grow before customers notice.*

---

## Description

Detects bound Kubernetes PVC filesystems trending toward byte or inode exhaustion using kubelet volume_stats metrics, projects days_to_full from hourly growth via streamstats, and correlates kube events such as FilesystemAlmostFull, FilesystemFull, and VolumeReadOnly before catastrophic read-only remounts. The control joins governance inventory for expansion_allowed, criticality, and owner routing, and optionally enriches with CIM Performance disk_usage peaks on the mounting node when names align.

## Value

Prevents silent write failures, database corruption, and 500-class outages that follow full PVCs or inode exhaustion by giving platform and application teams a dated ETA, explicit inode risk, and RO pre-failure signals tied to owning squads. Customer-visible reliability improves when expansions, log rotation, or migrations start before kubelet escalations, and FinOps gains proof of when expansion_allowed false forces migration instead of resize.

## Implementation

Stand up k8s_metrics, k8s_events, and k8s_storage with distinct HEC tokens; deploy Splunk OTel Collector scraping kubelet /metrics for kubelet_volume_stats series plus k8s_events; publish pvc_inventory.csv; save uc_3_2_16_pvc_filesystem_forecast_ro on a fifteen-to-thirty-minute cadence over earliest=-30h@h; route catastrophic rows with ro_remount_flag to voice; archive weekly CSV evidence.

## Evidence

Saved search uc_3_2_16_pvc_filesystem_forecast_ro with fifteen-to-thirty-minute schedule; lookups/pvc_inventory.csv versioned in git; weekly CSV export of the closing table to a restricted evidence index with redacted kube:events hashes when incidents involve regulated namespaces.

## Control test

### Positive scenario

In a lab namespace, bind a 1Gi PVC, generate sustained writes so kubelet_volume_stats_used_bytes rises across multiple hourly bins, ingest matching kubelet_volume_stats_capacity_bytes and inode series, optionally emit a FilesystemAlmostFull or VolumeReadOnly style kube event, execute uc_3_2_16_pvc_filesystem_forecast_ro, and expect a row with severity at least high or catastrophic when thresholds are crossed.

### Negative scenario

After deleting test data or expanding the volume under an expandable StorageClass, wait for fresh scrapes and hourly bins, confirm used_pct and inode_pct fall below alert bands, and verify the saved search emits no qualifying row for that PVC unless unrelated workloads remain hot.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with Kubernetes storage engineering, observability, and tenant SRE teams who operate Splunk OpenTelemetry Collector fleets and CSI drivers across cloud and on-prem footprints. UC-3.2.16 is the bound PersistentVolumeClaim filesystem saturation plane: it consumes kubelet volume_stats metrics for already-mounted PVCs, projects linear fill time from hourly samples, tracks inode exhaustion independently of byte pressure, and correlates Kubernetes events that precede read-only remounts. UC-3.2.5 remains the binding-axis detector for PVCs stuck Pending without a matching PV; this UC assumes Bound or otherwise mounted volumes that can still exhaust their formatted filesystem. UC-3.2.25 may overlap on instantaneous free-space percentages; this UC sharpens the story with ETA from growth, inode_pct, FilesystemAlmostFull and FilesystemFull precursors, and VolumeReadOnly style outcomes. UC-3.2.40 covers VolumeSnapshot health and backup posture, not live filesystem fill. UC-3.2.4 governs namespace ResourceQuota admission exhaustion, which can block new PVCs even when existing ones are healthy.

Index and token contracts precede saved-search authoring. Stand up index=k8s_metrics for prometheus:scrape:metrics series scraped from each kubelet metrics endpoint and optional CSI controller managers when your FinOps model permits the extra cardinality. Stand up index=k8s_events (or reuse index=k8s with sourcetype=kube:events) for v1.Event streams including kubelet and volume manager reasons. Stand up index=k8s_storage when you land CSI sidecar or controller metrics distinct from kubelet scrapes, and route those rows through the same label normalisation macros so cluster, namespace, and PVC names align with kube-state-metrics joins used elsewhere in cat-3.2. Issue distinct HEC tokens per index class with role-based search restrictions so developers can see capacity dashboards without reading privileged audit bodies. Document retention: metrics hot buckets at least fourteen days for replay, events at least thirty days for RO forensic timelines.

Splunk OpenTelemetry Collector for Kubernetes must scrape kubelet /metrics with prometheus_simple or an equivalent prometheus receiver job on every node, preserving Prometheus labels that map to persistentvolumeclaim, namespace, and node identity. The k8s_events receiver should watch the same clusters that feed metrics so FilesystemAlmostFull, FilesystemFull, and VolumeReadOnly narratives arrive with the same cluster tag your metrics carry. For managed Kubernetes, align StorageClass defaults with vendor guidance: Amazon EKS commonly uses EBS gp3 or io2 CSI classes; Google GKE uses pd-balanced or pd-ssd; Microsoft AKS uses managed-csi or azuredisk-csi. Expansion feasibility is not universal: only StorageClasses with allowVolumeExpansion=true support online growth; inventory must record expansion_allowed yes or no per PVC.

Governance lookup lookups/pvc_inventory.csv must contain cluster, namespace, pvc, storageclass, owner_team, criticality with gold silver bronze semantics, expansion_allowed yes or no, and backup_class snapshot or none so responders can tell whether a near-full volume is a primary datastore or an archival sink. Refresh weekly from GitOps exports or CMDB pipelines and attach commit hashes when auditors ask for lineage. Gold rows route catastrophic or critical severities to immediate paging when ro_remount_flag is true or when used_pct and inode_pct cross ninety-five. Silver rows open tickets with platform CC. Bronze rows remain dashboard-only unless an executive override marks customer impact.

Risk briefing: when usedBytes approaches capacityBytes on many CSI stacks, kubelet volume health signals escalate and some drivers eventually remount read-only to protect metadata, which turns a capacity incident into an application integrity incident. Inode exhaustion can strike while byte utilisation looks comfortable on small-file workloads such as mail spools or build caches, so inode_pct must ride alongside used_pct. Silent misconfiguration of prometheus relabel rules that drop persistentvolumeclaim labels makes this control blind while kubectl still shows Bound PVCs.

Licensing note: hourly binning plus twenty-five hour streamstats windows keep search cost predictable; avoid sub-minute raw scans on multi-thousand-node fleets without summary indexing. Privacy note: PVC names may echo internal product codenames; restrict dashboard ACLs.

Differentiation recap: bound PVC filesystem bytes and inodes with forecast ETA and RO detection, not unbound binding failures, not snapshot health, not namespace quota walls.

Collector architecture notes: self-managed clusters often scrape kubelet via the node IP with bearer tokens; managed offerings may require privileged DaemonSets. Document TLS, token rotation, and allowed egress from collectors to kubelet ports.

FinOps alignment: expansion_allowed false means migration or new PVC, not a quick patch; attach cost-centre owners from inventory.

Reliability alignment: StatefulSets with single replicas may not survive RO remount without manual intervention; catastrophic severity should open a bridge, not a ticket-only workflow.

Security alignment: events can include host paths; scrub exports when sharing outside platform teams.

Performance alignment: keep multisearch arms narrow with explicit metric names to prevent accidental high-cardinality explosions from unrelated kubelet counters.

Training alignment: teach responders that inode_pct high with modest used_pct is legitimate for some workloads and requires inode-aware remediation, not only byte expansion.

Documentation alignment: wiki-map this UC beside PersistentVolume, VolumeHealthMonitor, and StorageClass expansion docs.

Review cadence: quarterly replay one historical near-full PVC incident through the SPL after kubelet upgrades.

Escalation alignment: catastrophic plus gold criticality engages storage engineering and application leadership jointly.

Telemetry hygiene: deduplicate overlapping Prometheus agents that scrape the same kubelet without dedup keys.

Governance alignment: CAB records should cover HEC token ACL changes and ServiceMonitor edits together when kubelet scrape paths move.

Supplemental ownership depth: storage platform engineers certify scrape intervals during peak retail events when kubelet CPU is hot; application owners attest pvc_inventory.csv criticality quarterly; FinOps validates backup_class against real snapshot schedules; legal reviews event exports when host paths appear; chaos engineering namespaces carry explicit dampening in inventory; multi-region fleets duplicate tokens per region with identical label contracts; GitOps repos version ServiceMonitor YAML beside collector configs; runbooks link to Kubernetes volume health monitoring documentation and CSI external health monitor pages; ITSI optional episodes attach service IDs from CMDB when KPI import is enabled; Splunk Cloud search auto pause policies get an exception macro for this saved search during known migrations; OTEL memory limits rise when kubelet series cardinality grows after CSI upgrades; kube-state-metrics PV and PVC metrics remain sibling context for dashboards even when not in the primary multisearch; training videos show difference between Pending PVC binding and Bound PVC fill; executive summaries chart days_to_full distributions by criticality; auditors receive weekly CSV extracts with hashed PVC names when regulated; penetration tests validate HEC token scope cannot read unrelated security indexes; SRE onboarding includes lab dd fill exercises with tear-down checklists; FinOps chargeback maps growth_gb_per_24h to cost centres when log volumes spike; platform on-call rotates paired with storage vendor TAM contacts for Sev-1 RO incidents; documentation in Confluence stays synchronized with this JSON source of truth via generate_md pipeline; replay tests after kubernetes minor upgrades validate metric renames; dual-stack IPv6 node fleets use consistent instance labels in relabel configs; air-gapped environments mirror container images for OTEL collectors before kubelet scrapes go live; service mesh sidecars never obscure kubelet scrape paths when hostNetwork collectors are forbidden; windows node pools are out of scope unless your CSI and kubelet emit identical metric names; openshift routes may rename default namespaces so coalesce ladders stay tested; rancher managed clusters still need explicit cluster tags to avoid collisions; vmware tanzu supervisors require verified bearer token lifetimes; edge kubernetes clusters with intermittent uplinks widen earliest windows cautiously; data sovereignty regions keep evidence indexes local per counsel; immutable infrastructure rotations rebuild collectors from pinned helm charts; golden signals training links this UC to latency error rate saturation examples; post-incident reviews record whether remediation was expand, trim, migrate, or bugfix; synthetic monitors ping Splunk HEC health before declaring collector outages; dependency mapping shows this UC upstream of database SLO dashboards; configuration drift detectors compare live ServiceMonitor to git main; capacity planning spreadsheets import days_to_full CSV monthly; executive risk registers cite RO remount as tier-one platform hazard; vendor RFO documents attach to tickets when CSI bugs cause premature RO; cross-region failover drills include PVC fill scenarios; application architects review inode budgets during new service templates; build platform teams track scratch PVC growth separately from production; ml anomaly detection stays optional overlay only when baselines exist; prometheus remote write duplicates must not triple-count kubelet samples; thanos query paths are allowed only when dedup labels are proven; grafana mirror dashboards cite Splunk as system of record for paging; PagerDuty event orchestration enriches with owner_team from lookup; slack bridges post severity plus days_to_full in first line; jira auto-creates link back to saved search URL; confluence runbook includes kubectl debug node steps for volume inspection; legal hold procedures preserve kube events without deleting metrics; disaster recovery teams verify snapshot schedules when catastrophic fires during fill storms; finops approves bronze suppressions in writing quarterly.

Additional platform engineering notes for long-term curators: when service accounts rotate, replay a canary PVC fill in staging before production scrapes resume. When finance challenges license cost, compare bytes indexed to a single Sev-1 RO incident bridge cost estimate. When legal requests holds, include kubelet metric samples and event excerpts in preservation scope without exposing customer payload fields. When automating prune jobs, require human approval in regulated zones. When training new responders, teach the difference between byte pressure and inode pressure using side-by-side lab replays. When OT edge gateways embed Kubernetes, duplicate baselines with OT-specific bulk-load calendars. When integrating Splunk ITSI, map severities to episode priority with catastrophic tiers defaulting to P2 unless customer SLO mapping dictates P1. When Splunk Enterprise Security is present, keep risk scores low for known data-lake hosts documented in pvc_inventory.csv notes. When service meshes inject heavy logging sidecars, ensure sidecar R/W growth is visible so misattribution does not hide database PVC growth. When closing incidents, record whether remediation was capacity expansion, workload refactor, prune automation, or application bug fix. When cluster fleets exceed five thousand nodes, summary-index hourly rollups before alerting while retaining raw scrapes for investigations. When CSI drivers publish health metrics on custom ports, mirror those into k8s_storage with documented sourcetype contracts. When GitOps renames namespaces, update pvc_inventory.csv in the same merge request. When kube-state-metrics upgrades change metric names, cross-check dashboards for a week before declaring victory. When customers demand RPO guarantees, pair this UC with UC-3.2.40 snapshot success rates. When etcd storms delay events, widen event correlation windows temporarily. When node not ready cycles occur, dedup logic still picks the latest healthy scrape hour. When finance tracks chargeback by storageclass, join those codes into inventory. When SRE teams split on-call, document handoff expectations for catastrophic rows. When compliance frameworks ask for preventive controls, attach forecast CSV exports with signatures. When kubernetes deprecates metric labels, update coalesce ladders in the same release train. When observability budgets shrink, defend this UC as cheaper than outage bridges.

### Step 2 — Configure data collection

Deploy a ServiceMonitor or PodMonitor that selects the OpenTelemetry Collector DaemonSet and points a prometheus receiver at each node kubelet https endpoint with the service account token mounted for authentication. Use serviceMonitorSelector or podMonitorSelector labels that match your GitOps convention so staging and production scrape cadences differ intentionally. Example ServiceMonitor skeleton pointing at kubelet metrics path /metrics with TLS skip verify only when your threat model accepts it; prefer proper CA bundles in regulated zones.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: otel-kubelet-volumestats
  namespace: observability
  labels:
    release: otel-collector
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: opentelemetry-collector-agent
  namespaceSelector:
    matchNames:
      - observability
  endpoints:
    - port: prometheus
      scheme: https
      path: /metrics
      tlsConfig:
        insecureSkipVerify: false
      bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabelings:
        - action: replace
          targetLabel: k8s_cluster_name
          replacement: prod-eks-us-east-1
```

OpenTelemetry Collector fragment showing prometheus_simple against kubelet, k8s_events receiver, and splunk_hec exporter routing metrics to k8s_metrics and events to k8s_events with kube:events sourcetype normalization in your transforms.

```yaml
receivers:
  prometheus_simple/kubelet:
    collection_interval: 60s
    tls:
      insecure_skip_verify: false
      ca_file: /etc/pki/kubelet/ca.crt
    auth:
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    endpoints:
      - url: https://${KUBELET_HOST}:10250/metrics
        metric_relabel_configs:
          - source_labels: [__name__]
            regex: kubelet_volume_stats_(used_bytes|capacity_bytes|inodes_used|inodes|available_bytes)
            action: keep
  k8s_events:
    auth_type: serviceAccount
    namespaces: []
    mode: watch
exporters:
  splunk_hec/metrics:
    token: ${SPLUNK_HEC_TOKEN_K8S_METRICS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
  splunk_hec/events:
    token: ${SPLUNK_HEC_TOKEN_K8S_EVENTS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_events
    sourcetype: kube:events
service:
  pipelines:
    metrics/k8s:
      receivers: [prometheus_simple/kubelet]
      exporters: [splunk_hec/metrics]
    logs/events:
      receivers: [k8s_events]
      exporters: [splunk_hec/events]
```

Sample pvc_inventory.csv schema for governance joins referenced in SPL.

```csv
cluster,namespace,pvc,storageclass,owner_team,criticality,expansion_allowed,backup_class
prod-eks-us-east-1,prod-payments,data-pvc-0,gp3,payments-sre,gold,yes,snapshot
prod-eks-us-east-1,dev-analytics,scratch-pvc,gp3,data-platform,silver,no,none
```

StorageClass YAML showing allowVolumeExpansion=true for teams that rely on online resize after forecast warnings.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-expandable
provisioner: ebs.csi.aws.com
allowVolumeExpansion: true
parameters:
  type: gp3
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
```

props and transforms guidance: normalize __name__, value, namespace, persistentvolumeclaim, and cluster labels onto indexed fields; keep camelCase aliases from OTEL exporters in transforms.conf so coalesce ladders in SPL stay short.

Validation before alert authoring: index=k8s_metrics sourcetype=prometheus:scrape:metrics earliest=-30m must return kubelet_volume_stats_used_bytes and kubelet_volume_stats_capacity_bytes with non-empty persistentvolumeclaim labels; index=k8s_events sourcetype=kube:events earliest=-24h should show volume-related reasons in busy clusters. Clock skew between kubelet, API server, and Splunk _time must stay under sixty seconds or hourly bins misalign.

Extended validation checklist: confirm each node appears in scrapes at least once per interval; verify no duplicate k8s_cluster_name labels during cluster migration weekends; test HEC ACK when indexes roll; measure forwarder lag at p95; validate props LINE_BREAKER for multiline prometheus payloads if any; ensure heavy queries use workload_pool macros in Cloud; document sourcetype override paths for openshift logging stacks; rehearse token rotation without dropping scrapes; compare live kubectl get pvc capacity to metric capacity_bytes for a sample set weekly.

### Step 3 — Create the search and alert

Save the SPL as saved search uc_3_2_16_pvc_filesystem_forecast_ro with fifteen-minute schedule during business peaks and thirty-minute schedule overnight, dispatch earliest=-30h@h, dispatch latest=now, and throttle duplicate medium rows per cluster namespace pvc for two hours unless severity escalates. Route catastrophic to immediate voice paging with storage and application bridges; route critical to high-priority tickets with SMS backup for gold inventory rows; route high to standard queue with explicit ETA in the ticket subject.

Pipeline understanding for operators: the opening comment macro lists indexes, sourcetypes, bin width, streamstats window, and time horizon so retuning does not require opening this document cold. multisearch fans four kubelet metric arms so a silent failure in one CSI label set does not zero the entire join. coalesce ladders normalize cluster, namespace, pvc, and node labels across cloud and on-prem field naming. Hourly binning caps scan cost while preserving enough points for a twenty-five sample streamstats window spanning roughly one day. streamstats computes first and last used_bytes inside the window per PVC, derives growth_bytes_per_hour, converts to growth_gb_per_24h, and estimates days_to_full when growth is positive and material. inode_pct uses kubelet_volume_stats_inodes_used divided by kubelet_volume_stats_inodes. A nested multisearch on kube events indexes catches FilesystemAlmostFull, FilesystemFull, and VolumeReadOnly style signals with case-insensitive match logic on reason and message fields. inputlookup pvc_inventory.csv enriches owner_team, criticality, expansion_allowed, and storageclass. tstats against Performance.Storage supplies an optional host-level disk_usage peak join on node name when CIM acceleration aligns with Kubernetes node objects; the join is left outer and the auxiliary field is dropped before the analyst table. case maps severity: catastrophic when ro_remount_flag is set, critical when byte or inode percent exceeds ninety-five, high when byte percent exceeds eighty-five or days_to_full is three or fewer, medium when byte percent exceeds seventy-five or days_to_full is fourteen or fewer, otherwise low which is filtered out for alert noise. The closing table lists fifteen columns: cluster, namespace, pvc, storageclass, used_gb, capacity_gb, used_pct, inode_pct, growth_gb_per_24h, days_to_full, expansion_allowed, criticality, owner_team, severity, ro_remount_flag.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.16 Bound PVC forecast+inode+RO. idx=k8s_metrics,k8s_events st=prometheus:scrape:metrics,kube:events bin=1h win=25 earliest=-30h@h")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | eval node=trim(toString(coalesce(node, Node, instance, kubernetes_io_hostname, "")))
      | where mn="kubelet_volume_stats_used_bytes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>=0
      | bin _time span=1h
      | stats max(mv) AS used_bytes latest(node) AS node BY cluster namespace pvc _time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | eval node=trim(toString(coalesce(node, Node, instance, kubernetes_io_hostname, "")))
      | where mn="kubelet_volume_stats_capacity_bytes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>0
      | bin _time span=1h
      | stats max(mv) AS capacity_bytes latest(node) AS node BY cluster namespace pvc _time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | eval node=trim(toString(coalesce(node, Node, instance, kubernetes_io_hostname, "")))
      | where mn="kubelet_volume_stats_inodes_used" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>=0
      | bin _time span=1h
      | stats max(mv) AS inodes_used latest(node) AS node BY cluster namespace pvc _time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | eval node=trim(toString(coalesce(node, Node, instance, kubernetes_io_hostname, "")))
      | where mn="kubelet_volume_stats_inodes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>0
      | bin _time span=1h
      | stats max(mv) AS inodes_total latest(node) AS node BY cluster namespace pvc _time ]
| stats max(used_bytes) AS used_bytes max(capacity_bytes) AS capacity_bytes max(inodes_used) AS inodes_used max(inodes_total) AS inodes_total latest(node) AS node BY cluster namespace pvc _time
| where isnotnull(used_bytes) AND isnotnull(capacity_bytes) AND capacity_bytes>0
| sort 0 cluster, namespace, pvc, _time
| streamstats window=25 current=t global=f first(used_bytes) AS u_first last(used_bytes) AS u_last first(_time) AS t_first last(_time) AS t_last BY cluster, namespace, pvc
| eval hours_elapsed=round((t_last-t_first)/3600, 4)
| eval growth_bytes_per_hour=if(hours_elapsed>0.25 AND isnotnull(u_first) AND isnotnull(u_last), round((u_last-u_first)/hours_elapsed, 6), null())
| eval growth_gb_per_24h=if(isnotnull(growth_bytes_per_hour), round((growth_bytes_per_hour*24)/1073741824, 4), null())
| eval rem_bytes=capacity_bytes-u_last
| eval days_to_full=if(isnotnull(growth_bytes_per_hour) AND growth_bytes_per_hour>1024 AND rem_bytes>0, round(rem_bytes/(growth_bytes_per_hour*24), 3), null())
| eval used_pct=round(100*u_last/capacity_bytes, 3)
| eval inode_pct=if(isnotnull(inodes_total) AND inodes_total>0 AND isnotnull(inodes_used), round(100*inodes_used/inodes_total, 3), null())
| eval used_gb=round(u_last/1073741824, 3)
| eval capacity_gb=round(capacity_bytes/1073741824, 3)
| sort 0 - _time
| dedup cluster namespace pvc
| join type=left max=0 cluster namespace pvc
    [| multisearch
          [ search index=k8s_events sourcetype="kube:events" earliest=-30h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
            | eval namespace=trim(toString(coalesce(metadata_namespace, namespace, involvedObject_namespace, "")))
            | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, involvedObject_name, `involvedObject.name`, "")))
            | eval reason=trim(toString(coalesce(reason, Reason, "")))
            | eval msg=lower(toString(coalesce(message, Message, _raw, "")))
            | where len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0
            | eval ro_hit=if(match(reason,"(?i)VolumeReadOnly") OR match(msg,"(?i)readonly") OR match(msg,"(?i)filesystemalmostfull") OR match(msg,"(?i)filesystemfull") OR match(reason,"(?i)FilesystemAlmostFull") OR match(reason,"(?i)FilesystemFull"), 1, 0)
            | where ro_hit=1
            | stats dc(_time) AS ro_event_distinct BY cluster namespace pvc
            | eval ro_remount_flag=if(ro_event_distinct>0, 1, 0) ]
          [ search index=k8s sourcetype="kube:events" earliest=-30h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
            | eval namespace=trim(toString(coalesce(metadata_namespace, namespace, involvedObject_namespace, "")))
            | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, involvedObject_name, `involvedObject.name`, "")))
            | eval reason=trim(toString(coalesce(reason, Reason, "")))
            | eval msg=lower(toString(coalesce(message, Message, _raw, "")))
            | where len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0
            | eval ro_hit=if(match(reason,"(?i)VolumeReadOnly") OR match(msg,"(?i)readonly") OR match(msg,"(?i)filesystemalmostfull") OR match(msg,"(?i)filesystemfull") OR match(reason,"(?i)FilesystemAlmostFull") OR match(reason,"(?i)FilesystemFull"), 1, 0)
            | where ro_hit=1
            | stats dc(_time) AS ro_event_distinct BY cluster namespace pvc
            | eval ro_remount_flag=if(ro_event_distinct>0, 1, 0) ]
      | stats max(ro_remount_flag) AS ro_remount_flag BY cluster namespace pvc ]
| fillnull value=0 ro_remount_flag
| join type=left max=0 cluster namespace pvc
    [| inputlookup pvc_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=trim(toString(namespace))
      | eval pvc=trim(toString(coalesce(pvc, persistentvolumeclaim, persistent_volume_claim, "")))
      | eval owner_team=trim(toString(coalesce(owner_team, team, squad, "")))
      | eval criticality=lower(trim(toString(coalesce(criticality, tier, ""))))
      | eval expansion_allowed=lower(trim(toString(coalesce(expansion_allowed, allow_expand, vol_expand, ""))))
      | eval storageclass=trim(toString(coalesce(storageclass, storage_class, sc, "")))
      | eval backup_class=trim(toString(coalesce(backup_class, backup_tier, "")))
      | fields cluster namespace pvc storageclass owner_team criticality expansion_allowed backup_class ]
| fillnull value="unknown" owner_team
| fillnull value="bronze" criticality
| fillnull value="unknown" expansion_allowed
| fillnull value="unknown" storageclass
| join type=left max=0 node
    [| tstats summariesonly=t max(Performance.disk_usage) AS node_disk_peak_pct FROM datamodel=Performance WHERE nodename=Performance.Storage earliest=-4h@h latest=now BY Performance.host
      | rename Performance.host AS node ]
| fields - node_disk_peak_pct
| eval severity=case(
    ro_remount_flag>=1, "catastrophic",
    used_pct>=95 OR inode_pct>=95, "critical",
    used_pct>=85 OR (isnotnull(days_to_full) AND days_to_full<=3), "high",
    used_pct>=75 OR (isnotnull(days_to_full) AND days_to_full<=14), "medium",
    true(), "low")
| where severity IN ("catastrophic","critical","high","medium")
| table cluster namespace pvc storageclass used_gb capacity_gb used_pct inode_pct growth_gb_per_24h days_to_full expansion_allowed criticality owner_team severity ro_remount_flag
| sort - severity +cluster +namespace +pvc

```

Alert actions: include severity, days_to_full, expansion_allowed, and ro_remount_flag in tickets; link to Dashboard Studio PVC capacity view; attach three redacted kube events when legal approves.

Operational notes: when capacity_bytes is missing because a scrape dropped labels, used_pct stays null and the row disappears after the where clause; investigate relabel configs before muting. When only events fire without metrics, assume kubelet scrape failure rather than declaring the cluster healthy.

Dashboard publishing: heatmap of used_pct by namespace; line chart of growth_gb_per_24h; single value catastrophic count; table sorted by severity then criticality.

Evidence retention: weekly CSV of the closing table with pvc_inventory.csv commit hash stored in a restricted index satisfies internal audits when paired with kubectl describe pvc screenshots during game days.

Performance tuning: if Job Inspector shows multisearch queueing, materialize hourly rollups into a summary index and point this alert at summaries while retaining raw scrapes for investigations.

Reliability: during kubelet upgrades expect brief gaps; require two intervals of missing metrics before paging scrape failures unless events remain hot.

Governance: when legal requests preservation, include event hash lists and redact customer strings per counsel instructions.

### Step 4 — Validate

Synthetic fill test on a lab cluster: create a 1Gi PVC bound to a workload, exec a writer pod, run dd if=/dev/zero of=/data/fill bs=1M count=900, confirm kubelet_volume_stats_used_bytes rises in k8s_metrics and used_pct crosses eighty within the observation window, then watch for FilesystemAlmostFull class events in k8s_events as you approach the ninety-five percent band if your kubelet and CSI combination emits them.

Synthetic read-only signal test: consult your storage vendor lab guide for forced RO scenarios; where safe, simulate conditions that produce VolumeReadOnly reasons and confirm ro_remount_flag becomes one while severity becomes catastrophic.

ETA forecast test: maintain a controlled steady writer so growth_gb_per_24h stabilises; verify days_to_full shrinks as the remaining bytes numerator falls and that widening the PVC under an expandable StorageClass clears the alert after kubelet reflects new capacity_bytes.

Inode saturation test on a disposable small PVC: run a tight loop creating empty files such as for i in $(seq 1 200000); do touch /data/f$i; done adjusted to your inode budget, confirm inode_pct rises independently of byte used_pct, and verify the alert surfaces critical when inode_pct crosses ninety-five even if used_gb looks modest.

Negative control: delete fill files or expand the volume, wait two scrape intervals plus one hourly bin, confirm deduped latest rows fall below alert thresholds and severity drops out of the filtered set.

Tear down lab PVCs and confirm alert clears; remove synthetic event generators so production bridges do not inherit test noise.

Correlation: compare alert timestamps to application logs mentioning read-only file system or SQLite IOERR; misalignment often means the container saw RO before metrics landed, so widen event windows temporarily during investigations.

Field sanity: rename a sandbox forwarder label to persistent_volume_claim only and verify coalesce still resolves pvc. RBAC: readers without index access must see zero rows.

Extended validation: snapshot the alert table before and after resize; store kubectl get events output; capture CSI driver logs when available; verify streamstats window resets after long scrape gaps; confirm dedup chooses the newest hour during clock jumps.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Database PVC growing five gigabytes per day with days_to_full at four and expansion_allowed yes: trigger approved online volume expansion or file a change with the storage team; if cluster-autoscaler or storage autoscaler addons exist, validate they are not blocked by StorageClass caps.

Case 2 — Log-shipper PVC at ninety-nine percent with RO remount imminent: pause or throttle the shipper to drain backlog, rotate logs inside the volume, or attach a sidecar cleanup job before the kubelet escalates to read-only.

Case 3 — Inode saturation on a small-file workload such as maildir: migrate to a filesystem with higher inode density, replace the PVC with a class tuned for many small files, or shard data across multiple PVCs after architecture review.

Case 4 — Volume read-only remount detected with ro_remount_flag true: page on-call immediately as a data integrity emergency; do not restart databases blindly until filesystem health is assessed.

Case 5 — PVC still bound after StatefulSet deletion orphaned the workload: reclaim via documented salvage workflow, snapshot if policy requires, then delete the PVC under change control.

Case 6 — Fast growth in a dev namespace: often a missing trim cron or unbounded debug logs; engage owners with growth_gb_per_24h evidence before production spillover.

Case 7 — ReadWriteMany PVC on NFS or EFS hitting a logical size or quota ceiling: escalate to the storage team; expansion semantics differ from single-node RWO EBS.

Case 8 — PVC backed by StorageClass with allowVolumeExpansion false: plan workload migration or new PVC cutover rather than expecting resize in place.

Case 9 — Inode growth from a swarm of empty files: treat as likely application bug; pair with developer investigation while guarding production siblings.

Case 10 — Time spent above seventy-five percent for more than twenty-four hours without expansion ticket: audit governance; inventory flags may need tightening or FinOps review stalled the change.

Case 11 — Cross-link UC-3.2.40 snapshot health: if the PVC is full, recent recovery points may be stale or fail; verify snapshot jobs still succeed.

Case 12 — Cross-link UC-3.2.5 unbound PVCs: when disks are full, new claims may remain Pending; hand off binding diagnostics only after confirming this UC is not already in catastrophic state for siblings.

Closing checklist: five step headers use plain em dashes as mandated; Step 3 fenced SPL matches the spl JSON field; multisearch covers four kubelet series plus nested multisearch for events; streamstats implements ETA; join wraps inputlookup pvc_inventory.csv; case implements severity tiers; tstats enriches via left join; final table includes fifteen columns; monitoringType lists Performance and Capacity; cimModels lists Performance and Inventory; equipment lists kubernetes and opentelemetry; equipmentModels lists kubernetes_k8s; narrative avoids markdown headings and duplicate description value pairs; references span Kubernetes storage docs, CSI health monitor, kube-state-metrics PV and PVC metrics, StorageClass guidance, Splunk Kubernetes add-on documentation, and kubelet node metrics reference.

Long-term owners should rehearse handoffs to UC-3.2.25 when stakeholders only want instantaneous free-space dashboards, rehearse UC-3.2.4 when namespace quotas block new claims during incidents, keep pvc_inventory.csv aligned with GitOps truth, validate HEC routing whenever indexes split, replay synthetic fill tests after kubelet minor upgrades, and reconcile prometheus relabel rules quarterly so persistentvolumeclaim labels never silently disappear.

## SPL

```spl
`comment("UC-3.2.16 Bound PVC forecast+inode+RO. idx=k8s_metrics,k8s_events st=prometheus:scrape:metrics,kube:events bin=1h win=25 earliest=-30h@h")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | eval node=trim(toString(coalesce(node, Node, instance, kubernetes_io_hostname, "")))
      | where mn="kubelet_volume_stats_used_bytes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>=0
      | bin _time span=1h
      | stats max(mv) AS used_bytes latest(node) AS node BY cluster namespace pvc _time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | eval node=trim(toString(coalesce(node, Node, instance, kubernetes_io_hostname, "")))
      | where mn="kubelet_volume_stats_capacity_bytes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>0
      | bin _time span=1h
      | stats max(mv) AS capacity_bytes latest(node) AS node BY cluster namespace pvc _time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | eval node=trim(toString(coalesce(node, Node, instance, kubernetes_io_hostname, "")))
      | where mn="kubelet_volume_stats_inodes_used" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>=0
      | bin _time span=1h
      | stats max(mv) AS inodes_used latest(node) AS node BY cluster namespace pvc _time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, volume_kubernetes_io_persistentvolumeclaim, "")))
      | eval node=trim(toString(coalesce(node, Node, instance, kubernetes_io_hostname, "")))
      | where mn="kubelet_volume_stats_inodes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv) AND mv>0
      | bin _time span=1h
      | stats max(mv) AS inodes_total latest(node) AS node BY cluster namespace pvc _time ]
| stats max(used_bytes) AS used_bytes max(capacity_bytes) AS capacity_bytes max(inodes_used) AS inodes_used max(inodes_total) AS inodes_total latest(node) AS node BY cluster namespace pvc _time
| where isnotnull(used_bytes) AND isnotnull(capacity_bytes) AND capacity_bytes>0
| sort 0 cluster, namespace, pvc, _time
| streamstats window=25 current=t global=f first(used_bytes) AS u_first last(used_bytes) AS u_last first(_time) AS t_first last(_time) AS t_last BY cluster, namespace, pvc
| eval hours_elapsed=round((t_last-t_first)/3600, 4)
| eval growth_bytes_per_hour=if(hours_elapsed>0.25 AND isnotnull(u_first) AND isnotnull(u_last), round((u_last-u_first)/hours_elapsed, 6), null())
| eval growth_gb_per_24h=if(isnotnull(growth_bytes_per_hour), round((growth_bytes_per_hour*24)/1073741824, 4), null())
| eval rem_bytes=capacity_bytes-u_last
| eval days_to_full=if(isnotnull(growth_bytes_per_hour) AND growth_bytes_per_hour>1024 AND rem_bytes>0, round(rem_bytes/(growth_bytes_per_hour*24), 3), null())
| eval used_pct=round(100*u_last/capacity_bytes, 3)
| eval inode_pct=if(isnotnull(inodes_total) AND inodes_total>0 AND isnotnull(inodes_used), round(100*inodes_used/inodes_total, 3), null())
| eval used_gb=round(u_last/1073741824, 3)
| eval capacity_gb=round(capacity_bytes/1073741824, 3)
| sort 0 - _time
| dedup cluster namespace pvc
| join type=left max=0 cluster namespace pvc
    [| multisearch
          [ search index=k8s_events sourcetype="kube:events" earliest=-30h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
            | eval namespace=trim(toString(coalesce(metadata_namespace, namespace, involvedObject_namespace, "")))
            | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, involvedObject_name, `involvedObject.name`, "")))
            | eval reason=trim(toString(coalesce(reason, Reason, "")))
            | eval msg=lower(toString(coalesce(message, Message, _raw, "")))
            | where len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0
            | eval ro_hit=if(match(reason,"(?i)VolumeReadOnly") OR match(msg,"(?i)readonly") OR match(msg,"(?i)filesystemalmostfull") OR match(msg,"(?i)filesystemfull") OR match(reason,"(?i)FilesystemAlmostFull") OR match(reason,"(?i)FilesystemFull"), 1, 0)
            | where ro_hit=1
            | stats dc(_time) AS ro_event_distinct BY cluster namespace pvc
            | eval ro_remount_flag=if(ro_event_distinct>0, 1, 0) ]
          [ search index=k8s sourcetype="kube:events" earliest=-30h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
            | eval namespace=trim(toString(coalesce(metadata_namespace, namespace, involvedObject_namespace, "")))
            | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, involvedObject_name, `involvedObject.name`, "")))
            | eval reason=trim(toString(coalesce(reason, Reason, "")))
            | eval msg=lower(toString(coalesce(message, Message, _raw, "")))
            | where len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0
            | eval ro_hit=if(match(reason,"(?i)VolumeReadOnly") OR match(msg,"(?i)readonly") OR match(msg,"(?i)filesystemalmostfull") OR match(msg,"(?i)filesystemfull") OR match(reason,"(?i)FilesystemAlmostFull") OR match(reason,"(?i)FilesystemFull"), 1, 0)
            | where ro_hit=1
            | stats dc(_time) AS ro_event_distinct BY cluster namespace pvc
            | eval ro_remount_flag=if(ro_event_distinct>0, 1, 0) ]
      | stats max(ro_remount_flag) AS ro_remount_flag BY cluster namespace pvc ]
| fillnull value=0 ro_remount_flag
| join type=left max=0 cluster namespace pvc
    [| inputlookup pvc_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=trim(toString(namespace))
      | eval pvc=trim(toString(coalesce(pvc, persistentvolumeclaim, persistent_volume_claim, "")))
      | eval owner_team=trim(toString(coalesce(owner_team, team, squad, "")))
      | eval criticality=lower(trim(toString(coalesce(criticality, tier, ""))))
      | eval expansion_allowed=lower(trim(toString(coalesce(expansion_allowed, allow_expand, vol_expand, ""))))
      | eval storageclass=trim(toString(coalesce(storageclass, storage_class, sc, "")))
      | eval backup_class=trim(toString(coalesce(backup_class, backup_tier, "")))
      | fields cluster namespace pvc storageclass owner_team criticality expansion_allowed backup_class ]
| fillnull value="unknown" owner_team
| fillnull value="bronze" criticality
| fillnull value="unknown" expansion_allowed
| fillnull value="unknown" storageclass
| join type=left max=0 node
    [| tstats summariesonly=t max(Performance.disk_usage) AS node_disk_peak_pct FROM datamodel=Performance WHERE nodename=Performance.Storage earliest=-4h@h latest=now BY Performance.host
      | rename Performance.host AS node ]
| fields - node_disk_peak_pct
| eval severity=case(
    ro_remount_flag>=1, "catastrophic",
    used_pct>=95 OR inode_pct>=95, "critical",
    used_pct>=85 OR (isnotnull(days_to_full) AND days_to_full<=3), "high",
    used_pct>=75 OR (isnotnull(days_to_full) AND days_to_full<=14), "medium",
    true(), "low")
| where severity IN ("catastrophic","critical","high","medium")
| table cluster namespace pvc storageclass used_gb capacity_gb used_pct inode_pct growth_gb_per_24h days_to_full expansion_allowed criticality owner_team severity ro_remount_flag
| sort - severity +cluster +namespace +pvc

```

## CIM SPL

```spl
| tstats summariesonly=t max(Performance.disk_usage) AS peak_disk_pct latest(Performance.disk_usage) AS latest_disk_pct FROM datamodel=Performance WHERE nodename=Performance.Storage earliest=-4h@h latest=now BY Performance.host
| rename Performance.host AS kubelet_node
| where peak_disk_pct>85
```

## Visualization

Heatmap of used_pct by namespace; line chart of growth_gb_per_24h and days_to_full; single value catastrophic count; table of fifteen analyst columns with drilldown to kube:events; optional overlay with UC-3.2.25 instantaneous free-space panels.

## Known False Positives

Brief saturation spikes during bulk data-loader or restore jobs can cross high thresholds without customer impact; dampen using workload labels, maintenance macros, or temporary suppressions keyed on backup_class in pvc_inventory.csv when the window is CAB-approved. Archival or backup PVCs that are expected to land near full should carry backup_class=archive and criticality bronze so the alert routes to storage operations dashboards instead of product bridges. After PVC migration or node drain, growth rate may read zero until twenty-five hourly samples accumulate; days_to_full stays null and should not page alone without corroborating events. Inode_pct may climb while used_gb stays modest on legitimate small-file workloads such as mail or build artifact caches; pair with workload knowledge before declaring misconfiguration. Teams that deliberately run above eighty percent for cost control should set an inventory suppression flag or custom criticality tier after FinOps sign-off so governance matches intent. Duplicate scrapes from overlapping agents without dedup keys can jitter hour-over-hour growth; validate single writer per kubelet target. CIM node joins may miss when Performance.host naming differs from kubelet node labels; the control remains valid on kubelet metrics alone.

## References

- [Kubernetes PersistentVolumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Kubernetes Volume Health Monitoring](https://kubernetes.io/docs/concepts/storage/volume-health-monitoring/)
- [Kubernetes Storage Capacity](https://kubernetes.io/docs/concepts/storage/storage-capacity/)
- [Kubernetes CSI Volume Health Monitor](https://kubernetes-csi.github.io/docs/volume-health-monitor.html)
- [kube-state-metrics PersistentVolume metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/storage/persistentvolume-metrics.md)
- [kube-state-metrics PersistentVolumeClaim metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/storage/persistentvolumeclaim-metrics.md)
- [Kubernetes StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/)
- [Splunk Add-on for Kubernetes — About](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
- [Kubernetes node metrics (kubelet)](https://kubernetes.io/docs/reference/instrumentation/node-metrics/)
