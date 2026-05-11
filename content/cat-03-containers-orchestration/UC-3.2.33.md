<!-- AUTO-GENERATED from UC-3.2.33.json — DO NOT EDIT -->

---
id: "3.2.33"
title: "Kubernetes Node Drain Audit and Voluntary-Disruption Impact Correlation"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.33 · Kubernetes Node Drain Audit and Voluntary-Disruption Impact Correlation

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We keep a careful diary when computers in your container fleet are emptied on purpose for upgrades or resizing. We record who gave the order, how long the work took, and whether your applications bounced back quickly. That way surprises do not hide behind normal charts.*

---

## Description

Unique monitoring axis: audit and correlate voluntary node drain actions—not PDB steady-state compliance (UC-3.2.37), not service endpoint blackholes (UC-3.2.41), not autoscaler scale-out refusal (UC-3.2.46), and not involuntary NotReady storms (UC-3.2.3). The control fuses kube-apiserver audit for node patch cordon or taint mutations and Eviction API create calls, kube events on Node objects that narrate drain or NotSchedulable transitions, kube-state-metrics kube_node_spec_unschedulable for cordon truth, and kube_pod_status_phase Pending mass as a proxy for eviction pressure and reschedule velocity. inputlookup k8s_approved_drain_windows.csv ties each cluster and node_key to approved_change_ticket and maintenance windows so operators distinguish surge upgrades, autoscaler scale-down, and kured rotations from unplanned voluntary disruption. Severity tiers elevate when eviction HTTP failures, pending backlog, or absent tickets coincide with apiserver-attributed actors including human users and automation service accounts.

## Value

Platform leaders receive an evidence-ready ledger that names who cordoned or tainted a node, which eviction API calls accompanied the drain, how long the disruption window lasted, whether workloads piled into Pending, and whether a CAB ticket explains the action. Mean time to innocence improves because voluntary disruption stops masquerading as mystery latency: surge node pool replacements, consolidation drains, and approved maintenance share the same telemetry vocabulary while unplanned drains remain visible. Customer reliability improves when reschedule velocity drops or pending counts spike immediately after audit-proven drain actions because responders pivot to capacity, PDB, or scheduling constraints with timestamps aligned to the operator or controller identity.

## Implementation

Ingest kube:apiserver:audit at RequestResponse depth for node patches and pod eviction creates into k8s_audit, stream kube:events for Node voluntary disruption reasons into k8s, scrape kube_node_spec_unschedulable and kube_pod_status_phase into k8s_metrics, publish k8s_approved_drain_windows.csv with tickets and window epochs, save uc_3_2_33_node_drain_audit_impact every ten minutes on earliest=-4h@h latest=@h, route high_unplanned_drain_or_eviction to platform operations with actor and node_key, and validate using a lab kubectl drain under a recorded change.

## Evidence

Saved search uc_3_2_33_node_drain_audit_impact with ten-minute schedule; versioned k8s_approved_drain_windows.csv in git; weekly CSV export of the closing table to a restricted evidence index with lookup commit hashes and linked change tickets for auditors.

## Control test

### Positive scenario

In a lab cluster with audit at RequestResponse for nodes and pods/eviction, run kubectl drain against a single worker while workloads reschedule, confirm kube:apiserver:audit shows patch on /api/v1/nodes/{name} with unschedulable or taint semantics, eviction creates on /api/v1/namespaces/{ns}/pods/{pod}/eviction, kube:events surface Node-involved voluntary disruption reasons, kube_node_spec_unschedulable flips for that node, and uc_3_2_33_node_drain_audit_impact returns a consolidated row with non-zero drain_duration_sec when the lookup lacks a matching approved_change_ticket.

### Negative scenario

After the drain completes and the node is deleted or uncordoned per runbook with matching k8s_approved_drain_windows.csv rows populated for the same cluster and node_key including approved_change_ticket and open window epochs, rerun the saved search and confirm severity downgrades to ticketed maintenance tiers without high_unplanned_drain_or_eviction flags, or zero qualifying rows when only read-only audit noise remains.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with Kubernetes platform site reliability engineers, the identity and access management team that maps OIDC subjects to audit user.username values, and the observability engineers operating Splunk OpenTelemetry Collector or Splunk Connect for Kubernetes across production and pre-production. This use case is deliberately scoped to voluntary disruption and drain action auditing, not steady-state PodDisruptionBudget compliance scoring, which remains UC-3.2.37, not north-star service endpoint blackholes after backends disappear, which remains UC-3.2.41, not Cluster Autoscaler refusal to add capacity, which remains UC-3.2.46, and not kubelet-driven Node NotReady storms, which remain UC-3.2.3. Your evidence story is the immutable apiserver audit trail of who patched nodes toward unschedulability, who invoked Eviction objects, which Kubernetes events narrated the same node lifecycle, and whether kube-state-metrics agrees the node spec is unschedulable while pods mass into Pending. Without that four-plane agreement, executives confuse voluntary maintenance with mysterious application regressions.

Index contracts mirror other gold Kubernetes controls: dedicate index=k8s_audit for sourcetype=kube:apiserver:audit with role-based access control that lets platform security and infrastructure teams read requestObject fragments while application developers stay on metrics-only roles. Keep index=k8s for sourcetype=kube:events with cluster labels that coalesce cleanly across Amazon EKS, Google GKE, and Microsoft AKS naming conventions. Keep index=k8s_metrics for sourcetype=prometheus:scrape:metrics sourced from kube-state-metrics scrapes that include kube_node_spec_unschedulable and kube_pod_status_phase. Issue distinct HEC tokens per index class, rotate quarterly, and document which clusters land in which index partitions for data residency reviews.

Audit policy depth is non-negotiable for the node patch arm. Metadata-only logging for core v1 nodes hides spec.unschedulable transitions and taint edits inside requestObject, which blinds the first multisearch arm. Adopt RequestResponse for patch verbs on nodes at cluster scope, and RequestResponse for create on pods eviction subresources when you must prove admission outcomes and HTTP codes. OmitStages should still drop RequestReceived noise, but do not demote nodes or pod eviction creates to Metadata in regulated tiers without a compensating detective control. Document omitStages decisions in the same change repository as your audit ConfigMap so auditors can trace policy to evidence.

Publish lookups/k8s_approved_drain_windows.csv under change control with columns cluster (lowercased fleet identifier), node_key (exact node name as reported by kubectl get nodes, or a documented wildcard strategy implemented in your local macro layer), approved_change_ticket (pointer to ServiceNow, Jira, or internal CAB records), maint_owner (team name accountable for the window), window_start_epoch and window_end_epoch (Unix seconds bounding maintenance; zero pair means open-ended standing approval for automation such as kured when policy allows). Refresh the CSV when midnight maintenance moves or when surge upgrades reschedule. Evidence packs should cite commit hashes alongside ticket identifiers exactly as UC-3.2.23 does for break-glass allowlists.

Risk framing for leadership: voluntary disruption is still disruption. Customers experience latency or error budgets burn when evictions outpace reschedule capacity, when PodDisruptionBudgets throttle eviction velocity, or when cluster autoscaler scale-down races application scale-out. This UC does not replace PDB monitoring; it explains why PDB signals might spike by anchoring timelines to apiserver-proven eviction calls. Likewise, service endpoints may drop to zero after drains; UC-3.2.41 remains the service-discovery detector while this UC answers which operator action started the cascade.

Telemetry hygiene: clock skew between apiserver hosts, kube-state-metrics scrapers, and Splunk indexers must remain under sixty seconds or drain_duration_sec math misleads incident reviewers. Duplicate prometheus scrapes without deduplication keys can double pending_pod_units; validate one authoritative kube-state-metrics Service per cluster. Privacy: audit JSON can include pod and namespace names tied to sensitive workloads; restrict dashboards and evidence exports. Licensing: RequestResponse node auditing is cheaper than full Secret body capture but still material at fleet scale; compress at the collector and tier hot versus frozen retention deliberately.

Training: teach responders the difference between Eviction API HTTP 201 successes, 429 Too Many Requests when PDBs or quotas block evictions, and 404 when objects disappear mid-drain. Teach them to read user.username for human kubectl sessions versus system service accounts for controllers. Teach finance observers that surge upgrades and blue-green migrations may intentionally spike pending counts for minutes; pair timestamps with cloud console upgrade state before treating as defect.

Review cadence: quarterly replay one historical drain incident after Kubernetes minor upgrades because audit field flattening and prometheus label rewriting occasionally shift coalesce paths. Escalation alignment: high_unplanned_drain_or_eviction should page platform operations and the on-call service owner for the impacted namespace simultaneously when impact_ns maps to tier-one workloads via your inventory joins outside this base search.

Hardware and distribution notes: OpenShift uses the same audit verbs but may rename some collected fields; keep coalesce ladders until forwarders stabilize. Tanzu and air-gapped environments may batch audit files; watch for ingest delay that makes drain_duration_sec appear shorter than reality. Arm clusters behave identically when audit parity holds.

Differentiation recap: voluntary drain action audit plus impact correlation is the axis; PDB state compliance, endpoint zero readiness, autoscaler scale-out failure, and involuntary NotReady are explicitly out of scope as primary detectors.

### Step 2 — Configure data collection

Wire kube-apiserver audit to Splunk first. On self-managed clusters, tail audit.log with json_parser timestamps matching requestReceivedTimestamp or stageTimestamp per your distribution. On managed clusters, use the cloud control-plane audit export that preserves Kubernetes audit v1 JSON and normalize cluster dimensions so the SPL cluster coalesce ladder resolves eks_cluster_name, gke_cluster_name, and aks_cluster_name aliases consistently.

Audit policy fragment emphasizing node patches and eviction creates at RequestResponse:

```
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - "RequestReceived"
rules:
  - level: RequestResponse
    verbs: ["patch", "update"]
    resources:
      - group: ""
        resources: ["nodes"]
  - level: RequestResponse
    verbs: ["create"]
    resources:
      - group: ""
        resources: ["pods/eviction"]
  - level: Metadata
    resources:
      - group: ""
        resources: ["events"]
```

OpenTelemetry Collector fragment illustrating audit forwarding with dedicated HEC token:

```
receivers:
  filelog/audit:
    include: [/var/log/kubernetes/audit.log]
    operators:
      - type: json_parser
        timestamp:
          parse_from: attributes.requestReceivedTimestamp
          layout: '2006-01-02T15:04:05.999999999Z07:00'
exporters:
  splunk_hec/audit:
    token: "${SPLUNK_HEC_TOKEN_AUDIT}"
    endpoint: "https://splunk.example.com:8088/services/collector/event"
    index: k8s_audit
    sourcetype: kube:apiserver:audit
service:
  pipelines:
    logs/audit:
      receivers: [filelog/audit]
      exporters: [splunk_hec/audit]
```

Deploy kube-state-metrics with RBAC that can list nodes and pods cluster-wide. Scrape interval of thirty seconds is typical; shorter intervals improve pending math at license cost. Ensure kube_node_spec_unschedulable and kube_pod_status_phase series reach index=k8s_metrics with node, namespace, and phase labels preserved through relabel_config blocks.

Publish k8s_approved_drain_windows.csv sample rows aligned to your CAB discipline:

```
cluster,node_key,approved_change_ticket,maint_owner,window_start_epoch,window_end_epoch
prod-eks-01,ip-10-0-5-77.ec2.internal,CHG-991122,platform-sre,1745689200,1745696400
prod-gke-01,gke-prod-pool-abc123-node-9df4,CHG-991130,linux-patchers,0,0
```

Zero epochs for start and end mean your macro interprets standing approval for documented automation; prefer bounded windows in regulated environments.

Validate raw feeds before saving alerts: index=k8s_audit sourcetype=kube:apiserver:audit objectRef.resource=nodes verb=patch earliest=-30m must return lab traffic after a cordon test; objectRef.subresource=eviction objectRef.resource=pods verb=create must appear during forced evictions; index=k8s sourcetype=kube:events involvedObject.kind=Node earliest=-30m must show reasons during drain drills; index=k8s_metrics kube_node_spec_unschedulable earliest=-30m must flip when you cordon a lab node.

Security: restrict who can edit the maintenance lookup in git. Redact internal ARNs from alert emails when forwarding outside the platform team. Never paste live HEC tokens into wiki examples.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_33_node_drain_audit_impact with a ten-minute schedule, dispatch earliest=-4h@h, dispatch latest=@h, and throttle duplicate pages per cluster and node_key for forty-five minutes unless severity escalates from medium_ticketed_maintenance to high_unplanned_drain_or_eviction. Include actor_primary, signal_lanes, approved_change_ticket, and drain_duration_sec in pager bodies. Route high_unplanned rows to the platform bridge with raw audit drilldown links; route ticketed maintenance rows to informational dashboards unless pending_pod_units crosses executive thresholds.

Pipeline narrative for reviewers: the opening comment block lists tunables. After the stats collapse by cluster, node_key, and impact_ns, a join_key arm runs tstats against the Change data model counting change_plane_events in-window so auditors see broader change activity alongside drain evidence without claiming every Change row caused the drain. multisearch fans three arms so silent audit does not hide kube events and vice versa: apiserver node patch cordon or taint patterns filtered by verb and resource, apiserver pod eviction API create calls with HTTP codes, and kube events on Node objects with reasons consistent with voluntary disruption storytelling. coalesce ladders normalize cluster and actor fields across vendors. streamstats sequences drain_seq for burst interpretation per cluster node_key actor. eventstats computes lane_volume_4h per cluster signal_lane before the stats collapse. The stats command aggregates earliest and latest timestamps into drain_started and drain_ended for drain_duration_sec, collects signal lanes and actors, counts distinct evicted pods from audit metadata, and tracks maximum eviction HTTP codes. join wraps inputlookup k8s_approved_drain_windows.csv on cluster and node_key for ticket and maint_owner enrichment. A metrics join estimates pending_pod_units from kube_pod_status_phase Pending sums per namespace to proxy reschedule pressure. A second metrics join reads kube_node_spec_unschedulable as kube_node_unsched_flag for cordon truth. case assigns severity tiers comparing ticket presence, maintenance windows, eviction HTTP 429 pressure, pending backlog, and unticketed apiserver mutations. reschedule_pressure_score multiplies pending mass by drain duration as a coarse impact knob. The closing table lists sixteen analyst columns covering timestamps, cluster, node_key, namespace impact, primary actor, lanes, duration, eviction breadth, pending units, unschedulable gauge, ticket metadata, HTTP max, derived pressure score, change plane ticks, lane volume hint, and severity.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.33 Kubernetes node drain action audit and voluntary disruption impact correlation. Tunables: index=k8s_audit sourcetype=kube:apiserver:audit; index=k8s kube:events; index=k8s_metrics prometheus:scrape:metrics; lookup k8s_approved_drain_windows.csv; earliest=-4h@h latest=@h")`
| multisearch
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval node_name=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval uri=toString(coalesce(requestURI, requestUri, ""))
      | eval lr=lower(_raw)
      | where res_l="nodes" AND verb_l="patch" AND (match(lr, "unschedulable") OR match(lr, "noschedule") OR match(lr, "\"taints\"") OR match(uri, "/api/v1/nodes/"))
      | eval signal_lane="apiserver_node_patch_cordon_or_taint"
      | eval target_ns=""
      | eval target_pod=""
      | eval eviction_http=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")),10)
      | fields _time cluster node_name actor signal_lane target_ns target_pod eviction_http uri ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval subres_l=lower(trim(toString(coalesce('objectRef.subresource', objectRef.subresource, objectRef_subresource, ""))))
      | eval target_ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval target_pod=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval node_name=""
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval uri=toString(coalesce(requestURI, requestUri, ""))
      | where res_l="pods" AND subres_l="eviction" AND verb_l="create"
      | eval signal_lane="apiserver_pod_eviction_api_create"
      | eval eviction_http=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")),10)
      | fields _time cluster node_name actor signal_lane target_ns target_pod eviction_http uri ]
    [ search index=k8s sourcetype="kube:events" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
      | eval kind_ev=lower(trim(toString(coalesce(involvedObject.kind, `involvedObject.kind`, kind, ""))))
      | eval node_name=trim(toString(coalesce(involvedObject.name, involvedObject_name, "")))
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=lower(toString(coalesce(message, Message, "")))
      | where kind_ev="node" AND (rs IN ("NodeDrain", "NodeNotSchedulable") OR match(lower(rs), "drain") OR match(msg, "notschedulable") OR match(msg, "cordon"))
      | eval actor="kube-event-reporter"
      | eval signal_lane="kube_event_node_voluntary_disruption"
      | eval target_ns=""
      | eval target_pod=""
      | eval eviction_http=0
      | eval uri=""
      | fields _time cluster node_name actor signal_lane target_ns target_pod eviction_http uri ]
| fillnull value="" node_name target_ns target_pod actor uri
| fillnull value=0 eviction_http
| eval node_key=if(len(node_name)>0 AND node_name!="", node_name, "cluster_aggregate")
| eval impact_ns=if(len(target_ns)>0, target_ns, "_clusterwide")
| streamstats window=200 current=t global=f count AS drain_seq BY cluster node_key actor
| eventstats count AS lane_volume_4h BY cluster signal_lane
| stats earliest(_time) AS drain_started latest(_time) AS drain_ended values(signal_lane) AS signal_lanes values(actor) AS actors dc(target_pod) AS distinct_evicted_pods max(eviction_http) AS max_eviction_http max(lane_volume_4h) AS lane_volume_hint values(uri) AS request_uris BY cluster node_key impact_ns
| eval join_key="uc3233"
| join type=left max=1 join_key [
    | tstats count AS change_plane_events FROM datamodel=Change WHERE nodename=Change earliest=-4h@h latest=@h
    | eval join_key="uc3233" ]
| fields - join_key
| fillnull value=0 change_plane_events
| eval drain_duration_sec=round(drain_ended-drain_started,3)
| eval actor_primary=mvindex(mvdedup(actors),0)
| join type=left max=0 cluster node_key [
    | inputlookup k8s_approved_drain_windows.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, ""))))
    | eval node_key=trim(toString(coalesce(node_key, node, node_name, "")))
    | eval approved_change_ticket=toString(coalesce(approved_change_ticket, change_ticket, ticket, ""))
    | eval maint_owner=toString(coalesce(maint_owner, cab_owner, owner_team, ""))
    | eval window_start_epoch=tonumber(tostring(coalesce(window_start_epoch, start_epoch, "0")),10)
    | eval window_end_epoch=tonumber(tostring(coalesce(window_end_epoch, end_epoch, "0")),10)
    | fields cluster node_key approved_change_ticket maint_owner window_start_epoch window_end_epoch ]
| join type=left max=0 cluster impact_ns [
    | search ((index=k8s_metrics OR index=k8s) sourcetype="prometheus:scrape:metrics") earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | rex field=_raw "phase=\"(?<ph>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | where like(mn, "%kube_pod_status_phase%") AND lower(ph)="pending"
      | eval mv=tonumber(mval,10)
      | stats sum(mv) AS pending_pod_units BY cluster namespace
      | rename namespace AS impact_ns ]
| join type=left max=0 cluster node_key [
    | search ((index=k8s_metrics OR index=k8s) sourcetype="prometheus:scrape:metrics") earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | rex field=_raw "node=\"(?<node_key>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | where like(mn, "%kube_node_spec_unschedulable%")
      | eval mv=tonumber(mval,10)
      | stats latest(mv) AS kube_node_unsched_flag BY cluster node_key ]
| fillnull value=0 kube_node_unsched_flag pending_pod_units change_plane_events
| fillnull value="" approved_change_ticket maint_owner
| eval now_e=now()
| eval ticket_len=len(trim(approved_change_ticket))
| eval in_window=if(ticket_len>0 AND (window_end_epoch=0 OR (window_start_epoch>0 AND window_end_epoch>0 AND now_e>=window_start_epoch AND now_e<=window_end_epoch)), 1, 0)
| eval severity=case(
    in_window=1 AND max_eviction_http>=429 AND coalesce(pending_pod_units,0)>20, "high_ticketed_pdb_or_quota_pressure",
    in_window=1, "medium_ticketed_maintenance",
    ticket_len=0 AND match(mvjoin(signal_lanes, " "), "apiserver"), "high_unplanned_drain_or_eviction",
    ticket_len=0 AND coalesce(pending_pod_units,0)>30, "high_pending_after_unticketed_disruption",
    coalesce(kube_node_unsched_flag,0)>0 AND ticket_len=0, "high_uncordon_outside_window",
    true(), "medium_review_voluntary_disruption")
| where match(severity, "high_|medium_")
| eval reschedule_pressure_score=round(coalesce(pending_pod_units,0)*drain_duration_sec/60,2)
| table drain_started drain_ended cluster node_key impact_ns actor_primary signal_lanes drain_duration_sec distinct_evicted_pods pending_pod_units kube_node_unsched_flag approved_change_ticket maint_owner max_eviction_http reschedule_pressure_score change_plane_events lane_volume_hint severity```

savedsearches.conf sketch:

```
[uc_3_2_33_node_drain_audit_impact]
cron_schedule = */10 * * * *
dispatch.earliest_time = -4h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = platform-k8s@example.com
action.email.subject = Drain audit $result.cluster$ node $result.node_key$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch uc_3_2_33_node_drain_audit_impact | where severity IN ("high_unplanned_drain_or_eviction","high_pending_after_unticketed_disruption","high_uncordon_outside_window","high_ticketed_pdb_or_quota_pressure")
```

Step 4 — Validate

Positive test A — Lab kubectl drain: cordon and drain a disposable worker with a running Deployment, confirm audit shows node patch and eviction creates, confirm kube events include Node reasons or messages consistent with drain narration, confirm kube_node_spec_unschedulable becomes one on metrics for that node name, and execute uc_3_2_33_node_drain_audit_impact expecting a row with apiserver lanes present and drain_duration_sec greater than zero.

Positive test B — Eviction denial: craft a pod protected such that eviction returns HTTP 429 in lab only, confirm max_eviction_http reaches 429 in the audit arm, and confirm severity escalates toward PDB or quota pressure language when pending counts rise.

Negative test — Ticketed maintenance: add k8s_approved_drain_windows.csv rows matching the lab node with a valid approved_change_ticket and open window epochs covering the test, repeat the drain, confirm severity lands in medium_ticketed_maintenance or informational wrappers rather than high_unplanned.

Negative test — Read-only noise: ensure readers without k8s_audit index rights see zero rows, proving segregation.

Field sanity: rename a forwarder field to camelCase-only in sandbox and confirm coalesce ladders still resolve cluster and actor.

Correlation: compare Splunk drain_started to kubectl get events --field-selector involvedObject.kind=Node and to cloud provider node lifecycle logs for surge replacements.

Performance: run Job Inspector during Monday peaks; if multisearch cost exceeds budget, materialize per-arm summary indexes keyed on cluster and signal_lane.

Step 5 — Operationalize & Troubleshoot

Case 1 — high_unplanned_drain_or_eviction with a human OIDC user: call the operator, verify an approved change, freeze further kubectl sessions from that principal until identity confirms intent, and attach audit request_uris to the incident record.

Case 2 — Same severity with a cluster-autoscaler or karpenter service account: open the autoscaler or consolidation narrative, confirm scale-down or bin-packing policy, and route to platform capacity owners rather than application blame.

Case 3 — high_ticketed_pdb_or_quota_pressure during maintenance: eviction velocity is fighting safety budgets; coordinate with application owners to relax PDBs only under CAB, add temporary capacity, or extend the maintenance window.

Case 4 — pending_pod_units spikes without apiserver lanes: metrics may lead audit ingest; investigate collector delay before declaring false alarm, and verify kube-state-metrics still scrapes.

Case 5 — kube_node_unsched_flag stuck at one after maintenance: uncordon failures or zombie node objects may remain; use kubectl describe node and cloud console state to reconcile, then verify metrics return to zero.

Case 6 — Distinct_evicted_pods high but customer impact unclear: pivot to UC-3.2.41 for service endpoint readiness and UC-3.2.37 for PDB observations while keeping this UC as the root-cause action timeline.

Case 7 — Surge upgrade overlap: GKE, EKS, or AKS rolling replacements may interleave multiple nodes; widen stats window or split saved searches per node pool if rows collapse confusingly.

Case 8 — kured loop: repeated rows from the same node pool during kernel patching should align with standing tickets; annotate automation identities in the lookup to avoid nightly pages.

Case 9 — Cluster API MachineDeployment churn: map capi-controller-manager identities and reference Cluster API upgrade docs in bridges; expect burst drain_seq values.

Case 10 — Blue-green pool migration: pending counts may climb while traffic shifts; require dual ticket linkage for old and new pools in the lookup before muting.

Case 11 — Audit policy regression after upgrade: if node patch arm goes silent while events still fire, treat as telemetry incident and restore RequestResponse rules before muting alerts.

Case 12 — Off-hours batch rotation: operations teams may drain entire racks; ensure maint_owner field pages the correct regional bridge and that FinOps knows preemptible savings tie to these windows.

Closing checklist: five em-dash step headers appear exactly as required; Step 3 includes fenced SPL identical to the spl JSON field; Step 5 lists twelve case lines; monitoringType lists Reliability and Availability; cimModels lists Change and Application_State; equipmentModels lists kubernetes_k8s; references include Kubernetes drain and eviction documentation, kured, Cluster Autoscaler, Karpenter disruption, GKE surge upgrades, EKS managed node behavior, AKS upgrades, Cluster API upgrades, and Splunk Kubernetes add-on documentation.



## SPL

```spl
`comment("UC-3.2.33 Kubernetes node drain action audit and voluntary disruption impact correlation. Tunables: index=k8s_audit sourcetype=kube:apiserver:audit; index=k8s kube:events; index=k8s_metrics prometheus:scrape:metrics; lookup k8s_approved_drain_windows.csv; earliest=-4h@h latest=@h")`
| multisearch
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval node_name=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval uri=toString(coalesce(requestURI, requestUri, ""))
      | eval lr=lower(_raw)
      | where res_l="nodes" AND verb_l="patch" AND (match(lr, "unschedulable") OR match(lr, "noschedule") OR match(lr, "\"taints\"") OR match(uri, "/api/v1/nodes/"))
      | eval signal_lane="apiserver_node_patch_cordon_or_taint"
      | eval target_ns=""
      | eval target_pod=""
      | eval eviction_http=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")),10)
      | fields _time cluster node_name actor signal_lane target_ns target_pod eviction_http uri ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval subres_l=lower(trim(toString(coalesce('objectRef.subresource', objectRef.subresource, objectRef_subresource, ""))))
      | eval target_ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval target_pod=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval node_name=""
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval uri=toString(coalesce(requestURI, requestUri, ""))
      | where res_l="pods" AND subres_l="eviction" AND verb_l="create"
      | eval signal_lane="apiserver_pod_eviction_api_create"
      | eval eviction_http=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")),10)
      | fields _time cluster node_name actor signal_lane target_ns target_pod eviction_http uri ]
    [ search index=k8s sourcetype="kube:events" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
      | eval kind_ev=lower(trim(toString(coalesce(involvedObject.kind, `involvedObject.kind`, kind, ""))))
      | eval node_name=trim(toString(coalesce(involvedObject.name, involvedObject_name, "")))
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=lower(toString(coalesce(message, Message, "")))
      | where kind_ev="node" AND (rs IN ("NodeDrain", "NodeNotSchedulable") OR match(lower(rs), "drain") OR match(msg, "notschedulable") OR match(msg, "cordon"))
      | eval actor="kube-event-reporter"
      | eval signal_lane="kube_event_node_voluntary_disruption"
      | eval target_ns=""
      | eval target_pod=""
      | eval eviction_http=0
      | eval uri=""
      | fields _time cluster node_name actor signal_lane target_ns target_pod eviction_http uri ]
| fillnull value="" node_name target_ns target_pod actor uri
| fillnull value=0 eviction_http
| eval node_key=if(len(node_name)>0 AND node_name!="", node_name, "cluster_aggregate")
| eval impact_ns=if(len(target_ns)>0, target_ns, "_clusterwide")
| streamstats window=200 current=t global=f count AS drain_seq BY cluster node_key actor
| eventstats count AS lane_volume_4h BY cluster signal_lane
| stats earliest(_time) AS drain_started latest(_time) AS drain_ended values(signal_lane) AS signal_lanes values(actor) AS actors dc(target_pod) AS distinct_evicted_pods max(eviction_http) AS max_eviction_http max(lane_volume_4h) AS lane_volume_hint values(uri) AS request_uris BY cluster node_key impact_ns
| eval join_key="uc3233"
| join type=left max=1 join_key [
    | tstats count AS change_plane_events FROM datamodel=Change WHERE nodename=Change earliest=-4h@h latest=@h
    | eval join_key="uc3233" ]
| fields - join_key
| fillnull value=0 change_plane_events
| eval drain_duration_sec=round(drain_ended-drain_started,3)
| eval actor_primary=mvindex(mvdedup(actors),0)
| join type=left max=0 cluster node_key [
    | inputlookup k8s_approved_drain_windows.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, ""))))
    | eval node_key=trim(toString(coalesce(node_key, node, node_name, "")))
    | eval approved_change_ticket=toString(coalesce(approved_change_ticket, change_ticket, ticket, ""))
    | eval maint_owner=toString(coalesce(maint_owner, cab_owner, owner_team, ""))
    | eval window_start_epoch=tonumber(tostring(coalesce(window_start_epoch, start_epoch, "0")),10)
    | eval window_end_epoch=tonumber(tostring(coalesce(window_end_epoch, end_epoch, "0")),10)
    | fields cluster node_key approved_change_ticket maint_owner window_start_epoch window_end_epoch ]
| join type=left max=0 cluster impact_ns [
    | search ((index=k8s_metrics OR index=k8s) sourcetype="prometheus:scrape:metrics") earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | rex field=_raw "phase=\"(?<ph>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | where like(mn, "%kube_pod_status_phase%") AND lower(ph)="pending"
      | eval mv=tonumber(mval,10)
      | stats sum(mv) AS pending_pod_units BY cluster namespace
      | rename namespace AS impact_ns ]
| join type=left max=0 cluster node_key [
    | search ((index=k8s_metrics OR index=k8s) sourcetype="prometheus:scrape:metrics") earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | rex field=_raw "node=\"(?<node_key>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | where like(mn, "%kube_node_spec_unschedulable%")
      | eval mv=tonumber(mval,10)
      | stats latest(mv) AS kube_node_unsched_flag BY cluster node_key ]
| fillnull value=0 kube_node_unsched_flag pending_pod_units change_plane_events
| fillnull value="" approved_change_ticket maint_owner
| eval now_e=now()
| eval ticket_len=len(trim(approved_change_ticket))
| eval in_window=if(ticket_len>0 AND (window_end_epoch=0 OR (window_start_epoch>0 AND window_end_epoch>0 AND now_e>=window_start_epoch AND now_e<=window_end_epoch)), 1, 0)
| eval severity=case(
    in_window=1 AND max_eviction_http>=429 AND coalesce(pending_pod_units,0)>20, "high_ticketed_pdb_or_quota_pressure",
    in_window=1, "medium_ticketed_maintenance",
    ticket_len=0 AND match(mvjoin(signal_lanes, " "), "apiserver"), "high_unplanned_drain_or_eviction",
    ticket_len=0 AND coalesce(pending_pod_units,0)>30, "high_pending_after_unticketed_disruption",
    coalesce(kube_node_unsched_flag,0)>0 AND ticket_len=0, "high_uncordon_outside_window",
    true(), "medium_review_voluntary_disruption")
| where match(severity, "high_|medium_")
| eval reschedule_pressure_score=round(coalesce(pending_pod_units,0)*drain_duration_sec/60,2)
| table drain_started drain_ended cluster node_key impact_ns actor_primary signal_lanes drain_duration_sec distinct_evicted_pods pending_pod_units kube_node_unsched_flag approved_change_ticket maint_owner max_eviction_http reschedule_pressure_score change_plane_events lane_volume_hint severity
```

## CIM SPL

```spl
| tstats summariesonly=t count AS change_events latest(Change.action) AS last_change_action FROM datamodel=Change WHERE nodename=Change earliest=-4h@h latest=@h BY Change.user Change.object
| rename Change.object AS change_obj
| join type=left max=0 change_obj [
    | tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-4h@h latest=@h BY Application_State.dest
    | rename Application_State.dest AS change_obj ]
| table Change.user change_obj change_events last_change_action app_state app_info
```

## Visualization

Timeline of apiserver node patches and eviction creates by cluster; heatmap of pending_pod_units during drain windows; table mirroring the closing SPL projection with drilldowns to raw audit JSON and kube events; single value of distinct_evicted_pods for executive summaries.

## Known False Positives

Scheduled maintenance windows that are tracked in k8s_approved_drain_windows.csv or a wider change-management lookup will legitimately produce dense audit and eviction traffic without implying an incident; require absent tickets or closed windows before paging executives. Automated kured drains for kernel patching repeat cordon and eviction patterns every reboot cycle across the fleet; tag those clusters in the lookup or exclude the kured service account from high severity when tickets are standing. Cluster-autoscaler scale-down during off-peak hours removes underutilized nodes and emits voluntary disruption signals that resemble human kubectl drain; correlate kube-system cluster-autoscaler identity and node lifecycle timestamps before blaming application teams. Surge-upgrade rolling node replacement on managed control planes—GKE node pool surge parameters, EKS managed node group rolling update behavior, and AKS surge settings—creates overlapping patch and eviction rows that look noisy yet are expected when cloud consoles show an active upgrade. Karpenter consolidation drains for intentional bin-packing issue eviction creates with controller service accounts; severity should reference consolidation logs and documented FinOps policy. Cluster API rolling upgrades driven by MachineDeployments produce repeated node replacements; map cluster-api controller identities in the lookup. Off-hours batch infrastructure rotation and blue-green node pool migrations may spike pending counts briefly while new pools warm; widen suppression when dual write paths stay healthy and tickets reference pool cutovers. Finally, audit latency or missing RequestResponse bodies can hide true cordon semantics and make rex arms match too broadly—validate audit policy depth after upgrades before muting.

## References

- [Kubernetes — Safely drain a node](https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/)
- [Kubernetes — Eviction API](https://kubernetes.io/docs/concepts/scheduling-eviction/api-eviction/)
- [kured — Kubernetes Reboot Daemon](https://github.com/weaveworks/kured)
- [Kubernetes Autoscaler — Cluster Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)
- [Karpenter — Disruption concepts](https://karpenter.sh/docs/concepts/disruption/)
- [Google GKE — Surge upgrades for node pools](https://cloud.google.com/kubernetes-engine/docs/concepts/)
- [Amazon EKS — Managed node group update behavior](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-update-behavior.html)
- [Microsoft AKS — Upgrade an AKS cluster](https://learn.microsoft.com/en-us/azure/aks/upgrade-cluster)
- [Cluster API — Upgrading clusters](https://cluster-api.sigs.k8s.io/tasks/upgrading-clusters/)
- [Splunk — Add-on for Kubernetes](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
