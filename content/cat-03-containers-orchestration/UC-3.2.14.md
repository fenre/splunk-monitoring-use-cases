<!-- AUTO-GENERATED from UC-3.2.14.json — DO NOT EDIT -->

---
id: "3.2.14"
title: "Kubernetes ImagePullBackOff Detection"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.14 · Kubernetes ImagePullBackOff Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*Before any app on our Kubernetes clusters can run, the cluster must download its container image. When that download fails—a bad name, expired login, or blocked connection—the app never starts. We watch every download error so we can fix it before customers notice.*

---

## Description

Unique monitoring axis: kubelet-orchestrated image pull failures that leave pods in Waiting with reasons ImagePullBackOff or ErrImagePull, correlated with kubelet pull_image error counters, Failed API events whose messages start with Failed to pull image, optional CRI log lines, short-window registry hostname storm counts, and namespace-level imagePullSecret inventory joins. This is the supply-chain stop that blocks rolling updates before application code runs, distinct from CrashLoopBackOff in UC-3.2.10 after pulls succeed, distinct from Docker daemon pull telemetry in UC-3.1.26, and distinct from init or probe-focused siblings.

## Value

Mean time to repair improves when responders see cluster, namespace, pod, container, resolved image reference, derived registry hostname, dwell minutes in ImagePullBackOff-class states, event error text, owning workload, paging team, kubelet pull error counters on the node, and a registry storm rollup in one row instead of correlating kubectl describe, metrics UI, and registry dashboards by hand. Customer impact drops because deploy freezes from bad digests, expired tokens, blocked egress, or exhausted registry budgets surface with severity tied to environment tier and sustained dwell time. Finance gains evidence for authenticated registry spend when anonymous Hub limits explain incident timelines. Audit and platform governance teams reference timestamped exports alongside Kubernetes documentation links for images, private pulls, and imagePullSecrets.

## Implementation

Ingest kube-state-metrics and kubelet Prometheus scrapes into k8s_metrics, ship Kubernetes events and optional CRI logs into k8s, forward audit JSON into k8s_audit, publish k8s_namespace_tier.csv, k8s_workload_routing.csv, and image_pull_secret_inventory.csv, save uc_3_2_14_kube_imagepull_backoff every five minutes with earliest=-4h@m, route critical and high severities per savedsearches.conf, and validate with kubectl run using a nonexistent image in a lab namespace.

## Evidence

Saved search uc_3_2_14_kube_imagepull_backoff; lookups k8s_namespace_tier.csv, k8s_workload_routing.csv, and image_pull_secret_inventory.csv with version hashes; weekly CSV export of alert rows to a restricted evidence index; dashboard panels tied to the closing table and registry storm time series.

## Control test

### Positive scenario

In namespace qa-ipb run kubectl run ipb-lab --image=this-image-does-not-exist:v1 --restart=Always, wait for kube-state-metrics to expose waiting_reason ErrImagePull or ImagePullBackOff, execute uc_3_2_14_kube_imagepull_backoff, and expect a qualifying row with growing time_in_ipb_min and severity at least high when workload_tier indicates production in the tier lookup.

### Negative scenario

Run nginx:stable with a valid pull secret and healthy registry path in the same namespace; confirm waiting_reason never stays in ImagePullBackOff class beyond one scrape interval and the saved search yields no qualifying row for that pod across thirty minutes.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the Kubernetes platform site reliability team, the artifact registry operators, and the observability engineers who operate Splunk OpenTelemetry Collector DaemonSets plus cluster receivers across production and pre-production. This use case isolates the kubelet image-pull pipeline: pods whose containers never start because the kubelet cannot fetch the OCI image referenced by the Pod spec. UC-3.2.10 documents CrashLoopBackOff where the image already exists locally and the main container exits repeatedly; waiting reasons and restart counters there are post-pull. UC-3.1.26 documents Docker Engine journal and registry-egress telemetry on Linux workers before Kubernetes adoption or on hosts that run dockerd directly. UC-3.2.14 stays on kube-state-metrics kube_pod_container_status_waiting_reason for ImagePullBackOff and ErrImagePull, kubelet metric kubelet_runtime_operations_errors_total filtered to pull_image, Kubernetes events with Reason Failed whose human-readable message begins Failed to pull image, optional containerd or CRI-O file logs forwarded with filelog receivers, and Splunk correlation against registry-side failure storms using short-window Failed event counts grouped by registry hostname. UC-3.2.30 owns init-container phase failures. UC-3.2.43 owns probe failures after containers are running.

Platform prerequisites include Splunk indexes k8s_metrics for Prometheus text or normalized metric events, k8s for Kubernetes API events and optional runtime logs, and k8s_audit for kube-apiserver audit records when you must attribute a bad image reference to a CI principal or GitOps actor. HEC tokens live in vaults with quarterly rotation and index-time RBAC aligned to platform roles so developers cannot read Secret-derived material from verbose events.

Deploy kube-state-metrics with the workload metric set so pod waiting reasons include ImagePullBackOff and ErrImagePull without custom collectors. Scrape intervals of fifteen to thirty seconds are typical; shorter intervals improve dwell-time fidelity for ImagePullBackOff timers at license cost. kubelet metrics on port 10250 require bearer token authentication from the collector ServiceAccount and trust for the cluster serving certificate bundle. Document how your distro labels cluster identity in metric extractions so the cluster field in SPL matches k8s_workload_routing.csv.

Governance lookups include k8s_namespace_tier.csv for workload_tier values prod, production, preprod, staging, uat, nonprod, dev, and sandbox; k8s_workload_routing.csv for namespace, pod name or pattern documented in your runbook, owner_workload such as Deployment checkout-api, and on_call_team for paging; and image_pull_secret_inventory.csv listing namespace, optional workload owner, has_imagepullsecret as zero or one, and named_secrets for expected Secret names bound to ServiceAccounts that should pull from private registries. Refresh lookups on every namespace onboarding ticket.

For Docker Hub anonymous pulls, finance and platform teams align on either authenticated robot accounts, paid entitlements, or mandatory pull-through cache because anonymous IP budgets exhaust quickly behind shared NAT during patch waves. For Amazon ECR, Google Artifact Registry, and Azure Container Registry, document token lifetime and IAM or workload identity wiring so expired tokens surface as auth errors in events rather than mysterious network timeouts.

Risk narrative for executives: ImagePullBackOff blocks rolling updates because new ReplicaSet pods cannot become Ready until the image exists on the node; customer-visible errors accumulate while old pods drain or while capacity shrinks during autoscaling. Compliance mapping references public Kubernetes documentation on images, private pulls, imagePullSecrets, and logging architecture alongside Splunk documentation for the Kubernetes add-on and collector patterns.

Licensing note: metric cardinality grows with pod count; drop experimental labels at scrape time when safe. Event volume spikes during registry outages; consider routing verbose CRI pull logs to a dedicated sourcetype with shorter retention.

Collector hygiene: never expose kubelet read-only ports beyond the node firewall expectations of your cloud provider; rotate collector ServiceAccount tokens under change control. When dual-writing legacy HEC and OTel, deduplicate before interpreting kubelet counters.

Differentiation recap: CrashLoopBackOff in UC-3.2.10 means the container ran and crashed; ImagePullBackOff here means the kubelet never completed the pull. UC-3.1.26 explains dockerd-class pull failures on the host; this UC explains orchestrated pod lifecycle failures tied to kubelet state machines.

### Step 2 — Configure data collection

Splunk OpenTelemetry Collector for Kubernetes should run a prometheus receiver against kube-state-metrics and against each kubelet metrics endpoint per your security posture, a kubernetes_events or k8s_events receiver for the API event stream, kubeletstats when you also need resource summaries, and filelog receivers for /var/log/pods or containerd CRI JSON logs when security approves host file access. Export to Splunk HEC with splunk_hec exporters that set index, source, and sourcetype consistently across clusters.

Concrete ServiceMonitor or scrape config for kube-state-metrics can mirror your Prometheus Operator baseline: interval thirty seconds, path /metrics, scheme http inside the cluster, relabel rules that preserve namespace, pod, container, node, and image labels on kube_pod_container_status_waiting_reason series. For kubelet scrape, configure bearer_token_file on the collector pod and tls.insecure_skip_verify only if your policy mandates it; prefer proper CA validation against the cluster ConfigMap.

Example collector fragment with kubelet stats, prometheus scrapes, kubernetes events, filelog, and HEC:

```yaml
receivers:
  kubeletstats:
    collection_interval: 20s
    auth_type: serviceAccount
    endpoint: https://${K8S_NODE_NAME}:10250
    insecure_skip_verify: false
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
        - job_name: kubelet
          scheme: https
          tls_config:
            ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
          bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
          kubernetes_sd_configs:
            - role: node
          relabel_configs:
            - action: labelmap
              regex: __meta_kubernetes_node_label_(.+)
  k8s_events:
    auth_type: serviceAccount
    namespaces: []
  filelog:
    include:
      - /var/log/pods/*/*/*.log
    start_at: beginning
processors:
  batch:
    timeout: 5s
exporters:
  splunk_hec/k8s_metrics:
    token: ${SPLUNK_HEC_TOKEN}
    endpoint: https://splunk.example.com:8088/services/collector
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
  splunk_hec/k8s_events:
    token: ${SPLUNK_HEC_TOKEN}
    endpoint: https://splunk.example.com:8088/services/collector
    index: k8s
    sourcetype: kube:events
  splunk_hec/k8s_filelog:
    token: ${SPLUNK_HEC_TOKEN}
    endpoint: https://splunk.example.com:8088/services/collector
    index: k8s
    sourcetype: kube:container:runtime
service:
  pipelines:
    metrics:
      receivers: [kubeletstats, prometheus]
      processors: [batch]
      exporters: [splunk_hec/k8s_metrics]
    logs/events:
      receivers: [k8s_events]
      processors: [batch]
      exporters: [splunk_hec/k8s_events]
    logs/filelog:
      receivers: [filelog]
      processors: [batch]
      exporters: [splunk_hec/k8s_filelog]
```

ConfigMap snippet for optional kubelet service log capture when your distro journals kubelet separately from container logs:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: splunk-otel-kubelet-journal
  namespace: observability
data:
  relay.yaml: |
    receivers:
      filelog/kubelet:
        include: [/var/log/kubernetes/kubelet.log]
    service:
      pipelines:
        logs/kubelet:
          receivers: [filelog/kubelet]
          exporters: [splunk_hec/k8s_filelog]
```

Validate ingestion with short searches: index=k8s_metrics kube_pod_container_status_waiting_reason earliest=-15m, index=k8s sourcetype=kube:events Failed pull earliest=-15m, index=k8s sourcetype=kube:container:runtime pull earliest=-15m, index=k8s_metrics kubelet_runtime_operations_errors_total earliest=-15m. Skew between scrapes and events should stay under one minute for meaningful multisearch joins.

Security: redact pull secrets from CRI log lines at the collector when policy requires masking. Restrict k8s_audit to security and platform roles.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_14_kube_imagepull_backoff with schedule every five minutes and the same earliest and latest window as the comment macro. Throttle duplicate critical pages per cluster, namespace, and pod for thirty minutes when registry_storm=1 and vendor status pages document an active incident, but never suppress isolated credential regressions in production namespaces without a change ticket reference.

Understanding the pipeline: multisearch fans three arms so missing kube-state scrapes do not hide kube event narratives, and kubelet pull_image error counters still land even when event serialization lags. coalesce on cluster, namespace, pod, container, image, and node tolerates camelCase versus snake_case exporter differences across OTel and legacy agents. streamstats marks the first transition into ImagePullBackOff-class reasons per pod container, and eventstats max(time_in_ipb_min) stabilizes dwell estimates when scrape jitter fragments samples. Joins to k8s_namespace_tier.csv and k8s_workload_routing.csv add workload_tier, owner_workload, and on_call_team for routing. inputlookup image_pull_secret_inventory.csv adds has_imagepullsecret so responders immediately see namespaces that should carry registry credentials but often do not.

The registry correlation join aggregates Failed pull events over five minutes by image_registry hostname extracted from message text; when registry_failed_events_5m crosses registry_failed_storm_floor, severity escalates toward a rolled-up registry incident interpretation rather than a single bad tag, matching operational playbooks for Docker Hub rate limits and regional registry outages described in public Docker documentation.

cimSpl in the JSON field shows an accelerated tstats pattern against Application_State for environments that map Kubernetes workload identities into Application_State.app and node or host identities into Application_State.dest; adapt nodename filters to your Common Information Model implementation.

Fenced SPL for runbooks must match the spl JSON field exactly:

```spl
`comment("UC-3.2.14 Kubernetes ImagePullBackOff Detection. Tunables: indexes k8s_metrics k8s k8s_audit; sourcetypes prometheus:scrape:metrics kube:objects:metrics kube:events; lookups k8s_workload_routing.csv k8s_namespace_tier.csv image_pull_secret_inventory.csv; min_dwell_minutes_alert=3; registry_failed_storm_floor=25; earliest=-4h@m latest=now")`
| multisearch 
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "pod=\"(?<pod_rx>[^\"]+)\""
      | rex field=_raw "container=\"(?<ctr_rx>[^\"]+)\""
      | rex field=_raw "reason=\"(?<reason_rx>[^\"]+)\""
      | rex field=_raw "node=\"(?<node_rx>[^\"]+)\""
      | rex field=_raw "image=\"(?<img_rx>[^\"]+)\""
      | rex field=_raw "image_id=\"(?<image_id_rx>[^\"]+)\""
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval pod=trim(toString(coalesce(pod, pod_name, k8s_pod, pod_rx, "")))
      | eval container=trim(toString(coalesce(container, container_name, ctr_rx, "")))
      | eval waiting_reason=trim(toString(coalesce(reason, waiting_reason, reason_rx, "")))
      | eval node=trim(toString(coalesce(node, node_name, host_node, node_rx, "")))
      | eval image=trim(toString(coalesce(image, img_rx, image_id_rx, "")))
      | where (like(metric_nm, "%kube_pod_container_status_waiting_reason%") OR like(_raw, "kube_pod_container_status_waiting_reason"))
      | where waiting_reason="ImagePullBackOff" OR waiting_reason="ErrImagePull"
      | eval arm="ksm"
      | eval err_txt=""
      | fields _time cluster namespace pod container image waiting_reason node arm err_txt ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "node=\"(?<node_rx>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "")))
      | eval node=trim(toString(coalesce(node, node_name, node_rx, "")))
      | eval lrk=lower(_raw)
      | where (like(metric_nm, "%kubelet_runtime_operations_errors_total%") OR like(_raw, "kubelet_runtime_operations_errors_total")) AND match(lrk, "pull_image")
      | eval kubelet_pull_err=tonumber(mval, 10)
      | eval arm="kubelet"
      | eval namespace=""
      | eval pod=""
      | eval container=""
      | eval image=""
      | eval waiting_reason="KubeletPullImageErrors"
      | eval err_txt="kubelet_runtime_operations_errors_total operation_type pull_image"
      | fields _time cluster namespace pod container image waiting_reason node arm err_txt kubelet_pull_err ]
    [ search index=k8s sourcetype="kube:events" earliest=-4h@m latest=now
      | eval msg=trim(toString(coalesce(message, Message, "")))
      | eval lr=lower(msg)
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | where rs="Failed" AND match(lr, "failed to pull image")
      | eval pod=trim(toString(coalesce(involvedObject.name, involvedObject_name, pod, "")))
      | eval namespace=trim(toString(coalesce(metadata.namespace, namespace, "")))
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, "")))
      | eval arm="evt"
      | eval waiting_reason="FailedPullEvent"
      | eval err_txt=substr(msg, 1, 520)
      | rex field=msg "(?i)image\\s+\\\"(?<img_evt>[^\\\"]+)\""
      | eval image=coalesce(img_evt, "")
      | eval container=""
      | eval node=""
      | fields _time cluster namespace pod container image waiting_reason node arm err_txt ]
| eval cluster=coalesce(nullif(trim(cluster),""), "unknown-cluster")
| eval kubelet_err_f=if(arm="kubelet", kubelet_pull_err, null())
| eventstats max(kubelet_err_f) AS kubelet_pull_err_on_node BY cluster node
| where arm="ksm" OR arm="evt"
| eval kubelet_pull_err=coalesce(kubelet_pull_err_on_node, 0)
| join type=left max=0 namespace pod [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "pod=\"(?<pod>[^\"]+)\""
      | rex field=_raw "node=\"(?<node>[^\"]+)\""
      | where like(_raw, "kube_pod_info") OR like(lower(coalesce(metric_name, __name__, "")), "kube_pod_info")
      | stats latest(node) AS node_from_podinfo BY namespace pod ]
| eval node=coalesce(nullif(trim(node),""), node_from_podinfo, "")
| join type=left max=0 cluster node [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | rex field=_raw "node=\"(?<node>[^\"]+)\""
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, "")))
      | eval lrk=lower(_raw)
      | where like(_raw, "kubelet_runtime_operations_errors_total") AND match(lrk, "pull_image")
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | stats latest(tonumber(mval, 10)) AS kubelet_pull_err BY cluster node ]
| eval image_registry=case(
    match(image, "^[^/]+\\.[^/]+/"), mvindex(split(image, "/"), 0),
    match(image, "^docker\\.io/"), "docker.io",
    len(trim(coalesce(image,"")))>0 AND !match(image, "/"), "docker.io",
    true(), "unknown")
| join type=left max=0 image_registry [
    search index=k8s sourcetype="kube:events" earliest=-5m latest=now
      | eval msgf=trim(toString(coalesce(message, Message, "")))
      | eval rsf=trim(toString(coalesce(reason, Reason, "")))
      | where rsf="Failed" AND match(lower(msgf), "failed to pull image")
      | rex field=msgf "(?i)\\\"(?<regtok>[^/\"]+\\.[^/\"]+)"
      | eval image_registry=mvindex(split(regtok, "/"), 0)
      | stats count AS registry_failed_events_5m BY image_registry ]
| fillnull value=0 registry_failed_events_5m
| eval error_message=coalesce(nullif(trim(err_txt),""), "container image pull stalled; correlate kube event and kubelet metric arms")
| sort 0 cluster namespace pod container _time
| streamstats current=f last(waiting_reason) AS prev_wr BY cluster namespace pod container
| eval ipb_on=if(waiting_reason="ImagePullBackOff" OR waiting_reason="ErrImagePull" OR waiting_reason="FailedPullEvent", 1, 0)
| eval ipb_enter=if(ipb_on=1 AND (isnull(prev_wr) OR NOT (prev_wr="ImagePullBackOff" OR prev_wr="ErrImagePull" OR prev_wr="FailedPullEvent")), _time, null())
| streamstats last(ipb_enter) AS ipb_since BY cluster namespace pod container
| eval time_in_ipb_min=if(ipb_on=1 AND isnotnull(ipb_since), round((now()-ipb_since)/60, 2), null())
| eventstats max(time_in_ipb_min) AS dwell_ipb_pod_max BY cluster namespace pod container
| eval time_in_ipb_min=coalesce(time_in_ipb_min, dwell_ipb_pod_max)
| join type=left max=0 namespace [
    | inputlookup k8s_namespace_tier.csv
    | eval namespace=trim(toString(namespace))
    | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, "dev"))))
    | fields namespace workload_tier ]
| join type=left max=0 namespace pod [
    | inputlookup k8s_workload_routing.csv
    | eval namespace=trim(toString(namespace))
    | eval pod=trim(toString(pod))
    | eval owner_workload=trim(toString(coalesce(owner_workload, workload, owner_kind_name, "")))
    | eval on_call_team=trim(toString(coalesce(on_call_team, owner_team, squad, "")))
    | fields namespace pod owner_workload on_call_team ]
| join type=left max=0 namespace [
    | inputlookup image_pull_secret_inventory.csv
    | eval namespace=trim(toString(namespace))
    | eval has_imagepullsecret=tonumber(coalesce(has_imagepullsecret, has_secret, ip_secret_present, "1"), 10)
    | fields namespace has_imagepullsecret ]
| eval registry_storm=if(registry_failed_events_5m>=25, 1, 0)
| eval severity=case(
    registry_storm=1 AND (workload_tier="prod" OR workload_tier="production"), "critical",
    (workload_tier="prod" OR workload_tier="production") AND coalesce(time_in_ipb_min,0)>5, "critical",
    (workload_tier="prod" OR workload_tier="production") AND coalesce(time_in_ipb_min,0)>2, "high",
    match(workload_tier, "preprod|staging|uat|nonprod"), "medium",
    true(), "low")
| where ipb_on=1
| where coalesce(time_in_ipb_min,0)>=3 OR registry_storm=1
| stats latest(image) AS image latest(container) AS container latest(image_registry) AS image_registry latest(time_in_ipb_min) AS time_in_ipb_min latest(error_message) AS error_message latest(owner_workload) AS owner_workload latest(on_call_team) AS on_call_team latest(workload_tier) AS workload_tier latest(severity) AS severity latest(registry_failed_events_5m) AS registry_failed_events_5m latest(kubelet_pull_err) AS kubelet_pull_err latest(has_imagepullsecret) AS has_imagepullsecret BY cluster namespace pod container
| table cluster namespace pod container image image_registry time_in_ipb_min error_message owner_workload severity on_call_team registry_failed_events_5m kubelet_pull_err has_imagepullsecret
```

Alert actions should include cluster, namespace, pod, container, image, image_registry, time_in_ipb_min, severity, on_call_team, registry_failed_events_5m, and kubelet_pull_err in the email or ITSI notable body. Provide a drilldown search that pulls the last fifty matching kube:events lines for the same pod and a secondary drill that shows kubelet pull errors on the same node.

Performance: Job Inspector should stay within platform limits; if joins to kube_pod_info fail because your scrape shape differs, remove that enrichment arm and rely on node labels from kube-state-metrics waiting_reason series only. Materialize five-minute summaries of kube_pod_container_status_waiting_reason when raw metric indexes exceed petabyte-scale scan budgets.

### Step 4 — Validate

Synthetic negative image: kubectl run badimage --image=this-image-does-not-exist:v1 -n qa-ipb --restart=Always and confirm kube_pod_container_status_waiting_reason shows ErrImagePull then ImagePullBackOff within two scrape intervals. Execute uc_3_2_14_kube_imagepull_backoff and expect a row with non-null error_message and time_in_ipb_min growing beyond the min_dwell_minutes_alert gate.

Synthetic private registry without credentials: kubectl run private --image=privatereg.example.com/foo:v1 -n qa-ipb without an imagePullSecret on the ServiceAccount and confirm Failed events include unauthorized or pull access denied semantics depending on registry behavior. Expect severity at least high when workload_tier marks qa-ipb as production in k8s_namespace_tier.csv for lab realism.

Egress fault simulation: in a disposable lab only, block HTTPS toward a documented Docker Hub edge range using host or network policy tooling, then observe Failed to pull image messages and rising registry_failed_events_5m for docker.io or registry-1.docker.io hostnames. Document the exact CIDR you used in the test record and remove the block after validation.

Tear-down: delete the lab pod and Deployment objects, confirm the saved search returns zero qualifying rows on the next interval, and verify alert auto-clear behavior in your notification system.

Validation SPL for quiet clusters: index=k8s_metrics kube_pod_container_status_waiting_reason (ImagePullBackOff OR ErrImagePull) earliest=-24h | stats dc(pod) AS ipb_pods | where ipb_pods=0.

Audit correlation drill: index=k8s_audit sourcetype=kube:audit (verb=create OR verb=patch OR verb=update) objectRef.resource=deployments earliest=-2h to recover user.username or service account subjects that introduced the failing image string.

### Step 5 — Operationalize & Troubleshoot

Case 1 — ImagePullBackOff due to typo in image tag or wrong digest
Compare the image field in Splunk with the manifest in Git; correct the tag or digest, roll forward the Deployment, and confirm kube-state-metrics clears ErrImagePull. Use kubectl describe pod output referenced in kubectl documentation for human-readable pull errors.

Case 2 — ImagePullBackOff due to missing imagePullSecret
Join Splunk rows with low has_imagepullsecret against namespace ServiceAccount definitions; create a dockerconfigjson Secret, reference it under imagePullSecrets on the Pod template, and roll the workload. Kubernetes documentation for using Secrets as image pull credentials is the authoritative procedure reference.

Case 3 — ImagePullBackOff due to expired imagePullSecret token
Refresh robot credentials for private registries; for ECR patterns, verify GetAuthorizationToken automation and twelve-hour token lifecycles. Reconcile Secret data, restart affected pods, and watch kubelet counters return toward zero.

Case 4 — ImagePullBackOff due to Docker Hub anonymous rate limit
Correlate registry_failed_events_5m spikes for docker.io with documentation on Hub download rate limits; authenticate pulls, enable cache, or pause non-production image storms until budgets recover.

Case 5 — ImagePullBackOff due to private registry blocked by NetworkPolicy egress
NetworkPolicy denying TCP 443 to registry hosts produces timeouts mirrored as Failed to pull image; compare Splunk Network_Traffic or firewall logs with policy rules, temporarily relax under change control, or install cluster-internal pull-through mirrors.

Case 6 — ImagePullBackOff due to Amazon ECR token expiry lifecycle
ECR tokens expire quickly by design; broken IAM wiring or stale init containers that refresh tokens show repeating ErrImagePull. Fix workload identity chains and validate awslogs or CloudTrail RegistryAuthFailed patterns if you also ingest cloud control-plane telemetry.

Case 7 — ImagePullBackOff due to image scanned out or quarantined by registry policy
Vendor scanners may block vulnerable digests at pull time; pair this operational signal with UC-3.1.10 vulnerability governance for rebuild guidance rather than muting the alert.

Case 8 — ErrImagePull due to bad mTLS certificate on registry endpoint
TLS handshake failures appear in CRI logs and events; follow certificate trust stores on nodes and registry frontends. Cross-link UC-3.4.8 for deeper TLS observability when that use case exists in your catalogue.

Case 9 — ImagePullBackOff during cluster-autoscaler cold start when a new node has an empty image cache
Large images on fresh nodes can resemble ImagePullBackOff for thirty to ninety seconds; enforce min_dwell_minutes_alert at three minutes in production paging macros and require sustained registry_failed_events_5m before declaring registry outages.

Case 10 — False positive chaos engineering pods with deliberately invalid images
Suppress namespaces or pods labeled chaos.imagepull=expected in k8s_workload_routing.csv with pager_suppress=1 so game-day exercises do not page production bridges.

Case 11 — Storm with thousands of pods in ImagePullBackOff simultaneously
When registry_failed_events_5m exceeds the storm floor across many namespaces, treat as registry or identity platform outage; open vendor bridges, shift to mirrors, and page registry SRE using rolled-up signatures instead of per-pod tickets.

Case 12 — Docker host perspective without duplicating UC-3.1.26
When investigation proves dockerd or host-level registry egress is healthy but Kubernetes still shows ImagePullBackOff, stay in this kubelet-focused runbook; when nodes run only containerd with no Kubernetes, use UC-3.1.26 instead of blending both stories in one incident record.

Dashboard hygiene: keep a panel for kubelet_image_pull_duration_seconds quantiles when your scrape exposes them, and overlay kubelet image garbage collection indicators when nodes reclaim unused images during disk pressure investigations.

Evidence retention: weekly CSV export of alert rows with lookup commit hashes, kube-state-metrics chart version, and collector image digest for audit replay.

Governance: quarterly replay one real ImagePullBackOff incident through the SPL after kube-state-metrics upgrades because label names occasionally shift; update rex patterns when Prometheus relabel configs change.

Closing checklist: monitoringType includes Reliability and Availability; equipmentModels kubernetes_k8s; cimModels Application_State and Network_Traffic; five step headers use plain em dashes; Step 3 fenced SPL matches the spl JSON field; Step 5 lists twelve numbered cases; narrative fields avoid forbidden boilerplate phrases; references include six or more unique public URLs as listed in the references array.

Performance note: if multisearch scans become expensive, schedule a summary index writer that emits namespace, pod, container, waiting_reason, and cluster dimensions every five minutes, then point this alert at the summary while keeping raw scrapes for ad-hoc rex tuning.

Training: teach on-call staff to read event messages for manifest unknown versus unauthorized versus timeout classes before escalating to network teams.

Cloud control planes: on EKS, confirm security groups still allow node egress to registries after landing-zone changes; on GKE, validate workload identity for Artifact Registry; on AKS, validate managed identity attachments for ACR.

When finance questions spend on authenticated Hub plans, attach registry_failed_events_5m timelines showing revenue-impacting deploy freezes during anonymous budget exhaustion.



## SPL

```spl
`comment("UC-3.2.14 Kubernetes ImagePullBackOff Detection. Tunables: indexes k8s_metrics k8s k8s_audit; sourcetypes prometheus:scrape:metrics kube:objects:metrics kube:events; lookups k8s_workload_routing.csv k8s_namespace_tier.csv image_pull_secret_inventory.csv; min_dwell_minutes_alert=3; registry_failed_storm_floor=25; earliest=-4h@m latest=now")`
| multisearch 
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "pod=\"(?<pod_rx>[^\"]+)\""
      | rex field=_raw "container=\"(?<ctr_rx>[^\"]+)\""
      | rex field=_raw "reason=\"(?<reason_rx>[^\"]+)\""
      | rex field=_raw "node=\"(?<node_rx>[^\"]+)\""
      | rex field=_raw "image=\"(?<img_rx>[^\"]+)\""
      | rex field=_raw "image_id=\"(?<image_id_rx>[^\"]+)\""
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval pod=trim(toString(coalesce(pod, pod_name, k8s_pod, pod_rx, "")))
      | eval container=trim(toString(coalesce(container, container_name, ctr_rx, "")))
      | eval waiting_reason=trim(toString(coalesce(reason, waiting_reason, reason_rx, "")))
      | eval node=trim(toString(coalesce(node, node_name, host_node, node_rx, "")))
      | eval image=trim(toString(coalesce(image, img_rx, image_id_rx, "")))
      | where (like(metric_nm, "%kube_pod_container_status_waiting_reason%") OR like(_raw, "kube_pod_container_status_waiting_reason"))
      | where waiting_reason="ImagePullBackOff" OR waiting_reason="ErrImagePull"
      | eval arm="ksm"
      | eval err_txt=""
      | fields _time cluster namespace pod container image waiting_reason node arm err_txt ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "node=\"(?<node_rx>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "")))
      | eval node=trim(toString(coalesce(node, node_name, node_rx, "")))
      | eval lrk=lower(_raw)
      | where (like(metric_nm, "%kubelet_runtime_operations_errors_total%") OR like(_raw, "kubelet_runtime_operations_errors_total")) AND match(lrk, "pull_image")
      | eval kubelet_pull_err=tonumber(mval, 10)
      | eval arm="kubelet"
      | eval namespace=""
      | eval pod=""
      | eval container=""
      | eval image=""
      | eval waiting_reason="KubeletPullImageErrors"
      | eval err_txt="kubelet_runtime_operations_errors_total operation_type pull_image"
      | fields _time cluster namespace pod container image waiting_reason node arm err_txt kubelet_pull_err ]
    [ search index=k8s sourcetype="kube:events" earliest=-4h@m latest=now
      | eval msg=trim(toString(coalesce(message, Message, "")))
      | eval lr=lower(msg)
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | where rs="Failed" AND match(lr, "failed to pull image")
      | eval pod=trim(toString(coalesce(involvedObject.name, involvedObject_name, pod, "")))
      | eval namespace=trim(toString(coalesce(metadata.namespace, namespace, "")))
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, "")))
      | eval arm="evt"
      | eval waiting_reason="FailedPullEvent"
      | eval err_txt=substr(msg, 1, 520)
      | rex field=msg "(?i)image\\s+\\\"(?<img_evt>[^\\\"]+)\""
      | eval image=coalesce(img_evt, "")
      | eval container=""
      | eval node=""
      | fields _time cluster namespace pod container image waiting_reason node arm err_txt ]
| eval cluster=coalesce(nullif(trim(cluster),""), "unknown-cluster")
| eval kubelet_err_f=if(arm="kubelet", kubelet_pull_err, null())
| eventstats max(kubelet_err_f) AS kubelet_pull_err_on_node BY cluster node
| where arm="ksm" OR arm="evt"
| eval kubelet_pull_err=coalesce(kubelet_pull_err_on_node, 0)
| join type=left max=0 namespace pod [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "pod=\"(?<pod>[^\"]+)\""
      | rex field=_raw "node=\"(?<node>[^\"]+)\""
      | where like(_raw, "kube_pod_info") OR like(lower(coalesce(metric_name, __name__, "")), "kube_pod_info")
      | stats latest(node) AS node_from_podinfo BY namespace pod ]
| eval node=coalesce(nullif(trim(node),""), node_from_podinfo, "")
| join type=left max=0 cluster node [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | rex field=_raw "node=\"(?<node>[^\"]+)\""
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, "")))
      | eval lrk=lower(_raw)
      | where like(_raw, "kubelet_runtime_operations_errors_total") AND match(lrk, "pull_image")
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | stats latest(tonumber(mval, 10)) AS kubelet_pull_err BY cluster node ]
| eval image_registry=case(
    match(image, "^[^/]+\\.[^/]+/"), mvindex(split(image, "/"), 0),
    match(image, "^docker\\.io/"), "docker.io",
    len(trim(coalesce(image,"")))>0 AND !match(image, "/"), "docker.io",
    true(), "unknown")
| join type=left max=0 image_registry [
    search index=k8s sourcetype="kube:events" earliest=-5m latest=now
      | eval msgf=trim(toString(coalesce(message, Message, "")))
      | eval rsf=trim(toString(coalesce(reason, Reason, "")))
      | where rsf="Failed" AND match(lower(msgf), "failed to pull image")
      | rex field=msgf "(?i)\\\"(?<regtok>[^/\"]+\\.[^/\"]+)"
      | eval image_registry=mvindex(split(regtok, "/"), 0)
      | stats count AS registry_failed_events_5m BY image_registry ]
| fillnull value=0 registry_failed_events_5m
| eval error_message=coalesce(nullif(trim(err_txt),""), "container image pull stalled; correlate kube event and kubelet metric arms")
| sort 0 cluster namespace pod container _time
| streamstats current=f last(waiting_reason) AS prev_wr BY cluster namespace pod container
| eval ipb_on=if(waiting_reason="ImagePullBackOff" OR waiting_reason="ErrImagePull" OR waiting_reason="FailedPullEvent", 1, 0)
| eval ipb_enter=if(ipb_on=1 AND (isnull(prev_wr) OR NOT (prev_wr="ImagePullBackOff" OR prev_wr="ErrImagePull" OR prev_wr="FailedPullEvent")), _time, null())
| streamstats last(ipb_enter) AS ipb_since BY cluster namespace pod container
| eval time_in_ipb_min=if(ipb_on=1 AND isnotnull(ipb_since), round((now()-ipb_since)/60, 2), null())
| eventstats max(time_in_ipb_min) AS dwell_ipb_pod_max BY cluster namespace pod container
| eval time_in_ipb_min=coalesce(time_in_ipb_min, dwell_ipb_pod_max)
| join type=left max=0 namespace [
    | inputlookup k8s_namespace_tier.csv
    | eval namespace=trim(toString(namespace))
    | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, "dev"))))
    | fields namespace workload_tier ]
| join type=left max=0 namespace pod [
    | inputlookup k8s_workload_routing.csv
    | eval namespace=trim(toString(namespace))
    | eval pod=trim(toString(pod))
    | eval owner_workload=trim(toString(coalesce(owner_workload, workload, owner_kind_name, "")))
    | eval on_call_team=trim(toString(coalesce(on_call_team, owner_team, squad, "")))
    | fields namespace pod owner_workload on_call_team ]
| join type=left max=0 namespace [
    | inputlookup image_pull_secret_inventory.csv
    | eval namespace=trim(toString(namespace))
    | eval has_imagepullsecret=tonumber(coalesce(has_imagepullsecret, has_secret, ip_secret_present, "1"), 10)
    | fields namespace has_imagepullsecret ]
| eval registry_storm=if(registry_failed_events_5m>=25, 1, 0)
| eval severity=case(
    registry_storm=1 AND (workload_tier="prod" OR workload_tier="production"), "critical",
    (workload_tier="prod" OR workload_tier="production") AND coalesce(time_in_ipb_min,0)>5, "critical",
    (workload_tier="prod" OR workload_tier="production") AND coalesce(time_in_ipb_min,0)>2, "high",
    match(workload_tier, "preprod|staging|uat|nonprod"), "medium",
    true(), "low")
| where ipb_on=1
| where coalesce(time_in_ipb_min,0)>=3 OR registry_storm=1
| stats latest(image) AS image latest(container) AS container latest(image_registry) AS image_registry latest(time_in_ipb_min) AS time_in_ipb_min latest(error_message) AS error_message latest(owner_workload) AS owner_workload latest(on_call_team) AS on_call_team latest(workload_tier) AS workload_tier latest(severity) AS severity latest(registry_failed_events_5m) AS registry_failed_events_5m latest(kubelet_pull_err) AS kubelet_pull_err latest(has_imagepullsecret) AS has_imagepullsecret BY cluster namespace pod container
| table cluster namespace pod container image image_registry time_in_ipb_min error_message owner_workload severity on_call_team registry_failed_events_5m kubelet_pull_err has_imagepullsecret
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state count AS state_events FROM datamodel=Application_State WHERE nodename=Application_State earliest=-4h@h latest=@h BY Application_State.dest Application_State.app
| rename Application_State.dest AS correl_host Application_State.app AS correl_app
| where app_state!="running" OR state_events>0
```

## Visualization

Primary table mirroring the closing SPL projection; timechart of registry_failed_events_5m by image_registry; single value of distinct pods in ImagePullBackOff-class reasons; heatmap of kubelet_pull_err by node during incidents.

## Known False Positives

Brief ImagePullBackOff during cluster-autoscaler scale-out can appear when a new node downloads large layers for the first time; the condition often clears within thirty to ninety seconds while kubelet retries succeed. Require time_in_ipb_min above the min_dwell gate and corroborate with registry_failed_events_5m before paging production unless a single critical namespace is completely idle. Image-warming DaemonSets or registry preflight jobs sometimes schedule pods that intentionally reference cold or nonexistent layers to prime cache; mark those namespaces with warmup_job=1 in k8s_workload_routing.csv and exclude them from paging macros. Chaos experiments that deliberately fail pulls should carry chaos.imagepull=expected labels and a matching suppression row so game-day traffic does not look like a credential incident. Brief ImagePullBackOff spikes during in-cluster registry pod restarts can occur when pull-through cache pods recycle; dampen with vendor maintenance annotations or require two consecutive alert intervals above threshold. CI namespaces that rebuild unique tags every commit may hammer registries without production customer impact; lower severity using workload_tier=sandbox in k8s_namespace_tier.csv. Dual scrape agents emitting duplicate kube-state-metrics samples can inflate kubelet_join noise until deduplication macros land; watch for identical _raw lines doubling counts. Lab clusters that point at air-gapped mirrors may never populate docker.io storm columns even during real outages; document mirror hostname expectations in image_pull_secret_inventory.csv notes to avoid misinterpreted nulls.

## References

- [Kubernetes — Container Images](https://kubernetes.io/docs/concepts/containers/images/)
- [Kubernetes — Pull an Image from a Private Registry](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)
- [Kubernetes — Secrets: imagePullSecrets](https://kubernetes.io/docs/concepts/configuration/secret/#using-imagepullsecrets)
- [kubectl reference — describe](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#describe)
- [Kubernetes kubelet types (image pull error semantics)](https://github.com/kubernetes/kubernetes/blob/master/staging/src/k8s.io/kubelet/pkg/types/)
- [Docker Docs — Docker Hub download rate limit](https://docs.docker.com/docker-hub/download-rate-limit/)
- [Kubernetes — Cluster Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Splunk Docs — Splunk Add-on for Kubernetes](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
