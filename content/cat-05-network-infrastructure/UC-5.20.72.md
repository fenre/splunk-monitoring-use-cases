<!-- AUTO-GENERATED from UC-5.20.72.json — DO NOT EDIT -->

---
id: "5.20.72"
title: "NDP Cache Poisoning and IPv6 Spoofing Attack Detection"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.20.72 · NDP Cache Poisoning and IPv6 Spoofing Attack Detection

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*In our building, every resident has a name tag (IPv6 address) and a face (MAC address). If someone puts on a fake name tag that belongs to another resident, the security system at the front desk catches this — it knows what face should go with what name. We get an immediate alarm when someone tries to impersonate another resident, because they could intercept that person's mail and packages.*

---

## Description

Detects NDP cache poisoning attacks — the IPv6 equivalent of ARP poisoning — using SISF security events and NDP traffic analysis. An attacker sends forged Neighbor Advertisement messages to redirect traffic through their host, enabling man-in-the-middle attacks. Cisco SISF provides definitive detection through IP_THEFT and MAC_THEFT events. On non-SISF platforms, detection relies on rapid MAC-to-IPv6 binding changes in NDP cache logs.

## Value

NDP cache poisoning enables the same devastating MITM attacks as ARP poisoning — credential theft, session hijacking, DNS manipulation — but over IPv6. Because many security monitoring tools focus on ARP, NDP poisoning often goes undetected even in environments with mature ARP monitoring. SISF IP_THEFT events are definitive indicators of active attacks and require immediate response.

## Implementation

Monitor SISF security events for IP_THEFT and MAC_THEFT. Track NDP cache binding changes for rapid MAC address flapping. Correlate with RA spoofing and Redirect abuse detections for comprehensive NDP attack visibility.

## Detailed Implementation

### Prerequisites
- SISF (device-tracking) enabled on Cisco access switches with security level 'guard' for definitive detection.
- Alternatively, NDP cache logging via periodic polling or Zeek sensor for non-Cisco environments.
- Baseline of normal NDP cache binding change rates per VLAN.

### Step 1 — Configure data collection

**Cisco IOS-XE — SISF configuration for attack detection:**
```
device-tracking policy DT-POLICY
 security-level guard
 tracking enable

vlan configuration 100
 device-tracking attach-policy DT-POLICY
```
With `security-level guard`, SISF validates all NDP messages and generates `IP_THEFT` / `MAC_THEFT` events when spoofing is detected.

**Syslog messages to monitor:**
```
%SISF-4-IP_THEFT: IP Theft IP=2001:db8::100 MAC=0000.0c07.ac01 IF=Gi1/0/5 VLAN=100 Binding=2001:db8::100 MAC=aabb.cc00.1234 IF=Gi1/0/10 VLAN=100
%SISF-4-MAC_THEFT: MAC Theft MAC=aabb.cc00.1234 IP=2001:db8::100 IF=Gi1/0/5 VLAN=100 Existing-IF=Gi1/0/10
```

**Zeek/Corelight — NDP analysis (non-Cisco):**
Zeek does not parse NDP by default. Deploy the `zeek-ndi` plugin or use the `weird.log` for NDP anomalies:
```
# Zeek weird events related to NDP
index=network sourcetype="zeek:weird" ("unsolicited_neighbor_advertisement" OR "na_override_without_solicitation")
```

**NDP cache polling (fallback for platforms without inline security):**
```
# Poll NDP cache every 30 seconds via scripted input
show ipv6 neighbors
```
Store historical NDP cache snapshots and detect MAC changes for the same IPv6 address.

**Verification:**
```spl
index=network sourcetype="cisco:ios" "%SISF" earliest=-7d
| stats count by host
```

### Step 2 — Create the search and alert

**SISF attack detection (definitive — Cisco):**
```spl
index=network sourcetype="cisco:ios" ("%SISF-4-IP_THEFT" OR "%SISF-4-MAC_THEFT") earliest=-15m
| rex field=_raw "IP=(?<victim_ip>[0-9a-fA-F:.]+)"
| rex field=_raw "MAC=(?<attacker_mac>[0-9a-fA-F.]+)"
| rex field=_raw "IF=(?<attacker_port>\S+)"
| rex field=_raw "Binding=(?<legitimate_ip>[0-9a-fA-F:.]+).*MAC=(?<legitimate_mac>[0-9a-fA-F.]+).*IF=(?<legitimate_port>\S+)"
| eval alert="NDP SPOOFING ATTACK: " . attacker_mac . " on " . attacker_port . " is claiming IPv6 address " . victim_ip . " which belongs to " . coalesce(legitimate_mac, "unknown") . " on " . coalesce(legitimate_port, "unknown")
| table _time, host, victim_ip, attacker_mac, attacker_port, legitimate_mac, legitimate_port, alert
```
Trigger: any event. IP_THEFT is always an attack indicator (after excluding known VM migration and FHRP patterns).

**Rapid MAC flapping detection (platform-independent):**
```spl
index=network (sourcetype="cisco:ios" "%SISF-6-ENTRY_UPDATED") earliest=-15m
| rex field=_raw "IP=(?<ipv6_addr>[0-9a-fA-F:.]+)"
| rex field=_raw "MAC=(?<mac>[0-9a-fA-F.]+)"
| stats dc(mac) as mac_count values(mac) as macs count as changes by ipv6_addr, host
| where mac_count > 2
| eval alert="MAC flapping for " . ipv6_addr . ": " . mac_count . " different MACs (" . mvjoin(macs, ", ") . ") in 15 minutes — possible NDP poisoning or VM migration"
```

### Step 3 — Validate
(a) **SISF validation.** On a test VLAN with SISF enabled, send a spoofed NA from a test host. Verify the IP_THEFT event is generated and the alert fires.

(b) **VM migration exclusion.** Perform a planned VM migration. Verify the event is generated but correctly identified as a migration (known MAC pair).

(c) **MAC flap threshold.** Verify that normal DHCP lease reassignment (one MAC change per address per lease period) does not trigger the rapid flapping alert.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — NDP Security"):
- Row 1 — CRITICAL alerts: IP_THEFT and MAC_THEFT events.
- Row 2 — Table: all NDP security events with attacker and victim details.
- Row 3 — Timechart: NDP security event rate.
- Row 4 — Switch port heat map: which ports generate the most NDP security events.

**Scheduling:** IP_THEFT/MAC_THEFT real-time alert. MAC flapping every 5 minutes.

**Runbook:**
1. IP_THEFT confirmed: IMMEDIATE — shut down the attacker's switch port (`shutdown` interface). Investigate the attached device. Check for THC-IPv6, Scapy, or similar tools.
2. MAC_THEFT confirmed: same as IP_THEFT — isolate the port.
3. Rapid MAC flapping without IP_THEFT: investigate. Could be VM migration (check hypervisor logs), FHRP reconfiguration, or slow NDP poisoning attempt.
4. Post-incident: verify all affected hosts have correct NDP cache entries. Consider enabling SEND (Secure Neighbor Discovery) for critical infrastructure.

### Step 5 — Troubleshooting

- **SISF false positives from VM migration** — Create a SISF policy exception for known hypervisor ports. Use `device-tracking policy` with `limit address-count` appropriate for hypervisor ports.

- **SISF binding table capacity** — SISF maintains a binding table with limited capacity per switch. If the table is full, new bindings are not created and some attacks may not be detected. Monitor `show device-tracking database` for capacity.

- **Platform support** — SISF `security-level guard` is available on Cisco IOS-XE 16.x+ on Catalyst 9000 series. Older platforms support basic device-tracking without the guard security level. Verify platform capability.

## SPL

```spl
index=network sourcetype="cisco:ios" ("%SISF-4-IP_THEFT" OR "%SISF-4-MAC_THEFT" OR "%SISF-6-ENTRY_UPDATED") earliest=-1h
| rex field=_raw "IP=(?<ipv6_addr>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:MAC|mac)=(?<mac_addr>[0-9a-fA-F.]+)"
| rex field=_raw "(?:port|Port|IF)\s*=?\s*(?<port>\S+)"
| eval severity=case(
    match(_raw, "IP_THEFT"), "CRITICAL — NDP spoofing: someone is claiming another host's IPv6 address",
    match(_raw, "MAC_THEFT"), "CRITICAL — MAC spoofing: someone is impersonating another host's MAC address",
    match(_raw, "ENTRY_UPDATED") AND match(_raw, "Binding Changed"), "WARNING — NDP cache binding change",
    1=1, "INFO")
| stats count as events first(_time) as first_seen last(_time) as last_seen by host, ipv6_addr, mac_addr, port, severity
| sort -events
```

## Visualization

(1) Alert table: IP_THEFT and MAC_THEFT events with source details. (2) Timechart: NDP security event volume. (3) Network graph: relationships between spoofed addresses, real hosts, and attacker MACs. (4) Map: switch ports involved in spoofing events.

## Known False Positives

**VM migration.** When a virtual machine migrates between hypervisors, the same IPv6 address appears on a different port/MAC. This triggers SISF IP_THEFT for the migration duration. Configure SISF to allow known VM migration MAC pairs.

**VRRP/HSRP failover.** FHRP failover causes the virtual IPv6 address to move between physical hosts, triggering binding changes. Configure SISF to recognise FHRP virtual MACs.

**LACP/port-channel reconfiguration.** When link aggregation reconfigures, the same MAC may appear on different physical ports temporarily.

**DHCP lease reassignment.** When a DHCPv6 lease expires and is reassigned to a different host, the IPv6 address moves to a new MAC. This is legitimate but slower than attack patterns.

## References

- [RFC 4861 — Neighbor Discovery for IP version 6 (NDP specification)](https://www.rfc-editor.org/rfc/rfc4861)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3 — NDP security)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 3756 — IPv6 Neighbor Discovery (ND) Trust Models and Threats](https://www.rfc-editor.org/rfc/rfc3756)
