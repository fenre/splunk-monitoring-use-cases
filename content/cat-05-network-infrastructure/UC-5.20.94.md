<!-- AUTO-GENERATED from UC-5.20.94.json — DO NOT EDIT -->

---
id: "5.20.94"
title: "IPv6 Source Port Logging for User Attribution (RFC 6302 / BCP 162)"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.94 · IPv6 Source Port Logging for User Attribution (RFC 6302 / BCP 162)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Compliance, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*When multiple families share the same street address (IPv6 via NAT64), the only way to identify which family received a specific letter is by their apartment number (source port). The international standards (RFC 6302) say every post office and mailroom must record: the address, the apartment number, the exact time, and what type of post it was. We check that everyone is keeping proper records.*

---

## Description

Verifies that servers, firewalls, and network devices log source port numbers alongside IPv6 source addresses with accurate timestamps, as required by RFC 6302 (BCP 162). Source port logging is essential for user attribution in environments with shared IPv6 addresses (NAT64, CGN, privacy extensions). Without source port, it is impossible to attribute network activity to a specific user or device.

## Value

RFC 6302 compliance is the foundation of IPv6 forensic capability. Without source port logging, law enforcement requests, abuse complaints, and internal investigations involving IPv6 addresses are unanswerable when addresses are shared. Many organisations discover this gap only when they receive their first IPv6-related legal request and cannot identify the user. Proactive verification prevents this costly and potentially legally-significant discovery.

## Implementation

Audit web server, firewall, and load balancer log formats for source port inclusion. Verify NTP synchronisation accuracy. Create a compliance report showing which systems comply with RFC 6302.

## Detailed Implementation

### Prerequisites
- Internet-facing server log data in Splunk.
- Firewall log data with connection detail.
- NTP synchronisation verification capability.

### Step 1 — Configure data collection

**Apache/Nginx log format with source port:**

Apache httpd.conf:
```
LogFormat "%h:%{remote}p %l %u %t \"%r\" %>s %b" combined_with_port
```
The `%{remote}p` directive logs the client's source port.

Nginx:
```
log_format combined_port '$remote_addr:$remote_port - $remote_user [$time_local] '
                         '"$request" $status $body_bytes_sent ';
```

**Palo Alto Networks — source port is logged by default in traffic logs.** Verify with:
```spl
index=network sourcetype="pan:traffic" | eval has_sport=if(isnotnull(src_port), 1, 0) | stats count by has_sport
```

**Load balancer X-Forwarded-For with port:**
Many load balancers strip the source port from X-Forwarded-For. Configure to include it:
```
# HAProxy
http-request set-header X-Forwarded-Port %[src_port]

# F5 BIG-IP
HTTP::header insert X-Forwarded-Port [TCP::client_port]
```

**Verification:**
```spl
index=web sourcetype="access_combined" earliest=-1h | eval has_port=if(match(_raw, "\d+\.\d+\.\d+\.\d+:\d+|\]:?\d+"), 1, 0) | stats count by has_port
```

### Step 2 — Create compliance audit

**Full RFC 6302 compliance check (address + port + timestamp + protocol):**
```spl
index=web sourcetype="access_combined" earliest=-24h
| eval has_address=if(isnotnull(clientip), 1, 0)
| eval has_port=if(isnotnull(clientPort) OR match(_raw, ":\d{1,5}\s"), 1, 0)
| eval has_timestamp=if(isnotnull(_time), 1, 0)
| eval has_protocol=if(isnotnull(http_method) OR isnotnull(protocol), 1, 0)
| eval rfc6302_fields=has_address + has_port + has_timestamp + has_protocol
| eval rfc6302_compliant=if(rfc6302_fields=4, 1, 0)
| stats count as total count(eval(rfc6302_compliant=1)) as compliant by host
| eval compliance_pct=round(compliant / total * 100, 1)
| sort compliance_pct
```

**NTP accuracy audit (timestamps must be reliable):**
```spl
index=network sourcetype="cisco:ios" "%NTP" earliest=-24h
| eval ntp_issue=case(
    match(_raw, "clock.*unsynchronized"), "CRITICAL — clock not synchronized",
    match(_raw, "stratum.*16"), "CRITICAL — NTP unreachable (stratum 16)",
    match(_raw, "offset.*[0-9]{4,}"), "WARNING — clock offset >1 second",
    1=1, null())
| where isnotnull(ntp_issue)
| table host, ntp_issue
```

### Step 3 — Validate
(a) **Web server test.** From an IPv6 client, make an HTTP request to a sample web server. Verify the access log contains: client IPv6 address, source port, accurate timestamp, and protocol.

(b) **Firewall log test.** Verify firewall traffic logs for IPv6 connections contain all four RFC 6302 fields.

(c) **NTP verification.** Run `ntpq -p` on sample servers. Verify offset < 100ms and stratum < 5.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — RFC 6302 Source Port Compliance"):
- Row 1 — Single-value: systems with full RFC 6302 compliance.
- Row 2 — Table: per-system compliance audit with field-level detail.
- Row 3 — Bar chart: compliance rate by system category.
- Row 4 — NTP accuracy status across all systems.

**Scheduling:** Monthly audit of log format compliance.

**Runbook:**
1. Missing source port on web server: Update log format to include `%{remote}p` (Apache) or `$remote_port` (Nginx). Restart service.
2. Missing source port on load balancer: Add X-Forwarded-Port header insertion. Verify backend servers log this header.
3. NTP unsynchronised: Fix NTP configuration. Verify with `ntpstat` or `chronyc tracking`.

### Step 5 — Troubleshooting

- **Log parsing changes.** Adding source port to log format may break existing Splunk field extractions. Update props.conf EXTRACT or REPORT directives to handle the new format.

- **CDN/proxy chains.** When multiple proxies are involved (CDN → WAF → LB → server), source port information may be lost at each hop. Ensure each component propagates source port information.

- **IPv6 address format in logs.** IPv6 addresses in URLs use bracket notation ([2001:db8::1]:443). Verify log parsers handle this format correctly and don't confuse the port separator colon with IPv6 address colons.

## SPL

```spl
index=web sourcetype="access_combined" earliest=-24h
| eval has_src_port=if(isnotnull(clientPort) OR match(_raw, ":\d{1,5}\s"), 1, 0)
| eval has_ipv6_client=if(match(clientip, ":"), 1, 0)
| where has_ipv6_client=1
| stats count as total_requests count(eval(has_src_port=1)) as with_port count(eval(has_src_port=0)) as without_port by host
| eval port_logging_pct=round(with_port / total_requests * 100, 1)
| eval status=case(
    port_logging_pct=100, "COMPLIANT — all IPv6 requests include source port",
    port_logging_pct > 0, "PARTIAL — " . without_port . " IPv6 requests missing source port",
    1=1, "NON-COMPLIANT — NO source port logging for IPv6 clients")
| eval rfc6302_compliance=if(port_logging_pct=100, "PASS", "FAIL — RFC 6302 (BCP 162) requires source port for attribution")
| sort port_logging_pct
```

## Visualization

(1) Single-value: systems with RFC 6302-compliant IPv6 logging. (2) Table: per-system log format audit results. (3) Bar chart: compliance rate by system category (web server, firewall, LB). (4) Trend: compliance improvement over time.

## Known False Positives

**Direct connections without NAT.** When IPv6 hosts connect directly (no NAT64/CGN), the IPv6 address alone uniquely identifies the host. Source port is still recommended but less critical for attribution in this scenario.

**ICMP/ICMPv6 traffic.** ICMP does not have ports. RFC 6302 source port requirement applies to TCP and UDP traffic only.

**Internal-only services.** Services that are never internet-facing and serve only authenticated internal users may have lower RFC 6302 priority, since user identity is established by authentication rather than network attribution.

## References

- [RFC 6302 — Logging Recommendations for Internet-Facing Servers (BCP 162)](https://www.rfc-editor.org/rfc/rfc6302)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.1.5 — logging requirements)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 6269 — Issues with IP Address Sharing (motivation for source port logging)](https://www.rfc-editor.org/rfc/rfc6269)
