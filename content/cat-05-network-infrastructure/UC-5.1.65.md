<!-- AUTO-GENERATED from UC-5.1.65.json — DO NOT EDIT -->

---
id: "5.1.65"
title: "NDP Cache Anomalies and Poisoning Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.1.65 · NDP Cache Anomalies and Poisoning Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch for someone pretending to be another device on our IPv6 network, like an impostor answering to your neighbor's name to intercept their mail. When a device's network identity suddenly moves to a different location, our switches catch the change and alert us before any data is stolen.*

---

## Description

Detects NDP cache anomalies including IPv6 address theft (IP moved to different MAC), MAC theft (MAC moved to different port), and SISF policy violations. This is the IPv6 counterpart to ARP/MAC table anomaly monitoring — NDP poisoning enables the same man-in-the-middle and traffic interception attacks as ARP poisoning but using Neighbor Advertisement spoofing.

## Value

NDP cache poisoning is the IPv6 equivalent of ARP cache poisoning and is trivially easy to execute with tools like THC-IPv6 (`parasite6`). An attacker sends unsolicited Neighbor Advertisements with the Override flag to redirect traffic through their machine. Without SISF/FHS monitoring, these attacks are invisible because NDP operates silently at Layer 2. This UC catches the attack at the switch level where SISF detects the binding table violation.

## Implementation

Enable SISF on Cisco Catalyst switches. Monitor for IP_THEFT, MAC_THEFT, and PAK_DROP events in syslog. Correlate with Zeek/Suricata for deeper NDP packet analysis.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst switches running IOS-XE 16.x+ or IOS 15.2(2)E+ with SISF support.
- SISF policy configured and applied to access VLANs:
```
device-tracking policy SISF_POLICY
 security-level guard
 device-role node
!
vlan configuration 10-100
 device-tracking attach-policy SISF_POLICY
```
- Syslog from switches to Splunk via `TA-cisco_ios`.
- For deeper analysis: Zeek or Suricata sensor with ICMPv6 visibility.

### Step 1 — Configure SISF data collection
Verify SISF events are arriving:
```spl
index=network sourcetype="cisco:ios" facility="SISF" earliest=-1h | stats count by mnemonic
```
Expect to see PAK_DROP, IP_THEFT, MAC_THEFT events. If zero events, verify: (a) SISF policy is applied to VLANs, (b) syslog severity includes level 4 (`logging trap notifications` or lower), (c) the SISF security-level is `guard` (not `glean` which only learns without enforcement).

### Step 2 — Create monitoring and alerting
The primary search (above) classifies SISF events by severity. Additionally, monitor for patterns:

**Rapid MAC flapping (NDP poisoning indicator):**
```spl
index=network sourcetype="cisco:ios" facility="SISF" mnemonic="IP_THEFT" earliest=-15m
| stats count as flap_count dc(mac) as mac_count by stolen_ip, vlan
| where flap_count > 3 OR mac_count > 2
```

**Unsolicited NA detection via Zeek:**
```spl
index=network sourcetype="zeek:conn" service="icmp" id.resp_p=136 earliest=-1h
| stats count by id.orig_h
| where count > 100
```

Thresholds from RFC 6583 and operational experience:
- >100 NAs/sec from single source: likely NDP poisoning
- >1000 NS messages in 1-minute window: NS flood
- >5 IP_THEFT events for same IP in 15 minutes: active MITM

### Step 3 — Validate
(a) In a lab, run `parasite6 eth0` from THC-IPv6 toolkit. Verify SISF generates IP_THEFT events.
(b) Compare SISF binding table (`show device-tracking database`) with NDP cache (`show ipv6 neighbors`).
(c) Verify alert fires for the simulated attack.

### Step 4 — Operationalize
Dashboard ("IPv6 NDP Security"):
- Row 1 — Single-value tiles: IP_THEFT events (red if >0), MAC_THEFT events (red if >0), PAK_DROP rate.
- Row 2 — Table: recent theft events with IP, MAC, interface, VLAN, severity.
- Row 3 — Timechart: SISF events over 24h by event type.
- Drilldown: click event → show full SISF log context.

Alerting:
- IP_THEFT or MAC_THEFT: Immediate page to network security. Include affected VLAN, interface, and MAC for rapid port shutdown.
- PAK_DROP > 50/hour: Investigation priority — may indicate attack being mitigated or false positive from HA/VM environments.

### Step 5 — Troubleshooting
- **False positive: VM migration / HA failover.** CSCvx75602: SISF PAK_DROP blocks legitimate traffic in HA/VM environments where multiple IPs share one MAC. Workaround: Configure SISF to allow address overlap: `device-tracking policy SISF_POLICY` → `limit address-count 0` (no limit) for VM-hosting VLANs.
- **False positive: Wireless roaming.** Clients roaming between APs may trigger MAC_THEFT as the MAC appears on a different switch port. Configure the policy with `trusted-port` on AP uplinks.
- **No SISF events but NDP attacks visible on Zeek.** SISF may not be deployed on all switches. Run `show device-tracking policies` fleet-wide to identify gaps (see UC-5.20.142 for FHS coverage audit).

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-4h
  facility="SISF" mnemonic IN ("IP_THEFT", "MAC_THEFT", "PAK_DROP", "MAC_AND_IP_THEFT")
| rex field=_raw "IP=(?<stolen_ip>[0-9a-fA-F:.]+).*VLAN=(?<vlan>\d+).*MAC=(?<mac>[0-9a-fA-F.]+).*IF=(?<interface>\S+)"
| eval event_type=case(
    mnemonic="IP_THEFT", "IP moved to different MAC/port",
    mnemonic="MAC_THEFT", "MAC moved to different port",
    mnemonic="MAC_AND_IP_THEFT", "Both MAC and IP moved",
    mnemonic="PAK_DROP", "Packet dropped by SISF policy",
    1=1, mnemonic)
| stats count as events earliest(_time) as first_seen latest(_time) as last_seen by host, event_type, stolen_ip, mac, interface, vlan
| eval severity=case(
    event_type="MAC_AND_IP_THEFT", "CRITICAL",
    event_type="IP_THEFT" AND events > 5, "HIGH",
    event_type="MAC_THEFT", "HIGH",
    event_type="PAK_DROP" AND events > 50, "MEDIUM",
    1=1, "LOW")
| where severity IN ("CRITICAL", "HIGH", "MEDIUM")
| sort -events
```

## Visualization

(1) Single-value tiles: IP_THEFT count (red >0), MAC_THEFT count (red >0). (2) Table: recent events with severity, IP, MAC, interface, VLAN. (3) Timechart: SISF events over 24h. (4) Map: affected switches (if site data available).

## Known False Positives

**VM migration and HA failover.** CSCvx75602: SISF generates PAK_DROP and IP_THEFT events when VMs migrate between hypervisors because the same IPv6 address appears on a different switch port. This is the #1 source of SISF false positives. Distinguish by correlating with vCenter/HyperV migration events.

**Wireless client roaming.** Clients roaming between access points appear as MAC_THEFT when the MAC moves to a different switch port (AP uplink). Configure `trusted-port` on AP-facing ports to suppress.

**Dual-homed hosts.** Hosts with multiple NICs on the same VLAN may trigger IP_THEFT. Verify with `show device-tracking database` that the binding table accurately reflects the host's configuration.

## References

- [Cisco — IPv6 First-Hop Security (SISF)](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/ipv6_fhsec/configuration/xe-3s/ip6f-xe-3s-book.html)
- [RFC 4861 — Neighbor Discovery for IPv6](https://www.rfc-editor.org/rfc/rfc4861)
- [THC-IPv6 Attack Toolkit (parasite6, fake_router6)](https://github.com/vanhauser-thc/thc-ipv6)
