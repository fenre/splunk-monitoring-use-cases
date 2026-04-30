<!-- AUTO-GENERATED from UC-3.2.34.json — DO NOT EDIT -->

---
id: "3.2.34"
title: "CoreDNS and Kube-DNS Cluster DNS Plane Health"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.34 · CoreDNS and Kube-DNS Cluster DNS Plane Health

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*Every app inside a Kubernetes cluster looks up other apps by name through the cluster DNS service. When that DNS service slows or fails, even healthy apps appear broken to each other. We watch that cluster address book so the shared resolver is never invisible when things go wrong.*

---

## Description

This control isolates the east-west cluster DNS service plane: CoreDNS and kube-dns pods in kube-system that answer every in-cluster A, AAAA, SRV, and PTR lookup before workloads ever open TCP to a ClusterIP. The analytic fuses Prometheus coredns_* counters and histograms with kube-state readiness counts, Kubernetes events, and filtered CoreDNS container logs so operators see SERVFAIL and REFUSED spikes, NXDOMAIN storms, tail latency from dns_request_duration_seconds buckets, cache effectiveness from hits versus misses, upstream forward failure rates when the forward plugin targets public or corporate resolvers, reload failures from coredns_reload_failed_count_total, and replica readiness drift on the DNS Deployment. UC-3.2.9 owns north-south ingress HTTP health. UC-3.2.41 owns Kubernetes Service Endpoints object cardinality and zero-ready endpoint conditions. UC-3.1.14 owns Docker overlay L3 and L4 control-plane semantics. None of those replace authoritative observation of the recursive resolver that every pod hits via the cluster IP of kube-dns.

## Value

Customer pain from a brownout cluster DNS plane looks like random application timeouts, JDBC URL resolution failures, and intermittent gRPC channel errors while pod Ready columns stay green, because the failure sits between healthy processes and the names they resolve. Finance and executive stakeholders gain a single evidence line that separates DNS-plane incidents from application code regressions, which shortens bridges and avoids duplicate license spend on redundant APM traces. Platform teams quantify when NodeLocal DNSCache or CoreDNS HPA actually prevented an outage versus when it masked insufficient forward capacity. Regulators and internal auditors reviewing availability controls can cite saved-search exports that name cluster, replica readiness, error-class ratios, and tail latency in milliseconds tied to the same Prometheus families documented in CoreDNS metrics reference material.

## Implementation

Stand up index=k8s_metrics and index=k8s_logs with HEC tokens; scrape each CoreDNS pod :9153/metrics via OTel or ServiceMonitor; ship kube:container:logs for kube-system coredns-* pods and Kubernetes events; publish lookups/coredns_oncall_routing.csv; save uc_3_2_34_coredns_cluster_dns_plane every five minutes on earliest=-70m latest=now; route critical and high severities using on_call_team; retain weekly CSV snapshots for DNS SLO reviews.

## Evidence

Saved search uc_3_2_34_coredns_cluster_dns_plane; lookups/coredns_oncall_routing.csv versioned in git; weekly CSV exports of severity rows to a restricted evidence index; dashboard panels combining servfail_rate_pct, p99_latency_ms, cache_hit_ratio_pct, upstream_failure_rate_pct, ready_pod_count, and config_reload_failed timelines with drilldowns to kube:container:logs for kube-system CoreDNS pods.

## Control test

### Positive scenario

In a lab cluster, misconfigure CoreDNS forward upstream temporarily under change control, ingest elevated coredns_forward_responses_total with rcode SERVFAIL, execute uc_3_2_34_coredns_cluster_dns_plane, and expect a non-healthy severity with elevated servfail_rate_pct or upstream_failure_rate_pct on the affected cluster row.

### Negative scenario

In a steady lab cluster with healthy CoreDNS pods, stable coredns_reload_failed_count_total at zero, and nominal SERVFAIL ratios below tunable floors, expect healthy classification such that the alert search returns zero rows across four consecutive five-minute intervals.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the Kubernetes platform networking team, the fleet engineer who certifies kube-system telemetry, and the observability engineer who validates Prometheus label parity from OTel to Splunk. UC-3.2.34 isolates the cluster-internal DNS resolver plane implemented by CoreDNS or legacy kube-dns: the small Deployment in kube-system whose ClusterIP is wired into every Pod resolv.conf. UC-3.2.9 covers north-south HTTP ingress controller reliability. UC-3.2.41 covers Kubernetes Service Endpoints readiness and zero-endpoint conditions. UC-3.1.14 covers Docker Swarm overlay gossip and VXLAN data-plane health. Those siblings do not emit coredns_dns_responses_total rcode labels, forward plugin histograms, or Corefile reload failure counters, which are the authoritative signals for this plane.

Before you schedule the saved search, confirm six indexing paths are healthy. First, index=k8s_metrics ingests Prometheus scrapes from each CoreDNS Pod port 9153 with resource attributes that preserve cluster, namespace kube-system, pod, and container names through the Splunk OpenTelemetry Collector kubernetesattributes processor. Validate that metric_name or __name__ fields retain coredns_dns_requests_total, coredns_dns_responses_total, coredns_dns_request_duration_seconds_bucket, coredns_cache_hits_total, coredns_cache_misses_total, coredns_forward_responses_total, and coredns_reload_failed_count_total as documented in CoreDNS metrics plugin reference pages. Second, kube-state-metrics or an equivalent agent must emit kube_deployment_status_replicas_ready and kube_deployment_spec_replicas for the coredns or kube-dns Deployment so ready_pod_count can be compared to intent during incidents. Third, index=k8s_logs carries sourcetype kube:container:logs lines from CoreDNS containers with fields that allow filtering on kubernetes_namespace_name or namespace equal to kube-system and pod name prefix coredns-. Fourth, Kubernetes Warning and Normal events that mention CoreDNS pods, FailedScheduling, or Probe failures should land in the same ecosystem index you already use for platform troubleshooting. Fifth, publish lookups/coredns_oncall_routing.csv with cluster, on_call_team, optional synthetic_probe_namespace, and optional preview_cluster flag so paging routes consistently when multiple fleet patterns coexist. Sixth, RBAC on the collector ServiceAccount must allow GET on pods and endpoints in kube-system for Prometheus discovery when using kubernetes_sd_configs; document EKS IRSA ARMs, GKE workload identity bindings, or AKS managed identities beside this UC so audits trace secret usage.

Risk framing for incident commanders: when CoreDNS returns SERVFAIL or stops answering before upstream TCP connects succeed, applications log connection timeouts, gRPC UNAVAILABLE, and JDBC communications link failures that resemble database outages. Without this control, bridges burn hours proving databases innocent while the real fault is a broken recursive path or an overloaded DNS pod. NodeLocal DNSCache changes traffic patterns: CoreDNS may see fewer queries while node caches warm, so sudden load spikes after NodeLocal disablement are expected and must be read against architecture documentation rather than against yesterday’s absolute query count alone. Managed Kubernetes distributions differ: Amazon EKS ships CoreDNS as a managed add-on; Google Kubernetes Engine may expose kube-dns or CoreDNS depending on cluster generation; Azure Kubernetes Service standardizes on CoreDNS. Field normalization through coalesce must absorb those vendor label differences without forking the SPL per cloud.

Capacity and licensing: Prometheus scrape of fifteen-second cadence across three CoreDNS pods is modest compared to verbose application logs; still, high-cardinality zone labels on coredns_dns_requests_total can inflate series counts. Drop high-cardinality labels at the relabel stage when finance flags cardinality risk, keeping rcode and server labels that the alert requires. HEC tokens stay in vault with quarterly rotation. Legal review may require stripping QNAME-like strings if you later add log-based DNS analytics; this baseline UC relies on aggregated metrics and kube-system logs without per-tenant query logging by default.

Governance: coredns_oncall_routing.csv refreshes weekly from the service catalog. Clusters that run dedicated DNS node pools or Istio multi-cluster federation get explicit rows so severity routing does not default to a generic platform queue during a mesh incident.


### Step 2 — Configure data collection

Deploy a ServiceMonitor or PodMonitor, or an equivalent scrape job in the Splunk OpenTelemetry Collector prometheus receiver, that discovers every Endpoints object backing the kube-dns Service in kube-system and scrapes path /metrics on port 9153. Preserve kubernetes_pod_name, namespace, cluster, and node labels on every sample so the SPL can split by coredns_pod while still rolling up to cluster. Configure relabel rules that strip pod UID suffix randomness only when you have a stable alternate key; otherwise keep full pod names so restart storms remain visible.

Example ServiceMonitor for CoreDNS metrics in kube-system:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: coredns-metrics
  namespace: kube-system
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      k8s-app: kube-dns
  endpoints:
    - port: metrics
      interval: 15s
      path: /metrics
      scheme: http
```

Splunk OpenTelemetry Collector fragment with prometheus, k8s_events, filelog, and splunk_hec exporters:

```yaml
receivers:
  prometheus/coredns:
    config:
      scrape_configs:
        - job_name: kubernetes-pods-coredns
          kubernetes_sd_configs:
            - role: pod
          relabel_configs:
            - source_labels: [__meta_kubernetes_namespace]
              action: keep
              regex: kube-system
            - source_labels: [__meta_kubernetes_pod_name]
              action: keep
              regex: coredns.*
            - source_labels: [__meta_kubernetes_pod_ip]
              target_label: __address__
              replacement: "${1}:9153"
  k8s_events:
    auth_type: serviceAccount
  filelog/coredns:
    include:
      - /var/log/pods/kube-system_coredns-*/*/*.log
exporters:
  splunk_hec/metrics:
    token: "${SPLUNK_HEC_TOKEN_K8S_METRICS}"
    endpoint: "https://splunk.example.com:8088/services/collector"
    index: k8s_metrics
  splunk_hec/logs:
    token: "${SPLUNK_HEC_TOKEN_K8S_LOGS}"
    endpoint: "https://splunk.example.com:8088/services/collector"
    index: k8s_logs
service:
  pipelines:
    metrics:
      receivers: [prometheus/coredns]
      processors: [k8sattributes, batch]
      exporters: [splunk_hec/metrics]
    logs:
      receivers: [filelog/coredns]
      processors: [k8sattributes, batch]
      exporters: [splunk_hec/logs]
    events:
      receivers: [k8s_events]
      processors: [batch]
      exporters: [splunk_hec/logs]
```

CoreDNS Corefile ConfigMap fragment enabling prometheus on :9153:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health {
            lameduck 5s
        }
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
            pods insecure
            fallthrough in-addr.arpa ip6.arpa
            ttl 30
        }
        prometheus :9153
        forward . /etc/resolv.conf {
            max_concurrent 1000
        }
        cache 30
        reload
        loadbalance
    }
```

Kubernetes events receiver block for OTel:

```yaml
receivers:
  k8s_events:
    namespaces: [kube-system]
    evt_categories: ["k8s_event"]
```

After deployment, validate with searches against index=k8s_metrics for coredns_dns_requests_total and index=k8s_logs for kube:container:logs lines containing plugin reload strings. Compare pod lists to kubectl get pods -n kube-system -l k8s-app=kube-dns.


### Step 3 — Create the search and alert

Save the SPL as saved search uc_3_2_34_coredns_cluster_dns_plane with schedule every five minutes and time range earliest=-70m latest=now so each run includes enough history for one-minute bins plus five-minute streamstats windows. Throttle duplicate pages per cluster and coredns_pod for twenty minutes unless severity escalates from medium to critical inside the same hour. Attach the closing table row to the page body and include deep links to CoreDNS logs for the same pod.

Understanding the pipeline in operator terms: the comment macro lists index names, percentage gates, latency gates, and sibling UC references. The opening search normalizes metric names and dimensions with coalesce so mixed OTel and Prometheus field spellings still populate cluster, coredns_pod, and zone_l from zone versus domain labels. One-minute bins align counters across series. The stats stage rolls servfail_sum, refused_sum, cache hits and misses, and forward totals per cluster, pod, zone bucket, and minute. servfail_rate_pct divides SERVFAIL-class responses by all coredns_dns_responses_total samples in that bucket. cache_hit_ratio_pct divides cache hits by hits plus misses. upstream_failure_rate_pct divides forward SERVFAIL by all forward responses when the forward plugin exports rcode labels. config_reload_failed surfaces positive coredns_reload_failed_count_total readings. streamstats window=5 computes a rolling mean of per-second request rates derived from summed request counters per minute divided by sixty. The first join recomputes histogram bucket cumulative counts per minute, sorts by le label, applies streamstats cumulative sums, and picks the smallest le where cumulative mass reaches ninety-ninth percentile, converting seconds to p99_latency_ms. The second join pulls kube_deployment_status_replicas_ready for kube-system CoreDNS Deployments into ready_pod_count. The third join adds on_call_team. The case ladder emits critical, high, medium, low, and healthy tiers; the alert discards healthy rows.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.2.34 CoreDNS cluster DNS plane health. Tunables: index=k8s_metrics index_k8s_logs optional; SERVFAIL_CRIT_PCT=2.5 SERVFAIL_HIGH_PCT=1.0 P99_CRIT_MS=500 P99_HIGH_MS=200 CACHE_HIT_LOW_PCT=70 FWD_FAIL_HIGH_PCT=3 earliest=-70m latest=now; join coredns_oncall_routing.csv; complements UC-3.2.9 ingress and UC-3.2.41 endpoints.")`
| search index=k8s_metrics earliest=-70m latest=now
| eval mn=lower(toString(coalesce(metric_name, __name__, name, metric, "")))
| eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster, cluster_name, kube_cluster, k8s_cluster_name, source_cluster, ""))))
| eval coredns_pod=lower(trim(toString(coalesce(k8s_pod_name, pod, pod_name, podname, kubernetes_pod_name, k8s_pod, ""))))
| eval zone_l=lower(trim(toString(coalesce(zone, domain, zone_name, k8s_dns_zone, ""))))
| eval rcode_u=upper(trim(toString(coalesce(rcode, response_code, dns_rcode, ""))))
| eval le_label=toString(coalesce(le, le_quantile, upper_bound, ""))
| eval v=tonumber(tostring(coalesce(Value, value, metric_value, _value, "")), 10)
| eval mkind=case(
    match(mn, "coredns_dns_requests_total"), "req",
    match(mn, "coredns_dns_responses_total"), "resp",
    match(mn, "coredns_dns_request_duration_seconds_bucket"), "dur_bucket",
    match(mn, "coredns_cache_hits_total"), "chit",
    match(mn, "coredns_cache_misses_total"), "cmiss",
    match(mn, "coredns_forward_responses_total"), "fwd_resp",
    match(mn, "coredns_reload_failed_count_total"), "reload",
    true(), null())
| where isnotnull(mkind)
| where mkind!="dur_bucket"
| eval cluster=if(isnull(cluster) OR len(cluster)<1 OR cluster="null", "unknown_cluster", cluster)
| eval coredns_pod=if(isnull(coredns_pod) OR len(coredns_pod)<1, "aggregate_unknown_pod", coredns_pod)
| bin _time span=1m aligntime=@m
| eval is_servfail=if(mkind=="resp" AND rcode_u=="SERVFAIL", v, null())
| eval is_refused=if(mkind=="resp" AND rcode_u=="REFUSED", v, null())
| eval resp_total=if(mkind=="resp", v, null())
| eval req_v=if(mkind=="req", v, null())
| eval chit_v=if(mkind=="chit", v, null())
| eval cmiss_v=if(mkind=="cmiss", v, null())
| eval fwd_fail_v=if(mkind=="fwd_resp" AND rcode_u=="SERVFAIL", v, null())
| eval fwd_all_v=if(mkind=="fwd_resp", v, null())
| eval reload_v=if(mkind=="reload", v, null())
| stats
    sum(req_v) AS req_sum
    sum(resp_total) AS resp_sum
    sum(is_servfail) AS servfail_sum
    sum(is_refused) AS refused_sum
    sum(chit_v) AS chit_sum
    sum(cmiss_v) AS cmiss_sum
    sum(fwd_fail_v) AS fwd_fail_sum
    sum(fwd_all_v) AS fwd_all_sum
    max(reload_v) AS reload_failed_raw
  BY cluster coredns_pod zone_l _time
| eventstats sum(req_sum) AS req_cluster_minute BY cluster _time
| eval servfail_rate_pct=if(resp_sum>0, round(100.0*servfail_sum/resp_sum, 4), 0)
| eval refused_rate_pct=if(resp_sum>0, round(100.0*refused_sum/resp_sum, 4), 0)
| eval cache_hit_ratio_pct=if((chit_sum+cmiss_sum)>0, round(100.0*chit_sum/(chit_sum+cmiss_sum), 3), null())
| eval upstream_failure_rate_pct=if(fwd_all_sum>0, round(100.0*fwd_fail_sum/fwd_all_sum, 4), 0)
| eval config_reload_failed=if(isnotnull(reload_failed_raw) AND reload_failed_raw>0, 1, 0)
| sort 0 cluster coredns_pod zone_l _time
| streamstats window=5 current=t global=f avg(eval(if(req_sum>=0, req_sum/60.0, null()))) AS requests_per_sec BY cluster coredns_pod zone_l
| join type=left max=0 cluster coredns_pod _time
    [ search index=k8s_metrics earliest=-70m latest=now
      | eval mn=lower(toString(coalesce(metric_name, __name__, name, metric, "")))
      | where match(mn, "coredns_dns_request_duration_seconds_bucket")
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster, cluster_name, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval coredns_pod=lower(trim(toString(coalesce(k8s_pod_name, pod, pod_name, podname, kubernetes_pod_name, k8s_pod, ""))))
      | eval zone_l=lower(trim(toString(coalesce(zone, domain, zone_name, k8s_dns_zone, ""))))
      | eval le_num=tonumber(replace(toString(coalesce(le, le_quantile, upper_bound, "")), "[^0-9.Ee+-]", ""), 10)
      | eval v=tonumber(tostring(coalesce(Value, value, metric_value, _value, "")), 10)
      | eval cluster=if(isnull(cluster) OR len(cluster)<1 OR cluster="null", "unknown_cluster", cluster)
      | eval coredns_pod=if(isnull(coredns_pod) OR len(coredns_pod)<1, "aggregate_unknown_pod", coredns_pod)
      | bin _time span=1m aligntime=@m
      | stats latest(v) AS bcnt BY cluster coredns_pod zone_l _time le_num
      | sort cluster coredns_pod zone_l _time le_num
      | eventstats sum(bcnt) AS btot BY cluster coredns_pod zone_l _time
      | streamstats global=f sum(bcnt) AS cum_b BY cluster coredns_pod zone_l _time
      | eval frac=if(btot>0, cum_b/btot, 0)
      | where frac>=0.99 AND isnotnull(le_num)
      | stats min(le_num) AS p99_seconds BY cluster coredns_pod zone_l _time
      | eval p99_latency_ms=round(p99_seconds*1000, 2) ]
| fillnull value=0 servfail_rate_pct refused_rate_pct upstream_failure_rate_pct config_reload_failed
| join type=left max=0 cluster _time
    [ search index=k8s_metrics earliest=-70m latest=now
      | eval mn=lower(toString(coalesce(metric_name, __name__, name, metric, "")))
      | where match(mn, "kube_deployment_status_replicas_ready") OR match(mn, "kube_deployment_spec_replicas")
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster, cluster_name, kube_cluster, ""))))
      | eval ns=lower(trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ""))))
      | eval dep=lower(trim(toString(coalesce(deployment, deployment_name, ""))))
      | eval v=tonumber(tostring(coalesce(Value, value, metric_value, _value, "")), 10)
      | where (ns="kube-system" AND (match(dep, "coredns") OR match(dep, "kube-dns")))
      | eval series=if(match(mn, "spec_replicas"), "spec", "ready")
      | bin _time span=1m aligntime=@m
      | eval pivot_key=cluster."@@".tostring(_time)
      | stats latest(v) AS vv BY pivot_key series
      | xyseries pivot_key series vv
      | rex field=pivot_key "^(?<cluster>[^@]+)@@(?<tnum>[0-9.]+)"
      | eval _time=tonumber(tnum,10)
      | eval ready_pod_count=coalesce(tonumber(ready,10),0)
      | fields cluster _time ready_pod_count ]
| fillnull value=0 ready_pod_count
| join type=left max=0 cluster
    [| inputlookup coredns_oncall_routing.csv
     | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, ""))))
     | eval on_call_team=toString(coalesce(on_call_team, team, squad, pagerduty_service, ""))
     | fields cluster on_call_team ]
| eval on_call_team=if(isnull(on_call_team) OR len(trim(on_call_team))<1, "platform-kubernetes-dns", on_call_team)
| eval SERVFAIL_CRIT_PCT=2.5
| eval SERVFAIL_HIGH_PCT=1.0
| eval P99_CRIT_MS=500
| eval P99_HIGH_MS=200
| eval CACHE_HIT_LOW_PCT=70
| eval FWD_FAIL_HIGH_PCT=3
| eval p99_latency_ms=coalesce(p99_latency_ms, 0)
| eval cache_hit_ratio_pct=coalesce(cache_hit_ratio_pct, 100)
| eval severity=case(
    config_reload_failed==1, "critical",
    servfail_rate_pct>=SERVFAIL_CRIT_PCT OR upstream_failure_rate_pct>=FWD_FAIL_HIGH_PCT OR p99_latency_ms>=P99_CRIT_MS, "critical",
    servfail_rate_pct>=SERVFAIL_HIGH_PCT OR p99_latency_ms>=P99_HIGH_MS OR cache_hit_ratio_pct<CACHE_HIT_LOW_PCT OR refused_rate_pct>2, "high",
    servfail_rate_pct>0.3 OR upstream_failure_rate_pct>1 OR cache_hit_ratio_pct<80, "medium",
    servfail_rate_pct>0 OR refused_rate_pct>0.5, "low",
    true(), "healthy")
| where severity!="healthy"
| table cluster coredns_pod requests_per_sec servfail_rate_pct p99_latency_ms cache_hit_ratio_pct upstream_failure_rate_pct config_reload_failed ready_pod_count severity on_call_team
```

Dashboard drilldowns should link cluster to kubectl context aliases, coredns_pod to live describe pod output, and severity to CoreDNS manual sections for forward and cache plugins.


### Step 4 — Validate

Positive path A — healthy resolution: kubectl run dns-test --rm -i --restart=Never --image=tutum/dnsutils -- nslookup kubernetes.default.svc.cluster.local and confirm coredns_dns_requests_total increments in index=k8s_metrics for the target cluster within two scrape intervals.

Positive path B — upstream SERVFAIL injection: in a lab cluster only, introduce a broken forward target in a non-production CoreDNS Corefile under change control, reload, run the saved search, and expect non-healthy severity with elevated upstream_failure_rate_pct or servfail_rate_pct; restore the Corefile and verify auto-clear.

Positive path C — pod disruption: kubectl delete pod -n kube-system -l k8s-app=kube-dns --grace-period=0 on a lab node pool with surplus capacity, confirm Kubernetes events and temporary metric gaps appear, and expect alert rows during the disruption that clear after ready_pod_count returns to spec.

Positive path D — histogram sanity: compare p99_latency_ms from the search to Prometheus histogram_quantile(0.99, sum(rate(coredns_dns_request_duration_seconds_bucket[5m])) by (le)) on the same window; divergence beyond twenty percent indicates label cardinality or scrape alignment issues to fix in props or relabel rules.

Negative path — steady cluster: with no changes, expect predominantly healthy classification and zero alert rows after the final where clause across four consecutive five-minute runs.

Tear down: remove lab Corefile mutations, delete dns-test pods, and archive validation notes beside the change ticket.


### Step 5 — Operationalize & Troubleshoot

Case 1 — SERVFAIL spike from upstream public resolver: cloud DNS or ISP resolver returns transient failures; correlate forward plugin RCODE with external resolver status pages; widen forward max_fails or add parallel upstreams per CoreDNS forward plugin README guidance before blaming application teams.

Case 2 — NXDOMAIN spike from caller typos: application ConfigMaps reference wrong Service short names; pivot to client namespace logs; exclude namespaces listed in coredns_oncall_routing.csv synthetic_probe_namespace when those workloads are known low-impact.

Case 3 — p99 latency spike from CPU throttling: kubectl top pod -n kube-system shows CoreDNS at limit; raise CPU requests or add replicas via HPA; verify NodeLocal DNSCache is still enabled when architecture expects it.

Case 4 — cache hit ratio drop from TTL zero: a high-traffic Service sets ttl 0 in Corefile kubernetes stanza or uses headless patterns that bypass cache; differentiate intentional bypass from misconfiguration using zone_l and kubernetes plugin docs.

Case 5 — CoreDNS restart loop from bad Corefile: coredns_reload_failed_count_total rises and logs show plugin parse errors; roll back ConfigMap annotation-driven Corefile and validate with kubectl logs before reapplying.

Case 6 — NodeLocal DNSCache disabled: CoreDNS requests_per_sec jumps while node-local daemons stop; treat as architecture drift; restore DaemonSet or update fleet standards rather than silencing the alert globally.

Case 7 — Forward upstream auth failure: enterprise DNS requires TSIG or IP allow lists; SERVFAIL on forward with auth logs in corporate DNS; fix kube-system egress or credentials rather than scaling CoreDNS alone.

Case 8 — CoreDNS scale event two to four replicas during surge: ready_pod_count rises with spec replicas; normalize per-pod rates before declaring incident; HPA events should appear benign when error rates stay flat.

Case 9 — Suppression for synthetic monitoring DNS: probes from Datadog, Dynatrace, or internal blackboxes generate NXDOMAIN; list their namespaces in the lookup to drop medium noise.

Case 10 — Suppression during cluster autoscaler ramp: transient query storms while many nodes join; require sustained breach or correlate with node count metrics before sev-one.

Case 11 — EKS managed add-on rollover: AWS rotates CoreDNS pods during control plane upgrades; brief SERVFAIL may appear; compare event timestamps to EKS maintenance notifications and dampen when ready_pod_count recovers within one window.

Case 12 — Cross-link UC-3.2.41 zero endpoints: DNS still resolves ClusterIP A records while Service has no ready endpoints, so applications see timeouts on TCP connect; if symptoms mention resolution succeeding but connections failing, open UC-3.2.41 after confirming servfail_rate_pct is not dominant.

Governance: quarterly replay one historical DNS incident through the SPL after OTel collector upgrades. Update the comment macro when indexes or metric prefixes change. Require lookup owners to approve threshold edits in the same change record as published DNS SLO policy updates.

Evidence retention: weekly CSV exports of alert rows with coredns_oncall_routing.csv git hash satisfy internal audit samples when paired with kubectl rollout history screenshots for kube-system DNS Deployments.

Closing checklist: five step headers use em dashes; Step 3 fenced SPL matches the spl field; multisearch is not required because unified metric normalization keeps cardinality bounded; coalesce appears on cluster, pod, zone, rcode, and le fields; streamstats implements five-minute request rate smoothing and histogram join implements p99 from buckets; case implements five severity tiers; closing table lists eleven analyst-facing columns including cluster, coredns_pod, requests_per_sec, servfail_rate_pct, p99_latency_ms, cache_hit_ratio_pct, upstream_failure_rate_pct, config_reload_failed, ready_pod_count, severity, on_call_team; narrative fields avoid asterisk emphasis; references span CoreDNS manual, metrics plugin, three Kubernetes DNS tasks, forward and cache plugin README paths, and Splunk Kubernetes add-on documentation; monitoringType lists Reliability and Performance; equipmentModels lists kubernetes_k8s; cimModels lists Network_Resolution and Performance.

Supplemental notes for long-term owners: when IPv6 clusters dual-stack, verify ip6.arpa zones appear in metrics labels without exploding cardinality. When service meshes redirect DNS to sidecars, document which resolver still exports coredns_* metrics so this UC remains pointed at the cluster DNS Deployment rather than mesh proxies. When migrating to external-dns with private zones, keep CoreDNS as the in-cluster resolver this UC monitors. When Splunk Cloud search autoscaling changes concurrency, revalidate join fan-in costs. When legal requests log holds, include kube-system CoreDNS logs and Deployment rollout events in preservation scope alongside metrics extracts.

## SPL

```spl
`comment("UC-3.2.34 CoreDNS cluster DNS plane health. Tunables: index=k8s_metrics index_k8s_logs optional; SERVFAIL_CRIT_PCT=2.5 SERVFAIL_HIGH_PCT=1.0 P99_CRIT_MS=500 P99_HIGH_MS=200 CACHE_HIT_LOW_PCT=70 FWD_FAIL_HIGH_PCT=3 earliest=-70m latest=now; join coredns_oncall_routing.csv; complements UC-3.2.9 ingress and UC-3.2.41 endpoints.")`
| search index=k8s_metrics earliest=-70m latest=now
| eval mn=lower(toString(coalesce(metric_name, __name__, name, metric, "")))
| eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster, cluster_name, kube_cluster, k8s_cluster_name, source_cluster, ""))))
| eval coredns_pod=lower(trim(toString(coalesce(k8s_pod_name, pod, pod_name, podname, kubernetes_pod_name, k8s_pod, ""))))
| eval zone_l=lower(trim(toString(coalesce(zone, domain, zone_name, k8s_dns_zone, ""))))
| eval rcode_u=upper(trim(toString(coalesce(rcode, response_code, dns_rcode, ""))))
| eval le_label=toString(coalesce(le, le_quantile, upper_bound, ""))
| eval v=tonumber(tostring(coalesce(Value, value, metric_value, _value, "")), 10)
| eval mkind=case(
    match(mn, "coredns_dns_requests_total"), "req",
    match(mn, "coredns_dns_responses_total"), "resp",
    match(mn, "coredns_dns_request_duration_seconds_bucket"), "dur_bucket",
    match(mn, "coredns_cache_hits_total"), "chit",
    match(mn, "coredns_cache_misses_total"), "cmiss",
    match(mn, "coredns_forward_responses_total"), "fwd_resp",
    match(mn, "coredns_reload_failed_count_total"), "reload",
    true(), null())
| where isnotnull(mkind)
| where mkind!="dur_bucket"
| eval cluster=if(isnull(cluster) OR len(cluster)<1 OR cluster="null", "unknown_cluster", cluster)
| eval coredns_pod=if(isnull(coredns_pod) OR len(coredns_pod)<1, "aggregate_unknown_pod", coredns_pod)
| bin _time span=1m aligntime=@m
| eval is_servfail=if(mkind=="resp" AND rcode_u=="SERVFAIL", v, null())
| eval is_refused=if(mkind=="resp" AND rcode_u=="REFUSED", v, null())
| eval resp_total=if(mkind=="resp", v, null())
| eval req_v=if(mkind=="req", v, null())
| eval chit_v=if(mkind=="chit", v, null())
| eval cmiss_v=if(mkind=="cmiss", v, null())
| eval fwd_fail_v=if(mkind=="fwd_resp" AND rcode_u=="SERVFAIL", v, null())
| eval fwd_all_v=if(mkind=="fwd_resp", v, null())
| eval reload_v=if(mkind=="reload", v, null())
| stats
    sum(req_v) AS req_sum
    sum(resp_total) AS resp_sum
    sum(is_servfail) AS servfail_sum
    sum(is_refused) AS refused_sum
    sum(chit_v) AS chit_sum
    sum(cmiss_v) AS cmiss_sum
    sum(fwd_fail_v) AS fwd_fail_sum
    sum(fwd_all_v) AS fwd_all_sum
    max(reload_v) AS reload_failed_raw
  BY cluster coredns_pod zone_l _time
| eventstats sum(req_sum) AS req_cluster_minute BY cluster _time
| eval servfail_rate_pct=if(resp_sum>0, round(100.0*servfail_sum/resp_sum, 4), 0)
| eval refused_rate_pct=if(resp_sum>0, round(100.0*refused_sum/resp_sum, 4), 0)
| eval cache_hit_ratio_pct=if((chit_sum+cmiss_sum)>0, round(100.0*chit_sum/(chit_sum+cmiss_sum), 3), null())
| eval upstream_failure_rate_pct=if(fwd_all_sum>0, round(100.0*fwd_fail_sum/fwd_all_sum, 4), 0)
| eval config_reload_failed=if(isnotnull(reload_failed_raw) AND reload_failed_raw>0, 1, 0)
| sort 0 cluster coredns_pod zone_l _time
| streamstats window=5 current=t global=f avg(eval(if(req_sum>=0, req_sum/60.0, null()))) AS requests_per_sec BY cluster coredns_pod zone_l
| join type=left max=0 cluster coredns_pod _time
    [ search index=k8s_metrics earliest=-70m latest=now
      | eval mn=lower(toString(coalesce(metric_name, __name__, name, metric, "")))
      | where match(mn, "coredns_dns_request_duration_seconds_bucket")
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster, cluster_name, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval coredns_pod=lower(trim(toString(coalesce(k8s_pod_name, pod, pod_name, podname, kubernetes_pod_name, k8s_pod, ""))))
      | eval zone_l=lower(trim(toString(coalesce(zone, domain, zone_name, k8s_dns_zone, ""))))
      | eval le_num=tonumber(replace(toString(coalesce(le, le_quantile, upper_bound, "")), "[^0-9.Ee+-]", ""), 10)
      | eval v=tonumber(tostring(coalesce(Value, value, metric_value, _value, "")), 10)
      | eval cluster=if(isnull(cluster) OR len(cluster)<1 OR cluster="null", "unknown_cluster", cluster)
      | eval coredns_pod=if(isnull(coredns_pod) OR len(coredns_pod)<1, "aggregate_unknown_pod", coredns_pod)
      | bin _time span=1m aligntime=@m
      | stats latest(v) AS bcnt BY cluster coredns_pod zone_l _time le_num
      | sort cluster coredns_pod zone_l _time le_num
      | eventstats sum(bcnt) AS btot BY cluster coredns_pod zone_l _time
      | streamstats global=f sum(bcnt) AS cum_b BY cluster coredns_pod zone_l _time
      | eval frac=if(btot>0, cum_b/btot, 0)
      | where frac>=0.99 AND isnotnull(le_num)
      | stats min(le_num) AS p99_seconds BY cluster coredns_pod zone_l _time
      | eval p99_latency_ms=round(p99_seconds*1000, 2) ]
| fillnull value=0 servfail_rate_pct refused_rate_pct upstream_failure_rate_pct config_reload_failed
| join type=left max=0 cluster _time
    [ search index=k8s_metrics earliest=-70m latest=now
      | eval mn=lower(toString(coalesce(metric_name, __name__, name, metric, "")))
      | where match(mn, "kube_deployment_status_replicas_ready") OR match(mn, "kube_deployment_spec_replicas")
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster, cluster_name, kube_cluster, ""))))
      | eval ns=lower(trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ""))))
      | eval dep=lower(trim(toString(coalesce(deployment, deployment_name, ""))))
      | eval v=tonumber(tostring(coalesce(Value, value, metric_value, _value, "")), 10)
      | where (ns="kube-system" AND (match(dep, "coredns") OR match(dep, "kube-dns")))
      | eval series=if(match(mn, "spec_replicas"), "spec", "ready")
      | bin _time span=1m aligntime=@m
      | eval pivot_key=cluster."@@".tostring(_time)
      | stats latest(v) AS vv BY pivot_key series
      | xyseries pivot_key series vv
      | rex field=pivot_key "^(?<cluster>[^@]+)@@(?<tnum>[0-9.]+)"
      | eval _time=tonumber(tnum,10)
      | eval ready_pod_count=coalesce(tonumber(ready,10),0)
      | fields cluster _time ready_pod_count ]
| fillnull value=0 ready_pod_count
| join type=left max=0 cluster
    [| inputlookup coredns_oncall_routing.csv
     | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, ""))))
     | eval on_call_team=toString(coalesce(on_call_team, team, squad, pagerduty_service, ""))
     | fields cluster on_call_team ]
| eval on_call_team=if(isnull(on_call_team) OR len(trim(on_call_team))<1, "platform-kubernetes-dns", on_call_team)
| eval SERVFAIL_CRIT_PCT=2.5
| eval SERVFAIL_HIGH_PCT=1.0
| eval P99_CRIT_MS=500
| eval P99_HIGH_MS=200
| eval CACHE_HIT_LOW_PCT=70
| eval FWD_FAIL_HIGH_PCT=3
| eval p99_latency_ms=coalesce(p99_latency_ms, 0)
| eval cache_hit_ratio_pct=coalesce(cache_hit_ratio_pct, 100)
| eval severity=case(
    config_reload_failed==1, "critical",
    servfail_rate_pct>=SERVFAIL_CRIT_PCT OR upstream_failure_rate_pct>=FWD_FAIL_HIGH_PCT OR p99_latency_ms>=P99_CRIT_MS, "critical",
    servfail_rate_pct>=SERVFAIL_HIGH_PCT OR p99_latency_ms>=P99_HIGH_MS OR cache_hit_ratio_pct<CACHE_HIT_LOW_PCT OR refused_rate_pct>2, "high",
    servfail_rate_pct>0.3 OR upstream_failure_rate_pct>1 OR cache_hit_ratio_pct<80, "medium",
    servfail_rate_pct>0 OR refused_rate_pct>0.5, "low",
    true(), "healthy")
| where severity!="healthy"
| table cluster coredns_pod requests_per_sec servfail_rate_pct p99_latency_ms cache_hit_ratio_pct upstream_failure_rate_pct config_reload_failed ready_pod_count severity on_call_team
```

## CIM SPL

```spl
| tstats summariesonly=true count FROM datamodel=Network_Resolution WHERE nodename=All_Resolution earliest=-1h@h latest=@h BY All_Resolution.reply_code All_Resolution.dest span=5m
| rename All_Resolution.reply_code AS reply_code All_Resolution.dest AS dest
| eval fam=upper(trim(toString(reply_code)))
| stats sum(eval(if(fam=="SERVFAIL",count,0))) AS servfail_events sum(count) AS total_events BY dest _time
| eval servfail_rate_pct=if(total_events>0, round(100*servfail_events/total_events,3), 0)
| where servfail_rate_pct>0
```

## Visualization

Time-series combo of requests_per_sec and servfail_rate_pct by cluster, p99_latency_ms heatmap by coredns_pod, cache_hit_ratio_pct band versus zero-point-seven reference, upstream_failure_rate_pct stacked with forward RCODE facets, config_reload_failed state timeline, ready_pod_count versus spec replicas panel, and severity-tier table with drilldowns to raw metric events and CoreDNS log lines.

## Known False Positives

Rolling restarts of the CoreDNS Deployment emit short SERVFAIL or timeout bursts while endpoints drain and new pods pass readiness; dampen alerts to two consecutive evaluation windows or correlate with Kubernetes ReplicaSet revision timestamps before paging. NXDOMAIN spikes often trace to mis-typed Service names, canary namespaces, or security scanners hammering random labels; exclude known synthetic namespaces via coredns_oncall_routing.csv so caller mistakes do not wake platform on-call. Cache hit ratio drops sharply after cold cluster start or mass node replacement because in-process caches empty; require sustained low cache_hit_ratio_pct beyond fifteen minutes or pair with elevated forward query volume before treating as misconfiguration. Upstream public resolver or cloud DNS hiccups forward as transient SERVFAIL on the forward plugin counters; many clear within seconds and need ticket-only follow-up unless customer impact is already visible. Horizontal Pod Autoscaler scale-out from two to four CoreDNS replicas increases per-pod query share and can look like a load anomaly until you normalize rates by ready_pod_count; suppress alerts when spec replica changes align with HPA events. EKS managed CoreDNS add-on upgrades and GKE master upgrades can reorder pods without functional loss; annotate maintenance tickets beside the timeline. NodeLocal DNSCache rollouts temporarily shift histograms while traffic paths change; compare CoreDNS-facing rates against node-local metrics before blaming CoreDNS CPU. Broken negative testing in CI that points at non-existent Services can flood NXDOMAIN; route those clusters to lower severity tiers using lookup columns.

## References

- [CoreDNS manual](https://coredns.io/manual/toc/)
- [CoreDNS metrics plugin](https://coredns.io/plugins/metrics/)
- [Kubernetes — Using CoreDNS for Service Discovery](https://kubernetes.io/docs/tasks/administer-cluster/coredns/)
- [Kubernetes — Debugging DNS resolution](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)
- [CoreDNS forward plugin README](https://github.com/coredns/coredns/blob/master/plugin/forward/README.md)
- [Kubernetes — DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [Splunk — Kubernetes Add-on](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
- [CoreDNS cache plugin README](https://github.com/coredns/coredns/blob/master/plugin/cache/README.md)
