<!-- AUTO-GENERATED from UC-5.20.87.json — DO NOT EDIT -->

---
id: "5.20.87"
title: "IPv6 Management Plane Transport Readiness Audit"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.87 · IPv6 Management Plane Transport Readiness Audit

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*Our maintenance crew uses specific tools (SSH, SNMP, syslog) to manage the postal infrastructure. These tools were designed for the old address system (IPv4). Before we can switch the maintenance network to the new address system (IPv6), we need to check that every tool works with new addresses. If we switch before checking, the maintenance crew gets locked out.*

---

## Description

Audits management plane protocol configurations for IPv6 transport readiness across SSH, SNMP, syslog, NTP, TACACS+, RADIUS, and NETCONF/gRPC. As networks transition toward IPv6, the management infrastructure must also support IPv6 transport. A common failure scenario: the management network is migrated to IPv6-only, but TACACS+ is configured with IPv4 addresses only, locking out all administrators.

## Value

Management plane IPv6 readiness is a prerequisite for IPv6-only network operations. If management protocols are IPv4-dependent, the organisation cannot decommission IPv4 on the management network without losing administrative access, AAA, monitoring, and time synchronisation. This audit identifies which management protocols need IPv6 transport configuration before an IPv6-only management transition.

## Implementation

Parse running configurations for management protocol server addresses. Check whether IPv6 addresses are configured alongside or instead of IPv4 addresses. Score readiness percentage. Track readiness improvement over time.

## Detailed Implementation

### Prerequisites
- Running configuration collection from all managed devices.
- Inventory of management infrastructure components (AAA servers, syslog collectors, NTP servers, SNMP managers).
- Knowledge of which management infrastructure supports IPv6.

### Step 1 — Configure data collection

**Example IPv6-ready management configuration (Cisco IOS-XE):**
```
! SSH over IPv6
ip ssh version 2
line vty 0 15
 transport input ssh
 ipv6 access-class MGMT-ACLv6 in
!
! SNMP v3 over IPv6
snmp-server host 2001:db8:mgmt::100 version 3 priv SNMP_USER
!
! Syslog over IPv6
logging host ipv6 2001:db8:mgmt::200
!
! NTP over IPv6
ntp server ipv6 2001:db8:mgmt::10
ntp server ipv6 2001:db8:mgmt::11
!
! TACACS+ over IPv6
tacacs server ISE-PRIMARY
 address ipv6 2001:db8:mgmt::50
 key 0 <shared_secret>
!
! RADIUS over IPv6
radius server ISE-RADIUS
 address ipv6 2001:db8:mgmt::50 auth-port 1812 acct-port 1813
```

**Verification:**
```spl
index=network sourcetype="cisco:ios:config" "ipv6" ("logging host" OR "ntp server" OR "snmp-server host" OR "tacacs server" OR "radius server") | stats count by host
```

### Step 2 — Create readiness assessment

**Per-protocol readiness analysis:**
```spl
index=network (sourcetype="cisco:ios:config" OR sourcetype="cisco:iosxe:config") earliest=-7d
| dedup host
| eval ssh_v4=if(match(_raw, "(?i)ip ssh|ssh.*ipv4"), 1, 0)
| eval ssh_v6=if(match(_raw, "(?i)ipv6.*ssh|ssh.*ipv6"), 1, 0)
| eval syslog_v4=if(match(_raw, "(?i)logging host\s+\d+\.\d+\.\d+\.\d+"), 1, 0)
| eval syslog_v6=if(match(_raw, "(?i)logging host\s+(ipv6\s+)?[0-9a-fA-F]+:"), 1, 0)
| eval ntp_v4=if(match(_raw, "(?i)ntp server\s+\d+\.\d+\.\d+\.\d+"), 1, 0)
| eval ntp_v6=if(match(_raw, "(?i)ntp server\s+(ipv6\s+)?[0-9a-fA-F]+:"), 1, 0)
| eval tacacs_v4=if(match(_raw, "(?i)tacacs.*address\s+ipv4"), 1, 0)
| eval tacacs_v6=if(match(_raw, "(?i)tacacs.*address\s+ipv6"), 1, 0)
| stats count(eval(syslog_v6=1)) as syslog_ready count(eval(ntp_v6=1)) as ntp_ready count(eval(tacacs_v6=1)) as tacacs_ready count as total_devices
| eval syslog_pct=round(syslog_ready/total_devices*100, 0)
| eval ntp_pct=round(ntp_ready/total_devices*100, 0)
| eval tacacs_pct=round(tacacs_ready/total_devices*100, 0)
```

### Step 3 — Validate
(a) **SSH connectivity test.** From a management host, `ssh -6 admin@[2001:db8:mgmt::1]` to verify SSH over IPv6 works.

(b) **TACACS+ test.** Configure a test device with TACACS+ over IPv6. Verify authentication succeeds with `test aaa group tacacs+ <user> <pass> new-code`.

(c) **NTP sync.** Verify `show ntp associations` shows IPv6 NTP peers with synchronized status.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Management Plane Readiness"):
- Row 1 — Single-value: fleet management IPv6 readiness percentage.
- Row 2 — Bar chart: readiness percentage by protocol (SSH, SNMP, syslog, NTP, TACACS+, RADIUS, NETCONF).
- Row 3 — Table: devices with per-protocol readiness detail.
- Row 4 — Trend: readiness improvement over quarterly assessments.

**Scheduling:** Quarterly assessment aligned with IPv6 migration milestones.

**Runbook:**
1. TACACS+ not IPv6-ready: Verify ISE/ACS supports IPv6 transport. Configure `address ipv6` on tacacs server blocks.
2. Syslog not IPv6-ready: Verify syslog collector listens on IPv6. Configure `logging host ipv6 <addr>`.
3. NTP not IPv6-ready: Add IPv6 NTP peer addresses. Verify reachability with `ping ipv6 <ntp_server>`.

### Step 5 — Troubleshooting

- **TACACS+ IPv6 minimum IOS version.** TACACS+ over IPv6 requires IOS 15.4 or IOS-XE 3.13. Older platforms must maintain IPv4 management connectivity for AAA.

- **Syslog collector support.** Verify the syslog collector (rsyslog, syslog-ng, Splunk HEC) is configured to listen on IPv6. rsyslog requires `module(load="imudp") input(type="imudp" address="::" port="514")` for IPv6.

- **SNMP trap destinations.** SNMP traps to IPv6 destinations require the full address in bracket notation on some platforms. Test with `snmp-server host 2001:db8:mgmt::100`.

## SPL

```spl
index=network (sourcetype="cisco:ios:config" OR sourcetype="cisco:iosxe:config") earliest=-7d
| dedup host
| eval ssh_ipv6=if(match(_raw, "(?i)ip ssh.*ipv6|transport input ssh"), 1, 0)
| eval snmp_ipv6=if(match(_raw, "(?i)snmp-server host\s+[0-9a-fA-F:]+"), 1, 0)
| eval syslog_ipv6=if(match(_raw, "(?i)logging host\s+(ipv6\s+)?[0-9a-fA-F:]+"), 1, 0)
| eval ntp_ipv6=if(match(_raw, "(?i)ntp server\s+(ipv6\s+)?[0-9a-fA-F:]+"), 1, 0)
| eval tacacs_ipv6=if(match(_raw, "(?i)tacacs server.*address ipv6"), 1, 0)
| eval radius_ipv6=if(match(_raw, "(?i)radius server.*address ipv6"), 1, 0)
| eval netconf_ipv6=if(match(_raw, "(?i)netconf.*ipv6|gnmi.*ipv6"), 1, 0)
| eval total_protocols=7
| eval ipv6_ready=ssh_ipv6 + snmp_ipv6 + syslog_ipv6 + ntp_ipv6 + tacacs_ipv6 + radius_ipv6 + netconf_ipv6
| eval readiness_pct=round(ipv6_ready / total_protocols * 100, 0)
| eval status=case(
    readiness_pct=100, "FULLY READY — all management protocols support IPv6",
    readiness_pct >= 70, "MOSTLY READY — " . (total_protocols - ipv6_ready) . " protocols lack IPv6 transport",
    readiness_pct >= 40, "PARTIALLY READY — significant management IPv6 gaps",
    1=1, "NOT READY — management plane is IPv4-dependent")
| table host, ssh_ipv6, snmp_ipv6, syslog_ipv6, ntp_ipv6, tacacs_ipv6, radius_ipv6, netconf_ipv6, readiness_pct, status
| sort readiness_pct
```

## Visualization

(1) Single-value: fleet management IPv6 readiness percentage. (2) Table: per-device readiness matrix with protocol-level detail. (3) Bar chart: readiness by protocol (identifies which protocols are most commonly IPv4-only). (4) Trend: readiness improvement over quarterly assessments.

## Known False Positives

**Intentionally IPv4-only management.** Some organisations deliberately maintain a separate IPv4-only out-of-band management network. In this case, IPv6 management transport is not required and should be marked as 'N/A'.

**Platform limitations.** Older IOS versions may not support all management protocols over IPv6. Check IOS feature navigator for per-protocol IPv6 support.

**Dual-stack management.** In dual-stack management networks, IPv4 management configurations are still valid. The audit identifies readiness for IPv6-only, not a requirement to remove IPv4.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§3.2 — management plane)](https://www.rfc-editor.org/rfc/rfc9099)
- [Cisco IOS IPv6 Management Plane Configuration Guide](https://www.cisco.com/c/en/us/)
- [RFC 6613 — RADIUS over TCP (enables IPv6 transport for RADIUS)](https://www.rfc-editor.org/rfc/rfc6613)
