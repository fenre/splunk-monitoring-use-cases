<!-- AUTO-GENERATED from UC-5.9.31.json — DO NOT EDIT -->

---
id: "5.9.31"
title: "Multi-Cloud Network Performance"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.31 · Multi-Cloud Network Performance

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Run &middot; **Status:** Verified

*We check how fast data travels between our different cloud services (like Amazon and Microsoft), because if the highway between them is congested, our applications that span both clouds will be slow.*

---

## Description

Monitors network performance between cloud providers (AWS ↔ Azure ↔ GCP) and between cloud and on-premises environments using ThousandEyes Enterprise Agents deployed within each cloud environment. Tracks cross-cloud latency, loss, and jitter to ensure multi-cloud interconnections meet application requirements.

## Value

Multi-cloud architectures create invisible network dependencies between cloud providers. An application frontend in AWS calling a microservice in Azure traverses multiple provider networks, peering points, and backbone segments — any of which can degrade. Cloud provider native monitoring (CloudWatch, Azure Monitor, Stackdriver) only sees within their own boundary. ThousandEyes Enterprise Agents deployed in each cloud provide end-to-end cross-cloud visibility. This UC detects: inter-cloud peering degradation (AWS–Azure Express Route vs internet path), cloud region connectivity issues, and cross-cloud latency that violates application SLAs. Without this visibility, teams waste hours investigating application timeouts that are actually cross-cloud network latency issues.

## Implementation

Deploy Enterprise Agents in each cloud provider (as VMs, containers, or serverless). Create Agent-to-Server tests targeting key services in other clouds. Use consistent naming conventions for cloud identification.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **Enterprise Agents deployed in each cloud environment.** Deploy agents as VMs (AWS EC2 t3.medium+, Azure D2s_v3+, GCP e2-medium+) or containers (ECS Fargate, AKS, GKE). ThousandEyes provides cloud-specific deployment guides. Each agent must have outbound HTTPS (port 443) to ThousandEyes SaaS. Do NOT put agents behind NAT gateways that share IPs with production traffic.
  - **AWS:** Deploy in each relevant VPC/region. If you use Transit Gateway, deploy agents in the Transit VPC as well.
  - **Azure:** Deploy in each VNet/region. If you use Azure Virtual WAN, deploy in hub VNets.
  - **GCP:** Deploy in each VPC/region. If you use Shared VPC, deploy in the host project.
- **Cross-cloud Agent-to-Server tests configured.** For EACH cloud-to-cloud path direction, create a test. Naming convention is critical: `<SrcCloud>-<SrcRegion>-to-<DstCloud>-<DstRegion>` (e.g., `AWS-us-east-1-to-Azure-westeurope`). This enables SPL to extract source/destination clouds via `rex`.
  - **Test pairs to create (minimum):** For 3 clouds × 2 regions each = 6 agents. You need tests from each to every other. Focus on paths your applications actually use. A full mesh is ideal but costly.
  - **Targets:** Use a stable IP or hostname in the destination cloud. A small web server or health-check endpoint works well. Avoid targets behind load balancers that change IPs.
  - **Protocol:** TCP on the application port (e.g., 443) is more representative than ICMP. Cloud providers may deprioritize ICMP, causing misleadingly high latency readings.
  - **Interval:** 2 minutes for production paths; 5 minutes for secondary paths.
- **Security group / firewall rules.** Agent VMs need ICMP + TCP outbound to test targets. Target hosts need inbound rules allowing the agent IPs. In multi-cloud, this means cross-cloud security group rules.
- **Baseline cross-cloud latency documented.** Physics-based minimums for common paths:
  - Same-region cross-cloud (AWS us-east-1 ↔ Azure eastus): 1–5 ms (both in Northern Virginia).
  - US-East ↔ US-West: 60–80 ms.
  - US ↔ Europe: 80–120 ms.
  - US ↔ Asia-Pacific: 150–250 ms.
  - Cross-cloud via peering (e.g., AWS ↔ Azure via Microsoft/Amazon direct peering): typically 1–3 ms lower than internet transit.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
Cross-cloud Agent-to-Server test metrics flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify all cross-cloud tests are reporting data:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="agent-to-server" (thousandeyes.test.name="*AWS*" OR thousandeyes.test.name="*Azure*" OR thousandeyes.test.name="*GCP*") earliest=-1h
| stats count dc(thousandeyes.source.agent.name) as agents values(thousandeyes.source.agent.name) as agent_list by thousandeyes.test.name
| sort thousandeyes.test.name
```
Each test should show data. If a test shows 0 events, the agent is down or the target is unreachable.

**Metric reference for cross-cloud monitoring:**
- `network.latency` — round-trip time in SECONDS (OTel v2). Multiply by 1000 for ms. For cross-cloud paths, this includes: agent → cloud egress → internet/peering → cloud ingress → target, and back. Every segment adds latency.
- `network.loss` — packet loss as a PERCENTAGE (0–100). For cross-cloud paths, even 0.1% loss can cause TCP retransmissions that dramatically impact application performance.
- `network.jitter` — variation in latency in MILLISECONDS. Cross-cloud paths over the internet typically show higher jitter (5–15 ms) than dedicated interconnects (1–3 ms).

### Step 2 — Create the search and alert
**Cross-cloud performance overview (primary view):**
```spl
`stream_index` thousandeyes.test.type="agent-to-server" (thousandeyes.test.name="*AWS*" OR thousandeyes.test.name="*Azure*" OR thousandeyes.test.name="*GCP*")
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address, thousandeyes.test.name
| eval avg_latency_ms=round(avg_latency*1000,1), avg_loss_pct=round(avg_loss,2), avg_jitter_ms=round(avg_jitter,1)
| sort -avg_latency_ms
```

**Understanding this SPL**

`thousandeyes.test.name="*AWS*" OR *Azure*" OR *GCP*"` — filters to cross-cloud tests based on naming convention. If your naming convention is different (e.g., `cloud-` prefix), adjust accordingly.

`stats avg(network.latency) as avg_latency` — average round-trip time across all data points. Use `p95()` for tail latency which matters more for user experience.

`by thousandeyes.source.agent.name, server.address, thousandeyes.test.name` — one row per agent-to-target path. This shows every cross-cloud path individually.

`eval avg_latency_ms=round(avg_latency*1000,1)` — converts seconds to milliseconds for human readability.

**Cross-cloud latency matrix (source cloud × destination cloud):**
```spl
`stream_index` thousandeyes.test.type="agent-to-server" (thousandeyes.test.name="*AWS*" OR thousandeyes.test.name="*Azure*" OR thousandeyes.test.name="*GCP*") earliest=-24h
| rex field=thousandeyes.test.name "(?<src_cloud>AWS|Azure|GCP)-(?<src_region>[a-z0-9-]+)-to-(?<dst_cloud>AWS|Azure|GCP)-(?<dst_region>[a-z0-9-]+)"
| stats avg(network.latency) as avg_latency by src_cloud, dst_cloud
| eval avg_latency_ms=round(avg_latency*1000,1)
| xyseries src_cloud dst_cloud avg_latency_ms
```
This creates a matrix: rows = source cloud, columns = destination cloud, values = average latency in ms. Display as a heatmap. Diagonal (same-cloud) should be lowest. Off-diagonal cells show cross-cloud latency.

**Cross-cloud region-level detail:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server" (thousandeyes.test.name="*AWS*" OR thousandeyes.test.name="*Azure*" OR thousandeyes.test.name="*GCP*") earliest=-24h
| rex field=thousandeyes.test.name "(?<src_cloud>AWS|Azure|GCP)-(?<src_region>[a-z0-9-]+)-to-(?<dst_cloud>AWS|Azure|GCP)-(?<dst_region>[a-z0-9-]+)"
| eval path=src_cloud."-".src_region." → ".dst_cloud."-".dst_region
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss p95(network.latency) as p95_latency by path
| eval avg_ms=round(avg_latency*1000,1), p95_ms=round(p95_latency*1000,1), loss_pct=round(avg_loss,2)
| table path, avg_ms, p95_ms, loss_pct
| sort -avg_ms
```

**Cross-cloud latency trending (detect degradation):**
```spl
`stream_index` thousandeyes.test.type="agent-to-server" (thousandeyes.test.name="*AWS*" OR thousandeyes.test.name="*Azure*" OR thousandeyes.test.name="*GCP*") earliest=-7d
| rex field=thousandeyes.test.name "(?<src_cloud>AWS|Azure|GCP).*to.*(?<dst_cloud>AWS|Azure|GCP)"
| eval path=src_cloud." → ".dst_cloud
| timechart span=1h avg(network.latency) as avg_latency_s by path
```

**Scheduling:** cron `*/15 * * * *`, time range `-30m to now`. Alert on latency > 2× baseline or loss > 0.5% for any cross-cloud path. Throttle by `thousandeyes.test.name` for 1 hour.

### Step 3 — Validate
(a) **Verify each cross-cloud path has data.** Run the verification query from Step 1. Any test with 0 events means the agent is down or the target is unreachable. Check agent status in the ThousandEyes UI.

(b) **Cross-reference with traceroute.** SSH into a cloud VM and run `traceroute` (or `mtr`) to the target in another cloud. Compare hop count and latency with ThousandEyes path visualization data. They should be similar. If ThousandEyes shows significantly higher latency, the agent VM may be resource-constrained.

(c) **Security group / firewall validation.** Ensure test targets accept ICMP and TCP from the agent IPs. Test from the agent VM directly: `ping <target>`, `curl https://<target>`. If `ping` works but the ThousandEyes test shows loss, the test may be using TCP on a blocked port.

(d) **Baseline comparison.** Compare measured latency with physics-based minimums (see Prerequisites). If measured latency is significantly higher than the physics-based minimum, there is room for path optimization (dedicated interconnect, better peering).

(e) **Agent VM sizing.** Verify agent VMs have at least 2 vCPU and 2 GB RAM. Under-provisioned agents produce noisy, inconsistent results — especially when running many tests simultaneously.

### Step 4 — Operationalize
**Dashboard** ("Multi-Cloud Network Health" — designed for cloud networking and platform engineering):
- Row 1 — Cross-cloud matrix heatmap: source cloud × destination cloud, colour-coded by avg latency. Green < 50 ms, yellow 50–100 ms, red > 100 ms (adjust thresholds per geography).
- Row 2 — Region-level detail table: path | avg latency (ms) | p95 latency (ms) | loss (%). Sorted by worst latency. Drilldown to path visualization.
- Row 3 — Latency trending: timechart showing cross-cloud latency over 7 days. Reveals temporal patterns (congestion during business hours, maintenance windows).
- Row 4 — Interconnect ROI calculator: for paths currently using internet transit, show current latency vs estimated dedicated interconnect latency. Helps justify dedicated interconnect investment.

**Alerting (tiered):**
- Cross-cloud latency > 2× established baseline for a path → low-urgency Slack/Teams notification to `#cloud-networking`.
- Cross-cloud loss > 0.5% on a production path → medium-urgency notification. Even low loss causes TCP retransmissions.
- Cross-cloud latency spike > 3× baseline across ALL paths from one cloud → high-urgency notification. Likely a cloud provider peering issue or regional outage.

**Runbook** (owner: cloud networking / platform engineering):
1. **Cross-cloud latency spike on a single path.** (a) Check if the target cloud provider reports issues on their status page. (b) Use ThousandEyes path visualization (UC-5.9.9) to see which network segment added latency: cloud egress? internet peering? cloud ingress? (c) If the peering point changed (visible in path viz), route may have shifted to a less optimal path.
2. **Persistent high latency on a production-critical path.** (a) Evaluate dedicated interconnect: AWS Direct Connect, Azure ExpressRoute, GCP Cloud Interconnect. These provide private connectivity with lower and more consistent latency. (b) Calculate ROI: multiply latency reduction by number of API calls per second to get aggregate time savings.
3. **Loss on cross-cloud path.** (a) Check security group rules and NACLs on both sides. A recent security change may have introduced drops. (b) Check if the path traverses a NAT gateway or firewall with connection limits. (c) Check cloud provider network limits (bandwidth throttling on VM types).
4. **All cross-cloud paths from one cloud degraded.** Cloud provider issue. (a) Check provider status page. (b) Consider failover to an alternate region if your architecture supports it.

### Step 5 — Troubleshooting

- **No data from cloud agents** — Enterprise Agent VMs need outbound HTTPS (port 443) to `*.thousandeyes.com`. Cloud security groups and NACLs may block this. Check agent status in ThousandEyes UI → **Cloud & Enterprise Agents → Agent Settings**.

- **`rex` field extraction fails (src_cloud/dst_cloud empty)** — The naming convention doesn't match the regex. Verify test names follow `<Cloud>-<region>-to-<Cloud>-<region>` format. Adjust the `rex` pattern if your convention differs.

- **Latency seems too high for same-region cross-cloud** — If AWS us-east-1 to Azure eastus shows > 10 ms, check: (a) Are both endpoints actually in the same metro area? (b) Is the traffic going through a NAT gateway or proxy? (c) Is the test using ICMP? Switch to TCP — some clouds deprioritize ICMP.

- **Inconsistent results (high jitter on measurements)** — Agent VM is likely resource-constrained or sharing resources with noisy neighbors. Use dedicated/reserved instances for agent VMs. Avoid burstable instance types (t3, B-series).

- **All common troubleshooting** — See UC-5.9.1 Step 5 for general app troubleshooting.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server" thousandeyes.test.name="*cloud*" OR thousandeyes.test.name="*AWS*" OR thousandeyes.test.name="*Azure*" OR thousandeyes.test.name="*GCP*"
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address, thousandeyes.test.name
| eval avg_latency_ms=round(avg_latency*1000,1)
| sort -avg_latency_ms
```

## Visualization

(1) Matrix/heatmap: source cloud × destination cloud, showing average latency. (2) Table: cross-cloud paths sorted by latency. (3) Timechart: latency trending per cross-cloud path. (4) Single values: worst cross-cloud latency, highest cross-cloud loss.

## Known False Positives

**Geographic latency.** Cross-cloud paths between distant regions (US-East to Asia-Pacific) inherently have high latency (120–250 ms). This is physics, not a problem. Compare against baseline for each specific path.

**Cloud provider maintenance.** Cloud providers perform network maintenance that can temporarily increase latency or cause brief packet loss. Check provider status pages.

**Test agent resource contention.** Enterprise Agents on undersized VMs may produce inconsistent results during periods of co-tenant resource contention. Use dedicated VM sizes recommended by ThousandEyes.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes cloud monitoring](https://www.thousandeyes.com/solutions/cloud)
