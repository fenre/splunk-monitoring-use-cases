<!-- AUTO-GENERATED from UC-5.20.58.json — DO NOT EDIT -->

---
id: "5.20.58"
title: "Dual-Stack Parity Monitoring — IPv4 vs IPv6 Service Reachability"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.20.58 · Dual-Stack Parity Monitoring — IPv4 vs IPv6 Service Reachability

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*When we have both old roads and new roads going to the same places, we want them to be equally good. We check that the new road is just as fast and reliable as the old road. If the new road has potholes or takes twice as long, we need to fix it — otherwise why did we build it? This check tells us if our new road system (IPv6) is truly as good as the old one (IPv4).*

---

## Description

Compares IPv4 and IPv6 service reachability, latency, and success rates for dual-stack services to ensure protocol parity. In a properly deployed dual-stack environment, users should receive equivalent service quality regardless of which protocol is selected. Parity violations — where IPv6 is significantly slower, less reliable, or unreachable compared to IPv4 — indicate infrastructure issues that need investigation. This is the holistic 'are we doing IPv6 right?' metric.

## Value

Dual-stack parity is the ultimate measure of IPv6 deployment quality. If IPv6 is reachable but 200ms slower than IPv4, Happy Eyeballs will always prefer IPv4, and the IPv6 deployment is effectively wasted. If IPv6 has lower success rates, users experience intermittent failures. Parity monitoring provides the executive-level summary: 'Is our IPv6 as good as our IPv4?' This drives investment decisions — poor parity means the IPv6 deployment needs optimisation before it can carry production traffic.

## Implementation

Use synthetic monitoring (ITSI Synthetic Monitoring, ThousandEyes, or custom probes) to test dual-stack services over both IPv4 and IPv6. Compare reachability, latency, and throughput. Alert on parity violations.

## Detailed Implementation

### Prerequisites
- Dual-stack services with both A and AAAA DNS records.
- Synthetic monitoring capability (ITSI Synthetic Monitoring, ThousandEyes, or scripted probes) that can test both IPv4 and IPv6 endpoints.
- Baseline of expected latency for each service and protocol.

### Step 1 — Configure data collection

**Option A — ITSI Synthetic Monitoring (recommended):**
Create synthetic tests for each dual-stack service, testing both IPv4 and IPv6 endpoints:
```
Test 1: HTTPS to www.example.com via IPv4 (force -4 flag)
Test 2: HTTPS to www.example.com via IPv6 (force -6 flag)
```

**Option B — Scripted probes:**
Deploy a cron-based script that tests dual-stack services:
```bash
#!/bin/bash
for service in www.example.com api.example.com; do
  v4_time=$(curl -4 -s -o /dev/null -w "%{time_total}" https://${service})
  v6_time=$(curl -6 -s -o /dev/null -w "%{time_total}" https://${service})
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) service=${service} v4_latency=${v4_time} v6_latency=${v6_time}"
done | logger -t dualstack-probe
```

**Option C — NetFlow comparison:**
Compare TCP round-trip times from NetFlow data for IPv4 vs IPv6 flows to the same destination.

**Verification:**
```spl
index=itsi sourcetype="itsi:synthetic" earliest=-24h
| stats count by service_name
```

### Step 2 — Create the search and alert

**Service parity comparison:**
```spl
index=itsi sourcetype="itsi:synthetic" earliest=-24h
| eval protocol=if(match(dest_ip, ":"), "IPv6", "IPv4")
| chart avg(response_time) as avg_ms p95(response_time) as p95_ms avg(eval(if(status="success", 100, 0))) as success_pct by service_name, protocol
| eval ipv4_latency=if(protocol="IPv4", avg_ms, null())
| eval ipv6_latency=if(protocol="IPv6", avg_ms, null())
| stats first(ipv4_latency) as v4_ms first(ipv6_latency) as v6_ms first(eval(if(protocol="IPv4", success_pct, null()))) as v4_success first(eval(if(protocol="IPv6", success_pct, null()))) as v6_success by service_name
| eval latency_diff_pct=round(abs(v6_ms - v4_ms) / v4_ms * 100, 1)
| eval success_diff=round(v4_success - v6_success, 1)
| eval parity_status=case(
    v6_success < 95, "CRITICAL — IPv6 below 95% availability",
    success_diff > 5, "WARNING — IPv6 success rate lower than IPv4",
    latency_diff_pct > 30, "WARNING — IPv6 latency >30% worse than IPv4",
    1=1, "OK — parity maintained")
| table service_name, v4_ms, v6_ms, latency_diff_pct, v4_success, v6_success, success_diff, parity_status
| sort parity_status
```

**Parity violation alert:**
```spl
<parity comparison search above>
| where parity_status != "OK — parity maintained"
| eval alert="Dual-stack parity violation: " . service_name . " — " . parity_status
```

### Step 3 — Validate
(a) **Known good service.** Test a service where IPv4 and IPv6 are both healthy. Verify parity status is OK.

(b) **Induced latency.** Add a traffic shaping rule to add 100ms to IPv6 traffic for a test service. Verify the parity alert fires.

(c) **IPv6 failure.** Block IPv6 to a test service. Verify the availability parity alert fires.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Dual-Stack Service Parity"):
- Row 1 — Gauge: percentage of services at parity (OK status).
- Row 2 — Table: per-service parity comparison (IPv4 vs IPv6 latency, success rate).
- Row 3 — Dual timechart: IPv4 vs IPv6 response time for top services over 7 days.
- Row 4 — Alert panel: services with parity violations.

**Scheduling:** Parity comparison every 15 minutes. Alert on violation. Weekly parity report for management.

**Runbook:**
1. IPv6 latency higher: check routing path for IPv6 (traceroute6). Look for suboptimal paths, additional hops, or tunnel encapsulation adding overhead.
2. IPv6 success rate lower: check firewall rules for IPv6 ACLs. Check load balancer IPv6 backend health. Check server IPv6 socket binding.
3. IPv6 unreachable: check AAAA record, routing to the server, firewall rules, server IPv6 configuration.

### Step 5 — Troubleshooting

- **CDN and anycast** — Many services use CDN with anycast. IPv4 and IPv6 may route to different PoPs with inherently different latencies. Establish per-protocol baselines rather than requiring identical latency.

- **TLS negotiation differences** — IPv6 connections may negotiate different TLS versions or cipher suites if the server or intermediary is configured differently for IPv4 vs IPv6. Check TLS handshake details.

- **MTU impact on first-byte latency** — IPv6 has a minimum MTU of 1280 bytes. If PMTUD is not working properly (UC-5.20.38), the TLS handshake may require multiple round trips for certificate exchange, increasing latency specifically for IPv6.

## SPL

```spl
index=itsi sourcetype="itsi:synthetic" earliest=-24h
| eval protocol=case(
    match(dest_ip, ":"), "IPv6",
    match(dest_ip, "^[0-9]+\."), "IPv4",
    1=1, "unknown")
| stats avg(response_time) as avg_latency_ms perc95(response_time) as p95_latency_ms count(eval(status="success")) as successes count(eval(status="failure")) as failures count as total by service_name, protocol
| eval success_rate=round(successes / total * 100, 2)
| eventstats avg(avg_latency_ms) as overall_latency by service_name
| eval latency_parity=round(abs(avg_latency_ms - overall_latency) / overall_latency * 100, 1)
| eval status=case(
    success_rate < 95, "FAILED — " . protocol . " below 95% success rate",
    latency_parity > 50, "DEGRADED — " . protocol . " latency >50% different from parity",
    1=1, "OK")
| table service_name, protocol, avg_latency_ms, p95_latency_ms, success_rate, latency_parity, status
```

## Visualization

(1) Comparison table: per-service IPv4 vs IPv6 metrics. (2) Dual timechart: IPv4 vs IPv6 latency for top services. (3) Gauge: overall parity score (% of services with <10% latency difference). (4) Heatmap: service × protocol status matrix.

## Known False Positives

**Different CDN PoPs.** CDN providers may serve IPv4 and IPv6 from different Points of Presence, resulting in different latencies. This is a CDN routing decision, not a network problem.

**Transit provider differences.** IPv4 and IPv6 traffic may traverse different transit providers with different latency characteristics. This is an expected consequence of separate IPv4/IPv6 peering relationships.

**Synthetic monitoring probe location.** If the synthetic probe is located in a network segment with IPv6 issues, the parity measurement reflects the probe's network, not the service's IPv6 quality.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.2 — dual-stack service parity)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 8305 — Happy Eyeballs Version 2 (client-side protocol selection based on performance)](https://www.rfc-editor.org/rfc/rfc8305)
