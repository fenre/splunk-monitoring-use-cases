<!-- AUTO-GENERATED from UC-5.20.33.json — DO NOT EDIT -->

---
id: "5.20.33"
title: "IPv6 Source Guard Violation Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.33 · IPv6 Source Guard Violation Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Every device on the network has a verified identity — like a photo ID. Source Guard checks that every message comes from a device with a valid ID. If someone tries to send a message using a fake identity, the switch blocks it and reports the attempt.*

---

## Description

Monitors IPv6 Source Guard violations where packets are dropped because the source IPv6 address is not in the switch's SISF binding table. Source Guard is the IPv6 equivalent of IP Source Guard in IPv4 — it prevents hosts from using IPv6 addresses that have not been validated by SISF. This is a critical anti-spoofing control at the access layer.

## Value

IPv6 Source Guard prevents source address spoofing at the first hop. Without it, any host can send packets with any IPv6 source address, enabling denial-of-service amplification, session hijacking, and forensic evasion. Monitoring violations identifies both active spoofing attempts and SISF binding table gaps that could block legitimate traffic.

## Implementation

Collect SISF Source Guard violation events from syslog. Parse spoofed source address, port, and MAC. Alert on high violation rates (possible attack) and investigate recurring violations from the same port (possible binding gap).

## Detailed Implementation

### Prerequisites
- SISF in `guard` mode with source guard enabled.
- Syslog forwarding at severity 4.

### Step 1 — Configure data collection

**Enable IPv6 Source Guard on Cisco IOS-XE:**
```
device-tracking policy DT_GUARD_SG
 security-level guard
 tracking enable
!
ipv6 source-guard policy SG_POLICY
!
interface range GigabitEthernet1/0/1 - 48
 device-tracking attach-policy DT_GUARD_SG
 ipv6 source-guard attach-policy SG_POLICY
```

Verify bindings:
```
show device-tracking database
  Network Layer Address     Link Layer Address  Interface  vlan  prlvl  age    state      Time left
  2001:db8:100::a           aabb.ccdd.eeff      Gi1/0/5    100   0005   30s    REACHABLE  45 s
```

**Verification in Splunk:**
```spl
index=network sourcetype="cisco:ios" ("Source guard" OR "IPV6SG") earliest=-7d
| stats count by host
```

### Step 2 — Create the search and alert

**Primary alert — Source Guard violations:**
```spl
index=network sourcetype="cisco:ios" ("%SISF-4-PAK_DROP" "Source guard") OR "%IPV6SG-4-DENY" earliest=-1h
| rex field=_raw "IPv6 SRC:\s*(?<spoofed_src>[0-9a-fA-F:]+)"
| rex field=_raw "port\s+(?<port>\S+)"
| stats count as violations dc(spoofed_src) as unique_sources values(spoofed_src) as source_list by host, port
| eval severity=case(
    violations > 100, "CRITICAL — possible source spoofing attack",
    violations > 10, "WARNING — recurring violations",
    1=1, "INFO — occasional violations")
| where severity!="INFO"
| table host, port, violations, unique_sources, source_list, severity
```

**Binding gap detection:**
```spl
index=network sourcetype="cisco:ios" "%SISF-4-PAK_DROP" "Source guard" earliest=-24h
| rex field=_raw "port\s+(?<port>\S+)"
| stats count as violations earliest(_time) as first_seen latest(_time) as last_seen by host, port
| eval duration_hours=round((last_seen - first_seen) / 3600, 1)
| where duration_hours > 1
| eval assessment="PERSISTENT — likely binding gap, not attack"
```
Persistent violations from the same port over hours indicate a binding table gap (static address not learned), not an attack (which would be bursty).

### Step 3 — Validate
(a) **Spoofing test (lab).** Configure Source Guard, then use a packet generator to send packets with a source address NOT in the binding table. Verify PAK_DROP with Source guard reason.

(b) **Binding gap test.** Configure a host with a static IPv6 address. Verify it is learned by SISF. If not, add a static binding.

### Step 4 — Operationalize

**Dashboard:** Integrate into the UC-5.20.31 SISF enforcement dashboard as a separate row for Source Guard violations.

**Runbook:**
1. High violation rate from single port → investigate for source spoofing, shut port if attack confirmed.
2. Persistent low-rate violations → check SISF binding table for missing entries, add static bindings for statically-addressed hosts.

### Step 5 — Troubleshooting

- **All traffic dropped after enabling Source Guard** — The binding table may be empty. SISF needs time to learn bindings via NDP/DHCPv6. Start with `inspect` mode (log only) before switching to `guard` (enforce).

- **Source Guard drops packets from router SVI** — Router interfaces should not have Source Guard applied. Only access ports (user-facing) need Source Guard.

## SPL

```spl
index=network sourcetype="cisco:ios" ("%SISF-4-PAK_DROP" "Source guard") OR "%IPV6SG-4-DENY"
| rex field=_raw "IPv6 SRC:\s*(?<spoofed_src>[0-9a-fA-F:]+)"
| rex field=_raw "port\s+(?<port>\S+)"
| rex field=_raw "MAC=(?<src_mac>[0-9a-fA-F.]+)"
| stats count as violations dc(spoofed_src) as unique_sources values(spoofed_src) as sources by host, port
| sort -violations
```

## Visualization

(1) Table: Source Guard violations by switch, port, spoofed source. (2) Timechart: violation rate over time. (3) Single-value: total violations in 24h.

## Known False Positives

**Boot-time race condition.** When a host boots, it may send packets before SISF learns its binding via NDP/DHCPv6. The first few packets are dropped until SISF completes the binding. This is transient (seconds) and resolves automatically.

**Static addresses not in binding table.** Hosts with manually configured IPv6 addresses that are not learned via NDP or DHCPv6 may not appear in the SISF binding table. Solution: add static bindings or configure SISF to learn from data traffic.

**Privacy extension address rotation.** When a host generates a new privacy extension address, there may be a brief window where SISF has not yet learned the new address. Packets sourced from the new address are dropped until the binding is established.

## References

- [RFC 7039 — Source Address Validation Improvement (SAVI) Framework](https://www.rfc-editor.org/rfc/rfc7039)
- [Cisco SISF — IPv6 Source Guard configuration and PAK_DROP events](https://www.cisco.com/c/en/us/)
