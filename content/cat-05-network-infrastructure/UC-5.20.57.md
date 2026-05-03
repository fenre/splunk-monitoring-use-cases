<!-- AUTO-GENERATED from UC-5.20.57.json — DO NOT EDIT -->

---
id: "5.20.57"
title: "IPv6 Tunnel Protocol Detection and Shadow Tunnel Audit"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.20.57 · IPv6 Tunnel Protocol Detection and Shadow Tunnel Audit

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Imagine someone building a secret underground tunnel from inside your house to the outside, bypassing all your locks and security cameras. That's what these deprecated IPv6 tunnels do — they create hidden pathways through the firewall that security can't see. We watch for any signs of these secret tunnels being built and shut them down immediately.*

---

## Description

Detects unauthorized IPv6 transition tunnels (6to4, Teredo, ISATAP, 6rd) that bypass perimeter security controls by encapsulating IPv6 traffic inside IPv4 or UDP. These deprecated tunneling mechanisms were designed for early IPv6 adoption but are now major security risks because they allow IPv6 traffic to traverse IPv4 firewalls that don't inspect the tunnel payload. A single host running Teredo can create a bidirectional IPv6 tunnel to the internet that bypasses all perimeter security, enabling data exfiltration, command-and-control, and malware delivery over IPv6.

## Value

Shadow IPv6 tunnels are one of the most dangerous network security blind spots. A Windows machine with Teredo enabled (it was on by default in some Windows versions) creates an IPv6 tunnel through the corporate IPv4 firewall to a Microsoft relay on the internet. The firewall sees UDP traffic on port 3544 to a Microsoft IP — perfectly benign-looking. But inside that UDP stream is a full IPv6 tunnel that can carry any traffic, completely bypassing the firewall's DLP, IPS, and proxy inspection. Detecting and blocking these tunnels is a critical security requirement listed in NIST SP 800-119, RFC 9099, and DISA STIGs.

## Implementation

Monitor for IP protocol 41 (IPv6-in-IPv4), UDP port 3544 (Teredo), 6to4 anycast relay (192.88.99.1), and 2002::/16 address usage. Block deprecated tunnels at the firewall. Alert on any detection. Monitor for configured tunnels (GRE, IPsec) as legitimate exceptions.

## Detailed Implementation

### Prerequisites
- Firewall logging enabled for IP protocol 41, UDP port 3544, and traffic to 192.88.99.1.
- Zeek/Corelight sensors for deep packet inspection of tunnel payloads.
- Inventory of legitimate IPv6 tunnels (endpoints, protocols, purpose).

### Step 1 — Configure data collection

**Firewall rules — block deprecated tunnels at perimeter:**

**Palo Alto PAN-OS:**
```
# Block 6to4 anycast relay
security policy deny-6to4
  from any to any
  destination 192.88.99.1/32
  action deny
  log true

# Block Teredo
security policy deny-teredo
  from any to any
  application teredo
  action deny
  log true

# Block protocol 41 (except known tunnels)
security policy deny-proto41
  from any to any
  protocol 41
  action deny
  log true
```

**Cisco ASA:**
```
access-list DENY_TUNNELS deny 41 any host 192.88.99.1 log
access-list DENY_TUNNELS deny udp any any eq 3544 log
access-list DENY_TUNNELS deny 41 any any log
```

**Windows GPO — disable Teredo and ISATAP:**
```
netsh interface teredo set state disabled
netsh interface isatap set state disabled
netsh interface 6to4 set state disabled
```
Or via Group Policy: `Computer Configuration → Administrative Templates → Network → TCPIP Settings → IPv6 Transition Technologies → Set Teredo State → Disabled`.

**Verification:**
```spl
index=network (sourcetype="paloalto:traffic" OR sourcetype="cisco:asa") ("protocol 41" OR "3544" OR "192.88.99.1" OR "teredo" OR "6to4") earliest=-7d
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**6to4 detection (CRITICAL):**
```spl
index=network (sourcetype="paloalto:traffic" OR sourcetype="cisco:asa" OR sourcetype="cisco:ios")
  ("192.88.99.1" OR "2002:" OR ("protocol" AND "41"))
  earliest=-1h
| rex field=_raw "(?:src|source)\s*=?\s*(?<src>[0-9.]+)"
| eval alert="6to4 tunnel detected: " . src . " — deprecated by RFC 7526. Blocks perimeter security."
| table _time, host, src, alert
```
Trigger: any detection.

**Teredo detection (CRITICAL):**
```spl
index=network (sourcetype="paloalto:traffic" OR sourcetype="cisco:asa" OR sourcetype="zeek:conn")
  ("3544" OR "teredo")
  earliest=-1h
| rex field=_raw "(?:src|source)\s*=?\s*(?<src>[0-9.]+)"
| eval alert="Teredo tunnel detected: " . src . " — deprecated. Creates uncontrolled IPv6 tunnel through firewall."
| table _time, host, src, alert
```

**Protocol 41 inventory (legitimate vs shadow):**
```spl
index=network (sourcetype="paloalto:traffic" OR sourcetype="cisco:asa") "protocol 41" earliest=-24h
| rex field=_raw "(?:src|source)\s*=?\s*(?<src>[0-9.]+)"
| rex field=_raw "(?:dst|dest)\s*=?\s*(?<dst>[0-9.]+)"
| lookup approved_tunnels.csv src, dst OUTPUT tunnel_name, approved
| eval status=if(approved="yes", "APPROVED — " . tunnel_name, "UNAPPROVED — investigate immediately")
| table _time, src, dst, status
```

### Step 3 — Validate
(a) **Teredo test (lab).** Enable Teredo on a Windows machine (`netsh interface teredo set state client`). Verify the firewall logs and alert fire.

(b) **6to4 test (lab).** Configure a 6to4 tunnel on a test router. Verify protocol 41 traffic to 192.88.99.1 is detected.

(c) **Legitimate tunnel verification.** Verify that approved configured tunnels appear in the protocol 41 inventory with 'APPROVED' status.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Transition Tunnel Security"):
- Row 1 — Single-value: deprecated tunnel detections (6to4, Teredo, ISATAP) — must be 0.
- Row 2 — Table: all tunnel detections with type, source, destination, and approved/unapproved status.
- Row 3 — Timechart: tunnel traffic volume by type over 30 days.
- Row 4 — Windows GPO compliance: hosts with Teredo/ISATAP still enabled.

**Scheduling:** Deprecated tunnel detection continuous (every 5 minutes). Protocol 41 inventory daily.

**Runbook:**
1. 6to4/Teredo detected: immediately identify the source host. Disable the tunnel mechanism via GPO or local configuration. Block at firewall.
2. ISATAP detected: disable on the host. Remove ISATAP router configuration if present.
3. Unapproved protocol 41: investigate. Determine if this is a legitimate tunnel that needs documentation or an unauthorized tunnel that needs blocking.

### Step 5 — Troubleshooting

- **Windows Teredo re-enabling** — Windows may re-enable Teredo after updates. Use Group Policy to persistently enforce the disabled state.

- **Protocol 41 vs GRE** — GRE (protocol 47) also carries IPv6 but is used for legitimate DMVPN and SD-WAN tunnels. Do not confuse protocol 41 (raw IPv6-in-IPv4) with protocol 47 (GRE encapsulation). Both can carry IPv6 but have different security implications.

- **Firewall tunnel decapsulation** — Modern firewalls (Palo Alto, Fortinet) can decapsulate and inspect tunnel payloads. Enable tunnel inspection to detect malicious content inside legitimate tunnels.

## SPL

```spl
index=network (sourcetype="paloalto:traffic" OR sourcetype="cisco:ios" OR sourcetype="zeek:conn") earliest=-24h
| eval tunnel_type=case(
    match(_raw, "(?i)protocol.?41|ip-encap|ipv6inipv4") AND match(_raw, "192\.88\.99\.1"), "6to4 via anycast relay — CRITICAL",
    match(_raw, "(?i)protocol.?41|ip-encap") AND match(_raw, "2002:"), "6to4 tunnel — CRITICAL",
    match(_raw, "(?i)udp.*3544|teredo"), "Teredo — CRITICAL",
    match(_raw, "(?i)5efe|isatap"), "ISATAP — HIGH",
    match(_raw, "(?i)protocol.?41|ip-encap|ipv6inipv4") AND NOT match(_raw, "192\.88\.99\.1"), "Configured IPv6 tunnel (protocol 41) — verify",
    1=1, null())
| where isnotnull(tunnel_type)
| rex field=_raw "(?:src|source)\s*=?\s*(?<src_ip>[0-9.]+)"
| rex field=_raw "(?:dst|dest)\s*=?\s*(?<dst_ip>[0-9.]+)"
| stats count as events first(_time) as first_seen last(_time) as last_seen by src_ip, dst_ip, tunnel_type
| sort -events
```

## Visualization

(1) Table: detected tunnel traffic with type, source, destination, and severity. (2) Single-value: deprecated tunnel detections (should be 0). (3) Timechart: tunnel traffic volume by type. (4) Map: tunnel endpoint locations (especially concerning if external endpoints are in unexpected countries).

## Known False Positives

**Legitimate configured IPv6-in-IPv4 tunnels.** Protocol 41 is used for both deprecated (6to4) and legitimate (configured GRE-encapsulated, broker-based) IPv6 tunnels. The detection should distinguish between configured tunnels (known endpoints, documented) and shadow tunnels (unknown endpoints, undocumented).

**Teredo probing.** Windows may briefly probe Teredo during network setup even when disabled. Brief, low-volume UDP 3544 traffic may appear without an active Teredo tunnel.

**IPv6 tunnel brokers (Hurricane Electric).** Some organisations use IPv6 tunnel brokers like he.net for IPv6 connectivity. These use protocol 41 and are legitimate but should be documented and approved.

## References

- [RFC 7526 — Deprecating the Anycast Prefix for 6to4 Relay Routers (6to4 deprecated)](https://www.rfc-editor.org/rfc/rfc7526)
- [RFC 8190 — Updates to the Special-Purpose IP Address Registries (Teredo prefix deprecated)](https://www.rfc-editor.org/rfc/rfc8190)
- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6 (§5.1 — tunnel security)](https://csrc.nist.gov/publications/detail/sp/800-119/final)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3 — transition mechanism security)](https://www.rfc-editor.org/rfc/rfc9099)
