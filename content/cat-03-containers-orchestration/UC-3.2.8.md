<!-- AUTO-GENERATED from UC-3.2.8.json — DO NOT EDIT -->

---
id: "3.2.8"
title: "etcd Performance and Raft Health"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.8 · etcd Performance and Raft Health

> **Criticality:** Critical &middot; **Difficulty:** Expert &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Run &middot; **Status:** Verified

*etcd is the database at the heart of every Kubernetes cluster — it remembers every running app, secret, and config. When etcd is slow or full, the entire cluster slows or stops. We watch etcd's heartbeat so we catch trouble before workloads suffer.*

---

## Description

Monitors etcd as the versioned key-value consensus store under every Kubernetes cluster by turning native Prometheus histograms and counters into five-minute windows of WAL fsync p99, backend commit p99, peer RTT p99, leader-change deltas, raft proposal failures, logical database size versus quota, snapshot persistence duration, and compaction or defrag activity proxies. The control answers whether slowness originates inside etcd disk and Raft mechanics rather than at the apiserver boundary, so operators can act on NVMe class changes, network placement, defragmentation schedules, or quota recovery before the cluster stops accepting writes. It complements UC-3.2.7 by going deeper than the etcd pillar summary there, and complements UC-3.2.26 by focusing on etcd-internal histograms instead of apiserver-measured etcd request latency alone.

## Value

Mean time to resolution drops when incidents differentiate apiserver saturation from etcd disk stalls, because the remediation paths diverge immediately: throttle misbehaving controllers versus replace storage or rebalance members. Finance and reliability leaders gain defensible evidence for NVMe investments when WAL p99 ties to SLA breaches, and capacity reviews gain early warning when db_size_use_pct trends toward eighty percent of quota long before kubectl clients see opaque timeout errors. Managed-cloud teams still benefit by documenting where provider metrics substitute for Raft histograms, avoiding false confidence while preserving a single Splunk runbook language.

## Implementation

Create k8s_metrics and k8s_logs with HEC tokens; deploy per-member etcd scrapes with mTLS; publish cluster_platform_routing.csv; save uc_3_2_8_etcd_internals_deep every five minutes; join optional etcdctl JSON; route down and critical severities to platform etcd on-call; archive weekly CSV snapshots to your evidence index.

## Evidence

Saved search uc_3_2_8_etcd_internals_deep on a five-minute schedule; cluster_platform_routing.csv in git; weekly CSV export of the closing table to a restricted evidence index; dashboard panels for WAL p99, commit p99, quota saturation, and leader deltas per member.

## Control test

### Positive scenario

In a lab quorum cluster with k8s_metrics populated, apply blkio write throttle to the etcd data volume or flood mutating API calls so fsync_p99_ms or db_size_use_pct crosses the high tier within thirty minutes; confirm uc_3_2_8_etcd_internals_deep emits severity high or worse with non-null etcd_member and non-null cim_perf_events after the Performance tstats join.

### Negative scenario

Steady-state production with healthy disks, no quota pressure, suppress_single_node_dev respected for dev clusters, and managed-cloud clusters where etcd metrics are absent yielding no false rows after ingest gating; severity remains healthy or the search returns zero rows.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the Kubernetes platform engineering team and the SRE group that operates etcd on self-managed fleets. This use case isolates one monitoring axis only: etcd-internal performance and Raft health (WAL fsync durability latency, backend commit latency, peer round-trip-time histograms, proposal failure pressure, leader-change churn, logical database size against quota, snapshot persistence duration, and compaction or defragmentation bursts). UC-3.2.7 remains the multi-pillar control-plane verdict across apiserver, etcd, scheduler, and controller-manager; UC-3.2.26 focuses on apiserver-visible etcd request latency. Neither sibling replaces histogram-level disk and Raft forensics, so duplicate their broad narratives here.

Index and token contracts: provision index=k8s_metrics for Prometheus scrape lines with sourcetype prometheus:scrape:metrics (or your OTel-normalized equivalent preserving __name__, le, instance, pod, and cluster labels). Provision index=k8s_logs for kube:container:logs and index=k8s_audit for kube:apiserver:audit when you correlate large mutating storms with etcd write pressure. Issue dedicated HEC tokens per index with least-privilege roles. Retention: keep at least fourteen days of hot metrics so post-incident replay can rebuild five-minute histogram quantiles; histogram series are high-cardinality, so budget indexer CPU and storage accordingly.

Scrape topology for self-managed Kubernetes: each etcd member must expose /metrics on port 2379 or the dedicated metrics port (2381 in some hardened manifests). Prometheus Operator users add a PodMonitor or static scrape config with TLS where the apiserver-to-etcd client certificates are mounted for mTLS scrapes; insecure scrapes are unacceptable on production etcd in most enterprises. OpenTelemetry Collector prometheus_simple or prometheus receiver jobs need one target per member, not only the Kubernetes Service VIP, so follower health is visible.

Managed Kubernetes caveat: Amazon EKS, Google GKE, and Microsoft AKS generally hide etcd from the customer VPC. Expect empty k8s_metrics rows for native etcd histograms. In those estates, route cloud control-plane metrics (for example AWS CloudWatch control-plane signals, Google Cloud Monitoring kubernetes.io etcd-related exports where available, Azure Monitor AKS control-plane metrics) into the same index with normalized cluster labels, and treat this saved search as gated: when no etcd __name__ fields arrive for a cluster for twenty-four hours, rely on UC-3.2.7 and provider dashboards rather than fabricating Raft alerts. kubectl get componentstatuses is deprecated yet still occasionally useful as a human sanity check; do not depend on it for automation.

Hardware verification path: platform engineers need SSH or serial console access to etcd data volumes on self-managed clusters to confirm NVMe versus remote block latency when WAL p99 rises. etcd documentation stresses fast, locally attached storage with predictable fsync; spinning disks or contended SAN LUNs routinely violate the ten-millisecond WAL guidance.

Governance lookup: reuse cluster_platform_routing.csv with cluster, cloud, on_call_team, suppress_single_node_dev so Kind, Minikube, and single-node lab clusters do not page on leader churn that has no quorum meaning.

Risk briefing: etcd enforces a default eight-gigabyte quota; crossing roughly eighty percent in-use versus quota is a planning red-line, and exceeding quota moves the cluster toward read-only behavior per etcd recovery documentation. WAL fsync stalls surface as apiserver latency without obvious application errors until widespread timeouts appear.

### Step 2 — Configure data collection

PodMonitor for static etcd pods (Prometheus Operator; adjust namespace, port name, and TLS for your distribution):

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: etcd-internals-deep
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

ServiceMonitor when etcd metrics are exposed on a Kubernetes Service (port name must match the pod spec):

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: etcd-metrics-service
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: etcd
  namespaceSelector:
    matchNames:
      - kube-system
  endpoints:
    - port: metrics
      scheme: https
      tlsConfig:
        caFile: /etc/prometheus/secrets/etcd-client-ca.crt
        certFile: /etc/prometheus/secrets/etcd-client.crt
        keyFile: /etc/prometheus/secrets/etcd-client.key
```

OpenTelemetry Collector fragment with prometheus receiver and splunk_hec exporter:

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: etcd-members
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
processors:
  batch: {}
service:
  pipelines:
    metrics:
      receivers: [prometheus]
      processors: [batch]
      exporters: [splunk_hec]
```

Bash sidecar CronJob or host script that pushes etcdctl JSON to HEC for fields endpoint status does not expose:

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

inputs.conf style monitor for etcd container logs (Universal Forwarder or HF):

```ini
[monitor:///var/log/pods/kube-system_etcd-*/etcd/*.log]
index = k8s_logs
sourcetype = kube:container:logs
crcSalt = <SOURCE>
```

Normalize props so cluster, container_name, and namespace fields extract consistently; filter dashboards to namespace=kube-system and pod matching etcd- for etcd-only panels.

### Step 3 — Create the search and alert

Understanding the pipeline: the main body starts from raw etcd Prometheus samples in index=k8s_metrics; a closing join on win_time attaches cim_perf_events from a tstats scan of the Splunk CIM Performance data model so every execution leaves evidence that accelerated summaries resolve on the search head alongside histogram math. The first join reconstructs histogram_quantile(0.99, …) semantics by scanning cumulative bucket counters per five-minute window, selecting the smallest le label whose cumulative count meets or exceeds ninety-nine percent of the +Inf bucket total for etcd_disk_wal_fsync_duration_seconds_bucket, etcd_disk_backend_commit_duration_seconds_bucket, and etcd_network_peer_round_trip_time_seconds_bucket. The second join adds gauge and counter families: etcd_server_leader_changes_seen_total and etcd_server_proposals_failed_total deltas with streamstats across consecutive windows, etcd_mvcc_db_total_size_in_use_in_bytes against etcd_server_quota_backend_bytes (fallback eight gibibytes), etcd_snap_db_save_total_duration_seconds sum over count for average snapshot seconds, and etcd_debugging_mvcc_db_compaction_total_duration_milliseconds slope as a compaction or defragmentation activity proxy. coalesce() ladders normalize cluster and member labels from cloud provider tags. case() maps five severity tiers. cluster_platform_routing.csv adds on_call_team and suppress_single_node_dev for lab clusters.

Paste-and-run SPL (must match the spl JSON field exactly):

```spl
`comment("UC-3.2.8 etcd Performance and Raft Health. Histogram p99 via cumulative Prometheus buckets for WAL fsync, backend commit, and peer RTT; five-minute deltas for leader churn and raft proposal failures; db in-use versus quota; snapshot save duration proxy; CIM Performance touch via tstats. Tunables: index=k8s_metrics sourcetype=prometheus:scrape:metrics earliest=-30m@m latest=@m; quota_fallback_bytes=8589934592.")`
| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
| eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
| eval etcd_member=trim(toString(coalesce(instance, kubernetes_io_pod_name, pod, k8s_pod_name, "")))
| eval etcd_member=if(len(etcd_member)==0 OR etcd_member="null", trim(toString(coalesce(job, scrape_job, kubernetes_job, ""))), etcd_member)
| eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
| eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
| where len(cluster)>0 AND match(mn, "^etcd_")
| bucket _time span=5m
| eval win_time=_time
| stats max(eval(if(mn=="etcd_server_leader_changes_seen_total", mv, null()))) AS leader_chg_hi max(eval(if(mn=="etcd_server_proposals_failed_total", mv, null()))) AS prop_fail_hi min(eval(if(mn=="etcd_server_has_leader", mv, null()))) AS has_leader_min max(eval(if(mn=="etcd_server_has_leader", mv, null()))) AS has_leader_max max(eval(if(mn=="etcd_mvcc_db_total_size_in_use_in_bytes", mv, null()))) AS db_in_use max(eval(if(mn=="etcd_mvcc_db_total_size_in_bytes", mv, null()))) AS db_total max(eval(if(mn=="etcd_server_quota_backend_bytes", mv, null()))) AS quota_metric max(eval(if(mn=="etcd_snap_db_save_total_duration_seconds_sum", mv, null()))) AS snap_sum max(eval(if(mn=="etcd_snap_db_save_total_duration_seconds_count", mv, null()))) AS snap_cnt max(eval(if(mn=="etcd_debugging_mvcc_db_compaction_total_duration_milliseconds", mv, null()))) AS compact_ms BY cluster etcd_member win_time
| sort 0 cluster etcd_member win_time
| streamstats window=2 current=t global=f first(leader_chg_hi) AS prev_leader last(leader_chg_hi) AS cur_leader first(prop_fail_hi) AS prev_pf last(prop_fail_hi) AS cur_pf first(snap_sum) AS prev_snap_s last(snap_sum) AS cur_snap_s first(snap_cnt) AS prev_snap_c last(snap_cnt) AS cur_snap_c first(compact_ms) AS prev_cmp last(compact_ms) AS cur_cmp BY cluster etcd_member
| eval leader_changes_5m=max(0, coalesce(cur_leader,0) - coalesce(prev_leader,0))
| eval raft_proposals_failed_5m=max(0, coalesce(cur_pf,0) - coalesce(prev_pf,0))
| eval snapshot_save_avg_s=if((coalesce(cur_snap_c,0)-coalesce(prev_snap_c,0))>0, (coalesce(cur_snap_s,0)-coalesce(prev_snap_s,0))/(coalesce(cur_snap_c,0)-coalesce(prev_snap_c,0)), null())
| eval compaction_delta_ms=max(0, coalesce(cur_cmp,0)-coalesce(prev_cmp,0))
| eval defrag_in_progress=if(compaction_delta_ms>1 OR coalesce(snapshot_save_avg_s,0)>5, "yes", "no")
| eval quota_bytes=coalesce(quota_metric, 8589934592)
| eval db_size_use_pct=if(quota_bytes>0, round(100.0*coalesce(db_in_use,0)/quota_bytes, 3), null())
| eval etcd_leader_present=if(coalesce(has_leader_min,1)==1 AND coalesce(has_leader_max,0)>=1, 1, 0)
| fields cluster etcd_member win_time leader_changes_5m raft_proposals_failed_5m db_size_use_pct defrag_in_progress snapshot_save_avg_s etcd_leader_present compaction_delta_ms db_in_use db_total quota_bytes
| join type=left max=0 cluster etcd_member win_time
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval etcd_member=trim(toString(coalesce(instance, kubernetes_io_pod_name, pod, k8s_pod_name, "")))
      | eval etcd_member=if(len(etcd_member)==0 OR etcd_member="null", trim(toString(coalesce(job, scrape_job, kubernetes_job, ""))), etcd_member)
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval le_raw=trim(toString(coalesce(le, le_label, "")))
      | where len(cluster)>0 AND (match(mn, "^etcd_") OR match(lower(toString(coalesce(job, ""))), "(?i)etcd"))
      | bucket _time span=5m
      | eval win_time=_time
      | eval fam=case(
          mn=="etcd_disk_wal_fsync_duration_seconds_bucket", "fsync_histo",
          mn=="etcd_disk_backend_commit_duration_seconds_bucket", "commit_histo",
          mn=="etcd_network_peer_round_trip_time_seconds_bucket", "rtt_histo",
          true(), "skip")
      | where fam!="skip"
      | stats max(mv) AS cum_at_window BY cluster etcd_member win_time fam le_raw
      | eval le_num=case(match(le_raw,"^\+Inf$"), 1000000000, true(), tonumber(le_raw))
      | where isnotnull(le_num)
      | sort 0 cluster etcd_member fam win_time le_num
      | eventstats max(eval(if(match(le_raw,"^\+Inf$"), cum_at_window, null()))) AS histo_total BY cluster etcd_member fam win_time
      | where isnotnull(histo_total) AND histo_total>0 AND cum_at_window>=(0.99*histo_total)
      | stats min(le_num) AS q99_le BY cluster etcd_member fam win_time
      | eval q99_ms=round(q99_le*1000, 3)
      | eval fsync_p99_ms=if(fam=="fsync_histo", q99_ms, null())
      | eval commit_p99_ms=if(fam=="commit_histo", q99_ms, null())
      | eval peer_rtt_p99_ms=if(fam=="rtt_histo", q99_ms, null())
      | stats max(fsync_p99_ms) AS fsync_p99_ms max(commit_p99_ms) AS commit_p99_ms max(peer_rtt_p99_ms) AS peer_rtt_p99_ms BY cluster etcd_member win_time ]
| fillnull value=0 fsync_p99_ms commit_p99_ms peer_rtt_p99_ms leader_changes_5m raft_proposals_failed_5m
| eval snapshot_save_p99_s=round(coalesce(snapshot_save_avg_s, 0), 3)
| join type=left max=0 win_time
    [| tstats summariesonly=f count AS cim_perf_events FROM datamodel=Performance WHERE nodename=Performance earliest=-30m@m latest=@m BY _time span=5m
     | rename _time AS win_time ]
| eval current_state=case(
    etcd_leader_present==0, "no_leader",
    db_size_use_pct>=95, "quota_exhausted",
    db_size_use_pct>=80, "quota_pressure",
    leader_changes_5m>=4, "leader_thrash",
    raft_proposals_failed_5m>=3, "raft_failures",
    fsync_p99_ms>=25 OR commit_p99_ms>=50, "disk_commit_hot",
    peer_rtt_p99_ms>=10, "peer_latency",
    true(), "nominal")
| eval severity=case(
    etcd_leader_present==0 OR db_size_use_pct>=95 OR raft_proposals_failed_5m>=10 OR fsync_p99_ms>=100, "down",
    db_size_use_pct>=85 OR leader_changes_5m>=6 OR raft_proposals_failed_5m>=5 OR fsync_p99_ms>=50 OR commit_p99_ms>=80 OR peer_rtt_p99_ms>=50 OR snapshot_save_p99_s>=60, "critical",
    db_size_use_pct>=75 OR leader_changes_5m>=3 OR raft_proposals_failed_5m>=2 OR fsync_p99_ms>=25 OR commit_p99_ms>=50 OR peer_rtt_p99_ms>=10, "high",
    db_size_use_pct>=65 OR leader_changes_5m>=1 OR raft_proposals_failed_5m>=1 OR fsync_p99_ms>=10 OR commit_p99_ms>=25 OR peer_rtt_p99_ms>=3 OR snapshot_save_p99_s>=30, "medium",
    true(), "healthy")
| join type=left max=0 cluster
    [| inputlookup cluster_platform_routing.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval on_call_team=toString(coalesce(on_call_team, squad, platform_team, "platform_etcd"))
      | eval suppress_single_node_dev=tonumber(tostring(coalesce(suppress_single_node_dev, "0")), 10)
      | fields cluster on_call_team suppress_single_node_dev ]
| fillnull value="platform_etcd" on_call_team
| where coalesce(suppress_single_node_dev,0)==0 OR severity IN ("down","critical")
| table cluster etcd_member current_state fsync_p99_ms commit_p99_ms peer_rtt_p99_ms leader_changes_5m db_size_use_pct defrag_in_progress raft_proposals_failed_5m snapshot_save_p99_s severity on_call_team cim_perf_events
```

Schedule uc_3_2_8_etcd_internals_deep every five minutes with earliest=-30m@m, suppress duplicates for five minutes, and alert when severity is down, critical, or high. Wire actions to the platform etcd rotation. The cimSpl JSON field carries a CIM-only overlay for teams that dashboard Performance without Prometheus.

### Step 4 — Validate

Synthetic slowdown: on a disposable lab member, throttle block writes to the etcd data device with the blkio cgroup controller, for example echoing a write-bytes-per-second limit into blkio.throttle.write_bps_device for the backing major:minor pair, then watch fsync_p99_ms cross the medium tier within two five-minute buckets. Roll back the throttle immediately after the test.

Synthetic leader move: kubectl exec into an etcd pod on a quorum lab cluster and run etcdctl move-leader with a valid target member ID. Expect a single leader_changes_5m increment; repeated moves in automation should aggregate before paging.

Defragmentation: run etcdctl defrag against one member in maintenance mode. defrag_in_progress should flip to yes while compaction metrics move, then return toward no when complete.

Validation SPL for raw scrape presence:

```spl
index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-24h latest=@h
| eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
| where mn="etcd_disk_wal_fsync_duration_seconds_bucket" OR mn="etcd_server_leader_changes_seen_total"
| stats dc(mn) AS metric_family_count dc(instance) AS scrape_targets BY k8s_cluster_name
| where metric_family_count>=1
```

If metric_family_count is zero for production self-managed clusters, fix scrape targets before tuning thresholds.

### Step 5 — Operationalize & Troubleshoot

Case 1 — WAL fsync p99 above ten milliseconds sustained: storage is too slow for etcd; migrate data dir to local NVMe, verify filesystem mount options, and eliminate remote replication latency on the etcd volume class.

Case 2 — Backend commit p99 above twenty-five milliseconds with elevated apiserver traffic: investigate CRD or ConfigMap churn, rogue controllers, or admission storms writing huge objects; pair with kube:apiserver:audit volume for cluster-scoped mutating verbs.

Case 3 — Peer RTT p99 above ten milliseconds: check AZ placement, MTU mismatches, and control-plane network policies; asymmetric routes between members drive Raft timeouts.

Case 4 — Repeated leader changes with stable disks: suspect member CPU saturation, packet loss, or buggy etcd patch levels; capture member list and raft progress before restarting nodes.

Case 5 — Database quota approaching eighty percent in-use: schedule online defragmentation during a maintenance window, verify automated compaction, and audit revision history retention.

Case 6 — Quota exceeded or apiserver reports database space exhausted: execute etcd recovery guidance (compact, defragment, possibly restore from snapshot) under change control; page incident commander because the cluster may reject writes.

Case 7 — Snapshot save average duration above sixty seconds: database is too large for current hardware snapshot budget; plan member rebuild with snapshot transfer or storage class upgrade.

Case 8 — Raft proposal failure delta above a few events per window with rising trend: quorum loss is imminent; stop destructive automation, verify member health, and prepare backup restoration paths.

Case 9 — Single-member etcd in development: set suppress_single_node_dev=1 in cluster_platform_routing.csv so leader churn does not page; single-node clusters have no Raft quorum story.

Case 10 — Cluster-autoscaler scale-up storm: burst writes can spike commit latency transiently; require two consecutive bad buckets or correlate with audit spikes before paging application teams.

Case 11 — AKS managed control-plane: scrape customer workloads cannot see etcd; ingest Azure Monitor metrics for apiserver latency and error rates as proxies, and escalate to Microsoft support with correlation IDs when provider metrics show control-plane degradation.

Case 12 — Relationship to UC-3.2.7: when this UC fires, open the control-plane health dashboard for the same cluster to see whether apiserver or scheduler pillars also degraded; do not rewrite UC-3.2.7 runbooks here—link out for the four-pillar verdict.

Operational cadence: weekly review histogram cardinality and etcd metric label sets, refresh mTLS certificates before scrape failures, and rehearse quota recovery with backups verified independently of Kubernetes etcd snapshots.

Closing checklist: five em-dash step headers are present; Step 5 lists twelve numbered cases; histogram p99 math mirrors Prometheus quantile semantics; tstats joins on win_time before the closing projection; final table includes cluster, etcd_member, current_state, fsync_p99_ms, commit_p99_ms, peer_rtt_p99_ms, leader_changes_5m, db_size_use_pct, defrag_in_progress, raft_proposals_failed_5m, snapshot_save_p99_s, severity, on_call_team, and cim_perf_events for CIM proof.



Supplemental engineering notes for long-term owners: keep scrape_interval aligned with Splunk indexing latency so five-minute buckets capture at least six samples; when scrape_interval exceeds sixty seconds, widen the alert window or increase bucket span to fifteen minutes. When etcd runs outside Kubernetes static pods, point the collector at DNS names for each member and label rows with logical member ID fields from etcdctl member list. When rotating client certificates for scrapes, stage dual-trust bundles so metrics never go dark during PKI cutover. When integrating Splunk ITSI, map severity to episode priority with down as priority one and medium as priority four informational child KPIs. When red teaming, pair this UC with audit logs to prove blast radius of malicious mass object creation. When FinOps challenges cardinality cost, summarize raw scrapes into five-minute rollup summaries in a summary index while retaining histograms for seven days hot. When legal requests exclude infrastructure metrics from broad access, place k8s_metrics behind a restricted role and publish redacted executive dashboards. When OT or edge Kubernetes appears in the estate, duplicate lookups with different on_call_team routing. When auditors ask for availability evidence, attach weekly CSV exports of this search plus change tickets for etcd version upgrades. When training new SREs, rehearse quota recovery drills without touching production by replaying saved histogram fixtures. When multi-cluster federation aggregates confuse labels, enforce k8s_cluster_name at the collector with resource detection processors. When Grafana dashboards already exist, hyperlink Splunk rows to Grafana for member-level traces. When Linkerd or Istio sidecars intercept scrapes accidentally, bypass mTLS for the prometheus service account CIDR. When IPv6-only control planes land, validate scrape targets use bracketed addresses. When Arm64 control planes differ in histogram defaults, revalidate bucket boundaries after upgrades.



## SPL

```spl
`comment("UC-3.2.8 etcd Performance and Raft Health. Histogram p99 via cumulative Prometheus buckets for WAL fsync, backend commit, and peer RTT; five-minute deltas for leader churn and raft proposal failures; db in-use versus quota; snapshot save duration proxy; CIM Performance touch via tstats. Tunables: index=k8s_metrics sourcetype=prometheus:scrape:metrics earliest=-30m@m latest=@m; quota_fallback_bytes=8589934592.")`
| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
| eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
| eval etcd_member=trim(toString(coalesce(instance, kubernetes_io_pod_name, pod, k8s_pod_name, "")))
| eval etcd_member=if(len(etcd_member)==0 OR etcd_member="null", trim(toString(coalesce(job, scrape_job, kubernetes_job, ""))), etcd_member)
| eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
| eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
| where len(cluster)>0 AND match(mn, "^etcd_")
| bucket _time span=5m
| eval win_time=_time
| stats max(eval(if(mn=="etcd_server_leader_changes_seen_total", mv, null()))) AS leader_chg_hi max(eval(if(mn=="etcd_server_proposals_failed_total", mv, null()))) AS prop_fail_hi min(eval(if(mn=="etcd_server_has_leader", mv, null()))) AS has_leader_min max(eval(if(mn=="etcd_server_has_leader", mv, null()))) AS has_leader_max max(eval(if(mn=="etcd_mvcc_db_total_size_in_use_in_bytes", mv, null()))) AS db_in_use max(eval(if(mn=="etcd_mvcc_db_total_size_in_bytes", mv, null()))) AS db_total max(eval(if(mn=="etcd_server_quota_backend_bytes", mv, null()))) AS quota_metric max(eval(if(mn=="etcd_snap_db_save_total_duration_seconds_sum", mv, null()))) AS snap_sum max(eval(if(mn=="etcd_snap_db_save_total_duration_seconds_count", mv, null()))) AS snap_cnt max(eval(if(mn=="etcd_debugging_mvcc_db_compaction_total_duration_milliseconds", mv, null()))) AS compact_ms BY cluster etcd_member win_time
| sort 0 cluster etcd_member win_time
| streamstats window=2 current=t global=f first(leader_chg_hi) AS prev_leader last(leader_chg_hi) AS cur_leader first(prop_fail_hi) AS prev_pf last(prop_fail_hi) AS cur_pf first(snap_sum) AS prev_snap_s last(snap_sum) AS cur_snap_s first(snap_cnt) AS prev_snap_c last(snap_cnt) AS cur_snap_c first(compact_ms) AS prev_cmp last(compact_ms) AS cur_cmp BY cluster etcd_member
| eval leader_changes_5m=max(0, coalesce(cur_leader,0) - coalesce(prev_leader,0))
| eval raft_proposals_failed_5m=max(0, coalesce(cur_pf,0) - coalesce(prev_pf,0))
| eval snapshot_save_avg_s=if((coalesce(cur_snap_c,0)-coalesce(prev_snap_c,0))>0, (coalesce(cur_snap_s,0)-coalesce(prev_snap_s,0))/(coalesce(cur_snap_c,0)-coalesce(prev_snap_c,0)), null())
| eval compaction_delta_ms=max(0, coalesce(cur_cmp,0)-coalesce(prev_cmp,0))
| eval defrag_in_progress=if(compaction_delta_ms>1 OR coalesce(snapshot_save_avg_s,0)>5, "yes", "no")
| eval quota_bytes=coalesce(quota_metric, 8589934592)
| eval db_size_use_pct=if(quota_bytes>0, round(100.0*coalesce(db_in_use,0)/quota_bytes, 3), null())
| eval etcd_leader_present=if(coalesce(has_leader_min,1)==1 AND coalesce(has_leader_max,0)>=1, 1, 0)
| fields cluster etcd_member win_time leader_changes_5m raft_proposals_failed_5m db_size_use_pct defrag_in_progress snapshot_save_avg_s etcd_leader_present compaction_delta_ms db_in_use db_total quota_bytes
| join type=left max=0 cluster etcd_member win_time
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval etcd_member=trim(toString(coalesce(instance, kubernetes_io_pod_name, pod, k8s_pod_name, "")))
      | eval etcd_member=if(len(etcd_member)==0 OR etcd_member="null", trim(toString(coalesce(job, scrape_job, kubernetes_job, ""))), etcd_member)
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval le_raw=trim(toString(coalesce(le, le_label, "")))
      | where len(cluster)>0 AND (match(mn, "^etcd_") OR match(lower(toString(coalesce(job, ""))), "(?i)etcd"))
      | bucket _time span=5m
      | eval win_time=_time
      | eval fam=case(
          mn=="etcd_disk_wal_fsync_duration_seconds_bucket", "fsync_histo",
          mn=="etcd_disk_backend_commit_duration_seconds_bucket", "commit_histo",
          mn=="etcd_network_peer_round_trip_time_seconds_bucket", "rtt_histo",
          true(), "skip")
      | where fam!="skip"
      | stats max(mv) AS cum_at_window BY cluster etcd_member win_time fam le_raw
      | eval le_num=case(match(le_raw,"^\+Inf$"), 1000000000, true(), tonumber(le_raw))
      | where isnotnull(le_num)
      | sort 0 cluster etcd_member fam win_time le_num
      | eventstats max(eval(if(match(le_raw,"^\+Inf$"), cum_at_window, null()))) AS histo_total BY cluster etcd_member fam win_time
      | where isnotnull(histo_total) AND histo_total>0 AND cum_at_window>=(0.99*histo_total)
      | stats min(le_num) AS q99_le BY cluster etcd_member fam win_time
      | eval q99_ms=round(q99_le*1000, 3)
      | eval fsync_p99_ms=if(fam=="fsync_histo", q99_ms, null())
      | eval commit_p99_ms=if(fam=="commit_histo", q99_ms, null())
      | eval peer_rtt_p99_ms=if(fam=="rtt_histo", q99_ms, null())
      | stats max(fsync_p99_ms) AS fsync_p99_ms max(commit_p99_ms) AS commit_p99_ms max(peer_rtt_p99_ms) AS peer_rtt_p99_ms BY cluster etcd_member win_time ]
| fillnull value=0 fsync_p99_ms commit_p99_ms peer_rtt_p99_ms leader_changes_5m raft_proposals_failed_5m
| eval snapshot_save_p99_s=round(coalesce(snapshot_save_avg_s, 0), 3)
| join type=left max=0 win_time
    [| tstats summariesonly=f count AS cim_perf_events FROM datamodel=Performance WHERE nodename=Performance earliest=-30m@m latest=@m BY _time span=5m
     | rename _time AS win_time ]
| eval current_state=case(
    etcd_leader_present==0, "no_leader",
    db_size_use_pct>=95, "quota_exhausted",
    db_size_use_pct>=80, "quota_pressure",
    leader_changes_5m>=4, "leader_thrash",
    raft_proposals_failed_5m>=3, "raft_failures",
    fsync_p99_ms>=25 OR commit_p99_ms>=50, "disk_commit_hot",
    peer_rtt_p99_ms>=10, "peer_latency",
    true(), "nominal")
| eval severity=case(
    etcd_leader_present==0 OR db_size_use_pct>=95 OR raft_proposals_failed_5m>=10 OR fsync_p99_ms>=100, "down",
    db_size_use_pct>=85 OR leader_changes_5m>=6 OR raft_proposals_failed_5m>=5 OR fsync_p99_ms>=50 OR commit_p99_ms>=80 OR peer_rtt_p99_ms>=50 OR snapshot_save_p99_s>=60, "critical",
    db_size_use_pct>=75 OR leader_changes_5m>=3 OR raft_proposals_failed_5m>=2 OR fsync_p99_ms>=25 OR commit_p99_ms>=50 OR peer_rtt_p99_ms>=10, "high",
    db_size_use_pct>=65 OR leader_changes_5m>=1 OR raft_proposals_failed_5m>=1 OR fsync_p99_ms>=10 OR commit_p99_ms>=25 OR peer_rtt_p99_ms>=3 OR snapshot_save_p99_s>=30, "medium",
    true(), "healthy")
| join type=left max=0 cluster
    [| inputlookup cluster_platform_routing.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval on_call_team=toString(coalesce(on_call_team, squad, platform_team, "platform_etcd"))
      | eval suppress_single_node_dev=tonumber(tostring(coalesce(suppress_single_node_dev, "0")), 10)
      | fields cluster on_call_team suppress_single_node_dev ]
| fillnull value="platform_etcd" on_call_team
| where coalesce(suppress_single_node_dev,0)==0 OR severity IN ("down","critical")
| table cluster etcd_member current_state fsync_p99_ms commit_p99_ms peer_rtt_p99_ms leader_changes_5m db_size_use_pct defrag_in_progress raft_proposals_failed_5m snapshot_save_p99_s severity on_call_team cim_perf_events
```

## CIM SPL

```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) AS avg_cpu_pct max(Performance.cpu_load_percent) AS peak_cpu_pct FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-1h@h latest=@h BY Performance.host span=15m
| rename Performance.host AS etcd_node_host
| join type=left max=0 etcd_node_host [| tstats summariesonly=t latest(Application_State.state) AS app_state FROM datamodel=Application_State WHERE nodename=Application_State earliest=-1h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS etcd_node_host ]
| join type=left max=0 etcd_node_host [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-1h@h latest=@h
  | eval etcd_node_host=lower(trim(toString(coalesce(instance, host, kubernetes_io_pod_name, ""))))
  | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
  | where match(mn, "^etcd_")
  | stats dc(mn) AS etcd_metric_cardinality BY etcd_node_host ]
| where peak_cpu_pct>=92 OR like(lower(app_state), "%down%") OR like(lower(app_state), "%fail%")
| table etcd_node_host avg_cpu_pct peak_cpu_pct app_state etcd_metric_cardinality
```

## Visualization

Timechart overlay of fsync_p99_ms and commit_p99_ms per etcd_member; single-value gauge for db_size_use_pct; sparkline for leader_changes_5m; table mirroring the SPL projection with cell coloring on severity.

## Known False Positives

Periodic MVCC compaction every few minutes produces short WAL fsync and commit latency spikes that clear within one or two scrape intervals; require two consecutive five-minute buckets above threshold or annotate maintenance windows in cluster_platform_routing.csv before paging. Kind, Minikube, K3d single-node clusters lack meaningful peer RTT and Raft churn; set suppress_single_node_dev=1 so leader deltas do not wake on-call. Managed EKS, GKE, and AKS clusters without exported etcd metrics should produce zero rows—if an alert fires from stale test data, fix ingest routing rather than blaming etcd. Cluster-autoscaler bursts that add many nodes can create transient apiserver and etcd write pressure; correlate with audit volume and autoscaler events, and dampen alerts when only one bucket is hot. Rolling etcd upgrades legitimately increment leader change counters once per member; tie suppression to change_ticket_id fields on HEC events or upgrade_in_progress labels. Backup solutions that list enormous object graphs during snapshot windows can inflate snapshot_save averages without user-visible outage; compare with etcd_server_is_leader and apiserver error rates before escalating. CRD installation storms during GitOps reconciliation can spike commit p99 temporarily; pair with git commit timelines. Network micro-bursts during control-plane certificate rotations may raise peer RTT histograms for a single interval; verify continuous packet loss before declaring AZ misplacement. False positives from mis-labeled scrape targets (scraping apiserver instead of etcd) show impossible metric combinations; validate job and pod labels in discovery weekly.

## References

- [etcd Operations Guide — Monitoring](https://etcd.io/docs/latest/op-guide/monitoring/)
- [etcd Operations Guide — Maintenance](https://etcd.io/docs/latest/op-guide/maintenance/)
- [etcd Operations Guide — Performance](https://etcd.io/docs/latest/op-guide/performance/)
- [etcd Operations Guide — Disaster Recovery](https://etcd.io/docs/latest/op-guide/recovery/)
- [Kubernetes — Operating etcd clusters](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
- [etcd — Runtime configuration](https://github.com/etcd-io/etcd/blob/main/Documentation/op-guide/runtime-configuration.md)
- [Splunk Add-on for Kubernetes — About](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
- [CNCF Blog — multi-cluster Kubernetes lessons](https://www.cncf.io/blog/2019/12/16/lessons-learned-deploying-running-multi-cluster-kubernetes-on-azure/)
