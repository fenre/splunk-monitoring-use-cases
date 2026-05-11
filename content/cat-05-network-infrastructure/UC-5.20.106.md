<!-- AUTO-GENERATED from UC-5.20.106.json — DO NOT EDIT -->

---
id: "5.20.106"
title: "IPv6 GRE and IP-in-IP Tunnel Detection and Security Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.106 · IPv6 GRE and IP-in-IP Tunnel Detection and Security Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Sometimes people hide letters inside other letters — a new-format address (IPv6) letter inside an old-format (IPv4) envelope. Our security guards check the outer envelope but might not notice the hidden letter inside. We watch for these 'letters inside letters' to make sure nobody is sneaking things past our security guards through these hidden channels.*

---

## Description

Detects and classifies IPv6 tunneling protocols: 6in4 (protocol 41), GRE carrying IPv6, IP-in-IP, Teredo, and AYIYA. These encapsulation methods can bypass perimeter security by hiding IPv6 payloads inside IPv4 packets. Distinguishes approved (documented) tunnels from unauthorized ones that may indicate misconfiguration, shadow IT, or active exfiltration.

## Value

IPv6 tunnels are one of the most commonly exploited mechanisms for bypassing network security controls. A single unauthorized 6in4 tunnel through a firewall that doesn't inspect protocol 41 creates an unmonitored path to the internet. This UC provides complete tunnel visibility, distinguishing legitimate site-to-site tunnels from rogue connections. The Teredo and AYIYA checks catch consumer-grade tunnel brokers that users may install, and the GRE analysis catches both legitimate and malicious encapsulated IPv6.

## Implementation

Monitor for protocol 41, 47, and 4 in traffic logs. Maintain an approved tunnel inventory. Alert on unapproved tunnel endpoints. Track tunnel volume and duration.

## Detailed Implementation

### Prerequisites
- Firewall/IDS logging for protocol 41, 47, and 4.
- Approved tunnel inventory (CSV lookup).

### Step 1 — Configure data collection

**Approved tunnel inventory:**
```csv
src,dest,approved,tunnel_purpose
10.1.1.1,10.2.2.2,yes,"Site-to-site GRE tunnel — DC to branch"
10.1.1.1,192.0.2.100,yes,"6in4 tunnel to ISP IPv6 gateway"
```

**Cisco IOS — log protocol 41 and GRE:**
```
ipv4 access-list extended TUNNEL-DETECT
 permit 41 any any log
 permit 47 any any log
 permit 4 any any log
 permit ip any any
!
interface GigabitEthernet0/0
 ip access-group TUNNEL-DETECT in
```

**Palo Alto — ensure protocol 41 visibility:**
Palo Alto firewalls decode protocol 41 by default and show the inner IPv6 payload. Verify with:
```
show session all filter protocol 41
```

### Step 2 — Create monitoring searches

**Unapproved tunnel detection:**
```spl
index=network earliest=-24h
| eval is_tunnel=case(
    proto="41", "6in4",
    proto="47", "GRE",
    proto="4", "IP-in-IP",
    dest_port="3544" AND proto="17", "Teredo",
    1=1, null())
| where isnotnull(is_tunnel)
| lookup approved_tunnels.csv src, dest OUTPUT approved
| where isnull(approved) OR approved!="yes"
| stats count as flows sum(bytes) as bytes first(_time) as first last(_time) as last by src, dest, is_tunnel
| eval duration_hours=round((last - first) / 3600, 1)
| eval alert="UNAPPROVED " . is_tunnel . " tunnel: " . src . " → " . dest . " (" . flows . " flows, " . round(bytes/1048576, 1) . " MB, " . duration_hours . " hours)"
| sort -flows
```

**Endpoint Teredo/6to4 scan:**
```spl
index=os sourcetype="WinRegistry" earliest=-7d
  ("Teredo" OR "6to4" OR "ISATAP")
| rex field=_raw "State.*(?<tunnel_state>\d+)"
| eval status=case(
    match(_raw, "Teredo") AND tunnel_state!="0", "Teredo ENABLED — disable with 'netsh interface teredo set state disabled'",
    match(_raw, "6to4") AND tunnel_state!="0", "6to4 ENABLED — disable with 'netsh interface 6to4 set state disabled'",
    match(_raw, "ISATAP") AND tunnel_state!="0", "ISATAP ENABLED — disable with 'netsh interface isatap set state disabled'",
    1=1, null())
| where isnotnull(status)
| table host, status
```

### Step 3 — Validate
(a) **Tunnel detection test.** From a test host, establish a 6in4 tunnel to a test endpoint:
```bash
sudo ip tunnel add test6in4 mode sit remote 192.0.2.1 local 10.1.1.100
sudo ip link set test6in4 up
sudo ip -6 addr add 2001:db8:test::1/64 dev test6in4
ping6 -c 3 2001:db8:test::2
```
Verify the tunnel is detected in Splunk.

(b) **Teredo test.** On a Windows machine, enable Teredo (`netsh interface teredo set state client`). Verify the endpoint scan detects it.

(c) **Approved vs unapproved.** Verify that approved tunnels appear in the dashboard with 'APPROVED' status and do not trigger alerts.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Tunnel Security"):
- Row 1 — Single-values: unapproved tunnels (red if >0), total tunnel flows.
- Row 2 — Table: all detected tunnels with approval status.
- Row 3 — Pie chart: tunnel type distribution.
- Row 4 — Table: endpoints with Teredo/6to4/ISATAP enabled.

**Alert 1:** Any unapproved tunnel — high. Immediate investigation.
**Alert 2:** Teredo or AYIYA detected — high. Consumer tunnel broker on corporate network.
**Alert 3:** Tunnel volume >100MB/hour — medium. Possible data exfiltration via tunnel.

### Step 5 — Troubleshooting

- **Firewall not inspecting protocol 41.** Some older firewalls pass protocol 41 without inspection. Verify the firewall's IPv6 tunnel inspection capability. If it can't inspect, create an explicit deny rule for protocol 41 at the perimeter.

- **GRE tunnel volume.** High GRE volume is normal for approved site-to-site tunnels. Only investigate unapproved GRE tunnels or approved tunnels with unexpected volume spikes.

- **Tunnel endpoint identification.** When a tunnel is detected, identify both endpoints. The internal endpoint reveals the compromised or misconfigured host. The external endpoint may be a tunnel broker, attacker infrastructure, or legitimate partner.

## SPL

```spl
index=network (sourcetype="pan:traffic" OR sourcetype="cisco:ios" OR sourcetype="zeek:conn") earliest=-24h
| eval is_tunnel=case(
    match(proto, "^41$") OR match(protocol, "(?i)6in4|6to4|6rd|proto-41"), "6in4 (protocol 41)",
    match(proto, "^47$") OR match(protocol, "(?i)gre"), "GRE",
    match(proto, "^4$") OR match(protocol, "(?i)ipip|ip-in-ip"), "IP-in-IP",
    match(app, "(?i)teredo") OR (match(dest_port, "^3544$") AND match(proto, "^17$")), "Teredo (UDP 3544)",
    match(app, "(?i)ayiya") OR match(dest_port, "^5072$"), "AYIYA (UDP 5072)",
    1=1, null())
| where isnotnull(is_tunnel)
| lookup approved_tunnels.csv src, dest OUTPUT approved, tunnel_purpose
| eval security_status=case(
    approved="yes", "APPROVED — " . tunnel_purpose,
    is_tunnel="Teredo*", "HIGH RISK — Teredo bypasses all perimeter controls (RFC 7526 deprecated)",
    is_tunnel="AYIYA*", "HIGH RISK — AYIYA tunnel to external broker",
    is_tunnel="6in4*" AND NOT match(src, "^10\.|^172\.(1[6-9]|2[0-9]|3[01])\.|^192\.168\."), "MEDIUM — inbound 6in4 from external source",
    1=1, "UNAPPROVED — investigate immediately")
| stats count as flows sum(bytes) as total_bytes by src, dest, is_tunnel, security_status
| sort -flows
```

## Visualization

(1) Table: detected tunnels with approval status. (2) Pie chart: tunnel types. (3) Single-value: unapproved tunnel count (red if >0). (4) Traffic chart: tunnel volume over time.

## Known False Positives

**Approved site-to-site tunnels.** GRE and 6in4 tunnels between documented endpoints are expected. Maintain an approved tunnel lookup and exclude from alerts.

**SD-WAN tunnels.** SD-WAN devices (Viptela, Silverpeak) may use GRE for overlay transport. These are legitimate but should be documented in the approved tunnel list.

**VPN clients.** Some VPN solutions use protocol 41 or GRE for IPv6 transport. Corporate VPN clients should be documented as approved endpoints.

## References

- [RFC 4213 — Basic Transition Mechanisms for IPv6 Hosts and Routers (6in4 tunneling)](https://www.rfc-editor.org/rfc/rfc4213)
- [RFC 7526 — Deprecating the Anycast Prefix for 6to4 Relay Routers](https://www.rfc-editor.org/rfc/rfc7526)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.7 — tunnels)](https://www.rfc-editor.org/rfc/rfc9099)
