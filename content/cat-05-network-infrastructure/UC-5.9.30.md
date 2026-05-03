<!-- AUTO-GENERATED from UC-5.9.30.json — DO NOT EDIT -->

---
id: "5.9.30"
title: "SASE Secure Edge Performance"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.30 · SASE Secure Edge Performance

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Run &middot; **Status:** Verified

*We measure how fast the company's security gateway in the cloud processes our internet traffic, because when everything online feels slow, we need to know if it's the security checkpoint causing the delay or something else.*

---

## Description

Monitors the performance of SASE Secure Service Edge (SSE) / Secure Web Gateway (SWG) infrastructure from two perspectives: Endpoint Agents measure the user-to-proxy hop (local network to SASE PoP), and Enterprise Agent HTTP tests measure end-to-end performance through the SASE edge to backend applications. Together, these views isolate whether slowness is in the last mile to the proxy or in the proxy's processing and onward delivery.

## Value

SASE architectures route ALL web and SaaS traffic through a cloud-delivered security stack. When that stack degrades, it affects every application for every user — making SASE performance the single most impactful infrastructure metric in a SASE-first organization. Yet SASE vendors provide limited visibility into their own processing latency. ThousandEyes bridges this gap: the Endpoint Agent measures the network path TO the proxy, and the HTTP Server test measures the total trip THROUGH the proxy to the application. If the proxy hop is fast but the end-to-end test is slow, the SASE vendor's processing is the bottleneck. If the proxy hop is slow, the issue is between the user and the SASE PoP (ISP routing, DNS resolution to the wrong PoP). This data is essential for SASE vendor SLA enforcement and PoP selection optimization.

## Implementation

Combines Endpoint Agent proxy hop data with Enterprise Agent HTTP Server test data. Endpoint Agent data requires Endpoint Agents deployed on user devices. HTTP Server tests should be configured to access target applications THROUGH the SASE proxy.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.24 apply (Endpoint Agents deployed).
- All common prerequisites from UC-5.9.1 apply (for Enterprise Agent tests).
- **SASE/SSE infrastructure in use.** Users' web traffic must route through a cloud proxy (Zscaler, Cisco Umbrella SIG, Netskope, Palo Alto Prisma Access, etc.).
- **HTTP Server tests configured through SASE.** Create Agent-to-Server tests from Enterprise Agents that route through the SASE proxy to key applications.

### Step 1 — Configure data collection
Endpoint Agent proxy data: flows automatically when Endpoint Agents detect a proxy in the network path.

Verify proxy data:
```spl
index=thousandeyes_metrics thousandeyes.test.domain="endpoint" target.type="proxy" earliest=-24h
| stats dc(thousandeyes.source.agent.name) as endpoints count by server.address
| sort -endpoints
```

### Step 2 — Create the search
**Endpoint perspective (user-to-proxy hop):**
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="proxy"
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.score) as avg_score dc(thousandeyes.source.agent.name) as users by server.address
| eval avg_latency_ms=round(avg_latency*1000,1)
| sort avg_score
```

**End-to-end through SASE** (Enterprise Agent HTTP tests):
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="*SASE*" OR thousandeyes.test.name="*proxy*"
| stats avg(http.client.request.duration) as avg_ttfb avg(http.server.request.availability) as avg_avail by thousandeyes.test.name, server.address
| eval avg_ttfb_ms=round(avg_ttfb*1000,1)
| sort -avg_ttfb_ms
```

**SASE processing latency estimate:**
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="proxy" earliest=-4h
| stats avg(network.latency) as proxy_hop_latency by thousandeyes.source.agent.name
| eval proxy_hop_ms=round(proxy_hop_latency*1000,1)
| stats avg(proxy_hop_ms) as avg_proxy_hop_ms
| append [
  search `stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="*SASE*" earliest=-4h
  | stats avg(http.client.request.duration) as avg_e2e_s
  | eval avg_e2e_ms=round(avg_e2e_s*1000,1)
]
```
Compare `avg_proxy_hop_ms` with `avg_e2e_ms`. The difference includes SASE processing + server response time.

**Scheduling:** cron `*/15 * * * *`, time range `-30m to now`.

### Step 3 — Validate
(a) Verify proxy `server.address` values match your known SASE PoP IPs.
(b) Check that HTTP Server tests are actually routing through the SASE proxy (verify via path visualization or HTTP headers in the test results).

### Step 4 — Operationalize
**Dashboard** ("SASE Performance"):
- Proxy hop scoreboard: per-PoP, per-user.
- End-to-end performance through SASE.
- SASE processing latency estimate.

**Runbook** (owner: network security / SASE team):
1. High proxy hop latency → ISP peering issue to SASE PoP. Contact SASE vendor about PoP selection. Consider forcing users to a different PoP.
2. Low proxy hop latency but high end-to-end latency → SASE processing overhead. Check SASE vendor status page. Review TLS inspection policy (selective inspection reduces overhead).
3. Proxy loss > 0.5% → SASE PoP may be overloaded. Contact SASE vendor.

### Step 5 — Troubleshooting
- **No `target.type="proxy"` data** — Users may not be configured with a proxy, or the Endpoint Agent can't detect the proxy. Check system proxy settings (PAC file, WPAD, manual proxy).
- **Proxy data shows only one server.address** — All users may be routed to the same SASE PoP. This is normal for single-region deployments.
- See UC-5.9.24 Step 5 for general endpoint troubleshooting.

## SPL

```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="proxy"
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.score) as avg_score dc(thousandeyes.source.agent.name) as users by server.address
| eval avg_latency_ms=round(avg_latency*1000,1)
| sort avg_score
```

## Visualization

(1) Table: SASE proxy addresses sorted by score. (2) Timechart: proxy latency trending. (3) Comparison: user-to-proxy latency vs end-to-end application latency. (4) Distribution: user count per SASE PoP.

## Known False Positives

**Proxy bypass traffic.** Traffic that bypasses the SASE proxy (split-tunnel VPN direct access, proxy PAC exceptions) won't appear in `target.type="proxy"` data. This is expected — only proxied traffic is measured.

**SASE PoP selection changes.** Users may be routed to different SASE PoPs over time based on DNS resolution, Anycast routing, or SASE vendor load balancing. The `server.address` may change, making trend analysis per-PoP difficult. Group by SASE vendor name rather than individual PoP IPs.

**TLS inspection overhead.** SASE proxies performing TLS inspection add processing latency that increases with page complexity (more TLS connections = more inspection). This is expected behavior, not a bug — but it can be significant (20–100+ ms per request).

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes SASE monitoring](https://www.thousandeyes.com/solutions/sase)
