<!-- AUTO-GENERATED from UC-5.1.13.json — DO NOT EDIT -->

---
id: "5.1.13"
title: "ACL Deny Logging"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.13 · ACL Deny Logging

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We list traffic your access lists block so you can see unexpected scans or a mis-aimed app before it harms the business.*

---

## Description

ACL deny hits show blocked traffic. High volumes may indicate attacks or misconfigured apps.

## Value

Security teams analyze ACL deny logs across routers and switches, detecting port scans, distributed attacks, and misconfigured applications blocked by network access control policies.

## Implementation

Enable ACL logging (`log` keyword). Forward syslog. Dashboard showing top denied sources and trends.

## Detailed Implementation

### Prerequisites
* ACL deny log messages from network devices. Data in `index=network` with `sourcetype=cisco:ios` or vendor-specific sourcetypes. Key mnemonics: Cisco `%SEC-6-IPACCESSLOGP`, `%SEC-6-IPACCESSLOGDP`; Juniper `PFE_FW_SYSLOG_ETH`; Arista `SEC-6-IPACCESSLOG`.
* ACL deny logging records packets that were explicitly blocked by access-control lists. Analyzing these events reveals attack patterns, misconfigured applications, and policy effectiveness. High deny rates on specific rules may indicate active scanning or policy too permissive in other areas.

### Step 1 — - Configure data collection
```
# Cisco IOS -- ACL with logging
access-list 100 deny ip any any log
# Or named ACL:
ip access-list extended OUTSIDE-IN
 deny ip any any log

# Rate-limit ACL logging to avoid CPU impact
logging rate-limit 100

# Syslog forwarding
logging host <splunk-syslog-ip>
```
Verify:
```spl
index=network earliest=-4h
| where match(_raw, "(?i)IPACCESSLOG|ACL.*denied|denied.*acl|access.list.*denied|firewall.*deny")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- ACL deny event analysis:**
```spl
index=network earliest=-4h
| where match(_raw, "(?i)IPACCESSLOG|ACL.*denied|denied.*acl|access.list.*denied")
| rex field=_raw "(?i)(?:list|acl)\s+(?<acl_name>\S+)"
| rex field=_raw "(?i)denied\s+(?<protocol>\w+)\s+(?<src_ip>[\d\.]+).*?->\s*(?<dst_ip>[\d\.]+).*?(?<dst_port>\d+)"
| eval src=coalesce(src_ip, src, source)
| eval dst=coalesce(dst_ip, dst, destination)
| eval port=coalesce(dst_port, dest_port)
| eval device=coalesce(host, device_name)
| iplocation src prefix=src_
| stats count as denies dc(src) as unique_sources dc(dst) as unique_targets dc(port) as unique_ports by device, acl_name, protocol
| eval severity=case(
    denies > 1000 AND unique_sources > 50, "CRITICAL -- possible DDoS or distributed scan",
    unique_ports > 20 AND unique_sources < 5, "WARNING -- port scan detected",
    denies > 500, "WARNING -- high deny rate on ACL ".acl_name,
    1==1, "INFO")
| where severity != "INFO"
| sort severity, -denies
```

### Step 3 — - Validate
(a) CLI: `show access-lists` -- check ACL hit counts per rule.
(b) Correlate with firewall deny events for defense-in-depth validation.
(c) Verify ACL logging rate-limit is configured to avoid CPU overload.

### Step 4 — - Operationalize
Dashboard ("Network -- ACL Deny Analysis"):
* Row 1 -- Single-value: "Total denies (4h)", "Unique blocked sources", "ACLs triggered".
* Row 2 -- ACL deny timeline by ACL name.
* Row 3 -- Top blocked sources table.

Alert: Critical (>1000 denies from 50+ sources): distributed attack.

### Step 5 — - Troubleshooting

* **ACL logging overwhelming CPU** -- Enable rate-limiting: `logging rate-limit <n>`. Consider logging only specific ACL entries, not the catch-all deny.

* **Legitimate traffic blocked** -- Check if application requires ports not in ACL permit rules. Verify with the application team and add specific permit entries above the deny.

* **No ACL deny logs** -- Verify ACL has `log` keyword on deny entries. Check `logging trap` level includes informational (level 6).

**IPv6 Coverage:** IPv6 ACLs use `ipv6 access-list` and log via `%IPV6_ACL-6-ACCESSLOGP`. NIST SP 800-119 requires IPv4/IPv6 ACL parity. Critical: ICMPv6 types 133-137 (NDP) must be permitted — blocking them breaks IPv6 connectivity entirely.

## SPL

```spl
index=network sourcetype="cisco:ios" "%SEC-6-IPACCESSLOGP" OR "%IPV6_ACL-6-ACCESSLOGP"
| rex "list (?<acl>\S+) denied (?<proto>\w+) (?<src>\d+\.\d+\.\d+\.\d+|[0-9a-fA-F:]+(?:\:[0-9a-fA-F:]+)*|\[[0-9a-fA-F:]+\])"
| stats count by host, acl, src, proto | sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action All_Traffic.dvc span=1h
| where count>0
| sort -count
```

## Visualization

Table, Bar chart by source IP, Timechart.

## Known False Positives

New security baselines, pen tests, and mis-pointed app VIPs can spike denies. Weed out scanners and approved tests via subnet lookup.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
