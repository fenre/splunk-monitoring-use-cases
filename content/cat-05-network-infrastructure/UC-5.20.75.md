<!-- AUTO-GENERATED from UC-5.20.75.json — DO NOT EDIT -->

---
id: "5.20.75"
title: "DAD Denial-of-Service Detection — Address Assignment Prevention"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.75 · DAD Denial-of-Service Detection — Address Assignment Prevention

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*Before moving into a new apartment (getting an IPv6 address), you knock on the door and ask 'Is anyone already living here?' If no one answers, you move in. But what if a troublemaker in the hallway always shouts 'Yes, someone's here!' every time anyone knocks? Nobody can ever move in. We watch for this pattern — when many different apartments are all reported as 'occupied' by the same troublemaker, we know they're lying and we kick them out.*

---

## Description

Detects Duplicate Address Detection (DAD) denial-of-service attacks where an attacker responds to DAD probes to prevent legitimate hosts from obtaining IPv6 addresses. A single DAD failure for one address is common and usually indicates a genuine duplicate. Multiple different addresses failing DAD on the same interface/VLAN in a short period is a definitive indicator of a DAD DoS attack.

## Value

DAD DoS completely prevents IPv6 connectivity for all affected hosts. Because modern operating systems attempt multiple addresses before giving up (SLAAC generates a new temporary address when the first fails DAD), the attack generates a burst of DAD failures across multiple addresses — a distinct pattern that separates attacks from legitimate duplicates. Detecting this pattern enables rapid response before all hosts on the VLAN lose IPv6 connectivity.

## Implementation

Monitor `%IPV6-4-DUPLICATE` syslog messages. Count distinct failed addresses per interface/VLAN per time window. Alert when multiple different addresses fail DAD within a short period.

## Detailed Implementation

### Prerequisites
- Syslog from routers and switches forwarded to Splunk.
- SISF with DAD proxy configured on access switches (provides additional DAD visibility).

### Step 1 — Configure data collection

**Syslog messages to monitor:**
```
%IPV6-4-DUPLICATE: Duplicate address 2001:db8::100 on Vlan100, sourced by aabb.cc00.dead
```
This message is generated when a host detects that its address is already in use. The `sourced by` field contains the MAC address of the device that claimed the address.

**SISF DAD events:**
```
%SISF-6-ENTRY_CREATED: Entry created IP=2001:db8::100 MAC=aabb.cc00.1234 IF=Gi1/0/5 VLAN=100 (DAD)
%SISF-4-PAK_DROP: Packet dropped IP=2001:db8::100 Reason=DAD_FAILED
```

**Verification:**
```spl
index=network sourcetype="cisco:ios" "%IPV6-4-DUPLICATE" earliest=-30d
| stats count by host
```
A small number of events (1-5 per month) is normal. Daily events or bursts indicate a problem.

### Step 2 — Create the search and alert

**DAD DoS detection (multi-address failure burst):**
```spl
index=network sourcetype="cisco:ios" "%IPV6-4-DUPLICATE" earliest=-15m
| rex field=_raw "(?:address|Address)\s+(?<dup_address>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:sourced by|MAC)\s+(?<claiming_mac>[0-9a-fA-F.]+)"
| rex field=_raw "(?:on|interface)\s+(?<vlan_interface>\S+)"
| stats dc(dup_address) as unique_failures dc(claiming_mac) as unique_claiming_macs values(dup_address) as failed_addresses values(claiming_mac) as attacker_macs count as total by host, vlan_interface
| where unique_failures > 3
| eval attack_confidence=case(
    unique_claiming_macs=1 AND unique_failures > 5, "DEFINITE — single MAC (" . mvindex(attacker_macs, 0) . ") is claiming all addresses",
    unique_failures > 10, "HIGH — too many different DAD failures to be coincidence",
    unique_failures > 3, "MEDIUM — investigate",
    1=1, "LOW")
| table _time, host, vlan_interface, unique_failures, attacker_macs, attack_confidence, failed_addresses
```
The strongest indicator is a single MAC address claiming multiple different IPv6 addresses — this is definitively malicious.

**Persistent single-address conflict (configuration error):**
```spl
index=network sourcetype="cisco:ios" "%IPV6-4-DUPLICATE" earliest=-7d
| rex field=_raw "(?:address|Address)\s+(?<dup_address>[0-9a-fA-F:.]+)"
| stats count as occurrences first(_time) as first last(_time) as last by dup_address, host
| where occurrences > 5
| eval issue="Persistent DAD failure for " . dup_address . " — " . occurrences . " failures in 7 days. Likely static address conflict."
```

### Step 3 — Validate
(a) **Attack simulation.** Use THC-IPv6 `dos-new-ip6` or Scapy to respond to DAD probes on a test VLAN. Verify the multi-address failure detection fires.

(b) **Legitimate duplicate.** Configure two devices with the same static IPv6 address. Verify only a single-address persistent conflict is detected, not an attack.

(c) **Threshold tuning.** In large VLANs (>1000 hosts), occasional DAD failures are more common. Adjust the threshold based on VLAN size.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — DAD Security"):
- Row 1 — Alert: VLANs under DAD DoS attack.
- Row 2 — Table: all DAD failures with claiming MAC, failed address, and attack confidence.
- Row 3 — Timechart: DAD failure rate per VLAN over 30 days.
- Row 4 — Table: persistent single-address conflicts (configuration errors to fix).

**Scheduling:** DAD DoS detection every 5 minutes. Persistent conflict weekly.

**Runbook:**
1. Multi-address DAD failure (attack): identify the claiming MAC address. Locate the switch port via `show mac address-table`. Shut the port. Investigate the device.
2. Single-address persistent conflict: identify both devices claiming the address. Reconfigure one to use a different address.
3. Post-attack: affected hosts should automatically retry DAD and obtain addresses once the attacker is removed. If not, restart the IPv6 stack on affected hosts.

### Step 5 — Troubleshooting

- **DAD delay** — DAD waits for RetransTimer (default 1 second) before concluding that the address is unique. Reducing this timer speeds up address assignment but reduces the window for detecting legitimate duplicates. Do not reduce below 500ms.

- **Optimistic DAD (RFC 4429)** — Some hosts use Optimistic DAD, which allows using the address immediately while DAD is in progress. Optimistic DAD reduces the impact of DAD DoS but does not eliminate it — the address is still deprecated if DAD fails.

- **SEND (Secure Neighbor Discovery)** — RFC 3971 defines SEND which cryptographically protects NDP including DAD. However, SEND has very limited deployment. CGA (Cryptographically Generated Addresses) provide some protection against DAD DoS by proving address ownership.

## SPL

```spl
index=network sourcetype="cisco:ios" "%IPV6-4-DUPLICATE" earliest=-1h
| rex field=_raw "(?:address|Address)\s+(?<dup_address>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:interface|IF)\s+(?<interface>\S+)"
| stats dc(dup_address) as unique_dups count as total_events by host, interface
| where unique_dups > 3
| eval severity=case(
    unique_dups > 10, "CRITICAL — DAD DoS attack: " . unique_dups . " different addresses failed DAD on " . interface . " — attacker is preventing all IPv6 address assignment",
    unique_dups > 5, "HIGH — multiple DAD failures: " . unique_dups . " addresses on " . interface,
    unique_dups > 3, "WARNING — elevated DAD failures on " . interface,
    1=1, "LOW")
| sort -unique_dups
```

## Visualization

(1) Alert table: interfaces with multiple DAD failures. (2) Timechart: DAD failure rate per VLAN. (3) Table: failed addresses with timestamps. (4) Single-value: count of VLANs under DAD DoS attack.

## Known False Positives

**Legitimate duplicate addresses.** Static address conflicts (two devices configured with the same address) produce a single DAD failure for one specific address. This is a configuration error, not an attack.

**VM cloning without address randomisation.** Cloned VMs that inherit the same SLAAC-generated address will fail DAD until one of them generates a new address. This produces a single duplicate per cloning event.

**SISF DAD proxy.** On switches with SISF DAD proxy enabled, DAD probes may be proxied, causing temporary DAD failures during proxy resolution. These are resolved within seconds and do not persist.

## References

- [RFC 4862 — IPv6 Stateless Address Autoconfiguration (§5.4 — DAD mechanism)](https://www.rfc-editor.org/rfc/rfc4862)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.3 — DAD DoS)](https://www.rfc-editor.org/rfc/rfc9099)
