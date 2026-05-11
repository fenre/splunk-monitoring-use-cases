<!-- AUTO-GENERATED from UC-5.1.69.json — DO NOT EDIT -->

---
id: "5.1.69"
title: "IPv6 Interface and Neighbor Discovery Monitoring"
status: "community"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.69 · IPv6 Interface and Neighbor Discovery Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Configuration &middot; **Wave:** Walk &middot; **Status:** Community

*We watch the IPv6 part of the network — the newer system that lets every device have a unique address. When two devices accidentally claim the same address, or a device pretends to be a router and tries to redirect traffic, we catch it on the switch and tell the team.*

---

## Description

Tracks IPv6 interface state, NDP (Neighbor Discovery Protocol) events, and Router Advertisement (RA) consistency on dual-stack and IPv6-only routers. Surfaces hosts emitting duplicate-address-detection failures and routers with RA-Guard hits — both indicators of a misconfigured or actively malicious endpoint on the segment.

## Value

As organisations roll out dual-stack or pure IPv6 networks, the v6 control plane behaves nothing like IPv4. There is no DHCP for v6 in many deployments — clients self-configure via SLAAC from Router Advertisements. A single rogue device emitting RA messages can hijack traffic for the entire VLAN within seconds. Centralised RA-Guard and NDP monitoring catches this attack pattern before users notice their default gateway changed. The same data feed also catches duplicate address detection (DAD) failures, which on Linux clients is a benign `Address already in use` error and on networking gear is a routing-table poisoning condition.

## Implementation

Enable IPv6 ND syslog on every dual-stack device. Enable RA-Guard on access ports to detect rogue Router Advertisements (the RFC 6105 control). Forward syslog to Splunk at severity 4 or lower. Alert on duplicate-address-detection failures and on any RA-Guard hit (which by definition means a non-trusted port is sending Router Advertisements).

## SPL

```spl
index=network (sourcetype="cisco:ios" "%IPV6-4-DUPLICATE" OR "%IPV6_ND-6" OR "%RA_GUARD-6")
  OR (sourcetype="junos:syslog" "NDP" OR "ROUTER_ADVERTISEMENT")
| stats count by host, _raw
| sort - count
```

## Visualization

Table (IPv6 events grouped by device), Timeline (RA-Guard events per VLAN), Status grid (per-interface IPv6 state for the v6-critical access tier).

## Known False Positives

**Linux NetworkManager DAD on resume.** Linux laptops returning from sleep frequently emit a duplicate-address-detection event before settling on their previous address. Filter on hosts whose DHCP client is known to do DAD-on-resume.

**IPv6-only printers / IoT.** Some IoT devices send unsolicited RA-like messages every few minutes as part of normal operation. Maintain an allow-list of known-IoT MAC ranges so the RA-Guard alert focuses on truly rogue devices.

**Engineering test segments.** Lab segments where engineers run new RA-Guard and NDP-snooping configurations frequently emit alarms while testing. Filter alerts to production VLAN ID ranges.

## References

- [RFC 4861 — Neighbor Discovery for IPv6](https://www.rfc-editor.org/rfc/rfc4861)
- [RFC 6105 — IPv6 RA-Guard](https://www.rfc-editor.org/rfc/rfc6105)
- [Cisco IPv6 First-Hop Security](https://www.cisco.com/c/en/us/)
