<!-- AUTO-GENERATED from UC-3.2.42.json — DO NOT EDIT -->

---
id: "3.2.42"
title: "Kubelet Client/Server Certificate Auto-Rotation Pipeline (Kubelet CSR Renewal Axis)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.42 · Kubelet Client/Server Certificate Auto-Rotation Pipeline (Kubelet CSR Renewal Axis)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch each worker machine refresh its security badges automatically before they expire. If the refresh gets stuck, we warn you early so the machine does not go quiet and programs are not forced to move unexpectedly.*

---

## Description

Unique axis: kubelet client and server certificate auto-rotation through the CSR API—stuck approvals, absent signatures, kubelet disk write failures, expiring kubelet PEM material without pending CSR, rotateCertificates disabled, and serverTLSBootstrap gaps—correlated before Node NotReady. UC-3.2.13 remains the fleet-wide PKI inventory across apiserver, etcd, ingress, webhooks, and cert-manager; this UC does not duplicate that ledger. UC-3.2.3 detects NotReady dwell and eviction blast radius downstream of kubelet silence; this UC targets the renewal pipeline while nodes may still passing heartbeats, closing the prevention window.

## Value

Platform teams reduce surprise node loss by catching CSR backlog and kubelet write failures while kubectl exec still works and workloads remain scheduled. Security and audit stakeholders receive timestamped evidence tying apiserver CSR mutations to kubelet rotation logs and host-derived certificate horizons without waiting for broad PKI scans. Mean time to remediate improves because responders see whether the break is approver policy, signer health, kubelet disk, or disabled rotation flags before application teams interpret the incident as generic cluster instability.

## Implementation

Stand up k8s_audit, k8s_metrics, and k8s_logs with normalized cluster and node labels; deploy kube-state-metrics 2.7+, node_exporter ssl paths for /var/lib/kubelet/pki, and apiserver audit including CSR verbs. Publish kubelet_node_posture.csv for rotation expectations. Save uc_3_2_42_kubelet_csr_renewal_pipeline on a fifteen-minute cadence with earliest=-24h@h, route critical and high severities to platform on-call, and archive weekly exports with lookup commit hashes for crypto drift reviews.

## Evidence

Saved search uc_3_2_42_kubelet_csr_renewal_pipeline; versioned kubelet_node_posture.csv; weekly CSV export of the closing table to a restricted evidence index; drilldowns linking CSR audit objectRef.name, kubelet rotation logs, and ssl cert horizons.

## Control test

### Positive scenario

In lab, block CSR approval for a kubelet renewal while collectors ingest audit, kube-state-metrics, and kubelet logs; run uc_3_2_42_kubelet_csr_renewal_pipeline and expect csr_pipeline_stuck with medium or high severity until approval resumes.

### Negative scenario

Set expect_auto_rotation=0 for a lab node in kubelet_node_posture.csv with synthetic CSR backlog; confirm the saved search filters info rows and does not emit paging severities for that node.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the Kubernetes node lifecycle team, the identity and PKI engineers who operate cluster signers, and the observability engineers who curate Splunk indexes for platform telemetry. This use case isolates the kubelet-specific certificate renewal pipeline: the client credential the kubelet uses to authenticate to the apiserver and the serving credential the apiserver uses when it calls back into the kubelet for exec, logs, and port-forward. Those two PEM chains normally renew automatically through the CertificateSigningRequest API roughly thirty days before Not After, with the kube-controller-manager certificate signer or an external signer completing approval and signature, after which the kubelet writes refreshed material under /var/lib/kubelet/pki and continues heartbeats. UC-3.2.13 inventories fleet-wide PKI surfaces including apiserver, etcd, ingress, webhooks, and cert-manager overlays; it does not replace this narrow kubelet CSR workflow narrative. UC-3.2.3 models Node NotReady dwell and eviction blast radius after kubelet silence; this UC surfaces stuck approvals, absent renewals, disk write failures, and disabled rotation flags while the node may still report Ready, giving responders a prevention window before NotReady storms.

Index and ACL contracts land before parsers. Stand up index=k8s_audit for kube:apiserver:audit JSON with verbs on certificatesigningrequests, index=k8s_metrics for prometheus:scrape:metrics carrying kube-state-metrics kube_certificatesigningrequest_condition series beginning with kube-state-metrics 2.7, and node_exporter ssl certificate expiry metrics that include file paths under /var/lib/kubelet/pki, and index=k8s_logs for kubelet journal or container stdout lines that contain rotation narratives. Issue distinct HEC tokens per index class with least privilege roles so application teams cannot read audit bodies containing CSR PEM requests at RequestResponse depth unless your security standard explicitly allows it; prefer Metadata level for CSR create when counsel requires, while retaining enough objectRef.name signal to correlate pending requests with nodes.

Publish kubelet_node_posture.csv in git with columns cluster, node, node_pool, owner_team, expect_auto_rotation (1 when kubelet config enables rotateCertificates and bootstrap flows you expect in production), signer_profile (for example kubernetes.io/kube-apiserver-client-kubelet versus kubernetes.io/kubelet-serving), notes for managed-cloud opacity, and optional suppress_until_epoch for maintenance. Every row needs an accountable owner_team because CSR backlog incidents bridge platform and security on-call.

RBAC and network policy for collectors: scraping kube-state-metrics may require a cluster-internal ServiceAccount with get/list on certificatesigningrequests for complementary exporters; node_exporter host mounts must not expose private keys to Splunk, only metric labels and timestamps derived from certificate files. Legal review should confirm CSR request PEM bodies are redacted or omitted while still preserving object metadata.

Risk briefing: a pending CSR with Approved condition false is normal for minutes, abnormal for hours. A kubelet log line about rotating certificates without matching audit approve events may indicate an external signer path. serverTLSBootstrap disabled clusters will never mint serving CSRs; tune expect_auto_rotation and signer_profile columns so those estates downgrade noise. Cloud-managed node images on Amazon EKS, Google GKE, and Microsoft AKS may hide kubelet PEM paths from customer scrapers while still surfacing CSR objects in the API; document those rows as managed_signer in the lookup to steer triage toward provider consoles rather than host openssl.

Audit policy fragment guidance: include certificatesigningrequests at Metadata minimum with objectRef.name and username, escalate to Request when you must capture approver annotations for forensic replay. Pair policies with storage retention that satisfies your enterprise standard; this UC assumes thirty days hot in k8s_audit for CSR correlation.

Collector sizing: kubelet logs can be chatty during rotation storms; filter at the agent where possible with include patterns matching rotation phrases to keep license burn predictable. Prometheus scrape intervals of thirty to sixty seconds are adequate because renewal is a day-scale process; sub-minute precision is unnecessary unless you investigate signer outages.

Training: platform on-call should rehearse kubectl get csr, kubectl describe csr, openssl x509 against kubelet-client-current.pem and kubelet-server-current.pem on a lab node, and journalctl -u kubelet traces in parallel with Splunk rows so muscle memory matches the dashboard.

### Step 2 — Configure data collection

Splunk OpenTelemetry Collector for Kubernetes should scrape kube-state-metrics using the prometheus receiver and forward metrics into index=k8s_metrics with sourcetype=prometheus:scrape:metrics while preserving cluster labels you already normalize for UC-3.2.7 control-plane panels. Confirm kube-state-metrics version is 2.7 or newer so kube_certificatesigningrequest_condition metrics exist; if your distro pins an older image, plan an upgrade track because without KSM conditions this search leans harder on audit volume.

Deploy node_exporter on every worker with textfile collector optional but recommended; ensure the ssl certificate collector exposes paths for /var/lib/kubelet/pki/kubelet-client-current.pem and kubelet-server-current.pem when your security model allows reading those public certificates without keys. Some hardened images symlink current to numbered files; follow Linux file permissions so the exporter user can stat the target.

Ship kubelet logs through filelog receiver on systemd hosts or through the daemonset stdout collector on containerized kubelets, mapping sourcetype=kube:kubelet and enriching cluster, node, and cloud region tags identical to UC-3.2.3 node health panels for later correlation. Include drop filters that remove high-volume probe noise but keep strings matching Rotating kubelet client certificate and failure substrings referenced in the primary SPL.

Apiserver audit shipping: use filelog receiver against /var/log/kubernetes/kube-apiserver-audit.log or the equivalent control-plane path, json_parser with timestamp layout, and route sourcetype=kube:apiserver:audit into k8s_audit. Validate verbs include create, update, and approve for certificatesigningrequests.

Example kubelet_node_posture.csv maintenance:

```csv
cluster,node,node_pool,owner_team,expect_auto_rotation,signer_profile,notes
prod-eks,worker-gpu-1,gpu,platform-gpu,1,kubernetes.io/kubelet-serving,openssl ok on host
lab-kind,kind-worker,dev,platform-lab,0,kubernetes.io/kube-apiserver-client-kubelet,manual csr policy
```

Example audit policy rule emphasizing CSR without dumping full PEM when counsel requires minimalism:

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: Metadata
    verbs: ["create", "update", "patch", "delete"]
    resources:
      - group: "certificates.k8s.io"
        resources: ["certificatesigningrequests", "certificatesigningrequests/approval"]
```

OpenTelemetry Collector snippet for splitting metrics and audit:

```yaml
exporters:
  splunk_hec/metrics:
    token: "${SPLUNK_HEC_TOKEN_METRICS}"
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
  splunk_hec/audit:
    token: "${SPLUNK_HEC_TOKEN_AUDIT}"
    index: k8s_audit
    sourcetype: kube:apiserver:audit
service:
  pipelines:
    metrics:
      receivers: [prometheus]
      exporters: [splunk_hec/metrics]
    logs/audit:
      receivers: [filelog/audit]
      exporters: [splunk_hec/audit]
```

Pre-flight searches:

```text
index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-1h latest=now kube_certificatesigningrequest_condition
| head 20
```

```text
index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-1h latest=now certificatesigningrequests
| head 20
```

Zero-result investigations should block production alerting until collectors succeed.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_42_kubelet_csr_renewal_pipeline with schedule every fifteen minutes and dispatch window earliest=-24h@h latest=now to match the bounded window in the search. Throttle duplicate rows per cluster and node for one hour unless severity escalates from medium to high or critical tiers. Wire email and webhook actions for critical_kubelet_rotation_failure and critical_expiring_no_renewal_signal, route medium_csr_signing_backlog to a platform queue during business hours, and attach the kubelet_node_posture.csv git SHA in the alert payload for evidence packs.

Pipeline narrative for reviewers: multisearch fans four telemetry lanes in parallel. The audit arm captures CSR object activity and derives node identity from system:node service account hints in request bodies when present. The kube-state-metrics arm reads kube_certificatesigningrequest_condition and flags Approved status false as a pending-approval style backlog signal. The kubelet log arm confirms positive rotation narratives and error strings that imply write failures or expired certificates. The node_exporter arm supplies ssl cert not-after epochs for PEM paths under kubelet/pki so Splunk can compute days_to_expiry even when API objects look healthy. After four-hour buckets consolidate bursts, streamstats scans a three-bucket window per node to detect renewal_gap_risk runs that persist across quarters of a day. The inputlookup join adds expect_auto_rotation and signer expectations so clusters that intentionally disable automation do not page. The tstats join against Inventory supplies freshness context for dashboards that sit next to CIM Inventory summaries without forcing this alert to depend on acceleration for correctness.

Understanding severity: case() maps kubelet_rotation_fault to critical rotation failure, combines renewal_gap_risk with short horizons for critical expiring without renewal signals, treats CSR backlog with two-week horizon as high, and uses medium for signing backlog without imminent disk horizon. eventstats counts impacted_nodes per cluster for blast-radius captions in ITSI or email subjects.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.2.42 Kubelet CSR renewal pipeline — apiserver audit for CSR objects, kube-state-metrics kube_certificatesigningrequest_condition, kubelet rotation logs, node_exporter ssl cert under /var/lib/kubelet/pki. earliest=-24h@h latest=now")`
| multisearch 
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,cluster,objectRef_cluster,""))))
      | eval res_lc=lower(trim(toString(coalesce('objectRef.resource',objectRef.resource,objectRef_resource,""))))
      | eval csr_name=trim(toString(coalesce('objectRef.name',objectRef.name,objectRef_name,"")))
      | eval verb_l=lower(trim(toString(coalesce(verb,""))))
      | where res_lc="certificatesigningrequests" AND len(cluster)>0 AND len(csr_name)>0
      | eval node_hint=lower(trim(toString(coalesce('requestObject.spec.username',requestObject_spec_username,""))))
      | rex field=node_hint "^system:node:(?<node_from_sa>.+)$"
      | eval node=lower(trim(coalesce(node_from_sa,csr_name)))
      | eval lane="audit_csr_activity"
      | fields _time cluster node lane csr_name verb_l ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,cluster,eks_cluster_name,gke_cluster_name,aks_cluster_name,""))))
      | eval mn=lower(trim(toString(coalesce(__name__,metric_name,name,""))))
      | where like(mn,"kube_certificatesigningrequest_condition") AND len(cluster)>0
      | rex field=_raw "condition=\"(?<csr_cond>[^\"]+)\""
      | rex field=_raw "status=\"(?<csr_stat>[^\"]+)\""
      | rex field=_raw "certificatesigningrequest=\"(?<csr_nm>[^\"]+)\""
      | eval node=lower(trim(toString(csr_nm)))
      | eval lane="ksm_csr_condition"
      | eval ksm_csr_pending=if(lower(csr_cond)=="approved" AND csr_stat=="false",1,0)
      | fields _time cluster node lane ksm_csr_pending csr_cond csr_stat ]
    [ search index=k8s_logs (sourcetype="kube:kubelet" OR sourcetype="kube:container:kubelet" OR source="kubelet") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,cluster,""))))
      | eval node=lower(trim(toString(coalesce(host,hostname,k8s_node_name,kubernetes_io_hostname,nodename,""))))
      | eval lr=lower(_raw)
      | where match(lr,"rotating kubelet client certificate") OR match(lr,"rotating kubelet server certificate") OR match(lr,"failed to rotate certificate") OR match(lr,"x509: certificate has expired or is not yet valid")
      | eval lane="kubelet_rotation_log"
      | eval log_fault=if(match(lr,"failed|error|expired|not yet valid"),1,0)
      | fields _time cluster node lane log_fault ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,cluster,eks_cluster_name,gke_cluster_name,aks_cluster_name,""))))
      | eval mn=lower(trim(toString(coalesce(__name__,metric_name,name,""))))
      | where (like(mn,"ssl_cert_not_after") OR mn=="ssl_certificate_expiry_seconds" OR like(mn,"ssl_cert")) AND match(lower(_raw),"kubelet/pki")
      | rex field=_raw "instance=\"(?<inst>[^\"]+)\""
      | eval node=lower(trim(replace(inst,"^https?://([a-z0-9._-]+)(?::[0-9]+)?.*$","\1")))
      | eval mv=tonumber(tostring(coalesce(value,metric_value,"")),10)
      | eval lane="nodeexp_kubelet_pki_ssl"
      | fields _time cluster node lane mv ]
| eval node=lower(trim(toString(coalesce(node,""))))
| where len(cluster)>0 AND len(node)>0
| bucket _time span=4h
| stats
    earliest(_time) AS first_signal_ts
    latest(_time) AS last_signal_ts
    max(eval(if(lane=="audit_csr_activity",1,0))) AS saw_csr_audit
    max(eval(if(lane=="ksm_csr_condition",ksm_csr_pending,0))) AS ksm_csr_pending_max
    max(eval(if(lane=="kubelet_rotation_log",log_fault,0))) AS kubelet_rotation_fault
    max(eval(if(lane=="kubelet_rotation_log",1,0))) AS kubelet_rotation_any
    max(eval(if(lane=="nodeexp_kubelet_pki_ssl",mv,null()))) AS ssl_not_after_epoch
    values(lane) AS lanes_seen
  BY cluster node _time
| eval days_to_expiry=if(isnotnull(ssl_not_after_epoch) AND ssl_not_after_epoch>1000000000, round((ssl_not_after_epoch-now())/86400,2), null())
| eval csr_pipeline_stuck=if(ksm_csr_pending_max>0 OR (saw_csr_audit>0 AND kubelet_rotation_fault>0),1,0)
| eval renewal_gap_risk=if(isnotnull(days_to_expiry) AND days_to_expiry<=7 AND kubelet_rotation_any=0 AND ksm_csr_pending_max=0 AND saw_csr_audit=0,1,0)
| sort 0 + cluster + node + _time
| streamstats window=3 current=t global=f max(renewal_gap_risk) AS renewal_gap_run BY cluster node
| stats
    max(renewal_gap_run) AS renewal_gap_run_max
    max(renewal_gap_risk) AS renewal_gap_risk_max
    max(csr_pipeline_stuck) AS csr_pipeline_stuck_max
    max(kubelet_rotation_fault) AS kubelet_rotation_fault_max
    max(saw_csr_audit) AS saw_csr_audit_max
    max(ksm_csr_pending_max) AS ksm_csr_pending_max
    max(kubelet_rotation_any) AS kubelet_rotation_any_max
    latest(ssl_not_after_epoch) AS ssl_not_after_epoch
    latest(days_to_expiry) AS days_to_expiry
    latest(lanes_seen) AS lanes_seen
    latest(last_signal_ts) AS last_signal_ts
    earliest(first_signal_ts) AS first_signal_ts
  BY cluster node
| eval csr_pipeline_stuck=csr_pipeline_stuck_max
| eval renewal_gap_risk=if(renewal_gap_run_max>0 OR renewal_gap_risk_max>0,1,0)
| eval kubelet_rotation_fault=kubelet_rotation_fault_max
| eval saw_csr_audit=saw_csr_audit_max
| eval ksm_csr_pending_max=ksm_csr_pending_max
| eval kubelet_rotation_any=kubelet_rotation_any_max
| join type=left max=0 cluster, node [
    | inputlookup kubelet_node_posture.csv
    | eval cluster=lower(trim(toString(cluster)))
    | eval node=lower(trim(toString(node)))
    | eval expect_auto_rotation=tonumber(tostring(coalesce(expect_auto_rotation,"1")),10)
    | eval node_pool=toString(coalesce(node_pool,pool,"unknown_pool"))
    | eval owner_team=toString(coalesce(owner_team,squad,"platform_core"))
    | eval signer_profile=toString(coalesce(signer_profile,signer,"kubernetes.io/kubelet-serving"))
    | fields cluster node expect_auto_rotation node_pool owner_team signer_profile ]
| fillnull value=1 expect_auto_rotation
| fillnull value="unknown_pool" node_pool
| fillnull value="platform_core" owner_team
| fillnull value="kubernetes.io/kubelet-serving" signer_profile
| join type=left max=1 cluster [
    | tstats summariesonly=t latest(_time) AS inventory_fresh_ts FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
    | rename Inventory.dest AS cluster ]
| eval severity=case(
    expect_auto_rotation=0, "info_manual_rotation_cluster",
    kubelet_rotation_fault=1, "critical_kubelet_rotation_failure",
    renewal_gap_risk=1 AND coalesce(days_to_expiry,999)<=3, "critical_expiring_no_renewal_signal",
    renewal_gap_risk=1, "high_expiring_no_renewal_signal",
    csr_pipeline_stuck=1 AND coalesce(days_to_expiry,999)<=14, "high_csr_stuck_near_expiry",
    csr_pipeline_stuck=1, "medium_csr_signing_backlog",
    coalesce(days_to_expiry,999)<=7, "high_disk_cert_horizon",
    coalesce(days_to_expiry,999)<=14, "medium_disk_cert_horizon",
    true(), "low_ok")
| where expect_auto_rotation=1 AND NOT severity IN ("low_ok","info_manual_rotation_cluster")
| eventstats dc(node) AS impacted_nodes BY cluster
| eval action=case(
    severity=="critical_kubelet_rotation_failure", "inspect_kubelet_logs_and_pki_disk",
    severity=="critical_expiring_no_renewal_signal", "emergency_csr_signer_kubelet_bootstrap_review",
    severity=="high_expiring_no_renewal_signal", "validate_rotateCertificates_serverTLSBootstrap",
    severity=="high_csr_stuck_near_expiry", "unblock_csr_approval_and_signer",
    severity=="medium_csr_signing_backlog", "kubectl_get_csr_and_controller_manager_logs",
    severity=="high_disk_cert_horizon", "openssl_x509_and_disk_space_on_node",
    true(), "triage_pipeline")
| table cluster node node_pool owner_team severity days_to_expiry csr_pipeline_stuck renewal_gap_risk kubelet_rotation_fault saw_csr_audit ksm_csr_pending_max impacted_nodes last_signal_ts inventory_fresh_ts signer_profile action
```

savedsearches.conf sketch:

```ini
[uc_3_2_42_kubelet_csr_renewal_pipeline_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -24h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = platform-kubelet-pki@example.com
action.email.subject = Kubelet CSR pipeline $result.severity$ $result.cluster$ $result.node$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch uc_3_2_42_kubelet_csr_renewal_pipeline | where like(severity,"critical%") OR like(severity,"high%")
```

cimSpl points dashboards at Inventory summaries for node fleet coverage audits:

| tstats summariesonly=t latest(_time) AS inv_ts FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
| rename Inventory.dest AS cluster_key
| where like(cluster_key,"%prod%")
| sort - inv_ts

Tune join keys if Inventory.dest stores FQDN while Kubernetes node names are short; maintain a translation lookup if needed.

### Step 4 — Validate

Positive scenario A: on a lab worker with safe maintenance windows, temporarily rename kubelet-client-current.pem aside and restart kubelet to force renewal stress while collectors run; expect audit CSR create events, kubelet logs mentioning rotation, and Splunk rows that move through medium into high tiers if approval is slow. Restore the file and approve any pending CSR to return to steady state.

Positive scenario B: create a synthetic CSR using kubeadm or openssl in lab, deny approval intentionally, and confirm ksm_csr_pending_max stays positive with severity medium_csr_signing_backlog until you approve.

Negative scenario: on a node with expect_auto_rotation=0 in kubelet_node_posture.csv, confirm the search filters info_manual_rotation_cluster rows and does not page.

Negative scenario two: cordon-only maintenance without kubelet restart should not emit rotation_fault signals; verify the alert stays quiet.

Validation SPL for lookup completeness:

```text
| inputlookup kubelet_node_posture.csv
| eval cluster=lower(trim(toString(cluster)))
| eval node=lower(trim(toString(node)))
| stats dc(node) AS nodes_in_lookup BY cluster
| join type=left max=0 cluster [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h latest=now kube_node_info | eval cluster=lower(cluster) | stats dc(node) AS nodes_in_metrics BY cluster]
| where nodes_in_metrics>nodes_in_lookup+5
```

Rows indicate posture gaps before production enforcement.

Clock skew test: skew a lab VM forward ten minutes and confirm days_to_expiry moves consistently across metrics from that host, signaling NTP remediation rather than silent pipeline failure.

RBAC test: readers without k8s_audit should see zero CSR audit rows, proving index segregation.

### Step 5 — Operationalize & Troubleshoot

Case 1 — CSR submitted but never approved: verify kube-controller-manager CSRApproving controllers, check for disabled auto-approval in hardened clusters, confirm no ValidatingAdmissionPolicy blocks approval, and inspect RBAC for csr-approver roles.

Case 2 — Approved but unsigned: examine controller-manager logs for signer errors, CA expiry, or permission denied on signer private keys; external signers need health checks on cert-manager CertificateRequest flows or cloud PCA connectors.

Case 3 — Signed but kubelet cannot write disk: check /var/lib/kubelet/pki permissions, SELinux or AppArmor denials, disk full, and inode exhaustion; correlate with kubelet PLEG warnings.

Case 4 — Certificate inside seven days without pending CSR and without rotation logs: validate rotateCertificates true, confirm bootstrap kubeconfig still valid, and ensure kubelet can reach apiserver to issue new CSR.

Case 5 — serverTLSBootstrap disabled: expect absent serving renewal; document in kubelet_node_posture.csv and rely on sibling PKI inventory for manual server cert issuance.

Case 6 — External signer backlog: Vault PKI, AWS Private CA, or enterprise CMP endpoints may add hours of latency; widen thresholds using lookup notes rather than muting entirely.

Case 7 — GKE Autopilot style estates: node filesystem access may block node_exporter ssl paths; lean on audit and CSR metrics while teaching responders to use cloud console rotation evidence.

Case 8 — EKS worker nodes: confirm Amazon Linux or Bottlerocket paths for kubelet config; some agents emit rotation via journald only—ensure filelog covers journal and not only container logs.

Case 9 — AKS: correlate with AKS certificate rotation documentation timelines; provider maintenance can overlap with CSR spikes—check Azure health before paging kubelet teams.

Case 10 — Lab clusters with one-day TLS for rotation drills: mark expect_auto_rotation or use suppress windows to avoid nightly pages while still training the pipeline quarterly.

Case 11 — Disk pressure eviction: kubelet may throttle writes; pair this UC with node pressure metrics before blaming signer availability.

Case 12 — Post-incident evidence: export the closing table, attach kubectl get csr snapshots, openssl x509 issuer and subject for current PEM files, and controller-manager excerpts showing approved by messages for auditors reviewing crypto hygiene.

Closing checklist: five em-dash step headers present, Step 3 fence mirrors spl JSON, streamstats and multisearch participate, inputlookup and tstats enrich rows, case() governs severity, final table includes fourteen analyst-facing columns, references include Kubernetes rotation and cloud kubelet guides, cimModels lists Inventory and Change for posture and renewal evidence, monitoringType lists Reliability and Availability, and exclusions distinguish UC-3.2.13 and UC-3.2.3.

## SPL

```spl
`comment("UC-3.2.42 Kubelet CSR renewal pipeline — apiserver audit for CSR objects, kube-state-metrics kube_certificatesigningrequest_condition, kubelet rotation logs, node_exporter ssl cert under /var/lib/kubelet/pki. earliest=-24h@h latest=now")`
| multisearch 
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,cluster,objectRef_cluster,""))))
      | eval res_lc=lower(trim(toString(coalesce('objectRef.resource',objectRef.resource,objectRef_resource,""))))
      | eval csr_name=trim(toString(coalesce('objectRef.name',objectRef.name,objectRef_name,"")))
      | eval verb_l=lower(trim(toString(coalesce(verb,""))))
      | where res_lc="certificatesigningrequests" AND len(cluster)>0 AND len(csr_name)>0
      | eval node_hint=lower(trim(toString(coalesce('requestObject.spec.username',requestObject_spec_username,""))))
      | rex field=node_hint "^system:node:(?<node_from_sa>.+)$"
      | eval node=lower(trim(coalesce(node_from_sa,csr_name)))
      | eval lane="audit_csr_activity"
      | fields _time cluster node lane csr_name verb_l ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,cluster,eks_cluster_name,gke_cluster_name,aks_cluster_name,""))))
      | eval mn=lower(trim(toString(coalesce(__name__,metric_name,name,""))))
      | where like(mn,"kube_certificatesigningrequest_condition") AND len(cluster)>0
      | rex field=_raw "condition=\"(?<csr_cond>[^\"]+)\""
      | rex field=_raw "status=\"(?<csr_stat>[^\"]+)\""
      | rex field=_raw "certificatesigningrequest=\"(?<csr_nm>[^\"]+)\""
      | eval node=lower(trim(toString(csr_nm)))
      | eval lane="ksm_csr_condition"
      | eval ksm_csr_pending=if(lower(csr_cond)=="approved" AND csr_stat=="false",1,0)
      | fields _time cluster node lane ksm_csr_pending csr_cond csr_stat ]
    [ search index=k8s_logs (sourcetype="kube:kubelet" OR sourcetype="kube:container:kubelet" OR source="kubelet") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,cluster,""))))
      | eval node=lower(trim(toString(coalesce(host,hostname,k8s_node_name,kubernetes_io_hostname,nodename,""))))
      | eval lr=lower(_raw)
      | where match(lr,"rotating kubelet client certificate") OR match(lr,"rotating kubelet server certificate") OR match(lr,"failed to rotate certificate") OR match(lr,"x509: certificate has expired or is not yet valid")
      | eval lane="kubelet_rotation_log"
      | eval log_fault=if(match(lr,"failed|error|expired|not yet valid"),1,0)
      | fields _time cluster node lane log_fault ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,cluster,eks_cluster_name,gke_cluster_name,aks_cluster_name,""))))
      | eval mn=lower(trim(toString(coalesce(__name__,metric_name,name,""))))
      | where (like(mn,"ssl_cert_not_after") OR mn=="ssl_certificate_expiry_seconds" OR like(mn,"ssl_cert")) AND match(lower(_raw),"kubelet/pki")
      | rex field=_raw "instance=\"(?<inst>[^\"]+)\""
      | eval node=lower(trim(replace(inst,"^https?://([a-z0-9._-]+)(?::[0-9]+)?.*$","\1")))
      | eval mv=tonumber(tostring(coalesce(value,metric_value,"")),10)
      | eval lane="nodeexp_kubelet_pki_ssl"
      | fields _time cluster node lane mv ]
| eval node=lower(trim(toString(coalesce(node,""))))
| where len(cluster)>0 AND len(node)>0
| bucket _time span=4h
| stats
    earliest(_time) AS first_signal_ts
    latest(_time) AS last_signal_ts
    max(eval(if(lane=="audit_csr_activity",1,0))) AS saw_csr_audit
    max(eval(if(lane=="ksm_csr_condition",ksm_csr_pending,0))) AS ksm_csr_pending_max
    max(eval(if(lane=="kubelet_rotation_log",log_fault,0))) AS kubelet_rotation_fault
    max(eval(if(lane=="kubelet_rotation_log",1,0))) AS kubelet_rotation_any
    max(eval(if(lane=="nodeexp_kubelet_pki_ssl",mv,null()))) AS ssl_not_after_epoch
    values(lane) AS lanes_seen
  BY cluster node _time
| eval days_to_expiry=if(isnotnull(ssl_not_after_epoch) AND ssl_not_after_epoch>1000000000, round((ssl_not_after_epoch-now())/86400,2), null())
| eval csr_pipeline_stuck=if(ksm_csr_pending_max>0 OR (saw_csr_audit>0 AND kubelet_rotation_fault>0),1,0)
| eval renewal_gap_risk=if(isnotnull(days_to_expiry) AND days_to_expiry<=7 AND kubelet_rotation_any=0 AND ksm_csr_pending_max=0 AND saw_csr_audit=0,1,0)
| sort 0 + cluster + node + _time
| streamstats window=3 current=t global=f max(renewal_gap_risk) AS renewal_gap_run BY cluster node
| stats
    max(renewal_gap_run) AS renewal_gap_run_max
    max(renewal_gap_risk) AS renewal_gap_risk_max
    max(csr_pipeline_stuck) AS csr_pipeline_stuck_max
    max(kubelet_rotation_fault) AS kubelet_rotation_fault_max
    max(saw_csr_audit) AS saw_csr_audit_max
    max(ksm_csr_pending_max) AS ksm_csr_pending_max
    max(kubelet_rotation_any) AS kubelet_rotation_any_max
    latest(ssl_not_after_epoch) AS ssl_not_after_epoch
    latest(days_to_expiry) AS days_to_expiry
    latest(lanes_seen) AS lanes_seen
    latest(last_signal_ts) AS last_signal_ts
    earliest(first_signal_ts) AS first_signal_ts
  BY cluster node
| eval csr_pipeline_stuck=csr_pipeline_stuck_max
| eval renewal_gap_risk=if(renewal_gap_run_max>0 OR renewal_gap_risk_max>0,1,0)
| eval kubelet_rotation_fault=kubelet_rotation_fault_max
| eval saw_csr_audit=saw_csr_audit_max
| eval ksm_csr_pending_max=ksm_csr_pending_max
| eval kubelet_rotation_any=kubelet_rotation_any_max
| join type=left max=0 cluster, node [
    | inputlookup kubelet_node_posture.csv
    | eval cluster=lower(trim(toString(cluster)))
    | eval node=lower(trim(toString(node)))
    | eval expect_auto_rotation=tonumber(tostring(coalesce(expect_auto_rotation,"1")),10)
    | eval node_pool=toString(coalesce(node_pool,pool,"unknown_pool"))
    | eval owner_team=toString(coalesce(owner_team,squad,"platform_core"))
    | eval signer_profile=toString(coalesce(signer_profile,signer,"kubernetes.io/kubelet-serving"))
    | fields cluster node expect_auto_rotation node_pool owner_team signer_profile ]
| fillnull value=1 expect_auto_rotation
| fillnull value="unknown_pool" node_pool
| fillnull value="platform_core" owner_team
| fillnull value="kubernetes.io/kubelet-serving" signer_profile
| join type=left max=1 cluster [
    | tstats summariesonly=t latest(_time) AS inventory_fresh_ts FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
    | rename Inventory.dest AS cluster ]
| eval severity=case(
    expect_auto_rotation=0, "info_manual_rotation_cluster",
    kubelet_rotation_fault=1, "critical_kubelet_rotation_failure",
    renewal_gap_risk=1 AND coalesce(days_to_expiry,999)<=3, "critical_expiring_no_renewal_signal",
    renewal_gap_risk=1, "high_expiring_no_renewal_signal",
    csr_pipeline_stuck=1 AND coalesce(days_to_expiry,999)<=14, "high_csr_stuck_near_expiry",
    csr_pipeline_stuck=1, "medium_csr_signing_backlog",
    coalesce(days_to_expiry,999)<=7, "high_disk_cert_horizon",
    coalesce(days_to_expiry,999)<=14, "medium_disk_cert_horizon",
    true(), "low_ok")
| where expect_auto_rotation=1 AND NOT severity IN ("low_ok","info_manual_rotation_cluster")
| eventstats dc(node) AS impacted_nodes BY cluster
| eval action=case(
    severity=="critical_kubelet_rotation_failure", "inspect_kubelet_logs_and_pki_disk",
    severity=="critical_expiring_no_renewal_signal", "emergency_csr_signer_kubelet_bootstrap_review",
    severity=="high_expiring_no_renewal_signal", "validate_rotateCertificates_serverTLSBootstrap",
    severity=="high_csr_stuck_near_expiry", "unblock_csr_approval_and_signer",
    severity=="medium_csr_signing_backlog", "kubectl_get_csr_and_controller_manager_logs",
    severity=="high_disk_cert_horizon", "openssl_x509_and_disk_space_on_node",
    true(), "triage_pipeline")
| table cluster node node_pool owner_team severity days_to_expiry csr_pipeline_stuck renewal_gap_risk kubelet_rotation_fault saw_csr_audit ksm_csr_pending_max impacted_nodes last_signal_ts inventory_fresh_ts signer_profile action
```

## CIM SPL

```spl
| tstats summariesonly=t latest(_time) AS inv_latest FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
| rename Inventory.dest AS cluster_inventory_key
| join type=left max=0 cluster_inventory_key [| tstats summariesonly=t count FROM datamodel=Change WHERE nodename=Change All_Changes.status=success earliest=-24h@h latest=now BY Change.object_category]
| where len(cluster_inventory_key)>0
| sort - inv_latest
```

## Visualization

Severity-colored table mirroring the closing projection; timeline of renewal_gap_risk by node; single value of impacted_nodes per cluster; drilldowns from csr_pipeline_stuck rows to raw audit CSR events and kubelet logs.

## Known False Positives

Clusters that mandate manual CSR review introduce hours of deliberate latency while security tickets accumulate; treat Approved=false as expected until SLA breach, using kubelet_node_posture.csv notes to lengthen suppression windows rather than disabling the control. Freshly bootstrapped nodes may sit pending first signature overnight during change freezes; require sustained backlog or combine with days_to_expiry before paging. Amazon EKS, Google GKE, and Microsoft AKS managed node pools sometimes obscure host-level PEM inspection while provider automation still rotates; rows with only API signals should downgrade when lookup marks managed_signer and host openssl is unavailable by design. Bare-metal estates using cert-manager, AWS Private CA, HashiCorp Vault PKI, or CMP gateways can see multi-hour signing windows that look like stuck CSRs during CA maintenance; correlate external signer health before blaming kubelet. Lab clusters that intentionally set one-day certificate lifetimes for rotation drills will page frequently unless you set expect_auto_rotation=0 or maintenance suppress metadata for those clusters. Kubelet behavior under disk-pressure eviction can fail writes to /var/lib/kubelet/pki even when apiserver and signer are healthy; pair alerts with node pressure metrics and inode charts before escalating to PKI teams. Short-lived spot interruptions may kill nodes before renewal completes; distinguish provider churn from pipeline defects using cloud termination metadata. Audit sampling or Metadata-only policies may omit CSR correlates; never silence the UC solely because audit is thin—investigate collector policy instead.

## References

- [Kubernetes — Certificate Rotation](https://kubernetes.io/docs/tasks/administer-cluster/certificate-rotation/)
- [Kubernetes — kubelet TLS bootstrapping](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/)
- [Kubernetes — Certificate Signing Requests](https://kubernetes.io/docs/reference/access-authn-authz/certificate-signing-requests/)
- [Kubernetes — kube-controller-manager](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager/)
- [Kubernetes — kubeadm certificate management](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)
- [Amazon EKS — Worker node kubelet certificate rotation](https://docs.aws.amazon.com/eks/latest/userguide/kubelet-certificate-rotation.html)
- [Google GKE — Credential rotation overview](https://cloud.google.com/kubernetes-engine/docs/how-to/credential-rotation)
- [Microsoft AKS — Certificate rotation](https://learn.microsoft.com/en-us/azure/aks/certificate-rotation)
