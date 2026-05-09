<!-- AUTO-GENERATED from UC-5.1.73.json — DO NOT EDIT -->

---
id: "5.1.73"
title: "IGMP Snooping and Multicast Group Membership"
status: "community"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.73 · IGMP Snooping and Multicast Group Membership

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Walk &middot; **Status:** Community

*We track which devices on each office network are listening to live video or data feeds. When a device joins or leaves a feed unexpectedly, that usually points to a misconfiguration — or in rare cases, someone snooping on a feed they should not. We alert the team to investigate.*

---

## Description

Tracks IGMP membership reports and leave events at the access / distribution layer. Aggregates per-VLAN multicast group activity so the network team can see at a glance which VLANs have active multicast receivers — and equally important, when a previously-active group has gone empty.

## Value

IGMP snooping is the Layer-2 mechanism that prevents multicast traffic from broadcasting to every port on a VLAN. Without it, a single multicast feed at modest bitrate floods every host on the VLAN at line rate — a classic attack pattern, but more often a misconfiguration. With IGMP snooping correctly working, multicast goes only to ports whose hosts have actually joined the group. Monitoring membership reports gives the operator a real-time inventory of which VLANs have IPTV viewers, which have surveillance-camera receivers, and which have financial-market-data clients — useful both for capacity planning and for catching unexpected joins (a host that should not be receiving a group has joined it; that is either a misconfiguration or a pre-attack reconnaissance pattern).

## Implementation

Enable IGMP snooping on every access and distribution switch. Forward IGMP syslog at severity 5 or lower to Splunk. Monitor group-membership counts per VLAN; alert on unexpected group joins (potential multicast amplification or mis-routed feed) and on the complete leaving of a group on a VLAN that should always have receivers (service interruption).

## SPL

```spl
index=network sourcetype="cisco:ios" "%IGMP-5-GROUPCHANGE"
| rex "Group (?<mcast_group>\S+).*VLAN (?<vlan>\d+).*(?<action>JOIN|LEAVE)"
| stats count by host, vlan, mcast_group, action
| sort - count
```

## Visualization

Table (active groups per VLAN, sortable by count), Bar chart (join / leave ratio per VLAN, useful for spotting unstable groups), Timeline (group changes over time).

## Known False Positives

**Querier-election membership flushes.** When the IGMP querier role moves between switches (after a topology change), every group reports membership as part of a flush-and-rejoin sequence. This generates a brief storm of GROUPCHANGE events. Tolerate a 5-minute settle window after `%IGMP-5-QUERIER_NEW`.

**Multicast receiver host reboots.** Set-top boxes, IP cameras, and trading-floor receivers reboot at scheduled times and will leave / rejoin their groups. Suppress the alert for known-rebooting MAC ranges.

**Multicast flood-mode VLANs.** Some surveillance and broadcast VLANs intentionally run with IGMP snooping disabled because every host is a receiver. Filter the alert by VLAN-id range.

## References

- [RFC 4541 — Considerations for Internet Group Management Protocol (IGMP) and Multicast Listener Discovery (MLD) Snooping Switches](https://www.rfc-editor.org/rfc/rfc4541)
- [Cisco IGMP Snooping Configuration Guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/ipmulti_igmp/configuration/15-mt/imc-igmp-15-mt-book.html)
