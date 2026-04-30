<!-- AUTO-GENERATED from UC-3.3.13.json — DO NOT EDIT -->

---
id: "3.3.13"
title: "OpenShift ImageStream Import Failures and Internal Registry Operator Health"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.13 · OpenShift ImageStream Import Failures and Internal Registry Operator Health

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the cluster service that copies container images from outside vendors into our own library and keeps them fresh on a schedule. When that copying breaks or our internal image warehouse gets sick, we raise a clear signal so teams fix it before releases stall.*

---

## Description

Monitors the OpenShift-only image lifecycle plane formed by ImageStream, ImageStreamTag, and ImageStreamImport APIs in group image.openshift.io/v1 together with the cluster image-registry operator that materializes the integrated registry Service and storage backend. The analytic detects failed oc import-image and scheduled import reconciles, tag condition rows stuck on ImportFailed, lastUpdated staleness beyond expected scheduled intervals, ImageChange trigger starvation that blocks downstream DeploymentConfig rollouts, operator-level Degraded or Progressing drift on the image-registry ClusterOperator custom resource family, pruner CronJob silence that risks storage fill, registry Deployment pod restart bursts, PVC pressure and object-storage backend error hints, and pull-through failures against the internal registry hostname.

## Value

Platform teams lose weeks when base-layer tags silently stop refreshing: application rollouts appear healthy in generic workload dashboards while ImageStream tags never advance, mirrors desynchronize from vendor registries, and the integrated registry fills because pruning jobs stopped. Consolidated telemetry ties API-shaped import conditions to operator health, pruner cadence, and registry pod stability so leaders shorten mean time to innocence without confusing kubelet pull symptoms with upstream import pipeline faults. Risk and engineering governance gain a tamper-evident ledger that shows stewardship of Red Hat and third-party image supply paths distinct from vanilla Kubernetes image pull backoff analytics.

## Implementation

Land ocp_imagestream, ocp_imagestreamimport, ocp_imagestreamtag, ocp_imageregistry, k8s_events, and optional ocp_metrics prometheus lines into ocp_audit and ocp_events with consistent cluster labels; normalize import condition and operator condition fields in props; save openshift_uc_3_3_13_imagestream_registry_health every fifteen minutes over earliest=-6h@h; route page and warn severities to platform on-call; archive weekly CSV exports with exporter commit hashes for registry governance reviews.

## Evidence

Saved search openshift_uc_3_3_13_imagestream_registry_health with fifteen minute schedule; Splunk OpenShift App dashboard drilldowns on ocp_imagestream, ocp_imagestreamimport, ocp_imagestreamtag, ocp_imageregistry, k8s_events, and prometheus metric lines; alert routing to platform on-call; weekly CSV exports archived to a restricted evidence index.

## Control test

### Positive scenario

In a lab OpenShift project, ingest ocp_imagestream or ocp_imagestreamimport rows showing ImportFailed or Unauthorized codes after a controlled oc import-image against an invalid upstream tag, add matching k8s_events with reason ImageStreamImportFailed, execute openshift_uc_3_3_13_imagestream_registry_health, and confirm page or warn severity with non-null recommended_action within fifteen minutes.

### Negative scenario

After recovery when oc describe imagestreamtag shows healthy import conditions, configs.imageregistry.operator.openshift.io reports Available without Degraded, pruner jobs succeed, and registry pod restarts stay low, confirm severities return to info and the alert wrapper emits zero rows when filtering to page and warn only.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the OpenShift platform engineering lead accountable for the integrated registry and image.openshift.io APIs, the cluster lifecycle team that operates image-registry.operator.openshift.io and openshift-image-registry, and the observability engineers who steward Splunk HTTP Event Collector tokens plus management-cluster collectors that export API state. This use case isolates the OpenShift image abstraction layer that does not exist in vanilla Kubernetes: ImageStream objects declare tags that may reference external registries such as registry.redhat.io, quay.io, or docker.io, while controllers reconcile ImageStreamImport requests and scheduled import policies to populate status.tags entries with digest-resolved image metadata. ImageStreamTag objects expose per-tag history with lastUpdated timestamps and generation counters that ImageChange triggers on DeploymentConfig and BuildConfig consumers watch. Failures surface as ImportFailed conditions, ImageStreamImport status codes including Unauthorized, Forbidden, ManifestNotFound, and BadGateway, and event reasons such as ImageStreamImportFailed. The image-registry operator publishes cluster-scoped configuration and ClusterOperator-style condition semantics for Available, Progressing, and Degraded that explain storage backend choice across emptyDir, PVC, and cloud object buckets, route exposure choices, and pruner integration.

Scope boundaries are explicit. UC-3.2.14 remains kubelet-side ImagePullBackOff and ErrImagePull waiting reasons on Pods together with kubelet pull_image error counters, not the platform import controller ledger that populates ImageStream tags from upstream registries. UC-3.3.7 remains build.openshift.io Build and BuildConfig failures including PushImageToRegistryFailed after cluster builders assemble layers; this UC covers the consumer-facing scheduled import and tag resolution path that feeds those builds and triggers. UC-3.3.16 remains apps.openshift.io DeploymentConfig rollout progression, ReplicationController overlap, and hook semantics; ImageChange triggers there depend on ImageStreamTag bumps that never arrive when this UC signals upstream resolution failure, so investigators should open UC-3.3.16 only after confirming import health or explicitly tracking rollout stalls as a dependent symptom. UC-3.3.11 remains operators.coreos.com Subscription, InstallPlan, and ClusterServiceVersion reconcile health for add-on operators, not the integrated registry operand or image stream import plane. UC-3.3.6 remains broad ClusterOperator reconciliation for all platform operators including image-registry as one row among many; this UC deep-dives image-registry messages, storage backends, pruner CronJobs, and tag-level import conditions without replacing fleet-wide ClusterOperator dashboards.

RBAC and safety: exporters that run oc get imagestream -A -o json, oc get imagestreamimport -A -o json, oc get imagestreamtag -A -o json, or watches on image.openshift.io must use dedicated ServiceAccounts with get list watch on those resources, not personal cluster-admin kubeconfig files on laptops. Collectors that read image-registry.operator.openshift.io configuration need get list on configs.imageregistry.operator.openshift.io and cluster-scoped image registry custom resources per your OpenShift minor. Run jobs from hardened management hosts with short-lived credentials. Legal and privacy reviews should confirm dockerImageRepository hostnames, pull secrets referenced only by indirect identifiers, and upstream image names are acceptable in the analytics tier; redact authentication tokens from any raw message fields at ingest.

Index design: designate index=ocp_events for structured object snapshots and Kubernetes-style events, and index=ocp_audit when you dual-write API watches or audit JSON for administrative verbs on imagestreams and imagestreamimports. Designate index=ocp_metrics for prometheus:metrics lines federated from in-cluster monitoring that expose image_registry_operator_* series and imagestreams_imported_total when your platform version publishes them, plus kube_pod_container_status_restarts_total filtered to openshift-image-registry. Retention should cover at least fourteen days hot for incident replay on import storms, thirty days for quarterly supply-chain governance reviews, and cold storage aligned to enterprise logging policy.

Field normalization expectations: flatten ImageStream metadata.namespace and metadata.name into namespace and is_name, expand status.tags[].tag into tag_name, map conditions[].type ImportSuccess or ImportFailed into import_cond_type and conditions[].status into import_cond_status, preserve conditions[].message into import_cond_msg, and parse lastTransitionTime or lastUpdated into import_cond_epoch when exporters flatten JSON. For ImageStreamImport rows, flatten metadata.namespace, metadata.name, status.importStatus.images[].status.reason into isi_reason, status.importStatus.images[].status.message into isi_msg, and map digest-level failures into isi_fail_flag. For ImageStreamTag rows, flatten tag name, generation, image.dockerImageReference into docker_ref, scheduled import policy hints into scheduled_flag numeric, and lastUpdated into ist_last_epoch. For image-registry operator snapshots, flatten Available Progressing Degraded booleans or status strings into reg_avail_flag reg_prog_flag reg_deg_flag with paired messages reg_msg, and flatten storage.managementState or storage.pvc and storage.s3 bucket fields into storage_profile text. Cluster identity must appear on every event as cluster, openshift_cluster, or cluster_name.

Risk briefing: scheduled imports legitimately pause in disconnected estates during mirror maintenance; alerts must compare drift multiples against expected mirror cadence rather than treating every aged lastUpdated as an outage. One-shot tags created with oc tag or oc import-image without scheduled policy may never refresh; tune staleness logic using scheduled_flag. Registry operator Progressing=True is normal during storage migrations or certificate rotations; pair with dwell thresholds. Pull-through cache misses can spike when upstream registries rate-limit anonymous pulls; combine with vendor status pages before executive escalation. Integrated registry pods may restart during node drains; require sustained restart rates or correlated Degraded operator messages before paging leadership.

Differentiation recap: image.openshift.io import and tag resolution plus image-registry.operator.openshift.io health, not kubelet pull backoff alone, not Build assemble failures alone, not DeploymentConfig rollout mechanics alone, not OLM CSV health alone.

Operational posture: stamp change_ticket_id onto HTTP Event Collector payloads when maintenance touches ImageContentSourcePolicy, oc mirror automation, or registry storage secrets. When Splunk shows ImportFailed but oc describe cites transient upstream maintenance, annotate lookups to suppress short windows tied to vendor communications. Correlate enterprise firewall change records with BadGateway rows before blaming cluster misconfiguration.

### Step 2 — Configure data collection

Stand up five complementary lanes Splunk multisearch can fuse: ImageStream and ImageStreamImport structured snapshots for import conditions and digest-level failures, ImageStreamTag snapshots for staleness versus scheduled policy, image-registry operator configuration and condition snapshots, Kubernetes events and audit context for ImageStreamImportFailed PullImageError Unauthorized reasons plus pruner CronJob lifecycle, and Prometheus metrics for image_registry_operator_* counters, imagestreams_imported_total, registry pod restarts, and optional registry HTTP error rate series.

ImageStream and ImageStreamImport snapshot lane: schedule a Python or Go utility every two to five minutes from a management host. The utility should run oc get imagestream -A -o json and oc get imagestreamimport -A -o json, iterate items[], flatten tag conditions and import status arrays, and emit sourcetype=ocp_imagestream and sourcetype=ocp_imagestreamimport events with cluster, namespace, is_name, tag_name, import fields, and failure flags. Include resourceVersion or generation when you compute staleness deltas. Hash canonical JSON without volatile resourceVersion when tamper-evident auditing is required.

ImageStreamTag snapshot lane: on the same cadence run oc get imagestreamtag -A -o json or watch imagestream.image.openshift.io ImageStreamTag objects. Emit sourcetype=ocp_imagestreamtag with namespace, ist_name combining stream and tag, docker_ref, scheduled_flag, ist_last_epoch, and generation counters. Compute scheduled_interval_hint seconds in the exporter when spec.tag.importPolicy.scheduled is true and interval strings are present so Splunk can compare drift multiples without fragile rex at search time.

Image-registry operator lane: run oc get configs.imageregistry.operator.openshift.io cluster -o json or your documented equivalent for the cluster ImageRegistry custom resource, flatten status.conditions and spec.storage stanzas, and emit sourcetype=ocp_imageregistry with reg_avail_flag reg_prog_flag reg_deg_flag reg_msg storage_profile managementState replicas readOnly flags when available. Include route host fields when non-default external exposure is configured.

Events and pruner lane: forward Kubernetes events into index=ocp_events with sourcetype=k8s_events or sourcetype=ocp_events using Splunk OpenShift App patterns or an OpenTelemetry Collector k8s_events receiver. Retain involvedObject.kind involvedObject.name involvedObject.namespace reason message firstTimestamp lastTimestamp count type and cluster. Ensure ImageStreamImportFailed PullImageError Unauthorized Forbidden reasons are not filtered out at the forwarder. Add a targeted collector search for CronJob and Job objects in openshift-image-registry or namespaces your platform team uses for oc adm prune automation, emitting events or object snapshots when image-pruner jobs fail or skip runs.

Prometheus lane: federate in-cluster monitoring targets that expose image_registry_operator_* and imagestreams_imported_total metrics as documented for your OpenShift minor, plus kube_pod_container_status_restarts_total limited to namespace openshift-image-registry and deployments named cluster-image-registry or equivalent. Land lines in index=ocp_metrics with sourcetype=prometheus:metrics. Preserve namespace pod container labels for restart joins.

Audit lane: ship Kubernetes API audit JSON into index=ocp_audit with sourcetype=ocp_audit. Extract objectRef.apiGroup image.openshift.io, objectRef.resource imagestreams imagestreamimports imagestreamtags, verbs create update patch delete, user.username for actors issuing oc import-image or oc tag, and responseStatus.code for admission denials. Truncate large requestObject bodies while retaining object names.

Example oc verification operators run during design reviews:

oc get imagestream -n openshift -o wide
oc describe imagestreamtag ruby:25 -n openshift
oc get imagestreamimport -n app-ns
oc get configs.imageregistry.operator.openshift.io cluster -o yaml
oc get cronjob -n openshift-image-registry
oc get pods -n openshift-image-registry

props.conf guidance: TRUNCATE sufficiently large for JSON bodies, TIMESTAMP_FIELDS respected when event time is authoritative, LINE_BREAKER rules for NDJSON watch streams, FIELDALIAS maps from status.tags.tag to tag_name when flatteners differ.

Pre-save validation: index=ocp_events sourcetype=ocp_imagestream earliest=-1h must return events after the first interval; ocp_imagestreamimport ocp_imagestreamtag ocp_imageregistry arms should appear; k8s_events should show import failures during controlled oc import-image tests against invalid tags; ocp_metrics should include image_registry_operator or imagestreams_imported_total lines when your cluster exposes them.

Dashboards: Splunk OpenShift App panels should host a matrix by cluster and namespace with color thresholds from severity, drilldowns to raw JSON for each sourcetype, event text, prometheus lines, and audit rows.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_13_imagestream_registry_health with a fifteen minute schedule, dispatch earliest=-6h@h, dispatch latest=now, and alert when severity is page or warn. Throttle duplicate cluster namespace is_key rows for thirty minutes unless severity escalates from warn to page. Include recommended_action, import_hint, and reg_deg_flag in pager descriptions so incident commanders open the correct runbook section without rerunning ad hoc searches.

Pipeline narrative for operators: multisearch fans ImageStream and ImageStreamImport failure arms, ImageStreamTag staleness arms, image-registry operator condition arms, pruner and registry event arms, and prometheus operator and pod restart arms so a silent single sourcetype outage does not hide genuine import or storage failures. coalesce() absorbs field naming drift between exporters. streamstats ordered by is_key measures short-term repeated ImportFailed streaks. eventstats adds cluster-level context such as counts of degraded registry operator rows and ninetieth percentile staleness hours. case() maps ImportFailed and upstream error codes, staleness beyond multiples of scheduled hints, registry Degraded or Available false flags, pruner job failures, and elevated registry pod restarts into page warn or info tiers. recommended_action encodes concise verbs referencing oc import-image, oc describe imagestreamtag, oc get configs.imageregistry.operator.openshift.io, oc logs deployment cluster-image-registry, PVC or object storage checks, and mirror sync jobs without pretending search replaces those commands.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("Anchor: (index=ocp_audit OR index=ocp_events) sourcetype=ocp_imagestream OR sourcetype=ocp_imagestreamimport OR sourcetype=ocp_imagestreamtag OR sourcetype=ocp_imageregistry OR sourcetype=k8s_events reason=ImageStreamImportFailed OR reason=PullImageError OR reason=Unauthorized. Supplements: index=ocp_metrics image_registry_operator_* imagestreams_imported_total. UC-3.3.13 Tunables: stale_mult=3 pruner_fail_window_m=360 earliest=-6h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=ocp_events) (sourcetype=ocp_imagestream OR sourcetype=ocp_imagestreamimport) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, object_namespace, ""))))
      | eval is_name=lower(trim(toString(coalesce(is_name, imagestream, metadata_name, name, object_name, ""))))
      | eval tag_name=lower(trim(toString(coalesce(tag_name, tag, ist_tag, ""))))
      | eval isi_reason=lower(trim(toString(coalesce(isi_reason, failure_reason, status_reason, reason, ""))))
      | eval cond_t=lower(trim(toString(coalesce(import_cond_type, condition_type, cond_type, type, ""))))
      | eval cond_s=lower(trim(toString(coalesce(import_cond_status, condition_status, cond_status, status, ""))))
      | eval import_fail=if(match(cond_t,"importfailed") AND match(cond_s,"true|1"),1,if(match(cond_t,"importsuccess") AND match(cond_s,"false|0"),1,if(match(isi_reason,"unauthorized|forbidden|manifestnotfound|badgateway|imageimportfailed"),1,0)))
      | eval import_msg=trim(toString(coalesce(import_cond_msg, isi_msg, message, status_message, "")))
      | eval lane="is_import"
      | eval is_key=lower(trim(if(len(tag_name)>0, namespace+"/"+is_name+":"+tag_name, namespace+"/"+is_name)))
      | stats latest(_time) AS last_imp_t max(import_fail) AS import_fail_any latest(import_msg) AS import_msg latest(isi_reason) AS isi_reason values(tag_name) AS tags_seen BY cluster namespace is_key lane ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_imagestreamtag earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, ""))))
      | eval ist_name=lower(trim(toString(coalesce(ist_name, name, metadata_name, tag_fqn, ""))))
      | eval ist_last_epoch=tonumber(tostring(coalesce(ist_last_epoch, lastUpdated_epoch, tag_last_updated_epoch, "")),10)
      | eval sched_hint_sec=tonumber(tostring(coalesce(scheduled_interval_sec, import_interval_sec, sched_sec, "")),10)
      | eval scheduled_flag=tonumber(tostring(coalesce(scheduled_flag, tag_scheduled, "0")),10)
      | eval lane="ist_stale"
      | eval is_name=mvindex(split(ist_name, ":"),0)
      | eval tag_name=mvindex(split(ist_name, ":"),1)
      | eval is_key=lower(trim(coalesce(namespace+"/"+mvindex(split(ist_name, ":"),0)+":"+mvindex(split(ist_name, ":"),1), namespace+"/"+ist_name, "")))
      | eval stale_sec=if(isnotnull(ist_last_epoch) AND ist_last_epoch>0, now()-ist_last_epoch, null())
      | eval stale_mult=if(scheduled_flag==1 AND isnotnull(sched_hint_sec) AND sched_hint_sec>0 AND isnotnull(stale_sec), round(stale_sec/sched_hint_sec,3), null())
      | stats latest(_time) AS last_ist_t max(stale_sec) AS stale_sec_max max(stale_mult) AS stale_mult_max max(scheduled_flag) AS scheduled_any BY cluster namespace ist_name lane ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_imageregistry earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, "cluster"))))
      | eval reg_deg_flag=if(match(lower(toString(coalesce(reg_deg_flag, degraded_status, conditions_degraded, ""))),"true|1"),1,if(match(lower(reg_msg),"degrad|fail|unavailable"),1,0))
      | eval reg_avail_flag=if(match(lower(toString(coalesce(reg_avail_flag, available_status, conditions_available, ""))),"false|0"),1,0)
      | eval reg_prog_flag=if(match(lower(toString(coalesce(reg_prog_flag, progressing_status, conditions_progressing, ""))),"true|1"),1,0)
      | eval reg_msg=trim(toString(coalesce(reg_msg, message, status_message, operator_message, "")))
      | eval storage_profile=lower(trim(toString(coalesce(storage_profile, storage_backend, mgmt_state, ""))))
      | eval lane="reg_op"
      | eval is_key=namespace+"/imageregistry/cluster"
      | stats latest(_time) AS last_reg_t max(reg_deg_flag) AS reg_deg_flag max(reg_avail_flag) AS reg_avail_bad max(reg_prog_flag) AS reg_prog_flag latest(reg_msg) AS reg_msg latest(storage_profile) AS storage_profile BY cluster namespace lane ]
    [ search (index=ocp_audit OR index=ocp_events) (sourcetype=k8s_events OR sourcetype=ocp_events) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(involvedObject_namespace, involved_namespace, object_namespace, namespace, ""))))
      | eval kind=lower(trim(toString(coalesce(involvedObject_kind, involved_kind, object_kind, ""))))
      | eval obj=lower(trim(toString(coalesce(involvedObject_name, involved_name, object_name, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, event_reason, "")))
      | eval msg=lower(trim(toString(coalesce(message, Message, event_message, ""))))
      | eval pruner_hit=if(match(obj,"image-pruner|prune") OR match(msg,"image-pruner|prune|adm prune"),1,0)
      | eval import_evt=if(match(reason,"ImageStreamImportFailed|PullImageError|Unauthorized|Forbidden") OR match(msg,"imagestreamimportfailed|manifestnotfound|badgateway|unauthorized|forbidden|pullimageerror"),1,0)
      | where import_evt==1 OR pruner_hit==1 OR match(kind,"imagestream|imagestreamimport")
      | eval lane=if(pruner_hit==1,"pruner_evt","is_evt")
      | eval is_key=lower(trim(coalesce(namespace+"/"+obj, namespace+"/event/"+reason, "")))
      | stats latest(_time) AS last_evt_t latest(reason) AS evt_reason latest(msg) AS evt_msg max(pruner_hit) AS pruner_hit max(import_evt) AS import_evt BY cluster namespace is_key lane ]
    [ search index=ocp_metrics sourcetype=prometheus:metrics earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")),10)
      | eval pod=lower(trim(toString(coalesce(pod, pod_name, ""))))
      | eval ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | where match(mn,"image_registry_operator_|imagestreams_imported_total") OR (match(met_name,"kube_pod_container_status_restarts_total") AND match(ns,"openshift-image-registry"))
      | eval lane="reg_metrics"
      | eval is_key=lower(trim(coalesce(ns+"/metrics/"+mn, "cluster/metrics/"+mn, "")))
      | stats latest(_time) AS last_met_t sum(mv) AS met_sum latest(mn) AS met_name BY cluster is_key lane ]
| eval is_key=lower(trim(coalesce(is_key, "unknown_resource")))
| stats max(last_imp_t) AS last_imp_t max(import_fail_any) AS import_fail_any first(import_msg) AS import_msg first(isi_reason) AS isi_reason values(tags_seen) AS tags_seen max(last_ist_t) AS last_ist_t max(stale_sec_max) AS stale_sec_max max(stale_mult_max) AS stale_mult_max max(scheduled_any) AS scheduled_any max(last_reg_t) AS last_reg_t max(reg_deg_flag) AS reg_deg_flag max(reg_avail_bad) AS reg_avail_bad max(reg_prog_flag) AS reg_prog_flag first(reg_msg) AS reg_msg first(storage_profile) AS storage_profile max(last_evt_t) AS last_evt_t first(evt_reason) AS evt_reason first(evt_msg) AS evt_msg max(pruner_hit) AS pruner_hit max(import_evt) AS import_evt max(last_met_t) AS last_met_t max(met_sum) AS met_sum first(met_name) AS met_name BY cluster namespace is_key
| sort cluster namespace is_key
| streamstats window=3 current=t global=f last(import_fail_any) AS prev_imp_fail BY cluster namespace is_key
| eval imp_streak=if(import_fail_any==1 AND prev_imp_fail==1,1,import_fail_any)
| eventstats sum(reg_deg_flag) AS cluster_reg_deg_cnt sum(import_fail_any) AS cluster_imp_fail_cnt BY cluster
| eventstats perc90(stale_sec_max) AS fleet_stale_p90 BY cluster
| eval import_hint=if(import_fail_any==1 OR match(lower(coalesce(import_msg,evt_msg,"")),"unauthorized|forbidden|manifestnotfound|badgateway|imageimportfailed"),1,0)
| eval severity=case(
    reg_avail_bad==1 OR reg_deg_flag==1, "page",
    import_hint==1 AND imp_streak==1, "page",
    import_hint==1, "warn",
    scheduled_any==1 AND coalesce(stale_mult_max,0)>=3, "warn",
    scheduled_any==1 AND isnotnull(stale_sec_max) AND stale_sec_max>=86400 AND coalesce(fleet_stale_p90,0)>=3600, "warn",
    pruner_hit==1 AND match(lower(evt_msg),"fail|error|backoff"), "warn",
    match(met_name,"kube_pod_container_status_restarts_total") AND coalesce(met_sum,0)>=8, "warn",
    cluster_reg_deg_cnt>=1 AND cluster_imp_fail_cnt>=3, "warn",
    true(), "info")
| eval recommended_action=case(
    reg_deg_flag==1 OR reg_avail_bad==1, "oc_describe_imageregistry_operator_check_storage_and_routes",
    import_hint==1 AND match(lower(coalesce(import_msg,evt_msg,"")),"unauthorized|forbidden"), "validate_pull_secrets_icsp_and_registry_credentials_then_retry_import",
    import_hint==1 AND match(lower(coalesce(import_msg,evt_msg,"")),"manifestnotfound|badgateway"), "verify_upstream_tag_paths_mirrors_and_proxy_egress",
    scheduled_any==1 AND coalesce(stale_mult_max,0)>=3, "oc_import_image_or_review_imagestreamtag_schedule_and_mirror_sync",
    pruner_hit==1, "review_oc_adm_prune_cronjob_logs_and_registry_disk_budget",
    match(met_name,"kube_pod_container_status_restarts_total"), "oc_logs_image_registry_deployment_and_check_pvc_or_object_backend",
    true(), "correlate_imagestream_conditions_with_registry_operator_status")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster namespace is_key import_fail_any import_hint imp_streak stale_sec_max stale_mult_max reg_deg_flag reg_avail_bad reg_prog_flag storage_profile evt_reason pruner_hit met_name met_sum fleet_stale_p90 severity recommended_action last_imp_t cluster_tier owner_team environment
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_13_imagestream_registry_health_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -6h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-platform@example.com
action.email.subject = OCP ImageStream registry plane $result.severity$ $result.cluster$ $result.namespace$ $result.is_key$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_13_imagestream_registry_health | where severity IN ("page","warn")
```

Performance: if Job Inspector shows multisearch queue time above internal service levels, materialize hourly ocp_imagestreamtag summaries keyed on cluster, namespace, and ist_name into a summary index, widen alert searches to earliest=-2h@h on the summary, and retain this full search for investigations.

### Step 4 — Validate

Ground truth always starts on-cluster. Run oc get imagestream -n target-namespace, oc describe imagestreamtag stream:tag -n target-namespace, and oc get imagestreamimport -n target-namespace after a controlled oc import-image, then compare failure codes and messages to Splunk rows inside the last snapshot window. When statuses disagree, verify resourceVersion freshness, indexer clock skew, and duplicate cluster labels across regions before blaming parsers.

Registry operator truth: oc get configs.imageregistry.operator.openshift.io cluster -o yaml should mirror reg_avail_flag reg_deg_flag and storage_profile text in ocp_imageregistry events. Splunk should reflect condition transitions within one collection interval; if not, tighten scripted input frequency or fix kubeconfig expiration on the management host.

Pruner truth: oc get cronjob -n openshift-image-registry and oc get jobs -n openshift-image-registry should show recent successful completions when pruner_hit is zero in Splunk; absence of jobs across governance windows while disk metrics climb warrants storage investigation.

Prometheus cross-check: in the OpenShift console monitoring stack or via oc get --raw against metrics routes, validate imagestreams_imported_total increments during healthy imports and image_registry_operator_* series align with operator messages. When metrics disappear while API snapshots show ImportFailed, repair federation before muting the analytic.

Synthetic validation: in a lab namespace, run oc import-image against an intentionally invalid tag on a public repository under change control, ingest telemetry, and confirm openshift_uc_3_3_13_imagestream_registry_health surfaces warn or page with non-null recommended_action. Restore a valid tag, wait for ImportSuccess conditions, and confirm severity returns to info.

Negative test: on a cluster where scheduled imports succeed, registry operator conditions report Available without Degraded, pruner jobs complete, and registry pods show low restart counts, confirm the alert wrapper returns zero rows for page and warn filters after maintenance windows settle.

Audit cross-check: replay controlled oc import-image and oc tag commands, then confirm ocp_audit rows include verbs and actors without indexing sensitive credential material beyond policy.

### Step 5 — Operationalize & Troubleshoot

Case 1 — ImportFailed with Unauthorized against registry.redhat.io: validate global pull secret, ImageContentSourcePolicy mirrors, and HTTP proxy rules; retry oc import-image after secret rotation under change control.

Case 2 — BadGateway spikes during corporate egress maintenance: pair Splunk rows with firewall tickets and upstream registry status pages before deep cluster surgery.

Case 3 — ManifestNotFound after vendor retires a tag: update ImageStream spec tags to supported references, communicate S2I builder image deprecation announcements to developer champions, and refresh mirrors before application rebuilds stall.

Case 4 — Scheduled tag staleness with intentional scheduled false: confirm one-shot tags and suppress staleness logic for namespaces tagged static_import in lookups.

Case 5 — image-registry operator Degraded with PVC full: expand PVC or reclaim space via pruner jobs only after reviewing oc adm prune images safety constraints and backups.

Case 6 — object storage backend S3 5xx bursts: engage cloud storage teams, validate bucket IAM and endpoint health, and correlate with registry pod logs.

Case 7 — cluster-image-registry Deployment restart storm: inspect node pressure, SELinux or SCC denials, and certificate rotation narratives in operator messages.

Case 8 — image-pruner CronJob suspended during change freeze: document intentional suppression metadata on HTTP Event Collector events to avoid false storage incidents while disk budgets are watched manually.

Case 9 — Pull-through cache miss presenting as internal registry 503: validate Service openshift-image-registry endpoints and route health, then confirm upstream registry reachability from cluster egress.

Case 10 — ImageChange triggers stuck on DeploymentConfig with flat ImageStreamTag generation: pivot to UC-3.3.16 for rollout mechanics only after this UC confirms imports succeed; otherwise fix import pipeline first.

Case 11 — Fleet-wide info severities only: weekly spot-check Splunk rows against oc get imagestream -A on every production cluster to confirm parsers, tokens, and RBAC remain aligned.

Closing checklist: multisearch lists import, tag staleness, registry operator, event pruner, and metrics arms; coalesce normalizes cluster fields; streamstats flags repeated import failures; eventstats adds fleet staleness context; case maps severity; closing table includes cluster, namespace, is_key, import_fail_any, import_hint, imp_streak, stale_sec_max, stale_mult_max, reg_deg_flag, reg_avail_bad, reg_prog_flag, storage_profile, evt_reason, pruner_hit, met_name, met_sum, fleet_stale_p90, severity, recommended_action, and last_imp_t for twenty analyst-visible columns.


## SPL

```spl
`comment("Anchor: (index=ocp_audit OR index=ocp_events) sourcetype=ocp_imagestream OR sourcetype=ocp_imagestreamimport OR sourcetype=ocp_imagestreamtag OR sourcetype=ocp_imageregistry OR sourcetype=k8s_events reason=ImageStreamImportFailed OR reason=PullImageError OR reason=Unauthorized. Supplements: index=ocp_metrics image_registry_operator_* imagestreams_imported_total. UC-3.3.13 Tunables: stale_mult=3 pruner_fail_window_m=360 earliest=-6h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=ocp_events) (sourcetype=ocp_imagestream OR sourcetype=ocp_imagestreamimport) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, object_namespace, ""))))
      | eval is_name=lower(trim(toString(coalesce(is_name, imagestream, metadata_name, name, object_name, ""))))
      | eval tag_name=lower(trim(toString(coalesce(tag_name, tag, ist_tag, ""))))
      | eval isi_reason=lower(trim(toString(coalesce(isi_reason, failure_reason, status_reason, reason, ""))))
      | eval cond_t=lower(trim(toString(coalesce(import_cond_type, condition_type, cond_type, type, ""))))
      | eval cond_s=lower(trim(toString(coalesce(import_cond_status, condition_status, cond_status, status, ""))))
      | eval import_fail=if(match(cond_t,"importfailed") AND match(cond_s,"true|1"),1,if(match(cond_t,"importsuccess") AND match(cond_s,"false|0"),1,if(match(isi_reason,"unauthorized|forbidden|manifestnotfound|badgateway|imageimportfailed"),1,0)))
      | eval import_msg=trim(toString(coalesce(import_cond_msg, isi_msg, message, status_message, "")))
      | eval lane="is_import"
      | eval is_key=lower(trim(if(len(tag_name)>0, namespace+"/"+is_name+":"+tag_name, namespace+"/"+is_name)))
      | stats latest(_time) AS last_imp_t max(import_fail) AS import_fail_any latest(import_msg) AS import_msg latest(isi_reason) AS isi_reason values(tag_name) AS tags_seen BY cluster namespace is_key lane ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_imagestreamtag earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, ""))))
      | eval ist_name=lower(trim(toString(coalesce(ist_name, name, metadata_name, tag_fqn, ""))))
      | eval ist_last_epoch=tonumber(tostring(coalesce(ist_last_epoch, lastUpdated_epoch, tag_last_updated_epoch, "")),10)
      | eval sched_hint_sec=tonumber(tostring(coalesce(scheduled_interval_sec, import_interval_sec, sched_sec, "")),10)
      | eval scheduled_flag=tonumber(tostring(coalesce(scheduled_flag, tag_scheduled, "0")),10)
      | eval lane="ist_stale"
      | eval is_name=mvindex(split(ist_name, ":"),0)
      | eval tag_name=mvindex(split(ist_name, ":"),1)
      | eval is_key=lower(trim(coalesce(namespace+"/"+mvindex(split(ist_name, ":"),0)+":"+mvindex(split(ist_name, ":"),1), namespace+"/"+ist_name, "")))
      | eval stale_sec=if(isnotnull(ist_last_epoch) AND ist_last_epoch>0, now()-ist_last_epoch, null())
      | eval stale_mult=if(scheduled_flag==1 AND isnotnull(sched_hint_sec) AND sched_hint_sec>0 AND isnotnull(stale_sec), round(stale_sec/sched_hint_sec,3), null())
      | stats latest(_time) AS last_ist_t max(stale_sec) AS stale_sec_max max(stale_mult) AS stale_mult_max max(scheduled_flag) AS scheduled_any BY cluster namespace ist_name lane ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_imageregistry earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, "cluster"))))
      | eval reg_deg_flag=if(match(lower(toString(coalesce(reg_deg_flag, degraded_status, conditions_degraded, ""))),"true|1"),1,if(match(lower(reg_msg),"degrad|fail|unavailable"),1,0))
      | eval reg_avail_flag=if(match(lower(toString(coalesce(reg_avail_flag, available_status, conditions_available, ""))),"false|0"),1,0)
      | eval reg_prog_flag=if(match(lower(toString(coalesce(reg_prog_flag, progressing_status, conditions_progressing, ""))),"true|1"),1,0)
      | eval reg_msg=trim(toString(coalesce(reg_msg, message, status_message, operator_message, "")))
      | eval storage_profile=lower(trim(toString(coalesce(storage_profile, storage_backend, mgmt_state, ""))))
      | eval lane="reg_op"
      | eval is_key=namespace+"/imageregistry/cluster"
      | stats latest(_time) AS last_reg_t max(reg_deg_flag) AS reg_deg_flag max(reg_avail_flag) AS reg_avail_bad max(reg_prog_flag) AS reg_prog_flag latest(reg_msg) AS reg_msg latest(storage_profile) AS storage_profile BY cluster namespace lane ]
    [ search (index=ocp_audit OR index=ocp_events) (sourcetype=k8s_events OR sourcetype=ocp_events) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(involvedObject_namespace, involved_namespace, object_namespace, namespace, ""))))
      | eval kind=lower(trim(toString(coalesce(involvedObject_kind, involved_kind, object_kind, ""))))
      | eval obj=lower(trim(toString(coalesce(involvedObject_name, involved_name, object_name, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, event_reason, "")))
      | eval msg=lower(trim(toString(coalesce(message, Message, event_message, ""))))
      | eval pruner_hit=if(match(obj,"image-pruner|prune") OR match(msg,"image-pruner|prune|adm prune"),1,0)
      | eval import_evt=if(match(reason,"ImageStreamImportFailed|PullImageError|Unauthorized|Forbidden") OR match(msg,"imagestreamimportfailed|manifestnotfound|badgateway|unauthorized|forbidden|pullimageerror"),1,0)
      | where import_evt==1 OR pruner_hit==1 OR match(kind,"imagestream|imagestreamimport")
      | eval lane=if(pruner_hit==1,"pruner_evt","is_evt")
      | eval is_key=lower(trim(coalesce(namespace+"/"+obj, namespace+"/event/"+reason, "")))
      | stats latest(_time) AS last_evt_t latest(reason) AS evt_reason latest(msg) AS evt_msg max(pruner_hit) AS pruner_hit max(import_evt) AS import_evt BY cluster namespace is_key lane ]
    [ search index=ocp_metrics sourcetype=prometheus:metrics earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")),10)
      | eval pod=lower(trim(toString(coalesce(pod, pod_name, ""))))
      | eval ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | where match(mn,"image_registry_operator_|imagestreams_imported_total") OR (match(met_name,"kube_pod_container_status_restarts_total") AND match(ns,"openshift-image-registry"))
      | eval lane="reg_metrics"
      | eval is_key=lower(trim(coalesce(ns+"/metrics/"+mn, "cluster/metrics/"+mn, "")))
      | stats latest(_time) AS last_met_t sum(mv) AS met_sum latest(mn) AS met_name BY cluster is_key lane ]
| eval is_key=lower(trim(coalesce(is_key, "unknown_resource")))
| stats max(last_imp_t) AS last_imp_t max(import_fail_any) AS import_fail_any first(import_msg) AS import_msg first(isi_reason) AS isi_reason values(tags_seen) AS tags_seen max(last_ist_t) AS last_ist_t max(stale_sec_max) AS stale_sec_max max(stale_mult_max) AS stale_mult_max max(scheduled_any) AS scheduled_any max(last_reg_t) AS last_reg_t max(reg_deg_flag) AS reg_deg_flag max(reg_avail_bad) AS reg_avail_bad max(reg_prog_flag) AS reg_prog_flag first(reg_msg) AS reg_msg first(storage_profile) AS storage_profile max(last_evt_t) AS last_evt_t first(evt_reason) AS evt_reason first(evt_msg) AS evt_msg max(pruner_hit) AS pruner_hit max(import_evt) AS import_evt max(last_met_t) AS last_met_t max(met_sum) AS met_sum first(met_name) AS met_name BY cluster namespace is_key
| sort cluster namespace is_key
| streamstats window=3 current=t global=f last(import_fail_any) AS prev_imp_fail BY cluster namespace is_key
| eval imp_streak=if(import_fail_any==1 AND prev_imp_fail==1,1,import_fail_any)
| eventstats sum(reg_deg_flag) AS cluster_reg_deg_cnt sum(import_fail_any) AS cluster_imp_fail_cnt BY cluster
| eventstats perc90(stale_sec_max) AS fleet_stale_p90 BY cluster
| eval import_hint=if(import_fail_any==1 OR match(lower(coalesce(import_msg,evt_msg,"")),"unauthorized|forbidden|manifestnotfound|badgateway|imageimportfailed"),1,0)
| eval severity=case(
    reg_avail_bad==1 OR reg_deg_flag==1, "page",
    import_hint==1 AND imp_streak==1, "page",
    import_hint==1, "warn",
    scheduled_any==1 AND coalesce(stale_mult_max,0)>=3, "warn",
    scheduled_any==1 AND isnotnull(stale_sec_max) AND stale_sec_max>=86400 AND coalesce(fleet_stale_p90,0)>=3600, "warn",
    pruner_hit==1 AND match(lower(evt_msg),"fail|error|backoff"), "warn",
    match(met_name,"kube_pod_container_status_restarts_total") AND coalesce(met_sum,0)>=8, "warn",
    cluster_reg_deg_cnt>=1 AND cluster_imp_fail_cnt>=3, "warn",
    true(), "info")
| eval recommended_action=case(
    reg_deg_flag==1 OR reg_avail_bad==1, "oc_describe_imageregistry_operator_check_storage_and_routes",
    import_hint==1 AND match(lower(coalesce(import_msg,evt_msg,"")),"unauthorized|forbidden"), "validate_pull_secrets_icsp_and_registry_credentials_then_retry_import",
    import_hint==1 AND match(lower(coalesce(import_msg,evt_msg,"")),"manifestnotfound|badgateway"), "verify_upstream_tag_paths_mirrors_and_proxy_egress",
    scheduled_any==1 AND coalesce(stale_mult_max,0)>=3, "oc_import_image_or_review_imagestreamtag_schedule_and_mirror_sync",
    pruner_hit==1, "review_oc_adm_prune_cronjob_logs_and_registry_disk_budget",
    match(met_name,"kube_pod_container_status_restarts_total"), "oc_logs_image_registry_deployment_and_check_pvc_or_object_backend",
    true(), "correlate_imagestream_conditions_with_registry_operator_status")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster namespace is_key import_fail_any import_hint imp_streak stale_sec_max stale_mult_max reg_deg_flag reg_avail_bad reg_prog_flag storage_profile evt_reason pruner_hit met_name met_sum fleet_stale_p90 severity recommended_action last_imp_t cluster_tier owner_team environment
```

## CIM SPL

```spl
| tstats summariesonly=true latest(Inventory.vendor_product) AS vendor_product latest(Inventory.version) AS inv_version FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
| rename Inventory.dest AS inv_dest
| join type=left max=0 inv_dest
    [| tstats summariesonly=true latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-24h@h latest=now BY Application_State.dest
     | rename Application_State.dest AS inv_dest ]
| where like(lower(vendor_product), "%openshift%") OR like(lower(app_info), "%image%registry%") OR like(lower(app_info), "%imagestream%")
| table inv_dest vendor_product inv_version app_state app_info
```

## Visualization

Severity-colored table by cluster, namespace, and is_key with drilldowns to ocp_imagestream, ocp_imagestreamimport, ocp_imagestreamtag, ocp_imageregistry JSON, k8s_events text, and prometheus metric lines; single-value tiles for cluster_imp_fail_cnt; timeline of stale_sec_max versus scheduled hints; matrix of storage_profile by cluster.

## Known False Positives

Public registries such as docker.io and quay.io apply rate limits to anonymous pulls; bursts of Unauthorized or throttling messages during cold-start mornings can mirror incidents until authenticated pull secrets or mirror caches absorb traffic. Disconnected clusters run intentional mirror sync windows where ImageStream tags age until the next oc mirror job completes; require drift multiples beyond documented sync cadence before paging platform leadership. Teams that set spec.tag.importPolicy.scheduled false for one-shot promotion tags should never expect periodic refresh; staleness detectors must read scheduled_flag from exporters or suppress namespaces in a lookup table. Change-freeze periods sometimes suspend image-pruner CronJobs to avoid destructive pruning during holiday moratoriums; pair absent pruner rows with disk capacity dashboards and explicit freeze metadata before treating silence as failure. Vendor registry maintenance windows published on status pages can align with BadGateway spikes that self-resolve; annotate maintenance_authorized fields on HTTP Event Collector events when network teams pre-approve the window. S2I builder ImageStream deprecation announcements may cause intentional ManifestNotFound rows until application teams retag; route those pages to developer relations workflows rather than overnight platform bridges. Clusters that expose the integrated registry through alternative routes can leave status.dockerImageRepository empty in some snapshots while remains healthy; corroborate with oc get route and configs.imageregistry.operator.openshift.io before assuming import misconfiguration. Lab namespaces that continuously import intentionally broken tags for pipeline tests will generate warn noise unless routed to non-production indexes. Duplicate HTTP Event Collector submissions from redundant exporters can double met_sum restart counters until dedupe logic lands in summary indexes. Prometheus metric renames between OpenShift minors can hide image_registry_operator series for one rotation; fall back to ocp_imageregistry snapshots when metrics cardinality shifts.

## References

- [OpenShift Documentation — Managing images overview](https://docs.openshift.com/container-platform/latest/openshift_images/managing-images/managing-images-overview.html)
- [OpenShift Documentation — Managing image streams](https://docs.openshift.com/container-platform/latest/openshift_images/image-streams-manage.html)
- [OpenShift Documentation — Registry options](https://docs.openshift.com/container-platform/latest/registry/registry-options.html)
- [OpenShift Documentation — Configuring the registry for OpenShift on a public cloud](https://docs.openshift.com/container-platform/latest/registry/configuring-registry-operator.html)
- [OpenShift Documentation — Triggering updates on ImageStream changes](https://docs.openshift.com/container-platform/latest/openshift_images/triggering-updates-on-imagestream-changes.html)
- [OpenShift Documentation — Managing CLI plugins](https://docs.openshift.com/container-platform/latest/cli_reference/openshift_cli/managing-cli-plugins.html)
- [Red Hat Blog — Mirroring OpenShift registries the easy way](https://cloud.redhat.com/blog/mirroring-openshift-registries-the-easy-way)
