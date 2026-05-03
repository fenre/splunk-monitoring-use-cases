<!-- AUTO-GENERATED from UC-5.20.80.json — DO NOT EDIT -->

---
id: "5.20.80"
title: "RFC 8504 IPv6 Node Requirements Compliance Audit"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.80 · RFC 8504 IPv6 Node Requirements Compliance Audit

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Compliance &middot; **Wave:** Run &middot; **Status:** Verified

*There's a rule book (RFC 8504) that says every device on the new postal system (IPv6) must follow certain minimum standards — like having a proper letterbox, checking for duplicate addresses, and not putting your home address on the outside of every letter. We check each device against the rule book and flag any that aren't following the minimum standards.*

---

## Description

Audits IPv6 node behaviour against RFC 8504 (IPv6 Node Requirements), which specifies the minimum protocol capabilities every IPv6 host and router must implement. Detects devices using deprecated EUI-64 address generation (which exposes MAC addresses and enables tracking), devices not performing DAD, and devices with missing PMTUD support. RFC 8504 replaced RFC 6434 in 2019 with stricter requirements for stable identifiers and privacy.

## Value

RFC 8504 compliance ensures a baseline level of IPv6 interoperability and security across all devices. EUI-64 detection is particularly valuable — devices generating addresses with the ff:fe pattern in the interface identifier expose their MAC addresses to every device on the path, enabling persistent tracking across networks. RFC 7217 stable identifiers provide the same stability without the privacy exposure. Non-compliant devices are the most likely sources of subtle IPv6 connectivity failures.

## Implementation

Analyse syslog, configuration, and flow data for evidence of RFC 8504-compliant behaviour. Flag EUI-64 address usage, missing DAD, and PMTUD failures. Report non-compliant devices for remediation.

## Detailed Implementation

### Prerequisites
- IPv6 syslog and configuration data from hosts and routers.
- NDP cache polling (UC-5.20.16) for address pattern analysis.
- Understanding of RFC 8504 requirement categories (MUST, SHOULD, MAY).

### Step 1 — Configure data collection

**EUI-64 detection from NDP cache or flow data:**
```spl
index=network (sourcetype="netflow" OR sourcetype="cisco:ios") earliest=-24h
| rex field=_raw "(?<ipv6_addr>[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){7})"
| rex field=ipv6_addr "::?[0-9a-fA-F]{1,4}:(?<iid_high>[0-9a-fA-F]{1,4}):(?<iid_mid>[0-9a-fA-F]{1,4}):(?<iid_low>[0-9a-fA-F]{1,4})$"
| eval is_eui64=if(match(iid_mid, "(?i)^ff[Ff][Ee]$"), 1, 0)
| where is_eui64=1
| eval embedded_mac=replace(iid_high . ":" . "ff:fe:" . iid_low, "(..)(..)", "\1:\2")
| stats count as events dc(ipv6_addr) as unique_addresses by host, embedded_mac
| sort -unique_addresses
```
EUI-64 addresses contain `ff:fe` in the middle of the 64-bit interface identifier. This pattern uniquely identifies EUI-64 usage.

**Verification:**
```spl
index=network sourcetype="cisco:ios" "%IPV6-4-DUPLICATE" | stats count by host
```
This confirms DAD is operational and logging on devices where it triggers.

### Step 2 — Create compliance assessment

**RFC 8504 compliance scorecard:**
```spl
| inputlookup ipv6_device_inventory.csv
| eval slaac_compliant=if(address_method!="eui64", 1, 0)
| eval dad_enabled=if(dad_status="enabled", 1, 0)
| eval pmtud_working=if(pmtud_status="working", 1, 0)
| eval stable_identifiers=if(address_method="rfc7217" OR address_method="privacy_extensions", 1, 0)
| eval score=slaac_compliant + dad_enabled + pmtud_working + stable_identifiers
| eval grade=case(
    score=4, "FULLY COMPLIANT",
    score=3, "MOSTLY COMPLIANT",
    score <= 2, "NON-COMPLIANT")
| table host, device_type, address_method, dad_status, pmtud_status, grade
| sort grade
```

### Step 3 — Validate
(a) **EUI-64 verification.** On a sample device using EUI-64 (ff:fe in IID), verify the MAC address extraction matches the actual interface MAC.

(b) **DAD test.** On a test segment, configure two hosts with the same IPv6 address. Verify `%IPV6-4-DUPLICATE` messages appear in Splunk.

(c) **PMTUD test.** From a test host, `ping6 -s 1500 -M do <remote>` across a path with lower MTU. Verify ICMPv6 Packet Too Big is received and path MTU adapts.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — RFC 8504 Node Compliance"):
- Row 1 — Single-value: EUI-64 device count (target: 0), non-compliant device count.
- Row 2 — Pie chart: address generation method distribution.
- Row 3 — Table: non-compliant devices with specific RFC 8504 violations.
- Row 4 — Trend: EUI-64 elimination progress over 12 months.

**Alert:** New EUI-64 address detected — trigger on first occurrence of ff:fe pattern in new source address.

**Runbook:**
1. EUI-64 on Windows: Verify `netsh interface ipv6 set global randomizeidentifiers=enabled` is set.
2. EUI-64 on Linux: Verify `net.ipv6.conf.all.addr_gen_mode=3` (stable-privacy, RFC 7217).
3. EUI-64 on Cisco: Configure `ipv6 address autoconfig default` which uses RFC 7217 on modern IOS versions.
4. EUI-64 on macOS: Privacy extensions are enabled by default since macOS 10.12.

### Step 5 — Troubleshooting

- **Difficulty distinguishing address generation methods.** RFC 7217 stable identifiers look random but are deterministic. Privacy extensions (RFC 8981) are random and rotate. EUI-64 contains ff:fe. Only EUI-64 can be definitively identified by pattern; stable vs privacy requires tracking address persistence over time.

- **Link-local EUI-64.** Many devices use EUI-64 for link-local addresses even when using stable identifiers for global addresses. Link-local EUI-64 is lower risk (not routed) but still reveals MAC to local segment.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="syslog" OR sourcetype="cisco:iosxe") earliest=-30d
| eval has_slaac=if(match(_raw, "(?i)SLAAC|autoconfig|ipv6 address autoconfig"), 1, 0)
| eval has_eui64=if(match(_raw, "(?i)eui-64|EUI64"), 1, 0)
| eval has_dad=if(match(_raw, "(?i)DAD|duplicate.address|dad-attempts"), 1, 0)
| eval has_pmtud=if(match(_raw, "(?i)packet.too.big|icmpv6.*type.?2|path.mtu"), 1, 0)
| eval has_ndp=if(match(_raw, "(?i)neighbor.discovery|ipv6.nd|NDP"), 1, 0)
| stats max(has_slaac) as slaac max(has_eui64) as eui64 max(has_dad) as dad max(has_pmtud) as pmtud max(has_ndp) as ndp by host
| eval rfc8504_issues=mvappend(
    if(has_eui64=1, "EUI-64 in use — RFC 8504 §5.1 requires RFC 7217 stable identifiers", null()),
    if(slaac=0 AND ndp=0, "No SLAAC or NDP evidence — possible IPv6 misconfiguration", null()),
    if(dad=0, "No DAD evidence — RFC 8504 §5 requires DAD", null()))
| where isnotnull(rfc8504_issues)
| table host, eui64, slaac, dad, pmtud, ndp, rfc8504_issues
| sort -eui64
```

## Visualization

(1) Single-value: EUI-64 device count (target: 0). (2) Table: non-compliant devices with specific violations. (3) Pie chart: address generation method distribution (EUI-64 vs stable identifiers vs privacy extensions). (4) Trend: EUI-64 elimination progress over time.

## Known False Positives

**Infrastructure devices.** Routers and switches may legitimately use EUI-64 for link-local addresses on infrastructure interfaces. The risk is lower on point-to-point links than on shared access networks. Focus remediation on access-layer hosts.

**Legacy devices.** Older IoT devices, printers, and embedded systems may not support RFC 7217. Document these as accepted risks with a lifecycle replacement plan.

**DAD evidence absence.** DAD messages are typically not logged by default. Absence of DAD evidence in syslog does not necessarily mean DAD is disabled — the device may be performing DAD without logging it. Verify with packet captures on sample segments.

## References

- [RFC 8504 — IPv6 Node Requirements (current, replaces RFC 6434)](https://www.rfc-editor.org/rfc/rfc8504)
- [RFC 7217 — A Method for Generating Semantically Opaque Interface Identifiers with IPv6 SLAAC](https://www.rfc-editor.org/rfc/rfc7217)
- [RFC 8064 — Recommendation on Stable IPv6 Interface Identifiers (deprecates EUI-64)](https://www.rfc-editor.org/rfc/rfc8064)
