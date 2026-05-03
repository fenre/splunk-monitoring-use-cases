<!-- AUTO-GENERATED from UC-5.20.134.json — DO NOT EDIT -->

---
id: "5.20.134"
title: "IPv6 RDNSS and DNSSL via Router Advertisement Monitoring (RFC 8106)"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.134 · IPv6 RDNSS and DNSSL via Router Advertisement Monitoring (RFC 8106)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Availability, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*When devices join our network and get their new address (IPv6) automatically, the router also tells them which phone book (DNS server) to use. We watch to make sure nobody is telling devices to use a fake phone book that would send them to the wrong websites.*

---

## Description

Monitors RDNSS and DNSSL options in IPv6 Router Advertisements (RFC 8106). These options provide DNS configuration to SLAAC clients. Detects rogue RDNSS advertisements (attacker redirecting DNS), expired RDNSS lifetimes, and inconsistent DNS server advertisements across routers.

## Value

RDNSS is how SLAAC-configured hosts learn their DNS servers. If an attacker spoofs an RA with a rogue RDNSS option, they redirect all DNS queries from SLAAC clients to their resolver, enabling DNS spoofing, phishing, and traffic interception. This is more dangerous than rogue DHCP because SLAAC is preferred over DHCPv6 on many operating systems.

## Implementation

Monitor RA RDNSS options for authorized DNS server addresses. Alert on unauthorized RDNSS advertisements.

## Detailed Implementation

### Prerequisites
- RDNSS configured on routers.
- RA Guard deployed (see UC-5.20.28) to prevent rogue RAs.

### Step 1 — Configure RDNSS on routers:
```
interface GigabitEthernet0/0/0
 ipv6 nd ra dns server 2001:db8::53 3600
 ipv6 nd ra dns search-list example.com 3600
```

### Step 2 — Monitor RDNSS advertisements in syslog.

### Step 3 — Validate: Verify SLAAC clients receive correct DNS from `ipconfig /all` or `resolvectl`.

### Step 4 — Operationalize: Dashboard and alerting for rogue RDNSS.

### Step 5 — Troubleshooting
- RDNSS not received by clients: Verify router is sending RDNSS option. Check with packet capture of RA messages.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  ("RDNSS" OR "DNSSL" OR "dns.*option" OR "RFC8106")
| eval rdnss_event=case(
    match(_raw, "(?i)RDNSS.*spoof|DNS.*rogue|unauthorized.*DNS"), "ROGUE_RDNSS",
    match(_raw, "(?i)RDNSS.*lifetime.*0|RDNSS.*expired"), "RDNSS_EXPIRED",
    match(_raw, "(?i)RDNSS|dns.server.*option"), "RDNSS_ADVERTISED",
    1=1, "OTHER")
| rex field=_raw "RDNSS\s*(?<dns_server>[0-9a-fA-F:]+)"
| stats count as events values(dns_server) as advertised_dns by host, rdnss_event
| eval severity=case(
    rdnss_event="ROGUE_RDNSS", "CRITICAL — unauthorized DNS server in RA RDNSS option",
    rdnss_event="RDNSS_EXPIRED", "MEDIUM — RDNSS lifetime expired — clients may lose DNS",
    1=1, null())
| where isnotnull(severity)
| sort -events
```

## Visualization

(1) Table: RDNSS advertisements with DNS servers. (2) Single-value: rogue RDNSS count. (3) Timeline: RDNSS changes.

## Known False Positives

**Multiple legitimate DNS servers.** Redundant DNS servers in RDNSS options are normal. Verify all advertised servers are authorized.

**DHCPv6 coexistence.** When both RDNSS and DHCPv6 provide DNS, clients may receive different servers. This should be harmonized but isn't necessarily an attack.

## References

- [RFC 8106 — IPv6 Router Advertisement Options for DNS Configuration](https://www.rfc-editor.org/rfc/rfc8106)
