<!-- AUTO-GENERATED from UC-5.20.17.json — DO NOT EDIT -->

---
id: "5.20.17"
title: "SLAAC M-bit/O-bit/A-bit Flag Consistency Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "ITSI"
---

# UC-5.20.17 · SLAAC M-bit/O-bit/A-bit Flag Consistency Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** ITSI &middot; **Type:** Configuration, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*When a device joins an IPv6 network, the router sends it instructions: 'Here is how you should get your address.' If two routers on the same network give different instructions — one says 'choose your own address' while the other says 'ask the address server' — devices get confused and some might not connect properly. We watch for these conflicting instructions.*

---

## Description

Monitors the M (Managed), O (Other Configuration), and A (Autonomous) flags in IPv6 Router Advertisements to detect inconsistency between routers advertising the same prefix. When two routers on the same VLAN advertise the same prefix but with different flag settings — for example, Router A sends M=0,O=1,A=1 (SLAAC + DHCPv6 DNS) while Router B sends M=1,O=1,A=0 (DHCPv6-only) — hosts receive conflicting instructions. The result depends on which RA a host processes first: some hosts get SLAAC addresses, others get DHCPv6 addresses, and some get both. This 'split-brain' addressing is extremely difficult to troubleshoot because it is non-deterministic and varies by OS. RFC 4861 Section 4.2 defines the flag semantics but does not require routers to coordinate — that responsibility falls on the operator and monitoring.

## Value

Split-brain address assignment is one of the most insidious IPv6 operational problems because it presents as intermittent connectivity issues that vary by device. A Windows host may prefer SLAAC while a Linux host prefers DHCPv6, and both work — until a firewall rule or ACL is written for one addressing method and misses the other. This use case catches the root cause (RA flag inconsistency) before it manifests as user-reported connectivity problems. It also detects the dangerous M=0,O=0,A=0 configuration (no addressing at all) and the M=1,A=1 dual-assignment scenario that doubles the number of IPv6 addresses per host, complicating forensics and consuming IPAM space.

## Implementation

Capture RA flags from syslog, RA Guard, or network TAP/SPAN analysis (Zeek). Compare flag settings per prefix across all advertising routers on each VLAN. Alert on inconsistencies and risky combinations. Schedule a daily audit report of all active prefixes and their flag configurations.

## Detailed Implementation

### Prerequisites
- At least one source of RA data: Cisco IOS/IOS-XE syslog with IPv6 ND debugging enabled, RA Guard logging, or a network TAP/SPAN feeding Zeek or Suricata for ICMPv6 Type 134 decode.
- Understanding of your intended addressing architecture per VLAN/prefix: SLAAC-only, SLAAC+DHCPv6-DNS, or DHCPv6-only.
- A reference lookup (CSV or KV store) listing each prefix and its expected M/O/A flag configuration. Without this, the search can only detect inconsistency between routers — it cannot tell you which router is wrong.

### Step 1 — Configure data collection

**Option A: Cisco IOS/IOS-XE syslog (most common)**

Enable IPv6 ND logging on each VLAN interface:
```
interface Vlan100
 ipv6 nd ra-interval 200
 ipv6 nd prefix 2001:db8:100::/64
logging buffered 32768 informational
```
RAs are logged as part of normal ND operation. To see explicit flag details, you may need:
```
debug ipv6 nd
```
However, debug is high-volume and should only be used temporarily. For production, rely on RA Guard logging.

**Option B: RA Guard with syslog (preferred for security)**

RA Guard inspects every RA and logs violations:
```
! Define the RA Guard policy allowing only legitimate routers
ipv6 nd raguard policy RA_FROM_ROUTER
 device-role router
 match ra prefix-list IPV6_PREFIXES
!
! Apply to all access ports (where no RAs should originate)
interface range GigabitEthernet1/0/1 - 48
 ipv6 nd raguard attach-policy RA_FROM_ROUTER
```
RA Guard generates `%SISF-6-ENTRY_CREATED` logs for legitimate RAs and `%SISF-4-PAK_DROP` with `Reason:RA guard` for blocked RAs. Both contain flag information.

**Option C: Zeek/Corelight (best for deep decode)**

Zeek decodes ICMPv6 Type 134 and extracts all RA fields including M, O, and per-prefix A flags. Configure SPAN/TAP on each VLAN SVI or distribution switch uplink:
```
# zeek local.zeek
@load base/protocols/icmp
@load policy/protocols/conn/known-services
```
Zeek logs RA details to `icmp.log`. Forward to Splunk via Splunk Universal Forwarder with `sourcetype=corelight_zeek`.

**Verification:**
```spl
index=network ("ND_RA_PREFIX" OR "Router Advertisement" OR icmpv6_type=134) earliest=-24h
| stats count by sourcetype, host
| sort -count
```
Expected: one or more events per VLAN interface, from each router that advertises on that VLAN.

### Step 2 — Create the search and alert

**Primary search — RA flag consistency per prefix:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="syslog" OR sourcetype="corelight_zeek")
  ("ND_RA_PREFIX" OR "Router Advertisement" OR icmpv6_type=134)
  earliest=-24h
| rex field=_raw "M=(?<m_flag>\d)\s*O=(?<o_flag>\d)"
| rex field=_raw "prefix=(?<ra_prefix>[0-9a-fA-F:]+/\d+).*A=(?<a_flag>\d)"
| where isnotnull(ra_prefix)
| stats values(m_flag) as m_flags values(o_flag) as o_flags values(a_flag) as a_flags dc(host) as router_count values(host) as routers latest(_time) as last_seen by ra_prefix
| eval m_consistent=if(mvcount(m_flags)==1, "YES", "NO")
| eval o_consistent=if(mvcount(o_flags)==1, "YES", "NO")
| eval a_consistent=if(mvcount(a_flags)==1, "YES", "NO")
| eval inconsistent=if(m_consistent="NO" OR o_consistent="NO" OR a_consistent="NO", "YES", "NO")
| eval risk=case(
    mvindex(m_flags, 0)="0" AND mvindex(o_flags, 0)="0" AND mvindex(a_flags, 0)="0", "CRITICAL: No addressing — hosts cannot get IPv6 addresses",
    mvindex(m_flags, 0)="1" AND mvindex(a_flags, 0)="1", "WARNING: Dual-assignment — hosts get both SLAAC and DHCPv6 addresses",
    inconsistent="YES", "WARNING: Inconsistent flags between routers",
    1=1, "OK")
| sort -inconsistent, -risk
| table ra_prefix, m_flags, o_flags, a_flags, inconsistent, risk, router_count, routers, last_seen
```

**Understanding this SPL:**
- Groups by prefix and collects the distinct flag values from all advertising routers.
- If mvcount > 1 for any flag, that means different routers on the same segment are sending different flag values for the same prefix = inconsistency.
- The risk evaluation catches the two most dangerous configurations: no addressing at all (M=0,O=0,A=0) and dual-assignment (M=1,A=1).

**Alert — inconsistent RA flags detected:**
```spl
<above search>
| where inconsistent="YES" OR match(risk, "CRITICAL|WARNING")
```
Trigger: any result. Priority: medium for WARNING, high for CRITICAL. Action: email network engineering team with the prefix, routers involved, and flag mismatches.

**Lookup-based compliance check (optional, requires reference data):**
```spl
index=network ("ND_RA_PREFIX" OR "Router Advertisement" OR icmpv6_type=134) earliest=-24h
| rex field=_raw "M=(?<m_flag>\d)\s*O=(?<o_flag>\d)"
| rex field=_raw "prefix=(?<ra_prefix>[0-9a-fA-F:]+/\d+).*A=(?<a_flag>\d)"
| where isnotnull(ra_prefix)
| dedup ra_prefix, host
| lookup ipv6_prefix_plan.csv prefix as ra_prefix OUTPUT expected_m, expected_o, expected_a
| eval m_compliant=if(m_flag==expected_m, "YES", "NO")
| eval o_compliant=if(o_flag==expected_o, "YES", "NO")
| eval a_compliant=if(a_flag==expected_a, "YES", "NO")
| where m_compliant="NO" OR o_compliant="NO" OR a_compliant="NO"
```

### Step 3 — Validate
(a) **Controlled test.** On a lab VLAN with two routers, configure Router A with M=0,O=1,A=1 and Router B with M=1,O=1,A=0. Run the search — it should flag the prefix as inconsistent and show `WARNING: Inconsistent flags between routers`. Correct Router B to match Router A and re-run — the alert should clear.

(b) **Known configuration.** Pick a production VLAN where you know the intended configuration (e.g., M=0,O=1,A=1 for SLAAC + DHCPv6 DNS). Verify the search returns `OK` for that prefix with consistent flags.

(c) **Edge case — single router.** On a VLAN with only one router, the search should always show consistent flags (mvcount=1 for all flags). Verify `router_count=1`.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — RA Flag Consistency"):
- Row 1 — Single-value: count of prefixes with inconsistent flags, count of CRITICAL/WARNING configurations.
- Row 2 — Table: all active prefixes with their M/O/A flags, consistency status, and risk level. Colour-code: green=OK, yellow=WARNING, red=CRITICAL.
- Row 3 — Timechart: flag changes over time per prefix. A flag change is almost always unintentional — track when it happened and which router changed.

**Scheduling:** Run the consistency check every 4 hours (RAs have a default lifetime of 1800 seconds, so a 4-hour window captures at least 7 RA cycles). Alert immediately on CRITICAL (no addressing) or new inconsistencies.

**Runbook:**
1. CRITICAL: M=0,O=0,A=0 — Hosts on this prefix cannot obtain IPv6 addresses. Fix: enable A=1 on the prefix advertisement, or set M=1 and deploy DHCPv6.
2. WARNING: Inconsistent flags — Identify which router changed (check the timechart). Compare with the reference lookup or the network design document. Correct the non-conforming router.
3. WARNING: Dual-assignment — If intentional, document and suppress. If not, choose SLAAC-only (set M=0) or DHCPv6-only (set A=0) and update all advertising routers.

### Step 5 — Troubleshooting

- **No RA events in Splunk** — RAs are ICMPv6 Type 134 multicast messages (ff02::1). They are not logged by default on all platforms. Enable RA Guard (which logs all inspected RAs) or deploy Zeek/Suricata on a SPAN port. On Cisco, `show ipv6 interface <vlan>` displays current RA configuration but does not generate syslog unless ND debug is enabled.

- **Flags appear correct but hosts still get wrong addresses** — Some hosts (especially Android) ignore M=1 and only use SLAAC regardless. Other hosts (Windows) may configure both SLAAC and DHCPv6 addresses when M=1 and A=1. This use case monitors what routers advertise, not how hosts interpret the flags.

- **RA interval too infrequent for monitoring** — Default RA interval is 200 seconds (configurable 3-1800 seconds). If RAs are very infrequent, increase the search time window to 2x the RA interval to capture at least two RAs per router.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="syslog")
  ("ND_RA_PREFIX" OR "Router Advertisement" OR icmpv6_type=134)
| rex field=_raw "M=(?<m_flag>\d)\s*O=(?<o_flag>\d)"
| rex field=_raw "prefix=(?<ra_prefix>[0-9a-fA-F:]+/\d+).*A=(?<a_flag>\d)"
| stats values(m_flag) as m_flags values(o_flag) as o_flags values(a_flag) as a_flags dc(host) as router_count by ra_prefix
| eval flag_combo=mvjoin(m_flags, ",")."/".mvjoin(o_flags, ",")."/".mvjoin(a_flags, ",")
| eval inconsistent=if(mvcount(m_flags) > 1 OR mvcount(o_flags) > 1 OR mvcount(a_flags) > 1, "YES", "NO")
| eval risky=case(
    mvindex(m_flags, 0)="0" AND mvindex(o_flags, 0)="0" AND mvindex(a_flags, 0)="0", "CRITICAL: No addressing method configured",
    mvindex(m_flags, 0)="1" AND mvindex(a_flags, 0)="1", "WARNING: Both SLAAC and DHCPv6 active — hosts will get dual addresses",
    1=1, "OK"
  )
| table ra_prefix, flag_combo, inconsistent, risky, router_count
```

## Visualization

(1) Table: per-prefix flag summary with inconsistency and risk indicators. (2) Single-value: count of prefixes with inconsistent flags. (3) Timechart: trending of flag changes over time — a flag change mid-week usually indicates a misconfiguration. (4) Drilldown: click on a prefix to see the individual RAs from each router with timestamps.

## Known False Positives

**VRRP/HSRP active-standby transitions.** During a gateway failover, RAs may briefly originate from the new active router with slightly different timing, causing a transient 'inconsistency' alert until the old RAs expire (default RA lifetime = 1800 seconds). The flags themselves should be consistent between active and standby — if they differ, that is a genuine misconfiguration.

**Intentional M=1,A=1 (dual-assignment).** Some organisations intentionally configure both SLAAC and DHCPv6 addressing so that hosts get a SLAAC address for connectivity and a DHCPv6 address for DNS registration. This is a legitimate design choice but doubles the address count per host. If this is your intended architecture, suppress the M=1,A=1 warning for those specific prefixes.

**OS-dependent flag interpretation.** Android ignores the M-bit entirely and only uses SLAAC, regardless of flag settings. Windows and Linux honour both M and A bits. macOS honours M=1 but may also keep a SLAAC address. These OS behaviours don't change what the router advertises — this use case monitors router configuration consistency, not host behaviour.

## References

- [RFC 4861 — Neighbor Discovery for IP version 6 (§4.2 — Router Advertisement Message Format, M/O/A flag definitions)](https://www.rfc-editor.org/rfc/rfc4861)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.1 — Address architecture and autoconfiguration monitoring)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 7772 — Reducing Energy Consumption of Router Advertisements (BCP 202 — RA rate limiting for wireless environments)](https://www.rfc-editor.org/rfc/rfc7772)
