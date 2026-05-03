<!-- AUTO-GENERATED from UC-5.20.99.json — DO NOT EDIT -->

---
id: "5.20.99"
title: "IPv6 Operational Hygiene — Deprecated Address and Protocol Audit"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.99 · IPv6 Operational Hygiene — Deprecated Address and Protocol Audit

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Compliance, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Over the years, some of the rules and address formats for the new postal system (IPv6) were tried but found to be unsafe or unnecessary, like an old lock that's easy to pick. We check all our equipment to make sure nobody is still using these outdated and unsafe address formats or methods, and we make a list of everything that needs to be updated to the current standards.*

---

## Description

Audits network device configurations for deprecated IPv6 addresses, protocols, and features that should have been removed: site-local addresses (fec0::/10), 6bone addresses (3ffe::/16), EUI-64 interface identifiers, 6to4 tunnels, Teredo, ISATAP, and Routing Header Type 0. These deprecated features represent security risks, compliance violations, and operational technical debt.

## Value

Deprecated IPv6 features are often forgotten in configurations, creating hidden security exposures and compliance violations. Site-local addresses confuse routing, 6to4/Teredo create uncontrolled IPv6 connectivity, EUI-64 exposes hardware identifiers, and Routing Header Type 0 enables traffic amplification attacks. A periodic deprecation audit ensures configurations follow current standards and eliminates technical debt that could be exploited.

## Implementation

Parse device configurations for deprecated IPv6 patterns. Flag each finding with the specific RFC that deprecated the feature. Generate a remediation checklist sorted by severity.

## Detailed Implementation

### Prerequisites
- Device configuration collection via syslog, RANCID/Oxidized, or NETCONF.
- Configuration data indexed in Splunk.

### Step 1 — Configure data collection

**RANCID/Oxidized config backup to Splunk:**
Configure Oxidized to export device configurations to a directory monitored by Splunk:
```yaml
# oxidized config
output:
  file:
    directory: /opt/oxidized/configs/
```

Splunk `inputs.conf`:
```ini
[monitor:///opt/oxidized/configs/]
disabled = false
sourcetype = cisco:ios:config
index = network
host_segment = 4
```

**Windows endpoint audit (for Teredo/ISATAP):**
```powershell
# Check for Teredo
Get-NetTeredoConfiguration | Select-Object Type, ServerName
# Check for ISATAP
Get-NetIsatapConfiguration | Select-Object State, Router
```
Collect via Splunk UF with a scripted input.

### Step 2 — Create monitoring searches

**Fleet-wide deprecation summary:**
```spl
index=network sourcetype="cisco:*:config" earliest=-7d
| dedup host
| eval site_local=if(match(_raw, "(?i)fec0::"), 1, 0)
| eval eui64=if(match(_raw, "(?i)eui-64"), 1, 0)
| eval sixto4=if(match(_raw, "(?i)6to4"), 1, 0)
| eval rh0=if(match(_raw, "(?i)source-route"), 1, 0)
| stats sum(site_local) as site_local sum(eui64) as eui64 sum(sixto4) as sixto4 sum(rh0) as rh0
| eval total_deprecations=site_local + eui64 + sixto4 + rh0
```

**Remediation tracking:**
```spl
index=network sourcetype="cisco:*:config" earliest=-90d
| dedup host, _time
| eval deprecated=if(
    match(_raw, "(?i)fec0::|3ffe::|eui-64|6to4|teredo|isatap|source-route"), 1, 0)
| timechart span=1w dc(eval(if(deprecated=1, host, null()))) as devices_with_deprecated
```

### Step 3 — Validate
(a) **Manual spot-check.** SSH to a flagged device. Run `show running-config | include eui-64` (or equivalent) to confirm the deprecated feature is actually configured.

(b) **False positive test.** Verify that configuration comments containing deprecated terms don't trigger false positives. If they do, refine regex to match only active configuration lines.

(c) **Remediation test.** Remove a deprecated feature from a lab device. Verify the device disappears from the deprecation report within one config collection cycle.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Operational Hygiene"):
- Row 1 — Single-values: total deprecated findings, devices affected.
- Row 2 — Bar chart: finding types across the fleet.
- Row 3 — Table: per-device findings with RFC references.
- Row 4 — Trend: remediation progress over time.

**Scheduled report:** Weekly. Send to network operations team with remediation priorities.

**Remediation runbook:**
1. **RH0 (Routing Header Type 0):** Remove immediately. `no ipv6 source-route` is the default on modern IOS. Verify with `show ipv6 source-route`.
2. **6to4/Teredo/ISATAP:** Remove tunnel interfaces. If still needed for legacy connectivity, plan migration to native dual-stack.
3. **EUI-64:** Replace with `ipv6 address autoconfig default` (which uses RFC 7217 on modern IOS-XE) or static addressing.
4. **Site-local (fec0::):** Replace with ULA (fd00::/8) if site-scoped addressing is needed, or with GUA.

### Step 5 — Troubleshooting

- **EUI-64 still appearing after remediation.** Some older IOS versions default to EUI-64 for SLAAC. Verify the IOS version supports RFC 7217 (IOS-XE 16.3+ / IOS 15.6+). If not, use static addressing.

- **6to4 traffic still flowing.** Even after removing the tunnel interface, hosts may generate 6to4 traffic if their OS has 6to4 enabled. Disable 6to4 on endpoints: Windows — `netsh interface 6to4 set state disabled`; Linux — `modprobe -r sit`.

- **Config parser limitations.** Some configuration parsers may not capture the full running configuration (e.g., crypto maps, route-maps). Ensure the config collection tool exports the complete configuration.

## SPL

```spl
index=network (sourcetype="cisco:ios:config" OR sourcetype="cisco:iosxe:config") earliest=-7d
| dedup host
| eval site_local=if(match(_raw, "(?i)fec0::"), 1, 0)
| eval sixbone=if(match(_raw, "(?i)3ffe::"), 1, 0)
| eval eui64=if(match(_raw, "(?i)eui-64|eui64"), 1, 0)
| eval sixto4=if(match(_raw, "(?i)tunnel mode ipv6ip 6to4|2002::"), 1, 0)
| eval teredo=if(match(_raw, "(?i)teredo|2001:0000::"), 1, 0)
| eval isatap=if(match(_raw, "(?i)isatap"), 1, 0)
| eval rh0=if(match(_raw, "(?i)ipv6 source-route|routing-header type 0"), 1, 0)
| eval total_checks=7
| eval deprecated_found=site_local + sixbone + eui64 + sixto4 + teredo + isatap + rh0
| where deprecated_found > 0
| eval findings=mvappend(
    if(site_local=1, "fec0::/10 site-local address (RFC 3879 — deprecated 2004)", null()),
    if(sixbone=1, "3ffe::/16 6bone address (RFC 3701 — decommissioned 2006)", null()),
    if(eui64=1, "EUI-64 interface ID (RFC 8064 — deprecated; use RFC 7217)", null()),
    if(sixto4=1, "6to4 tunnel (RFC 7526 — deprecated 2015)", null()),
    if(teredo=1, "Teredo tunnel (deprecated for enterprise use)", null()),
    if(isatap=1, "ISATAP tunnel (deprecated by Microsoft)", null()),
    if(rh0=1, "Routing Header Type 0 enabled (RFC 5095 — deprecated 2007, MUST drop)", null()))
| table host, deprecated_found, findings
| sort -deprecated_found
```

## Visualization

(1) Table: devices with deprecated IPv6 features. (2) Bar chart: finding types across the fleet. (3) Single-value: total devices with deprecated configurations. (4) Trend: remediation progress over time.

## Known False Positives

**Lab/test environments.** Some deprecated features may be intentionally configured in lab environments for testing or training. Exclude lab devices from production audits.

**Legacy documentation.** Configuration comments or description fields may reference deprecated addresses without actually configuring them. Verify the match appears in an active configuration stanza, not a comment.

**EUI-64 on point-to-point links.** Some operators intentionally use EUI-64 on router-to-router point-to-point links where privacy is not a concern. Document exceptions rather than suppressing the finding.

## References

- [RFC 3879 — Deprecating Site Local Addresses](https://www.rfc-editor.org/rfc/rfc3879)
- [RFC 7526 — Deprecating the Anycast Prefix for 6to4 Relay Routers](https://www.rfc-editor.org/rfc/rfc7526)
- [RFC 5095 — Deprecation of Type 0 Routing Headers in IPv6](https://www.rfc-editor.org/rfc/rfc5095)
- [RFC 8064 — Recommendation on Stable IPv6 Interface Identifiers (deprecates EUI-64)](https://www.rfc-editor.org/rfc/rfc8064)
