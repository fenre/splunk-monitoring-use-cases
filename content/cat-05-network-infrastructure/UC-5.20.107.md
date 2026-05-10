<!-- AUTO-GENERATED from UC-5.20.107.json — DO NOT EDIT -->

---
id: "5.20.107"
title: "IPv6 Happy Eyeballs (RFC 8305) Client Connection Race Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.107 · IPv6 Happy Eyeballs (RFC 8305) Client Connection Race Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*Modern phones and computers are smart — when they want to reach a website, they try both the old address (IPv4) and the new address (IPv6) at the same time and use whichever works faster. This means that if the new address system is broken, nobody notices because the old one still works.*

---

## Description

Monitors Happy Eyeballs (RFC 8305) connection racing behaviour on dual-stack networks. Tracks the IPv6 preference ratio (what percentage of connections use IPv6 vs IPv4), identifies services where IPv6 consistently loses the connection race (indicating IPv6 performance problems), and detects IPv6 degradation that is otherwise invisible because Happy Eyeballs silently falls back to IPv4.

## Value

Happy Eyeballs is simultaneously the best and worst thing about dual-stack networking. It ensures users always get a working connection, but it also hides IPv6 failures. An organisation can have completely broken IPv6 for weeks without any user complaints because every connection silently falls back to IPv4. This UC surfaces the hidden IPv6 failures by analysing connection patterns, ensuring IPv6 issues are detected and remediated before they become entrenched.

## Implementation

Analyse connection logs to determine IPv6 vs IPv4 usage ratios. Compare connection timing. Identify services where IPv6 consistently loses the race. Alert on declining IPv6 preference ratios.

## Detailed Implementation

### Prerequisites
- Zeek or Corelight sensor on key network segments.
- Dual-stack network with both IPv4 and IPv6 connectivity.
- DNS returning both A and AAAA records for target services.

### Step 1 — Configure data collection

Zeek's `conn.log` naturally captures both IPv4 and IPv6 connections. No special configuration is needed beyond standard Zeek deployment.

**For web server analysis, use server access logs:**
```
LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" %{remote}p" combined_port
```
(The `%{remote}p` captures the client port needed for RFC 6302 compliance.)

**Splunk UF `inputs.conf` for web logs:**
```ini
[monitor:///var/log/nginx/access.log]
sourcetype = access_combined
index = web
```

### Step 2 — Create monitoring searches

**Overall IPv6 preference ratio (key metric):**
```spl
index=network sourcetype="zeek:conn" earliest=-24h
| eval ip_version=if(match(id_orig_h, ":") OR match(id_resp_h, ":"), "IPv6", "IPv4")
| timechart span=1h count by ip_version
| eval total=IPv4 + IPv6
| eval ipv6_pct=round(IPv6 / total * 100, 1)
```

**Per-service Happy Eyeballs analysis:**
```spl
index=network sourcetype="zeek:conn" earliest=-24h id_resp_p IN (80, 443, 8080, 8443)
| eval ip_version=if(match(id_resp_h, ":"), "IPv6", "IPv4")
| stats count as conns avg(duration) as avg_duration by id_resp_h, id_resp_p, ip_version
| eventstats sum(conns) as total_conns by id_resp_h, id_resp_p
| eval pct=round(conns / total_conns * 100, 1)
| where ip_version="IPv6"
| eval assessment=case(
    pct > 80, "Healthy",
    pct > 50, "OK",
    pct > 20, "Degraded — investigate IPv6 path",
    1=1, "Poor — IPv6 likely broken for this service")
| sort pct
```

**IPv6 preference trend (detect degradation):**
```spl
index=network sourcetype="zeek:conn" earliest=-30d
| eval day=strftime(_time, "%Y-%m-%d")
| eval is_ipv6=if(match(id_orig_h, ":") OR match(id_resp_h, ":"), 1, 0)
| stats count as total sum(is_ipv6) as ipv6 by day
| eval ipv6_pct=round(ipv6 / total * 100, 1)
| sort day
```

### Step 3 — Validate
(a) **Dual-stack test.** From a dual-stack client, access a known dual-stack service (e.g., `curl -v https://google.com`). Note whether the connection uses IPv6 or IPv4. Correlate with the Splunk data.

(b) **Forced IPv6 test.** Use `curl -6 https://example.com` to force IPv6. If this fails but `curl -4` succeeds, IPv6 connectivity is broken and Happy Eyeballs is masking it.

(c) **Timing test.** Measure IPv6 vs IPv4 connection setup time:
```bash
time curl -6 -o /dev/null -s https://example.com
time curl -4 -o /dev/null -s https://example.com
```
If IPv6 is consistently slower by >250ms, it will lose every Happy Eyeballs race.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Happy Eyeballs Monitoring"):
- Row 1 — Gauge: overall IPv6 preference ratio (green >80%, amber 50-80%, red <50%).
- Row 2 — Timechart: IPv6 vs IPv4 connection counts over time.
- Row 3 — Table: services with low IPv6 preference (potential issues).
- Row 4 — Trend: 30-day IPv6 preference trend (detect degradation).

**Alert:** IPv6 preference ratio drops below 50% (when previously >80%) — high. Something has changed.
**Alert:** Specific dual-stack service shows 0% IPv6 for >1 hour — medium. IPv6 connectivity to that service is likely broken.

### Step 5 — Troubleshooting

- **IPv6 preference suddenly drops.** Check for (a) DNS resolution issues (AAAA records not returned or delayed), (b) routing changes (IPv6 default route missing), (c) upstream ISP IPv6 outage, (d) firewall rule change blocking IPv6.

- **IPv6 preference is always low.** If IPv6 always loses the race, measure RTT for both protocols. Common causes: asymmetric routing (IPv6 taking a longer path), broken PMTUD (fragmentation causing retransmissions), or DNS64/NAT64 overhead.

- **Different results by client type.** Different operating systems implement Happy Eyeballs differently. macOS/iOS aggressively prefer IPv6; Windows uses a more conservative 250ms timeout; older Linux kernels may not implement Happy Eyeballs at all. Segment analysis by client OS if possible.

## SPL

```spl
index=network sourcetype="zeek:conn" earliest=-4h
| eval is_ipv6=if(match(id_orig_h, ":") OR match(id_resp_h, ":"), 1, 0)
| eval conn_duration_ms=round(duration * 1000, 0)
| stats count as total count(eval(is_ipv6=1)) as ipv6_conns count(eval(is_ipv6=0)) as ipv4_conns avg(eval(if(is_ipv6=1, conn_duration_ms, null()))) as avg_ipv6_ms avg(eval(if(is_ipv6=0, conn_duration_ms, null()))) as avg_ipv4_ms by id_resp_p
| eval ipv6_pct=round(ipv6_conns / total * 100, 1)
| eval performance_gap=round(avg_ipv6_ms - avg_ipv4_ms, 0)
| eval happy_eyeballs_status=case(
    ipv6_pct > 80, "HEALTHY — IPv6 preferred (" . ipv6_pct . "%)",
    ipv6_pct > 50, "OK — slight IPv6 preference (" . ipv6_pct . "%)",
    ipv6_pct > 20, "DEGRADED — IPv4 winning most races (IPv6 only " . ipv6_pct . "%)",
    ipv6_pct > 0, "POOR — IPv6 rarely used (" . ipv6_pct . "%) — check for connectivity issues",
    1=1, "NO IPv6 — all connections are IPv4")
| where ipv6_pct < 80 AND total > 100
| sort ipv6_pct
```

## Visualization

(1) Gauge: IPv6 preference ratio (target >80%). (2) Timechart: IPv6 vs IPv4 connection counts. (3) Table: services with low IPv6 preference. (4) Line chart: IPv6 preference trend over days/weeks.

## Known False Positives

**IPv4-only services.** Services that are IPv4-only will correctly show 0% IPv6. Only investigate services that are supposed to be dual-stack.

**DNS load balancing.** Some DNS load balancers may rotate between A and AAAA responses, leading to roughly 50/50 distribution. This is expected behaviour for some CDN configurations.

**Client population.** If the client population includes many legacy devices that don't support Happy Eyeballs (older IoT, embedded systems), the IPv6 preference ratio will be lower. Segment analysis by client type.

## References

- [RFC 8305 — Happy Eyeballs Version 2: Better Connectivity Using Concurrency](https://www.rfc-editor.org/rfc/rfc8305)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6 — monitoring parity)](https://www.rfc-editor.org/rfc/rfc9099)
