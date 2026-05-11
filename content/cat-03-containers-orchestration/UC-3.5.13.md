<!-- AUTO-GENERATED from UC-3.5.13.json — DO NOT EDIT -->

---
id: "3.5.13"
title: "eBPF Network Observability (Cilium Hubble)"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.5.13 · eBPF Network Observability (Cilium Hubble)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Performance, Fault &middot; **Wave:** Crawl &middot; **Status:** Verified

*Like an invisible camera system in every hallway that records who walks where and which doors they try, we monitor every network connection inside the cluster to catch blocked or suspicious traffic.*

---

## Description

Ingests Cilium Hubble **eBPF-level network flow logs** to provide kernel-level L3/L4/L7 visibility into every pod-to-pod, pod-to-service, and pod-to-external network connection — detecting **dropped flows** (network policy violations), **DNS resolution failures**, **unexpected communication paths** (lateral movement indicators), and **wide fan-out patterns** (service discovery storms) without sidecar injection overhead.

## Value

Traditional Kubernetes network monitoring requires service mesh sidecars (adding CPU/memory overhead and operational complexity) or packet capture (requiring privileged containers and massive storage). Cilium Hubble provides equivalent visibility at the kernel level via eBPF programs that intercept every network syscall with near-zero performance impact. Ingesting Hubble flows into Splunk gives security teams network-level evidence for incident investigation that application logs cannot provide: which pod talked to which external IP, which DNS queries were made, and which connections were blocked by network policy — all correlated with Kubernetes identity (namespace, pod, service) rather than raw IPs that change constantly.

## Implementation

Deploy Cilium as the Kubernetes CNI with Hubble enabled. Export flow logs to Splunk via the OTel Hubble receiver or Hubble Relay gRPC stream. Build two search variants: dropped flow analysis with policy violation classification and fan-out detection, and DNS flow analysis for resolution failure identification. Alert on BLOCKED or HIGH_DROP patterns and DNS failure rates exceeding 5%.

## Detailed Implementation

### Prerequisites
- **Cilium** 1.12+ deployed as the **Kubernetes CNI** (Container Network Interface) plugin. Cilium replaces traditional CNIs (Calico, Flannel) with an **eBPF-based datapath** that handles packet forwarding, network policy enforcement, load balancing, and observability at the **Linux kernel level**.
- **Hubble** enabled in the Cilium installation — Hubble is Cilium's built-in observability layer that captures **network flow logs** from the eBPF datapath. Enable via Helm: `hubble.enabled=true`, `hubble.relay.enabled=true`, `hubble.ui.enabled=true` (optional).
- **Hubble Relay** deployed as a **Deployment** in the `kube-system` namespace — Hubble Relay aggregates flow logs from all Cilium agent pods (which run as a **DaemonSet**) and exposes them via a **gRPC** stream on port **4245**.
- **Splunk Distribution of OTel Collector** with the **Hubble receiver** configured to connect to Hubble Relay's gRPC endpoint and export flow logs to **Splunk HEC** as **`sourcetype=cilium:hubble:flows`** in **`index=containers`**.
- **Cilium agent metrics**: configure the OTel Collector **Prometheus receiver** to scrape Cilium agent metrics from each node's agent pod on port **9962** (default). Key metrics:
  — `cilium_drop_count_total` (counter, labeled by reason and direction) — total packet drops by the eBPF datapath
  — `cilium_forward_count_total` (counter) — total forwarded packets
  — `cilium_policy_count` (gauge) — number of active **CiliumNetworkPolicies**
  — `cilium_endpoint_count` (gauge) — number of managed endpoints (pods)
  — `cilium_unreachable_nodes` (gauge) — nodes that the Cilium agent cannot reach via **tunnel** or **native routing**
- **Splunk HEC** token for **`index=containers`** with sourcetype routing for flow logs, metrics, and events.
- **License estimate**: Hubble flow log volume is proportional to network activity. A 200-pod cluster with moderate inter-service traffic generates approximately **50–500 MB/day** of flow logs. For high-traffic clusters, configure **flow sampling** in Hubble to reduce volume while maintaining statistical accuracy. DNS flow logs are typically 5–10% of total flow volume.
- **Kubernetes RBAC**: the OTel Collector needs access to the Hubble Relay **Service** in `kube-system`. The Cilium agent **ServiceAccount** needs extensive RBAC for CNI operation (configured by the Cilium Helm chart).
- Splunk RBAC: assign a **`network_analyst`** role with **`srchIndexesAllowed`** including `containers`.

### Step 1 — Configure data collection
(1) **Hubble flow log export**: configure the OTel Collector's **Hubble receiver** to connect to Hubble Relay:
— **Endpoint**: `hubble-relay.kube-system.svc:4245`
— **Buffer size**: 65536 (default) — increase for high-volume clusters
— **TLS**: configure mTLS if Hubble Relay requires client certificates

Key fields in each Hubble flow record:
— **`source.*`** (namespace, pod_name, identity, IP, port, labels) — the sender of the network flow
— **`destination.*`** (namespace, pod_name, identity, IP, port, labels, service) — the receiver
— **`verdict`** — **FORWARDED** (allowed by policy), **DROPPED** (blocked by policy or eBPF), **AUDIT** (logged but not enforced), **ERROR** (eBPF program error)
— **`drop_reason`** / **`drop_reason_desc`** — why the flow was dropped (e.g., **POLICY_DENIED**, **CT_TRUNCATED**, **INVALID_SOURCE_MAC**, **STALE_OR_UNROUTABLE**)
— **`traffic_direction`** — INGRESS or EGRESS relative to the reporting endpoint
— **`l7`** — Layer 7 protocol details (available when L7 visibility is enabled):
- **HTTP**: method, path, status code, headers
- **DNS**: query name, response code (NOERROR, NXDOMAIN, SERVFAIL), response IPs
- **Kafka**: topic, partition, API key

(2) **L7 visibility configuration**: by default, Hubble captures L3/L4 flows only. To enable **L7 visibility** (HTTP, DNS, Kafka), annotate pods or namespaces:
  `policy.cilium.io/proxy-visibility: "<Ingress/53/UDP/DNS>,<Egress/53/UDP/DNS>,<Ingress/80/TCP/HTTP>"`
  L7 visibility adds approximately **20% overhead** to flow log volume but provides protocol-aware details that L3/L4 flows cannot.

(3) **DNS-aware flow collection**: Cilium's eBPF programs intercept DNS traffic at the kernel level, providing **DNS query and response correlation** without a separate DNS monitoring solution. This is one of Hubble's most powerful features — it maps pod-level DNS queries to responses, detecting:
  — **NXDOMAIN** responses (querying non-existent domains — may indicate misconfiguration or data exfiltration attempts)
  — **SERVFAIL** responses (DNS server errors — may indicate CoreDNS overload)
  — **REFUSED** responses (query blocked by DNS policy)
  — **Unusual query patterns** (e.g., a pod querying hundreds of unique domains may indicate DNS tunneling)

(4) **CiliumNetworkPolicy snapshots**: collect **`sourcetype=cilium:policy`** for CiliumNetworkPolicy resources to correlate dropped flows with the specific policy rule that blocked them. The `cilium_policy_count` metric provides the total active policy count.

### Step 2 — Create the search and alert
The primary SPL aggregates Hubble flows in 5-minute windows per source pod and classifies them:
— **BLOCKED**: >50% of flows are dropped — the source pod is effectively network-isolated
— **HIGH_DROP**: >10% of flows are dropped — significant policy violations occurring
— **POLICY_HIT**: any dropped flows — normal policy enforcement
— **WIDE_FAN_OUT**: >50 unique destinations in 5 minutes — may indicate service discovery storms, port scanning, or lateral movement
— **NORMAL**: healthy traffic patterns

The DNS variant identifies pods with high **DNS failure rates** (>5% or >20 failures in 15 minutes). Common root causes:
— **NXDOMAIN**: querying services that do not exist (typos, deleted services, stale DNS cache)
— **SERVFAIL**: CoreDNS is overloaded or upstream DNS is failing
— **REFUSED**: DNS policy is blocking the query

Schedule the flow analysis every **5 minutes** and alert on BLOCKED or HIGH_DROP (may indicate misconfigured policies blocking legitimate traffic or active security incidents). Schedule the DNS analysis every **15 minutes** and alert on failure rates exceeding 5%.

### Step 3 — Validate
(a) Verify Hubble flow collection: `index=containers sourcetype="cilium:hubble:flows" earliest=-1h | stats count as total_flows, dc(source_namespace) as src_namespaces`. Should show flows from multiple namespaces.
(b) Test dropped flow detection: create a **CiliumNetworkPolicy** that blocks traffic from a test pod and attempt a connection: `kubectl exec test-pod -- curl blocked-service:80`. Verify the DROPPED flow appears: `index=containers sourcetype="cilium:hubble:flows" verdict="DROPPED" earliest=-5m`.
(c) Verify DNS flow collection (if L7 enabled): `index=containers sourcetype="cilium:hubble:flows" l7_type="DNS" earliest=-1h | stats count by dns_status`. Should show NOERROR and potentially NXDOMAIN entries.
(d) Verify Cilium metrics: `index=containers sourcetype="cilium:metrics" metric_name="cilium_drop_count_total" earliest=-1h | stats sum(metric_value) by reason`. Should show drop reasons.
(e) Cross-validate with Hubble CLI: `hubble observe --namespace <ns> --verdict DROPPED --last 5m` and compare with Splunk query results.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **single-value tiles** — total flows (last 1h), drop rate %, BLOCKED sources count, DNS failure rate %, active CiliumNetworkPolicies.
- Row B: **Sankey diagram** (or parallel coordinates) showing namespace-to-namespace traffic flows colored by verdict (green=forwarded, red=dropped) — immediately reveals unexpected communication paths.
- Row C: **dropped flow table** — src_ns, src_pod, dst_ns, direction, total_flows, dropped_flows, drop_pct, flow_flag, drop_reasons. Red rows for BLOCKED, amber for HIGH_DROP.
- Row D: **DNS failure table** — src_ns, src_pod, total_queries, failed_queries, failure_rate, unique_queries, response_codes.
- **Alerting**: BLOCKED → PagerDuty P2 (legitimate traffic may be denied); HIGH_DROP sustained → Slack `#network-security`; DNS failure rate > 10% → Slack `#platform-ops`; WIDE_FAN_OUT → Slack `#security-ops` (potential lateral movement).
- **Runbook**: (1) for BLOCKED: identify the CiliumNetworkPolicy causing drops: `kubectl get ciliumnetworkpolicies -n <ns> -o yaml`, (2) for DNS failures: check CoreDNS pod health and upstream DNS connectivity, (3) for WIDE_FAN_OUT: investigate the source pod for compromised workloads, (4) for policy changes: `hubble observe --verdict DROPPED --from-namespace <ns>` for real-time verification.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **network topology graph** where nodes represent namespaces and edges represent observed flows — dropped flows shown as dashed red lines, forwarded as solid green. Edge thickness proportional to flow volume.
- **Alert design**: include `src_ns`, `src_pod`, `dst_ns`, `direction`, `total_flows`, `dropped_flows`, `drop_pct`, `flow_flag`, and `drop_reasons` in the alert payload. For DNS alerts include `failure_rate`, `unique_queries`, and `response_codes`.
- **No flow logs appearing** — Hubble may not be enabled or Hubble Relay may not be deployed. Verify: `cilium hubble status` and `kubectl get pods -n kube-system -l k8s-app=hubble-relay`.
- **All flows show FORWARDED** — no CiliumNetworkPolicies are configured, so Cilium defaults to allow-all. This is expected in clusters without network policy enforcement but reduces the security value of flow monitoring.
- **Flow volume is overwhelming** — configure Hubble flow **sampling** to capture 1-in-N flows: set `hubble.eventQueueSize` and `hubble.eventBufferCapacity` in the Cilium Helm values. Alternatively, filter flows at the OTel Collector level to only export dropped flows and L7 flows.
- **DNS flows missing** — L7 visibility must be explicitly enabled for DNS. Add the proxy-visibility annotation to namespaces or pods where DNS monitoring is needed.

## SPL

```spl
`comment("--- Cilium Hubble Flow Analysis — Dropped Flows and Policy Violations ---")`
index=containers sourcetype="cilium:hubble:flows"
| eval src_ns=coalesce(source_namespace, source.namespace, "external")
| eval src_pod=coalesce(source_pod_name, source.pod_name, source_ip)
| eval dst_ns=coalesce(destination_namespace, destination.namespace, "external")
| eval dst_pod=coalesce(destination_pod_name, destination.pod_name, destination_ip)
| eval direction=coalesce(traffic_direction, direction, "unknown")
| eval flow_verdict=coalesce(verdict, flow_verdict)
| eval drop_reason_desc=coalesce(drop_reason_desc, drop_reason, "none")
| eval l7_type=coalesce(l7_type, l7.type, "L3_L4")
| bin _time span=5m
| stats count as total_flows,
    sum(eval(if(flow_verdict="DROPPED", 1, 0))) as dropped_flows,
    sum(eval(if(flow_verdict="FORWARDED", 1, 0))) as forwarded_flows,
    dc(dst_pod) as unique_destinations,
    dc(drop_reason_desc) as unique_drop_reasons,
    values(drop_reason_desc) as drop_reasons
    by _time, src_ns, src_pod, dst_ns, direction
| eval drop_pct=round(100 * dropped_flows / max(total_flows, 1), 2)
| eval flow_flag=case(
    drop_pct > 50, "BLOCKED",
    drop_pct > 10, "HIGH_DROP",
    dropped_flows > 0, "POLICY_HIT",
    unique_destinations > 50, "WIDE_FAN_OUT",
    1=1, "NORMAL")
| where flow_flag != "NORMAL"
| sort -dropped_flows
| head 50
| table _time src_ns src_pod dst_ns direction total_flows dropped_flows drop_pct unique_destinations flow_flag drop_reasons

`comment("--- DNS Flow Analysis — Resolution Failures and Anomalous Queries ---")`
index=containers sourcetype="cilium:hubble:flows" l7_type="DNS"
| eval src_ns=coalesce(source_namespace, source.namespace)
| eval src_pod=coalesce(source_pod_name, source.pod_name)
| eval dns_query=coalesce(l7.dns.query, dns_query, "unknown")
| eval dns_rcode=coalesce(l7.dns.rcode, dns_rcode, 0)
| eval dns_status=case(
    dns_rcode=0, "NOERROR",
    dns_rcode=2, "SERVFAIL",
    dns_rcode=3, "NXDOMAIN",
    dns_rcode=5, "REFUSED",
    1=1, "OTHER_".tostring(dns_rcode))
| bin _time span=15m
| stats count as total_queries,
    sum(eval(if(dns_rcode > 0, 1, 0))) as failed_queries,
    dc(dns_query) as unique_queries,
    values(dns_status) as response_codes
    by _time, src_ns, src_pod
| eval failure_rate=round(100 * failed_queries / max(total_queries, 1), 2)
| where failure_rate > 5 OR failed_queries > 20
| sort -failed_queries
| table _time src_ns src_pod total_queries failed_queries failure_rate unique_queries response_codes
```

## Visualization

Sankey diagram of namespace-to-namespace flows, dropped flow table with reasons, DNS failure trend line, network graph of pod communication, single-value tiles (drop rate, blocked sources, DNS failure rate).

## Known False Positives

**policy_rollout_transition** — When deploying new CiliumNetworkPolicies, there is a brief transition period where the eBPF datapath is updated across nodes. During this window, some flows may be dropped by the new policy before applications have been updated to comply. These transient drops resolve once the rollout completes. Correlate drop spikes with policy change timestamps.

**identity_allocation_delay** — Cilium assigns security identities to pods based on labels. When a new pod starts, there is a brief delay before the identity is allocated and propagated to all nodes. Flows from the pod during this window may be dropped with POLICY_DENIED even though the pod should be allowed. These resolve within seconds of identity allocation.

**node_to_node_tunnel_flap** — In overlay networking mode (VXLAN or Geneve), Cilium establishes tunnels between nodes. Tunnel flaps cause temporary packet drops that appear as DROPPED flows with reason CT_TRUNCATED or STALE_OR_UNROUTABLE. These are infrastructure-level events, not application policy violations.

**dns_negative_cache** — Applications that query non-existent services generate NXDOMAIN responses that are cached by CoreDNS. The initial query produces a flow with dns_rcode=3, but subsequent queries may be answered from cache without generating a Hubble flow. The DNS failure rate may undercount persistent resolution issues that are being served from negative cache.

**hubble_ring_buffer_overflow** — Under extreme network load, the Hubble ring buffer on individual Cilium agents may overflow, causing flow log drops. The dropped flows are not the same as policy-dropped packets — they are observability gaps. Monitor `cilium_hubble_events_lost_total` to detect ring buffer overflows.

**external_traffic_identity** — Traffic from external sources (outside the cluster) appears with `source_identity=world` and no namespace/pod information. Dropped flows from external sources may represent legitimate firewall behavior (blocking inbound traffic to internal services) rather than policy violations.

## References

- [Cilium — Hubble Introduction](https://docs.cilium.io/en/stable/observability/hubble/)
- [Cilium — Hubble Metrics](https://docs.cilium.io/en/stable/observability/metrics/)
- [Cilium — Network Policy](https://docs.cilium.io/en/stable/security/policy/)
- [Splunk Distribution of OpenTelemetry Collector](https://docs.splunk.com/observability/en/gdi/opentelemetry/opentelemetry.html)
