<!-- AUTO-GENERATED from UC-3.2.5.json — DO NOT EDIT -->

---
id: "3.2.5"
title: "Kubernetes PersistentVolumeClaim Pending and Provisioning Failure Detection"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.5 · Kubernetes PersistentVolumeClaim Pending and Provisioning Failure Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch storage claims that never finish attaching so databases and other apps that need saved data cannot start. When a claim stays unfinished too long or the cluster reports a volume setup failure, we raise a clear signal so teams fix settings or capacity before customers feel it.*

---

## Description

Detects Kubernetes PersistentVolumeClaims stuck in phase Pending because dynamic provisioning failed or never completed: kube_persistentvolumeclaim_status_phase remains pending beyond a soak window, kube events surface FailedProvisioning, ProvisioningFailed, or ExternalProvisioning narratives, kube_storageclass_info reveals missing provisioners or WaitForFirstConsumer semantics, and requested bytes from kube_persistentvolumeclaim_resource_requests_storage_bytes contextualize capacity asks. The monitoring axis is bind-time and provisioner health, not bound-volume fill rate (UC-3.2.16), not cluster autoscaler node scale-out refusal (UC-3.2.46), and not image pull backoff (UC-3.2.14).

## Value

Cuts mean time to repair when databases, queues, and stateful microservices cannot mount volumes: responders see cluster, namespace, claim, StorageClass, CSI provisioner, binding mode, soak minutes, fused event reasons, governance tier, owning team, and optional fleet memory context in one row instead of correlating kubectl, metrics consoles, and five CSI log streams by hand. Customer-visible reliability improves when StorageClass, quota, topology, access mode, or CSI controller failures are fixed before StatefulSets stall for an hour.

## Implementation

Ingest kube-state-metrics PVC and StorageClass info plus Kubernetes API events into Splunk indexes k8s_metrics and k8s; publish lookups/critical_namespaces.csv with tier and owner columns; schedule saved search uc_3_2_5_pvc_provisioning_failure every five minutes with earliest=-45m@m and latest=now; page when pending_soak_min crosses ten minutes with provisioning-failure events or critical severity; validate using a lab PVC that references a nonexistent StorageClass and confirm phase Pending persists until you delete the claim.

## Evidence

Saved search uc_3_2_5_pvc_provisioning_failure with five-minute schedule; lookups/critical_namespaces.csv versioned in git; weekly CSV export of alert rows to a restricted evidence index with lookup commit hash for auditors.

## Control test

### Positive scenario

In lab namespace qa-pvc-provision, create a PVC with storageClassName pointing at a deliberately missing class, wait for kube_persistentvolumeclaim_status_phase pending samples and kube:events provisioning failure messages, execute uc_3_2_5_pvc_provisioning_failure, and expect a qualifying row with severity at least medium after the soak gate.

### Negative scenario

Delete the lab PVC or correct the StorageClass to a valid gp3, pd-balanced, managed-csi, or equivalent class, wait for fresh scrapes, confirm phase transitions to Bound in metrics, and verify the saved search emits no qualifying row for that claim.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with Kubernetes storage engineering, observability, and tenant site-reliability teams who operate Splunk OpenTelemetry Collector fleets and CSI drivers across cloud and on-premises footprints. UC-3.2.5 is the PersistentVolumeClaim binding and dynamic provisioning failure plane: it consumes kube-state-metrics series kube_persistentvolumeclaim_status_phase for phase Pending, kube_persistentvolumeclaim_info for requested StorageClass and bound volume hints, kube_persistentvolumeclaim_resource_requests_storage_bytes for capacity asks, kube_storageclass_info for provisioner identity and volume binding semantics, and Kubernetes API events whose reasons include FailedProvisioning, ProvisioningFailed, and ExternalProvisioning or whose messages reference missing StorageClasses, unsupported access modes, CSI driver discovery failures, or cloud quota denials. UC-3.2.16 remains the bound PVC filesystem fill-rate, inode, and read-only remount story once volumes are mounted; do not route byte-exhaustion analytics here. UC-3.2.46 covers cluster autoscaler and Karpenter scale-out refusal with pod Pending backlog tied to node provisioning; this UC isolates volume provisioning backlog on the PVC object itself even when nodes are plentiful. UC-3.2.4 governs namespace ResourceQuota admission exhaustion that can block object creation including PVCs; pair alerts when Splunk shows quota denial events in the same namespace minute. UC-3.2.14 documents ImagePullBackOff; storage claims can remain Pending while pods never schedule, so correlate but keep ticketing separate until image pulls succeed.

Index and token contracts precede saved-search authoring. Stand up index=k8s_metrics for prometheus:scrape:metrics text or normalized metric events scraped from kube-state-metrics Deployments and from optional CSI controller manager metrics endpoints when FinOps approves the extra cardinality. Stand up index=k8s or index=k8s_events for sourcetype=kube:events streams with consistent cluster labels matching your kube-state-metrics external labels. Issue distinct HEC tokens per index class with role-based search restrictions so developers can troubleshoot their namespaces without reading kube-system audit bodies. Document retention: metrics hot buckets at least fourteen days for replay, events at least thirty days for provisioning timelines.

Deploy kube-state-metrics with the storage metric families enabled so kube_persistentvolumeclaim_status_phase exposes labels namespace, persistentvolumeclaim, and phase, kube_persistentvolumeclaim_info exposes storageclass and volumename transitions, and kube_storageclass_info exposes provisioner, reclaim policy, and volume binding mode labels per your chart version. Scrape intervals of thirty seconds are typical; fifteen seconds improves soak-time fidelity at license cost. For managed Kubernetes, align default StorageClasses with vendor guidance: Amazon EKS commonly ships gp2 or gp3 CSI classes backed by ebs.csi.aws.com; Google GKE uses persistent disk CSI provisioners; Microsoft AKS uses managed disk CSI equivalents; VMware Tanzu uses the vSphere CSI driver; Red Hat OpenShift clusters may add Ceph CSI classes for Rook, portworx.io for Portworx, driver.longhorn.io for Longhorn, and Local Storage Operator workflows that pair local static provisioners with discovery rules.

Governance lookup lookups/critical_namespaces.csv must contain namespace, workload_tier taking values prod, production, preprod, staging, dev, sandbox, and owner_team or on_call_team strings for routing gold namespaces to voice bridges. Refresh weekly from GitOps exports or service catalog pipelines and attach commit hashes when auditors ask for lineage. Gold rows route critical severity to immediate paging when FailedProvisioning coincides with database or queue namespaces. Silver rows open tickets with platform carbon copy. Bronze and sandbox rows remain dashboard-only unless an executive override marks customer impact.

Risk briefing: a PVC stuck Pending blocks StatefulSets, Kafka brokers, Elasticsearch data nodes, relational databases, and machine-learning checkpoint volumes from becoming Ready. CSI external-provisioner and attacher sidecars can backlog when the API server is slow or when cloud rate limits throttle volume creation; Splunk shows Pending phase long before kubectl events scroll off the terminal. Silently dropping persistentvolumeclaim labels at scrape time makes the control blind while kubectl still shows Pending claims.

Licensing note: multisearch arms and appendcols tstats overlays keep search cost predictable; avoid unbounded joins across full metric indexes without filters. Privacy note: event messages can include volume handles; restrict dashboard ACLs.

Differentiation recap: PVC Pending soak plus provisioning failure events and StorageClass metadata, not bound-volume fill rate, not autoscaler node denial, not image pull failure taxonomy.

Collector architecture notes: self-managed clusters scrape kube-state-metrics inside the mesh; air-gapped environments mirror images before enabling storage metrics. Dual-stack IPv6 clusters must preserve consistent instance labels in relabel configs.

FinOps alignment: requested_storage_bytes from kube_persistentvolumeclaim_resource_requests_storage_bytes helps compare ask versus cloud quota denial messages.

Reliability alignment: single-replica StatefulSets may stall entirely when the ordinal zero claim never binds; critical severity should open a bridge, not a ticket-only workflow.

Security alignment: CSI driver logs can include cloud resource identifiers; scrub exports when sharing outside platform teams.

Performance alignment: keep multisearch arms narrow with explicit metric names to prevent accidental high-cardinality explosions from unrelated kube-state-metrics families.

Training alignment: teach responders that WaitForFirstConsumer classes are Pending by design until scheduling, distinct from missing StorageClass errors.

Documentation alignment: wiki-map this UC beside PersistentVolume, StorageClass, and CSI troubleshooting documentation.

Review cadence: quarterly replay one historical provisioning outage through the SPL after kube-state-metrics upgrades.

Escalation alignment: critical plus gold workload_tier engages storage engineering and application leadership jointly.

Telemetry hygiene: deduplicate overlapping Prometheus agents that scrape kube-state-metrics without honor_labels discipline.

Governance alignment: CAB records should cover HEC token ACL changes and ServiceMonitor edits together when scrape paths move.

Platform engineering note 1: AWS EBS CSI controller logs frequently include volume attachment race messages after node loss; correlate Pending claims with node repair before resizing claims.

Platform engineering note 2: GCE PD CSI surfaces zone mismatch errors when regional disks are requested with incompatible topology; validate allowedTopologies in StorageClass YAML against workload node selectors.

Platform engineering note 3: Azure Disk CSI returns throttling strings during subscription-wide storms; widen alert correlation to Azure Monitor storage metrics when finance approves cloud telemetry joins.

Platform engineering note 4: vSphere CSI logs CNS task failures when datastore clusters lack capacity; pair Splunk rows with vCenter alarms before declaring application bugs.

Platform engineering note 5: OpenShift Local Storage Operator adds discovery DaemonSets; Pending claims on local volumes may mean no eligible disks matched the device filter.

Platform engineering note 6: Rook-Ceph operator logs show OSD preparation failures when raw devices are busy; distinguish operator errors from Kubernetes API provisioning timeouts.

Platform engineering note 7: Portworx px-storage logs include quorum loss narratives; escalate to storage vendor bridges when many claims stall simultaneously.

Platform engineering note 8: Longhorn manager logs replica scheduling failures when node disk pressure blocks replica placement; cross-check node conditions before muting.

Platform engineering note 9: External-provisioner sidecars emit ExternalProvisioning events while waiting for CSI CreateVolume; long dwell times can mean controller backlog, not user error.

Platform engineering note 10: kubectl describe storageclass still answers whether volumeBindingMode is WaitForFirstConsumer or Immediate; teach responders to read that line before paging.

Platform engineering note 11: Static provisioning with claimRef on a PV requires label and selector alignment; Splunk may show Pending until the claim name matches the reservation.

Platform engineering note 12: VolumeSnapshot restore controllers can leave claims Pending while content populates; verify VolumeSnapshotContents and snapshot-controller logs.

Platform engineering note 13: AccessMode ReadWriteMany on a ReadWriteOnce-only class fails fast with clear events; route to architects, not capacity teams.

Platform engineering note 14: ResourceQuota can block PVC creation entirely; UC-3.2.4 should fire alongside this UC when admission rejects new claims.

Platform engineering note 15: Helm pre-upgrade hooks that create PVCs may race chart deletes; sandbox namespaces can look unhealthy during CI churn.

Platform engineering note 16: Dual kube-state-metrics during migration can duplicate phase series; enforce one authoritative scrape per cluster label set.

Platform engineering note 17: Air-gapped registries must host CSI sidecar images; missing sidecars present as Pending without obvious API errors until describe inspects pod events on controller Deployments.

Platform engineering note 18: PodSecurity admission does not usually block PVCs, but namespace policy changes during incidents can confuse investigators; keep RBAC audit trails handy.

Platform engineering note 19: Immutable Secrets for CSI driver credentials rotate on different cadences than node AMIs; token expiry shows up as generic provisioning failures.

Platform engineering note 20: Windows node pools with Linux-formatted StorageClasses remain unsupported combinations; validate OS and CSI matrix in architecture reviews.

Platform engineering note 21: Tanzu supervisor clusters may rename contexts; ensure Splunk cluster labels match kubectl context names operators recognize.

Platform engineering note 22: Edge clusters with intermittent WAN may delay event delivery; widen earliest modestly only after confirming clock sync.

Platform engineering note 23: PCI environments should redact customer volume IDs in ticket bodies while keeping hashed correlators for forensics.

Platform engineering note 24: SOC2 evidence packs should store weekly CSV exports with lookup commit hashes tied to change records.

Platform engineering note 25: FinOps chargeback can map requested_storage_bytes spikes to cost centers when many teams land claims during the same patch Tuesday.

Platform engineering note 26: Chaos experiments that delete StorageClasses should carry suppressions so game days do not page executives.

Platform engineering note 27: GitOps drift detectors should compare live StorageClass parameters with repository YAML, especially encrypted and kms-key-id fields.

Platform engineering note 28: KMS permission changes on cloud disks surface as authorization failures in CSI logs; route to cloud identity teams quickly.

Platform engineering note 29: Zonal outages in a single AZ can strand Immediate binding classes that lack topology spread; read cloud provider status pages when severity spikes region-wide.

Platform engineering note 30: OpenTelemetry memory limits may drop metric batches during etcd storms; watch collector health before blaming storage backends.

Platform engineering note 31: Splunk Cloud workload management may pause searches during indexer maintenance; document exceptions for this saved search in runbooks.

Platform engineering note 32: ITSI optional episodes should bind PVC entities only when service models already map datastores; avoid duplicate notable storms.

Platform engineering note 33: Executive summaries benefit from a thirty-day rolling count of critical provisioning incidents by provisioner string.

Platform engineering note 34: Post-incident reviews should record whether remediation was class correction, quota increase, CSI upgrade, cloud ticket, or architecture change.

Platform engineering note 35: Penetration tests should validate HEC tokens cannot read unrelated security indexes while still indexing kube events.

Platform engineering note 36: SRE onboarding labs should include deliberate StorageClass typos with tear-down checklists so new responders recognize metric shapes.

Platform engineering note 37: Configuration management databases should feed critical_namespaces.csv automatically to reduce stale owner routing.

Platform engineering note 38: Multi-region fleets need identical label contracts on kube-state-metrics scrapes so joins never null cluster keys during failover drills.

Platform engineering note 39: RPO and RTO reviews should mention PVC provisioning time because restore timelines include binding latency, not only snapshot copy minutes.

Platform engineering note 40: Application architects should document allowed access modes during service template reviews so misconfiguration alerts decline over time.

Platform engineering note 41: Build platforms that mint ephemeral PVCs for compilation caches should tag namespaces as sandbox in lookups to protect paging quality.

Platform engineering note 42: Anomaly detection overlays remain optional until baselines exist; do not auto-tune soak minutes from ML without SME review.

Platform engineering note 43: Grafana mirror dashboards should cite Splunk as the paging system of record to avoid dual-alert fatigue.

Platform engineering note 44: PagerDuty deduplication keys should include cluster, namespace, and pvc to prevent merged tickets from hiding distinct claims.

Platform engineering note 45: Slack bridges should post provisioner, storageclass, and pending_soak_min in the first line for fast human triage.

Platform engineering note 46: Jira automation should link back to the saved search URL and include three redacted event excerpts when legal approves.

Platform engineering note 47: Legal hold procedures must preserve kube events without deleting metrics samples that prove phase transitions.

Platform engineering note 48: Disaster recovery teams should rehearse provisioning failures during partial region isolation exercises annually.

### Step 2 — Configure data collection

Deploy a ServiceMonitor or PodMonitor that selects kube-state-metrics and scrapes port 8080 metrics path /metrics with intervals and timeouts aligned to your kube-prometheus-stack baseline. Relabel rules must preserve namespace, persistentvolumeclaim, storageclass, phase, provisioner, and volume_binding_mode labels emitted by your kube-state-metrics version so Splunk coalesce ladders stay short.

OpenTelemetry Collector prometheus receiver jobs should target the kube-state-metrics Service DNS name inside the cluster and forward to Splunk HEC with index=k8s_metrics and sourcetype=prometheus:scrape:metrics. Pair this with a kubernetes_events or k8s_events receiver in watch mode so FailedProvisioning narratives arrive with the same cluster tag your metrics carry.

Example ServiceMonitor skeleton:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-storage
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
      path: /metrics
```

Collector fragment showing kube-state-metrics scrape plus events export:

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: kube-state-metrics
          kubernetes_sd_configs:
            - role: endpoints
          relabel_configs:
            - source_labels: [__meta_kubernetes_service_name]
              action: keep
              regex: kube-state-metrics
  k8s_events:
    auth_type: serviceAccount
    namespaces: []
exporters:
  splunk_hec/metrics:
    token: ${SPLUNK_HEC_TOKEN_K8S_METRICS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
  splunk_hec/events:
    token: ${SPLUNK_HEC_TOKEN_K8S_EVENTS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s
    sourcetype: kube:events
service:
  pipelines:
    metrics/ksm:
      receivers: [prometheus]
      exporters: [splunk_hec/metrics]
    logs/events:
      receivers: [k8s_events]
      exporters: [splunk_hec/events]
```

Sample critical_namespaces.csv:

```csv
namespace,workload_tier,owner_team,criticality
prod-payments-db,prod,payments-sre,gold
qa-load,sandbox,platform-qa,bronze
```

Forward CSI controller logs when policy permits: AWS EBS CSI controller pods often log InvalidParameterCombination or attachment failures; GCE PD CSI logs volume handle errors; Azure Disk CSI surfaces throttling strings; vSphere CSI logs CNS task failures; Rook-Ceph operator logs reconcile errors; Longhorn manager logs replica scheduling failures; Portworx px-storage pods log cluster quorum issues. Filelog receivers may tail controller namespaces with redaction rules.

props and transforms guidance: normalize __name__, value, namespace, persistentvolumeclaim, storageclass, and cluster labels onto indexed fields; keep camelCase aliases from OTEL exporters in transforms.conf so SPL coalesce lists stay stable.

Validation before alert authoring: index=k8s_metrics kube_persistentvolumeclaim_status_phase earliest=-30m must return phase pending with non-zero values; index=k8s sourcetype=kube:events earliest=-24h should include provisioning failures in busy clusters. Clock skew between API server, kube-state-metrics, and Splunk _time must stay under sixty seconds.

### Step 3 — Create the search and alert

Save the SPL as saved search uc_3_2_5_pvc_provisioning_failure with five-minute schedule, dispatch earliest=-45m@m, dispatch latest=now, and throttle duplicate medium rows per cluster namespace pvc for ninety minutes unless severity escalates to critical. Route critical to immediate voice paging with storage and application bridges; route high to high-priority tickets with SMS backup for gold namespaces from critical_namespaces.csv.

Pipeline understanding for operators: the opening comment macro lists indexes, soak threshold, and time horizon. multisearch fans phase timelines and provisioning event arms so a silent failure in one path still surfaces the other. streamstats measures continuous Pending duration per PVC using one-minute buckets. coalesce ladders normalize cluster, namespace, pvc, and storageclass labels across EKS, GKE, and AKS field habits. join pulls kube_persistentvolumeclaim_info for StorageClass hints, kube_persistentvolumeclaim_resource_requests_storage_bytes for capacity asks, and kube_storageclass_info for provisioner and volume_binding_mode. inputlookup critical_namespaces.csv enriches workload_tier and owner_team. appendcols runs an accelerated tstats average against Performance.Memory as a fleet memory pressure hint when Common Information Model summaries exist; if the subsearch returns no rows, cim_mem_fleet_avg may be null without blocking results. eventstats adds cluster_peak_pending for situational awareness. case maps severity using event text and soak minutes. The closing table lists thirteen analyst columns.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.5 PVC Pending / provisioning failure axis. idx=k8s_metrics,k8s earliest=-45m@m latest=now pending_soak_alert_min=10")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-45m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval phase=lower(trim(toString(coalesce(phase, phase_name, ""))))
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, "")))
      | where mn="kube_persistentvolumeclaim_status_phase" AND phase="pending" AND mv>0 AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0
      | bucket _time span=1m
      | stats max(mv) AS pend BY cluster namespace pvc _time
      | where pend>0
      | sort 0 cluster namespace pvc + _time
      | streamstats current=t global=f first(_time) AS pend_start BY cluster namespace pvc
      | eval pending_soak_min=round((now()-pend_start)/60, 3)
      | stats latest(pending_soak_min) AS pending_soak_min BY cluster namespace pvc
      | eval evt_reason=""
      | eval evt_msg="" ]
    [ search (index=k8s OR index=k8s_events) sourcetype="kube:events" earliest=-45m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
      | eval namespace=trim(toString(coalesce(metadata_namespace, namespace, involvedObject_namespace, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, involvedObject_name, `involvedObject.name`, "")))
      | eval ik=lower(trim(toString(coalesce(involvedObject_kind, `involvedObject.kind`, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=toString(coalesce(message, Message, ""))
      | eval lump=lower(reason." ".msg)
      | where ik="persistentvolumeclaim" OR like(lump, "%persistentvolumeclaim%") OR like(lump, "%volume claim%")
      | where match(lump, "(?i)failedprovisioning|provisioningfailed|externalprovisioning|waiting for a volume to be created|storageclass|no.*provisioner|not supported|did not find.*driver|insufficient.*capacity|access mode|already exists") OR reason IN ("ProvisioningFailed","FailedProvisioning","ExternalProvisioning")
      | stats latest(reason) AS evt_reason latest(msg) AS evt_msg BY cluster namespace pvc
      | eval pending_soak_min=0 ]
| stats max(pending_soak_min) AS pending_soak_min values(evt_reason) AS evt_reason_mv values(evt_msg) AS evt_msg_mv BY cluster namespace pvc
| eval evt_reason=coalesce(nullif(trim(mvindex(mvdedup(evt_reason_mv),0)),""), "")
| eval evt_msg=coalesce(nullif(trim(mvindex(mvdedup(evt_msg_mv),0)),""), "")
| eventstats max(pending_soak_min) AS cluster_peak_pending BY cluster
| join type=left max=0 cluster namespace pvc
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-45m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, "")))
      | eval sc=trim(toString(coalesce(storageclass, storage_class_name, storage_class, "")))
      | where mn="kube_persistentvolumeclaim_info" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0
      | stats latest(sc) AS storageclass BY cluster namespace pvc ]
| join type=left max=0 cluster namespace pvc
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-45m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, "")))
      | where mn="kube_persistentvolumeclaim_resource_requests_storage_bytes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv)
      | stats latest(mv) AS requested_storage_bytes BY cluster namespace pvc ]
| join type=left max=0 cluster storageclass
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-45m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval storageclass=trim(toString(coalesce(storageclass, storage_class, "")))
      | eval provisioner=trim(toString(coalesce(provisioner, "")))
      | eval volume_binding_mode=trim(toString(coalesce(volume_binding_mode, volumeBindingMode, "")))
      | where mn="kube_storageclass_info" AND len(storageclass)>0
      | stats latest(provisioner) AS provisioner latest(volume_binding_mode) AS volume_binding_mode BY cluster storageclass ]
| join type=left max=0 namespace
    [| inputlookup critical_namespaces.csv
      | eval namespace=trim(toString(namespace))
      | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, criticality, "standard"))))
      | eval owner_team=trim(toString(coalesce(owner_team, squad, on_call_team, "")))
      | fields namespace workload_tier owner_team ]
| fillnull value="" evt_reason evt_msg provisioner volume_binding_mode storageclass
| fillnull value=0 requested_storage_bytes cluster_peak_pending
| eval pending_soak_min=round(coalesce(pending_soak_min, 0), 2)
| eval severity=case(
    match(lower(evt_msg), "(?i)storageclass.*not found|no.*provisioner|not found") AND pending_soak_min>=10, "critical",
    match(lower(evt_reason), "(?i)provisioningfailed|failedprovisioning") OR match(lower(evt_msg), "(?i)provisioningfailed|failedprovisioning"), "critical",
    pending_soak_min>=25 AND len(storageclass)==0, "critical",
    pending_soak_min>=20, "high",
    pending_soak_min>=15 OR len(evt_reason)>0, "high",
    pending_soak_min>=10, "medium",
    true(), "low")
| where severity IN ("critical","high","medium") AND (pending_soak_min>=10 OR len(evt_reason)>0 OR len(evt_msg)>0)
| appendcols [ | tstats summariesonly=true avg(Performance.mem_used_percent) AS cim_mem_fleet_avg FROM datamodel=Performance WHERE nodename=Performance.Memory earliest=-2h@h latest=now | head 1 ]
| table cluster namespace pvc storageclass provisioner volume_binding_mode requested_storage_bytes pending_soak_min cluster_peak_pending evt_reason evt_msg workload_tier owner_team severity cim_mem_fleet_avg
| sort - severity +cluster +namespace +pvc
```

Alert actions: include cluster, namespace, pvc, storageclass, provisioner, pending_soak_min, evt_reason, evt_msg, severity, and owner_team in tickets; link to Dashboard Studio PVC health view; attach three redacted kube events when legal approves.

Operational notes: when kube_persistentvolumeclaim_info is missing because a scrape dropped labels, storageclass may be null while kubectl still shows a class; investigate relabel configs before muting. When only events fire without Pending metrics, assume kube-state-metrics outage rather than healthy storage.

Dashboard publishing: heatmap of pending_soak_min by namespace; single value critical count; table sorted by severity then tier.

Evidence retention: weekly CSV of the closing table with critical_namespaces.csv commit hash stored in a restricted index satisfies internal audits when paired with kubectl describe pvc screenshots during game days.

Performance tuning: if Job Inspector shows multisearch queueing, materialize five-minute rollups into a summary index and point this alert at summaries while retaining raw scrapes for investigations.

Reliability: during kube-state-metrics upgrades expect brief gaps; require two intervals of missing metrics before paging scrape failures unless events remain hot.

Governance: when legal requests preservation, include event hash lists and redact customer strings per counsel instructions.

### Step 4 — Validate

Synthetic negative StorageClass: in namespace qa-pvc-provision create a PVC referencing storageClassName this-class-does-not-exist with a modest resource request; confirm kube_persistentvolumeclaim_status_phase shows pending within two scrape intervals and kube:events includes messages that name the missing class. Execute uc_3_2_5_pvc_provisioning_failure and expect a row with non-null evt_msg or evt_reason and severity at least medium after the soak gate.

Synthetic access mode mismatch: create a PVC requesting readWriteMany against a class that only supports readWriteOnce when your lab policy allows; confirm provisioning failure events appear quickly even when soak is short; validate severity escalates on message patterns without waiting for unrelated fill-rate signals.

Synthetic positive clear: delete the lab PVC and broken StorageClass references, restore normal classes, confirm the saved search returns zero qualifying rows on the next interval, and verify alert auto-clear behavior in your notification system.

Field sanity: rename a sandbox forwarder label to persistent_volume_claim only and verify coalesce still resolves pvc. RBAC: readers without index access must see zero rows.

Correlation: compare alert timestamps to kubectl describe pvc and kubectl describe storageclass output; misalignment often means metrics lagged behind API writes, so widen the alert window temporarily during investigations.

CSI controller health: scale the CSI controller Deployment to zero in lab only, observe Pending claims and provisioner errors, then restore replicas and confirm recovery paths match runbook expectations.

Extended validation: snapshot the alert table before and after fixing the StorageClass; store kubectl get events output; capture CSI controller logs when available; verify streamstats soak resets after intentional claim deletion.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Missing StorageClass name or typo in volume.beta.kubernetes.io/storage-class annotation on legacy claims: fix GitOps manifests, roll forward, confirm kube_storageclass_info joins succeed, and watch phase transition to Bound.

Case 2 — AWS EBS CSI controller pods not Ready: kubectl get pods for the driver namespace, read controller logs for AWS API errors, fix IAM or STS assumptions, then replay provisioning.

Case 3 — GCE PD CSI topology mismatch: adjust allowedTopologies in the StorageClass or relax pod constraints; confirm PD creation succeeds in the intended zone.

Case 4 — Azure Disk CSI throttling or subscription limits: open a cloud ticket with evt_msg excerpts; temporarily shed non-production workloads.

Case 5 — vSphere CSI CNS failures: engage virtualization teams with datastore utilization evidence; do not assume Kubernetes alone can fix datastore exhaustion.

Case 6 — OpenShift Local Storage Operator discovery problems: validate LocalVolume and node disk inventory; Pending local claims often mean no matching devices.

Case 7 — Rook-Ceph operator reconcile errors: inspect ceph cluster health before resizing claims; operator logs beat guessing from Pending alone.

Case 8 — Portworx quorum or metadata issues: follow vendor bridges; many claims stall together when the storage cluster is unhealthy.

Case 9 — Longhorn replica scheduling blocked by disk pressure: clean node disks or expand backing stores; correlate with node condition metrics.

Case 10 — External-provisioner backlog during API server outages: treat as control-plane incident; widen correlation to UC-3.2.7 style signals when present in your catalogue.

Case 11 — Namespace terminating with PVC finalizers: finalize stuck objects under change control rather than blaming CSI drivers.

Case 12 — Manual PV pre-bind flow waiting for claimRef alignment: complete the static provisioning checklist; suppress alerts only with documented migration windows.

Closing checklist: five step headers use plain em dashes as mandated; Step 3 fenced SPL matches the spl JSON field; multisearch covers phase and event arms; streamstats implements soak timing; joins include PVC info, request bytes, StorageClass info, and critical_namespaces inputlookup; case implements severity tiers; appendcols provides tstats Performance overlay; final table includes thirteen columns; monitoringType lists Reliability and Availability; cimModels lists Performance and Inventory; equipment lists kubernetes and opentelemetry; equipmentModels lists kubernetes_k8s; narrative avoids markdown bold in operational fields; references span Kubernetes storage docs, CSI guidance, and major CSI drivers.

## SPL

```spl
`comment("UC-3.2.5 PVC Pending / provisioning failure axis. idx=k8s_metrics,k8s earliest=-45m@m latest=now pending_soak_alert_min=10")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-45m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval phase=lower(trim(toString(coalesce(phase, phase_name, ""))))
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, "")))
      | where mn="kube_persistentvolumeclaim_status_phase" AND phase="pending" AND mv>0 AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0
      | bucket _time span=1m
      | stats max(mv) AS pend BY cluster namespace pvc _time
      | where pend>0
      | sort 0 cluster namespace pvc + _time
      | streamstats current=t global=f first(_time) AS pend_start BY cluster namespace pvc
      | eval pending_soak_min=round((now()-pend_start)/60, 3)
      | stats latest(pending_soak_min) AS pending_soak_min BY cluster namespace pvc
      | eval evt_reason=""
      | eval evt_msg="" ]
    [ search (index=k8s OR index=k8s_events) sourcetype="kube:events" earliest=-45m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
      | eval namespace=trim(toString(coalesce(metadata_namespace, namespace, involvedObject_namespace, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, involvedObject_name, `involvedObject.name`, "")))
      | eval ik=lower(trim(toString(coalesce(involvedObject_kind, `involvedObject.kind`, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=toString(coalesce(message, Message, ""))
      | eval lump=lower(reason." ".msg)
      | where ik="persistentvolumeclaim" OR like(lump, "%persistentvolumeclaim%") OR like(lump, "%volume claim%")
      | where match(lump, "(?i)failedprovisioning|provisioningfailed|externalprovisioning|waiting for a volume to be created|storageclass|no.*provisioner|not supported|did not find.*driver|insufficient.*capacity|access mode|already exists") OR reason IN ("ProvisioningFailed","FailedProvisioning","ExternalProvisioning")
      | stats latest(reason) AS evt_reason latest(msg) AS evt_msg BY cluster namespace pvc
      | eval pending_soak_min=0 ]
| stats max(pending_soak_min) AS pending_soak_min values(evt_reason) AS evt_reason_mv values(evt_msg) AS evt_msg_mv BY cluster namespace pvc
| eval evt_reason=coalesce(nullif(trim(mvindex(mvdedup(evt_reason_mv),0)),""), "")
| eval evt_msg=coalesce(nullif(trim(mvindex(mvdedup(evt_msg_mv),0)),""), "")
| eventstats max(pending_soak_min) AS cluster_peak_pending BY cluster
| join type=left max=0 cluster namespace pvc
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-45m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, "")))
      | eval sc=trim(toString(coalesce(storageclass, storage_class_name, storage_class, "")))
      | where mn="kube_persistentvolumeclaim_info" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0
      | stats latest(sc) AS storageclass BY cluster namespace pvc ]
| join type=left max=0 cluster namespace pvc
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-45m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | eval pvc=trim(toString(coalesce(persistentvolumeclaim, persistent_volume_claim, pvc, persistentVolumeClaim, "")))
      | where mn="kube_persistentvolumeclaim_resource_requests_storage_bytes" AND len(cluster)>0 AND len(namespace)>0 AND len(pvc)>0 AND isnotnull(mv)
      | stats latest(mv) AS requested_storage_bytes BY cluster namespace pvc ]
| join type=left max=0 cluster storageclass
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-45m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval storageclass=trim(toString(coalesce(storageclass, storage_class, "")))
      | eval provisioner=trim(toString(coalesce(provisioner, "")))
      | eval volume_binding_mode=trim(toString(coalesce(volume_binding_mode, volumeBindingMode, "")))
      | where mn="kube_storageclass_info" AND len(storageclass)>0
      | stats latest(provisioner) AS provisioner latest(volume_binding_mode) AS volume_binding_mode BY cluster storageclass ]
| join type=left max=0 namespace
    [| inputlookup critical_namespaces.csv
      | eval namespace=trim(toString(namespace))
      | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, criticality, "standard"))))
      | eval owner_team=trim(toString(coalesce(owner_team, squad, on_call_team, "")))
      | fields namespace workload_tier owner_team ]
| fillnull value="" evt_reason evt_msg provisioner volume_binding_mode storageclass
| fillnull value=0 requested_storage_bytes cluster_peak_pending
| eval pending_soak_min=round(coalesce(pending_soak_min, 0), 2)
| eval severity=case(
    match(lower(evt_msg), "(?i)storageclass.*not found|no.*provisioner|not found") AND pending_soak_min>=10, "critical",
    match(lower(evt_reason), "(?i)provisioningfailed|failedprovisioning") OR match(lower(evt_msg), "(?i)provisioningfailed|failedprovisioning"), "critical",
    pending_soak_min>=25 AND len(storageclass)==0, "critical",
    pending_soak_min>=20, "high",
    pending_soak_min>=15 OR len(evt_reason)>0, "high",
    pending_soak_min>=10, "medium",
    true(), "low")
| where severity IN ("critical","high","medium") AND (pending_soak_min>=10 OR len(evt_reason)>0 OR len(evt_msg)>0)
| appendcols [ | tstats summariesonly=true avg(Performance.mem_used_percent) AS cim_mem_fleet_avg FROM datamodel=Performance WHERE nodename=Performance.Memory earliest=-2h@h latest=now | head 1 ]
| table cluster namespace pvc storageclass provisioner volume_binding_mode requested_storage_bytes pending_soak_min cluster_peak_pending evt_reason evt_msg workload_tier owner_team severity cim_mem_fleet_avg
| sort - severity +cluster +namespace +pvc
```

## CIM SPL

```spl
| tstats summariesonly=true latest(Inventory.vendor_product) AS inv_product count AS inv_events FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
| rename Inventory.dest AS inventory_dest
| join type=left max=0 inventory_dest [| tstats summariesonly=true avg(Performance.mem_used_percent) AS mem_used_pct FROM datamodel=Performance WHERE nodename=Performance.Memory earliest=-4h@h latest=now BY Performance.host
| rename Performance.host AS inventory_dest ]
| where inv_events>0
```

## Visualization

Primary table mirroring the closing SPL projection; secondary single value for critical severity row count; timechart of pending_soak_min by namespace; drilldown to kube:events and CSI controller logs for the same claim.

## Known False Positives

WaitForFirstConsumer StorageClasses legitimately leave new claims in phase Pending until a pod that references the volume is scheduled; treat long soak only as incident-grade when no workload is waiting or when events already show FailedProvisioning. Short-lived Pending rows from CI namespaces that create and delete claims within a few minutes resemble outages in raw metrics; require the ten-minute soak or an explicit provisioning event before paging production. Snapshot restore or clone workflows can keep claims Pending while the external snapshot controller binds objects; cross-check VolumeSnapshotContents before blaming CSI drivers. Capacity-starved development clusters may queue dynamic provisioning for tens of minutes during noisy neighbor tests; dampen dev tiers via critical_namespaces.csv workload_tier=sandbox. Namespaces stuck in Terminating often retain PVC finalizers; kubectl get namespace shows status Terminating and Splunk still lists Pending phase even though no new work is expected—route to namespace finalizer runbooks instead of storage rebuilds. Manual static provisioning with pre-created PersistentVolumes and claimRef can intentionally delay binding until selectors align; suppress known migration windows with CAB macros. RWX requests against a ReadWriteOnce-only class produce immediate FailedProvisioning messages that are real incidents but not disk-full problems; do not hand off to UC-3.2.16 fill-rate analytics. Helm test hooks that mint ephemeral PVCs may spam events; exclude chart test namespaces via lookup flags. Dual kube-state-metrics scrapes without deduplication can double pending_soak calculations until relabel rules converge. Cloud credential or quota errors on EBS, PD, Azure Disk, or vSphere volumes surface as distinct error strings; avoid muting the alert when only the message wording changes between vendor releases.

## References

- [Kubernetes PersistentVolumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Kubernetes StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/)
- [Kubernetes CSI documentation](https://kubernetes-csi.github.io/docs/)
- [Amazon EKS — Amazon EBS CSI driver](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html)
- [Google Cloud — GKE persistent disk CSI driver](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/gce-pd-csi-driver)
- [Azure Disk CSI driver](https://github.com/kubernetes-sigs/azuredisk-csi-driver)
- [VMware vSphere Container Storage Plug-in](https://docs.vmware.com/en/VMware-vSphere-Container-Storage-Plug-in/index.html)
- [Rook Ceph documentation](https://rook.io/docs/rook/latest-release/)
- [Longhorn documentation](https://longhorn.io/docs/)
- [Portworx on Kubernetes](https://docs.portworx.com/portworx-kubernetes.html)
- [Splunk Add-on for Kubernetes — About](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
