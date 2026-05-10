<!-- AUTO-GENERATED from UC-5.20.64.json — DO NOT EDIT -->

---
id: "5.20.64"
title: "IPv6-Specific Firewall Rule Audit — ICMPv6 and Extension Header Handling"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.64 · IPv6-Specific Firewall Rule Audit — ICMPv6 and Extension Header Handling

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*IPv6 works very differently from the old system. There are certain messages that IPv6 absolutely needs to function — like 'this letter is too big for the mailbox' or 'who is my neighbour?' If the security guard blocks ALL messages because some might be dangerous, the new system stops working entirely.*

---

## Description

Performs a comprehensive audit of firewall rules for IPv6-specific handling — ICMPv6 essential message types, extension header processing, fragment reassembly, NDP multicast, and link-local scope. Firewalls that apply IPv4 filtering assumptions to IPv6 (e.g., 'block all ICMP') will break fundamental IPv6 operations. This audit identifies firewalls with IPv6-hostile rulesets and grades them on their IPv6 readiness.

## Value

The most common IPv6 deployment failure is firewalls that block essential ICMPv6 messages. Path MTU Discovery (PMTUD) depends entirely on ICMPv6 Type 2 (Packet Too Big). Neighbour Discovery Protocol (NDP) depends on ICMPv6 Types 133-137. SLAAC depends on ICMPv6 Types 133-134. Blocking any of these causes symptoms that are extremely difficult to diagnose — TCP connections that hang after the initial handshake (PMTUD failure), hosts that cannot obtain IPv6 addresses (NDP failure), or intermittent connectivity as NDP cache entries expire and are not renewed. This audit catches these misconfigurations before they cause production incidents.

## Implementation

Collect firewall configurations periodically. Audit each configuration for essential IPv6 rule elements. Score each firewall on IPv6 readiness. Alert on firewalls with failing grades.

## Detailed Implementation

### Prerequisites
- Firewall configurations collected periodically (via RANCID, Oxidized, or config backup tools).
- Understanding of each firewall's role (perimeter vs internal) and IPv6 deployment status.
- Knowledge of platform-specific ICMPv6 and extension header handling defaults.

### Step 1 — Configure data collection

**Configuration collection:**
Index firewall configurations as `sourcetype=cisco:ios:config`, `sourcetype=paloalto:config`, or `sourcetype=cisco:asa:config`. See UC-5.20.36 for configuration collection guidance.

**Firewall role lookup:**
```csv
host,fw_role,ipv6_enabled,fw_platform
fw-perimeter-01,perimeter,true,paloalto
fw-internal-01,internal,true,cisco_asa
fw-dmz-01,dmz,true,fortinet
fw-legacy-01,perimeter,false,cisco_ios
```
Upload as `firewall_roles.csv`. The `ipv6_enabled` field allows excluding firewalls that intentionally do not process IPv6.

**Verification:**
```spl
index=network (sourcetype="*:config") "ipv6" earliest=-7d
| stats count by host, sourcetype
```

### Step 2 — Create the search and alert

**Comprehensive IPv6 firewall rule audit:**
```spl
index=network (sourcetype="cisco:ios:config" OR sourcetype="cisco:asa:config" OR sourcetype="paloalto:config") earliest=-2d
| lookup firewall_roles.csv host OUTPUT fw_role, ipv6_enabled, fw_platform
| where ipv6_enabled="true"
| eval checks=mvappend(
    if(match(_raw, "(?i)permit\s+icmpv6?.*packet.too.big|permit.*icmpv6.*type\s*2"), null(), "MISSING: permit ICMPv6 Packet Too Big (Type 2) — breaks PMTUD"),
    if(match(_raw, "(?i)permit\s+icmpv6?.*destination.unreachable|permit.*icmpv6.*type\s*1"), null(), "MISSING: permit ICMPv6 Destination Unreachable (Type 1)"),
    if(match(_raw, "(?i)permit\s+icmpv6?.*time.exceeded|permit.*icmpv6.*type\s*3"), null(), "MISSING: permit ICMPv6 Time Exceeded (Type 3)"),
    if(match(_raw, "(?i)permit\s+icmpv6?.*parameter.problem|permit.*icmpv6.*type\s*4"), null(), "MISSING: permit ICMPv6 Parameter Problem (Type 4)"),
    if(NOT match(_raw, "(?i)deny\s+icmpv6?\s+any\s+any$"), null(), "CRITICAL: blanket deny all ICMPv6"),
    if(fw_role="internal" AND match(_raw, "(?i)permit.*(?:nd-na|nd-ns|neighbor.solicit|neighbor.advert|133|134|135|136)"), null(),
       if(fw_role="internal", "MISSING: permit NDP messages (Types 133-136) on internal firewall", null())),
    if(NOT match(_raw, "(?i)deny.*routing.header.*type.0|deny.*RH0"), "CONSIDER: explicit deny for Routing Header Type 0 (banned by RFC 5095)", null()))
| mvexpand checks
| stats values(checks) as findings count(checks) as issue_count by host, fw_role, fw_platform
| sort -issue_count
```

**Extension header handling audit:**
```spl
index=network (sourcetype="cisco:asa:config" OR sourcetype="paloalto:config") earliest=-2d
| eval eh_policy=case(
    match(_raw, "(?i)deny.*all.*ext.header|drop.*extension"), "BLOCK ALL — may break legitimate IPv6 traffic",
    match(_raw, "(?i)permit.*hop.by.hop|permit.*ext.header"), "PERMIT ALL — may allow EH-based evasion",
    match(_raw, "(?i)routing.header.*type.0.*deny"), "Selective — RH0 blocked (correct)",
    1=1, "Platform default — verify manually")
| table host, eh_policy
```

### Step 3 — Validate
(a) **Known misconfiguration.** On a test firewall, remove the ICMPv6 Packet Too Big permit rule. Verify the audit detects the missing rule.

(b) **Known good configuration.** On a firewall with all essential ICMPv6 rules, verify it receives an A grade.

(c) **Platform-specific defaults.** For Palo Alto, verify the audit accounts for implicit ICMPv6 permits. For Cisco ASA, verify the audit correctly parses the `icmp permit` syntax.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Firewall Rule Audit"):
- Row 1 — Scorecard: IPv6 readiness grade distribution (A/B/C/D/F).
- Row 2 — Table: specific findings per firewall, sorted by severity.
- Row 3 — Trend: average IPv6 readiness score over time (improvement tracking).
- Row 4 — Platform comparison: average score by firewall platform.

**Scheduling:** Weekly configuration audit. Immediate alert on new firewall deployments.

**Runbook:**
1. Grade F (blanket ICMPv6 deny): URGENT — remove the blanket deny. Add specific permits for Types 1-4, 128, 129, 133-137. Test connectivity immediately after change.
2. Grade C (missing PMTUD permit): HIGH — add ICMPv6 Type 2 permit. This single rule prevents the most common and hardest-to-diagnose IPv6 failure mode.
3. Missing NDP on internal: add permits for Types 133-136 and solicited-node multicast (FF02::1:FF00:0/104) on all internal interfaces.
4. Missing RH0 deny: add explicit deny for Routing Header Type 0 per RFC 5095.

### Step 5 — Troubleshooting

- **Implicit permits** — Palo Alto implicitly permits some ICMPv6 types for zone-internal traffic. Cisco ASA has `icmp permit` global commands separate from ACLs. Check platform documentation for default ICMPv6 behaviour.

- **Zone-based vs interface-based** — On zone-based firewalls (Cisco IOS-XE ZBF), ICMPv6 permits must be in the zone-pair policy, not in interface ACLs. The audit should check both locations.

- **Configuration format variations** — Different platforms use different syntax:
  - Cisco IOS: `permit icmp any any packet-too-big`
  - Cisco ASA: `icmp permit any packet-too-big outside`
  - Palo Alto: security-policy rule with application `ping6` or `icmp6-ptb`
  - Juniper SRX: `policy ... then permit; application junos-icmpv6-packet-too-big`

The regex patterns in the search must account for these variations, or use separate searches per platform.

## SPL

```spl
index=network (sourcetype="paloalto:config" OR sourcetype="cisco:asa:config" OR sourcetype="cisco:ios:config") earliest=-2d
| eval blocks_icmpv6_all=if(match(_raw, "(?i)deny\s+icmpv6?\s+any\s+any(?!\s+(destination-unreachable|packet-too-big|time-exceeded|echo|nd-na|nd-ns|router))"), 1, 0)
| eval blocks_nd_multicast=if(match(_raw, "(?i)deny.*(?:ff02::1:ff|solicited.node)"), 1, 0)
| eval blocks_all_ext_headers=if(match(_raw, "(?i)deny.*(?:ext-header|extension.header|routing.header|hop-by-hop)"), 1, 0)
| eval permits_ptb=if(match(_raw, "(?i)permit\s+icmpv6?.*packet.too.big"), 1, 0)
| eval permits_nd=if(match(_raw, "(?i)permit\s+icmpv6?.*(?:nd-na|nd-ns|neighbor|router.solicit|router.advert)"), 1, 0)
| eval score=permits_ptb + permits_nd + (1 - blocks_icmpv6_all) + (1 - blocks_nd_multicast) + (1 - blocks_all_ext_headers)
| eval grade=case(
    score=5, "A — fully IPv6-aware",
    score >= 3, "C — partial IPv6 awareness",
    score >= 1, "F — likely breaking IPv6",
    1=1, "UNKNOWN")
| table host, permits_ptb, permits_nd, blocks_icmpv6_all, blocks_nd_multicast, blocks_all_ext_headers, score, grade
| sort score
```

## Visualization

(1) Scorecard: IPv6 firewall readiness grade per firewall (A/B/C/D/F). (2) Table: specific missing rules per firewall. (3) Trend: IPv6 readiness improvement over time. (4) Summary: count of firewalls per grade.

## Known False Positives

**Perimeter vs internal firewalls.** NDP multicast (FF02::) and link-local (FE80::/10) rules are only needed on internal/interface-facing rules, not on the external perimeter. The audit should distinguish between perimeter and internal rulesets.

**Intentionally restrictive environments.** Some high-security environments intentionally block all IPv6 traffic at the perimeter (IPv4-only policy). In these environments, blocking all ICMPv6 is correct because there is no IPv6 traffic at all. The audit should identify these environments and not flag them.

**Next-generation firewalls.** Palo Alto and similar NGFWs handle ICMPv6 and extension headers differently than traditional ACL-based firewalls. Some NGFWs automatically permit essential ICMPv6 types without explicit rules. Verify the platform's default behaviour before flagging.

## References

- [RFC 4890 — Recommendations for Filtering ICMPv6 Messages in Firewalls](https://www.rfc-editor.org/rfc/rfc4890)
- [RFC 7045 — Transmission and Processing of IPv6 Extension Headers](https://www.rfc-editor.org/rfc/rfc7045)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.4)](https://www.rfc-editor.org/rfc/rfc9099)
