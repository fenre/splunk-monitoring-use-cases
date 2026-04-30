<!-- AUTO-GENERATED from UC-3.3.19.json — DO NOT EDIT -->

---
id: "3.3.19"
title: "OpenShift IngressController Operator Reconciliation Failures, Shard or Scope Drift, and TLS or Wildcard Policy Conflicts"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.19 · OpenShift IngressController Operator Reconciliation Failures, Shard or Scope Drift, and TLS or Wildcard Policy Conflicts

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the OpenShift service that turns your desired edge routing design into live routers and DNS integration. When that service cannot reconcile shards, certificates, or health checks, we raise a clear signal so teams fix the platform configuration before customer routes fail.*

---

## Description

Detects ingress operator reconciliation failures on IngressController shards—conditions, DNS or load balancer drift, canary failures, wildcard clashes, TLS profile drift—before Routes fail broadly.

## Value

OpenShift ingress operator: IngressController reconciliation and policy plane

## Implementation

Index ocp_clusteroperator snapshots for ingress, ocp_ingresscontroller CR exports, ocp_events from openshift-ingress-operator and canary namespaces, and federated prometheus:metrics for ingress operator series with consistent cluster labels; normalize condition and replica fields in props; deploy lookup ocp_platform_maintenance_windows.csv for suppression; save openshift_uc_3_3_19_ingresscontroller_operator_plane on a ten-minute cadence over earliest=-6h@h; route page and warn to platform ingress on-call; archive weekly CSV evidence for operator-plane audits.

## Evidence

Saved search openshift_uc_3_3_19_ingresscontroller_operator_plane with ten or fifteen minute schedule; dashboard drilldowns on ocp_clusteroperator ingress, ocp_ingresscontroller, ocp_events, prometheus ingress operator lines, and maintenance lookup joins; alert stanza with platform routing keys; weekly CSV exports to a restricted evidence index.

## Control test

### Positive scenario

In a lab OpenShift cluster, ingest ocp_ingresscontroller rows where CanaryChecksSucceeding is False or DeploymentReplicasMinAvailable is False after a controlled nodeSelector mismatch, add matching ocp_clusteroperator ingress Degraded or Progressing snapshots, execute openshift_uc_3_3_19_ingresscontroller_operator_plane, and confirm page or warn severity with non-null recommended_action within two collection windows.

### Negative scenario

After recovery when oc describe ingresscontroller shows healthy conditions, canary checks succeed, and ingress ClusterOperator reports Available without Degraded, confirm severities return to info and the alert wrapper filtered to page and warn emits zero qualifying rows.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the OpenShift networking and platform engineering leads who administer the cluster-ingress-operator in openshift-ingress-operator, the teams that curate DNS and cloud load balancer integrations for IngressController publishing strategies, and the observability engineers who operate HTTP Event Collector tokens plus management-cluster exporters that snapshot operator.openshift.io IngressController objects and config.openshift.io ClusterOperator ingress rows. This use case isolates the configuration and reconciliation plane owned by the ingress ClusterOperator and its operator Deployment ingress-operator: how IngressController custom resources express desired shard topology, endpoint publishing strategy, route admission wildcard policies, TLS security profile selections, node placement, replica counts, namespace and route selectors, and how status.conditions such as Available, Progressing, DeploymentReplicasMinAvailable, LoadBalancerManaged, DNSManaged, and CanaryChecksSucceeding narrate operand health. The cluster-ingress-operator watches IngressController objects, materializes router Deployments and related Services in openshift-ingress, coordinates canary checks in openshift-ingress-canary, integrates with cloud DNS and load-balancer controllers when endpointPublishingStrategy requests hosted management, and enforces admission policy that can collide when multiple IngressControllers overlap wildcard admission domains.

Scope boundaries are explicit so sibling analytics stay distinct. UC-3.3.9 remains openshift-ingress HAProxy data-plane saturation: frontend session pressure, backend queues, and 5xx counters scraped from router Pods on port 1936. This UC does not replace those runtime economics. UC-3.2.9 remains vanilla Kubernetes Ingress controller error rates for community controllers such as NGINX Ingress, Traefik, or Contour without OpenShift Route admission semantics. UC-3.3.6 remains fleet-wide ClusterOperator reconciliation across roughly thirty platform operators; this UC narrows evidence to ingress ClusterOperator signals and IngressController CR conditions without duplicating generic operator-wide dashboards. UC-3.3.8 remains Route-level TLS certificate expiry and edge trust governance on Route objects, not IngressController-level tlsSecurityProfile or apiserver cluster default alignment. UC-3.3.1 ClusterVersion progression is out of scope except when upgrade metadata annotates intentional IngressController default changes you correlate in change tickets.

API and object model expectations: IngressController lives in group operator.openshift.io and is cluster-scoped. Platform teams commonly manage default, plus sharded controllers named for business units or environments. spec.endpointPublishingStrategy.type values include Private, HostNetwork, NodePortService, and LoadBalancerService with cloud-specific tuning fields. spec.nodePlacement.nodeSelector and tolerations must match schedulable nodes; an over-constrained selector can strand router Pods while conditions report Progressing=True. spec.routeAdmission.wildcardPolicy controls whether Routes may claim wildcard hosts and how conflicts resolve across shards. spec.tlsSecurityProfile names a profile that should align with cluster-wide cryptographic policy on apiservers.config.openshift.io cluster unless you intentionally override edge behavior. status.availableReplicas compared to spec.replicas exposes replica drift after upgrades that change defaults, horizontal autoscaler interactions, or budget-limited rollouts. status.domain and status.endpointPublishingStrategy observations should match DNS and load balancer reality; DNSManaged=False often follows IAM or credential loss on cloud DNS integrations. LoadBalancerManaged=False can track cloud provider quota, subnet, or security group faults distinct from router Pod readiness. CanaryChecksSucceeding=False indicates the operator’s canary Route probe failed, which may reflect NetworkPolicy denying in-cluster checks, Services without Endpoints, or genuine external unreachability; interpret alongside openshift-ingress-canary workload events rather than assuming only external outages.

RBAC and safety: collectors that run oc get ingresscontroller -A -o json, oc get clusteroperator ingress -o json, or watches on operator.openshift.io must use dedicated ServiceAccounts with get and list on those resources, not long-lived kubeadmin kubeconfigs on employee laptops. Prometheus federation jobs should use read-only monitoring tokens. Audit and event collectors must avoid persisting Secret bodies. Legal review should confirm internal domain names and cloud account identifiers in messages are acceptable in Splunk.

Index design: designate index=ocp_metrics for sourcetype=ocp_clusteroperator snapshots filtered to ingress, sourcetype=ocp_ingresscontroller for IngressController JSON exports with flattened conditions, and sourcetype=prometheus:metrics lines carrying cluster_operator_* series or operator workqueue metrics when your platform exposes them for the ingress operator. Designate index=ocp_events for sourcetype=ocp_events covering openshift-ingress-operator, openshift-ingress, and openshift-ingress-canary. Designate index=ocp_audit for sourcetype=ocp_audit when administrative verbs mutate IngressController objects, apiservers.config.openshift.io for tlsSecurityProfile, or DNS integrations. Retention should cover at least fourteen days hot for incident replay on reconciliation dwell, thirty days for upgrade postmortems, and cold storage aligned to enterprise logging policy.

Field normalization expectations: flatten IngressController metadata.name into ic_name, spec.replicas into ic_spec_rep, status.availableReplicas into ic_avail_rep, spec.endpointPublishingStrategy.type into eps_type, spec.routeAdmission.wildcardPolicy into wildcard_pol, spec.tlsSecurityProfile.type into ic_tls_type when present, spec.namespaceSelector and spec.routeSelector into stable text hashes or JSON snippets for drift analytics, and expand status.conditions[] into rows or parallel fields cond_Available, cond_Progressing, cond_DeploymentReplicasMinAvailable, cond_LoadBalancerManaged, cond_DNSManaged, cond_CanaryChecksSucceeding with paired reasons and messages. For ingress ClusterOperator snapshots, retain Available Progressing Degraded Upgradeable semantics with messages that cite IngressController operands. Cluster identity must appear on every event as cluster, openshift_cluster, or cluster_name.

Risk briefing: Progressing=True is normal during shard scaling, certificate rotations coordinated by the operator, and publishing strategy edits; measure dwell time and heartbeat age before paging. Canary failures after deliberate NetworkPolicy hardening may be expected once; pair with change records. Cloud DNS credential rotation can flip DNSManaged=False transiently during automation; require sustained false or corroborating cloud audit denial events. Wildcard admission collisions require human prioritization of which IngressController owns overlapping domains; Splunk surfaces the conflict signals rather than choosing winners.

Differentiation recap: ingress ClusterOperator plus IngressController CR condition and spec drift analytics, not generic HAProxy saturation alone, not vanilla Kubernetes Ingress error rates, not broad ClusterOperator fleet tables without ingress focus, not Route cert notAfter inventory.

Operational posture: stamp change_ticket_id onto HTTP Event Collector payloads when maintenance touches IngressController shards, DNS zones, or cloud IAM for load balancer and DNS integrations. When Splunk shows CanaryChecksSucceeding=False but external synthetic monitors stay green, suspect in-cluster policy or Service endpoints before blaming WAN providers.

### Step 2 — Configure data collection

Stand up five complementary lanes Splunk multisearch can fuse: ingress-scoped ClusterOperator snapshots, IngressController API snapshots with flattened conditions and replica math, Kubernetes events and audit records for openshift-ingress-operator and canary namespaces, optional Prometheus metrics for cluster_operator_conditions and operator queue depth, and a lookup-backed maintenance suppression lane you join at search time rather than muting indexes blindly.

Ingress ClusterOperator snapshot lane: schedule a utility every five minutes to oc get clusteroperator ingress -o json, flatten status.conditions into available progressing degraded upgradeable fields with lastTransitionTime per type, preserve relatedObjects references to IngressController instances when present, and emit sourcetype=ocp_clusteroperator with operator_name forced to ingress for join consistency. Include resourceVersion or observed generation hints when your exporter provides them.

IngressController snapshot lane: on the same cadence run oc get ingresscontroller -A -o json, iterate items[], compute replica_gap=abs(spec.replicas - status.availableReplicas) when both numbers exist, flatten conditions as described in prerequisites, capture spec.routeAdmission and spec.tlsSecurityProfile stanzas, and emit sourcetype=ocp_ingresscontroller with ic_name, ic_spec_rep, ic_avail_rep, replica_gap, eps_type, wildcard_pol, ic_tls_type, selector_fingerprint fields, and cond_CanaryChecksSucceeding boolean derived from the condition type CanaryChecksSucceeding status.

Events lane: forward Kubernetes events with sourcetype=ocp_events using Splunk Add-on for Kubernetes patterns or an OpenTelemetry Collector k8s_events receiver. Include openshift-ingress-operator for ingress-operator Pod scheduling, backoff, and admission controller messages, openshift-ingress for router operand rollouts, and openshift-ingress-canary for canary DaemonSet or check failures. Retain involvedObject.kind, involvedObject.name, reason, message, count, and firstTimestamp.

Audit lane: ship Kubernetes API audit JSON into index=ocp_audit with sourcetype=ocp_audit. Ensure objectRef captures ingresscontroller.operator.openshift.io, apiservers.config.openshift.io when tlsSecurityProfile changes, and DNS or DNSRecord custom resources your platform uses. Extract verbs, users, and responseStatus codes for admission denials.

Prometheus lane: federate openshift-monitoring targets that expose cluster_operator_up, cluster_operator_conditions, and workqueue depth or reconcile duration histograms when available for the ingress operator. Land lines in index=ocp_metrics with sourcetype=prometheus:metrics. Preserve name or operator labels that identify ingress.

Maintenance suppression lookup: maintain a CSV lookup such as ocp_platform_maintenance_windows with fields cluster, window_start, window_end, suppress_ingress_operator_alerts, change_ticket, and optional ic_name shard scope. Refresh via scheduled report or Git-backed upload so join logic can downgrade severity during approved changes.

props.conf guidance: TRUNCATE sufficiently large for JSON, TIMESTAMP_FIELDS respected when event time is authoritative, FIELDALIAS rules coalesce alternate exporter spellings for condition types.

Pre-save validation: index=ocp_metrics sourcetype=ocp_ingresscontroller earliest=-1h must return events after the first interval; ocp_clusteroperator rows filtered to ingress must exist; ocp_events should show operator lifecycle messages during controlled IngressController edits; prometheus lines should include cluster_operator_conditions during healthy scrapes.

Dashboards: host a matrix keyed on cluster and ic_name with color thresholds from severity, drilldowns to raw JSON, events, audit excerpts, and prometheus lines.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_19_ingresscontroller_operator_plane with a ten or fifteen minute schedule, dispatch earliest=-6h@h, dispatch latest=now, and alert when severity is page or warn after maintenance suppression. Throttle duplicate cluster ic_name rows for thirty minutes unless severity escalates. Include recommended_action, ic_msg, replica_gap, and canary_bad flags in pager bodies.

Pipeline narrative: multisearch fans ingress ClusterOperator snapshots, IngressController condition snapshots, ingress-operator event summaries, canary condition extracts, and prometheus operator metrics so a silent single lane does not hide genuine reconciliation failure. coalesce() absorbs cluster label drift. streamstats measures short-term progression dwell by ic_name. eventstats adds cluster-level counts of bad canary rows and replica gap outliers. case() maps Available false, DeploymentReplicasMinAvailable false, DNSManaged or LoadBalancerManaged false sustained windows, CanaryChecksSucceeding false, tlsSecurityProfile mismatch hints, wildcard policy collision hints, and ingress-operator pod failure bursts into page versus warn versus info. join to inputlookup applies maintenance suppression. recommended_action encodes verbs referencing oc describe ingresscontroller, oc get clusteroperator ingress, oc logs deployment ingress-operator, oc adm inspect when vendor guidance requires, and cloud provider DNS or load balancer runbooks without pretending search replaces platform engineering judgement.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.19 IngressController operator config plane — multisearch arms: ingress ClusterOperator, IngressController CR conditions, openshift-ingress-operator events, canary condition lane, prometheus ingress operator series. Maintenance join: lookup ocp_platform_maintenance_windows. Tunables: earliest=-6h@h latest=now replica_gap_warn=1 replica_gap_page=2 op_fail_warn=3")`
| multisearch
    [ search index=ocp_metrics sourcetype=ocp_clusteroperator earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval operator_name=lower(trim(toString(coalesce(name, operator, clusteroperator_name, metadata_name, co_name, ""))))
      | where operator_name="ingress"
      | eval av=lower(trim(toString(coalesce(available, conditions_available, available_status, ""))))
      | eval pr=lower(trim(toString(coalesce(progressing, conditions_progressing, progressing_status, ""))))
      | eval dg=lower(trim(toString(coalesce(degraded, conditions_degraded, degraded_status, ""))))
      | eval co_avail=if(match(av,"true|1"),1,0)
      | eval co_prog=if(match(pr,"true|1"),1,0)
      | eval co_deg=if(match(dg,"true|1"),1,0)
      | eval co_msg=trim(toString(coalesce(message, reason, status_message, condition_message, co_message, "")))
      | eval ic_name="*"
      | eval lane="co_ingress"
      | stats latest(_time) AS lane_t max(co_avail) AS co_avail max(co_prog) AS co_prog max(co_deg) AS co_deg latest(co_msg) AS co_msg BY cluster ic_name lane ]
    [ search index=ocp_metrics sourcetype=ocp_ingresscontroller earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval ic_name=lower(trim(toString(coalesce(ic_name, name, metadata_name, ingresscontroller, ""))))
      | eval ic_spec_rep=tonumber(tostring(coalesce(ic_spec_rep, spec_replicas, specReplicas, replicas, "")),10)
      | eval ic_avail_rep=tonumber(tostring(coalesce(ic_avail_rep, availableReplicas, status_availableReplicas, "")),10)
      | eval replica_gap=if(isnotnull(ic_spec_rep) AND isnotnull(ic_avail_rep), abs(ic_spec_rep-ic_avail_rep), null())
      | eval eps_type=lower(trim(toString(coalesce(eps_type, endpointPublishingStrategy_type, publishing_strategy, ""))))
      | eval wildcard_pol=lower(trim(toString(coalesce(wildcard_pol, routeAdmission_wildcardPolicy, spec_routeAdmission_wildcardPolicy, ""))))
      | eval ic_tls_type=lower(trim(toString(coalesce(ic_tls_type, tlsSecurityProfile_type, spec_tlsSecurityProfile_type, tls_profile, ""))))
      | eval c_can=lower(trim(toString(coalesce(cond_CanaryChecksSucceeding, canaryChecksSucceeding, CanaryChecksSucceeding, ""))))
      | eval c_dns=lower(trim(toString(coalesce(cond_DNSManaged, dnsManaged, DNSManaged, ""))))
      | eval c_lb=lower(trim(toString(coalesce(cond_LoadBalancerManaged, loadBalancerManaged, LoadBalancerManaged, ""))))
      | eval c_dep=lower(trim(toString(coalesce(cond_DeploymentReplicasMinAvailable, deploymentReplicasMinAvailable, DeploymentReplicasMinAvailable, ""))))
      | eval c_av=lower(trim(toString(coalesce(cond_Available, availableCond, conditions_Available, ""))))
      | eval c_pr=lower(trim(toString(coalesce(cond_Progressing, progressingCond, conditions_Progressing, ""))))
      | eval canary_bad=if(match(c_can,"false|0"),1,0)
      | eval dns_bad=if(match(c_dns,"false|0"),1,0)
      | eval lb_bad=if(match(c_lb,"false|0"),1,0)
      | eval depmin_bad=if(match(c_dep,"false|0"),1,0)
      | eval avail_bad=if(match(c_av,"false|0"),1,0)
      | eval prog_bad=if(match(c_pr,"true|1"),1,0)
      | eval ic_msg=trim(toString(coalesce(status_message, condition_message, ic_condition_msg, message, "")))
      | eval lane="ic_cr"
      | stats latest(_time) AS lane_t max(replica_gap) AS replica_gap max(canary_bad) AS canary_bad max(dns_bad) AS dns_bad max(lb_bad) AS lb_bad max(depmin_bad) AS depmin_bad max(avail_bad) AS avail_bad max(prog_bad) AS prog_bad latest(ic_msg) AS ic_msg latest(eps_type) AS eps_type latest(wildcard_pol) AS wildcard_pol latest(ic_tls_type) AS ic_tls_type BY cluster ic_name lane ]
    [ search index=ocp_events sourcetype=ocp_events earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval ns=lower(trim(toString(coalesce(namespace, involvedObject_namespace, object_namespace, ""))))
      | where ns IN ("openshift-ingress-operator","openshift-ingress","openshift-ingress-canary")
      | eval iname=lower(trim(toString(coalesce(involvedObject_name, object_name, ""))))
      | eval msg=lower(trim(toString(coalesce(message, Message, reason, ""))))
      | eval op_fail=if(match(msg,"backoff|failed|error|unhealthy|crashloop|admission|kill") OR match(iname,"ingress-operator"),1,0)
      | eval ic_name=coalesce(lower(trim(toString(ingresscontroller_name))),"*")
      | eval lane="ic_evt"
      | stats latest(_time) AS lane_t sum(op_fail) AS op_fail_cnt latest(msg) AS evt_tail BY cluster ic_name lane ]
    [ search index=ocp_metrics sourcetype=ocp_ingresscontroller earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval ic_name=lower(trim(toString(coalesce(ic_name, name, metadata_name, ingresscontroller, ""))))
      | eval c_can=lower(trim(toString(coalesce(cond_CanaryChecksSucceeding, canaryChecksSucceeding, ""))))
      | eval canary_bad=if(match(c_can,"false|0"),1,0)
      | where canary_bad==1
      | eval lane="canary_lane"
      | stats latest(_time) AS lane_t max(canary_bad) AS canary_bad latest(status_message) AS canary_msg BY cluster ic_name lane ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype="prometheus:cluster_operator_up") earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")),10)
      | where match(mn,"cluster_operator_up|cluster_operator_conditions|workqueue_depth|workqueue_adds_total|workqueue_work_duration_seconds_count")
      | eval oname=lower(trim(toString(coalesce(name, clusteroperator, exported_clusteroperator, ""))))
      | where oname="ingress" OR (len(oname)=0 AND match(lower(_raw),"\\bingress\\b"))
      | eval ic_name="*"
      | eval lane="ic_prom"
      | stats latest(_time) AS lane_t latest(mn) AS prom_name max(mv) AS prom_peak BY cluster ic_name lane ]
| stats max(lane_t) AS last_seen max(co_avail) AS co_avail max(co_prog) AS co_prog max(co_deg) AS co_deg latest(co_msg) AS co_msg max(replica_gap) AS replica_gap max(canary_bad) AS canary_bad max(dns_bad) AS dns_bad max(lb_bad) AS lb_bad max(depmin_bad) AS depmin_bad max(avail_bad) AS avail_bad max(prog_bad) AS prog_bad latest(ic_msg) AS ic_msg latest(evt_tail) AS evt_tail max(op_fail_cnt) AS op_fail_cnt latest(eps_type) AS eps_type latest(wildcard_pol) AS wildcard_pol latest(ic_tls_type) AS ic_tls_type latest(prom_name) AS prom_name max(prom_peak) AS prom_peak latest(canary_msg) AS canary_msg BY cluster ic_name
| sort cluster ic_name
| filldown co_msg
| eventstats max(co_avail) AS co_avail_c max(co_prog) AS co_prog_c max(co_deg) AS co_deg_c BY cluster
| eval co_avail=coalesce(co_avail, co_avail_c)
| eval co_prog=coalesce(co_prog, co_prog_c)
| eval co_deg=coalesce(co_deg, co_deg_c)
| streamstats window=4 current=t global=f last(prog_bad) AS prev_prog BY cluster ic_name
| eval prog_dwell=if(prog_bad==1 AND prev_prog==1,1,prog_bad)
| eventstats sum(canary_bad) AS cluster_canary_bad_cnt sum(dns_bad) AS cluster_dns_bad_cnt max(eval(if(isnotnull(replica_gap),replica_gap,0))) AS cluster_max_replica_gap BY cluster
| eval tls_drift_hint=if(len(ic_tls_type)>0 AND match(ic_tls_type,"old|intermediate|custom|modern"),1,0)
| eval wildcard_collision_hint=if(match(wildcard_pol,"wildcard|subdomain|any") AND cluster_canary_bad_cnt>=2,1,0)
| eval severity=case(
    co_deg==1 OR avail_bad==1 OR depmin_bad==1, "page",
    canary_bad==1 AND co_prog==1, "page",
    dns_bad==1 AND lb_bad==1, "page",
    replica_gap>=2 AND depmin_bad==1, "page",
    canary_bad==1, "warn",
    dns_bad==1 OR lb_bad==1, "warn",
    co_prog==1 AND prog_dwell>=1, "warn",
    op_fail_cnt>=3, "warn",
    wildcard_collision_hint==1, "warn",
    tls_drift_hint==1 AND match(ic_msg,"tls|profile|cipher|minimum"), "warn",
    true(), "info")
| eval recommended_action=case(
    depmin_bad==1 OR avail_bad==1, "oc_describe_ingresscontroller_check_nodeplacement_and_router_deployment",
    dns_bad==1, "validate_cloud_dns_credentials_iam_and_zone_delegation",
    lb_bad==1, "validate_cloud_load_balancer_health_quotas_and_subnets",
    canary_bad==1, "inspect_openshift_ingress_canary_networkpolicy_endpoints_and_probe_path",
    replica_gap>=1, "compare_spec_replicas_to_hpa_and_upgrade_release_notes_for_default_changes",
    co_deg==1, "oc_describe_clusteroperator_ingress_and_collect_ingress_operator_logs",
    op_fail_cnt>=3, "oc_logs_ingress_operator_and_review_admission_webhooks",
    true(), "correlate_ingresscontroller_status_with_route_admission_messages")
| join type=left max=0 cluster [| inputlookup ocp_platform_maintenance_windows.csv | eval cluster=lower(trim(cluster)) | eval maint_suppress=tonumber(coalesce(suppress_ingress_operator_alerts, suppress_ingress, "0"),10) | fields cluster maint_suppress maint_ticket | rename maint_ticket AS change_ticket ]
| eval severity=if(maint_suppress==1 AND severity!="page", "info", severity)
| table cluster ic_name co_avail co_prog co_deg replica_gap dns_bad lb_bad depmin_bad canary_bad op_fail_cnt wildcard_pol ic_tls_type cluster_canary_bad_cnt cluster_dns_bad_cnt cluster_max_replica_gap severity recommended_action maint_suppress change_ticket last_seen prom_name prom_peak evt_tail ic_msg canary_msg co_msg
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_19_ingresscontroller_operator_plane_alert]
cron_schedule = */10 * * * *
dispatch.earliest_time = -6h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-platform@example.com
action.email.subject = OCP ingress operator plane $result.severity$ $result.cluster$ $result.ic_name$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_19_ingresscontroller_operator_plane | where severity IN ("page","warn")
```

Performance: materialize five-minute summaries keyed on cluster and ic_name into a summary index when Job Inspector shows multisearch queue delays.

### Step 4 — Validate

Ground truth begins on-cluster. Run oc get clusteroperator ingress -o wide and oc get ingresscontroller -A -o yaml, then compare Available, Progressing, and Degraded columns to Splunk rows from the same interval. When statuses disagree, verify resourceVersion freshness, exporter clock skew, and duplicate cluster labels across regions.

Deep dive with oc describe clusteroperator ingress and oc describe ingresscontroller <name> to read condition messages about DNS, load balancer, canary, and deployment minimum availability. Splunk should mirror transitions within one collection interval; if not, tighten scripted input cadence or fix kubeconfig expiration on management hosts.

Canary truth: oc -n openshift-ingress-canary get pods, events, and routes tied to canary checks. When CanaryChecksSucceeding=False in telemetry, confirm whether NetworkPolicy changed, Services lost Endpoints, or external dependencies broke.

Prometheus cross-check: validate cluster_operator_conditions and cluster_operator_up for ingress in the OpenShift console monitoring UI versus Splunk prom_peak rows.

Synthetic validation: in a lab shard, apply a nodeSelector that matches no nodes under change control, observe Progressing and DeploymentReplicasMinAvailable conditions, and confirm the saved search elevates severity with non-null recommended_action. Roll back and confirm recovery.

Negative test: on a healthy cluster after edits settle, confirm severities return to info and the alert wrapper filtered to page and warn emits zero rows.

Audit cross-check: replay a controlled oc patch ingresscontroller and tlsSecurityProfile edit, then confirm ocp_audit rows include verbs and actors.

Lookup validation: ensure inputlookup ocp_platform_maintenance_windows.csv exists in the Splunk lookup directory or replace the join with a KV Store collection; absence should not null the entire search—use outer join patterns in production hardening.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Custom IngressController stuck in Progressing because nodeSelector matches no nodes: relax or correct nodePlacement.nodeSelector and tolerations, verify machine health, and confirm router Pods schedule before DNS or load balancer checks time out.

Case 2 — Wildcard policy admission collision when two IngressControllers claim overlapping domains: prioritize shard ownership with architecture review, adjust spec.routeAdmission.wildcardPolicy and namespace or route selectors, and reconcile GitOps templates that duplicated host patterns.

Case 3 — DNSManaged=False after cloud DNS IAM revocation or key rotation: restore credentials per cloud provider guidance, validate zone delegation for apps domain, and replay operator reconciliation before customer routes fail externally.

Case 4 — tlsSecurityProfile drift from cluster default after manual edit to IngressController: compare apiservers.config.openshift.io cluster spec.tlsSecurityProfile with IngressController spec, align profiles intentionally, and document exceptions for regulated environments.

Case 5 — CanaryChecksSucceeding=False because NetworkPolicy denies openshift-ingress-canary probes: add controlled egress and ingress rules for canary namespaces while preserving security intent, or temporarily scope policy changes through maintenance windows with suppression metadata.

Case 6 — Replica request drift after upgrade default changes or HPA edits: reconcile spec.replicas with platform baselines, read release notes for new defaults, and verify budget constraints are not capping available replicas silently.

Case 7 — LoadBalancerManaged=False with healthy router Pods: investigate cloud quota, security groups, subnet tags, and provider API throttling distinct from router container health.

Case 8 — HostNetwork versus NodePortService publishing strategy drift after platform migration: validate eps_type matches architecture standards, confirm node firewall openings, and adjust scrape paths only after operand readiness returns.

Case 9 — ingress-operator Pod crash loops after CRD or webhook upgrades: collect oc logs deployment ingress-operator, verify validating webhook availability, and roll forward or roll back per vendor guidance with change tickets linked in Splunk.

Case 10 — Route selector and namespace selector mismatches stranding Routes on unintended shards: reconcile labels on Namespaces and Routes with spec.namespaceSelector and spec.routeSelector expectations, then verify admission messages in events.

Case 11 — Fleet-wide info severities only: weekly spot-check Splunk rows against oc get ingresscontroller for every production cluster to confirm parsers, tokens, and RBAC remain aligned.

Closing checklist: multisearch lists five arms; coalesce normalizes cluster fields; streamstats flags progression dwell; eventstats adds cluster context; case maps severity; join applies maintenance suppression; closing table includes cluster, ic_name, co_avail, co_prog, co_deg, replica_gap, dns_bad, lb_bad, depmin_bad, canary_bad, op_fail_cnt, wildcard_pol, ic_tls_type, cluster_canary_bad_cnt, cluster_dns_bad_cnt, cluster_max_replica_gap, severity, recommended_action, maint_suppress, change_ticket, last_seen, prom_name, prom_peak, evt_tail, ic_msg, canary_msg, and co_msg for analyst review.


## SPL

```spl
`comment("UC-3.3.19 IngressController operator config plane — multisearch arms: ingress ClusterOperator, IngressController CR conditions, openshift-ingress-operator events, canary condition lane, prometheus ingress operator series. Maintenance join: lookup ocp_platform_maintenance_windows. Tunables: earliest=-6h@h latest=now replica_gap_warn=1 replica_gap_page=2 op_fail_warn=3")`
| multisearch
    [ search index=ocp_metrics sourcetype=ocp_clusteroperator earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval operator_name=lower(trim(toString(coalesce(name, operator, clusteroperator_name, metadata_name, co_name, ""))))
      | where operator_name="ingress"
      | eval av=lower(trim(toString(coalesce(available, conditions_available, available_status, ""))))
      | eval pr=lower(trim(toString(coalesce(progressing, conditions_progressing, progressing_status, ""))))
      | eval dg=lower(trim(toString(coalesce(degraded, conditions_degraded, degraded_status, ""))))
      | eval co_avail=if(match(av,"true|1"),1,0)
      | eval co_prog=if(match(pr,"true|1"),1,0)
      | eval co_deg=if(match(dg,"true|1"),1,0)
      | eval co_msg=trim(toString(coalesce(message, reason, status_message, condition_message, co_message, "")))
      | eval ic_name="*"
      | eval lane="co_ingress"
      | stats latest(_time) AS lane_t max(co_avail) AS co_avail max(co_prog) AS co_prog max(co_deg) AS co_deg latest(co_msg) AS co_msg BY cluster ic_name lane ]
    [ search index=ocp_metrics sourcetype=ocp_ingresscontroller earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval ic_name=lower(trim(toString(coalesce(ic_name, name, metadata_name, ingresscontroller, ""))))
      | eval ic_spec_rep=tonumber(tostring(coalesce(ic_spec_rep, spec_replicas, specReplicas, replicas, "")),10)
      | eval ic_avail_rep=tonumber(tostring(coalesce(ic_avail_rep, availableReplicas, status_availableReplicas, "")),10)
      | eval replica_gap=if(isnotnull(ic_spec_rep) AND isnotnull(ic_avail_rep), abs(ic_spec_rep-ic_avail_rep), null())
      | eval eps_type=lower(trim(toString(coalesce(eps_type, endpointPublishingStrategy_type, publishing_strategy, ""))))
      | eval wildcard_pol=lower(trim(toString(coalesce(wildcard_pol, routeAdmission_wildcardPolicy, spec_routeAdmission_wildcardPolicy, ""))))
      | eval ic_tls_type=lower(trim(toString(coalesce(ic_tls_type, tlsSecurityProfile_type, spec_tlsSecurityProfile_type, tls_profile, ""))))
      | eval c_can=lower(trim(toString(coalesce(cond_CanaryChecksSucceeding, canaryChecksSucceeding, CanaryChecksSucceeding, ""))))
      | eval c_dns=lower(trim(toString(coalesce(cond_DNSManaged, dnsManaged, DNSManaged, ""))))
      | eval c_lb=lower(trim(toString(coalesce(cond_LoadBalancerManaged, loadBalancerManaged, LoadBalancerManaged, ""))))
      | eval c_dep=lower(trim(toString(coalesce(cond_DeploymentReplicasMinAvailable, deploymentReplicasMinAvailable, DeploymentReplicasMinAvailable, ""))))
      | eval c_av=lower(trim(toString(coalesce(cond_Available, availableCond, conditions_Available, ""))))
      | eval c_pr=lower(trim(toString(coalesce(cond_Progressing, progressingCond, conditions_Progressing, ""))))
      | eval canary_bad=if(match(c_can,"false|0"),1,0)
      | eval dns_bad=if(match(c_dns,"false|0"),1,0)
      | eval lb_bad=if(match(c_lb,"false|0"),1,0)
      | eval depmin_bad=if(match(c_dep,"false|0"),1,0)
      | eval avail_bad=if(match(c_av,"false|0"),1,0)
      | eval prog_bad=if(match(c_pr,"true|1"),1,0)
      | eval ic_msg=trim(toString(coalesce(status_message, condition_message, ic_condition_msg, message, "")))
      | eval lane="ic_cr"
      | stats latest(_time) AS lane_t max(replica_gap) AS replica_gap max(canary_bad) AS canary_bad max(dns_bad) AS dns_bad max(lb_bad) AS lb_bad max(depmin_bad) AS depmin_bad max(avail_bad) AS avail_bad max(prog_bad) AS prog_bad latest(ic_msg) AS ic_msg latest(eps_type) AS eps_type latest(wildcard_pol) AS wildcard_pol latest(ic_tls_type) AS ic_tls_type BY cluster ic_name lane ]
    [ search index=ocp_events sourcetype=ocp_events earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval ns=lower(trim(toString(coalesce(namespace, involvedObject_namespace, object_namespace, ""))))
      | where ns IN ("openshift-ingress-operator","openshift-ingress","openshift-ingress-canary")
      | eval iname=lower(trim(toString(coalesce(involvedObject_name, object_name, ""))))
      | eval msg=lower(trim(toString(coalesce(message, Message, reason, ""))))
      | eval op_fail=if(match(msg,"backoff|failed|error|unhealthy|crashloop|admission|kill") OR match(iname,"ingress-operator"),1,0)
      | eval ic_name=coalesce(lower(trim(toString(ingresscontroller_name))),"*")
      | eval lane="ic_evt"
      | stats latest(_time) AS lane_t sum(op_fail) AS op_fail_cnt latest(msg) AS evt_tail BY cluster ic_name lane ]
    [ search index=ocp_metrics sourcetype=ocp_ingresscontroller earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval ic_name=lower(trim(toString(coalesce(ic_name, name, metadata_name, ingresscontroller, ""))))
      | eval c_can=lower(trim(toString(coalesce(cond_CanaryChecksSucceeding, canaryChecksSucceeding, ""))))
      | eval canary_bad=if(match(c_can,"false|0"),1,0)
      | where canary_bad==1
      | eval lane="canary_lane"
      | stats latest(_time) AS lane_t max(canary_bad) AS canary_bad latest(status_message) AS canary_msg BY cluster ic_name lane ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype="prometheus:cluster_operator_up") earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")),10)
      | where match(mn,"cluster_operator_up|cluster_operator_conditions|workqueue_depth|workqueue_adds_total|workqueue_work_duration_seconds_count")
      | eval oname=lower(trim(toString(coalesce(name, clusteroperator, exported_clusteroperator, ""))))
      | where oname="ingress" OR (len(oname)=0 AND match(lower(_raw),"\\bingress\\b"))
      | eval ic_name="*"
      | eval lane="ic_prom"
      | stats latest(_time) AS lane_t latest(mn) AS prom_name max(mv) AS prom_peak BY cluster ic_name lane ]
| stats max(lane_t) AS last_seen max(co_avail) AS co_avail max(co_prog) AS co_prog max(co_deg) AS co_deg latest(co_msg) AS co_msg max(replica_gap) AS replica_gap max(canary_bad) AS canary_bad max(dns_bad) AS dns_bad max(lb_bad) AS lb_bad max(depmin_bad) AS depmin_bad max(avail_bad) AS avail_bad max(prog_bad) AS prog_bad latest(ic_msg) AS ic_msg latest(evt_tail) AS evt_tail max(op_fail_cnt) AS op_fail_cnt latest(eps_type) AS eps_type latest(wildcard_pol) AS wildcard_pol latest(ic_tls_type) AS ic_tls_type latest(prom_name) AS prom_name max(prom_peak) AS prom_peak latest(canary_msg) AS canary_msg BY cluster ic_name
| sort cluster ic_name
| filldown co_msg
| eventstats max(co_avail) AS co_avail_c max(co_prog) AS co_prog_c max(co_deg) AS co_deg_c BY cluster
| eval co_avail=coalesce(co_avail, co_avail_c)
| eval co_prog=coalesce(co_prog, co_prog_c)
| eval co_deg=coalesce(co_deg, co_deg_c)
| streamstats window=4 current=t global=f last(prog_bad) AS prev_prog BY cluster ic_name
| eval prog_dwell=if(prog_bad==1 AND prev_prog==1,1,prog_bad)
| eventstats sum(canary_bad) AS cluster_canary_bad_cnt sum(dns_bad) AS cluster_dns_bad_cnt max(eval(if(isnotnull(replica_gap),replica_gap,0))) AS cluster_max_replica_gap BY cluster
| eval tls_drift_hint=if(len(ic_tls_type)>0 AND match(ic_tls_type,"old|intermediate|custom|modern"),1,0)
| eval wildcard_collision_hint=if(match(wildcard_pol,"wildcard|subdomain|any") AND cluster_canary_bad_cnt>=2,1,0)
| eval severity=case(
    co_deg==1 OR avail_bad==1 OR depmin_bad==1, "page",
    canary_bad==1 AND co_prog==1, "page",
    dns_bad==1 AND lb_bad==1, "page",
    replica_gap>=2 AND depmin_bad==1, "page",
    canary_bad==1, "warn",
    dns_bad==1 OR lb_bad==1, "warn",
    co_prog==1 AND prog_dwell>=1, "warn",
    op_fail_cnt>=3, "warn",
    wildcard_collision_hint==1, "warn",
    tls_drift_hint==1 AND match(ic_msg,"tls|profile|cipher|minimum"), "warn",
    true(), "info")
| eval recommended_action=case(
    depmin_bad==1 OR avail_bad==1, "oc_describe_ingresscontroller_check_nodeplacement_and_router_deployment",
    dns_bad==1, "validate_cloud_dns_credentials_iam_and_zone_delegation",
    lb_bad==1, "validate_cloud_load_balancer_health_quotas_and_subnets",
    canary_bad==1, "inspect_openshift_ingress_canary_networkpolicy_endpoints_and_probe_path",
    replica_gap>=1, "compare_spec_replicas_to_hpa_and_upgrade_release_notes_for_default_changes",
    co_deg==1, "oc_describe_clusteroperator_ingress_and_collect_ingress_operator_logs",
    op_fail_cnt>=3, "oc_logs_ingress_operator_and_review_admission_webhooks",
    true(), "correlate_ingresscontroller_status_with_route_admission_messages")
| join type=left max=0 cluster [| inputlookup ocp_platform_maintenance_windows.csv | eval cluster=lower(trim(cluster)) | eval maint_suppress=tonumber(coalesce(suppress_ingress_operator_alerts, suppress_ingress, "0"),10) | fields cluster maint_suppress maint_ticket | rename maint_ticket AS change_ticket ]
| eval severity=if(maint_suppress==1 AND severity!="page", "info", severity)
| table cluster ic_name co_avail co_prog co_deg replica_gap dns_bad lb_bad depmin_bad canary_bad op_fail_cnt wildcard_pol ic_tls_type cluster_canary_bad_cnt cluster_dns_bad_cnt cluster_max_replica_gap severity recommended_action maint_suppress change_ticket last_seen prom_name prom_peak evt_tail ic_msg canary_msg co_msg
```

## CIM SPL

```spl
| tstats summariesonly=true latest(Change.action) AS change_action latest(Change.object) AS change_object latest(Change.user) AS change_user FROM datamodel=Change WHERE nodename=Change earliest=-24h@h latest=now BY Change.dest
| rename Change.dest AS cim_dest
| join type=left max=0 cim_dest
    [| tstats summariesonly=true latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-24h@h latest=now BY Application_State.dest
     | rename Application_State.dest AS cim_dest ]
| where like(lower(change_object), "%ingresscontroller%") OR like(lower(app_info), "%openshift%ingress%")
| table cim_dest change_action change_object change_user app_state app_info
```

## Visualization

Severity-colored table by cluster and ic_name with drilldowns to ocp_clusteroperator ingress rows, ocp_ingresscontroller JSON, ocp_events in operator namespaces, and prometheus ingress operator series; single-value tiles for cluster_canary_bad_cnt; timeline of replica_gap by shard.

## Known False Positives

Short Progressing=True windows are normal during shard scaling, certificate rotations, and edits to endpointPublishingStrategy; require pairing with depmin_bad, canary_bad, or sustained dns_bad before paging leadership. Cloud DNS automation that rotates credentials can flip DNSManaged=False for minutes while controllers reconcile; corroborate with provider audit logs and route53 or azure-dns activity before treating as incident. CanaryChecksSucceeding=False after deliberate NetworkPolicy tightening may be a one-time expected blip when change tickets document the hardening; distinguish from silent data-plane outages using external synthetic checks and openshift-ingress-canary Pod logs. Wildcard admission collisions often reflect intentional migration projects where two shards temporarily overlap; use architecture runbooks rather than automatic rollback unless customer Routes fail admission. Replica gaps can appear during voluntary cluster autoscaler scale-in of router nodes when budgets cap available replicas; compare to machine health, PodDisruptionBudgets, and upgrade notes before opening defects against the operator. Prometheus scrape gaps from monitoring outages can null prom_peak while API snapshots remain authoritative; combine lanes before muting metrics-only arms. Duplicate HTTP Event Collector submissions from redundant exporters can inflate op_fail_cnt until dedupe lands in summary indexes. Lab clusters that continuously churn IngressController tests will generate warn noise unless routed to non-production indexes. tlsSecurityProfile fields vary by exporter flattening; false tls_drift_hint rows appear until FIELDALIAS maps stabilize after OpenShift minor upgrades. Maintenance suppression misuse can hide genuine outages if tickets are left open; expire lookup rows on schedule and require human approval for long suppress windows.

## References

- [OpenShift Documentation — Ingress Operator](https://docs.openshift.com/container-platform/latest/networking/networking_operators/ingress-operator.html)
- [OpenShift Documentation — Managing ingress sharding](https://docs.openshift.com/container-platform/latest/networking/configuring_ingress_cluster_traffic/ingress-sharding.html)
- [OpenShift Documentation — TLS security profiles](https://docs.openshift.com/container-platform/latest/security/tls_security_profiles.html)
- [OpenShift REST API Reference — IngressController](https://docs.openshift.com/container-platform/latest/rest_api/operator_apis/ingresscontroller-operator-openshift-io-v1.html)
- [OpenShift REST API Reference — APIServer cluster config](https://docs.openshift.com/container-platform/latest/rest_api/config_apis/apiserver-config-openshift-io-v1.html)
- [GitHub — openshift/cluster-ingress-operator](https://github.com/openshift/cluster-ingress-operator)
- [GitHub — openshift/api operator IngressController types](https://github.com/openshift/api/blob/master/operator/v1/types_ingress.go)
- [OpenShift — Container Platform product page](https://www.openshift.com/products/container-platform)
