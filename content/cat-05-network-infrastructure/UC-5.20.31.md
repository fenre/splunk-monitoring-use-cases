<!-- AUTO-GENERATED from UC-5.20.31.json — DO NOT EDIT -->

---
id: "5.20.31"
title: "SISF Binding Table Health and PAK_DROP Event Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.20.31 · SISF Binding Table Health and PAK_DROP Event Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Security, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*The security system at each network switch keeps a list of who is allowed to be where. When it blocks someone — either because they are genuinely suspicious or because the list is full — it writes a report. We read every report to make sure the security system is blocking real threats and not accidentally locking out legitimate users.*

---

## Description

Monitors SISF PAK_DROP events across all switches to track how the IPv6 first-hop security enforcement is performing. Every PAK_DROP represents a packet that was blocked by SISF — either a legitimate security enforcement (rogue RA blocked, IP theft prevented) or a potential misconfiguration (legitimate traffic dropped due to binding table limits, timing races, or known bugs). By categorising PAK_DROP events by reason, this use case distinguishes security-relevant drops (RA guard, IP theft) from operational issues (limit reached, not enough resources) and helps tune SISF deployment to minimise false drops while maintaining security enforcement.

## Value

SISF is powerful but can cause operational disruption if not tuned correctly. A common scenario: SISF is deployed in guard mode, the binding table fills up, and new hosts cannot connect because their packets are dropped with `Reason:Limit reached`. Another scenario: SISF generates false IP_THEFT events during VM migration or NIC failover (Cisco bug CSCvx75602), causing unnecessary security alerts. Monitoring PAK_DROP events by reason provides the operational visibility needed to: (1) confirm that security enforcement is working (rogue RAs are being blocked), (2) detect tuning issues (binding table limits, resource exhaustion), and (3) distinguish real attacks from known false positives.

## Implementation

Collect all SISF PAK_DROP syslog events. Parse the Reason field, source port, VLAN, and source IPv6. Categorise by reason and trend over time. Alert on security-relevant reasons (RA guard, IP theft) and on operational issues (limit reached, not enough resources). Track known false positive patterns (CSCvx75602).

## Detailed Implementation

### Prerequisites
- Cisco IOS-XE switches with SISF in `guard` mode (UC-5.20.29, UC-5.20.30).
- Syslog forwarding at severity 4 (warning) or higher to capture `%SISF-4-*` events.
- Understanding of SISF Reason codes and their operational vs security significance.

### Step 1 — Configure data collection

SISF PAK_DROP events are generated automatically when SISF is in `guard` mode. Ensure syslog forwarding captures severity level 4:
```
logging host <splunk_syslog> transport udp port 514
logging trap warnings
```

**Verify SISF is generating events:**
```
show device-tracking database
show device-tracking counters vlan 100
  Binding Table
  Total entries: 245
  Limit: 512
  Drops:
    RA guard: 3
    Source guard: 0
    IP theft: 1
    Limit reached: 0
```

**SISF binding table tuning:**
```
device-tracking binding max-entries 1024 vlan-limit 512 port-limit 10
device-tracking binding reachable-lifetime 86400
device-tracking binding stale-lifetime 86400
```

**Verification in Splunk:**
```spl
index=network sourcetype="cisco:ios" "%SISF-4-PAK_DROP" earliest=-7d
| stats count by host
```

### Step 2 — Create the search and alert

**Primary search — PAK_DROP categorised by reason:**
```spl
index=network sourcetype="cisco:ios" "%SISF-4-PAK_DROP" earliest=-24h
| rex field=_raw "port\s+(?<src_port>\S+)\s+interface\s+(?<vlan>\S+)"
| rex field=_raw "Reason:(?<drop_reason>[^,]+)"
| rex field=_raw "IPv6 SRC:\s*(?<src_ipv6>[0-9a-fA-F:]+)"
| rex field=_raw "IPv6 DST:\s*(?<dst_ipv6>[0-9a-fA-F:]+)"
| eval category=case(
    match(drop_reason, "(?i)RA guard"), "SECURITY — Rogue RA blocked",
    match(drop_reason, "(?i)DHCP.*guard|server guard"), "SECURITY — Rogue DHCPv6 blocked",
    match(drop_reason, "(?i)IP.?theft"), "SECURITY — IP theft detected",
    match(drop_reason, "(?i)source guard"), "SECURITY — Unknown source blocked",
    match(drop_reason, "(?i)limit|resource"), "OPERATIONAL — Capacity issue",
    1=1, "OTHER — " . drop_reason)
| stats count as drops dc(src_ipv6) as unique_sources values(src_port) as ports by host, vlan, category
| sort -drops
```

**Security-focused alert:**
```spl
index=network sourcetype="cisco:ios" "%SISF-4-PAK_DROP" earliest=-15m
| rex field=_raw "Reason:(?<drop_reason>[^,]+)"
| where match(drop_reason, "(?i)RA guard|IP.?theft|MAC.?theft")
| stats count as drops values(drop_reason) as reasons by host
| where drops > 0
```
Trigger: any result. Priority: HIGH.

**Operational alert — binding table capacity:**
```spl
index=network sourcetype="cisco:ios" "%SISF-4-PAK_DROP" "Limit" earliest=-1h
| stats count as limit_drops by host, vlan
| where limit_drops > 5
```
Trigger: >5 limit-related drops per hour. Priority: MEDIUM. Action: increase binding table limits.

### Step 3 — Validate
(a) **Rogue RA test.** On a lab VLAN with SISF in guard mode, enable IPv6 forwarding on a laptop. Verify PAK_DROP with `Reason:RA guard` appears in Splunk.

(b) **Binding table limit test.** Set a very low limit (`device-tracking binding max-entries 5 vlan-limit 5`) on a lab VLAN with 10+ hosts. Verify PAK_DROP with `Reason:Limit reached` appears.

(c) **False IP_THEFT test.** If you have a VM environment, perform a vMotion and check if IP_THEFT events appear. Document as a known false positive.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — SISF Enforcement"):
- Row 1 — Pie chart: PAK_DROP by category (Security vs Operational vs Other).
- Row 2 — Timechart: drop rate by category over 24 hours.
- Row 3 — Table: detailed drops with switch, port, VLAN, reason, source IP.
- Row 4 — Binding table health: entries vs limits per VLAN.

**Scheduling:** Real-time for security drops. Every 15 minutes for operational drops.

**Runbook:**
1. Security drops (RA guard, IP theft): investigate per UC-5.20.21 (rogue RA) and UC-5.20.32 (IP theft).
2. Limit reached: increase binding table limits or reduce the number of hosts per VLAN.
3. Resource exhaustion: check switch TCAM usage (`show platform hardware fed switch active fwd-asic resource utilization`) — SISF bindings consume TCAM entries.

### Step 5 — Troubleshooting

- **Too many PAK_DROP events** — SISF in guard mode can be aggressive. Consider starting with `security-level inspect` (logs but does not block) before moving to `guard`.

- **SISF drops legitimate traffic after switch upgrade** — IOS-XE upgrades may change SISF default behaviour. After upgrading, verify SISF policy settings and binding table contents: `show device-tracking database`.

- **PAK_DROP but no binding table entry** — The source device may be using a privacy extension address that hasn't been learned yet. Increase the SISF probe interval or configure SISF to learn from data traffic (not just DHCPv6/NDP).

## SPL

```spl
index=network sourcetype="cisco:ios" "%SISF-4-PAK_DROP"
| rex field=_raw "port\s+(?<src_port>\S+)\s+interface\s+(?<vlan>\S+)"
| rex field=_raw "Reason:(?<drop_reason>[^,]+)"
| rex field=_raw "IPv6 SRC:\s*(?<src_ipv6>[0-9a-fA-F:]+)"
| stats count as drops dc(src_ipv6) as unique_sources values(drop_reason) as reasons by host, vlan
| sort -drops
```

## Visualization

(1) Pie chart: PAK_DROP events by reason — shows the distribution of drop causes. (2) Timechart: PAK_DROP rate by reason over time. (3) Table: detailed drop events with switch, port, VLAN, reason, source IP. (4) Single-value: total security drops (RA guard + IP theft) and total operational drops (limit + resources).

## Known False Positives

**VM migration (vMotion) causing IP_THEFT.** When a VM migrates between hypervisors, the new host's NIC may briefly claim the VM's IPv6 address before the SISF binding table updates. SISF sees the 'new' MAC claiming an IP bound to the 'old' MAC and generates `%SISF-4-IP_THEFT`. Cisco bug CSCvx75602 documents this. Workaround: increase the SISF re-probe timer or use `device-tracking binding reachable-lifetime` to allow faster re-binding.

**Wireless roaming.** When a wireless client roams from one AP to another, its MAC appears on a different switch port. SISF may generate a transient PAK_DROP until the binding table is updated. This is especially common with fast roaming protocols (802.11r).

**Binding table limit during onboarding.** When many hosts connect simultaneously (e.g., morning office arrival), the binding table may temporarily fill, causing PAK_DROP with `Reason:Limit reached`. Increase the per-VLAN binding limit: `device-tracking binding max-entries <per-vlan> vlan-limit <max>`.

## References

- [Cisco SISF Configuration Guide — PAK_DROP events and Reason codes](https://www.cisco.com/c/en/us/)
- [Cisco Bug CSCvx75602 — SISF false IP_THEFT during HA/VM failover](https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvx75602)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.2 — First-hop security deployment guidance)](https://www.rfc-editor.org/rfc/rfc9099)
