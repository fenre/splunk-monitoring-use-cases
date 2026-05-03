<!-- AUTO-GENERATED from UC-5.20.79.json — DO NOT EDIT -->

---
id: "5.20.79"
title: "DISA STIG IPv6 Router and Firewall Compliance Audit"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.79 · DISA STIG IPv6 Router and Firewall Compliance Audit

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Compliance &middot; **Wave:** Run &middot; **Status:** Verified

*The military has a very specific list of safety rules for how to set up the new postal system (IPv6). We check every post office (router) against that list: 'Is the back door locked? Are the correct windows open? Is the guard posted at the entrance?' We score each post office and flag any that don't follow every rule on the list.*

---

## Description

Audits router and firewall configurations against Defense Information Systems Agency (DISA) Security Technical Implementation Guide (STIG) requirements for IPv6. Checks for mandatory controls including Routing Header Type 0 blocking, ULA and site-local address filtering, bogon prefix filtering, RA Guard deployment, and proper ICMPv6 policy. While DISA STIGs are mandatory only for US Department of Defense networks, they represent a widely-respected hardening baseline used by many organisations worldwide.

## Value

DISA STIGs represent the most prescriptive and actionable IPv6 hardening checklist available. Even for non-DoD organisations, STIG compliance provides concrete, testable security controls that are often missing from more general guidelines. Each STIG requirement addresses a specific, documented attack vector. Automated compliance checking transforms a manual, error-prone audit process into a continuous assurance capability that can be run at every configuration change.

## Implementation

Collect running configurations from all IPv6-capable routers and firewalls. Parse configurations against each STIG requirement. Score compliance and track trending. Alert on configuration changes that reduce compliance score.

## Detailed Implementation

### Prerequisites
- Configuration collection infrastructure — CiscoConfParse, RANCID, Oxidized, or Splunk Add-on for Cisco IOS.
- Knowledge of which devices are in scope for DISA STIG compliance.
- STIG requirements lookup table mapping STIG IDs to configuration patterns.

### Step 1 — Configure data collection

**Create STIG requirements lookup:**
```csv
stig_id,requirement,config_pattern,severity,description
NET-IPV6-004,Block Routing Header Type 0,"no ipv6 source-route|deny.*routing-type 0",CAT I,RFC 5095 deprecated RH0 due to amplification and source routing attacks
NET-IPV6-032,Filter ULA at perimeter,"deny.*ipv6.*(fc00|fd[0-9a-fA-F]{2})::/7",CAT II,ULA addresses must not cross organisational perimeters
NET-IPV6-064,Block deprecated site-local,"deny.*ipv6.*fec0::/10",CAT II,Site-local addresses deprecated by RFC 3879
NET-IPV6-066,Filter IPv6 bogons,"deny.*ipv6.*(3ffe::|2001:db8::|::ffff:0:0/96)",CAT II,Documentation and decommissioned prefixes must be blocked
NET-IPV6-035,Permit essential ICMPv6,"permit.*icmpv6.*(packet-too-big|nd-|router-|echo)",CAT II,RFC 4890 mandates essential ICMPv6 types for IPv6 operation
NET-IPV6-068,RA Guard on access ports,"ipv6 nd raguard",CAT I,Prevents rogue Router Advertisement attacks
```
Upload as `disa_stig_ipv6.csv`.

**Collect running configurations:**
```
[monitor:///opt/rancid/configs/routers/*.conf]
sourcetype = cisco:ios:config
index = network
```

Alternatively, use the Cisco IOS REST API or NETCONF to poll configurations on a schedule.

**Verification:**
```spl
index=network sourcetype="cisco:ios:config" | stats count by host | sort -count
```
Expected: one configuration per in-scope device.

### Step 2 — Create the compliance search

**Per-device STIG compliance matrix:**
```spl
index=network (sourcetype="cisco:ios:config" OR sourcetype="cisco:iosxe:config") earliest=-7d
| dedup host
| eval rh0_blocked=if(match(_raw, "(?i)no ipv6 source-route") OR match(_raw, "(?i)deny.*ipv6.*routing-type\s+0"), "PASS", "FAIL")
| eval ula_filtered=if(match(_raw, "(?i)deny.*ipv6.*(fc00|fd[0-9a-fA-F]{2})::"), "PASS", "FAIL")
| eval sitelocal_filtered=if(match(_raw, "(?i)deny.*ipv6.*fec0::"), "PASS", "FAIL")
| eval bogon_filtered=if(match(_raw, "(?i)deny.*ipv6.*(3ffe::|2001:db8::)"), "PASS", "FAIL")
| eval raguard=if(match(_raw, "(?i)ipv6 nd raguard"), "PASS", "FAIL")
| eval icmpv6_policy=if(match(_raw, "(?i)permit.*icmpv6?.*(packet-too-big|nd-na|nd-ns)"), "PASS", "FAIL")
| eval passed=mvcount(mvfilter(match(mvappend(rh0_blocked, ula_filtered, sitelocal_filtered, bogon_filtered, raguard, icmpv6_policy), "PASS")))
| eval total=6
| eval pct=round(passed/total*100, 0)
| table host, rh0_blocked, ula_filtered, sitelocal_filtered, bogon_filtered, raguard, icmpv6_policy, pct
| sort pct
```

**Fleet-level compliance summary:**
```spl
| inputlookup stig_compliance_results.csv
| stats count(eval(status="PASS")) as passed count(eval(status="FAIL")) as failed by stig_id, requirement
| eval compliance_rate=round(passed / (passed + failed) * 100, 0) . "%"
| sort compliance_rate
```

### Step 3 — Validate
(a) **Manual verification.** SSH to 3 sample devices across core/distribution/access tiers. Run `show running-config | include source-route` and `show running-config | section ipv6 access-list`. Verify SPL results match.

(b) **Known-bad test.** Temporarily remove `no ipv6 source-route` from a lab device. Verify the compliance search flags it as FAIL for NET-IPV6-004.

(c) **Cross-platform validation.** If running Juniper, verify the equivalent configuration patterns: `set security flow reject-routing-header-type-0` and `set firewall family inet6 filter` rules.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — DISA STIG Compliance"):
- Row 1 — Single-value: fleet compliance percentage. Colour-code: green ≥ 95%, amber 80-94%, red < 80%.
- Row 2 — Table: per-device compliance matrix with PASS/FAIL per STIG ID.
- Row 3 — Bar chart: compliance rate by STIG requirement (identifies which controls are most commonly missed).
- Row 4 — Trend: compliance percentage over 90 days.

**Alert:** `compliance_pct < 100` on any device in production — trigger immediately on configuration change. Route to network security team.

**Runbook:**
1. FAIL on NET-IPV6-004 (RH0 not blocked): Add `no ipv6 source-route` globally on IOS/IOS-XE. On NX-OS, add explicit ACL deny for routing-type 0.
2. FAIL on NET-IPV6-068 (no RA Guard): Enable RA Guard on all access layer switchports. Configure as RA Guard device role "host" on access ports and "router" only on uplinks to legitimate routers.
3. FAIL on NET-IPV6-035 (ICMPv6 blocked): Review IPv6 ACLs. Ensure Types 1-4 (errors), 128-129 (echo), and 133-137 (NDP) are permitted per RFC 4890.

### Step 5 — Troubleshooting

- **Configuration format variations.** Different IOS versions may use different CLI syntax for the same feature. Build a regex pattern library that covers IOS, IOS-XE, IOS-XR, NX-OS, and ASA syntax.

- **False failures from context-dependent config.** Some STIG checks are interface-specific (e.g., RA Guard on access ports only, not uplinks). Ensure the search scopes correctly — RA Guard on a trunk to a legitimate router is intentional.

- **STIG version drift.** DISA updates STIGs quarterly. Subscribe to DISA STIG announcements and update the lookup table when new STIGs are released or existing ones are modified.

## SPL

```spl
index=network (sourcetype="cisco:ios:config" OR sourcetype="cisco:iosxe:config") earliest=-7d
| dedup host
| eval rh0_blocked=if(match(_raw, "(?i)deny.*routing.?header.*type.?0|no ipv6 source-route"), 1, 0)
| eval ula_filtered=if(match(_raw, "(?i)deny.*ipv6.*(fc00|fd[0-9a-fA-F]{2})::"), 1, 0)
| eval sitelocal_filtered=if(match(_raw, "(?i)deny.*ipv6.*fec0::"), 1, 0)
| eval bogon_filtered=if(match(_raw, "(?i)deny.*ipv6.*(3ffe::|2001:db8::|::ffff:)"), 1, 0)
| eval raguard_enabled=if(match(_raw, "(?i)ipv6 nd raguard"), 1, 0)
| eval icmpv6_permitted=if(match(_raw, "(?i)permit.*icmpv6?.*(packet-too-big|nd-na|nd-ns|router-solicit|router-advert|echo)"), 1, 0)
| eval stig_checks=6
| eval stig_passed=rh0_blocked + ula_filtered + sitelocal_filtered + bogon_filtered + raguard_enabled + icmpv6_permitted
| eval compliance_pct=round(stig_passed / stig_checks * 100, 0)
| eval rating=case(
    compliance_pct=100, "COMPLIANT",
    compliance_pct >= 80, "MOSTLY COMPLIANT — " . (stig_checks - stig_passed) . " findings",
    compliance_pct >= 50, "PARTIALLY COMPLIANT — significant gaps",
    1=1, "NON-COMPLIANT — immediate remediation required")
| table host, rh0_blocked, ula_filtered, sitelocal_filtered, bogon_filtered, raguard_enabled, icmpv6_permitted, compliance_pct, rating
| sort compliance_pct
```

## Visualization

(1) Single-value: fleet compliance percentage (target: 100%). (2) Table: per-device STIG compliance matrix. (3) Heatmap: compliance by device role (core/distribution/access). (4) Trend: compliance score over time.

## Known False Positives

**Configuration parsing limitations.** Regex-based configuration parsing may miss variations in CLI syntax across different IOS versions or platforms. For example, `no ipv6 source-route` is the IOS global command for RH0 blocking, while an explicit ACL deny is the NX-OS approach.

**Intentional exceptions.** Some organisations may intentionally allow certain traffic (e.g., ULA for internal lab segments) with documented risk acceptance. These should be annotated in a STIG exceptions lookup.

**Multi-context firewalls.** ASA or FWSM multi-context configurations may show partial compliance if only some contexts are checked.

## References

- [DISA STIG Library — Network IPv6 STIGs](https://public.cyber.mil/stigs/)
- [RFC 5095 — Deprecation of Type 0 Routing Headers in IPv6](https://www.rfc-editor.org/rfc/rfc5095)
- [RFC 4890 — Recommendations for Filtering ICMPv6 Messages in Firewalls](https://www.rfc-editor.org/rfc/rfc4890)
- [RFC 6105 — IPv6 Router Advertisement Guard (RA Guard)](https://www.rfc-editor.org/rfc/rfc6105)
