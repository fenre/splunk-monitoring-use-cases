<!-- AUTO-GENERATED from UC-5.20.29.json — DO NOT EDIT -->

---
id: "5.20.29"
title: "RA Guard Enforcement Coverage Audit"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.20.29 · RA Guard Enforcement Coverage Audit

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Every network port where a user plugs in their device should have a guard that blocks fake 'I am the router' announcements. This use case checks every port on every switch to make sure the guard is actually turned on. Even one unguarded port is like leaving one door unlocked — an intruder only needs to find that one opening.*

---

## Description

Audits RA Guard deployment coverage across all access-facing switch ports in the network to verify that every access port is protected against rogue Router Advertisements. RA Guard (RFC 6105) is the foundational IPv6 first-hop security control — it prevents unauthorised devices from sending Router Advertisements that can redirect traffic, assign malicious prefixes, or disrupt IPv6 connectivity for an entire VLAN. However, RA Guard only works when deployed on every access port. A single unprotected access port on a VLAN allows an attacker to plug in and send rogue RAs that reach all hosts on that VLAN, regardless of whether other ports are protected.

RFC 9099 §2.3.2.4 explicitly recommends deploying RA Guard on all access ports as a baseline IPv6 security control. DISA STIG requires RA Guard on all access-layer ports in DoD networks.

## Value

Without RA Guard, any device on an access port can become a rogue router by sending a single ICMPv6 Type 134 packet. This is trivially easy — enabling IPv6 forwarding on a laptop or running THC-IPv6 `fake_router6` takes seconds. The damage is immediate and VLAN-wide: all hosts process the rogue RA and may change their default gateway, prefix, or DNS server. RA Guard is the only switch-level control that prevents this. Auditing coverage ensures that the protection is actually deployed where it matters — on every access port that connects end-user devices. A 95% deployment rate means 5% of ports are attack vectors, and an attacker only needs to find one.

## Implementation

Collect running configurations from all switches. Parse interface configurations to identify access ports (switchport mode access) and check for the presence of RA Guard policy attachment. Calculate coverage percentage per switch and network-wide. Alert on any switch with <100% coverage on access ports.

## Detailed Implementation

### Prerequisites
- Access to running configurations from all access-layer switches. This can be collected via:
  - Cisco DNA Center / Catalyst Center configuration archive
  - RANCID/Oxidized configuration backup
  - Scripted SSH collection (`show running-config`)
  - SNMP-based configuration retrieval
- A reference list of all access-layer switches in the network.
- Understanding of which ports are access (user-facing) vs trunk (switch-to-switch/router).

### Step 1 — Configure data collection

**Scripted configuration collection (recommended):**
```bash
#!/bin/bash
# collect_switch_configs.sh
for switch in $(cat /opt/splunk/etc/apps/ipv6_ops/lookups/access_switches.txt); do
  echo "=== $switch ==="
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 splunk-svc@$switch \
    "show running-config | section interface" 2>/dev/null
done
```
```
# inputs.conf
[script://./bin/collect_switch_configs.sh]
interval = 86400
sourcetype = cisco:ios:config
index = network
source = switch_config_audit
```
Run daily — configuration audits don't need real-time frequency.

**Alternative — SISF policy summary via CLI:**
```bash
#!/bin/bash
# sisf_raguard_audit.sh
for switch in $(cat /opt/splunk/etc/apps/ipv6_ops/lookups/access_switches.txt); do
  echo "=== $switch ==="
  ssh -o StrictHostKeyChecking=no splunk-svc@$switch \
    "show device-tracking policies" 2>/dev/null
  echo "---INTERFACES---"
  ssh -o StrictHostKeyChecking=no splunk-svc@$switch \
    "show ipv6 nd raguard policy" 2>/dev/null
done
```

**Cisco IOS-XE RA Guard deployment (reference):**
```
! Define RA Guard policies
ipv6 nd raguard policy RA_ROUTER
 device-role router
!
ipv6 nd raguard policy RA_HOST
 device-role host
!
! Apply to interfaces
interface range GigabitEthernet1/0/1 - 48
 switchport mode access
 ipv6 nd raguard attach-policy RA_HOST
!
interface GigabitEthernet1/0/49
 switchport mode trunk
 ipv6 nd raguard attach-policy RA_ROUTER
```

**Verification:**
```spl
index=network sourcetype="cisco:ios:config" earliest=-2d
| stats count by host
```

### Step 2 — Create the search and alert

**Primary audit — RA Guard coverage per switch:**
```spl
index=network sourcetype="cisco:ios:config" earliest=-2d
| rex max_match=0 field=_raw "(?ms)(?:^|\n)interface\s+(?<iface>(?:Gi|Te|Tw|Fa)\S+)(?<iface_config>[\s\S]*?)(?=\ninterface\s|\n!|$)"
| eval combined=mvzip(iface, iface_config, "|||")
| mvexpand combined
| rex field=combined "(?<interface>[^|]+)\|\|\|(?<config>.+)"
| eval is_access=if(match(config, "switchport mode access"), 1, 0)
| eval has_raguard=if(match(config, "raguard"), 1, 0)
| where is_access=1
| stats sum(has_raguard) as protected sum(eval(1-has_raguard)) as unprotected by host
| eval total=protected + unprotected
| eval coverage_pct=round(protected / total * 100, 1)
| eval status=case(
    coverage_pct=100, "COMPLIANT",
    coverage_pct >= 90, "NEAR-COMPLIANT",
    coverage_pct >= 50, "PARTIAL",
    1=1, "NON-COMPLIANT")
| sort coverage_pct
| table host, protected, unprotected, total, coverage_pct, status
```

**Alert — switches with gaps:**
```spl
<above search>
| where coverage_pct < 100
```
Trigger: any result. Priority: CRITICAL for <50%, HIGH for <100%.

**Network-wide summary:**
```spl
<above search>
| stats sum(protected) as total_protected sum(unprotected) as total_unprotected
| eval network_coverage=round(total_protected / (total_protected + total_unprotected) * 100, 1)
| eval target=100
```

### Step 3 — Validate
(a) **Spot-check.** Pick 3 switches and manually verify the configuration: `show running-config | include raguard`. Count the access ports with and without RA Guard. Compare with the Splunk audit results.

(b) **Intentional gap test.** On a lab switch, remove RA Guard from one access port: `no ipv6 nd raguard attach-policy RA_HOST`. Re-run the audit. Verify the switch shows coverage_pct < 100% and the unprotected port count increases by 1.

(c) **Trunk port exclusion.** Verify that trunk ports (switchport mode trunk) are NOT flagged as 'unprotected' — they should be excluded from the access-port coverage calculation.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — First-Hop Security Coverage"):
- Row 1 — Single-value: network-wide RA Guard coverage %, switches at 100%, switches below 100%.
- Row 2 — Table: per-switch audit results sorted by coverage (worst first).
- Row 3 — Bar chart: coverage percentage by switch — visual gap identification.
- Row 4 — Drilldown: click a switch to see specific unprotected interfaces.

**Scheduling:** Daily configuration audit (run config collection script overnight). Alert evaluation daily.

**Runbook:**
1. Switch at <100% coverage:
   a. Generate the list of unprotected access ports.
   b. Apply RA Guard: `interface <port>` → `ipv6 nd raguard attach-policy RA_HOST`.
   c. If the switch doesn't support RA Guard, apply a port ACL: `ipv6 access-list BLOCK_RA` → `deny icmp any any router-advertisement` → apply to the interface.
2. New switch deployment: include RA Guard in the standard switch template. Verify coverage within 24 hours of deployment.
3. Hardware limitation: document switches that cannot support RA Guard and compensate with alternative controls.

### Step 5 — Troubleshooting

- **Configuration parsing fails** — The regex for interface-section extraction is complex. If it fails, simplify: collect `show ipv6 nd raguard interface` which lists all interfaces with RA Guard attached. Compare against `show interfaces status` for all access ports.

- **RA Guard blocks legitimate RAs on uplink** — If a trunk/uplink port accidentally gets the 'host' RA Guard policy, legitimate RAs from routers will be dropped. Verify uplink ports have the 'router' role policy.

- **RA Guard bypass via fragmentation** — Older IOS versions are vulnerable to RA Guard bypass using IPv6 fragmentation (RFC 7113). Ensure switches run IOS-XE 16.x+ and use `ipv6 nd raguard` with reassembly support. Verify with: `show ipv6 nd raguard policy <name>` — should show `Fragment: ENABLED` (reassembly).

## SPL

```spl
index=network sourcetype="cisco:ios:config" OR sourcetype="config:running"
| rex max_match=0 "interface\s+(?<interface>\S+).*?(?=interface\s|$)" 
| mvexpand interface
| eval has_raguard=if(match(_raw, interface . "[\s\S]*?raguard"), "YES", "NO")
| eval is_access=if(match(_raw, interface . "[\s\S]*?switchport mode access"), "YES", "NO")
| where is_access="YES"
| stats count(eval(has_raguard="YES")) as protected count(eval(has_raguard="NO")) as unprotected by host
| eval coverage_pct=round(protected / (protected + unprotected) * 100, 1)
| eval status=case(
    coverage_pct=100, "COMPLIANT",
    coverage_pct >= 80, "PARTIAL — gaps exist",
    1=1, "NON-COMPLIANT — significant gaps")
| sort coverage_pct
```

## Visualization

(1) Single-value: network-wide RA Guard coverage percentage. (2) Table: per-switch coverage with protected/unprotected port counts. (3) Bar chart: switches sorted by coverage percentage — worst performers highlighted. (4) Drilldown: click on a switch to see the list of unprotected access ports.

## Known False Positives

**Trunk ports and uplink ports.** These connect to other switches or routers and should NOT have RA Guard in 'host' mode — they need to pass legitimate RAs. The audit should only count access ports (switchport mode access) as needing RA Guard protection.

**Ports intentionally exempted.** Some ports connect to legitimate IPv6 routers in non-standard locations (e.g., a lab router connected to an access port for testing). These should be explicitly documented as 'router' role in the RA Guard policy, not left unprotected.

**Switches that don't support RA Guard.** Older or lower-end switches may not support RA Guard. These should be flagged as 'hardware limitation' and compensated with other controls (e.g., port ACLs blocking ICMPv6 Type 134).

## References

- [RFC 6105 — IPv6 Router Advertisement Guard (RA Guard specification for Layer 2 switches)](https://www.rfc-editor.org/rfc/rfc6105)
- [RFC 7113 — Implementation Advice for IPv6 Router Advertisement Guard (RA Guard bypass mitigations, extended header handling)](https://www.rfc-editor.org/rfc/rfc7113)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.2.4 — RA Guard deployment recommendation)](https://www.rfc-editor.org/rfc/rfc9099)
- [Cisco SISF Configuration Guide — RA Guard and Device Tracking Policy](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sisf/configuration/xe-17/sisf-xe-17-book.html)
