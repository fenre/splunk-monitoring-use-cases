<!-- AUTO-GENERATED from UC-5.20.83.json — DO NOT EDIT -->

---
id: "5.20.83"
title: "Dual-Stack VPN IPv6 Traffic Leakage Detection (RFC 7359)"
status: "verified"
criticality: "critical"
splunkPillar: "Platform"
---

# UC-5.20.83 · Dual-Stack VPN IPv6 Traffic Leakage Detection (RFC 7359)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*When you use a secret tunnel (VPN) to send your letters privately, some of your letters might accidentally go through the regular postal system (IPv6) instead of the secret tunnel. A spy at the coffee shop could read those letters. We check for any letters that escaped the secret tunnel and went out the normal way.*

---

## Description

Detects IPv6 traffic from VPN-connected clients that is bypassing the encrypted VPN tunnel and flowing directly over the local network. This is a well-documented vulnerability (RFC 7359) where VPN clients that only tunnel IPv4 traffic leave IPv6 traffic exposed. The issue is amplified by Happy Eyeballs (RFC 8305), which causes the operating system to prefer IPv6 when available, meaning most dual-stack traffic will take the unprotected path.

## Value

VPN leakage via IPv6 is one of the most impactful and least-understood IPv6 security vulnerabilities. A user who believes they are protected by a corporate VPN may have 50% or more of their traffic flowing unencrypted over the local network. This affects confidentiality (traffic inspection), integrity (traffic modification), and compliance (data crossing uncontrolled networks). Detection is critical because users have no visibility into which path their traffic takes.

## Implementation

Correlate VPN session data with IPv6 flow data. Identify IPv6 flows from VPN clients that exit through the physical interface rather than the VPN tunnel interface. Alert on any IPv6 traffic that bypasses the VPN.

## Detailed Implementation

### Prerequisites
- VPN session log data (Cisco AnyConnect, GlobalProtect, FortiClient).
- Firewall or flow data showing both tunnel and non-tunnel interfaces.
- Understanding of VPN client IPv6 capabilities.

### Step 1 — Configure data collection

**Create VPN client assignment lookup (auto-populated from VPN logs):**
```spl
index=network (sourcetype="pan:globalprotect" OR sourcetype="cisco:asa" OR sourcetype="cisco:ftd") "VPN" "connected"
| rex field=_raw "user=(?<vpn_user>\S+)"
| rex field=_raw "(?:assigned|tunnel).?(?:ip|address)\s*=?\s*(?<tunnel_ip>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:public|real).?(?:ip|address)\s*=?\s*(?<public_ip>[0-9a-fA-F:.]+)"
| eval vpn_status="connected"
| eval tunnel_interface="tunnel.1"
| table vpn_user, public_ip, tunnel_ip, vpn_status, tunnel_interface
| outputlookup vpn_client_assignments.csv
```

**Detection search — DNS leakage via IPv6:**
```spl
index=network (sourcetype="pan:traffic" OR sourcetype="cisco:asa") dest_port=53 earliest=-1h
| eval is_ipv6_dns=if(match(src, ":") AND match(dest, ":"), 1, 0)
| where is_ipv6_dns=1
| lookup vpn_client_assignments.csv public_ip as src OUTPUT vpn_user, vpn_status
| where vpn_status="connected"
| stats count as dns_queries dc(dest) as unique_resolvers by src, vpn_user
| eval alert="VPN user " . vpn_user . " sending " . dns_queries . " DNS queries over IPv6 (outside VPN tunnel) to " . unique_resolvers . " resolvers"
```

**Verification:**
```spl
index=network sourcetype="pan:globalprotect" "connected" | stats count by user | head 10
```

### Step 2 — Create detection dashboard

**Full VPN leakage detection:**
```spl
index=network (sourcetype="pan:traffic" OR sourcetype="netflow") earliest=-4h
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| where is_ipv6=1
| lookup vpn_client_assignments.csv public_ip as src OUTPUT vpn_user, vpn_status
| where vpn_status="connected"
| eval leaked_dest_type=case(
    dest_port=53, "DNS (reveals browsing activity)",
    dest_port=443, "HTTPS (reveals sites visited)",
    dest_port=80, "HTTP (content exposed)",
    1=1, "Other (port " . dest_port . ")")
| stats count as flows sum(bytes) as bytes dc(dest) as unique_dests by vpn_user, leaked_dest_type
| sort -flows
```

### Step 3 — Validate
(a) **Controlled test.** Connect a test device to VPN. Enable IPv6 on the local interface. Browse to a dual-stack website (google.com). Check whether flows appear on the local (non-VPN) interface in IPv6.

(b) **DNS leak test.** While connected to VPN, run `nslookup -type=AAAA google.com` and observe which DNS resolver responds. If it's not the VPN DNS, leakage is confirmed.

(c) **RA injection test.** On a lab network with a VPN client, inject a rogue RA providing IPv6 connectivity. Verify the VPN client's traffic shifts to IPv6 (bypassing the tunnel).

### Step 4 — Operationalize

**Dashboard** ("IPv6 — VPN Traffic Leakage"):
- Row 1 — Single-value: users with active IPv6 VPN leakage (target: 0).
- Row 2 — Table: per-user leakage detail with traffic classification.
- Row 3 — Timechart: leaked flows over time.
- Row 4 — Pie chart: leakage by traffic type (DNS, HTTPS, other).

**Alert:** Any VPN user with IPv6 DNS leakage — immediate notification. DNS leakage reveals all browsing activity regardless of HTTPS encryption.

**Remediation options:**
1. **VPN client configuration.** Configure VPN client to tunnel IPv6 (Cisco AnyConnect: `ipv6-addr-only` split-tunnel policy).
2. **Disable IPv6 on VPN adapter.** Less ideal but effective: disable IPv6 on the physical adapter when VPN connects.
3. **Full tunnel mode.** Use full-tunnel VPN that captures all traffic (both IPv4 and IPv6).
4. **Network-level mitigation.** Deploy RA Guard on network segments used by VPN clients to prevent rogue RA attacks.

### Step 5 — Troubleshooting

- **VPN platform variations.** Each VPN platform handles IPv6 differently. Cisco AnyConnect supports IPv6 tunnel transport but may not tunnel IPv6 traffic by default. Palo Alto GlobalProtect requires explicit IPv6 tunnel configuration. WireGuard tunnels both by default if configured.

- **Mobile devices.** iOS and Android VPN clients have different IPv6 handling. iOS Always-On VPN with IKEv2 tunnels IPv6 by default. Android depends on the VPN app.

- **Correlation timing.** VPN session start/end times may not align precisely with flow data timestamps. Allow a 5-minute tolerance window around VPN session boundaries.

## SPL

```spl
index=network (sourcetype="pan:traffic" OR sourcetype="netflow") earliest=-4h
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| where is_ipv6=1
| lookup vpn_client_assignments.csv src_ip as src OUTPUT vpn_user, vpn_status, tunnel_interface
| where vpn_status="connected" AND isnotnull(vpn_user)
| eval egress=coalesce(egress_interface, outbound_if)
| eval leaking=if(egress != tunnel_interface, 1, 0)
| where leaking=1
| stats count as leaked_flows dc(dest) as unique_dests sum(bytes) as leaked_bytes by src, vpn_user, egress
| eval alert="VPN user " . vpn_user . " has " . leaked_flows . " IPv6 flows (" . round(leaked_bytes/1024, 0) . " KB) bypassing VPN tunnel via " . egress
| sort -leaked_flows
```

## Visualization

(1) Single-value: number of VPN users with IPv6 leakage. (2) Table: per-user leakage detail with flow count and data volume. (3) Timechart: leaked IPv6 flows over time. (4) Pie chart: leaked traffic by destination category.

## Known False Positives

**Split-tunnel VPN by design.** Some organisations intentionally configure split-tunnel VPNs where internet traffic bypasses the VPN. In this case, IPv6 internet traffic on the local interface is expected. However, even with split-tunnel, traffic to corporate resources should still go through the VPN tunnel.

**VPN client-side IPv6 connectivity testing.** During VPN connection establishment, there may be a brief window where IPv6 traffic flows locally before the tunnel captures it.

**IPv6-only VPN clients.** Modern VPN clients (WireGuard, some Cisco AnyConnect versions) can tunnel IPv6 natively. Verify VPN client configuration before flagging leakage.

## References

- [RFC 7359 — Layer 3 Virtual Private Network (VPN) Tunnel Traffic Leakages in Dual-Stack Hosts/Networks](https://www.rfc-editor.org/rfc/rfc7359)
- [RFC 8305 — Happy Eyeballs Version 2 (exacerbates VPN leakage by preferring IPv6)](https://www.rfc-editor.org/rfc/rfc8305)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.7.3 — VPN dual-stack considerations)](https://www.rfc-editor.org/rfc/rfc9099)
