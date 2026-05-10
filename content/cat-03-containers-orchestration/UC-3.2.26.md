<!-- AUTO-GENERATED from UC-3.2.26.json — DO NOT EDIT -->

---
id: "3.2.26"
title: "Kubernetes etcd Quorum Health, Raft Member Risk, and Cluster-Membership Drift (Operational-Quorum Axis)"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.26 · Kubernetes etcd Quorum Health, Raft Member Risk, and Cluster-Membership Drift (Operational-Quorum Axis)

> **Criticality:** Critical &middot; **Difficulty:** Expert &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*We watch the small voter group that keeps the control plane's shared records in agreement. If that group is one loss away from deadlock, if a trainee member never graduates, or if leaders keep re-electing, we warn you before everything that depends on that memory freezes.*

---

## Description

Monitors the operational quorum axis for Kubernetes etcd: voting member coverage scraped from metrics, Raft leader visibility via etcd_server_has_leader, leader election churn from etcd_server_leader_changes_seen_total, peer path latency via etcd_network_peer_round_trip_time_seconds_bucket as a partition and placement signal, proposal backlog pressure from etcd_server_proposals_pending versus etcd_server_proposals_committed_total with etcd_server_proposals_failed_total deltas, member health counters from etcd_server_health_failures, learner posture from etcd_server_is_learner, asymmetric peer-only comparison of etcd_disk_backend_commit_duration_seconds_bucket quantiles (skew versus cluster peers, not UC-3.2.8 histogram performance depth), and etcd_mvcc_db_total_size_in_bytes as a capacity-side correlate for alarm conditions such as NOSPACE. The control surfaces when the cluster is one failure away from losing quorum, when membership implied by scrapes disagrees with governance expectations, and when sustained proposal backlog or repeated health failures precede apiserver-wide write outages.

## Value

Platform and reliability leaders shorten incidents that would otherwise masquerade as generic apiserver slowness: quorum risk, learner transitions, and member drift have distinct remediation paths from scheduler saturation or kubelet noise. Finance and audit stakeholders gain evidence that etcd membership and Raft stability are continuously measured alongside the broader control-plane story in UC-3.2.7, without duplicating UC-3.2.8 deep disk and WAL histogram forensics or UC-3.2.19 apiserver request latency analytics. Self-managed fleets retain defensible runbooks for partition, misconfigured peer URLs, asymmetric backup pauses, and defragmentation hygiene; managed-cloud teams document compensating provider metrics when member scrapes are impossible.

## Implementation

Provision k8s_metrics with per-member etcd scrapes preserving cluster and instance labels; publish cluster_platform_routing.csv; save uc_3_2_26_etcd_quorum_operational every five minutes with earliest=-30m@m latest=@m; join optional endpoint status JSON for drift audits; route severity down or critical to platform etcd on-call; pair with UC-3.2.7 for multi-pillar context and UC-3.2.8 only when histogram performance investigation is explicitly required.

## Evidence

Saved search uc_3_2_26_etcd_quorum_operational on a five-minute schedule; cluster_platform_routing.csv with optional expected_etcd_voting_members; weekly CSV export of the closing table to a restricted evidence index; optional dashboard comparing voting_members to etcdctl endpoint status ingest.

## Control test

### Positive scenario

In a lab quorum cluster with k8s_metrics populated from three etcd members, block outbound 2380 between two followers for ten minutes while scrapes continue; expect uc_3_2_26_etcd_quorum_operational to emit critical or high severity with peer_rtt_p95_ms or quorum_margin at or below one on at least one window, and cluster_min_has_leader or member_unhealthy flags consistent with the partition narrative.

### Negative scenario

Steady-state production with three healthy voting members, leader_changes_5m at zero across thirty minutes, suppress_single_node_dev respected for dev clusters, and no membership_drift when expected_etcd_voting_members matches voting_members; severity remains healthy or medium at worst during single-bucket jitter under two hundred milliseconds RTT without sustained breach.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the Kubernetes platform engineering team and the etcd operations group that curates member lifecycle, backup cadence, and defragmentation policy. This use case isolates one monitoring axis only: etcd cluster membership and Raft quorum operational health as seen through Prometheus-style metrics scraped from each voting member and optional etcdctl endpoint status JSON for ground truth on member lists, revisions, and errors. UC-3.2.7 remains the four-pillar control-plane verdict across apiserver, etcd summary, scheduler, and controller-manager; it does not replace per-member quorum math, learner promotion lag, or scrape-derived membership drift checks. UC-3.2.8 remains the deep etcd performance plane for WAL fsync, snapshot duration, MVCC compaction histograms, and quota pressure interpreted as performance engineering work; this UC may reference etcd_disk_backend_commit_duration_seconds_bucket only as a peer skew ratio against the cluster median in the same time bucket, never as the primary performance SLO. UC-3.2.19 remains apiserver-side request latency and throttling analytics. When this alert fires, pause destructive automation that removes etcd members, resizes control-plane networks, or runs full-cluster defragmentation without sequencing until quorum margin is restored.

Index and token contracts: designate index=k8s_metrics for prometheus:scrape:metrics lines (or your OTel-normalized equivalent) with fields __name__, value, le, instance, pod, job, and k8s_cluster_name or cloud-specific cluster tags. Provision index=k8s_logs for optional sourcetype=kube:etcd:endpoint_status JSON emitted by a CronJob that runs etcdctl endpoint status -w json inside the kube-system etcd pod or from a bastion with the same trust material. Issue dedicated HEC tokens per index class with least privilege roles. Retention: keep at least fourteen days of hot metrics so post-incident replay can rebuild five-minute windows across leader transitions and member replacements.

Scrape topology for self-managed Kubernetes: each etcd member must be scraped individually. Static pod kubeadm clusters expose metrics on 2379 or a dedicated metrics port such as 2381; Prometheus Operator users install a PodMonitor with mTLS client certificates mounted from the same PKI trust chain the apiserver uses. Scraping only the Kubernetes Service VIP hides follower health and breaks quorum margin math. OpenTelemetry Collector prometheus receiver jobs should list each member endpoint explicitly when service discovery collapses followers.

Governance lookup: maintain cluster_platform_routing.csv with cluster, cloud, on_call_team, suppress_single_node_dev, and optional expected_etcd_voting_members. The optional expected count supports drift detection when automation or documentation says three voting members but scrapes only see two active instance labels after a failed add. Dev clusters on Kind, Minikube, or K3d should set suppress_single_node_dev=1 so HA-only thresholds never page overnight.

Managed Kubernetes caveat: Amazon EKS, Google GKE, and Microsoft AKS generally hide etcd from the customer VPC. Expect empty or provider-normalized series. When no etcd __name__ fields arrive for a production cluster classification for more than twenty-four hours, document the gap and rely on UC-3.2.7 plus cloud consoles rather than fabricating Raft alerts from unrelated scrapes.

Risk briefing: Raft tolerates f failures for odd cluster sizes N=2f+1. The saved search estimates voting_members as distinct etcd_member labels with etcd_server_is_learner not equal to one. Learners do not count toward quorum until promoted; prolonged learner posture with promotion stalled is a distinct failure mode called out in severity ladders. etcd alarms such as NOSPACE and CORRUPT surface in logs and metrics; etcd_mvcc_db_total_size_in_bytes is used here only as a coarse capacity correlate for planning defragmentation and quota conversations, not as a substitute for UC-3.2.8 quota histogram analysis.

Training: platform on-call should rehearse etcdctl member list, etcdctl endpoint status, and etcdctl move-leader against lab clusters so Splunk rows map to CLI truth. Network engineers should understand that etcd_network_peer_round_trip_time_seconds_bucket quantiles flag symmetric or asymmetric latency between peers, often an early partition hint before apiserver error rates move.

### Step 2 — Configure data collection

PodMonitor for static etcd pods (adjust namespace, port name, and TLS for your distribution):

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: etcd-quorum-per-member
  namespace: monitoring
spec:
  podMetricsEndpoints:
    - port: metrics
      scheme: https
      tlsConfig:
        caFile: /etc/prometheus/secrets/etcd-client-ca.crt
        certFile: /etc/prometheus/secrets/etcd-client.crt
        keyFile: /etc/prometheus/secrets/etcd-client.key
  namespaceSelector:
    matchNames:
      - kube-system
  selector:
    matchLabels:
      component: etcd
```

OpenTelemetry Collector fragment with one scrape job per member role discovery:

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: etcd-members-quorum
          scheme: https
          tls_config:
            ca_file: /otel/certs/etcd-ca.pem
            cert_file: /otel/certs/etcd-client.pem
            key_file: /otel/certs/etcd-client-key.pem
          kubernetes_sd_configs:
            - role: pod
          relabel_configs:
            - source_labels: [__meta_kubernetes_pod_label_component]
              regex: etcd
              action: keep
            - source_labels: [__meta_kubernetes_pod_ip]
              target_label: __address__
              replacement: ${1}:2379
exporters:
  splunk_hec:
    token: "${SPLUNK_HEC_TOKEN_K8S_METRICS}"
    endpoint: "https://splunk-hec.example:8088/services/collector/event"
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
service:
  pipelines:
    metrics:
      receivers: [prometheus]
      exporters: [splunk_hec]
```

Optional CronJob that pushes etcdctl endpoint status JSON for membership drift audits:

```bash
#!/usr/bin/env bash
set -euo pipefail
NS="${ETCD_NAMESPACE:-kube-system}"
POD="$(kubectl -n "$NS" get pods -l component=etcd -o jsonpath='{.items[0].metadata.name}')"
JSON="$(kubectl -n "$NS" exec "$POD" -- etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/healthcheck-client.crt \
  --key=/etc/kubernetes/pki/etcd/healthcheck-client.key endpoint status -w json)"
PAYLOAD=$(jq -n --argjson ev "$JSON" '{sourcetype:"kube:etcd:endpoint_status", index:"k8s_logs", event:$ev}')
curl -sS -k "https://splunk-hec.example:8088/services/collector/event" \
  -H "Authorization: Splunk ${SPLUNK_HEC_TOKEN_LOGS}" \
  -d "$PAYLOAD"
```

Extend cluster_platform_routing.csv with optional expected_etcd_voting_members when your CMDB knows the declared quorum size. After any add or remove, update the lookup in git within the same change ticket.

Normalize props so cluster, container_name, and pod labels extract consistently; verify kube-system etcd pod names appear in instance or pod fields before enabling alerts.

### Step 3 — Create the search and alert

Understanding the pipeline: multisearch runs two parallel metric reductions. The first arm ingests non-histogram etcd series and rolls five-minute maxima per cluster, etcd_member, and win_time for etcd_server_has_leader, etcd_server_is_learner, etcd_server_health_failures, etcd_server_leader_changes_seen_total, etcd_server_proposals_pending, etcd_server_proposals_committed_total, etcd_server_proposals_failed_total, and etcd_mvcc_db_total_size_in_bytes. The second arm rebuilds approximate ninety-fifth percentile peer round-trip time from etcd_network_peer_round_trip_time_seconds_bucket and ninety-fifth percentile backend commit latency from etcd_disk_backend_commit_duration_seconds_bucket using cumulative bucket counts, solely to compare each member against the cluster median commit quantile in the same window (commit_peer_skew_ratio). This ratio flags asymmetric slow disks or stalled peers; it is not the UC-3.2.8 performance deep dive. After multisearch, stats collapses duplicate keys, streamstats derives leader and proposal deltas per member, eventstats counts voting_members and healthy_voting to compute quorum_margin against floor(N/2)+1, and a second eventstats derives cluster_median_commit_p95 for skew. Joins attach Application_State and Performance tstats touch counts per window for CIM evidence, and inputlookup cluster_platform_routing.csv adds on_call_team, suppress_single_node_dev, and expected_etcd_voting_members. case() maps operational_state and severity tiers. The closing table lists cluster, etcd_member, win_time, voting_members, healthy_voting, quorum_margin, leader_changes_5m, peer_rtt_p95_ms, commit_peer_skew_ratio, proposal_backlog_ratio, prop_failed_5m, mvcc_db_gb, is_learner, operational_state, severity, on_call_team, app_state_touch, avg_host_load, and membership_drift.

Paste-and-run SPL (must match the spl JSON field exactly):

```spl
`comment("UC-3.2.26 etcd quorum and Raft membership operational health. multisearch merges gauge/counter arms with histogram arms; streamstats for leader and proposal deltas; eventstats for quorum margin; commit histogram used only for peer skew ratio versus cluster median (not UC-3.2.8 perf depth). Tunables: earliest=-30m@m latest=@m; span=5m; skew_warn=2.0; rtt_warn_ms=800; mvcc_warn_gb=7.")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval etcd_member=trim(toString(coalesce(instance, kubernetes_io_pod_name, pod, k8s_pod_name, "")))
      | eval etcd_member=if(len(etcd_member)==0 OR etcd_member="null", trim(toString(coalesce(job, scrape_job, kubernetes_job, ""))), etcd_member)
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | where len(cluster)>0 AND match(mn, "^etcd_") AND NOT match(mn, "_bucket$")
      | bucket _time span=5m
      | eval win_time=_time
      | stats max(eval(if(mn=="etcd_server_has_leader", mv, null()))) AS has_leader_snap max(eval(if(mn=="etcd_server_is_learner", mv, null()))) AS is_learner max(eval(if(mn=="etcd_server_health_failures", mv, null()))) AS health_fail_hi max(eval(if(mn=="etcd_server_leader_changes_seen_total", mv, null()))) AS leader_chg_hi max(eval(if(mn=="etcd_server_proposals_pending", mv, null()))) AS prop_pend max(eval(if(mn=="etcd_server_proposals_committed_total", mv, null()))) AS prop_commit_hi max(eval(if(mn=="etcd_server_proposals_failed_total", mv, null()))) AS prop_fail_hi max(eval(if(mn=="etcd_mvcc_db_total_size_in_bytes", mv, null()))) AS mvcc_db_total BY cluster etcd_member win_time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval etcd_member=trim(toString(coalesce(instance, kubernetes_io_pod_name, pod, k8s_pod_name, "")))
      | eval etcd_member=if(len(etcd_member)==0 OR etcd_member="null", trim(toString(coalesce(job, scrape_job, kubernetes_job, ""))), etcd_member)
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval le_raw=trim(toString(coalesce(le, le_label, "")))
      | where len(cluster)>0 AND (mn=="etcd_network_peer_round_trip_time_seconds_bucket" OR mn=="etcd_disk_backend_commit_duration_seconds_bucket")
      | bucket _time span=5m
      | eval win_time=_time
      | eval fam=if(mn=="etcd_network_peer_round_trip_time_seconds_bucket", "peer_rtt", "be_commit")
      | stats max(mv) AS cum_at_window BY cluster etcd_member win_time fam le_raw
      | eval le_num=case(match(le_raw,"^\\+Inf$"), 1000000000, true(), tonumber(le_raw))
      | where isnotnull(le_num)
      | sort 0 cluster etcd_member fam win_time le_num
      | eventstats max(eval(if(match(le_raw,"^\\+Inf$"), cum_at_window, null()))) AS histo_total BY cluster etcd_member fam win_time
      | where isnotnull(histo_total) AND histo_total>0 AND cum_at_window>=(0.95*histo_total)
      | stats min(le_num) AS q95_le BY cluster etcd_member fam win_time
      | eval q95_ms=round(q95_le*1000, 3)
      | eval peer_rtt_p95_ms=if(fam=="peer_rtt", q95_ms, null())
      | eval backend_commit_p95_ms_peer=if(fam=="be_commit", q95_ms, null())
      | stats max(peer_rtt_p95_ms) AS peer_rtt_p95_ms max(backend_commit_p95_ms_peer) AS backend_commit_p95_ms_peer BY cluster etcd_member win_time ]
| stats max(has_leader_snap) AS has_leader_snap max(is_learner) AS is_learner max(health_fail_hi) AS health_fail_hi max(leader_chg_hi) AS leader_chg_hi max(prop_pend) AS prop_pend max(prop_commit_hi) AS prop_commit_hi max(prop_fail_hi) AS prop_fail_hi max(mvcc_db_total) AS mvcc_db_total max(peer_rtt_p95_ms) AS peer_rtt_p95_ms max(backend_commit_p95_ms_peer) AS backend_commit_p95_ms_peer BY cluster etcd_member win_time
| sort 0 cluster etcd_member win_time
| streamstats window=2 current=t global=f first(leader_chg_hi) AS prev_lc last(leader_chg_hi) AS cur_lc first(prop_fail_hi) AS prev_pf last(prop_fail_hi) AS cur_pf first(prop_commit_hi) AS prev_pc last(prop_commit_hi) AS cur_pc first(health_fail_hi) AS prev_hf last(health_fail_hi) AS cur_hf BY cluster etcd_member
| eval leader_changes_5m=max(0, coalesce(cur_lc,0)-coalesce(prev_lc,0))
| eval prop_failed_5m=max(0, coalesce(cur_pf,0)-coalesce(prev_pf,0))
| eval prop_committed_5m=max(0, coalesce(cur_pc,0)-coalesce(prev_pc,0))
| eval health_fail_delta=max(0, coalesce(cur_hf,0)-coalesce(prev_hf,0))
| eval proposal_backlog_ratio=if(isnotnull(prop_pend), round(prop_pend/max(prop_committed_5m, 0.001), 3), null())
| eval mvcc_db_gb=round(coalesce(mvcc_db_total,0)/1073741824, 3)
| eval member_unhealthy=if(coalesce(is_learner,0)==1, 0, if(coalesce(has_leader_snap,1)==0 OR health_fail_delta>0 OR prop_failed_5m>3, 1, 0))
| eval voting_participant=if(coalesce(is_learner,0)==0, 1, 0)
| eventstats dc(eval(if(voting_participant==1, etcd_member, null()))) AS voting_members dc(eval(if(voting_participant==1 AND member_unhealthy==0, etcd_member, null()))) AS healthy_voting sum(eval(if(voting_participant==1 AND member_unhealthy==1, 1, 0))) AS unhealthy_voting_ct BY cluster win_time
| eval quorum_needed=if(voting_members>0, floor(voting_members/2)+1, 0)
| eval quorum_margin=healthy_voting-quorum_needed
| eventstats median(backend_commit_p95_ms_peer) AS cluster_median_commit_p95 BY cluster win_time
| eval commit_peer_skew_ratio=if(isnotnull(backend_commit_p95_ms_peer) AND coalesce(cluster_median_commit_p95,0)>0.0001, round(backend_commit_p95_ms_peer/cluster_median_commit_p95, 3), null())
| eventstats min(has_leader_snap) AS cluster_min_has_leader BY cluster win_time
| join type=left max=0 win_time [| tstats summariesonly=f count AS app_state_touch FROM datamodel=Application_State WHERE nodename=Application_State earliest=-30m@m latest=@m BY _time span=5m | rename _time AS win_time ]
| join type=left max=0 cluster [| inputlookup cluster_platform_routing.csv | eval cluster=lower(trim(toString(cluster))) | eval on_call_team=toString(coalesce(on_call_team, squad, platform_team, "platform_etcd")) | eval suppress_single_node_dev=tonumber(tostring(coalesce(suppress_single_node_dev, "0")), 10) | eval expected_etcd_voting_members=tonumber(tostring(coalesce(expected_etcd_voting_members, "")), 10) | fields cluster on_call_team suppress_single_node_dev expected_etcd_voting_members ]
| fillnull value="platform_etcd" on_call_team
| eval membership_drift=if(isnotnull(expected_etcd_voting_members) AND expected_etcd_voting_members>0 AND voting_members!=expected_etcd_voting_members, 1, 0)
| eval operational_state=case(cluster_min_has_leader==0, "no_leader_view", quorum_margin<0, "quorum_lost", quorum_margin==0, "quorum_barely_met", membership_drift==1, "membership_drift", leader_changes_5m>=4, "leader_thrash", coalesce(proposal_backlog_ratio,0)>=50 OR coalesce(prop_pend,0)>=5000, "proposal_backlog_hot", coalesce(peer_rtt_p95_ms,0)>=800, "peer_partition_risk", coalesce(commit_peer_skew_ratio,0)>=2, "commit_skew_peer", coalesce(mvcc_db_gb,0)>=7, "mvcc_capacity_signal", true(), "nominal")
| eval severity=case(cluster_min_has_leader==0 OR quorum_margin<0 OR operational_state=="quorum_lost", "down", quorum_margin<=1 OR operational_state=="leader_thrash" OR operational_state=="proposal_backlog_hot" OR membership_drift==1, "critical", operational_state=="peer_partition_risk" OR operational_state=="commit_skew_peer" OR unhealthy_voting_ct>=2, "high", operational_state=="mvcc_capacity_signal" OR leader_changes_5m>=2 OR prop_failed_5m>0 OR coalesce(peer_rtt_p95_ms,0)>=200, "medium", true(), "healthy")
| where coalesce(suppress_single_node_dev,0)==0 OR severity IN ("down","critical")
| join type=left max=0 win_time [| tstats summariesonly=f avg(Performance.cpu_load_percent) AS avg_host_load FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-30m@m latest=@m BY _time span=5m | rename _time AS win_time ]
| table cluster etcd_member win_time voting_members healthy_voting quorum_margin leader_changes_5m peer_rtt_p95_ms commit_peer_skew_ratio proposal_backlog_ratio prop_failed_5m mvcc_db_gb is_learner operational_state severity on_call_team app_state_touch avg_host_load membership_drift
```

Schedule uc_3_2_26_etcd_quorum_operational every five minutes with dispatch earliest=-30m@m and latest=now, suppress duplicates for five minutes, and alert when severity is down or critical. Wire actions to the platform etcd rotation documented in cluster_platform_routing.csv. For Splunk ITSI, map quorum_margin to a KPI with critical threshold at or below one for two consecutive samples.

### Step 4 — Validate

Synthetic partition: on a disposable three-member lab cluster, insert an iptables or cloud security-group rule that blocks etcd peer port 2380 between two followers while leaving metrics scrapes from the monitoring namespace intact. Within two five-minute windows, expect peer_rtt_p95_ms elevation or member_unhealthy counts to move quorum_margin toward zero. Remove the rule immediately after the test.

Synthetic leader move: run etcdctl move-leader to a named member ID during a rehearsed maintenance window. Expect a single leader_changes_5m increment, not sustained leader_thrash, when annotated.

Learner drill: add a learner per etcd runtime configuration guidance and observe etcd_server_is_learner equal to one on the new member while quorum_margin still computes from voting members only. Promote the learner and confirm is_learner returns to zero in metrics.

Lookup drift drill: set expected_etcd_voting_members to two in cluster_platform_routing.csv while three members scrape, confirm membership_drift flags one until the lookup is corrected.

Validation SPL for raw scrape presence:

```spl
index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-24h latest=@h
| eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
| where mn="etcd_server_has_leader" OR mn="etcd_server_leader_changes_seen_total"
| stats dc(mn) AS fam dc(instance) AS scrape_targets BY k8s_cluster_name
| where fam>=1
```

Zero rows for self-managed production clusters mean scrapes are misconfigured; fix targets before tuning thresholds.

Negative check: steady-state lab with suppress_single_node_dev=1 should yield filtered rows per the closing where clause; confirm dev noise does not page.

### Step 5 — Operationalize & Troubleshoot

Case 1 — quorum_margin at zero or negative with cluster_min_has_leader zero: treat as quorum loss or imminent loss; stop member removals, open etcd recovery runbooks, verify member list from etcdctl endpoint status, and prepare snapshot restore paths under change control.

Case 2 — leader_thrash with modest peer RTT: inspect clock skew, CPU steal, and buggy etcd patch levels; capture raft term progression and avoid rolling all members simultaneously.

Case 3 — peer_partition_risk with asymmetric AZ routing: validate security groups, MTU, and transient cloud backbone faults; map etcd_member to AZ labels from node exports before blaming application teams.

Case 4 — commit_skew_peer with one follower hot: compare disk class and fsync latency on the outlier only; escalate to storage owners; defer deep histogram analysis to UC-3.2.8 when sustained.

Case 5 — proposal_backlog_hot with elevated prop_pend: investigate apiserver write storms, large object writes, and slow followers; correlate with UC-3.2.7 apiserver pillar summaries before shrinking etcd quotas.

Case 6 — membership_drift versus etcdctl JSON: reconcile scrape targets with live member list; stale instance labels after IP changes point to discovery bugs; update expected_etcd_voting_members after approved topology changes.

Case 7 — learner promotion stuck: verify member add completed, certificates for peer URLs, and network reachability on 2380; use learner promotion documentation and avoid forcing promote without consensus health checks.

Case 8 — mvcc_capacity_signal with operator alarms: plan online defragmentation during maintenance windows, validate automated compaction, and cross-check etcd_server_quota_backend_bytes in UC-3.2.8 panels when available.

Case 9 — prop_failed_5m rising on one member: isolate misconfigured peer URLs or certificate mismatches; compare raw metrics labels across members for inconsistent advertise-client-urls.

Case 10 — healthy_voting equals two of three: you are one failure from quorum loss; page platform etcd and freeze risky changes even if apiserver still answers; document the single point of failure until a third healthy voter returns.

Case 11 — backup pause on one peer: when vendor backup freezes one member, annotate maintenance and expect transient skew; verify other members remain healthy and backlog clears after resume.

Case 12 — relationship to UC-3.2.7: when this UC fires, open the control-plane health dashboard for the same cluster to see whether apiserver, scheduler, or controller-manager pillars also degraded; use UC-3.2.7 for the aggregate verdict and this UC for etcd membership specifics.

Operational cadence: weekly review of voting_members versus CMDB, refresh mTLS scrape certificates before expiry, rehearse member add and remove with lookup updates in the same ticket, and archive CSV exports of the closing table for reliability retrospectives.

Closing checklist: five em-dash step headers are present; Step 3 includes a fenced SPL block matching the spl JSON field; Step 5 lists twelve Case entries; multisearch, streamstats, eventstats, coalesce, case severity tiering, inputlookup join, and dual tstats joins appear in the SPL; commit histogram math is peer skew only; final table includes eighteen columns; references span etcd monitoring, recovery, runtime configuration, Kubernetes etcd operations, metrics reference, kubeadm HA topology, learner design, and SIG Cluster Lifecycle; exclusions cite UC-3.2.7, UC-3.2.8, and UC-3.2.19; cimModels lists Application_State and Performance for CIM overlays documented in cimSpl.

Supplemental owner notes: tune mvcc_warn_gb and rtt_warn_ms to your storage and network baselines after thirty days of observation. When scrape_interval exceeds sixty seconds, widen buckets to fifteen minutes or require two consecutive breaches. When IPv6-only control planes land, validate bracketed scrape targets. When Linkerd or Istio accidentally intercepts scrapes, bypass the mesh for the prometheus service account. When FinOps challenges cardinality, summarize five-minute rollups to a summary index while retaining raw scrapes for seven days. When legal restricts metrics access, place k8s_metrics behind restricted roles and publish redacted executive summaries. When multi-cluster federation duplicates cluster labels, enforce k8s_cluster_name at the collector. When Grafana mirrors these panels, hyperlink from Splunk rows to Grafana for member-level views. When Arm64 histogram defaults differ, revalidate bucket boundaries after upgrades. When OT or edge Kubernetes appears, duplicate routing lookups with different on_call_team values. When auditors request availability evidence, attach weekly CSV exports plus change tickets for etcd upgrades. When training new SREs, replay saved fixtures from prior incidents in a sandbox index. When cloud provider maintenance overlaps signals, downgrade severity only with provider acknowledgement documented in the ticket. When etcd runs external to Kubernetes, point collectors at member DNS names and label rows with logical member IDs from etcdctl. When automated remediation removes members, gate playbooks behind human approval until quorum_margin is at least two.



## SPL

```spl
`comment("UC-3.2.26 etcd quorum and Raft membership operational health. multisearch merges gauge/counter arms with histogram arms; streamstats for leader and proposal deltas; eventstats for quorum margin; commit histogram used only for peer skew ratio versus cluster median (not UC-3.2.8 perf depth). Tunables: earliest=-30m@m latest=@m; span=5m; skew_warn=2.0; rtt_warn_ms=800; mvcc_warn_gb=7.")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval etcd_member=trim(toString(coalesce(instance, kubernetes_io_pod_name, pod, k8s_pod_name, "")))
      | eval etcd_member=if(len(etcd_member)==0 OR etcd_member="null", trim(toString(coalesce(job, scrape_job, kubernetes_job, ""))), etcd_member)
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | where len(cluster)>0 AND match(mn, "^etcd_") AND NOT match(mn, "_bucket$")
      | bucket _time span=5m
      | eval win_time=_time
      | stats max(eval(if(mn=="etcd_server_has_leader", mv, null()))) AS has_leader_snap max(eval(if(mn=="etcd_server_is_learner", mv, null()))) AS is_learner max(eval(if(mn=="etcd_server_health_failures", mv, null()))) AS health_fail_hi max(eval(if(mn=="etcd_server_leader_changes_seen_total", mv, null()))) AS leader_chg_hi max(eval(if(mn=="etcd_server_proposals_pending", mv, null()))) AS prop_pend max(eval(if(mn=="etcd_server_proposals_committed_total", mv, null()))) AS prop_commit_hi max(eval(if(mn=="etcd_server_proposals_failed_total", mv, null()))) AS prop_fail_hi max(eval(if(mn=="etcd_mvcc_db_total_size_in_bytes", mv, null()))) AS mvcc_db_total BY cluster etcd_member win_time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval etcd_member=trim(toString(coalesce(instance, kubernetes_io_pod_name, pod, k8s_pod_name, "")))
      | eval etcd_member=if(len(etcd_member)==0 OR etcd_member="null", trim(toString(coalesce(job, scrape_job, kubernetes_job, ""))), etcd_member)
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval le_raw=trim(toString(coalesce(le, le_label, "")))
      | where len(cluster)>0 AND (mn=="etcd_network_peer_round_trip_time_seconds_bucket" OR mn=="etcd_disk_backend_commit_duration_seconds_bucket")
      | bucket _time span=5m
      | eval win_time=_time
      | eval fam=if(mn=="etcd_network_peer_round_trip_time_seconds_bucket", "peer_rtt", "be_commit")
      | stats max(mv) AS cum_at_window BY cluster etcd_member win_time fam le_raw
      | eval le_num=case(match(le_raw,"^\\+Inf$"), 1000000000, true(), tonumber(le_raw))
      | where isnotnull(le_num)
      | sort 0 cluster etcd_member fam win_time le_num
      | eventstats max(eval(if(match(le_raw,"^\\+Inf$"), cum_at_window, null()))) AS histo_total BY cluster etcd_member fam win_time
      | where isnotnull(histo_total) AND histo_total>0 AND cum_at_window>=(0.95*histo_total)
      | stats min(le_num) AS q95_le BY cluster etcd_member fam win_time
      | eval q95_ms=round(q95_le*1000, 3)
      | eval peer_rtt_p95_ms=if(fam=="peer_rtt", q95_ms, null())
      | eval backend_commit_p95_ms_peer=if(fam=="be_commit", q95_ms, null())
      | stats max(peer_rtt_p95_ms) AS peer_rtt_p95_ms max(backend_commit_p95_ms_peer) AS backend_commit_p95_ms_peer BY cluster etcd_member win_time ]
| stats max(has_leader_snap) AS has_leader_snap max(is_learner) AS is_learner max(health_fail_hi) AS health_fail_hi max(leader_chg_hi) AS leader_chg_hi max(prop_pend) AS prop_pend max(prop_commit_hi) AS prop_commit_hi max(prop_fail_hi) AS prop_fail_hi max(mvcc_db_total) AS mvcc_db_total max(peer_rtt_p95_ms) AS peer_rtt_p95_ms max(backend_commit_p95_ms_peer) AS backend_commit_p95_ms_peer BY cluster etcd_member win_time
| sort 0 cluster etcd_member win_time
| streamstats window=2 current=t global=f first(leader_chg_hi) AS prev_lc last(leader_chg_hi) AS cur_lc first(prop_fail_hi) AS prev_pf last(prop_fail_hi) AS cur_pf first(prop_commit_hi) AS prev_pc last(prop_commit_hi) AS cur_pc first(health_fail_hi) AS prev_hf last(health_fail_hi) AS cur_hf BY cluster etcd_member
| eval leader_changes_5m=max(0, coalesce(cur_lc,0)-coalesce(prev_lc,0))
| eval prop_failed_5m=max(0, coalesce(cur_pf,0)-coalesce(prev_pf,0))
| eval prop_committed_5m=max(0, coalesce(cur_pc,0)-coalesce(prev_pc,0))
| eval health_fail_delta=max(0, coalesce(cur_hf,0)-coalesce(prev_hf,0))
| eval proposal_backlog_ratio=if(isnotnull(prop_pend), round(prop_pend/max(prop_committed_5m, 0.001), 3), null())
| eval mvcc_db_gb=round(coalesce(mvcc_db_total,0)/1073741824, 3)
| eval member_unhealthy=if(coalesce(is_learner,0)==1, 0, if(coalesce(has_leader_snap,1)==0 OR health_fail_delta>0 OR prop_failed_5m>3, 1, 0))
| eval voting_participant=if(coalesce(is_learner,0)==0, 1, 0)
| eventstats dc(eval(if(voting_participant==1, etcd_member, null()))) AS voting_members dc(eval(if(voting_participant==1 AND member_unhealthy==0, etcd_member, null()))) AS healthy_voting sum(eval(if(voting_participant==1 AND member_unhealthy==1, 1, 0))) AS unhealthy_voting_ct BY cluster win_time
| eval quorum_needed=if(voting_members>0, floor(voting_members/2)+1, 0)
| eval quorum_margin=healthy_voting-quorum_needed
| eventstats median(backend_commit_p95_ms_peer) AS cluster_median_commit_p95 BY cluster win_time
| eval commit_peer_skew_ratio=if(isnotnull(backend_commit_p95_ms_peer) AND coalesce(cluster_median_commit_p95,0)>0.0001, round(backend_commit_p95_ms_peer/cluster_median_commit_p95, 3), null())
| eventstats min(has_leader_snap) AS cluster_min_has_leader BY cluster win_time
| join type=left max=0 win_time [| tstats summariesonly=f count AS app_state_touch FROM datamodel=Application_State WHERE nodename=Application_State earliest=-30m@m latest=@m BY _time span=5m | rename _time AS win_time ]
| join type=left max=0 cluster [| inputlookup cluster_platform_routing.csv | eval cluster=lower(trim(toString(cluster))) | eval on_call_team=toString(coalesce(on_call_team, squad, platform_team, "platform_etcd")) | eval suppress_single_node_dev=tonumber(tostring(coalesce(suppress_single_node_dev, "0")), 10) | eval expected_etcd_voting_members=tonumber(tostring(coalesce(expected_etcd_voting_members, "")), 10) | fields cluster on_call_team suppress_single_node_dev expected_etcd_voting_members ]
| fillnull value="platform_etcd" on_call_team
| eval membership_drift=if(isnotnull(expected_etcd_voting_members) AND expected_etcd_voting_members>0 AND voting_members!=expected_etcd_voting_members, 1, 0)
| eval operational_state=case(cluster_min_has_leader==0, "no_leader_view", quorum_margin<0, "quorum_lost", quorum_margin==0, "quorum_barely_met", membership_drift==1, "membership_drift", leader_changes_5m>=4, "leader_thrash", coalesce(proposal_backlog_ratio,0)>=50 OR coalesce(prop_pend,0)>=5000, "proposal_backlog_hot", coalesce(peer_rtt_p95_ms,0)>=800, "peer_partition_risk", coalesce(commit_peer_skew_ratio,0)>=2, "commit_skew_peer", coalesce(mvcc_db_gb,0)>=7, "mvcc_capacity_signal", true(), "nominal")
| eval severity=case(cluster_min_has_leader==0 OR quorum_margin<0 OR operational_state=="quorum_lost", "down", quorum_margin<=1 OR operational_state=="leader_thrash" OR operational_state=="proposal_backlog_hot" OR membership_drift==1, "critical", operational_state=="peer_partition_risk" OR operational_state=="commit_skew_peer" OR unhealthy_voting_ct>=2, "high", operational_state=="mvcc_capacity_signal" OR leader_changes_5m>=2 OR prop_failed_5m>0 OR coalesce(peer_rtt_p95_ms,0)>=200, "medium", true(), "healthy")
| where coalesce(suppress_single_node_dev,0)==0 OR severity IN ("down","critical")
| join type=left max=0 win_time [| tstats summariesonly=f avg(Performance.cpu_load_percent) AS avg_host_load FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-30m@m latest=@m BY _time span=5m | rename _time AS win_time ]
| table cluster etcd_member win_time voting_members healthy_voting quorum_margin leader_changes_5m peer_rtt_p95_ms commit_peer_skew_ratio proposal_backlog_ratio prop_failed_5m mvcc_db_gb is_learner operational_state severity on_call_team app_state_touch avg_host_load membership_drift
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (like(Application_State.app, "%kube%") OR like(Application_State.app, "%etcd%")) earliest=-1h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS ctrl_host
| join type=left max=0 ctrl_host [| tstats summariesonly=t avg(Performance.cpu_load_percent) AS avg_cpu FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-1h@h latest=@h BY Performance.host | rename Performance.host AS ctrl_host ]
| where like(lower(app_state), "%down%") OR like(lower(app_info), "%fail%") OR avg_cpu>=95
| table ctrl_host app_state app_info avg_cpu
```

## Visualization

Cluster-level single value for quorum_margin and voting_members; timechart of leader_changes_5m stacked by etcd_member; heatmap of commit_peer_skew_ratio; table mirroring the SPL closing projection with cell coloring on severity; overlay of mvcc_db_gb against provider quota consoles when available.

## Known False Positives

Rolling restart of a single etcd member during planned control-plane certificate renewal produces one expected leader handoff and a short burst of etcd_server_leader_changes_seen_total; pair alerts with change tickets or maintenance=true on cluster_platform_routing.csv and require two consecutive windows above churn thresholds before paging. An intentional etcdctl move-leader during a rehearsed failover exercise increments leader change counters once and should not be treated as thrash when annotated. Learner promotion in progress can temporarily show four members while etcd_server_is_learner toggles; widen evaluation to five or ten minutes or correlate with endpoint status JSON showing isLearner transitioning to false before declaring stuck promotion. Maintenance defragmentation on one peer can raise etcd_disk_backend_commit_duration_seconds_bucket skew and etcd_server_proposals_pending briefly without quorum risk; suppress when defrag_started labels or kube-system logs show defrag. Scheduled disaster-recovery tests that snapshot and replicate large states may spike etcd_network_peer_round_trip_time_seconds_bucket for one interval; compare with cross-AZ routing and test windows. A single peer paused for vendor backup can look unhealthy to metrics while quorum remains; verify backup runbooks and heartbeat suppression labels. Graceful member replacement using member remove and add produces short membership drift versus static lookups until expected_etcd_voting_members is updated; treat lookup mismatch as informational until two consecutive scrapes disagree. Brief control-plane network jitter under two hundred milliseconds can elevate histogram quantiles without sustained packet loss; require sustained peer_rtt_p95_ms above warn or packet-drop correlates from network teams before declaring partition. Kind, Minikube, and single-node lab clusters lack meaningful quorum semantics; honor suppress_single_node_dev=1 in the routing lookup.

## References

- [etcd Operations Guide — Monitoring](https://etcd.io/docs/latest/op-guide/monitoring/)
- [etcd Operations Guide — Disaster Recovery](https://etcd.io/docs/latest/op-guide/recovery/)
- [etcd — Runtime configuration (member operations)](https://github.com/etcd-io/etcd/blob/main/Documentation/op-guide/runtime-configuration.md)
- [Kubernetes — Operating etcd clusters for HA](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
- [etcd — Metrics reference](https://etcd.io/docs/latest/metrics/)
- [Kubernetes — kubeadm HA topology (stacked and external etcd)](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/ha-topology/)
- [etcd — Learner design and promotion safety](https://etcd.io/docs/latest/learning/design-learner/)
- [Kubernetes SIG Cluster Lifecycle — community home](https://github.com/kubernetes/community/tree/master/sig-cluster-lifecycle)
