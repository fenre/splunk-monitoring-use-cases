<!-- AUTO-GENERATED from UC-5.20.36.json — DO NOT EDIT -->

---
id: "5.20.36"
title: "First-Hop Security Feature Coverage Gap Audit"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.36 · First-Hop Security Feature Coverage Gap Audit

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*We perform a health inspection of every network switch, checking that all five security locks are installed: one to block fake routers, one to block fake address servers, one to verify sender identities, one to prevent neighbours from being overwhelmed by fake callers, and one that ties it all together. Any switch missing even one lock gets flagged for immediate repair.*

---

## Description

Performs a comprehensive audit of IPv6 first-hop security (FHS) feature deployment across every access-layer switch, checking for the presence of all five critical FHS features: SISF device-tracking, RA Guard, DHCPv6 Guard, Source Guard, and Destination Guard. While individual audits exist for each feature (UC-5.20.29 through UC-5.20.34), this composite view reveals the overall security posture and identifies switches with partial deployments — the most dangerous state, because partial deployment creates a false sense of security while leaving attack vectors open.

## Value

Partial FHS deployment is worse than no deployment in some ways, because it creates false confidence. An operator who sees RA Guard deployed may assume the switch is fully protected, not realising that DHCPv6 Guard, Source Guard, and Destination Guard are all missing. This composite audit exposes the complete picture: which features are deployed, which are missing, and what attack vectors remain open on each switch. It enables prioritised remediation — the switches with zero or one feature should be addressed first.

## Implementation

Collect running configurations from all access switches. Check for the presence of each FHS feature at the global and interface level. Score each switch on a 0-5 scale and categorise as FULLY PROTECTED (5/5), PARTIALLY PROTECTED (3-4/5), MINIMALLY PROTECTED (1-2/5), or UNPROTECTED (0/5). Generate a fleet-wide compliance report.

## Detailed Implementation

### Prerequisites
- Running configuration data from all access-layer switches in Splunk (same collection as UC-5.20.29).
- A lookup identifying which switches are access-layer (to exclude core/distribution from the audit).
- Understanding of SISF implicit feature enablement (guard mode = RA Guard + DHCPv6 Guard).

### Step 1 — Configure data collection

Use the same configuration collection mechanism as UC-5.20.29. The FHS audit parses the same data for all five features.

**Create the access-switch inventory lookup:**
```csv
host,role,supports_sisf
access-sw-01,access,true
access-sw-02,access,true
core-sw-01,core,true
old-sw-01,access,false
```
Upload as `switch_inventory.csv`.

**Verification:**
```spl
index=network sourcetype="cisco:ios:config" earliest=-2d
| stats count by host
| lookup switch_inventory.csv host OUTPUT role, supports_sisf
| where role="access"
```

### Step 2 — Create the search and alert

**Primary audit — fleet-wide FHS coverage:**
```spl
index=network sourcetype="cisco:ios:config" earliest=-2d
| rex field=_raw "hostname\s+(?<switch_name>\S+)"
| lookup switch_inventory.csv host OUTPUT role, supports_sisf
| where role="access" AND supports_sisf="true"
| eval has_sisf=if(match(_raw, "device-tracking"), 1, 0)
| eval sisf_guard=if(match(_raw, "security-level guard"), 1, 0)
| eval has_raguard=if(match(_raw, "raguard") OR sisf_guard=1, 1, 0)
| eval has_dhcpv6_guard=if(match(_raw, "dhcpv6-guard|dhcp-guard") OR sisf_guard=1, 1, 0)
| eval has_source_guard=if(match(_raw, "source-guard|ipv6 source-guard"), 1, 0)
| eval has_dest_guard=if(match(_raw, "destination-guard"), 1, 0)
| eval features=has_sisf + has_raguard + has_dhcpv6_guard + has_source_guard + has_dest_guard
| eval missing=mvappend(
    if(has_sisf=0, "SISF", null()),
    if(has_raguard=0, "RA Guard", null()),
    if(has_dhcpv6_guard=0, "DHCPv6 Guard", null()),
    if(has_source_guard=0, "Source Guard", null()),
    if(has_dest_guard=0, "Dest Guard", null()))
| eval status=case(
    features=5, "FULLY PROTECTED",
    features >= 3, "PARTIAL",
    features >= 1, "MINIMAL",
    1=1, "UNPROTECTED")
| table host, switch_name, has_sisf, has_raguard, has_dhcpv6_guard, has_source_guard, has_dest_guard, features, status, missing
| sort features
```

**Fleet summary:**
```spl
<above search>
| stats count as switches count(eval(features=5)) as fully_protected count(eval(features >= 3 AND features < 5)) as partial count(eval(features < 3 AND features >= 1)) as minimal count(eval(features=0)) as unprotected
| eval full_pct=round(fully_protected / switches * 100, 1)
```

**Feature adoption rates:**
```spl
<above search>
| stats avg(has_sisf) as sisf_rate avg(has_raguard) as raguard_rate avg(has_dhcpv6_guard) as dhcpv6guard_rate avg(has_source_guard) as srcguard_rate avg(has_dest_guard) as destguard_rate
| eval sisf_pct=round(sisf_rate * 100, 1)
| eval raguard_pct=round(raguard_rate * 100, 1)
| eval dhcpv6guard_pct=round(dhcpv6guard_rate * 100, 1)
| eval srcguard_pct=round(srcguard_rate * 100, 1)
| eval destguard_pct=round(destguard_rate * 100, 1)
```
This shows which features are most commonly deployed and which are lagging.

### Step 3 — Validate
(a) **Spot-check 5 switches.** Compare the audit results with `show device-tracking policies`, `show ipv6 nd raguard`, `show ipv6 source-guard`, and `show ipv6 destination-guard` on the actual devices.

(b) **SISF guard mode implicit features.** On a switch with `security-level guard` but no explicit `raguard` directive, verify the audit correctly counts RA Guard and DHCPv6 Guard as deployed.

(c) **Unsupported hardware.** Verify that switches marked `supports_sisf=false` are excluded from the compliance calculation.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — First-Hop Security Fleet Compliance"):
- Row 1 — Gauge: fleet-wide FHS coverage % (target: 100% fully protected).
- Row 2 — Stacked bar chart: switches by protection level (FULLY, PARTIAL, MINIMAL, UNPROTECTED).
- Row 3 — Feature adoption: horizontal bar chart showing adoption rate for each of the 5 features.
- Row 4 — Remediation priority: switches sorted by features deployed (least first), with missing features listed.
- Row 5 — Trend: weekly snapshots of fleet-wide coverage over time.

**Scheduling:** Daily audit. Weekly trending report. Monthly executive summary.

**Runbook:**
1. UNPROTECTED switches: immediate remediation — deploy SISF with guard mode at minimum.
2. MINIMAL switches: prioritise RA Guard (highest-impact threat prevention).
3. PARTIAL switches: deploy the missing features to reach FULLY PROTECTED.
4. Target: 100% of access switches at FULLY PROTECTED within 6 months.

### Step 5 — Troubleshooting

- **Configuration parsing complexity** — Some switches have different configuration styles (IOS vs IOS-XE vs NX-OS). Ensure the regex patterns cover all platform configuration formats.

- **Feature names vary by platform** — Cisco IOS-XE uses `device-tracking`, older IOS uses `ipv6 nd inspection`. Juniper uses `router-advertisement-guard`. Include platform-specific feature names in the detection patterns.

- **SISF may disable features during upgrade** — Some IOS-XE upgrades change SISF defaults. Re-audit after every major firmware upgrade to verify FHS features remain active.

## SPL

```spl
index=network sourcetype="cisco:ios:config" earliest=-2d
| rex field=_raw "hostname\s+(?<switch_name>\S+)"
| eval has_sisf=if(match(_raw, "device-tracking"), 1, 0)
| eval has_raguard=if(match(_raw, "raguard"), 1, 0)
| eval has_dhcpv6_guard=if(match(_raw, "dhcpv6-guard|dhcp-guard"), 1, 0)
| eval has_source_guard=if(match(_raw, "source-guard|ipv6 source-guard"), 1, 0)
| eval has_dest_guard=if(match(_raw, "destination-guard"), 1, 0)
| eval features_deployed=has_sisf + has_raguard + has_dhcpv6_guard + has_source_guard + has_dest_guard
| eval missing=mvappend(
    if(has_sisf=0, "SISF/device-tracking", null()),
    if(has_raguard=0, "RA Guard", null()),
    if(has_dhcpv6_guard=0, "DHCPv6 Guard", null()),
    if(has_source_guard=0, "Source Guard", null()),
    if(has_dest_guard=0, "Destination Guard", null()))
| eval compliance_pct=round(features_deployed / 5 * 100)
| eval status=case(
    features_deployed=5, "FULLY PROTECTED",
    features_deployed >= 3, "PARTIALLY PROTECTED",
    features_deployed >= 1, "MINIMALLY PROTECTED",
    1=1, "UNPROTECTED")
| table host, switch_name, has_sisf, has_raguard, has_dhcpv6_guard, has_source_guard, has_dest_guard, compliance_pct, status, missing
| sort compliance_pct
```

## Visualization

(1) Single-value: percentage of switches fully protected (5/5). (2) Table: per-switch FHS feature matrix with colour-coded presence/absence. (3) Bar chart: feature deployment rates — which features are most commonly missing? (4) Trend chart: FHS coverage improvement over time (weekly snapshots).

## Known False Positives

**Switches without IPv6 support.** Older switches that do not support IPv6 or SISF will show 0/5 features. These should be categorised separately as 'hardware limitation' rather than 'non-compliant.'

**SISF implicitly enabling multiple features.** On Cisco IOS-XE, `device-tracking policy` with `security-level guard` automatically provides RA Guard and DHCPv6 Guard functionality. The configuration may not show explicit `raguard` or `dhcpv6-guard` directives — the protection is inherited. The audit search should check for SISF guard mode as equivalent to RA Guard + DHCPv6 Guard.

**Router/distribution switches.** FHS features are designed for access-layer switches (user-facing ports). Core and distribution switches typically do not need access-port FHS features. Exclude non-access switches from the audit.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.2 — Comprehensive first-hop security recommendation)](https://www.rfc-editor.org/rfc/rfc9099)
- [Cisco SISF Design Guide — Complete first-hop security deployment](https://www.cisco.com/c/en/us/)
- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6 (first-hop security requirements)](https://csrc.nist.gov/publications/detail/sp/800-119/final)
