<!-- AUTO-GENERATED from UC-5.20.20.json — DO NOT EDIT -->

---
id: "5.20.20"
title: "NDP Cache Anomalies and Poisoning Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.20 · NDP Cache Anomalies and Poisoning Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*Imagine someone in your neighbourhood changes the name on your mailbox to redirect your mail to their house. They can read all your letters before forwarding them. We watch for this kind of identity switching on the network — if a device's 'name tag' suddenly changes to point to a different physical device, we sound the alarm.*

---

## Description

Detects NDP cache poisoning attacks by identifying rapid MAC address changes for the same IPv6 address in the NDP cache. NDP poisoning is functionally identical to ARP poisoning in IPv4: the attacker sends unsolicited Neighbor Advertisements with the Override (O) flag set, convincing the target device that the attacker's MAC address owns the victim's IPv6 address. All traffic destined for the victim is then redirected to the attacker for interception. Unlike ARP, IPv6 NDP also uses Neighbor Solicitation/Advertisement for Duplicate Address Detection (DAD) and Router Discovery, so NDP poisoning can also disrupt address assignment and default gateway resolution. This use case detects poisoning by comparing consecutive SNMP polls of the NDP cache: a MAC change for the same IPv6 address within 300 seconds is anomalous; within 60 seconds is almost certainly an active attack.

## Value

NDP poisoning is the primary layer-2 attack vector in IPv6 networks. Unlike IPv4, where ARP poisoning defences are mature and widely deployed (Dynamic ARP Inspection), NDP poisoning defences (RA Guard, SISF) are often not configured — especially on networks where IPv6 was enabled unintentionally. An attacker who successfully poisons the NDP cache can intercept all traffic, steal credentials, inject malicious responses, or redirect DNS. This use case provides a network-layer detection capability that works even when first-hop security features are not deployed, complementing SISF-based detections (UC-5.20.32) with an independent, polling-based signal.

## Implementation

Poll the NDP cache from every Layer 3 device at 30-second to 5-minute intervals via SNMP. Use `streamstats` to compare consecutive MAC bindings for each IPv6 address. A MAC change within 60 seconds triggers a CRITICAL alert; within 300 seconds triggers a WARNING. Cross-reference with SISF events if available.

## Detailed Implementation

### Prerequisites
- NDP cache historical logging (UC-5.20.16) must be operational — this use case requires consecutive SNMP polls of the NDP cache to detect changes.
- Poll interval of 5 minutes or less. For high-security environments, 30-second intervals (per RFC 9099 §2.6.1.4) provide faster detection but higher data volume.
- SISF (Switch Integrated Security Features) events are a valuable complementary signal but are not required — this use case provides detection even without first-hop security.
- Suppression lookup for known VM migration prefixes, VRRP/HSRP VIPs, and bonded NIC MACs.

### Step 1 — Configure data collection

**NDP cache polling (primary signal):**
Follow UC-5.20.16 for SC4SNMP or scripted SNMP polling of `ipv6NetToMediaTable` at 5-minute intervals.

**SISF syslog (complementary signal):**
On Cisco IOS-XE switches with SISF enabled:
```
device-tracking policy DT_POLICY
 security-level guard
 tracking enable
 logging
!
interface range GigabitEthernet1/0/1 - 48
 device-tracking attach-policy DT_POLICY
```
SISF generates:
- `%SISF-4-IP_THEFT` — a new MAC claims an IP already bound to a different MAC.
- `%SISF-4-MAC_THEFT` — a new port claims a MAC already bound to a different port.
- `%SISF-4-PAK_DROP` with `Reason:IP theft` — the offending packet was dropped.

These events are forwarded to Splunk via the Cisco IOS TA with `sourcetype=cisco:ios`.

**Verification:**
```spl
index=network (sourcetype="ndp:cache" OR (sourcetype="cisco:ios" ("IP_THEFT" OR "MAC_THEFT"))) earliest=-24h
| stats count by sourcetype
```
Expected: ndp:cache events from all polled devices, and optionally SISF events from switches.

### Step 2 — Create the search and alert

**Primary detection — MAC change in NDP cache (polling-based):**
```spl
index=network sourcetype="ndp:cache" earliest=-1h
| where NOT match(ipv6_address, "^fe80:") AND NOT match(ipv6_address, "^ff")
| sort 0 ipv6_address, _time
| streamstats current=f last(mac_address) as prev_mac last(_time) as prev_time by ipv6_address
| where isnotnull(prev_mac) AND mac_address!=prev_mac
| eval time_delta_sec=round(_time - prev_time)
| where time_delta_sec < 300
| lookup ndp_anomaly_suppressions.csv ipv6_address OUTPUT suppress
| where isnull(suppress) OR suppress!="true"
| eval severity=case(
    time_delta_sec < 60, "CRITICAL",
    time_delta_sec < 300, "WARNING",
    1=1, "INFO")
| table _time, host, interface, ipv6_address, prev_mac, mac_address, time_delta_sec, severity
```

**Understanding this SPL:**
- Filters out link-local (fe80::) and multicast (ff::) to focus on global unicast addresses.
- `streamstats` with `current=f` provides the previous MAC for each IPv6 address, enabling comparison.
- Time delta < 60 seconds is almost certainly an attack — legitimate MAC changes (NIC replacement, VM migration) take longer.
- Suppression lookup allows whitelisting known VM migration prefixes and VRRP VIPs.

**Complementary detection — SISF IP_THEFT events (real-time, switch-based):**
```spl
index=network sourcetype="cisco:ios" ("SISF-4-IP_THEFT" OR "SISF-4-MAC_THEFT")
| rex field=_raw "IP=(?<stolen_ip>[0-9a-fA-F:]+)\s+.*New\s+MAC=(?<attacker_mac>[0-9a-fA-F.]+).*Old\s+MAC=(?<victim_mac>[0-9a-fA-F.]+)"
| table _time, host, stolen_ip, victim_mac, attacker_mac
```
SISF events provide real-time detection (no polling delay) but require SISF to be configured on the switch.

**Combined correlation (both signals):**
```spl
(index=network sourcetype="ndp:cache" earliest=-1h
  | sort 0 ipv6_address, _time
  | streamstats current=f last(mac_address) as prev_mac by ipv6_address
  | where isnotnull(prev_mac) AND mac_address!=prev_mac
  | eval detection_source="NDP_POLL"
  | rename ipv6_address as target_ip, mac_address as attacker_mac, prev_mac as victim_mac)
OR
(index=network sourcetype="cisco:ios" ("SISF-4-IP_THEFT")
  | rex field=_raw "IP=(?<target_ip>[0-9a-fA-F:]+)\s+.*New\s+MAC=(?<attacker_mac>[0-9a-fA-F.]+).*Old\s+MAC=(?<victim_mac>[0-9a-fA-F.]+)"
  | eval detection_source="SISF")
| stats values(detection_source) as sources count as detections by target_ip, attacker_mac, victim_mac
| eval confidence=if(mvcount(sources) > 1, "HIGH — confirmed by multiple sources", "MEDIUM — single source")
| sort -confidence, -detections
```

### Step 3 — Validate
(a) **Controlled poisoning test (lab only).** On a lab network, use THC-IPv6 `na6` or `parasite6` to send a spoofed NA for a test host's IPv6 address:
```bash
sudo na6 -i eth0 -s <attacker_linklocal> -d ff02::1 \
  -S <target_global_ipv6> -E <attacker_mac> -o
```
The `-o` flag sets the Override bit. The next NDP cache poll should show the MAC change for the target's IPv6 address, triggering a CRITICAL alert.

(b) **SISF test.** On a lab switch with SISF in `guard` mode, connect a second host configured with the same IPv6 address as an existing host. SISF should generate `IP_THEFT` and `PAK_DROP` events. Verify they appear in Splunk.

(c) **False positive validation.** Trigger a VM migration (vMotion) of a test VM. Verify the MAC change is detected but suppressed by the VM prefix suppression lookup.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — NDP Cache Security"):
- Row 1 — Single-value: active CRITICAL alerts, total anomalies (24h).
- Row 2 — Timeline: NDP cache anomaly events on a timeline — clustered events indicate an active attack campaign.
- Row 3 — Table: anomaly details with target IP, victim MAC, attacker MAC, detection source, and confidence.
- Row 4 — Switch port mapping: if anomalies correlate with SISF, show the physical switch port where the attacker is connected.

**Scheduling:** SNMP-poll-based detection runs every 5 minutes. SISF-based detection runs in real-time. Combined correlation runs every 15 minutes.

**Runbook:**
1. CRITICAL NDP poisoning detected:
   a. Identify the attacker MAC and locate the switch port: `show mac address-table address <attacker_mac>`.
   b. Shut the port: `interface <port>` → `shutdown`.
   c. Investigate: is the attacker MAC a known device? Check asset inventory.
   d. Clear the poisoned NDP entry: `clear ipv6 neighbors <victim_ip>` on the affected router.
   e. Deploy SISF if not already configured (UC-5.20.29-36).
2. WARNING (rapid MAC change, 60-300s):
   a. Check if this correlates with a known operational event (VM migration, NIC failover).
   b. If no operational context, escalate to security team.

### Step 5 — Troubleshooting

- **High false positive rate from VM environments** — Filter VM MAC prefixes (00:50:56 for VMware, 00:15:5D for Hyper-V, 52:54:00 for KVM/QEMU) from the detection search, or add them to the suppression lookup.

- **Polling interval too coarse for detection** — At 5-minute polling, an attack that starts and stops within 5 minutes may be missed (the poisoned entry may revert before the next poll). For high-security environments, reduce to 30-second polling or rely on real-time SISF events.

- **Link-local poisoning not detected** — The primary search filters out fe80:: addresses because link-local MAC changes are common during router reboots. However, link-local poisoning targeting the default gateway is a high-impact attack. Create a separate search specifically for the gateway's link-local address MAC change.

- **SISF PAK_DROP from legitimate HA/VM** — Cisco bug CSCvx75602 causes SISF to generate false IP_THEFT events during certain HA failover scenarios. Check the Cisco bug navigator for your IOS-XE version and apply the recommended workaround.

## SPL

```spl
index=network sourcetype="ndp:cache" earliest=-1h
| sort 0 ipv6_address, _time
| streamstats current=f last(mac_address) as prev_mac last(_time) as prev_time by ipv6_address
| where isnotnull(prev_mac) AND mac_address!=prev_mac
| eval time_delta_sec=_time - prev_time
| where time_delta_sec < 300
| eval severity=case(
    time_delta_sec < 60, "CRITICAL — likely poisoning",
    time_delta_sec < 300, "WARNING — rapid MAC change",
    1=1, "INFO")
| table _time, host, interface, ipv6_address, prev_mac, mac_address, time_delta_sec, severity
```

## Visualization

(1) Table: NDP cache anomalies with timestamp, device, IPv6 address, previous MAC, new MAC, time delta, and severity. (2) Single-value: active CRITICAL poisoning alerts. (3) Timechart: NDP anomaly events over time — a burst of events indicates an active attack. (4) Map/topology: which switch/interface the anomalies are occurring on — helps localise the attacker's physical location.

## Known False Positives

**VM live migration (vMotion/KVM live migration).** When a virtual machine migrates between hypervisors, its IPv6 address stays the same but the underlying MAC address changes to the new host's vNIC. This produces a legitimate rapid MAC change. Suppress known VM prefixes or hypervisor MAC OUIs (e.g., VMware 00:50:56, Microsoft Hyper-V 00:15:5D).

**NIC failover / bonding.** Server NIC teaming or bonding failover swaps the active MAC while keeping the same IPv6 address. The time delta depends on the failover method (active-backup: instant; LACP: negotiated). These events are rare and should correlate with server health events.

**VRRP/HSRP active-standby transition.** During a gateway failover, the IPv6 VIP transitions from one physical MAC to another (or from virtual MAC on the old active to virtual MAC on the new active). The MAC change for the VIP is expected and should complete within seconds. Filter known VRRP/HSRP VIP addresses.

**DHCP lease expiry and reassignment.** If a DHCPv6 address is released and immediately reassigned to a different client, the MAC association changes. The time delta will typically be > 300 seconds (lease expiry + new assignment).

## References

- [RFC 4861 — Neighbor Discovery for IP version 6 (Neighbor Advertisement Override flag, NDP cache update rules)](https://www.rfc-editor.org/rfc/rfc4861)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3 — NDP security, cache poisoning risks)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 3756 — IPv6 Neighbor Discovery (ND) Trust Models and Threats (formal threat model for NDP attacks)](https://www.rfc-editor.org/rfc/rfc3756)
- [THC-IPv6 Attack Toolkit — parasite6 and na6 NDP poisoning tools](https://github.com/vanhauser-thc/thc-ipv6)
