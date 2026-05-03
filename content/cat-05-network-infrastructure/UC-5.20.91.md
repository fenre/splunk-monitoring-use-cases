<!-- AUTO-GENERATED from UC-5.20.91.json — DO NOT EDIT -->

---
id: "5.20.91"
title: "CIS Benchmark IPv6 Hardening Compliance Audit"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.91 · CIS Benchmark IPv6 Hardening Compliance Audit

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*There's an international safety checklist (CIS Benchmarks) for securing computers. Several items on the checklist are about the new postal system (IPv6). We check every computer against the list: 'Is the new mailbox locked when not in use? Does it reject fake postman announcements? Is the firewall configured for new-format letters?' We report which computers aren't following the safety rules.*

---

## Description

Audits host and network device configurations against CIS Benchmark IPv6 hardening controls. CIS Benchmarks provide specific, testable requirements for disabling unnecessary IPv6 features, blocking dangerous IPv6 protocol behaviour, and hardening IPv6 firewall rules. Key controls include disabling RA acceptance on servers (prevents rogue RA attacks), disabling IPv6 redirects (prevents MITM), and configuring ip6tables/nftables with default DROP policies.

## Value

CIS Benchmarks are the most widely-adopted hardening standards used in compliance audits (SOC 2, PCI DSS, HIPAA). IPv6-specific CIS controls are frequently overlooked because many organisations have not explicitly deployed IPv6. However, IPv6 is enabled by default on all modern operating systems, making these controls security-critical even in 'IPv4-only' environments. Automated compliance checking ensures consistent hardening across the fleet.

## Implementation

Collect sysctl values from Linux hosts and registry settings from Windows hosts. Compare against CIS Benchmark requirements. Score compliance percentage per host and per control. Alert on non-compliant systems.

## Detailed Implementation

### Prerequisites
- Splunk Universal Forwarder on Linux/Windows hosts.
- sysctl collection configured (Linux).
- Registry monitoring configured (Windows).
- CIS Benchmark documents for applicable platforms.

### Step 1 — Configure data collection

**Linux sysctl collection (inputs.conf):**
```
[script://./bin/sysctl_ipv6.sh]
interval = 86400
sourcetype = linux:sysctl
index = os

# sysctl_ipv6.sh:
#!/bin/bash
sysctl net.ipv6.conf.all.accept_ra
sysctl net.ipv6.conf.all.accept_redirects
sysctl net.ipv6.conf.all.forwarding
sysctl net.ipv6.conf.all.disable_ipv6
sysctl net.ipv6.conf.default.accept_ra
sysctl net.ipv6.conf.default.accept_redirects
```

**Windows registry monitoring (inputs.conf):**
```
[WinRegMon://IPv6Settings]
hive = HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters
baseline = 1
index = os
sourcetype = WinRegistry
```

**ip6tables/nftables default policy check:**
```bash
#!/bin/bash
# Check ip6tables default policies
ip6tables -L INPUT -n | head -1 | grep -q 'DROP\|REJECT' && echo 'ip6tables.input.default_policy=DROP' || echo 'ip6tables.input.default_policy=ACCEPT'
ip6tables -L FORWARD -n | head -1 | grep -q 'DROP\|REJECT' && echo 'ip6tables.forward.default_policy=DROP' || echo 'ip6tables.forward.default_policy=ACCEPT'
```

**Verification:**
```spl
index=os sourcetype="linux:sysctl" "net.ipv6" | stats count by host
```

### Step 2 — Create compliance dashboard

**Per-control compliance rate:**
```spl
index=os sourcetype="linux:sysctl" earliest=-7d
| rex field=_raw "(?<sysctl_key>net\.ipv6\.[^=]+)\s*=\s*(?<value>\d+)"
| eval expected=case(
    sysctl_key="net.ipv6.conf.all.accept_ra", 0,
    sysctl_key="net.ipv6.conf.all.accept_redirects", 0,
    sysctl_key="net.ipv6.conf.all.forwarding", 0,
    sysctl_key="net.ipv6.conf.default.accept_ra", 0,
    sysctl_key="net.ipv6.conf.default.accept_redirects", 0)
| eval compliant=if(tonumber(value)=expected, 1, 0)
| stats count(eval(compliant=1)) as passed count(eval(compliant=0)) as failed by sysctl_key
| eval compliance_pct=round(passed / (passed + failed) * 100, 0) . "%"
| sort compliance_pct
```

**Windows CIS IPv6 compliance:**
```spl
index=os sourcetype="WinRegistry" "DisableIPSourceRouting" "IPv6"
| rex field=data "(?<reg_value>\d+)"
| eval compliant=if(reg_value="2", "PASS", "FAIL — CIS 18.4.21")
| stats count by host, compliant
```

### Step 3 — Validate
(a) **Manual verification.** SSH to 3 sample Linux servers. Run `sysctl net.ipv6.conf.all.accept_ra` and compare with SPL results.

(b) **Remediation test.** On a non-compliant test host, apply `sysctl -w net.ipv6.conf.all.accept_ra=0`. Verify the next collection shows compliance.

(c) **ip6tables check.** Run `ip6tables -L -n` on sample hosts. Verify INPUT and FORWARD default policies are DROP.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — CIS Benchmark Compliance"):
- Row 1 — Single-value: fleet CIS IPv6 compliance percentage (target: 100% for servers).
- Row 2 — Bar chart: compliance rate by CIS control.
- Row 3 — Table: non-compliant hosts with specific findings and CIS control IDs.
- Row 4 — Trend: compliance improvement over quarterly assessments.

**Alert:** Server with `accept_ra = 1` — high severity. Server accepting Router Advertisements is vulnerable to rogue RA attack.

**Runbook:**
1. `accept_ra = 1` on server: Apply `sysctl -w net.ipv6.conf.all.accept_ra=0` and make persistent in `/etc/sysctl.d/99-ipv6-hardening.conf`.
2. `accept_redirects = 1`: Apply `sysctl -w net.ipv6.conf.all.accept_redirects=0`.
3. ip6tables default ACCEPT: Configure `ip6tables -P INPUT DROP` and `ip6tables -P FORWARD DROP` with explicit allow rules.

### Step 5 — Troubleshooting

- **CIS control applicability.** Not all CIS IPv6 controls apply to all systems. Disable-IPv6 (3.1.1) breaks systems that need IPv6. Create an exceptions lookup with justification.

- **sysctl persistence.** Runtime sysctl changes (`sysctl -w`) are lost on reboot. Ensure changes are persisted in `/etc/sysctl.d/` or `/etc/sysctl.conf`.

- **Container hosts.** Docker and Kubernetes hosts may need `forwarding = 1` and `accept_ra = 1` for container networking. Document these as justified exceptions in the compliance framework.

## SPL

```spl
index=os (sourcetype="linux:sysctl" OR sourcetype="WinRegistry") earliest=-7d
| eval control=case(
    match(_raw, "net.ipv6.conf.all.accept_ra"), "accept_ra",
    match(_raw, "net.ipv6.conf.all.accept_redirects"), "accept_redirects",
    match(_raw, "net.ipv6.conf.all.forwarding"), "forwarding",
    match(_raw, "net.ipv6.conf.all.disable_ipv6"), "disable_ipv6",
    match(_raw, "DisableIPSourceRouting.*IPv6"), "source_routing_win",
    1=1, null())
| where isnotnull(control)
| rex field=_raw "=\s*(?<value>\d+)"
| eval compliant=case(
    control="accept_ra" AND value="0", 1,
    control="accept_redirects" AND value="0", 1,
    control="forwarding" AND value="0", 1,
    control="disable_ipv6" AND value="1", 1,
    control="source_routing_win" AND value="2", 1,
    1=1, 0)
| stats count(eval(compliant=1)) as passed count(eval(compliant=0)) as failed by host, control
| where failed > 0
| eval finding=case(
    control="accept_ra", "CIS 3.2.9 — Host accepts Router Advertisements (should be disabled on servers)",
    control="accept_redirects", "CIS 3.2.10 — Host accepts ICMPv6 Redirects (MITM risk)",
    control="forwarding", "CIS 3.2.11 — IPv6 forwarding enabled on non-router (host acting as router)",
    control="disable_ipv6", "CIS 3.1.1 — IPv6 NOT disabled (required if not in use)",
    control="source_routing_win", "CIS 18.4.21 — IPv6 source routing not disabled on Windows")
| sort host, control
```

## Visualization

(1) Single-value: fleet CIS IPv6 compliance percentage. (2) Heatmap: compliance by control and host group. (3) Table: non-compliant hosts with specific findings. (4) Trend: compliance improvement over time.

## Known False Positives

**IPv6 intentionally deployed.** On systems where IPv6 is intentionally used, `disable_ipv6 = 1` would break connectivity. Apply this control only to systems that do not need IPv6.

**Routers and gateways.** `forwarding = 0` and `accept_ra = 0` do not apply to systems acting as IPv6 routers or gateways. Exclude router-role hosts from these checks.

**Dynamic workstations.** Desktop/laptop systems that roam between networks may need `accept_ra = 1` for SLAAC. Apply the RA rejection control only to servers with static addresses.

**Docker/container hosts.** Container networking may require IPv6 forwarding enabled. Document these as accepted exceptions.

## References

- [CIS Benchmarks — Download Center (Linux, Windows, Network Device benchmarks)](https://www.cisecurity.org/cis-benchmarks)
- [CIS Ubuntu Linux 22.04 LTS Benchmark v2.0.0 (§3.1-3.5 — IPv6 hardening)](https://www.cisecurity.org/benchmark/ubuntu_linux)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3 — host hardening)](https://www.rfc-editor.org/rfc/rfc9099)
