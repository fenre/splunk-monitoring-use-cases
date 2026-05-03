<!-- AUTO-GENERATED from UC-5.20.131.json — DO NOT EDIT -->

---
id: "5.20.131"
title: "IPv6 ICMPv6 Rate Limiting and Policy Compliance (RFC 4890)"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.131 · IPv6 ICMPv6 Rate Limiting and Policy Compliance (RFC 4890)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*IPv6 relies on special control messages (ICMPv6) to work — like 'this letter is too big for the mailbox' or 'is anyone home at this address?' Some overzealous security guards block ALL of these messages, not realising they're blocking the ones that keep the postal service running. We check that the essential messages are always allowed through.*

---

## Description

Verifies ICMPv6 filtering policies comply with RFC 4890. Detects firewalls that incorrectly block essential ICMPv6 messages: Packet Too Big (PMTUD), NS/NA (neighbour resolution), RS/RA (SLAAC/NDP), and Echo (diagnostics). Blocking these messages is the most common cause of mysterious IPv6 connectivity failures.

## Value

Blocking ICMPv6 is the #1 most common IPv6 misconfiguration. Administrators accustomed to IPv4 (where blocking ICMP is common hardening) apply the same logic to IPv6, breaking fundamental protocol operations. RFC 4890 provides clear guidance on which ICMPv6 types must be permitted. This UC detects violations and prevents connectivity failures caused by overly aggressive ICMPv6 filtering.

## Implementation

Monitor firewall deny logs for blocked ICMPv6 types. Classify by RFC 4890 category. Alert on MUST NOT DROP violations.

## Detailed Implementation

### Prerequisites
- Firewall logging for ICMPv6 deny actions.

### Step 1 — Audit ICMPv6 firewall rules. Verify RFC 4890 compliance.

### Step 2 — Create monitoring searches for blocked essential ICMPv6.

### Step 3 — Validate: Test PMTUD by sending large IPv6 packets. Verify PTB messages are delivered.

### Step 4 — Operationalize
**Dashboard:** RFC 4890 compliance. **Alert:** Any MUST NOT DROP violation — critical.

### Step 5 — Troubleshooting
- Blocked PTB causing black holes: Add explicit permit rule for ICMPv6 type 2 on all transit firewalls.
- Blocked NS/NA causing resolution failures: Add explicit permit for ICMPv6 types 135/136.

## SPL

```spl
index=network (sourcetype="paloalto:traffic" OR sourcetype="cisco:asa" OR sourcetype="cisco:ftd") earliest=-24h
  ("icmpv6" OR "ICMPv6" OR "icmp6") AND ("deny" OR "drop" OR "block")
| rex field=_raw "type\s*=?\s*(?<icmpv6_type>\d+)"
| eval rfc4890_category=case(
    icmpv6_type IN ("2", "128", "129", "133", "134", "135", "136"), "MUST NOT DROP — RFC 4890 violation",
    icmpv6_type IN ("1", "3", "4"), "SHOULD NOT DROP — may impact operations",
    icmpv6_type IN ("137", "138", "139", "140"), "MAY DROP — policy decision",
    1=1, null())
| where rfc4890_category="MUST NOT DROP*"
| eval violation_detail=case(
    icmpv6_type="2", "Packet Too Big BLOCKED — PMTUD is broken, causes black holes",
    icmpv6_type="128" OR icmpv6_type="129", "Echo blocked — diagnostic capability lost",
    icmpv6_type="133" OR icmpv6_type="134", "RS/RA blocked — NDP/SLAAC will fail",
    icmpv6_type="135" OR icmpv6_type="136", "NS/NA blocked — neighbour resolution fails",
    1=1, "ICMPv6 type " . icmpv6_type . " blocked")
| stats count as drops by host, icmpv6_type, violation_detail
| sort -drops
```

## Visualization

(1) Table: blocked ICMPv6 types with RFC 4890 classification. (2) Single-value: MUST NOT DROP violations (should be zero). (3) Bar chart: blocked types. (4) Trend: violation count over time.

## Known False Positives

**External-to-internal RA/RS.** Blocking RS/RA from external networks at the perimeter is correct — RFC 4890 distinguishes between transit and local-link filtering.

**ICMPv6 redirect.** Blocking redirects at firewalls is acceptable (type 137 is in the MAY DROP category).

## References

- [RFC 4890 — Recommendations for Filtering ICMPv6 Messages in Firewalls](https://www.rfc-editor.org/rfc/rfc4890)
- [RFC 8200 — IPv6 Specification (PMTUD requirements)](https://www.rfc-editor.org/rfc/rfc8200)
