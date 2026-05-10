<!-- AUTO-GENERATED from UC-3.3.10.json — DO NOT EDIT -->

---
id: "3.3.10"
title: "OpenShift Storage Operator and ClusterCSIDriver Health (CSI lifecycle, snapshot controller, storage class governance)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.10 · OpenShift Storage Operator and ClusterCSIDriver Health (CSI lifecycle, snapshot controller, storage class governance)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the cluster machinery that hands out disks and keeps disk drivers healthy. When that machinery breaks, drifts from your catalog, or cannot attach snapshots cleanly, we raise a clear signal so teams fix the foundation before applications lose reliable storage.*

---

## Description

Detects OpenShift storage control-plane failures focused on the storage ClusterOperator, per-driver ClusterCSIDriver custom resources in operator.openshift.io/v1, CSINode registration gaps, stuck VolumeAttachment reconciliation, snapshot.storage.k8s.io VolumeSnapshot and VolumeSnapshotContent errors, VolumeSnapshotClass governance context, StorageClass parameter drift against catalog baselines for clouds such as AWS gp3, elevated CSI sidecar and controller restart counters, optional storage_operator and csi mstats when metrics indexes exist, and high-signal Kubernetes events including ProvisioningFailed, AttachVolumeFailed, FailedMount, and snapshot lifecycle reasons across openshift-cluster-csi-drivers, openshift-cluster-storage-operator, and openshift-storage.

## Value

Platform and storage teams shorten mean time to innocence when PVCs look healthy in dashboards yet cloud disks stop attaching: a Degraded ClusterCSIDriver or a flapping snapshot controller starves stateful workloads before binding analytics scream. Executives receive a consolidated ledger that ties ClusterOperator storage conditions, driver-level OperatorDegraded messages, VolumeAttachment age, snapshot errors, storage class governance, and CSI metrics into one searchable narrative that survives personnel rotations. Risk and engineering governance groups gain evidence that default StorageClass changes, CSI upgrades, and snapshot retention jobs leave audit trails rather than silent drift.

## Implementation

Land ocp_clusteroperator snapshots for the storage ClusterOperator, ocp_clustercsidriver and ocp_csinode exports, VolumeAttachment and snapshot.storage.k8s.io sourcetypes, ocp_storageclass baselines, correlated ocp_events and k8s_events for storage failure reasons, Prometheus CSI lines, and optional mstats on metrics indexes; normalize operator.openshift.io fields; save openshift_uc_3_3_10_storage_operator_csi_health every fifteen minutes over earliest=-6h@h; route page and warn via the Splunk OpenShift App; archive weekly evidence exports.

## Evidence

Saved search openshift_uc_3_3_10_storage_operator_csi_health with fifteen minute schedule; Splunk OpenShift App dashboard drilldowns on storage-plane sourcetypes; alert routing to platform storage on-call; weekly CSV exports archived to a restricted evidence index.

## Control test

### Positive scenario

In a lab OpenShift cluster, ingest ocp_clusteroperator rows where storage reports Degraded=True with snapshot controller messaging, matching ocp_clustercsidriver OperatorDegraded=True for a non-production driver, plus ocp_events citing AttachVolumeFailed; confirm openshift_uc_3_3_10_storage_operator_csi_health returns page or warn with non-null recommended_action within fifteen minutes.

### Negative scenario

After recovery when oc get clusteroperator storage shows Available=True without Degraded, oc get clustercsidriver shows OperatorAvailable=True for tested drivers, VolumeAttachment test fixtures clear, and events quiet, confirm severities return to info and the alert wrapper emits zero rows when filtering to page and warn only.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the OpenShift storage and infrastructure team that operates the cluster-storage-operator, the CSI driver operators shipped for AWS EBS, VMware vSphere, Azure Disk, Google Cloud persistent disk, Red Hat OpenShift Data Foundation, and any partner CSI installed through Operator Lifecycle Manager, plus the observability engineers who operate HTTP Event Collector tokens and OpenTelemetry Collector agents on management clusters. This use case isolates the storage control plane that sits upstream of PersistentVolumeClaim binding analytics: the storage ClusterOperator reconciles platform-owned operands such as the cluster-storage-operator deployment and the CSI snapshot controller machinery, while ClusterCSIDriver custom resources in the operator.openshift.io API group advertise per-driver lifecycle conditions including OperatorAvailable, OperatorProgressing, and OperatorDegraded that must align with healthy DaemonSets and controller Deployments in openshift-cluster-csi-drivers and related namespaces. Operand pods include node plugins such as aws-ebs-csi-driver-node or vmware-vsphere-csi-driver-node, controller stacks with external-attacher, external-provisioner, external-resizer, and snapshotter sidecars, and leader-elected control loops that show up in logs as lease acquire and release churn when etcd or API latency is poor.

Scope boundaries are explicit so reviewers do not duplicate sibling gold use cases. UC-3.3.6 remains the fleet-wide ClusterOperator ledger across kube-apiserver, dns, monitoring, authentication, and dozens of other operators without the storage-plane drill path this document prescribes; you still page UC-3.3.6 when multiple unrelated operators degrade together, while UC-3.3.10 answers whether the storage operator, snapshot controller, ClusterCSIDriver rows, CSI sidecars, and storage class governance caused or amplified the incident. UC-3.2.5 remains user-visible PersistentVolumeClaim binding delays and capacity class mismatches at the workload namespace; this use case explains driver-level failures that often precede those binding signals. UC-3.2.16 remains utilization inside already bound volumes; UC-3.2.25 remains capacity burn rate service levels; neither replaces attach-detach reconciliation, snapshot content errors, or storage class parameter drift. UC-3.3.13 remains image stream and integrated registry planes. UC-3.3.17 remains MachineConfigPool convergence and node configuration drift rather than kubelet CSI registration. Splunk becomes the tamper-resistant ledger that fuses periodic oc get clusteroperator storage exports, oc get clustercsidriver condition snapshots, VolumeAttachment age and phase signals, VolumeSnapshot and VolumeSnapshotContent errors from the snapshot.storage.k8s.io group, VolumeSnapshotClass governance rows, StorageClass parameter snapshots compared to your GitOps catalog, Kubernetes events with attach, mount, and provision failure reasons, audit JSON for storageclasses and clustercsidriver changes, and optional Prometheus lines such as storage_operator_cluster_csi_driver_degraded_count style series when your monitoring tier forwards them.

RBAC and safety: collectors that run oc get clusteroperator storage, oc get clustercsidriver, oc get csinode, oc get volumeattachment, oc get volumesnapshot across all namespaces, and oc get storageclass must use a dedicated ServiceAccount with cluster-scoped get and list on those resources, not long-lived kubeadmin credentials on administrator laptops. Run exporters from a hardened management host or CI worker with short-lived kubeconfigs. When you supplement with in-cluster Prometheus federation, bind read-only ServiceMonitor scrapes to a metrics forwarder identity rather than cluster-admin. Legal review should confirm node names, internal cloud volume identifiers, and storage backend hostnames appearing in condition messages are acceptable in Splunk; minimize requestObject bodies on audit feeds.

Index design: designate index=ocp_audit for Kubernetes API audit or equivalent OpenShift audit JSON with sourcetype=ocp_audit when you capture storageclasses, clustercsidriver, or volumeattachment mutations. Designate index=ocp_events for normalized object snapshots and Kubernetes events with sourcetypes such as ocp_clusteroperator, ocp_clustercsidriver, ocp_csinode, ocp_volumeattachment, ocp_volumesnapshot, ocp_volumesnapshotcontent, ocp_volumesnapshotclass, ocp_storageclass, ocp_events, and k8s_events depending on how your Splunk Add-on for Kubernetes and OpenShift exporters split feeds. Designate index=ocp_metrics for Prometheus exposition including csi_sidecar_, csi_operations_, storage_operator_, and kube_pod_container_status_restarts_total lines scraped from openshift-cluster-csi-drivers, openshift-cluster-storage-operator, and openshift-storage when present. Retention should cover at least fourteen days hot for attach-detach replay windows, thirty days for forensic review after CSI upgrades, and cold storage aligned to observability policy.

Field normalization: flatten metadata.name into driver or storage class names, map ClusterOperator storage conditions into available, progressing, and degraded friendly fields with parallel lastTransitionTime columns, map ClusterCSIDriver status conditions into operatorAvailable, operatorProgressing, and operatorDegraded equivalents your exporter emits, preserve VolumeAttachment metadata.creationTimestamp and status.attached style flags, flatten VolumeSnapshot status.error messages, and concatenate VolumeSnapshotContent errors when exporters fan out child events. StorageClass snapshots should retain parameters maps or JSON blobs for gp3 iops, throughput, encrypted, and kms key identifiers on AWS, plus comparable keys for other clouds. Cluster identity must appear on every event as cluster, openshift_cluster, or cluster_name.

Risk briefing: Progressing=True on the storage ClusterOperator is normal during z-stream upgrades, CSI driver rollouts, and snapshot controller bumps; alerts must measure dwell time and heartbeat age rather than paging on every short reconcile. Degraded=True on a ClusterCSIDriver for a single cloud often correlates with cloud API throttling or credential rotation rather than cluster-wide catastrophe; pair Splunk rows with provider status dashboards before executive escalation. VolumeSnapshotContentDeletionFailed events may appear during intentional namespace teardown storms; require correlation with stuck VolumeAttachment objects before treating as data loss. StorageClass parameter drift detections depend on an accurate GitOps baseline; a deliberate platform change to default encrypted volumes can look like drift until the catalog updates.

Collector posture: stamp change_ticket_id onto HTTP Event Collector payloads when maintenance touches StorageClass default annotations or ClusterCSIDriver managementState fields. When Splunk shows snapshotter errors but kubectl describe node reports healthy kubelet, suspect split-brain between control-plane and worker time skew or a partially upgraded CSI DaemonSet.

Differentiation recap: storage ClusterOperator plus ClusterCSIDriver deep conditions, CSI snapshot and VolumeAttachment lifecycle, CSI sidecar stability signals, and StorageClass governance, not generic ClusterOperator fleet tables alone, not PVC binding user experience alone, not filesystem fullness inside volumes, not image registry planes, not MachineConfigPool convergence.

### Step 2 — Configure data collection

Stand up six complementary lanes Splunk multisearch can fuse: structured snapshots for the storage ClusterOperator and ClusterCSIDriver objects, CSINode driver registration exports, VolumeAttachment and snapshot.storage.k8s.io resources plus high-signal Kubernetes events, Prometheus CSI and storage operator metrics, StorageClass parameter baselines, and optional audit narratives for storageclasses and clustercsidriver mutations.

ClusterOperator lane: schedule a utility every five minutes to run oc get clusteroperator storage -o json and emit sourcetype=ocp_clusteroperator events with metadata.name=storage, status.conditions expanded into parallel fields, generation and observedGeneration when present, and relatedObjects hints when your OpenShift minor includes them. Include a sha256 hash of canonical JSON without volatile resourceVersion when regulated customers require tamper evidence.

ClusterCSIDriver lane: run oc get clustercsidriver -o json on the same cadence or watch operator.openshift.io/v1 clustercsidriver objects, emitting sourcetype=ocp_clustercsidriver with one row per driver such as ebs.csi.aws.com, csi.vsphere.vmware.com, disk.csi.azure.com, pd.csi.storage.gke.io, openshift-storage.cephfs.csi.ceph.com, or partner-specific names installed through OLM. Flatten status.conditions types OperatorAvailable, OperatorProgressing, and OperatorDegraded with status, reason, message, and lastTransitionTime. Preserve spec.managementState when operators pause reconciliation during change freezes.

CSINode lane: run oc get csinode -o json and emit sourcetype=ocp_csinode with per-node flattened lists of drivers and allocatable counts when exporters provide them. This lane supports detection of kubelet-visible registration gaps after node reboots or incomplete DaemonSet rollouts.

Volume and snapshot lane: run oc get volumeattachment -o json, oc get volumesnapshot -A -o json, oc get volumesnapshotcontent -A -o json, and oc get volumesnapshotclass -o json on five- to ten-minute intervals depending on API load budgets. Emit sourcetype=ocp_volumeattachment, ocp_volumesnapshot, ocp_volumesnapshotcontent, and ocp_volumesnapshotclass respectively. Include involved UID cross references when VolumeSnapshot status boundVolumeSnapshotContentName is present. For high-churn clusters, consider watches with bounded buffering rather than full-cluster list storms.

Events lane: forward Kubernetes events into index=ocp_events with sourcetype=ocp_events or sourcetype=k8s_events using the Splunk Add-on for Kubernetes patterns or an OpenTelemetry Collector k8s_events receiver. Retain reason and message for ProvisioningFailed, AttachVolumeFailed, FailedMount, VolumeSnapshotCreated informational storms you still want for correlation, and VolumeSnapshotContentDeletionFailed failures. Namespace-filter events from openshift-cluster-csi-drivers, openshift-cluster-storage-operator, openshift-storage, and openshift CSI operator namespaces when volume requires.

Prometheus lane: federate kube-state-metrics style restart counters and CSI operation histograms from openshift-monitoring or user-workload monitoring as your governance model permits. Land lines in index=ocp_metrics with sourcetype=prometheus:metrics or sourcetype=prometheus:ocp. Preserve labels that identify daemonset, pod, container, and driver names. When remote write lands in a Splunk Metrics index, keep the mstats arm in the saved search to query storage_operator_cluster_csi_driver_degraded_count and csi_sidecar_operation_duration_seconds style metrics with fifteen minute spans; disable that arm when only event-indexed prometheus lines exist.

StorageClass lane: emit sourcetype=ocp_storageclass snapshots with parameters maps, provisioner strings, reclaimPolicy, volumeBindingMode, and annotations including storageclass.kubernetes.io/is-default-class. Store a GitOps-derived lookup openshift_storageclass_catalog.csv with columns cluster, storageclass, expected_encrypted, expected_iops, expected_throughput, and notes for gp3, encrypted disk, and regional defaults so SPL can join drift math without hard-coding every tenant class name.

Audit lane: ship Kubernetes API audit JSON for storageclasses and clustercsidriver objects at Metadata or RequestResponse depth consistent with volume policy. Capture verbs, user.username, objectRef.name, and responseStatus.code for default StorageClass swaps performed under change control.

Example oc helpers for design reviews:

```bash
oc get clusteroperator storage -o wide
oc get clustercsidriver -o custom-columns=NAME:.metadata.name,AVAILABLE:.status.conditions[?(@.type==\"OperatorAvailable\")].status,DEGRADED:.status.conditions[?(@.type==\"OperatorDegraded\")].status
oc get volumeattachment | head
oc get volumesnapshot,volumesnapshotcontent,volumesnapshotclass -A | head
oc -n openshift-cluster-csi-drivers get pods
```

props.conf guidance: TRUNCATE sufficiently large for JSON, TIMESTAMP_FIELDS respected when HTTP Event Collector time is authoritative, LINE_BREAKER rules for prometheus exposition when multiplexed with syslog headers, and FIELDALIAS maps for dotted versus flattened JSON paths.

Pre-save validation: index=ocp_events sourcetype=ocp_clusteroperator earliest=-1h must return the storage row after the first interval; ocp_clustercsidriver must list every driver your platform enables; ocp_events must show attach failures during intentional lab detach tests; prometheus lines must move when you restart a non-production CSI pod under vendor guidance.

Dashboards: the Splunk OpenShift App should host a matrix by cluster and entity_key with color thresholds from severity, drilldowns to raw JSON, event text, prometheus lines, and audit rows. Splunk ITSI users may bind KPIs to counts of page severity storage-plane rows per cluster and open episodes when two consecutive windows remain non-info for production entities.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_10_storage_operator_csi_health with a fifteen minute schedule during steady-state production, dispatch earliest=-6h@h, dispatch latest=now, and alert when severity is page or warn. Throttle duplicate cluster, entity_key rows for thirty minutes unless severity escalates from warn to page. Include recommended_action, coalesce_lane, and evt_reasons in pager descriptions so incident commanders open storage runbooks without re-running ad hoc searches.

Pipeline narrative: multisearch fans the storage ClusterOperator arm, per-driver ClusterCSIDriver arm, CSINode registration arm, VolumeAttachment and snapshot plus event arm, Prometheus CSI and restart arm, StorageClass governance arm, and optional mstats enrichment so a silent single sourcetype outage does not hide a genuine CSI degradation. coalesce() ladders absorb flattened versus dotted JSON field naming drift across exporters. streamstats measures short Progressing dwell on the storage ClusterOperator snapshot stream. eventstats adds cluster-level context such as counts of degraded storage-plane entities. case() maps ClusterOperator storage Degraded, ClusterCSIDriver Degraded, stuck VolumeAttachment ages, snapshot errors, high-impact Kubernetes event reasons, elevated CSI pod restart counters, StorageClass parameter drift hints, CSINode registration gaps, and mstats degraded hints into page versus warn versus info tiers. recommended_action encodes oc describe clusteroperator storage, oc describe clustercsidriver, oc describe volumeattachment, oc describe volumesnapshot, oc logs for csi-snapshot-controller, oc -n openshift-cluster-csi-drivers get pods, and GitOps diff steps without pretending Splunk replaces kubectl.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.10 OpenShift cluster-storage-operator + ClusterCSIDriver + snapshots + VolumeAttachment + StorageClass governance + CSI sidecar signals. Tunables: va_stuck_warn_min=25 va_stuck_page_min=45 prog_warn_min=45 earliest=-6h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=ocp_events OR index=ocp_metrics) sourcetype=ocp_clusteroperator earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval co_name=lower(trim(toString(coalesce(name, operator_name, metadata_name, co_name, ""))))
      | where co_name="storage"
      | eval av=lower(trim(toString(coalesce(available, conditions_available, available_status, ""))))
      | eval pr=lower(trim(toString(coalesce(progressing, conditions_progressing, progressing_status, ""))))
      | eval dg=lower(trim(toString(coalesce(degraded, conditions_degraded, degraded_status, ""))))
      | eval avail_f=if(match(av,"true|1"),1,0)
      | eval prog_f=if(match(pr,"true|1"),1,0)
      | eval deg_f=if(match(dg,"true|1"),1,0)
      | eval ltt_p=trim(toString(coalesce(ltt_progressing, last_transition_progressing, lastTransitionTime_progressing, "")))
      | eval ltt_epoch=if(len(ltt_p)>0 AND match(ltt_p,"^[0-9]{4}-"), strptime(ltt_p,"%Y-%m-%dT%H:%M:%SZ"), null())
      | eval cond_msg=substr(trim(toString(coalesce(message, reason, status_message, condition_message, co_message, ""))),1,420)
      | sort 0 + cluster - _time
      | streamstats window=2 current=t global=f last(_time) AS prev_ts last(prog_f) AS prev_prog BY cluster
      | eval prog_dwell_min=if(prog_f==1 AND prev_prog==1 AND isnotnull(prev_ts), round((_time-prev_ts)/60,2), if(prog_f==1, round((now()-_time)/60,2), 0))
      | eval lane="co_storage"
      | eval entity_key="cluster_operator_storage"
      | fields _time cluster lane entity_key avail_f prog_f deg_f cond_msg prog_dwell_min ltt_epoch ]
    [ search (index=ocp_audit OR index=ocp_events OR index=ocp_metrics) sourcetype=ocp_clustercsidriver earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval entity_key=lower(trim(toString(coalesce(name, metadata_name, driver, csi_driver, ""))))
      | eval oa=lower(trim(toString(coalesce(operatorAvailable, conditions_operatorAvailable, op_avail, ""))))
      | eval op=lower(trim(toString(coalesce(operatorProgressing, conditions_operatorProgressing, op_prog, ""))))
      | eval od=lower(trim(toString(coalesce(operatorDegraded, conditions_operatorDegraded, op_deg, ""))))
      | eval avail_f=if(match(oa,"true|1"),1,0)
      | eval prog_f=if(match(op,"true|1"),1,0)
      | eval deg_f=if(match(od,"true|1"),1,0)
      | eval cond_msg=substr(trim(toString(coalesce(message, reason, status_message, ""))),1,420)
      | eval ltt_epoch=null()
      | eval prog_dwell_min=0
      | eval lane="csi_crd"
      | stats max(_time) AS _time max(avail_f) AS avail_f max(prog_f) AS prog_f max(deg_f) AS deg_f values(cond_msg) AS cmv BY cluster lane entity_key
      | eval cond_msg=substr(trim(toString(mvindex(mvdedup(cmv),0))),1,420) ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_csinode earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval node=lower(trim(toString(coalesce(node, nodeName, metadata_name, name, ""))))
      | eval drivers=trim(toString(coalesce(drivers, driver_list, status_drivers, "")))
      | eval lane="csi_node"
      | eval entity_key=strcat("csinode_",node)
      | eval drv_cnt=if(len(drivers)>4, len(split(drivers,",")), if(len(drivers)>0,1,0))
      | eval deg_f=if(drv_cnt==0 OR len(drivers)==0,1,0)
      | eval avail_f=if(deg_f==0,1,0)
      | eval prog_f=0
      | eval cond_msg=if(deg_f==1,"csinode_driver_list_empty_or_unparsed","csinode_observed")
      | eval prog_dwell_min=0
      | eval ltt_epoch=null()
      | fields _time cluster lane entity_key avail_f prog_f deg_f cond_msg prog_dwell_min ltt_epoch ]
    [ search (index=ocp_audit OR index=ocp_events) (sourcetype=ocp_volumeattachment OR sourcetype=ocp_volumesnapshot OR sourcetype=ocp_volumesnapshotcontent OR sourcetype=ocp_volumesnapshotclass OR (sourcetype=ocp_events OR sourcetype=k8s_events)) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval lane="va_snap_evt"
      | eval entity_key=lower(trim(toString(coalesce(name, involvedObject_name, object_name, volumeattachment, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=lower(trim(toString(coalesce(message, Message, ""))))
      | eval attacher=lower(trim(toString(coalesce(attacher, ""))))
      | eval va_phase=lower(trim(toString(coalesce(phase, status_phase, ""))))
      | eval attached=lower(trim(toString(coalesce(attached, status_attached, ""))))
      | eval created=strptime(trim(toString(coalesce(creationTimestamp, metadata_creationTimestamp, firstTimestamp, ""))),"%Y-%m-%dT%H:%M:%SZ")
      | eval age_min=if(isnotnull(created) AND created>0, round((now()-created)/60,2), null())
      | eval va_stuck=if(sourcetype=~"ocp_volumeattachment" AND isnotnull(age_min) AND age_min>=45 AND (match(attached,"false|0") OR len(attached)==0),1,0)
      | eval snap_fail=if(sourcetype=~"ocp_volumesnapshot" AND (match(msg,"fail|error|timeout") OR match(reason,"Error|Failed")),1,0)
      | eval evt_storage=if((sourcetype=~"ocp_events" OR sourcetype=~"k8s_events") AND match(reason,"ProvisioningFailed|AttachVolumeFailed|FailedMount|VolumeSnapshotCreated|VolumeSnapshotContentDeletionFailed"),1,0)
      | eval deg_f=if(va_stuck==1 OR snap_fail==1 OR evt_storage==1,1,0)
      | eval avail_f=if(deg_f==0,1,0)
      | eval prog_f=0
      | eval cond_msg=substr(strcat(reason," ",msg),1,420)
      | eval prog_dwell_min=coalesce(age_min,0)
      | eval ltt_epoch=created
      | where len(entity_key)>0
      | stats max(_time) AS _time max(va_stuck) AS va_stuck max(snap_fail) AS snap_fail max(evt_storage) AS evt_storage max(deg_f) AS deg_f max(avail_f) AS avail_f max(prog_f) AS prog_f max(prog_dwell_min) AS prog_dwell_min first(attacher) AS va_attacher values(reason) AS evt_reasons first(cond_msg) AS cond_msg max(ltt_epoch) AS ltt_epoch BY cluster lane entity_key ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype=prometheus:ocp OR sourcetype="prometheus:openshift") earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where match(mn,"csi_sidecar_|csi_operations_|storage_operator_|kube_pod_container_status_restarts_total")
      | eval pod=lower(trim(toString(coalesce(pod, pod_name, ""))))
      | eval lane="csi_metrics"
      | eval entity_key=lower(trim(toString(coalesce(driver, daemonset, pod, mn, "csi_aggregate"))))
      | eval deg_f=if(match(mn,"kube_pod_container_status_restarts_total") AND mv>=8,1,0)
      | eval avail_f=if(deg_f==0,1,0)
      | eval prog_f=0
      | eval cond_msg=strcat(mn,"=",tostring(round(mv,4)))
      | eval prog_dwell_min=0
      | eval ltt_epoch=null()
      | stats max(_time) AS _time max(mv) AS met_peak max(deg_f) AS deg_f max(avail_f) AS avail_f max(prog_f) AS prog_f first(cond_msg) AS cond_msg max(prog_dwell_min) AS prog_dwell_min first(mn) AS prom_name BY cluster lane entity_key ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_storageclass earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval sc=lower(trim(toString(coalesce(name, metadata_name, storageclass, ""))))
      | eval params=lower(trim(toString(coalesce(parameters_json, parameters, provisioner_parameters, ""))))
      | eval lane="sc_gov"
      | eval entity_key=strcat("storageclass_",sc)
      | eval gp3_drift=if(match(sc,"gp3|ebs.csi.aws.com") AND !match(params,"encrypted") AND !match(_raw,"encrypted"),1,0)
      | eval gp3_iops_gap=if(match(sc,"gp3") AND !match(params,"iops") AND !match(_raw,"iops"),1,0)
      | eval deg_f=if(gp3_drift==1 OR gp3_iops_gap==1,1,0)
      | eval avail_f=if(deg_f==0,1,0)
      | eval prog_f=0
      | eval cond_msg=case(gp3_drift==1,"storageclass_unencrypted_or_param_gap", gp3_iops_gap==1,"gp3_missing_iops_hint", true(),"storageclass_snapshot_ok")
      | eval prog_dwell_min=0
      | eval ltt_epoch=null()
      | stats max(_time) AS _time max(deg_f) AS deg_f max(avail_f) AS avail_f max(prog_f) AS prog_f first(cond_msg) AS cond_msg max(prog_dwell_min) AS prog_dwell_min BY cluster lane entity_key ]
    [ | mstats latest(_value) AS mv WHERE index=ocp_metrics earliest=-6h@h latest=now span=15m BY cluster metric_name
      | eval cluster=lower(trim(toString(cluster)))
      | eval mn=lower(trim(toString(metric_name)))
      | where like(mn,"csi_%") OR like(mn,"storage_operator%")
      | eval lane="mstats_supp"
      | eval entity_key=strcat("metric_",mn)
      | eval met_peak=mv
      | eval deg_f=if(like(mn,"%degraded%") AND mv>0,1,0)
      | eval avail_f=if(deg_f==0,1,0)
      | eval prog_f=0
      | eval cond_msg=strcat(mn,"=",tostring(round(mv,6)))
      | eval prog_dwell_min=0
      | eval ltt_epoch=null()
      | eval prom_name=mn
      | eval va_stuck=0
      | eval snap_fail=0
      | eval evt_storage=0
      | fields _time cluster lane entity_key avail_f prog_f deg_f cond_msg prog_dwell_min ltt_epoch met_peak prom_name va_stuck snap_fail evt_storage ]
| eval entity_key=lower(trim(coalesce(entity_key,"unknown_entity")))
| stats max(_time) AS last_seen max(avail_f) AS avail_f max(prog_f) AS prog_f max(deg_f) AS deg_f max(prog_dwell_min) AS prog_dwell_min max(va_stuck) AS va_stuck max(snap_fail) AS snap_fail max(evt_storage) AS evt_storage values(lane) AS lanes first(cond_msg) AS cond_msg first(va_attacher) AS va_attacher first(evt_reasons) AS evt_reasons first(prom_name) AS prom_name max(met_peak) AS met_peak max(ltt_epoch) AS ltt_epoch BY cluster entity_key
| eval coalesce_lane=mvindex(mvdedup(lanes),0)
| eval heartbeat_age_h=if(isnotnull(ltt_epoch) AND ltt_epoch>0, round((now()-ltt_epoch)/3600,3), null())
| eventstats sum(deg_f) AS cluster_deg_cnt sum(eval(if(match(coalesce_lane,"co_storage|csi_crd"),1,0)*deg_f)) AS cluster_storage_deg_cnt BY cluster
| eval severity=case(
    match(entity_key,"cluster_operator_storage") AND deg_f==1, "page",
    match(coalesce_lane,"csi_crd") AND deg_f==1, "page",
    coalesce(va_stuck,0)>=1, "page",
    coalesce(snap_fail,0)>=1 AND match(cond_msg,"fail|error|timeout"), "warn",
    coalesce(evt_storage,0)>=1 AND match(cond_msg,"attachvolumefailed|failedmount|provisioningfailed"), "page",
    coalesce(evt_storage,0)>=1, "warn",
    match(coalesce_lane,"csi_metrics|mstats_supp") AND coalesce(met_peak,0)>=20, "page",
    match(coalesce_lane,"csi_metrics|mstats_supp") AND coalesce(met_peak,0)>=8, "warn",
    match(coalesce_lane,"sc_gov") AND deg_f==1, "warn",
    match(coalesce_lane,"csi_node") AND deg_f==1, "warn",
    prog_f==1 AND prog_dwell_min>=120, "page",
    prog_f==1 AND prog_dwell_min>=45, "warn",
    coalesce(heartbeat_age_h,0)>=8 AND prog_f==1, "warn",
    true(), "info")
| eval recommended_action=case(
    match(entity_key,"cluster_operator_storage") AND deg_f==1, "oc_describe_clusteroperator_storage_then_check_cluster_storage_operator_and_snapshot_controller_pods",
    match(coalesce_lane,"csi_crd") AND deg_f==1, "oc_describe_clustercsidriver_then_check_operand_daemonset_and_controller_in_openshift_cluster_csi_drivers",
    coalesce(va_stuck,0)>=1, "oc_describe_volumeattachment_and_correlate_with_csi_attacher_logs",
    coalesce(snap_fail,0)>=1, "oc_describe_volumesnapshot_and_snapshot_controller_logs",
    coalesce(evt_storage,0)>=1, "oc_get_events_storage_related_and_tail_csi_sidecar_logs",
    match(coalesce_lane,"csi_metrics|mstats_supp"), "correlate_prometheus_or_mstats_csi_lines_with_pod_restart_reasons",
    match(coalesce_lane,"sc_gov"), "diff_storageclass_against_gitops_catalog_and_audit_default_annotation_changes",
    match(coalesce_lane,"csi_node"), "oc_describe_csinode_and_verify_kubelet_driver_registration",
    true(), "refresh_storage_operator_and_csi_telemetry_lanes")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster entity_key coalesce_lane avail_f prog_f deg_f prog_dwell_min va_stuck snap_fail evt_storage met_peak prom_name cond_msg cluster_storage_deg_cnt cluster_deg_cnt severity recommended_action last_seen heartbeat_age_h va_attacher evt_reasons cluster_tier owner_team environment
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_10_storage_operator_csi_health_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -6h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-storage-platform@example.com
action.email.subject = OCP Storage CSI $result.severity$ $result.cluster$ $result.entity_key$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_10_storage_operator_csi_health | where severity IN ("page","warn")
```

Performance: if Job Inspector shows multisearch queue time above internal service level objectives, materialize ocp_clustercsidriver and ocp_clusteroperator storage snapshots hourly into a summary index keyed on cluster and entity_key, widen alert searches to earliest=-2h@h on the summary, and retain this full search for investigations. For clusters with very large VolumeAttachment counts, consider indexer-side filtering on exporter hosts to emit only non-attached or aged attachments.

### Step 4 — Validate

Ground truth always starts on-cluster. Run oc get clusteroperator storage -o wide and compare AVAILABLE, PROGRESSING, and DEGRADED columns to the Splunk row for the same cluster inside the last snapshot window. When statuses disagree, verify resourceVersion freshness, indexer clock skew, and duplicate cluster labels across regions before blaming parsers.

Deep dive with oc describe clusteroperator storage to read related objects, condition messages, and version entries. For each ClusterCSIDriver flagged Degraded in Splunk, run oc describe clustercsidriver name and compare to Splunk cond_msg text. Splunk should mirror transitions within one collection interval; if not, tighten scripted input frequency or fix kubeconfig expiration on the management host.

VolumeAttachment correlation: pick a Splunk row with high va_stuck hints, run oc describe volumeattachment on that name, and confirm age and attacher fields match exporter math. Pair with oc get pods -n openshift-cluster-csi-drivers to see whether attacher sidecars report leader election or RPC errors.

Snapshot correlation: for snap_fail hints, oc describe volumesnapshot and oc describe volumesnapshotcontent should explain snapshot controller or CSI snapshotter failures. Confirm VolumeSnapshotClass deletePolicy and secret references align with documentation for your driver.

Event correlation: run oc get events -n openshift-cluster-csi-drivers and openshift-cluster-storage-operator, then confirm Splunk evt_reasons capture the same ProvisioningFailed or AttachVolumeFailed text you see live.

Metrics cross-check: in the OpenShift console monitoring stack or via oc get --raw against Prometheus endpoints, validate CSI operation counters and kube pod restart series for the same pods Splunk indexes. When metrics disappear while API snapshots look healthy, suspect scrape misconfiguration or label collisions.

Synthetic validation: in a lab cluster under vendor guidance, induce a non-destructive CSI pod restart or snapshot error, confirm openshift_uc_3_3_10_storage_operator_csi_health returns warn or page with non-null recommended_action, then recover and confirm severity returns to info.

Negative test: on a healthy cluster after upgrades settle with storage Available, ClusterCSIDriver rows Available, no stuck VolumeAttachment test fixtures, and quiet events, confirm the alert wrapper returns zero rows for page and warn filters.

Runbook linkage: document expected Progressing windows during CSI migrations from in-tree to CSI for vSphere, Azure, and AWS so validators do not file false defects when change calendars show an approved migration.

### Step 5 — Operationalize & Troubleshoot

Case 1 — storage ClusterOperator Degraded with snapshot controller errors: inspect cluster-storage-operator and csi-snapshot-controller pods in openshift-cluster-storage-operator, review leader election logs, validate ValidatingWebhookConfiguration interactions if upgrades recently changed admission, and gather must-gather only after capturing Splunk timelines.

Case 2 — ClusterCSIDriver Degraded for ebs.csi.aws.com with node plugin CrashLoopBackOff: check AWS STS or IAM roles for the control plane and workers, verify regional endpoint reachability, and compare node IAM instance profiles with the openshift-cluster-csi-drivers service accounts.

Case 3 — vSphere CSI driver Degraded after vCenter certificate rotation: validate trust bundles mounted into CSI pods, confirm tagged datastore visibility, and reconcile CSI migration feature gates without duplicating generic compute alerts.

Case 4 — Azure Disk CSI Degraded during disk encryption set changes: confirm key vault permissions, disk encryption set regional pairing, and subscription quotas; pair with cloud audit narratives.

Case 5 — Stuck VolumeAttachment rows after force-deleted pods: identify terminating pods still holding volume handles, review finalizers, and coordinate with workload owners before forcibly deleting VolumeAttachment objects under break-glass policy.

Case 6 — VolumeSnapshotContentDeletionFailed during namespace cleanup: validate snapshot finalizers, VolumeSnapshotClass reclaim policies, and backend retention rules; avoid silent orphaning of cloud disks.

Case 7 — CSINode objects missing driver entries on newly scaled nodes: confirm DaemonSet rollouts reached the node, review kubelet logs for registration errors, and check for SELinux or mount namespace issues on the host.

Case 8 — CSI sidecar restart storms with OOMKilled reasons: increase sane memory limits under vendor guidance, verify API server latency, and check for excessive ListVolumes calls during controller churn.

Case 9 — Leader election churn across CSI controllers: inspect etcd and API health, network partitions between control-plane and workers, and clock skew; correlate with UC-3.3.6 only for platform-wide operator symptoms without merging narratives into this saved search.

Case 10 — StorageClass gp3 parameter drift without encryption flags: compare live StorageClass YAML to openshift_storageclass_catalog.csv, confirm whether drift matches a sanctioned FinOps change, and audit default StorageClass annotation mutations through ocp_audit.

Case 11 — False calm when exporter paused: if Splunk shows info severities but oc get clustercsidriver shows Degraded, restore collection jobs before trusting negative results.

Case 12 — Fleet-wide healthy storage plane: weekly spot-check Splunk rows against oc get clusteroperator storage and oc get clustercsidriver on every production cluster to confirm parsers, tokens, and cluster labels remain aligned.

Closing checklist: five em-dash step headers are present; Step 3 fenced SPL matches the spl field exactly; multisearch lists storage ClusterOperator, ClusterCSIDriver, CSINode, VolumeAttachment and snapshot event, Prometheus CSI, StorageClass, and mstats arms; coalesce, streamstats, eventstats, and case appear; closing table includes cluster, entity_key, coalesce_lane, avail_f, prog_f, deg_f, prog_dwell_min, va_stuck, snap_fail, evt_storage, met_peak, prom_name, cond_msg, cluster_storage_deg_cnt, cluster_deg_cnt, severity, recommended_action, last_seen, heartbeat_age_h, va_attacher, and evt_reasons for nineteen analyst-visible columns.

## SPL

```spl
`comment("UC-3.3.10 OpenShift cluster-storage-operator + ClusterCSIDriver + snapshots + VolumeAttachment + StorageClass governance + CSI sidecar signals. Tunables: va_stuck_warn_min=25 va_stuck_page_min=45 prog_warn_min=45 earliest=-6h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=ocp_events OR index=ocp_metrics) sourcetype=ocp_clusteroperator earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval co_name=lower(trim(toString(coalesce(name, operator_name, metadata_name, co_name, ""))))
      | where co_name="storage"
      | eval av=lower(trim(toString(coalesce(available, conditions_available, available_status, ""))))
      | eval pr=lower(trim(toString(coalesce(progressing, conditions_progressing, progressing_status, ""))))
      | eval dg=lower(trim(toString(coalesce(degraded, conditions_degraded, degraded_status, ""))))
      | eval avail_f=if(match(av,"true|1"),1,0)
      | eval prog_f=if(match(pr,"true|1"),1,0)
      | eval deg_f=if(match(dg,"true|1"),1,0)
      | eval ltt_p=trim(toString(coalesce(ltt_progressing, last_transition_progressing, lastTransitionTime_progressing, "")))
      | eval ltt_epoch=if(len(ltt_p)>0 AND match(ltt_p,"^[0-9]{4}-"), strptime(ltt_p,"%Y-%m-%dT%H:%M:%SZ"), null())
      | eval cond_msg=substr(trim(toString(coalesce(message, reason, status_message, condition_message, co_message, ""))),1,420)
      | sort 0 + cluster - _time
      | streamstats window=2 current=t global=f last(_time) AS prev_ts last(prog_f) AS prev_prog BY cluster
      | eval prog_dwell_min=if(prog_f==1 AND prev_prog==1 AND isnotnull(prev_ts), round((_time-prev_ts)/60,2), if(prog_f==1, round((now()-_time)/60,2), 0))
      | eval lane="co_storage"
      | eval entity_key="cluster_operator_storage"
      | fields _time cluster lane entity_key avail_f prog_f deg_f cond_msg prog_dwell_min ltt_epoch ]
    [ search (index=ocp_audit OR index=ocp_events OR index=ocp_metrics) sourcetype=ocp_clustercsidriver earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval entity_key=lower(trim(toString(coalesce(name, metadata_name, driver, csi_driver, ""))))
      | eval oa=lower(trim(toString(coalesce(operatorAvailable, conditions_operatorAvailable, op_avail, ""))))
      | eval op=lower(trim(toString(coalesce(operatorProgressing, conditions_operatorProgressing, op_prog, ""))))
      | eval od=lower(trim(toString(coalesce(operatorDegraded, conditions_operatorDegraded, op_deg, ""))))
      | eval avail_f=if(match(oa,"true|1"),1,0)
      | eval prog_f=if(match(op,"true|1"),1,0)
      | eval deg_f=if(match(od,"true|1"),1,0)
      | eval cond_msg=substr(trim(toString(coalesce(message, reason, status_message, ""))),1,420)
      | eval ltt_epoch=null()
      | eval prog_dwell_min=0
      | eval lane="csi_crd"
      | stats max(_time) AS _time max(avail_f) AS avail_f max(prog_f) AS prog_f max(deg_f) AS deg_f values(cond_msg) AS cmv BY cluster lane entity_key
      | eval cond_msg=substr(trim(toString(mvindex(mvdedup(cmv),0))),1,420) ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_csinode earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval node=lower(trim(toString(coalesce(node, nodeName, metadata_name, name, ""))))
      | eval drivers=trim(toString(coalesce(drivers, driver_list, status_drivers, "")))
      | eval lane="csi_node"
      | eval entity_key=strcat("csinode_",node)
      | eval drv_cnt=if(len(drivers)>4, len(split(drivers,",")), if(len(drivers)>0,1,0))
      | eval deg_f=if(drv_cnt==0 OR len(drivers)==0,1,0)
      | eval avail_f=if(deg_f==0,1,0)
      | eval prog_f=0
      | eval cond_msg=if(deg_f==1,"csinode_driver_list_empty_or_unparsed","csinode_observed")
      | eval prog_dwell_min=0
      | eval ltt_epoch=null()
      | fields _time cluster lane entity_key avail_f prog_f deg_f cond_msg prog_dwell_min ltt_epoch ]
    [ search (index=ocp_audit OR index=ocp_events) (sourcetype=ocp_volumeattachment OR sourcetype=ocp_volumesnapshot OR sourcetype=ocp_volumesnapshotcontent OR sourcetype=ocp_volumesnapshotclass OR (sourcetype=ocp_events OR sourcetype=k8s_events)) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval lane="va_snap_evt"
      | eval entity_key=lower(trim(toString(coalesce(name, involvedObject_name, object_name, volumeattachment, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=lower(trim(toString(coalesce(message, Message, ""))))
      | eval attacher=lower(trim(toString(coalesce(attacher, ""))))
      | eval va_phase=lower(trim(toString(coalesce(phase, status_phase, ""))))
      | eval attached=lower(trim(toString(coalesce(attached, status_attached, ""))))
      | eval created=strptime(trim(toString(coalesce(creationTimestamp, metadata_creationTimestamp, firstTimestamp, ""))),"%Y-%m-%dT%H:%M:%SZ")
      | eval age_min=if(isnotnull(created) AND created>0, round((now()-created)/60,2), null())
      | eval va_stuck=if(sourcetype=~"ocp_volumeattachment" AND isnotnull(age_min) AND age_min>=45 AND (match(attached,"false|0") OR len(attached)==0),1,0)
      | eval snap_fail=if(sourcetype=~"ocp_volumesnapshot" AND (match(msg,"fail|error|timeout") OR match(reason,"Error|Failed")),1,0)
      | eval evt_storage=if((sourcetype=~"ocp_events" OR sourcetype=~"k8s_events") AND match(reason,"ProvisioningFailed|AttachVolumeFailed|FailedMount|VolumeSnapshotCreated|VolumeSnapshotContentDeletionFailed"),1,0)
      | eval deg_f=if(va_stuck==1 OR snap_fail==1 OR evt_storage==1,1,0)
      | eval avail_f=if(deg_f==0,1,0)
      | eval prog_f=0
      | eval cond_msg=substr(strcat(reason," ",msg),1,420)
      | eval prog_dwell_min=coalesce(age_min,0)
      | eval ltt_epoch=created
      | where len(entity_key)>0
      | stats max(_time) AS _time max(va_stuck) AS va_stuck max(snap_fail) AS snap_fail max(evt_storage) AS evt_storage max(deg_f) AS deg_f max(avail_f) AS avail_f max(prog_f) AS prog_f max(prog_dwell_min) AS prog_dwell_min first(attacher) AS va_attacher values(reason) AS evt_reasons first(cond_msg) AS cond_msg max(ltt_epoch) AS ltt_epoch BY cluster lane entity_key ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype=prometheus:ocp OR sourcetype="prometheus:openshift") earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where match(mn,"csi_sidecar_|csi_operations_|storage_operator_|kube_pod_container_status_restarts_total")
      | eval pod=lower(trim(toString(coalesce(pod, pod_name, ""))))
      | eval lane="csi_metrics"
      | eval entity_key=lower(trim(toString(coalesce(driver, daemonset, pod, mn, "csi_aggregate"))))
      | eval deg_f=if(match(mn,"kube_pod_container_status_restarts_total") AND mv>=8,1,0)
      | eval avail_f=if(deg_f==0,1,0)
      | eval prog_f=0
      | eval cond_msg=strcat(mn,"=",tostring(round(mv,4)))
      | eval prog_dwell_min=0
      | eval ltt_epoch=null()
      | stats max(_time) AS _time max(mv) AS met_peak max(deg_f) AS deg_f max(avail_f) AS avail_f max(prog_f) AS prog_f first(cond_msg) AS cond_msg max(prog_dwell_min) AS prog_dwell_min first(mn) AS prom_name BY cluster lane entity_key ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_storageclass earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval sc=lower(trim(toString(coalesce(name, metadata_name, storageclass, ""))))
      | eval params=lower(trim(toString(coalesce(parameters_json, parameters, provisioner_parameters, ""))))
      | eval lane="sc_gov"
      | eval entity_key=strcat("storageclass_",sc)
      | eval gp3_drift=if(match(sc,"gp3|ebs.csi.aws.com") AND !match(params,"encrypted") AND !match(_raw,"encrypted"),1,0)
      | eval gp3_iops_gap=if(match(sc,"gp3") AND !match(params,"iops") AND !match(_raw,"iops"),1,0)
      | eval deg_f=if(gp3_drift==1 OR gp3_iops_gap==1,1,0)
      | eval avail_f=if(deg_f==0,1,0)
      | eval prog_f=0
      | eval cond_msg=case(gp3_drift==1,"storageclass_unencrypted_or_param_gap", gp3_iops_gap==1,"gp3_missing_iops_hint", true(),"storageclass_snapshot_ok")
      | eval prog_dwell_min=0
      | eval ltt_epoch=null()
      | stats max(_time) AS _time max(deg_f) AS deg_f max(avail_f) AS avail_f max(prog_f) AS prog_f first(cond_msg) AS cond_msg max(prog_dwell_min) AS prog_dwell_min BY cluster lane entity_key ]
    [ | mstats latest(_value) AS mv WHERE index=ocp_metrics earliest=-6h@h latest=now span=15m BY cluster metric_name
      | eval cluster=lower(trim(toString(cluster)))
      | eval mn=lower(trim(toString(metric_name)))
      | where like(mn,"csi_%") OR like(mn,"storage_operator%")
      | eval lane="mstats_supp"
      | eval entity_key=strcat("metric_",mn)
      | eval met_peak=mv
      | eval deg_f=if(like(mn,"%degraded%") AND mv>0,1,0)
      | eval avail_f=if(deg_f==0,1,0)
      | eval prog_f=0
      | eval cond_msg=strcat(mn,"=",tostring(round(mv,6)))
      | eval prog_dwell_min=0
      | eval ltt_epoch=null()
      | eval prom_name=mn
      | eval va_stuck=0
      | eval snap_fail=0
      | eval evt_storage=0
      | fields _time cluster lane entity_key avail_f prog_f deg_f cond_msg prog_dwell_min ltt_epoch met_peak prom_name va_stuck snap_fail evt_storage ]
| eval entity_key=lower(trim(coalesce(entity_key,"unknown_entity")))
| stats max(_time) AS last_seen max(avail_f) AS avail_f max(prog_f) AS prog_f max(deg_f) AS deg_f max(prog_dwell_min) AS prog_dwell_min max(va_stuck) AS va_stuck max(snap_fail) AS snap_fail max(evt_storage) AS evt_storage values(lane) AS lanes first(cond_msg) AS cond_msg first(va_attacher) AS va_attacher first(evt_reasons) AS evt_reasons first(prom_name) AS prom_name max(met_peak) AS met_peak max(ltt_epoch) AS ltt_epoch BY cluster entity_key
| eval coalesce_lane=mvindex(mvdedup(lanes),0)
| eval heartbeat_age_h=if(isnotnull(ltt_epoch) AND ltt_epoch>0, round((now()-ltt_epoch)/3600,3), null())
| eventstats sum(deg_f) AS cluster_deg_cnt sum(eval(if(match(coalesce_lane,"co_storage|csi_crd"),1,0)*deg_f)) AS cluster_storage_deg_cnt BY cluster
| eval severity=case(
    match(entity_key,"cluster_operator_storage") AND deg_f==1, "page",
    match(coalesce_lane,"csi_crd") AND deg_f==1, "page",
    coalesce(va_stuck,0)>=1, "page",
    coalesce(snap_fail,0)>=1 AND match(cond_msg,"fail|error|timeout"), "warn",
    coalesce(evt_storage,0)>=1 AND match(cond_msg,"attachvolumefailed|failedmount|provisioningfailed"), "page",
    coalesce(evt_storage,0)>=1, "warn",
    match(coalesce_lane,"csi_metrics|mstats_supp") AND coalesce(met_peak,0)>=20, "page",
    match(coalesce_lane,"csi_metrics|mstats_supp") AND coalesce(met_peak,0)>=8, "warn",
    match(coalesce_lane,"sc_gov") AND deg_f==1, "warn",
    match(coalesce_lane,"csi_node") AND deg_f==1, "warn",
    prog_f==1 AND prog_dwell_min>=120, "page",
    prog_f==1 AND prog_dwell_min>=45, "warn",
    coalesce(heartbeat_age_h,0)>=8 AND prog_f==1, "warn",
    true(), "info")
| eval recommended_action=case(
    match(entity_key,"cluster_operator_storage") AND deg_f==1, "oc_describe_clusteroperator_storage_then_check_cluster_storage_operator_and_snapshot_controller_pods",
    match(coalesce_lane,"csi_crd") AND deg_f==1, "oc_describe_clustercsidriver_then_check_operand_daemonset_and_controller_in_openshift_cluster_csi_drivers",
    coalesce(va_stuck,0)>=1, "oc_describe_volumeattachment_and_correlate_with_csi_attacher_logs",
    coalesce(snap_fail,0)>=1, "oc_describe_volumesnapshot_and_snapshot_controller_logs",
    coalesce(evt_storage,0)>=1, "oc_get_events_storage_related_and_tail_csi_sidecar_logs",
    match(coalesce_lane,"csi_metrics|mstats_supp"), "correlate_prometheus_or_mstats_csi_lines_with_pod_restart_reasons",
    match(coalesce_lane,"sc_gov"), "diff_storageclass_against_gitops_catalog_and_audit_default_annotation_changes",
    match(coalesce_lane,"csi_node"), "oc_describe_csinode_and_verify_kubelet_driver_registration",
    true(), "refresh_storage_operator_and_csi_telemetry_lanes")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster entity_key coalesce_lane avail_f prog_f deg_f prog_dwell_min va_stuck snap_fail evt_storage met_peak prom_name cond_msg cluster_storage_deg_cnt cluster_deg_cnt severity recommended_action last_seen heartbeat_age_h va_attacher evt_reasons cluster_tier owner_team environment
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Inventory.vendor_product) AS vendor_product latest(Inventory.version) AS inv_version FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
| rename Inventory.dest AS inv_dest
| join type=left max=0 inv_dest
    [| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-24h@h latest=now BY Application_State.dest
     | rename Application_State.dest AS inv_dest ]
| where like(lower(vendor_product), "%openshift%") OR like(lower(app_info), "%csi%") OR like(lower(app_info), "%storage%")
| table inv_dest vendor_product inv_version app_state app_info
```

## Visualization

Severity-colored table by cluster and entity_key with drilldowns to raw ocp_clusteroperator storage rows, ocp_clustercsidriver JSON, VolumeAttachment and snapshot objects, ocp_storageclass parameters, ocp_events text, prometheus and mstats metric lines, and optional ocp_audit rows; single-value tiles for cluster_storage_deg_cnt; timeline of prog_dwell_min for the storage ClusterOperator.

## Known False Positives

Vendor-managed CSI operator upgrades during approved change windows routinely flip OperatorProgressing=True on ClusterCSIDriver rows and restart node DaemonSets; require dwell thresholds and change_ticket_id correlation before paging application teams. Intentional default StorageClass annotation moves during platform refresh look like governance drift in naive comparisons until GitOps baselines and audit verbs confirm the actor and ticket. Scheduled snapshot garbage collection jobs can emit VolumeSnapshotContentDeletionFailed bursts that are benign when namespaces are purged under automation; pair with VolumeAttachment age and cloud disk inventory before treating as corruption. Rolling node drains produce intentional VolumeAttachment churn and AttachVolumeFailed events that clear after kubelet finishes detaching; suppress when maintenance metadata is present. In-tree to CSI migration windows for vSphere, Azure, and AWS inflate Progressing time on both storage ClusterOperator and driver-specific ClusterCSIDriver resources; consult OpenShift release notes for expected duration. Lab clusters that constantly recycle StorageClasses for pipeline tests will trigger sc_gov hints unless non-production indexes or lookups downgrade severity. Prometheus scrape gaps or Splunk Metrics index misconfiguration can empty the mstats_supp arm while API snapshots remain healthy; repair federation before muting metrics entirely. CSINode exporter parsers that flatten driver lists differently may appear as empty driver strings; validate FIELDALIAS rules quarterly to avoid false registration gaps. Duplicate HTTP Event Collector submissions from redundant forwarders can double entity rows until dedupe logic lands in summary indexes. EBS gp3 classes without explicit iops in parameters may still be valid when defaults satisfy finance policy; tune gp3_iops_gap logic against openshift_storageclass_catalog.csv rather than raw heuristics alone.

## References

- [OpenShift Documentation — Storage overview](https://docs.openshift.com/container-platform/latest/storage/storage-overview.html)
- [OpenShift Documentation — Understanding persistent storage](https://docs.openshift.com/container-platform/latest/storage/understanding-persistent-storage.html)
- [OpenShift Documentation — Configuring CSI volumes](https://docs.openshift.com/container-platform/latest/storage/container_storage_interface/persistent-storage-csi.html)
- [OpenShift Documentation — VMware vSphere CSI Driver Operator](https://docs.openshift.com/container-platform/latest/storage/container_storage_interface/persistent-storage-csi-vsphere.html)
- [OpenShift Documentation — AWS Elastic Block Store CSI Driver Operator](https://docs.openshift.com/container-platform/latest/storage/container_storage_interface/persistent-storage-csi-aws-ebs.html)
- [OpenShift Documentation — Expanding persistent volumes](https://docs.openshift.com/container-platform/latest/storage/expanding-persistent-volumes.html)
- [OpenShift Documentation — CSI volume snapshots](https://docs.openshift.com/container-platform/latest/storage/container_storage_interface/persistent-storage-csi-snapshots.html)
- [Red Hat Blog — CIFS and OpenShift using the Container Storage Interface](https://www.redhat.com/en/blog/cifs-and-openshift-using-the-container-storage-interface-1)
