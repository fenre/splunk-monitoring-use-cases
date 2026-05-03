<!-- AUTO-GENERATED from UC-5.20.61.json — DO NOT EDIT -->

---
id: "5.20.61"
title: "IPv6 ACL Hit Count Analysis and Rule Effectiveness Audit"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.20.61 · IPv6 ACL Hit Count Analysis and Rule Effectiveness Audit

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*Our security guards have a checklist of what to allow and what to block. Over time, some items on the checklist become outdated — nobody tries to bring that item anymore. We check which items on the security list have never been matched, so we can clean up the list and make it more efficient. We also make sure the checklist for new visitors (IPv6) matches the checklist for regular visitors (IPv4).*

---

## Description

Analyses IPv6 ACL hit counts to identify unused rules (zero hits — potentially obsolete), overly broad rules (very high hit counts — potentially too permissive), and shadow rules (rules that can never match because a broader rule precedes them). ACL hygiene is especially important for IPv6 because of the dual-stack complexity — rules must be maintained in parallel for both IPv4 and IPv6, and IPv6 rules are often less mature and less tested than their IPv4 counterparts.

## Value

IPv6 ACLs accumulate rule sprawl faster than IPv4 because IPv6 deployment is newer and ACL management tooling is less mature. Unused rules create security risk (they may permit traffic that should be blocked) and performance impact (every packet must be evaluated against every rule). This audit identifies rules that should be removed, consolidated, or reordered, improving both security posture and forwarding performance.

## Implementation

Collect IPv6 ACL hit count data via SNMP polling or `show ipv6 access-list` with match counts. Identify zero-hit rules, very-high-hit rules, and rules that shadow each other. Compare IPv6 ACLs with corresponding IPv4 ACLs for parity.

## Detailed Implementation

### Prerequisites
- IPv6 ACLs deployed on routers and firewalls.
- ACL hit count data available via SNMP, CLI collection, or firewall traffic logs.
- Baseline period of at least 30 days for meaningful hit count analysis.

### Step 1 — Configure data collection

**Cisco IOS-XE — ACL hit counts via CLI:**
```
show ipv6 access-list
  IPv6 access list EXTERNAL_IN
    permit icmp any any destination-unreachable (1523 matches)
    permit icmp any any packet-too-big (234 matches)
    permit icmp any any echo-request (89012 matches)
    deny ipv6 2001:db8:bad::/48 any log (0 matches)
    permit tcp any host 2001:db8:100::80 eq 443 (456789 matches)
    deny ipv6 any any (12345 matches)
```

Collect this output periodically via scripted input or RANCID:
```
[script]
interval = 3600
index = network
sourcetype = cisco:ios:acl_hits
script = /opt/splunk/bin/scripts/poll_acl_hits.sh
```

**Palo Alto — rule hit counts:**
Palo Alto tracks hit counts per security rule. Export via `show running security-policy` with hit counts, or use the PAN-OS API.

**Verification:**
```spl
index=network (sourcetype="cisco:ios:acl_hits" OR sourcetype="cisco:ios") "access-list" "IPv6" earliest=-7d
| stats count by host
```

### Step 2 — Create the search and alert

**Zero-hit rule identification (potentially obsolete):**
```spl
index=network sourcetype="cisco:ios:acl_hits" earliest=-30d
| rex field=_raw "(?<rule_text>(?:permit|deny)\s+[^(]+)\((?<hit_count>\d+)\s+matches\)"
| where hit_count=0 AND match(rule_text, "ipv6")
| stats count as zero_hit_rules values(rule_text) as unused_rules by host
| where zero_hit_rules > 5
| eval recommendation="Review and consider removing " . zero_hit_rules . " IPv6 ACL rules with 0 hits in 30 days"
```

**IPv4 vs IPv6 ACL parity check:**
```spl
index=network sourcetype="cisco:ios:config" earliest=-2d
| rex max_match=0 field=_raw "(?<ipv4_acl>ip access-list (?:standard|extended)\s+\S+)"
| rex max_match=0 field=_raw "(?<ipv6_acl>ipv6 access-list\s+\S+)"
| eval ipv4_acl_count=mvcount(ipv4_acl)
| eval ipv6_acl_count=mvcount(ipv6_acl)
| eval parity_gap=ipv4_acl_count - ipv6_acl_count
| where parity_gap > 2
| eval warning="IPv4/IPv6 ACL parity gap: " . ipv4_acl_count . " IPv4 ACLs vs " . ipv6_acl_count . " IPv6 ACLs — missing IPv6 equivalents"
| table host, ipv4_acl_count, ipv6_acl_count, parity_gap, warning
```
A large gap between IPv4 and IPv6 ACL counts indicates rules are maintained for one protocol but not the other.

**Overly broad permit rule detection:**
```spl
index=network sourcetype="cisco:ios:acl_hits" earliest=-30d
| rex field=_raw "(?<rule_text>permit\s+ipv6\s+any\s+any[^(]*)\((?<hit_count>\d+)\s+matches\)"
| where isnotnull(rule_text) AND NOT match(rule_text, "icmp")
| eval warning="Overly broad IPv6 permit rule: '" . rule_text . "' — consider narrowing scope"
| table host, rule_text, hit_count, warning
```

### Step 3 — Validate
(a) **Zero-hit accuracy.** On a router with known zero-hit rules, verify the search correctly identifies them.

(b) **Parity check accuracy.** On a router with known IPv4/IPv6 ACL parity, verify the gap calculation is correct.

(c) **Hit count progression.** Verify that hit counts increase over time for active rules.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — ACL Effectiveness Audit"):
- Row 1 — Single-value: total IPv6 ACL rules, zero-hit rules, ACLs with parity issues.
- Row 2 — Table: zero-hit rules sorted by age.
- Row 3 — Parity comparison: IPv4 vs IPv6 ACL count per router.
- Row 4 — Top-hit rules: most frequently matched IPv6 rules.

**Scheduling:** Zero-hit analysis monthly. Parity check weekly. Hit count trending daily.

**Runbook:**
1. Zero-hit rules (>90 days): schedule for review. Document business justification or remove.
2. Large parity gap: compare IPv4 and IPv6 ACLs line by line. Add missing IPv6 rules.
3. Overly broad permit: narrow the rule scope with specific prefix-lists and port ranges.

### Step 5 — Troubleshooting

- **ACL hit count reset** — Hit counts reset on device reload or `clear access-list counters`. Ensure the collection script accounts for counter resets.

- **Hardware vs software ACL** — On platforms with TCAM-based ACLs, some complex rules (e.g., with extension header matching) may be processed in software instead of hardware, impacting performance. Monitor for rules that fall out of hardware acceleration.

- **Named vs numbered ACLs** — IPv6 uses only named ACLs (no numbered ACLs like IPv4). Ensure the parsing regex matches the named ACL format.

## SPL

```spl
index=network sourcetype="cisco:ios:acl_hits" earliest=-30d
| rex field=_raw "access-list\s+(?<acl_name>\S+)"
| rex field=_raw "(?<rule_text>(?:permit|deny)\s+[^(]+)\((?<hit_count>\d+)\s+matches\)"
| eval hit_count=tonumber(hit_count)
| eval action=if(match(rule_text, "^\s*deny"), "deny", "permit")
| eval status=case(
    hit_count=0, "ZERO HITS — potentially obsolete",
    hit_count < 10, "LOW — rarely matched",
    hit_count > 1000000, "HIGH — very frequently matched",
    1=1, "NORMAL")
| stats count as total_rules count(eval(hit_count=0)) as zero_hit_rules sum(hit_count) as total_hits by host, acl_name
| eval obsolete_pct=round(zero_hit_rules / total_rules * 100, 1)
| sort -obsolete_pct
```

## Visualization

(1) Table: IPv6 ACL rules sorted by hit count (ascending to show unused rules first). (2) Bar chart: hit count distribution across rules. (3) Heatmap: IPv6 ACL rule activity over time. (4) Parity table: IPv4 vs IPv6 ACL rule count comparison.

## Known False Positives

**Seasonal rules.** Some ACL rules are for seasonal traffic patterns (e.g., year-end reporting, holiday shopping). These rules may show zero hits for most of the year and are not obsolete.

**Emergency rules.** Rules added during incidents for temporary blocking may show low hit counts after the incident is resolved but should be kept as a template.

**Standby/DR rules.** Rules for disaster recovery traffic paths may show zero hits during normal operations.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.4 — filtering guidance)](https://www.rfc-editor.org/rfc/rfc9099)
- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6 (§4.3 — access control)](https://csrc.nist.gov/publications/detail/sp/800-119/final)
