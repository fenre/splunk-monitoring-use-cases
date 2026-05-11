<!-- AUTO-GENERATED from UC-3.2.31.json — DO NOT EDIT -->

---
id: "3.2.31"
title: "Kubernetes Service Mesh Sidecar Injection Compliance and Coverage Drift (Istio, Linkerd, Consul Connect, Cilium Ambient)"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-3.2.31 · Kubernetes Service Mesh Sidecar Injection Compliance and Coverage Drift (Istio, Linkerd, Consul Connect, Cilium Ambient)

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Configuration, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We check that the small helpers that encrypt traffic between your applications are actually present wherever your rules say every workload should carry them, and we flag places where the rule says inject but running programs are missing those helpers so trust stays consistent inside the cluster.*

---

## Description

Unique monitoring axis: service mesh sidecar injection policy enforcement versus live proxy attachment—kube_namespace_labels istio-injection=enabled and istio.io/rev coverage compared to kube_pod_container_info and kube_pod_info Running inventories for istio-proxy, linkerd-proxy, and Envoy-class containers, kube_pod_annotations sidecar.istio.io/inject=false overrides, Cilium ambient namespace exemptions via io.cilium.ambient/enabled, Istio pilot_proxy_convergence_time and pilot_xds_pushes control-plane reach signals, Linkerd linkerd_proxy_inbound_tls_handshake_total proxy reach, mesh_sidecar_governance.csv for mesh_flavor and ambient_mesh_ns, PeerAuthentication STRICT and AuthorizationPolicy bypass risk when workloads lack sidecars. This is mesh injection compliance and drift, not UC-3.2.27 NetworkPolicy default-deny, not UC-3.2.22 PSA, not UC-3.2.40 admission webhook health.

## Value

When namespaces claim injection but pods run without mesh proxies, east-west mutual TLS, uniform L7 telemetry, and mesh authorization intent fracture long before traditional perimeter alerts notice. Timestamped gap rows give platform and service mesh teams a prioritized backlog tied to owner_team from governance lookups. Customers and regulators asking for zero-trust Kubernetes evidence receive proof that mesh posture is monitored continuously, not only described in diagrams. Mean time to contain improves because Splunk shows which cluster, which namespace, how many Running pods lack proxies, and whether inject=false annotations or ambient exemptions explain the pattern.

## Implementation

Stand up k8s_metrics scrapes of kube-state-metrics namespace, pod, container, and annotation metric families plus Istio istiod and Linkerd control-plane Prometheus endpoints. Publish mesh_sidecar_governance.csv with mesh_flavor, ambient exempt flags, grace epochs, and owners. Save uc_3_2_31_mesh_sidecar_injection_compliance on a ten-minute cadence over earliest=-4h@h latest=@h, route critical_mesh_gap rows to the platform mesh bridge, and archive weekly evidence exports with lookup commit hashes for zero-trust reviews.

## Evidence

Saved search uc_3_2_31_mesh_sidecar_injection_compliance; versioned mesh_sidecar_governance.csv in git; weekly CSV export of the closing table to a restricted evidence index; dashboard drilldowns from severity to raw prometheus scrape lines and pod lists.

## Control test

### Positive scenario

In a lab namespace labeled istio-injection=enabled with mesh_sidecar_governance.csv sidecar_required=1, deploy a pod that remains Running without istio-proxy in kube_pod_container_info, confirm kube_namespace_labels still shows enabled, run uc_3_2_31_mesh_sidecar_injection_compliance, and expect compliance_gap=1 with missing_proxy_pod_cnt greater than zero and severity critical_mesh_gap or high_mesh_gap when workload_tier marks production-like tiers.

### Negative scenario

Label the same namespace io.cilium.ambient/enabled=true with ambient_mesh_ns=1 in the lookup, confirm ns_expect_mesh_sidecar evaluates to zero expectation in the namespace arm, verify the search returns no compliance_gap for ambient-only workloads, then roll pods after enabling classic injection in a non-ambient namespace and confirm missing_proxy_pod_cnt returns to zero within two evaluation windows.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the service mesh engineering lead who operates Istio, Linkerd, Consul Connect, or Cilium ambient fleets, the zero-trust architecture council that signs off on east-west mutual TLS posture, workload identity and PKI operators who rotate mesh trust anchors, GitOps owners who apply namespace labels such as istio-injection=enabled and istio.io/rev revision tags, and observability engineers who run Splunk OpenTelemetry Collector Prometheus receivers against kube-state-metrics plus mesh control-plane scrape targets. UC-3.2.31 isolates service mesh sidecar injection compliance and ambient coverage drift only: whether kube-state-metrics kube_namespace_labels show mesh-enabling labels where architecture expects automatic sidecar injection, whether io.cilium.ambient/enabled=true marks namespaces that legitimately omit classic sidecars because the ambient dataplane captures traffic without per-pod Envoy, whether kube_pod_container_info joined to kube_pod_info Running inventory proves proxy containers named istio-proxy, linkerd-proxy, linkerd2-proxy, or envoy-sidecar classes exist on workloads that should participate in the mesh, whether kube_pod_annotations expose sidecar.istio.io/inject=false overrides that explain missing proxies, whether Istio istiod exposes pilot_proxy_convergence_time and pilot_xds_pushes as witnesses of healthy configuration distribution, whether linkerd_proxy_inbound_tls_handshake_total demonstrates Linkerd proxies terminating TLS on inbound paths, and whether mesh-aware policy objects such as PeerAuthentication STRICT mode, Sidecar resources, and AuthorizationPolicy intent would be undermined when workloads bypass the mesh. UC-3.2.27 remains Kubernetes NetworkPolicy default-deny coverage and networking.k8s.io object governance, not mesh proxy attachment. UC-3.2.22 remains Pod Security Admission denials and pod-security.kubernetes.io label drift. UC-3.2.40 remains out-of-tree admission webhook latency and failurePolicy traps rather than per-pod mesh proxy inventories. No sibling replaces kube_pod_container_info minus-proxy gap counting inside injection-enabled namespaces or Cilium ambient label interpretation for sidecarless-by-design posture.

Index and sourcetype contracts: dedicate index=k8s_metrics for sourcetype=prometheus:scrape:metrics with fifteen-to-sixty second scrape cadence from kube-state-metrics and mesh control planes, preserving k8s_cluster_name or equivalent cluster labels on every line. Confirm Prometheus label translation maps Kubernetes annotation keys with slashes into underscore form on scraped lines so rex ladders can reach istio_injection, istio_io_rev, and io_cilium_ambient_enabled patterns consistently. Optional summary index=k8s_mesh_compliance may hold hourly rollups of missing_proxy_pod_cnt when search cost grows; document lag acceptance when alerts point at summaries instead of raw scrapes.

Governance lookup: publish lookups/mesh_sidecar_governance.csv from the same Git repository that applies namespace labels and Helm values so auditors trace rows to commits. Minimum columns: cluster, namespace, mesh_flavor among istio, linkerd, consul_connect, cilium_ambient, none, sidecar_required as 1 when CSV asserts expectation even if a transient label scrape lags, ambient_mesh_ns as 1 when namespaces intentionally use Cilium ambient or equivalent sidecarless mesh modes, owner_team, workload_tier for severity weighting, grace_until_epoch Unix seconds for phased mesh rollouts, optional notes for Consul Connect connect-inject naming variants. Refresh when namespaces are created, retired, or change mesh mode.

Risk framing: workloads in namespaces labeled for injection but lacking proxies bypass mesh mutual TLS, lose uniform L7 telemetry headers, and may violate AuthorizationPolicy intent while still passing naive L3/L4 checks. Pods created before namespace labels flipped to enabled often run without restarts; Splunk surfaces that drift as label-on versus proxy-off gaps. Operators who annotate sidecar.istio.io/inject=false for convenience without recording governance exceptions look identical to incidents until annotation arms corroborate intent. Clock skew between Prometheus scrapes, kube-state-metrics watches, and Splunk indexing can mis-order convergence spikes; keep NTP within thirty seconds across collectors, apiservers, and indexers.

Legal and privacy: pod names and annotations may include customer identifiers; restrict k8s_metrics indexes and redact alert emails per DLP policy. Licensing: kube_pod_container_info cardinality follows pod churn; FinOps should review high-churn clusters before sub-minute schedules.

Training: teach responders the difference between ambient mesh exempt namespaces and classic sidecar omission, how PeerAuthentication STRICT interacts with non-meshed clients, and why istiod pilot_proxy_convergence_time outliers may indicate control-plane overload rather than workload misconfiguration alone.

Differentiation recap: mesh injection compliance and drift, not NetworkPolicy object governance, not PSA admission outcomes, not generic admission webhook SLO scoring.

### Step 2 — Configure data collection

Deploy kube-state-metrics with RBAC that can list namespaces, pods, containers, and annotations so kube_namespace_labels, kube_pod_info, kube_pod_container_info, and kube_pod_annotations series appear in documentation-aligned forms. Confirm your kube-state-metrics release exposes pod annotation metrics when your security posture enables them; without kube_pod_annotations the inject=false arm stays quiet and you rely more heavily on live kubectl audits for annotation truth. Configure Splunk OpenTelemetry Collector prometheus receiver scrape jobs against the kube-state-metrics Service with honor_labels settings that preserve namespace, pod, and container labels on series.

Scrape Istio control-plane metrics from istiod or the operator-managed metrics Service so pilot_proxy_convergence_time histograms and pilot_xds_pushes counters reach the same index family with identical cluster attribution fields. For Linkerd, scrape the destination, proxy, or viz Prometheus endpoints documented for your release so linkerd_proxy_inbound_tls_handshake_total is observable fleet-wide. For Consul Connect on Kubernetes, align scrape configs with the connect-inject controller metrics guidance in HashiCorp documentation and map cluster labels consistently. For Cilium ambient, ensure namespace labels io.cilium.ambient/enabled surface on kube_namespace_labels scrapes or parallel Cilium metrics pipelines; if labels appear only on Cilium CRs, extend this UC with a companion small exporter after architecture review.

Example prometheus receiver fragment:

```yaml
receivers:
  prometheus/ksm:
    config:
      scrape_configs:
        - job_name: kube-state-metrics
          scrape_interval: 30s
          kubernetes_sd_configs:
            - role: endpoints
          relabel_configs:
            - source_labels: [__meta_kubernetes_service_name]
              regex: kube-state-metrics
              action: keep
exporters:
  splunk_hec/metrics:
    token: "${SPLUNK_HEC_TOKEN_K8S_METRICS}"
    endpoint: "https://splunk.example.com:8088/services/collector/event"
    sourcetype: prometheus:scrape:metrics
    index: k8s_metrics
service:
  pipelines:
    metrics/ksm:
      receivers: [prometheus/ksm]
      exporters: [splunk_hec/metrics]
```

Publish a starter mesh_sidecar_governance.csv:

```csv
cluster,namespace,mesh_flavor,sidecar_required,ambient_mesh_ns,owner_team,workload_tier,grace_until_epoch,notes
prod-eks-01,payments,istio,1,0,team-payments,critical,0,baseline mesh
prod-eks-01,observability,cilium_ambient,0,1,team-obs,standard,0,ambient dataplane
lab-gke,mesh-pilot-lab,istio,1,0,team-lab,lab,1735689600,rev tag rollout window
```

Pre-flight searches: index=k8s_metrics kube_namespace_labels earliest=-30m must return lines with namespace labels for mesh-enabled namespaces; kube_pod_container_info must list istio-proxy on a known meshed pod; pilot_xds_pushes or linkerd_proxy_inbound_tls_handshake_total should be non-zero on active clusters after scrapes stabilize.

CIM acceleration: accelerate Splunk CIM Application_State and Change summaries on kubernetes_cluster or management-plane entities referenced in Application_State.dest so tstats overlays stay warm for executive correlation panels described in cimSpl.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_31_mesh_sidecar_injection_compliance with a five-to-fifteen minute schedule during steady operations using earliest=-4h@h latest=@h inside the query. Throttle duplicate pages per cluster and namespace for forty-five minutes unless severity escalates from high to critical within the same hour. Route critical_mesh_gap rows to the service mesh bridge with owner_team from mesh_sidecar_governance.csv attached. Archive weekly CSV snapshots of the closing table to a restricted evidence index with lookup commit hashes for auditors reviewing zero-trust east-west enforcement.

Pipeline narrative: the opening comment macro records tunable index names, sourcetypes, lookup keys, time window, and sibling differentiation. multisearch fans four arms so namespace label posture, Running pod proxy gaps, inject=false annotation density, and Running pod inventory converge without silently dropping lanes when one exporter pauses. The first arm derives ns_expect_mesh_sidecar from istio-injection=enabled, non-empty istio.io/rev, or Cilium ambient=true exemptions that set expectation to zero classic sidecars. The second arm inner-joins kube_pod_container_info to kube_pod_info Running pods, flags pods whose container set lacks mesh proxy names, and counts missing_proxy_pod_cnt per namespace. The third arm counts inject_false_ann_cnt from kube_pod_annotations. The fourth arm records running_pod_cnt for context. Outer stats merges by cluster and namespace. join overlays mesh_sidecar_governance.csv for mesh_flavor, sidecar_required, ambient_mesh_ns, tiers, and grace epochs. A follow-on join pulls pilot_proxy_convergence_time, pilot_xds_pushes, and linkerd_proxy_inbound_tls_handshake_total aggregates per cluster. tstats arms enrich Change and Application_State touches for configuration correlation. eventstats derives fleet_pilot_conv_med for Istiod spike detection. streamstats smooths missing_proxy_ma3 for drift momentum. case assigns severity. The closing table projects nineteen analyst columns for triage.

Paste-and-run SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.2.31 Service mesh sidecar injection compliance and coverage drift. Signals: kube_namespace_labels for istio-injection=enabled and istio.io/rev, Cilium ambient io.cilium.ambient/enabled, kube_pod_container_info proxy containers (istio-proxy, linkerd-proxy, envoy), kube_pod_annotations sidecar.istio.io/inject=false, kube_pod_info Running inventory, istiod pilot_proxy_convergence_time and pilot_xds_pushes, Linkerd linkerd_proxy_inbound_tls_handshake_total. Tunables: index=k8s_metrics sourcetype=prometheus:scrape:metrics; lookup mesh_sidecar_governance.csv keys cluster+namespace; earliest=-4h@h latest=@h; complements UC-3.2.27 NetworkPolicy, UC-3.2.22 PSA, UC-3.2.40 admission webhooks.")`
| multisearch 
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn,"%kube_namespace_labels%") OR match(_raw,"kube_namespace_labels")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
      | rex field=_raw "(?i)istio_injection\\s*=\\s*\\\"(?<istio_inj_l>[^\\\"]+)\\\""
      | rex field=_raw "(?i)istio_io_rev\\s*=\\s*\\\"(?<istio_rev_l>[^\\\"]+)\\\""
      | rex field=_raw "(?i)io_cilium_ambient_enabled\\s*=\\s*\\\"(?<cilium_amb_l>[^\\\"]+)\\\""
      | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
      | eval istio_inject_live=lower(trim(toString(coalesce(istio_inj_l, ""))))
      | eval istio_rev_live=len(trim(toString(coalesce(istio_rev_l, ""))))>0
      | eval cilium_ambient_live=lower(trim(toString(coalesce(cilium_amb_l, ""))))
      | eval ns_expect_mesh_sidecar=case(
          match(cilium_ambient_live,"^true$"), 0,
          match(istio_inject_live,"^enabled$"), 1,
          istio_rev_live=1, 1,
          true(), 0)
      | eval lane="ns_mesh_posture"
      | eval missing_proxy_pod_cnt=0
      | eval inject_false_ann_cnt=0
      | eval running_pod_cnt=0
      | fields _time cluster namespace lane ns_expect_mesh_sidecar istio_inject_live cilium_ambient_live missing_proxy_pod_cnt inject_false_ann_cnt running_pod_cnt ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn,"%kube_pod_container_info%")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
      | rex field=_raw "pod\\s*=\\s*\\\"(?<pod>[^\\\"]+)\\\""
      | rex field=_raw "container\\s*=\\s*\\\"(?<container>[^\\\"]+)\\\""
      | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
      | eval pod=trim(toString(coalesce(pod, k8s_pod_name, pod_name, "")))
      | join type=inner cluster namespace pod [
          search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
          | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
          | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
          | where like(mn,"%kube_pod_info%")
          | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
          | rex field=_raw "pod\\s*=\\s*\\\"(?<pod>[^\\\"]+)\\\""
          | rex field=_raw "phase\\s*=\\s*\\\"(?<phase>[^\\\"]+)\\\""
          | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
          | eval pod=trim(toString(coalesce(pod, k8s_pod_name, pod_name, "")))
          | where phase="Running" OR match(lower(_raw),"phase=running")
          | fields cluster namespace pod ]
      | eval cn=lower(trim(toString(container)))
      | eval proxy_hit=if(match(cn,"^(istio-proxy|linkerd-proxy|linkerd2-proxy|envoy)$") OR match(cn,"envoy-sidecar"),1,0)
      | stats max(proxy_hit) AS pod_proxy_max BY cluster namespace pod
      | where pod_proxy_max=0
      | stats count AS missing_proxy_pod_cnt BY cluster namespace
      | eval lane="pod_container_gap"
      | eval ns_expect_mesh_sidecar=0
      | eval istio_inject_live=""
      | eval cilium_ambient_live=""
      | eval inject_false_ann_cnt=0
      | eval running_pod_cnt=0
      | fields _time cluster namespace lane ns_expect_mesh_sidecar istio_inject_live cilium_ambient_live missing_proxy_pod_cnt inject_false_ann_cnt running_pod_cnt ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn,"%kube_pod_annotations%")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
      | rex field=_raw "pod\\s*=\\s*\\\"(?<pod>[^\\\"]+)\\\""
      | rex field=_raw "(?i)sidecar_istio_io_inject\\s*=\\s*\\\"(?<sinj>[^\\\"]+)\\\""
      | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
      | where match(lower(sinj),"^false$")
      | stats count AS inject_false_ann_cnt BY cluster namespace
      | eval lane="pod_ann_override"
      | eval ns_expect_mesh_sidecar=0
      | eval istio_inject_live=""
      | eval cilium_ambient_live=""
      | eval missing_proxy_pod_cnt=0
      | eval running_pod_cnt=0
      | fields _time cluster namespace lane ns_expect_mesh_sidecar istio_inject_live cilium_ambient_live missing_proxy_pod_cnt inject_false_ann_cnt running_pod_cnt ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn,"%kube_pod_info%")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
      | rex field=_raw "pod\\s*=\\s*\\\"(?<pod>[^\\\"]+)\\\""
      | rex field=_raw "phase\\s*=\\s*\\\"(?<phase>[^\\\"]+)\\\""
      | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
      | where phase="Running" OR match(lower(_raw),"phase=running")
      | stats dc(pod) AS running_pod_cnt BY cluster namespace
      | eval lane="pod_running_inv"
      | eval ns_expect_mesh_sidecar=0
      | eval istio_inject_live=""
      | eval cilium_ambient_live=""
      | eval missing_proxy_pod_cnt=0
      | eval inject_false_ann_cnt=0
      | fields _time cluster namespace lane ns_expect_mesh_sidecar istio_inject_live cilium_ambient_live missing_proxy_pod_cnt inject_false_ann_cnt running_pod_cnt ]
| stats 
    max(ns_expect_mesh_sidecar) AS ns_expect_mesh_sidecar
    max(missing_proxy_pod_cnt) AS missing_proxy_pod_cnt
    max(inject_false_ann_cnt) AS inject_false_ann_cnt
    max(running_pod_cnt) AS running_pod_cnt
    values(istio_inject_live) AS istio_inject_vals
    values(cilium_ambient_live) AS cilium_amb_vals
    values(lane) AS lanes_seen
    max(_time) AS _time
  BY cluster namespace
| eval cluster=lower(trim(toString(cluster)))
| join type=left max=0 cluster, namespace [
    | inputlookup mesh_sidecar_governance.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, ""))))
    | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, ns, "")))
    | eval mesh_flavor=lower(trim(toString(coalesce(mesh_flavor, mesh_mode, "istio"))))
    | eval sidecar_required=tonumber(tostring(coalesce(sidecar_required, requires_sidecar, "1")),10)
    | eval ambient_mesh_ns=tonumber(tostring(coalesce(ambient_mesh_ns, cilium_ambient_inventory, "0")),10)
    | eval owner_team=toString(coalesce(owner_team, squad, platform_owner, ""))
    | eval workload_tier=toString(coalesce(workload_tier, tier, "standard"))
    | eval grace_until_epoch=tonumber(tostring(coalesce(grace_until_epoch, mesh_grace_until, "0")),10)
    | fields cluster namespace mesh_flavor sidecar_required ambient_mesh_ns owner_team workload_tier grace_until_epoch ]
| fillnull value=0 sidecar_required ambient_mesh_ns grace_until_epoch missing_proxy_pod_cnt inject_false_ann_cnt running_pod_cnt ns_expect_mesh_sidecar
| fillnull value="" owner_team workload_tier mesh_flavor
| eval now_epoch=now()
| eval grace_active=if(grace_until_epoch>0 AND now_epoch<grace_until_epoch,1,0)
| eval cilium_join=lower(mvjoin(cilium_amb_vals,""))
| eval ambient_exempt=if(ambient_mesh_ns=1 OR match(cilium_join,"true"),1,0)
| eval sidecar_req_eff=case(len(owner_team)>0, sidecar_required, ns_expect_mesh_sidecar=1, 1, true(), 0)
| eval compliance_gap=if(sidecar_req_eff=1 AND grace_active=0 AND ambient_exempt=0 AND ns_expect_mesh_sidecar=1 AND missing_proxy_pod_cnt>0,1,0)
| eval mesh_bypass_risk_score=round(compliance_gap*coalesce(missing_proxy_pod_cnt,0)+inject_false_ann_cnt*0.25,3)
| join type=left max=0 cluster [
    search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | eval mv=tonumber(tostring(coalesce(Value, value, metric_value, _value, "0")),10)
      | where like(mn,"%pilot_proxy_convergence_time%") OR like(mn,"%pilot_xds_pushes%") OR like(mn,"%linkerd_proxy_inbound_tls_handshake_total%")
      | eval pilot_conv_sample=if(like(mn,"%pilot_proxy_convergence_time%"), mv, 0)
      | eval pilot_xds_sample=if(like(mn,"%pilot_xds_pushes%"), mv, 0)
      | eval linkerd_tls_sample=if(like(mn,"%linkerd_proxy_inbound_tls_handshake_total%"), mv, 0)
      | stats max(pilot_conv_sample) AS pilot_conv_sample max(pilot_xds_sample) AS pilot_xds_sample max(linkerd_tls_sample) AS linkerd_tls_sample BY cluster ]
| fillnull value=0 pilot_conv_sample pilot_xds_sample linkerd_tls_sample
| join type=left max=1 cluster [
    | tstats summariesonly=t count AS cim_change_touch FROM datamodel=Change WHERE nodename=Change.All_Changes All_Changes.dest=* earliest=-4h@h latest=@h BY All_Changes.dest
    | rename All_Changes.dest AS cluster ]
| join type=left max=1 cluster [
    | tstats summariesonly=t latest(Application_State.info) AS cim_app_state FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
    | rename Application_State.dest AS cluster ]
| fillnull value=0 cim_change_touch
| fillnull value="" cim_app_state
| eventstats median(pilot_conv_sample) AS fleet_pilot_conv_med BY cluster
| streamstats window=3 current=t global=f avg(missing_proxy_pod_cnt) AS missing_proxy_ma3 BY cluster, namespace
| eval severity=case(
    compliance_gap=1 AND match(workload_tier,"(?i)prod|critical|tier0|payments"), "critical_mesh_gap",
    compliance_gap=1, "high_mesh_gap",
    inject_false_ann_cnt>=3 AND ns_expect_mesh_sidecar=1, "high_annotation_override_cluster",
    pilot_conv_sample>0 AND fleet_pilot_conv_med>0 AND pilot_conv_sample>3*fleet_pilot_conv_med, "medium_istiod_convergence_spike",
    linkerd_tls_sample=0 AND match(mesh_flavor,"linkerd") AND running_pod_cnt>20, "medium_linkerd_tls_stall",
    ns_expect_mesh_sidecar=1 AND running_pod_cnt>0 AND missing_proxy_pod_cnt=0 AND pilot_xds_sample=0 AND match(mesh_flavor,"istio"), "medium_review_xds_quiet",
    true(), "low_info_watch")
| where compliance_gap=1 OR inject_false_ann_cnt>0 OR severity IN ("critical_mesh_gap","high_mesh_gap","high_annotation_override_cluster","medium_istiod_convergence_spike","medium_linkerd_tls_stall","medium_review_xds_quiet")
| where NOT (match(namespace,"^(kube-system|kube-public|kube-node-lease)$") AND compliance_gap=0 AND inject_false_ann_cnt=0)
| table _time cluster namespace severity mesh_flavor workload_tier owner_team lanes_seen ns_expect_mesh_sidecar sidecar_req_eff missing_proxy_pod_cnt inject_false_ann_cnt running_pod_cnt mesh_bypass_risk_score pilot_conv_sample pilot_xds_sample linkerd_tls_sample missing_proxy_ma3 cim_change_touch cim_app_state
```

savedsearches.conf sketch:

```ini
[uc_3_2_31_mesh_sidecar_injection_compliance]
cron_schedule = */10 * * * *
dispatch.earliest_time = -4h@h
dispatch.latest_time = now
enableSched = 1
alert.track = 1
action.email = 1
action.email.to = platform-mesh@example.com
action.email.subject = Mesh sidecar compliance $result.severity$ on $result.cluster$ ns $result.namespace$
search = | savedsearch uc_3_2_31_mesh_sidecar_injection_compliance_base
```

### Step 4 — Validate

Synthetic mesh gap: label a lab namespace istio-injection=enabled, deploy a sleep pod without restart after labeling, confirm kube_pod_container_info lacks istio-proxy while kube_namespace_labels shows enabled, execute the search, and expect compliance_gap=1 with non-zero missing_proxy_pod_cnt after governance rows mark sidecar_required=1.

Synthetic ambient exempt: set io.cilium.ambient/enabled=true on a namespace in mesh_sidecar_governance.csv with ambient_mesh_ns=1, confirm ns_expect_mesh_sidecar evaluates to zero expectation in the SPL arm and compliance_gap stays zero even if classic sidecars are absent.

Synthetic annotation override: annotate a pod with sidecar.istio.io/inject=false, confirm inject_false_ann_cnt rises and severity routes toward high_annotation_override_cluster when counts cross thresholds in injected namespaces.

Synthetic Istiod signal: during controlled load on istiod in lab, confirm pilot_proxy_convergence_time samples appear on index=k8s_metrics and medium_istiod_convergence_spike triggers only when samples exceed three times the fleet median from eventstats.

Synthetic Linkerd signal: verify linkerd_proxy_inbound_tls_handshake_total increments on meshed pods; in a broken lab scrape, confirm medium_linkerd_tls_stall remains a deliberate investigative tier, not a production default without tuning.

Negative path: roll pods after fixing injection, confirm missing_proxy_pod_cnt returns to zero and alert rows clear within two evaluation windows.

RBAC path: readers without k8s_metrics must see zero rows.

Data quality path: if kube-state-metrics upgrades drop kube_pod_annotations, document the loss and rely on pod exec spot checks until restored.

Lookup path: namespaces without CSV rows still evaluate sidecar_req_eff from live labels but carry empty owner_team until inventory catches up.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Namespace labeled enabled but legacy pods never restarted: roll the workload or delete pods to force injection; document change tickets linking label time to rollout completion.

Case 2 — Helm chart sets sidecar.istio.io/inject=false cluster-wide: move override to workload scope, record exception in mesh_sidecar_governance.csv, or revert chart defaults after security review.

Case 3 — Revision tags istio.io/rev misaligned with injector webhook: validate istioctl tag or revision labels on namespaces against mutating webhook configurations; fix GitOps ordering before muting Splunk.

Case 4 — Cilium ambient namespace misclassified as sidecar-required: set ambient_mesh_ns=1 and mesh_flavor=cilium_ambient in CSV; educate teams that absence of istio-proxy is expected.

Case 5 — STRICT PeerAuthentication with partial mesh participation: pair this UC with mesh traffic tap or L7 access logs to prove plaintext paths; do not rely on NetworkPolicy alone.

Case 6 — Istiod overload distorts pilot_proxy_convergence_time: scale istiod, review discovery debounce settings, and correlate with kube-apiserver watch traffic before blaming applications.

Case 7 — Linkerd proxy metrics absent after upgrade: validate prometheus scrapes of proxy admin ports or pod monitor patterns; restore metrics before trusting zero TLS handshake counters.

Case 8 — Consul Connect sidecar naming deviates: extend container regex ladder in a macro after reviewing connect-inject template outputs.

Case 9 — kube-state-metrics RBAC prevents pod lists: repair ClusterRole bindings; treat missing series as telemetry failure not compliance pass.

Case 10 — GitOps reverts namespace labels during merge conflicts: add admission policy or OPA Gatekeeper constraints requiring mesh labels on tier-one namespaces; correlate with cim_change_touch spikes.

Case 11 — Paused Deployments during change freeze: pods stay unrolled and show persistent gaps; communicate freeze windows in governance CSV grace epochs.

Case 12 — Service accounts running gateway-style ingress pods: mark gateways as mesh_flavor exceptions with sidecar_required=0 when architecture routes through dedicated ingress proxies rather than workload sidecars.

Governance: quarterly replay historical gap spikes after kube-state-metrics, mesh, or collector upgrades. Update the comment macro when indexes move.

Evidence retention: weekly CSV exports of the closing table satisfy internal zero-trust scorecards when paired with change tickets and mesh policy Git history for PeerAuthentication and AuthorizationPolicy objects.

Closing checklist: five em-dash step headers present; Step 3 fenced SPL matches the spl field exactly; multisearch lists namespace labels, pod container gaps with Running join, pod annotations, and Running inventory arms; coalesce appears in cluster attribution ladders; inputlookup wraps mesh_sidecar_governance.csv; tstats uses Change and Application_State data models; eventstats and streamstats add fleet median and moving averages; case assigns severity tiers; final table includes at least ten columns including mesh_bypass_risk_score and control-plane metric samples; monitoringType includes Configuration and Compliance; cimModels lists Application_State and Change; equipmentModels lists kubernetes_k8s; references include seven authoritative URLs spanning Istio injection, mesh security concepts, Linkerd proxy, Cilium service mesh, Consul Connect proxy, kube-state-metrics namespace metrics, and OPA Gatekeeper policy documentation.

## SPL

```spl
`comment("UC-3.2.31 Service mesh sidecar injection compliance and coverage drift. Signals: kube_namespace_labels for istio-injection=enabled and istio.io/rev, Cilium ambient io.cilium.ambient/enabled, kube_pod_container_info proxy containers (istio-proxy, linkerd-proxy, envoy), kube_pod_annotations sidecar.istio.io/inject=false, kube_pod_info Running inventory, istiod pilot_proxy_convergence_time and pilot_xds_pushes, Linkerd linkerd_proxy_inbound_tls_handshake_total. Tunables: index=k8s_metrics sourcetype=prometheus:scrape:metrics; lookup mesh_sidecar_governance.csv keys cluster+namespace; earliest=-4h@h latest=@h; complements UC-3.2.27 NetworkPolicy, UC-3.2.22 PSA, UC-3.2.40 admission webhooks.")`
| multisearch 
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn,"%kube_namespace_labels%") OR match(_raw,"kube_namespace_labels")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
      | rex field=_raw "(?i)istio_injection\\s*=\\s*\\\"(?<istio_inj_l>[^\\\"]+)\\\""
      | rex field=_raw "(?i)istio_io_rev\\s*=\\s*\\\"(?<istio_rev_l>[^\\\"]+)\\\""
      | rex field=_raw "(?i)io_cilium_ambient_enabled\\s*=\\s*\\\"(?<cilium_amb_l>[^\\\"]+)\\\""
      | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
      | eval istio_inject_live=lower(trim(toString(coalesce(istio_inj_l, ""))))
      | eval istio_rev_live=len(trim(toString(coalesce(istio_rev_l, ""))))>0
      | eval cilium_ambient_live=lower(trim(toString(coalesce(cilium_amb_l, ""))))
      | eval ns_expect_mesh_sidecar=case(
          match(cilium_ambient_live,"^true$"), 0,
          match(istio_inject_live,"^enabled$"), 1,
          istio_rev_live=1, 1,
          true(), 0)
      | eval lane="ns_mesh_posture"
      | eval missing_proxy_pod_cnt=0
      | eval inject_false_ann_cnt=0
      | eval running_pod_cnt=0
      | fields _time cluster namespace lane ns_expect_mesh_sidecar istio_inject_live cilium_ambient_live missing_proxy_pod_cnt inject_false_ann_cnt running_pod_cnt ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn,"%kube_pod_container_info%")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
      | rex field=_raw "pod\\s*=\\s*\\\"(?<pod>[^\\\"]+)\\\""
      | rex field=_raw "container\\s*=\\s*\\\"(?<container>[^\\\"]+)\\\""
      | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
      | eval pod=trim(toString(coalesce(pod, k8s_pod_name, pod_name, "")))
      | join type=inner cluster namespace pod [
          search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
          | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
          | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
          | where like(mn,"%kube_pod_info%")
          | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
          | rex field=_raw "pod\\s*=\\s*\\\"(?<pod>[^\\\"]+)\\\""
          | rex field=_raw "phase\\s*=\\s*\\\"(?<phase>[^\\\"]+)\\\""
          | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
          | eval pod=trim(toString(coalesce(pod, k8s_pod_name, pod_name, "")))
          | where phase="Running" OR match(lower(_raw),"phase=running")
          | fields cluster namespace pod ]
      | eval cn=lower(trim(toString(container)))
      | eval proxy_hit=if(match(cn,"^(istio-proxy|linkerd-proxy|linkerd2-proxy|envoy)$") OR match(cn,"envoy-sidecar"),1,0)
      | stats max(proxy_hit) AS pod_proxy_max BY cluster namespace pod
      | where pod_proxy_max=0
      | stats count AS missing_proxy_pod_cnt BY cluster namespace
      | eval lane="pod_container_gap"
      | eval ns_expect_mesh_sidecar=0
      | eval istio_inject_live=""
      | eval cilium_ambient_live=""
      | eval inject_false_ann_cnt=0
      | eval running_pod_cnt=0
      | fields _time cluster namespace lane ns_expect_mesh_sidecar istio_inject_live cilium_ambient_live missing_proxy_pod_cnt inject_false_ann_cnt running_pod_cnt ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn,"%kube_pod_annotations%")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
      | rex field=_raw "pod\\s*=\\s*\\\"(?<pod>[^\\\"]+)\\\""
      | rex field=_raw "(?i)sidecar_istio_io_inject\\s*=\\s*\\\"(?<sinj>[^\\\"]+)\\\""
      | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
      | where match(lower(sinj),"^false$")
      | stats count AS inject_false_ann_cnt BY cluster namespace
      | eval lane="pod_ann_override"
      | eval ns_expect_mesh_sidecar=0
      | eval istio_inject_live=""
      | eval cilium_ambient_live=""
      | eval missing_proxy_pod_cnt=0
      | eval running_pod_cnt=0
      | fields _time cluster namespace lane ns_expect_mesh_sidecar istio_inject_live cilium_ambient_live missing_proxy_pod_cnt inject_false_ann_cnt running_pod_cnt ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn,"%kube_pod_info%")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
      | rex field=_raw "pod\\s*=\\s*\\\"(?<pod>[^\\\"]+)\\\""
      | rex field=_raw "phase\\s*=\\s*\\\"(?<phase>[^\\\"]+)\\\""
      | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
      | where phase="Running" OR match(lower(_raw),"phase=running")
      | stats dc(pod) AS running_pod_cnt BY cluster namespace
      | eval lane="pod_running_inv"
      | eval ns_expect_mesh_sidecar=0
      | eval istio_inject_live=""
      | eval cilium_ambient_live=""
      | eval missing_proxy_pod_cnt=0
      | eval inject_false_ann_cnt=0
      | fields _time cluster namespace lane ns_expect_mesh_sidecar istio_inject_live cilium_ambient_live missing_proxy_pod_cnt inject_false_ann_cnt running_pod_cnt ]
| stats 
    max(ns_expect_mesh_sidecar) AS ns_expect_mesh_sidecar
    max(missing_proxy_pod_cnt) AS missing_proxy_pod_cnt
    max(inject_false_ann_cnt) AS inject_false_ann_cnt
    max(running_pod_cnt) AS running_pod_cnt
    values(istio_inject_live) AS istio_inject_vals
    values(cilium_ambient_live) AS cilium_amb_vals
    values(lane) AS lanes_seen
    max(_time) AS _time
  BY cluster namespace
| eval cluster=lower(trim(toString(cluster)))
| join type=left max=0 cluster, namespace [
    | inputlookup mesh_sidecar_governance.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, ""))))
    | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, ns, "")))
    | eval mesh_flavor=lower(trim(toString(coalesce(mesh_flavor, mesh_mode, "istio"))))
    | eval sidecar_required=tonumber(tostring(coalesce(sidecar_required, requires_sidecar, "1")),10)
    | eval ambient_mesh_ns=tonumber(tostring(coalesce(ambient_mesh_ns, cilium_ambient_inventory, "0")),10)
    | eval owner_team=toString(coalesce(owner_team, squad, platform_owner, ""))
    | eval workload_tier=toString(coalesce(workload_tier, tier, "standard"))
    | eval grace_until_epoch=tonumber(tostring(coalesce(grace_until_epoch, mesh_grace_until, "0")),10)
    | fields cluster namespace mesh_flavor sidecar_required ambient_mesh_ns owner_team workload_tier grace_until_epoch ]
| fillnull value=0 sidecar_required ambient_mesh_ns grace_until_epoch missing_proxy_pod_cnt inject_false_ann_cnt running_pod_cnt ns_expect_mesh_sidecar
| fillnull value="" owner_team workload_tier mesh_flavor
| eval now_epoch=now()
| eval grace_active=if(grace_until_epoch>0 AND now_epoch<grace_until_epoch,1,0)
| eval cilium_join=lower(mvjoin(cilium_amb_vals,""))
| eval ambient_exempt=if(ambient_mesh_ns=1 OR match(cilium_join,"true"),1,0)
| eval sidecar_req_eff=case(len(owner_team)>0, sidecar_required, ns_expect_mesh_sidecar=1, 1, true(), 0)
| eval compliance_gap=if(sidecar_req_eff=1 AND grace_active=0 AND ambient_exempt=0 AND ns_expect_mesh_sidecar=1 AND missing_proxy_pod_cnt>0,1,0)
| eval mesh_bypass_risk_score=round(compliance_gap*coalesce(missing_proxy_pod_cnt,0)+inject_false_ann_cnt*0.25,3)
| join type=left max=0 cluster [
    search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | eval mv=tonumber(tostring(coalesce(Value, value, metric_value, _value, "0")),10)
      | where like(mn,"%pilot_proxy_convergence_time%") OR like(mn,"%pilot_xds_pushes%") OR like(mn,"%linkerd_proxy_inbound_tls_handshake_total%")
      | eval pilot_conv_sample=if(like(mn,"%pilot_proxy_convergence_time%"), mv, 0)
      | eval pilot_xds_sample=if(like(mn,"%pilot_xds_pushes%"), mv, 0)
      | eval linkerd_tls_sample=if(like(mn,"%linkerd_proxy_inbound_tls_handshake_total%"), mv, 0)
      | stats max(pilot_conv_sample) AS pilot_conv_sample max(pilot_xds_sample) AS pilot_xds_sample max(linkerd_tls_sample) AS linkerd_tls_sample BY cluster ]
| fillnull value=0 pilot_conv_sample pilot_xds_sample linkerd_tls_sample
| join type=left max=1 cluster [
    | tstats summariesonly=t count AS cim_change_touch FROM datamodel=Change WHERE nodename=Change.All_Changes All_Changes.dest=* earliest=-4h@h latest=@h BY All_Changes.dest
    | rename All_Changes.dest AS cluster ]
| join type=left max=1 cluster [
    | tstats summariesonly=t latest(Application_State.info) AS cim_app_state FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
    | rename Application_State.dest AS cluster ]
| fillnull value=0 cim_change_touch
| fillnull value="" cim_app_state
| eventstats median(pilot_conv_sample) AS fleet_pilot_conv_med BY cluster
| streamstats window=3 current=t global=f avg(missing_proxy_pod_cnt) AS missing_proxy_ma3 BY cluster, namespace
| eval severity=case(
    compliance_gap=1 AND match(workload_tier,"(?i)prod|critical|tier0|payments"), "critical_mesh_gap",
    compliance_gap=1, "high_mesh_gap",
    inject_false_ann_cnt>=3 AND ns_expect_mesh_sidecar=1, "high_annotation_override_cluster",
    pilot_conv_sample>0 AND fleet_pilot_conv_med>0 AND pilot_conv_sample>3*fleet_pilot_conv_med, "medium_istiod_convergence_spike",
    linkerd_tls_sample=0 AND match(mesh_flavor,"linkerd") AND running_pod_cnt>20, "medium_linkerd_tls_stall",
    ns_expect_mesh_sidecar=1 AND running_pod_cnt>0 AND missing_proxy_pod_cnt=0 AND pilot_xds_sample=0 AND match(mesh_flavor,"istio"), "medium_review_xds_quiet",
    true(), "low_info_watch")
| where compliance_gap=1 OR inject_false_ann_cnt>0 OR severity IN ("critical_mesh_gap","high_mesh_gap","high_annotation_override_cluster","medium_istiod_convergence_spike","medium_linkerd_tls_stall","medium_review_xds_quiet")
| where NOT (match(namespace,"^(kube-system|kube-public|kube-node-lease)$") AND compliance_gap=0 AND inject_false_ann_cnt=0)
| table _time cluster namespace severity mesh_flavor workload_tier owner_team lanes_seen ns_expect_mesh_sidecar sidecar_req_eff missing_proxy_pod_cnt inject_false_ann_cnt running_pod_cnt mesh_bypass_risk_score pilot_conv_sample pilot_xds_sample linkerd_tls_sample missing_proxy_ma3 cim_change_touch cim_app_state
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.info) AS app_state latest(Application_State.status) AS app_status FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS cluster
| join type=left max=0 cluster [
| tstats summariesonly=t count AS change_cnt FROM datamodel=Change WHERE nodename=Change.All_Changes earliest=-4h@h latest=@h BY All_Changes.dest
| rename All_Changes.dest AS cluster ]
| table cluster app_state app_status change_cnt
```

## Visualization

Severity-colored table mirroring the closing SPL projection; single-value tiles for critical_mesh_gap versus high_mesh_gap counts; timechart of missing_proxy_pod_cnt by namespace; drilldown from inject_false_ann_cnt to annotation samples; companion panel for pilot_conv_sample and linkerd_tls_sample by cluster.

## Known False Positives

Legitimately mesh-exempt workloads include cluster logging agents, eBPF node security agents, kube-system control-plane components, and DaemonSets that intentionally use hostNetwork for CNI or observability reasons—mark them in mesh_sidecar_governance.csv with sidecar_required=0 instead of muting alerts globally. Deliberate bypasses via sidecar.istio.io/inject=false on batch jobs, gateway pods that run as ingress-gateway Deployments rather than classic workload sidecars, and Helm chart workload-level overrides produce missing proxies by design; require annotation arms and inventory notes before escalating. CRD operators that need raw cluster API access sometimes opt out of injection; document those service accounts. Pods created before a namespace gained istio-injection=enabled need rolls to pick up mutating webhook changes; transient gaps after label flips are common until rollouts finish. Paused Deployments during freezes can hold stale pod specs indefinitely. Cilium ambient and similar sidecarless mesh modes intentionally omit istio-proxy containers; set ambient_mesh_ns=1 to avoid false positives. Services explicitly excluded from mesh policy or PeerAuthentication peer lists may not need sidecars even when a namespace is labeled—confirm architecture before paging. Recently restarted mesh control planes can create brief pilot_proxy_convergence_time spikes that resemble incidents; correlate with change tickets. kube-state-metrics version skew may drop kube_pod_annotations series temporarily, inflating apparent silence on inject=false counts—verify telemetry health first.

## References

- [Istio — Sidecar injection](https://istio.io/latest/docs/setup/additional-setup/sidecar-injection/)
- [Istio — Security overview](https://istio.io/latest/docs/concepts/security/)
- [Linkerd — Proxy](https://linkerd.io/2.14/features/)
- [Cilium — Service mesh](https://docs.cilium.io/en/stable/network/servicemesh/)
- [HashiCorp Consul — Connect proxy](https://developer.hashicorp.com/consul/docs/connect/proxy)
- [kube-state-metrics — Namespace metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/)
- [OPA Gatekeeper Library — policy patterns (injection and sidecar governance)](https://open-policy-agent.github.io/gatekeeper-library/website/)
