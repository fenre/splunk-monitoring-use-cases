<!-- AUTO-GENERATED from UC-3.3.12.json — DO NOT EDIT -->

---
id: "3.3.12"
title: "OpenShift Network Operator and OVN-Kubernetes Cluster Network Health"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.12 · OpenShift Network Operator and OVN-Kubernetes Cluster Network Health

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the internal networking fabric that lets pods talk to each other across your OpenShift cluster. When that fabric’s control software struggles or IP assignment breaks, apps fail in confusing ways even when the front door still works, so we raise a clear signal for the networking team to fix it.*

---

## Description

Detects degradation of the OpenShift cluster network control plane and OVN-Kubernetes data plane by correlating the network ClusterOperator conditions, Network.config.openshift.io observed networkType and migration fields, openshift-ovn-kubernetes ovnkube DaemonSet restart pressure, Kubernetes sandbox and CNI failure events, EgressIP and EgressFirewall assignment failures, AdminNetworkPolicy drift hints, openshift-network-diagnostics synthetic probe failures, and optional ovn_controller, ovnkube_master, ovsdb_jsonrpc, and network_check Prometheus metrics when federated into Splunk.

## Value

Platform and application leaders shorten mean time to innocence when east-west pod traffic fails while the web console still loads, because those symptoms often trace to the cluster network operator and OVN-K overlay rather than ingress edges or DNS alone. Splunk preserves a reconciled ledger across API snapshots, events, egress objects, admin-tier policy exports, and metrics so executives see continuous stewardship of the shared pod network during upgrades, SDN migrations, and cloud networking changes.

## Implementation

Land ocp_clusteroperator snapshots with network rows, ocp_network_config, ocp_ovnkube, ocp_egressip, ocp_egressfirewall, ocp_adminnetworkpolicy, ocp_events or k8s_events for CNI reasons, optional ocp_network_diagnostics, and prometheus ovn lines into governed indexes with cluster labels; normalize fields in props; save openshift_uc_33312_ovnk_cluster_network_health on ten to fifteen minute cadence over earliest=-6h@h; route page and warn to platform networking on-call; archive weekly CSV for stewardship reviews.

## Evidence

Saved search openshift_uc_33312_ovnk_cluster_network_health with ten to fifteen minute schedule; Splunk OpenShift App drilldowns on ocp_clusteroperator network rows, ocp_network_config, ocp_ovnkube, egress and admin policy exports, events, diagnostics, and prometheus ovn samples; alert stanza with platform networking routing keys; weekly CSV exports to a restricted evidence index.

## Control test

### Positive scenario

In a lab OpenShift cluster on OVN-Kubernetes, ingest ocp_clusteroperator rows where network reports Degraded=True with message text referencing ovn-kubernetes, add matching ocp_ovnkube restart totals and ocp_events FailedCreatePodSandBox samples, optionally add prometheus ovn_controller drop counters, execute openshift_uc_33312_ovnk_cluster_network_health, and confirm page or warn severity with non-null recommended_action within the scheduled window.

### Negative scenario

After recovery when oc get clusteroperator network shows Available=True, Progressing=False, Degraded=False, openshift-ovn-kubernetes Pods are stable, sandbox event rates return to baseline, and diagnostics Pods succeed, confirm severities return to info and the alert wrapper emits zero rows when filtering to page and warn only.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with the OpenShift platform networking lead, the cluster network engineering team that operates the cluster-network-operator and openshift-ovn-kubernetes namespace, and the observability engineers who steward Splunk HTTP Event Collector tokens plus OpenTelemetry Collector agents that federate in-cluster Prometheus from OpenShift Monitoring. This use case isolates the OpenShift cluster-wide pod network plane managed by the network ClusterOperator in group operator.openshift.io: the ClusterOperator object named network whose Available, Progressing, and Degraded conditions summarize reconciliation of Network.config.openshift.io cluster defaults, migration state between OpenShiftSDN and OVNKubernetes plugins, and the health of OVN northbound and southbound database planes, ovnkube control components, and Geneve overlay tunnels between nodes. UC-3.3.6 remains generic ClusterOperator ledger analytics across roughly thirty operators without the specialized field lens, Prometheus joins, and openshift-ovn-kubernetes DaemonSet semantics that this document requires. UC-3.3.9 remains the IngressController and HAProxy north-south edge that publishes Routes to clients outside the cluster, not east-west pod IP connectivity. UC-3.3.14 remains OAuth and identity provider flow failures on openshift-authentication. UC-3.2.27 remains Kubernetes NetworkPolicy admission and default-deny compliance auditing at the API admission layer, not the health of the CNI data plane or the network operator reconcile loop. UC-3.2.34 remains CoreDNS and cluster DNS resolution, which can mask as application failures when broken but is intentionally out of scope for overlay tunnel, IPAM, and OVN database narrative here. UC-3.3.17 remains MachineConfigPool and node configuration timelines driven by the Machine Configuration Operator, including CRI-O settings, kernel arguments, and Ignition apply batches, which may correlate with node reboots but do not replace monitoring of ovnkube-node readiness on the pod network.

Operational scope emphasizes three API surfaces plus emitted telemetry. First, ClusterOperator network status conditions with per-condition reason and message strings that cite ovn-kubernetes, openshift-sdn migration, IP pool exhaustion, iptables or nftables sync, and multus attachment order when documented for your minor version. Second, the cluster-scoped Network CR in config.openshift.io that declares observed networkType values such as OVNKubernetes versus OpenShiftSDN, clusterNetwork and serviceNetwork CIDR observations, and migrationStatus fields during live migration projects. Third, workloads in openshift-ovn-kubernetes including DaemonSets ovnkube-master, ovnkube-node, and ovnkube-cluster-manager on supported layouts, their container restart counts, leader election labels on ovnkube-master, and logs referencing ovsdb-server, ovn-northd, northbound and southbound database connectivity. Fourth, OpenShift-specific policy objects including EgressIP in k8s.ovn.org or legacy forms your exporter preserves, EgressFirewall in k8s.ovn.org for namespace-scoped egress rules, EgressService when enabled, AdminNetworkPolicy and BaselineAdminNetworkPolicy for cluster-admin-tier rules enforced by OVN-K, and on legacy OpenShiftSDN estates HostSubnet in network.openshift.io with node subnet annotations compared to k8s.ovn.org node subnet annotations on OVN-K. Fifth, Kubernetes events on workload namespaces with reasons FailedCreatePodSandBox, NetworkNotReady, CNIPluginNotInitialized, IPAMFailure, EgressIPNotAssigned, NodeIPAMNotReady, and user-facing hints such as PathMTUDiscoveryError when MTU mismatches surface through the CNI path. Sixth, openshift-network-diagnostics network-check-source and network-check-target Pods that run synthetic probes and export results your pipeline maps into Splunk. Seventh, optional Prometheus series including ovn_controller metrics that expose packet drops, Geneve tunnel statistics, ovsdb jsonrpc error counters when scraped, and ovnkube_master leader or rebuild metrics when your OpenShift Monitoring version publishes them.

Index and permission design precedes field extraction. Designate index=ocp_metrics for sourcetype=ocp_clusteroperator when snapshots include all operators and SPL filters name=network, for sourcetype=ocp_network_config mapping oc get networks.config.openshift.io cluster -o json snapshots, for sourcetype=ocp_ovnkube summarizing per-Pod or per-DaemonSet restart and phase fields from openshift-ovn-kubernetes, for sourcetype=ocp_egressip and sourcetype=ocp_egressfirewall listing assignment and status conditions, for sourcetype=ocp_adminnetworkpolicy summarizing AdminNetworkPolicy object generations versus admission markers your team defines, and for federated prometheus lines with sourcetype=prometheus:metrics carrying ovn_controller, ovnkube, ovsdb, or network_check metric families. Designate index=ocp_events with sourcetype=ocp_events or k8s_events for the Kubernetes events watch stream normalized with reason, involvedObject.kind, involvedObject.namespace, and message. Designate index=ocp_audit with sourcetype=ocp_audit for administrative verbs on networks.config.openshift.io, egressip.k8s.ovn.org, adminnetworkpolicy policies, and operator.openshift.io clusteroperators named network when counsel requires change attribution. Issue distinct HEC tokens per environment. Platform networking staff may search all lanes; application teams receive filtered views. Retention should cover at least fourteen days hot for incident replay on overlay partitions, thirty days for migration forensics, and align with observability policy.

RBAC and safety: exporters that run oc get clusteroperator network or watch Network.config.openshift.io must use a dedicated ServiceAccount with get list on cluster-scoped objects, not long-lived administrator kubeconfig files on employee laptops. Collectors ingesting openshift-ovn-kubernetes Pod lists need get list on pods in that namespace. EgressIP enumeration requires cluster read on egressips.k8s.ovn.org. AdminNetworkPolicy requires read on policies.networking.k8s.io when using the Kubernetes upstream CRDs shipped with OpenShift. When federation pulls Prometheus, bind scrapers to metrics readers rather than cluster administrators.

Field normalization: flatten ClusterOperator network rows into available, progressing, degraded booleans, lastTransitionTime per condition, reason, and message. Flatten Network CR into networkType, clusterNetwork entries, serviceNetwork, and migrationStatus when present. Map ovnkube DaemonSet rows into ds_name, restart totals, and optional leader boolean. Normalize event reasons to a canonical vocabulary. Preserve cluster identity on every event as cluster, openshift_cluster, or cluster_name. coalesce() ladders in SPL absorb exporter renames across minor upgrades.

Risk briefing: Progressing=True on network operator during z-stream upgrades, certificate rotations touching the platform trust bundle, and rolling ovnkube restarts is expected for bounded intervals; dwell thresholds and multisearch corroboration prevent noise. Migration from OpenShiftSDN to OVN-K produces deliberate condition churn and must be annotated with change_ticket_id on HEC payloads. Brief EgressIPNotAssigned events during node drains can clear when reassignment completes. MTU changes and cloud security group edits can look like overlay failures until paths stabilize. Geneve renegotiation after cluster certificate rotation may elevate transient drop counters without sustained operator Degraded status.

Differentiation recap: cluster network operator and OVN-K data plane health, not generic ClusterOperator fleet analytics, not ingress router saturation, not DNS pods alone, not NetworkPolicy admission audits, not MachineConfigPool ledger.

Operational posture: stamp maintenance metadata when cluster administrators run documented migration procedures or adjust networkType. When Splunk shows Geneve drops on one rack only, pair with top-of-rack switch port counters before blaming OVN software. When application teams report east-west timeouts while the console still loads, prioritize this UC over UC-3.3.9 because the symptom pattern points at pod networking rather than Route edges.

### Step 2 — Configure data collection

Stand up multisearch lanes that Splunk can fuse: Network ClusterOperator snapshots filtered to metadata.name network, Network.config.openshift.io snapshots, openshift-ovn-kubernetes Pod or DaemonSet inventory with container restart counters, Kubernetes events filtered to sandbox and CNI reasons, EgressIP status and EgressFirewall status exporters, AdminNetworkPolicy object inventory with optional admission webhook outcome fields when you emit them, HostSubnet snapshots only on OpenShiftSDN estates for drift contrast, optional node annotation snapshots for k8s.ovn.org node subnets on OVN-K, prometheus federation for ovn_controller and ovnkube series, and openshift-network-diagnostics synthetic job outcomes mapped to sourcetype ocp_network_diagnostics or fields inside ocp_events.

ClusterOperator lane: schedule a management utility every two to five minutes to oc get clusteroperator network -o json or watch operator.openshift.io clusteroperators. Emit sourcetype=ocp_clusteroperator events that include metadata.name, generation, observedGeneration, and the full status.conditions array flattened by your parser into fields used by this UC. Include version entries when present so upgrade forensics align with ClusterVersion history without duplicating UC-3.3.1.

Network.config lane: on the same cadence or bundled in one scripted oc get -o json run, export networks.config.openshift.io cluster object with spec and status. Emit sourcetype=ocp_network_config including networkType, serviceNetwork, clusterNetwork CIDR list, and migration fields when your cluster is mid-migration.

OVN-Kube lane: export openshift-ovn-kubernetes Pod lists via oc get pods -n openshift-ovn-kubernetes -o json and compute container restart sums per Pod or aggregate by DaemonSet using ownerReferences. Alternatively ship kube-state-metrics pod container restart counters filtered by namespace openshift-ovn-kubernetes into sourcetype=ocp_ovnkube with stable metric_name mapping. Include pod phase transitions when your exporter preserves them.

Events lane: forward Kubernetes events cluster-wide with reason preserved. Route high-value reasons to a summary index if volume requires. Ensure FailedCreatePodSandBox messages retain CNI stderr substrings when the apiserver stores them so investigators see the same text as oc describe pod without re-querying the cluster during partial outages.

Egress lane: periodically oc get egressip -o json and oc get egressfirewall -A -o json when policy permits. Parse status items assignment conditions and namespace-scoped failure messages into sourcetype=ocp_egressip and ocp_egressfirewall. Include namespace and egressIP name keys for drilldowns.

Admin policy lane: oc get adminnetworkpolicy and oc get baselineadminnetworkpolicy when APIs are enabled, emitting sourcetype=ocp_adminnetworkpolicy with generation, resourceVersion, and optional validator hints from your GitOps diff job when you compute generation_gap or not_enforced heuristics offline.

Diagnostics lane: oc get pods -n openshift-network-diagnostics -o wide and capture log lines or structured check outputs from network-check-source and network-check-target into Splunk. Map failure boolean or error counters into fields network_check_failed and network_check_detail. When diagnostics Pods remain Pending on tainted nodes, record node name and taint keys so Splunk suppressions can exclude known infra-only gaps.

Prometheus lane: verify ServiceMonitors or platform rules expose ovn_controller packet counters, drop counters your version documents, ovsdb_jsonrpc session error class metrics when present, ovnkube_master leader gauge or rebuild histograms, and custom network_check metrics if the diagnostics Pod scrapes locally. Forward with cluster label parity to events.

props.conf guidance: TRUNCATE sufficiently large for JSON snapshots, TIMESTAMP_FIELDS on _time, LINE_BREAKER for multiplexed syslog when needed.

Pre-save validation: after enablement, index=ocp_metrics sourcetype=ocp_clusteroperator must return network rows; openshift-ovn-kubernetes inventory must show non-zero Pod counts on healthy clusters; intentional lab disruption should raise sandbox events in ocp_events within minutes.

Dashboards: Splunk OpenShift App panels should include cluster and severity from this search with drilldowns to ovnkube Pod lists, Network CR JSON, event excerpts, egress statuses, and prometheus metric charts.

Supplemental correlation guidance: when multitenant security teams ask whether AdminNetworkPolicy drift equals a compliance gap, treat Splunk anp_drift_hint as an operational signal that demands oc get adminnetworkpolicy reconciliation on-cluster, not as a substitute for formal policy attestations. For air-gapped clusters, verify mirrored images include ovn-kubernetes and openvswitch containers expected by the release image set before interpreting ImagePull-related network operator messages as overlay bugs. Hybrid cloud estates should align Splunk cluster labels with the same identifiers finance uses for chargeback so executive reviews map spend to incident clusters without manual spreadsheet joins.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_33312_ovnk_cluster_network_health with a ten or fifteen minute schedule, dispatch earliest=-6h@h, dispatch latest=now, and alert when severity is page or warn. Throttle duplicate cluster rows for twenty minutes unless severity escalates. Include recommended_action and net_co_reason in pager bodies so incident commanders open openshift-network-diagnostics and openshift-ovn-kubernetes runbook sections without rerunning ad hoc searches.

Pipeline narrative: multisearch fans ClusterOperator network arm, Network.config arm, ovnkube restart arm, CNI and sandbox event arm, egress assignment failure arm, optional AdminNetworkPolicy drift arm, optional network diagnostics arm, and mstats supplement on ovn_controller and network_check metric names. coalesce() absorbs cluster label drift. streamstats measures short-term progression flips on the network operator. eventstats adds fleet-wide counts of clusters with coordinated degradation. case() maps combined operator Degraded, sustained sandbox failures, egress assignment failures, diagnostics probe failures, and metric spikes into page warn or info tiers.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.12 OVN-K cluster network — network CO, Net.config, ovnkube, CNI events, egress, ANP, diagnostics, ovn mstats. earliest=-6h@h latest=now")`
| multisearch
    [ search ((index=ocp_audit OR index=ocp_events OR index=ocp_metrics) AND sourcetype=ocp_clusteroperator) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval op=lower(trim(toString(coalesce(name, operator, clusteroperator_name, metadata_name, ""))))
      | where match(op,"^network$")
      | eval av=lower(trim(toString(coalesce(available, conditions_available, available_status, ""))))
      | eval pr=lower(trim(toString(coalesce(progressing, conditions_progressing, progressing_status, ""))))
      | eval dg=lower(trim(toString(coalesce(degraded, conditions_degraded, degraded_status, ""))))
      | eval co_avail=if(match(av,"true|1"),1,0)
      | eval co_prog=if(match(pr,"true|1"),1,0)
      | eval co_deg=if(match(dg,"true|1"),1,0)
      | eval co_reason=trim(toString(coalesce(reason, condition_reason, status_reason, "")))
      | eval co_msg=substr(trim(toString(coalesce(message, co_message, condition_message, ""))),1,280)
      | sort 0 + cluster - _time
      | streamstats window=2 current=t global=f last(co_prog) AS prev_prog BY cluster
      | eval prog_flip=if(co_prog==1 AND coalesce(prev_prog,0)==0,1,0)
      | stats latest(_time) AS last_co_t max(co_deg) AS net_co_deg max(co_prog) AS net_co_prog min(co_avail) AS net_co_avail_min sum(eval(coalesce(prog_flip,0))) AS co_prog_flips values(co_reason) AS co_reasons values(co_msg) AS co_msgs BY cluster
      | eval net_co_reason=mvindex(mvdedup(co_reasons),0)
      | eval lane="net_co" ]
    [ search (index=ocp_metrics OR index=ocp_audit) sourcetype=ocp_network_config earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval net_type=upper(trim(toString(coalesce(networkType, network_type, status_networkType, spec_networkType, ""))))
      | eval mig=lower(trim(toString(coalesce(migrationStatus, migration_status, spec_migration_mode, ""))))
      | stats latest(_time) AS last_cfg_t latest(net_type) AS cluster_net_type latest(mig) AS migration_status BY cluster
      | eval lane="net_cfg" ]
    [ search index=ocp_metrics sourcetype=ocp_ovnkube earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval restarts=tonumber(tostring(coalesce(restartCount, container_restarts, restart_total, "0")),10)
      | eval pod=lower(trim(toString(coalesce(pod, pod_name, kubernetes_pod_name, ""))))
      | stats sum(restarts) AS ovn_restart_sum dc(pod) AS ovn_pod_cnt latest(_time) AS last_ovn_t BY cluster
      | eval lane="ovnkube" ]
    [ search (index=ocp_events OR index=ocp_audit) (sourcetype=ocp_events OR sourcetype=k8s_events) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | where rs IN ("FailedCreatePodSandBox","NetworkNotReady","CNIPluginNotInitialized","IPAMFailure","EgressIPNotAssigned","NodeIPAMNotReady") OR match(lower(_raw),"failedcreatepodsandbox|networknotready|cnipluginnotinitialized|ipamfailure|egressipnotassigned|pathmtudiscoveryerror")
      | stats count AS cni_bad_evt count(eval(if(match(rs,"FailedCreatePodSandBox"),1,null()))) AS sandbox_fail count(eval(if(match(rs,"NetworkNotReady|CNIPluginNotInitialized|NodeIPAMNotReady"),1,null()))) AS netready_fail latest(_time) AS last_cni_t BY cluster
      | eval lane="cni_evt" ]
    [ search (index=ocp_metrics OR index=ocp_audit) (sourcetype=ocp_egressip OR sourcetype=ocp_egressfirewall) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval fail_hint=tonumber(tostring(coalesce(assignment_failed, status_failed, not_ready, "0")),10)
      | eval fail_hint=if(isnotnull(fail_hint) AND fail_hint>0,fail_hint,if(match(lower(toString(coalesce(status_phase, phase, ""))),"fail|pending|error"),1,0))
      | stats sum(fail_hint) AS egress_fail_cnt count AS egress_rows latest(_time) AS last_eg_t BY cluster
      | eval lane="egress" ]
    [ search index=ocp_metrics sourcetype=ocp_adminnetworkpolicy earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval drift=tonumber(tostring(coalesce(generation_gap, policy_drift, not_enforced, "0")),10)
      | stats max(drift) AS anp_drift_hint latest(_time) AS last_anp_t BY cluster
      | eval lane="anp" ]
    [ search (index=ocp_events OR index=ocp_metrics) (sourcetype=ocp_events OR sourcetype=ocp_network_diagnostics) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval pod=lower(trim(toString(coalesce(involvedObject_name, pod, pod_name, ""))))
      | eval msg=lower(toString(coalesce(message, Message, "")))
      | where match(pod,"network-check-source|network-check-target") OR match(lower(_raw),"network-check|network_check|synthetic.*probe") OR match(msg,"probe fail|check fail|diagnostics fail")
      | eval diag_hit=1
      | stats sum(diag_hit) AS diag_fail_hint latest(_time) AS last_diag_t BY cluster
      | eval lane="netcheck" ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype="prometheus:ocp") earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where match(mn,"^ovn_controller_|^ovnkube_master_|^ovsdb_jsonrpc_|^network_check_")
      | eval is_drop=if(match(mn,"drop|error|fail"),1,0)
      | stats sum(mv) AS ovn_m_raw sum(eval(if(is_drop==1,mv,0))) AS ovn_drop_like latest(_time) AS last_mstat_t BY cluster
      | eval ovn_mstat_spike=round(coalesce(ovn_drop_like,0)+sqrt(coalesce(ovn_m_raw,0)),3)
      | eval lane="mstat_ovn" ]
| eval cluster=lower(trim(coalesce(cluster, "unknown_cluster")))
| stats
    max(eval(if(lane=="net_co", net_co_deg, null()))) AS net_co_deg
    max(eval(if(lane=="net_co", net_co_prog, null()))) AS net_co_prog
    max(eval(if(lane=="net_co", net_co_avail_min, null()))) AS net_co_avail_min
    max(eval(if(lane=="net_co", co_prog_flips, null()))) AS co_prog_flips
    max(eval(if(lane=="net_co", last_co_t, null()))) AS last_co_t
    max(eval(if(lane=="net_co", net_co_reason, null()))) AS net_co_reason
    max(eval(if(lane=="net_cfg", cluster_net_type, null()))) AS cluster_net_type
    max(eval(if(lane=="net_cfg", migration_status, null()))) AS migration_status
    max(eval(if(lane=="net_cfg", last_cfg_t, null()))) AS last_cfg_t
    max(eval(if(lane=="ovnkube", ovn_restart_sum, null()))) AS ovn_restart_sum
    max(eval(if(lane=="ovnkube", ovn_pod_cnt, null()))) AS ovn_pod_cnt
    max(eval(if(lane=="ovnkube", last_ovn_t, null()))) AS last_ovn_t
    max(eval(if(lane=="cni_evt", cni_bad_evt, null()))) AS cni_bad_evt
    max(eval(if(lane=="cni_evt", sandbox_fail, null()))) AS sandbox_fail
    max(eval(if(lane=="cni_evt", netready_fail, null()))) AS netready_fail
    max(eval(if(lane=="cni_evt", last_cni_t, null()))) AS last_cni_t
    max(eval(if(lane=="egress", egress_fail_cnt, null()))) AS egress_fail_cnt
    max(eval(if(lane=="egress", last_eg_t, null()))) AS last_eg_t
    max(eval(if(lane=="anp", anp_drift_hint, null()))) AS anp_drift_hint
    max(eval(if(lane=="anp", last_anp_t, null()))) AS last_anp_t
    max(eval(if(lane=="netcheck", diag_fail_hint, null()))) AS diag_fail_hint
    max(eval(if(lane=="netcheck", last_diag_t, null()))) AS last_diag_t
    max(eval(if(lane=="mstat_ovn", ovn_mstat_spike, null()))) AS ovn_mstat_spike
    max(eval(if(lane=="mstat_ovn", last_mstat_t, null()))) AS last_mstat_t
    values(lane) AS signal_lanes
    max(_time) AS last_seen
  BY cluster
| fillnull value=0 net_co_deg net_co_prog cni_bad_evt sandbox_fail netready_fail egress_fail_cnt diag_fail_hint co_prog_flips ovn_mstat_spike ovn_restart_sum
| eval net_co_avail_min=coalesce(net_co_avail_min,1)
| eventstats sum(net_co_deg) AS fleet_deg_cnt sum(eval(if(cni_bad_evt>=8,1,0))) AS fleet_evt_hot BY cluster
| streamstats window=6 current=t global=f sum(co_prog_flips) AS prog_flip_window BY cluster
| eval severity=case(
    net_co_deg==1 AND net_co_prog==1, "page",
    net_co_deg==1, "page",
    sandbox_fail>=5 OR netready_fail>=8, "page",
    cni_bad_evt>=25, "page",
    egress_fail_cnt>=3, "warn",
    diag_fail_hint>=3, "warn",
    coalesce(ovn_mstat_spike,0)>=500 AND net_co_prog==1, "warn",
    ovn_restart_sum>=48, "warn",
    net_co_prog==1 AND prog_flip_window>=3, "warn",
    cni_bad_evt>=8, "warn",
    coalesce(anp_drift_hint,0)>=1, "warn",
    true(), "info")
| eval recommended_action=case(
    net_co_deg==1, "oc_describe_clusteroperator_network_then_oc_logs_cluster_network_operator_and_ovnk_pods",
    sandbox_fail>=3 OR netready_fail>=3, "verify_ipam_node_subnets_mtu_geneve_and_ovnkube_node_logs",
    egress_fail_cnt>=1, "oc_describe_egressip_oc_get_egressfirewall_validate_cloud_routing",
    diag_fail_hint>=1, "oc_get_pods_openshift_network_diagnostics_review_network_check_logs",
    ovn_restart_sum>=24, "inspect_ovn_kubernetes_daemonsets_and_leader_election_logs",
    coalesce(anp_drift_hint,0)>=1, "validate_adminnetworkpolicy_controller_and_oc_get_adminnetworkpolicy",
    true(), "refresh_network_operator_snapshot_and_prometheus_ovn_metrics")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster signal_lanes net_co_deg net_co_prog net_co_avail_min cluster_net_type migration_status ovn_restart_sum cni_bad_evt sandbox_fail netready_fail egress_fail_cnt diag_fail_hint ovn_mstat_spike co_prog_flips severity recommended_action last_seen net_co_reason cluster_tier owner_team environment
```

savedsearches.conf sketch:

```ini
[openshift_uc_33312_ovnk_cluster_network_health_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -6h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-networking@example.com
action.email.subject = OCP OVN-K network $result.severity$ $result.cluster$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_33312_ovnk_cluster_network_health | where severity IN ("page","warn")
```

Performance: materialize five-minute aggregates into summary indexes keyed on cluster when Job Inspector shows multisearch queue delays. For very large fleets, run the mstats arm on a longer span with coarser prestats in a separate summary and join by cluster.

### Step 4 — Validate

Ground truth begins with oc get clusteroperator network -o wide and oc describe clusteroperator network to read condition messages compared to Splunk net_co_deg and net_co_prog fields in the same interval. Run oc get networks.config.openshift.io cluster -o yaml and verify networkType and migrationStatus match Splunk cluster_net_type and migration_status.

In openshift-ovn-kubernetes, run oc get pods -o wide and compare restart counts to Splunk ovn_restart_sum trends. Corrupt ovsdb connectivity often appears in ovnkube-node logs referencing disconnected databases; correlate with prometheus ovsdb error counters when scraping is enabled.

Event drilldown: during lab tests, cordon a node or misconfigure a small test namespace network attachment to elicit sandbox creation failures and confirm ocp_events reasons appear in Splunk cni_bad_evt counts.

Egress drilldown: simulate an unassignable EgressIP by requesting an address outside cloud allocation in lab only and confirm status conditions surface in ocp_egressip with nonzero egress_fail_cnt in Splunk.

AdminNetworkPolicy drilldown: when policy APIs are enabled, apply a test AdminNetworkPolicy in lab, confirm object lists in exporter output, and validate Splunk lane sees expected generations.

Negative test: on a stable cluster post-upgrade with Available=True and Progressing=False on the network operator, quiet sandbox events, and healthy diagnostics Pods, confirm the alert wrapper filtered to page and warn emits zero rows.

mstats cross-check: compare Splunk ovn metric sums to OpenShift console metrics explorer samples for matching metric_name and cluster labels.

Audit correlation: replay a controlled oc patch networks.config.openshift.io cluster activity in lab and confirm ocp_audit rows include verbs, actors, and object names without indexing sensitive request bodies beyond policy.

### Step 5 — Operationalize & Troubleshoot

Case 1 — network ClusterOperator Degraded with ovnkube-master pods restarting: gather cluster networking diagnostics per vendor guidance, review ovnkube-master logs for database elections, verify etcd and API health, and check control-plane node pressure before changing overlay MTU.

Case 2 — Progressing=True for longer than vendor guidance during upgrade: correlate with ClusterVersion history, confirm image pulls succeed to the release registry, and inspect cluster-network-operator logs for operand apply errors.

Case 3 — Frequent FailedCreatePodSandBox in many namespaces: check IPAM pool exhaustion in status.hostSubnet or node subnet annotations, review ovnkube-node readiness, verify Geneve UDP path between nodes with cloud security group audits, and validate MTU end to end.

Case 4 — PathMTUDiscoveryError bursts after WAN MTU change: align cluster network MTU with infrastructure paths, update host-network-interface MachineConfigs if required per platform documentation, and schedule controlled node reboots.

Case 5 — EgressIPNotAssigned during cloud subnet drift: reconcile cloud router table advertisements with EgressIP allocation, verify address is on the correct L3 segment, and validate node labels used for egress matching.

Case 6 — CNIPluginNotInitialized after unclean node reboot: restart ovnkube-node only under runbook guidance, verify systemd and kubelet start order, and check for stale lock files or ovs-vswitchd failures on the node.

Case 7 — AdminNetworkPolicy appears absent in Splunk exporter while API enabled: fix RBAC for the collector ServiceAccount, confirm CRD version matches exporter expectations, and reconcile GitOps apply order versus BaselineAdminNetworkPolicy defaults.

Case 8 — network-check-source pod Pending on taints: adjust diagnostics DaemonSet tolerations for dedicated infra nodes or document that synthetic probe silence is expected on tainted subsets and exclude those nodes in evaluator logic.

Case 9 — OpenShiftSDN to OVN-K migration window: expect elevated progressing and deliberate NetworkNotReady on nodes as SDN daemons drain; follow product migration guide timelines and annotate Splunk suppressions with migration ticket identifiers.

Case 10 — ovsdb_jsonrpc error counters climb without operator Degraded: validate prometheus scrape targets on ovn metrics endpoints, rule out label collisions, and compare northbound and southbound database Pod restarts in openshift-ovn-kubernetes.

Case 11 — Geneve tunnel drop counters isolated to one availability zone: escalate to network infrastructure for switch ECMP imbalance or hypervisor packet budgets before opening OVN software defects.

Case 12 — HostSubnet drift on legacy SDN clusters: oc get hostsubnet compares to node annotations; reconcile SDN subnet allocations before widening IP pools in Splunk-only automation.

Closing checklist: multisearch lists operator, config, ovnkube, events, egress, optional ANP, optional diagnostics, and mstats arms; coalesce, streamstats, eventstats, and case appear; closing table carries cluster, signal_lanes, net_co_deg, net_co_prog, net_co_avail_min, cluster_net_type, migration_status, ovn_restart_sum, cni_bad_evt, sandbox_fail, netready_fail, egress_fail_cnt, diag_fail_hint, ovn_mstat_spike, co_prog_flips, severity, recommended_action, last_seen, and net_co_reason for nineteen analyst-visible columns.

## SPL

```spl
`comment("UC-3.3.12 OVN-K cluster network — network CO, Net.config, ovnkube, CNI events, egress, ANP, diagnostics, ovn mstats. earliest=-6h@h latest=now")`
| multisearch
    [ search ((index=ocp_audit OR index=ocp_events OR index=ocp_metrics) AND sourcetype=ocp_clusteroperator) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval op=lower(trim(toString(coalesce(name, operator, clusteroperator_name, metadata_name, ""))))
      | where match(op,"^network$")
      | eval av=lower(trim(toString(coalesce(available, conditions_available, available_status, ""))))
      | eval pr=lower(trim(toString(coalesce(progressing, conditions_progressing, progressing_status, ""))))
      | eval dg=lower(trim(toString(coalesce(degraded, conditions_degraded, degraded_status, ""))))
      | eval co_avail=if(match(av,"true|1"),1,0)
      | eval co_prog=if(match(pr,"true|1"),1,0)
      | eval co_deg=if(match(dg,"true|1"),1,0)
      | eval co_reason=trim(toString(coalesce(reason, condition_reason, status_reason, "")))
      | eval co_msg=substr(trim(toString(coalesce(message, co_message, condition_message, ""))),1,280)
      | sort 0 + cluster - _time
      | streamstats window=2 current=t global=f last(co_prog) AS prev_prog BY cluster
      | eval prog_flip=if(co_prog==1 AND coalesce(prev_prog,0)==0,1,0)
      | stats latest(_time) AS last_co_t max(co_deg) AS net_co_deg max(co_prog) AS net_co_prog min(co_avail) AS net_co_avail_min sum(eval(coalesce(prog_flip,0))) AS co_prog_flips values(co_reason) AS co_reasons values(co_msg) AS co_msgs BY cluster
      | eval net_co_reason=mvindex(mvdedup(co_reasons),0)
      | eval lane="net_co" ]
    [ search (index=ocp_metrics OR index=ocp_audit) sourcetype=ocp_network_config earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval net_type=upper(trim(toString(coalesce(networkType, network_type, status_networkType, spec_networkType, ""))))
      | eval mig=lower(trim(toString(coalesce(migrationStatus, migration_status, spec_migration_mode, ""))))
      | stats latest(_time) AS last_cfg_t latest(net_type) AS cluster_net_type latest(mig) AS migration_status BY cluster
      | eval lane="net_cfg" ]
    [ search index=ocp_metrics sourcetype=ocp_ovnkube earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval restarts=tonumber(tostring(coalesce(restartCount, container_restarts, restart_total, "0")),10)
      | eval pod=lower(trim(toString(coalesce(pod, pod_name, kubernetes_pod_name, ""))))
      | stats sum(restarts) AS ovn_restart_sum dc(pod) AS ovn_pod_cnt latest(_time) AS last_ovn_t BY cluster
      | eval lane="ovnkube" ]
    [ search (index=ocp_events OR index=ocp_audit) (sourcetype=ocp_events OR sourcetype=k8s_events) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | where rs IN ("FailedCreatePodSandBox","NetworkNotReady","CNIPluginNotInitialized","IPAMFailure","EgressIPNotAssigned","NodeIPAMNotReady") OR match(lower(_raw),"failedcreatepodsandbox|networknotready|cnipluginnotinitialized|ipamfailure|egressipnotassigned|pathmtudiscoveryerror")
      | stats count AS cni_bad_evt count(eval(if(match(rs,"FailedCreatePodSandBox"),1,null()))) AS sandbox_fail count(eval(if(match(rs,"NetworkNotReady|CNIPluginNotInitialized|NodeIPAMNotReady"),1,null()))) AS netready_fail latest(_time) AS last_cni_t BY cluster
      | eval lane="cni_evt" ]
    [ search (index=ocp_metrics OR index=ocp_audit) (sourcetype=ocp_egressip OR sourcetype=ocp_egressfirewall) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval fail_hint=tonumber(tostring(coalesce(assignment_failed, status_failed, not_ready, "0")),10)
      | eval fail_hint=if(isnotnull(fail_hint) AND fail_hint>0,fail_hint,if(match(lower(toString(coalesce(status_phase, phase, ""))),"fail|pending|error"),1,0))
      | stats sum(fail_hint) AS egress_fail_cnt count AS egress_rows latest(_time) AS last_eg_t BY cluster
      | eval lane="egress" ]
    [ search index=ocp_metrics sourcetype=ocp_adminnetworkpolicy earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval drift=tonumber(tostring(coalesce(generation_gap, policy_drift, not_enforced, "0")),10)
      | stats max(drift) AS anp_drift_hint latest(_time) AS last_anp_t BY cluster
      | eval lane="anp" ]
    [ search (index=ocp_events OR index=ocp_metrics) (sourcetype=ocp_events OR sourcetype=ocp_network_diagnostics) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval pod=lower(trim(toString(coalesce(involvedObject_name, pod, pod_name, ""))))
      | eval msg=lower(toString(coalesce(message, Message, "")))
      | where match(pod,"network-check-source|network-check-target") OR match(lower(_raw),"network-check|network_check|synthetic.*probe") OR match(msg,"probe fail|check fail|diagnostics fail")
      | eval diag_hit=1
      | stats sum(diag_hit) AS diag_fail_hint latest(_time) AS last_diag_t BY cluster
      | eval lane="netcheck" ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype="prometheus:ocp") earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where match(mn,"^ovn_controller_|^ovnkube_master_|^ovsdb_jsonrpc_|^network_check_")
      | eval is_drop=if(match(mn,"drop|error|fail"),1,0)
      | stats sum(mv) AS ovn_m_raw sum(eval(if(is_drop==1,mv,0))) AS ovn_drop_like latest(_time) AS last_mstat_t BY cluster
      | eval ovn_mstat_spike=round(coalesce(ovn_drop_like,0)+sqrt(coalesce(ovn_m_raw,0)),3)
      | eval lane="mstat_ovn" ]
| eval cluster=lower(trim(coalesce(cluster, "unknown_cluster")))
| stats
    max(eval(if(lane=="net_co", net_co_deg, null()))) AS net_co_deg
    max(eval(if(lane=="net_co", net_co_prog, null()))) AS net_co_prog
    max(eval(if(lane=="net_co", net_co_avail_min, null()))) AS net_co_avail_min
    max(eval(if(lane=="net_co", co_prog_flips, null()))) AS co_prog_flips
    max(eval(if(lane=="net_co", last_co_t, null()))) AS last_co_t
    max(eval(if(lane=="net_co", net_co_reason, null()))) AS net_co_reason
    max(eval(if(lane=="net_cfg", cluster_net_type, null()))) AS cluster_net_type
    max(eval(if(lane=="net_cfg", migration_status, null()))) AS migration_status
    max(eval(if(lane=="net_cfg", last_cfg_t, null()))) AS last_cfg_t
    max(eval(if(lane=="ovnkube", ovn_restart_sum, null()))) AS ovn_restart_sum
    max(eval(if(lane=="ovnkube", ovn_pod_cnt, null()))) AS ovn_pod_cnt
    max(eval(if(lane=="ovnkube", last_ovn_t, null()))) AS last_ovn_t
    max(eval(if(lane=="cni_evt", cni_bad_evt, null()))) AS cni_bad_evt
    max(eval(if(lane=="cni_evt", sandbox_fail, null()))) AS sandbox_fail
    max(eval(if(lane=="cni_evt", netready_fail, null()))) AS netready_fail
    max(eval(if(lane=="cni_evt", last_cni_t, null()))) AS last_cni_t
    max(eval(if(lane=="egress", egress_fail_cnt, null()))) AS egress_fail_cnt
    max(eval(if(lane=="egress", last_eg_t, null()))) AS last_eg_t
    max(eval(if(lane=="anp", anp_drift_hint, null()))) AS anp_drift_hint
    max(eval(if(lane=="anp", last_anp_t, null()))) AS last_anp_t
    max(eval(if(lane=="netcheck", diag_fail_hint, null()))) AS diag_fail_hint
    max(eval(if(lane=="netcheck", last_diag_t, null()))) AS last_diag_t
    max(eval(if(lane=="mstat_ovn", ovn_mstat_spike, null()))) AS ovn_mstat_spike
    max(eval(if(lane=="mstat_ovn", last_mstat_t, null()))) AS last_mstat_t
    values(lane) AS signal_lanes
    max(_time) AS last_seen
  BY cluster
| fillnull value=0 net_co_deg net_co_prog cni_bad_evt sandbox_fail netready_fail egress_fail_cnt diag_fail_hint co_prog_flips ovn_mstat_spike ovn_restart_sum
| eval net_co_avail_min=coalesce(net_co_avail_min,1)
| eventstats sum(net_co_deg) AS fleet_deg_cnt sum(eval(if(cni_bad_evt>=8,1,0))) AS fleet_evt_hot BY cluster
| streamstats window=6 current=t global=f sum(co_prog_flips) AS prog_flip_window BY cluster
| eval severity=case(
    net_co_deg==1 AND net_co_prog==1, "page",
    net_co_deg==1, "page",
    sandbox_fail>=5 OR netready_fail>=8, "page",
    cni_bad_evt>=25, "page",
    egress_fail_cnt>=3, "warn",
    diag_fail_hint>=3, "warn",
    coalesce(ovn_mstat_spike,0)>=500 AND net_co_prog==1, "warn",
    ovn_restart_sum>=48, "warn",
    net_co_prog==1 AND prog_flip_window>=3, "warn",
    cni_bad_evt>=8, "warn",
    coalesce(anp_drift_hint,0)>=1, "warn",
    true(), "info")
| eval recommended_action=case(
    net_co_deg==1, "oc_describe_clusteroperator_network_then_oc_logs_cluster_network_operator_and_ovnk_pods",
    sandbox_fail>=3 OR netready_fail>=3, "verify_ipam_node_subnets_mtu_geneve_and_ovnkube_node_logs",
    egress_fail_cnt>=1, "oc_describe_egressip_oc_get_egressfirewall_validate_cloud_routing",
    diag_fail_hint>=1, "oc_get_pods_openshift_network_diagnostics_review_network_check_logs",
    ovn_restart_sum>=24, "inspect_ovn_kubernetes_daemonsets_and_leader_election_logs",
    coalesce(anp_drift_hint,0)>=1, "validate_adminnetworkpolicy_controller_and_oc_get_adminnetworkpolicy",
    true(), "refresh_network_operator_snapshot_and_prometheus_ovn_metrics")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster signal_lanes net_co_deg net_co_prog net_co_avail_min cluster_net_type migration_status ovn_restart_sum cni_bad_evt sandbox_fail netready_fail egress_fail_cnt diag_fail_hint ovn_mstat_spike co_prog_flips severity recommended_action last_seen net_co_reason cluster_tier owner_team environment
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-24h@h latest=now BY Application_State.dest
| rename Application_State.dest AS cim_dest
| join type=left max=0 cim_dest
    [| tstats summariesonly=t latest(Network_Traffic.action) AS nt_action latest(Network_Traffic.src) AS nt_src latest(Network_Traffic.dest) AS nt_dest FROM datamodel=Network_Traffic WHERE nodename=Network_Traffic earliest=-24h@h latest=now BY Network_Traffic.dest
     | rename Network_Traffic.dest AS cim_dest ]
| where like(lower(app_info), "%openshift%") OR like(lower(app_info), "%ovn%") OR match(lower(nt_action), "blocked|allowed|unknown")
| table cim_dest app_state app_info nt_action nt_src nt_dest
```

## Visualization

Severity-colored table by cluster with drilldowns to ocp_clusteroperator network JSON, Network.config snapshots, openshift-ovn-kubernetes Pod inventory, CNI event excerpts, egress status objects, AdminNetworkPolicy lists, diagnostics Pod logs, and ovn metric timecharts.

## Known False Positives

Planned OpenShiftSDN to OVN-K migration windows produce sustained Progressing=True on the network ClusterOperator, elevated NetworkNotReady events on nodes while daemons roll, and temporary EgressIP churn; annotate change_ticket_id on HTTP Event Collector payloads and widen suppression minutes per migration runbook guidance before paging executives. Scheduled z-stream upgrades that restart ovnkube-master and ovnkube-node DaemonSets routinely elevate container restart counters and short Geneve tunnel metric noise without customer impact; require multisearch corroboration with Degraded=True or sustained sandbox failures before declaring incidents. Transient EgressIPNotAssigned events during node drain and replacement often clear after assignment reconciles across cloud subnets; pair with oc describe egressip before automated ticketing. Cluster certificate rotations that recycle control-plane trust bundles can spike ovsdb reconnect counters for minutes; treat as benign when operator Available stays True and diagnostics Pods pass. network-check-source or network-check-target Pods scheduled to tainted infrastructure nodes may remain Pending; exclude known taint keys in lookup tables so synthetic probe silence does not masquerade as overlay failure. Large batch pod creation storms from CI namespaces can inflate FailedCreatePodSandBox counts when temporary IP pools are tight; scope alerts with namespace allow and deny lists. Duplicate log forwarders can double event counts; dedupe on involvedObject.uid when present. Prometheus scrape outages drop mstats arms while the data plane remains healthy; combine metric silence with ocp_clusteroperator snapshots before muting ovn_controller math entirely. Lab clusters that constantly churn network test namespaces will page unless routed to non-production indexes. AdminNetworkPolicy exporter drift from API version skew can raise anp_drift_hint during harmless CRD bumps; validate CRD generation against OpenShift release notes before runbook execution.

## References

- [OpenShift Documentation — About networking](https://docs.openshift.com/container-platform/latest/networking/about-networking.html)
- [OpenShift Documentation — About the OVN-Kubernetes network provider](https://docs.openshift.com/container-platform/latest/networking/ovn_kubernetes_network_provider/about-ovn-kubernetes.html)
- [OpenShift Documentation — Migrating from the OpenShift SDN network provider](https://docs.openshift.com/container-platform/latest/networking/ovn_kubernetes_network_provider/migrate-from-openshift-sdn.html)
- [OpenShift Documentation — Configuring egress IPs for OVN-Kubernetes](https://docs.openshift.com/container-platform/latest/networking/ovn_kubernetes_network_provider/configuring-egress-ips-ovn.html)
- [OpenShift Documentation — Configuring multitenant network policy](https://docs.openshift.com/container-platform/latest/networking/network_security/configuring-multitenant-network-policy.html)
- [OpenShift Documentation — Cluster Network Operator](https://docs.openshift.com/container-platform/latest/networking/cluster-network-operator.html)
- [Red Hat Blog — OpenShift 4.5 full stack automated operations and the OVN-Kubernetes networking model](https://www.redhat.com/en/blog/)
