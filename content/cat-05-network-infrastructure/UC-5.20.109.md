<!-- AUTO-GENERATED from UC-5.20.109.json — DO NOT EDIT -->

---
id: "5.20.109"
title: "IPv6 Multicast Listener Discovery (MLD) Anomaly Detection"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.109 · IPv6 Multicast Listener Discovery (MLD) Anomaly Detection

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Security, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*In our network, devices join 'interest groups' to receive specific types of messages — like subscribing to a newspaper. MLD is the protocol that manages these subscriptions for IPv6. If someone floods the subscription desk with thousands of fake subscriptions, it overwhelms the system and everyone's newspapers get mixed up. We watch the subscription desk to make sure it's not being overwhelmed or tricked.*

---

## Description

Monitors IPv6 Multicast Listener Discovery (MLD) protocol for anomalies: MLD report flooding (state exhaustion), MLD query spoofing (reconnaissance), snooping bypass, and unauthorized PIM neighbour establishment. MLD is essential for IPv6 NDP operation — all NDP messages use multicast — making MLD security directly tied to IPv6 infrastructure security.

## Value

MLD is invisible in most monitoring but fundamental to IPv6 operation. An MLD state exhaustion attack can crash switches and flood multicast traffic, disrupting all IPv6 connectivity on the segment. MLD query spoofing reveals host group memberships for reconnaissance. Because NDP depends on multicast (and thus MLD), MLD attacks can destabilise the entire IPv6 first-hop security infrastructure.

## Implementation

Monitor MLD report/query/leave rates. Alert on state table exhaustion. Track MLD snooping status. Verify PIM neighbour authenticity.

## Detailed Implementation

### Prerequisites
- MLD snooping enabled on switches (default on most modern switches).
- Switch logging for MLD events.
- Understanding of expected multicast groups on each VLAN.

### Step 1 — Configure MLD snooping and monitoring

**Cisco Catalyst 9000 MLD snooping (default enabled, verify):**
```
ipv6 mld snooping
ipv6 mld snooping vlan 10
ipv6 mld snooping vlan 10 mrouter interface GigabitEthernet1/0/1
```

**MLD rate limiting to prevent state exhaustion:**
```
ipv6 mld snooping vlan 10 limit 500
```

**Enable MLD event logging:**
```
logging buffered 8192 informational
```

### Step 2 — Create monitoring searches

**MLD snooping status audit:**
```spl
index=network sourcetype="cisco:*:config" earliest=-7d
| dedup host
| eval mld_snooping=if(match(_raw, "(?i)ipv6 mld snooping") AND NOT match(_raw, "(?i)no ipv6 mld snooping"), "ENABLED", "DISABLED")
| table host, mld_snooping
| where mld_snooping="DISABLED"
| eval finding="MLD snooping DISABLED — all IPv6 multicast will flood (including NDP)"
```

**MLD state table monitoring:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  "MLD" AND ("group" OR "state")
| rex field=_raw "(?<group_count>\d+)\s+groups?"
| eval group_count=tonumber(group_count)
| stats max(group_count) as max_groups by host
| eval status=case(
    max_groups > 4000, "CRITICAL — MLD state table near capacity",
    max_groups > 2000, "WARNING — MLD state table growing",
    1=1, "OK — " . max_groups . " groups")
| sort -max_groups
```

### Step 3 — Validate
(a) **MLD snooping test.** On a test VLAN, send an IPv6 multicast packet. Verify it is only forwarded to ports with interested listeners (not flooded to all ports). If it floods, MLD snooping is not working.

(b) **Rate limiting test.** Send rapid MLD reports from a test host. Verify the switch rate-limits after the configured threshold.

(c) **PIM neighbour audit.** Check `show ipv6 pim neighbor` on all routers. Verify all PIM neighbours are authorized.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — MLD/Multicast Security"):
- Row 1 — Single-values: MLD snooping status (green if all enabled), state table utilization.
- Row 2 — Timechart: MLD event rates.
- Row 3 — Table: VLANs with MLD snooping disabled.
- Row 4 — PIM neighbour table audit.

**Alert 1:** MLD state table >80% capacity — critical.
**Alert 2:** MLD snooping disabled on production VLAN — high.
**Alert 3:** Unexpected PIM neighbour — medium.

### Step 5 — Troubleshooting

- **MLD snooping disabled by default on some platforms.** While most modern switches enable MLD snooping by default, some older platforms or non-default VLANs may have it disabled. Always explicitly configure `ipv6 mld snooping`.

- **MLD querier missing.** If no MLD querier is present on a VLAN, MLD snooping gradually ages out all group state and reverts to flooding. Ensure at least one L3 switch on each VLAN acts as MLD querier.

- **Performance impact of state exhaustion.** When the MLD state table overflows, switches typically fall back to flooding all multicast. This dramatically increases switch backplane utilization and can cause collateral packet drops for all traffic.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  ("%MLD" OR "multicast" OR "%IGMP" OR "snooping" OR "PIM")
| eval mld_event=case(
    match(_raw, "(?i)MLD.*report|listener.*report"), "MLD_REPORT",
    match(_raw, "(?i)MLD.*query|general.*query"), "MLD_QUERY",
    match(_raw, "(?i)MLD.*leave|listener.*done"), "MLD_LEAVE",
    match(_raw, "(?i)snooping.*overflow|state.*exhaustion|table.*full"), "STATE_EXHAUSTION",
    match(_raw, "(?i)PIM.*neighbor.*new|PIM.*adjacency"), "PIM_NEIGHBOR",
    1=1, "OTHER")
| eval is_ipv6=if(match(_raw, "(?i)ipv6|MLDv|ff02::|ff05::|ff08::"), 1, 0)
| where is_ipv6=1
| stats count as events by host, mld_event
| eval anomaly=case(
    mld_event="STATE_EXHAUSTION", "CRITICAL — multicast state table full — possible MLD flood attack",
    mld_event="MLD_REPORT" AND events > 1000, "HIGH — excessive MLD reports (" . events . ") — possible state exhaustion attack",
    mld_event="MLD_QUERY" AND events > 100, "MEDIUM — excessive MLD queries — possible spoofed querier",
    mld_event="PIM_NEIGHBOR", "INFO — new PIM neighbor detected — verify authorized",
    1=1, null())
| where isnotnull(anomaly)
| sort -events
```

## Visualization

(1) Timechart: MLD event rates by type. (2) Single-value: state table utilization. (3) Table: anomalous MLD event sources. (4) Status: MLD snooping enabled/disabled by VLAN.

## Known False Positives

**High density environments.** Large numbers of hosts on a single VLAN generate many MLD reports (one per solicited-node group per host). In a VLAN with 500+ hosts, thousands of MLD reports are normal.

**Multicast applications.** Video conferencing (Zoom, Teams), streaming, and building management systems generate legitimate MLD reports. Baseline your environment before setting thresholds.

**MLD querier election.** When multiple layer-3 switches are on the same segment, MLD querier election generates additional MLD queries during transitions. This is normal.

## References

- [RFC 3810 — Multicast Listener Discovery Version 2 (MLDv2) for IPv6](https://www.rfc-editor.org/rfc/rfc3810)
- [RFC 4541 — Considerations for IGMP and MLD Snooping Switches](https://www.rfc-editor.org/rfc/rfc4541)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3 — first-hop security)](https://www.rfc-editor.org/rfc/rfc9099)
