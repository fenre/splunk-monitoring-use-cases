<!-- AUTO-GENERATED from UC-5.20.37.json — DO NOT EDIT -->

---
id: "5.20.37"
title: "ICMPv6 Firewall Policy Compliance Audit"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.20.37 · ICMPv6 Firewall Policy Compliance Audit

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*IPv6 networks use special system messages to function — like emergency alerts that tell devices about roadblocks, detours, and who lives where. If the firewall blocks these messages, the network stops working properly. We check every firewall to make sure it allows these essential messages through, just like making sure fire trucks are never blocked by traffic barriers.*

---

## Description

Audits firewall and ACL configurations to verify that IPv6 ICMPv6 filtering policies comply with RFC 4890 (Recommendations for Filtering ICMPv6 Messages in Firewalls). This is the single most critical IPv6 compliance check because incorrectly filtered ICMPv6 is the #1 cause of IPv6 operational failures worldwide. Unlike IPv4 where ICMP can be broadly filtered, IPv6 requires ICMPv6 Types 1-4 (error messages) and Types 133-137 (Neighbor Discovery) to be permitted for basic connectivity. Blocking ICMPv6 Type 2 (Packet Too Big) breaks Path MTU Discovery and causes TCP connections to hang after the initial handshake. Blocking Types 135-136 (Neighbor Solicitation/Advertisement) breaks IPv6 address resolution entirely — the equivalent of blocking all ARP in IPv4.

## Value

The #1 question when debugging IPv6 connectivity issues is: 'Is the firewall blocking ICMPv6?' The answer is 'yes' in a shocking number of enterprise deployments, because firewall administrators apply IPv4 habits to IPv6. In IPv4, blocking ICMP is a common (if controversial) hardening practice. In IPv6, blocking ICMPv6 breaks the protocol. This audit catches the misconfiguration proactively — before users report 'IPv6 doesn't work' — by comparing firewall rules against the RFC 4890 requirements. Every IPv6 deployment should run this audit as part of the deployment validation.

## Implementation

Collect firewall and ACL configurations. Parse ICMPv6 type-specific rules. Compare against RFC 4890 requirements (Types 1-4 MUST be permitted, Types 133-137 MUST be permitted on internal interfaces). Flag any DENY rule for essential ICMPv6 types.

## Detailed Implementation

### Prerequisites
- Firewall and router ACL configurations in Splunk (from configuration management, RANCID, or scripted collection).
- Knowledge of which firewalls are perimeter (where NDP types should be blocked) vs internal (where NDP types must be permitted).
- Reference: RFC 4890 §4.3 for the complete filtering matrix.

### Step 1 — Configure data collection

Collect firewall configurations using the same mechanisms as UC-5.20.29 (switch configs) extended to firewalls. For Palo Alto, use `show running security-policy` exported to Splunk. For Cisco ASA, use `show running-config access-list`.

**Reference — correct ICMPv6 ACL on Cisco IOS (internal interface):**
```
ipv6 access-list ICMPV6_INTERNAL
 remark === RFC 4890 MUST PERMIT ===
 permit icmp any any destination-unreachable
 permit icmp any any packet-too-big
 permit icmp any any time-exceeded
 permit icmp any any parameter-problem
 permit icmp any any echo-request
 permit icmp any any echo-reply
 remark === NDP — link-local only ===
 permit icmp any any router-solicitation
 permit icmp any any router-advertisement
 permit icmp any any neighbor-solicitation
 permit icmp any any neighbor-advertisement
 permit icmp any any redirect
 remark === MLD ===
 permit icmp any any 130
 permit icmp any any 131
 permit icmp any any 143
 remark === DENY EVERYTHING ELSE ===
 deny icmp any any log
```

**Reference — correct ICMPv6 ACL (perimeter interface):**
```
ipv6 access-list ICMPV6_PERIMETER
 remark === RFC 4890 MUST PERMIT (errors) ===
 permit icmp any any destination-unreachable
 permit icmp any any packet-too-big
 permit icmp any any time-exceeded
 permit icmp any any parameter-problem
 permit icmp any any echo-request
 permit icmp any any echo-reply
 remark === NDP blocked at perimeter ===
 deny icmp any any router-solicitation log
 deny icmp any any router-advertisement log
 deny icmp any any neighbor-solicitation log
 deny icmp any any neighbor-advertisement log
 deny icmp any any redirect log
 remark === DENY EVERYTHING ELSE ===
 deny icmp any any log
```

### Step 2 — Create the search and alert

**Primary compliance audit:**
```spl
index=network (sourcetype="cisco:ios:config" OR sourcetype="cisco:asa:config" OR sourcetype="paloalto:firewall:config") earliest=-2d
| rex max_match=0 field=_raw "(?<rule>(?:deny|reject)\s+(?:icmp|icmpv6)\s+.*?(?:destination-unreachable|packet-too-big|time-exceeded|parameter-problem|unreachable|too-big|type\s*[1234]\b).*)"
| mvexpand rule
| lookup firewall_role.csv host OUTPUT fw_role
| eval blocked_type=case(
    match(rule, "unreachable|type\s*1\b"), "Type 1 — Destination Unreachable",
    match(rule, "packet-too-big|too-big|type\s*2\b"), "Type 2 — Packet Too Big",
    match(rule, "time-exceeded|type\s*3\b"), "Type 3 — Time Exceeded",
    match(rule, "parameter-problem|type\s*4\b"), "Type 4 — Parameter Problem",
    1=1, "Unknown")
| eval severity=case(
    match(blocked_type, "Type 2"), "CRITICAL — blocking PMTUD breaks TCP data transfer",
    match(blocked_type, "Type 1"), "HIGH — blocking error signaling",
    1=1, "MEDIUM")
| table host, fw_role, rule, blocked_type, severity
```

**Specific alert — Type 2 (Packet Too Big) blocked:**
```spl
index=network (sourcetype="cisco:ios:config" OR sourcetype="cisco:asa:config") earliest=-2d
| rex max_match=0 field=_raw "(?<rule>deny\s+icmp\s+.*(?:packet-too-big|type\s*2\b).*)"
| mvexpand rule
| where isnotnull(rule)
| table host, rule
```
Trigger: any result. Priority: CRITICAL. Blocking PTB messages is the single most common IPv6 misconfiguration.

**NDP types on internal interfaces:**
```spl
index=network sourcetype="cisco:ios:config" earliest=-2d
| lookup firewall_role.csv host OUTPUT fw_role
| where fw_role="internal"
| rex max_match=0 field=_raw "(?<rule>deny\s+icmp\s+.*(?:neighbor-solicitation|neighbor-advertisement|router-solicitation|router-advertisement).*)"
| mvexpand rule
| where isnotnull(rule)
| eval issue="NON-COMPLIANT — blocking NDP on internal interface breaks IPv6"
| table host, rule, issue
```

### Step 3 — Validate
(a) **Known-good firewall.** Audit a firewall with correct RFC 4890 configuration. Verify zero non-compliant findings.

(b) **Known-bad firewall.** Audit a firewall known to block ICMPv6 broadly (`deny icmp any any`). Verify all essential types are flagged.

(c) **Type 2 impact test (lab).** On a lab path with MTU 1280, block ICMPv6 Type 2 at a firewall. Attempt a TCP connection: the handshake completes (SYN/SYN-ACK/ACK are small) but data transfer hangs because the sending host never reduces its packet size. Unblock Type 2, observe data flows normally.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — ICMPv6 Policy Compliance"):
- Row 1 — Single-value: firewalls blocking Type 2 (CRITICAL), total non-compliant rules.
- Row 2 — Table: all non-compliant rules with firewall, blocked type, and severity.
- Row 3 — Heatmap: ICMPv6 type compliance across the firewall fleet.

**Scheduling:** Daily configuration audit. Immediate alert on Type 2 blocking.

**Runbook:**
1. Type 2 blocked: URGENT — add `permit icmp any any packet-too-big` to the ACL. This is the most impactful single-line fix in IPv6 operations.
2. Types 1, 3, 4 blocked: HIGH — add permits for error message types.
3. NDP types blocked on internal interface: HIGH — add permits for Types 133-137.
4. NDP types blocked at perimeter: COMPLIANT — this is correct behaviour.

### Step 5 — Troubleshooting

- **Implicit deny catching ICMPv6** — Many ACLs end with `deny any any`. If ICMPv6 types are not explicitly permitted before this rule, they are implicitly blocked. The audit should check for the presence of explicit permits, not just the absence of explicit denies.

- **Palo Alto security policy** — Palo Alto uses application-based rules, not type-based. `application=icmpv6` with `action=allow` permits all types. If the policy blocks `icmpv6`, it blocks all types including essential ones.

- **Stateful firewalls and ICMPv6** — Stateful firewalls may allow ICMPv6 error messages (Types 1-4) only if they match an existing session. This is acceptable for errors but does not cover unsolicited PTB messages (which may arrive before the session exists in the firewall state table). Ensure the firewall has a specific permit for PTB that is not session-dependent.

## SPL

```spl
index=network sourcetype="cisco:ios:config" earliest=-2d
| rex max_match=0 field=_raw "(?<acl_entry>(?:permit|deny)\s+icmp\s+.*(?:type|echo|unreachable|packet-too-big|time-exceeded|parameter-problem|router-solicitation|router-advertisement|neighbor-solicitation|neighbor-advertisement|redirect).*)"
| mvexpand acl_entry
| eval icmpv6_type=case(
    match(acl_entry, "unreachable"), "Type 1 — Dest Unreachable",
    match(acl_entry, "packet-too-big"), "Type 2 — Packet Too Big",
    match(acl_entry, "time-exceeded"), "Type 3 — Time Exceeded",
    match(acl_entry, "parameter-problem"), "Type 4 — Parameter Problem",
    match(acl_entry, "echo-request|echo.*request"), "Type 128 — Echo Request",
    match(acl_entry, "echo-reply|echo.*reply"), "Type 129 — Echo Reply",
    match(acl_entry, "router-solicitation"), "Type 133 — Router Solicitation",
    match(acl_entry, "router-advertisement"), "Type 134 — Router Advertisement",
    match(acl_entry, "neighbor-solicitation"), "Type 135 — Neighbor Solicitation",
    match(acl_entry, "neighbor-advertisement"), "Type 136 — Neighbor Advertisement",
    match(acl_entry, "redirect"), "Type 137 — Redirect",
    1=1, "Other")
| eval action=if(match(acl_entry, "^\s*deny"), "DENY", "PERMIT")
| eval rfc4890_compliant=if(action="DENY" AND match(icmpv6_type, "Type [1234] "), "NON-COMPLIANT — blocking essential error type", "OK")
| table host, acl_entry, icmpv6_type, action, rfc4890_compliant
```

## Visualization

(1) Table: ICMPv6 type-by-type compliance matrix per firewall/ACL. (2) Single-value: count of non-compliant rules. (3) Heatmap: which ICMPv6 types are most commonly blocked across the fleet. (4) Drilldown: click on a non-compliant rule to see the full ACL context.

## Known False Positives

**Perimeter blocking of NDP types (133-137).** RFC 4890 explicitly recommends blocking NDP messages at the site perimeter because they are link-local scoped and should never cross network boundaries. A perimeter firewall with `deny icmp any any router-solicitation` is compliant — the audit should distinguish perimeter from internal firewalls.

**Rate-limited ICMPv6.** A firewall that rate-limits (rather than blocks) ICMPv6 is compliant as long as legitimate traffic is not dropped under normal load. Rate limiting is a recommended best practice.

**Implicit deny at end of ACL.** Most ACLs have an implicit `deny any any` at the end. This implicitly blocks all ICMPv6 types not explicitly permitted earlier in the ACL. The audit should check that the required types are explicitly permitted before the implicit deny.

## References

- [RFC 4890 — Recommendations for Filtering ICMPv6 Messages in Firewalls (the authoritative guide for ICMPv6 filtering)](https://www.rfc-editor.org/rfc/rfc4890)
- [RFC 8200 — Internet Protocol, Version 6 (IPv6) Specification (§4.5 — ICMPv6 as integral part of IPv6)](https://www.rfc-editor.org/rfc/rfc8200)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.4.3 — ICMPv6 filtering guidance)](https://www.rfc-editor.org/rfc/rfc9099)
