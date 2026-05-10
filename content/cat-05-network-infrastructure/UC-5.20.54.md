<!-- AUTO-GENERATED from UC-5.20.54.json — DO NOT EDIT -->

---
id: "5.20.54"
title: "Dual-Stack Happy Eyeballs Connection Timing and Fallback Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-5.20.54 · Dual-Stack Happy Eyeballs Connection Timing and Fallback Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Performance, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*Modern devices are smart — when they want to visit a website, they try both the new road (IPv6) and the old road (IPv4) at the same time, and take whichever one connects first. If the new road is broken, they silently switch to the old road with barely a pause. We measure how often devices actually use the new road versus the old road.*

---

## Description

Monitors dual-stack Happy Eyeballs (RFC 8305) connection behaviour to detect IPv6 connectivity problems that are masked by automatic IPv4 fallback. Happy Eyeballs is designed to be invisible to users — when IPv6 is broken, applications silently fall back to IPv4 with only a 250ms delay. While this is great for user experience, it creates an observability gap where IPv6 failures go undetected. This use case closes that gap by measuring the IPv6 preference rate (what percentage of dual-stack connections use IPv6), the fallback rate, and the connection time penalty.

## Value

Happy Eyeballs masks IPv6 failures so effectively that many organisations are unaware their IPv6 is broken for weeks or months. Users experience a barely noticeable 250ms delay on initial connections, which is typically attributed to 'the network being slow.' By measuring the IPv6 preference rate on dual-stack services, this use case reveals the true IPv6 connectivity health. A declining IPv6 preference rate is the canary in the coal mine — it indicates IPv6 connectivity degradation before users file tickets about slow connections.

## Implementation

Collect web access logs or NetFlow data for dual-stack services. Classify connections by IP version (IPv4 vs IPv6). Calculate the IPv6 preference rate per destination. Track over time. Alert on declining rates.

## Detailed Implementation

### Prerequisites
- Web access logs from dual-stack services (web servers, load balancers, reverse proxies) with client IP address captured.
- NetFlow/IPFIX from network devices with src/dst IP version distinguishable.
- Services must have both A and AAAA records published in DNS.

### Step 1 — Configure data collection

**Web server access logs** are the most direct source of Happy Eyeballs behaviour data. The `clientip` field directly shows which IP version the client chose:

**nginx — log format with IP version:**
```
log_format combined_v6 '$remote_addr - $remote_user [$time_local] '
                       '"$request" $status $body_bytes_sent '
                       '"$http_referer" "$http_user_agent"';
```
nginx logs IPv6 addresses directly (e.g., `2001:db8::1 - - [01/Jan/2026:...]`).

**F5 BIG-IP — client SSL profile with IP version logging:**
F5 HTTP profiles log the client IP address. IPv6 client addresses contain colons.

**NetFlow — connection-level analysis:**
NetFlow records include the IP version. IPv6 flows have 128-bit source/destination addresses.

**Verification:**
```spl
index=web sourcetype="access_combined" earliest=-24h
| eval ip_version=if(match(clientip, ":"), "IPv6", "IPv4")
| stats count by ip_version
```

### Step 2 — Create the search and alert

**IPv6 preference rate trending:**
```spl
index=web sourcetype="access_combined" earliest=-30d
| eval ip_ver=if(match(clientip, ":"), "IPv6", "IPv4")
| timechart span=1d count by ip_ver
| eval ipv6_pct=round(IPv6 / (IPv6 + IPv4) * 100, 1)
```

**Declining IPv6 preference alert:**
```spl
index=web sourcetype="access_combined" earliest=-7d
| eval ip_ver=if(match(clientip, ":"), "IPv6", "IPv4")
| bin _time span=1d
| stats count(eval(ip_ver="IPv6")) as ipv6 count(eval(ip_ver="IPv4")) as ipv4 by _time
| eval daily_pct=round(ipv6 / (ipv6 + ipv4) * 100, 1)
| delta daily_pct as pct_change
| where pct_change < -5
| eval alert="IPv6 preference dropped " . abs(pct_change) . " percentage points — investigate IPv6 connectivity"
```
Trigger: day-over-day IPv6 preference drop of more than 5 percentage points indicates an IPv6 issue.

**Per-destination IPv6 connectivity score:**
```spl
index=web sourcetype="access_combined" earliest=-24h
| eval ip_ver=if(match(clientip, ":"), "IPv6", "IPv4")
| stats count(eval(ip_ver="IPv6")) as v6 count(eval(ip_ver="IPv4")) as v4 count as total by dest_host
| where total > 100
| eval v6_pct=round(v6 / total * 100, 1)
| eval connectivity=case(
    v6_pct > 40, "healthy",
    v6_pct > 10, "degraded — some IPv6 fallback",
    v6_pct > 0, "mostly failing — heavy IPv4 fallback",
    1=1, "no IPv6 — check AAAA record")
| sort v6_pct
```

### Step 3 — Validate
(a) **Known dual-stack service.** For a service with both A and AAAA records, verify the IPv6 preference rate is >30% in a healthy network.

(b) **IPv6 connectivity break.** Temporarily break IPv6 connectivity (e.g., remove the AAAA record or block IPv6 at the firewall). Verify the IPv6 preference rate drops to near 0% and the declining preference alert fires.

(c) **IPv4-only service.** For a service with only an A record, verify 0% IPv6 connections.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Dual-Stack Connection Health"):
- Row 1 — Gauge: overall IPv6 preference rate (target: >40% for dual-stack).
- Row 2 — Timechart: IPv6 preference rate over 30 days with trend.
- Row 3 — Table: per-destination IPv6 connectivity scores.
- Row 4 — Alert: destinations with declining IPv6 preference.

**Scheduling:** Preference trending daily. Declining preference alert daily. Per-destination analysis weekly.

**Runbook:**
1. Declining IPv6 preference fleet-wide: check for network-wide IPv6 issue (firewall blocking, routing failure, DNS AAAA resolution failure).
2. Declining for a specific destination: check that destination's IPv6 connectivity — AAAA record correct? Firewall allowing IPv6? Service listening on IPv6?
3. Zero IPv6 for a dual-stack service: verify AAAA record, verify IPv6 connectivity to the server, check server socket binding.

### Step 5 — Troubleshooting

- **Happy Eyeballs 250ms delay** — The 250ms connection delay before IPv4 fallback is configurable in some applications but is the RFC 8305 default. In environments with consistently slow IPv6, this delay is experienced on every new connection. Monitoring the IPv6 connection success rate (not just preference) identifies whether the delay is caused by slow IPv6 or broken IPv6.

- **Proxy/load balancer masking** — If a reverse proxy terminates client connections and makes backend connections over a single IP version, the web server logs show the proxy's IP version, not the client's. Ensure the logging captures the original client IP (e.g., via X-Forwarded-For) and its IP version.

- **Measuring connection timing** — To directly measure the Happy Eyeballs delay, correlate the DNS query timing (AAAA response time vs A response time) with the TCP SYN timing for both protocols. The difference reveals the fallback penalty.

## SPL

```spl
index=web sourcetype="access_combined" earliest=-24h
| eval client_ip_version=if(match(clientip, ":"), "IPv6", "IPv4")
| stats count as total count(eval(client_ip_version="IPv6")) as ipv6_conns count(eval(client_ip_version="IPv4")) as ipv4_conns by dest_host
| eval ipv6_preference_pct=round(ipv6_conns / total * 100, 1)
| eval status=case(
    ipv6_preference_pct > 60, "Strong IPv6 preference",
    ipv6_preference_pct > 30, "Balanced dual-stack",
    ipv6_preference_pct > 5, "Low IPv6 — possible connectivity issues",
    ipv6_preference_pct > 0, "Minimal IPv6 — likely broken",
    1=1, "No IPv6 connections")
| sort -total
```

## Visualization

(1) Gauge: overall IPv6 preference percentage for dual-stack destinations. (2) Timechart: IPv6 vs IPv4 connection ratio over 30 days. (3) Table: per-destination IPv6 preference rates (identifies destinations with IPv6 issues). (4) Histogram: connection time distribution by IP version.

## Known False Positives

**IPv4-only clients.** Legacy clients that do not support IPv6 will always connect via IPv4, lowering the IPv6 preference rate. The measurement should focus on clients known to be IPv6-capable.

**CDN IPv4 preference.** Some CDN configurations may prefer IPv4 for traffic engineering reasons, directing clients to IPv4 endpoints even when IPv6 is available. This is a CDN configuration choice, not a connectivity issue.

**Internal services without IPv6.** Services that only have A records (no AAAA) will always see 100% IPv4 connections. These should be excluded from the dual-stack preference analysis — they are IPv4-only destinations, not Happy Eyeballs fallback.

## References

- [RFC 8305 — Happy Eyeballs Version 2: Better Connectivity Using Concurrency](https://www.rfc-editor.org/rfc/rfc8305)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.1 — dual-stack application behaviour)](https://www.rfc-editor.org/rfc/rfc9099)
