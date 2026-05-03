<!-- AUTO-GENERATED from UC-5.20.27.json — DO NOT EDIT -->

---
id: "5.20.27"
title: "MLD Snooping Health and Group Membership Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "ITSI"
---

# UC-5.20.27 · MLD Snooping Health and Group Membership Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** ITSI &middot; **Type:** Availability, Configuration &middot; **Wave:** Walk &middot; **Status:** Verified

*IPv6 devices communicate using group messages — like a public address system where only people in the right room hear the announcement. A special system on the network switches makes sure these announcements only go to the rooms where someone is listening. If this system breaks, the announcements either go nowhere (and devices cannot connect) or go everywhere (wasting energy). We check that this announcement-routing system is healthy.*

---

## Description

Monitors MLD (Multicast Listener Discovery) Snooping health on Layer 2 switches to ensure that IPv6 multicast — and critically, NDP multicast groups — are properly forwarded to all ports that need them. MLD is the IPv6 equivalent of IGMP, and MLD Snooping is the IPv6 equivalent of IGMP Snooping. If MLD Snooping is disabled or misconfigured, two failure modes occur: (1) All IPv6 multicast is flooded to all ports (performance waste on large VLANs), or (2) NDP-critical multicast groups (ff02::1 for Router Advertisements, ff02::1:ffXX:XXXX for Solicited-Node multicast used by Neighbor Solicitation) are not forwarded to the correct ports, breaking NDP and causing IPv6 connectivity failures. This use case monitors MLD Snooping state, group membership, and the presence of NDP-critical groups on each VLAN.

## Value

Broken MLD Snooping is one of the most difficult IPv6 problems to diagnose because it manifests as intermittent NDP failures. A host may be unable to resolve the default gateway (because ff02::2 Router Solicitation multicast is not forwarded) or unable to resolve specific neighbors (because Solicited-Node Multicast is not forwarded to the target's port). The symptoms look like random connectivity drops that clear themselves when the MLD Snooping state is refreshed — leading to 'works sometimes, fails sometimes' trouble tickets. Monitoring MLD Snooping health ensures that the multicast foundation required by IPv6 NDP is always functioning correctly.

## Implementation

Poll MLD Snooping status and group membership from switches via CLI or SNMP. Verify that NDP-critical multicast groups (ff02::1, ff02::2, ff02::1:ff00:0/104) are present in the snooping table for each VLAN. Alert on VLANs where MLD Snooping is disabled or where NDP-critical groups are missing. Track group membership churn over time.

## Detailed Implementation

### Prerequisites
- MLD Snooping enabled on all VLANs (Cisco default: enabled globally). Verify: `show ipv6 mld snooping`.
- MLD Querier configured (typically the Layer 3 router/SVI). Without a querier, MLD membership times out.
- Syslog forwarding from switches at informational level for MLD events.

### Step 1 — Configure data collection

**Cisco IOS/IOS-XE MLD Snooping verification:**
```
show ipv6 mld snooping
Global MLD Snooping configuration:
  MLD Snooping              : Enabled
  MLD Querier               : Disabled

Vlan 100:
  MLD Snooping              : Enabled
  Immediately Leave         : Disabled
  Last Member Query Count   : 2
  Last Member Query Interval : 1000
```

Verify group membership:
```
show ipv6 mld snooping groups vlan 100
Vlan  Group                    Type     Version  Port List
----  -----                    ----     -------  ---------
100   FF02::1                  mld      v2       Gi1/0/1,Gi1/0/2
100   FF02::2                  mld      v2       Gi1/0/1
100   FF02::1:FF00:1           mld      v2       Gi1/0/5
```

**Scripted input for MLD Snooping status:**
```bash
#!/bin/bash
# mld_snooping_status.sh
for switch in $(cat /opt/splunk/etc/apps/ipv6_ops/lookups/switches.txt); do
  echo "=== $switch ==="
  ssh -o StrictHostKeyChecking=no splunk-svc@$switch \
    "show ipv6 mld snooping" 2>/dev/null
  echo "---GROUPS---"
  ssh -o StrictHostKeyChecking=no splunk-svc@$switch \
    "show ipv6 mld snooping groups" 2>/dev/null
done
```
```
# inputs.conf
[script://./bin/mld_snooping_status.sh]
interval = 3600
sourcetype = mld:snooping
index = network
```

**Verification:**
```spl
index=network (sourcetype="mld:snooping" OR (sourcetype="cisco:ios" "MLD")) earliest=-24h
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**Primary search — MLD Snooping health per VLAN:**
```spl
index=network sourcetype="mld:snooping" earliest=-2h
| rex field=_raw "Vlan\s*(?<vlan>\d+):"
| rex field=_raw "MLD Snooping\s*:\s*(?<mld_status>\w+)"
| dedup host, vlan
| eval healthy=if(mld_status="Enabled", "YES", "NO — MLD Snooping disabled")
| table host, vlan, mld_status, healthy
```

**NDP-critical group presence check:**
```spl
index=network sourcetype="mld:snooping" "GROUPS" earliest=-2h
| rex field=_raw "(?<vlan>\d+)\s+(?<mcast_group>FF02::[0-9a-fA-F:]+)"
| where isnotnull(mcast_group)
| stats values(mcast_group) as groups by host, vlan
| eval has_all_nodes=if(match(mvjoin(groups, " "), "(?i)ff02::1(\/|\s|$)"), "YES", "MISSING")
| eval has_all_routers=if(match(mvjoin(groups, " "), "(?i)ff02::2"), "YES", "MISSING or no router")
| eval ndp_health=case(
    has_all_nodes="MISSING", "CRITICAL — ff02::1 missing, RAs cannot reach hosts",
    has_all_routers="MISSING or no router", "WARNING — ff02::2 missing, check if router exists on VLAN",
    1=1, "OK")
| where ndp_health!="OK"
| table host, vlan, has_all_nodes, has_all_routers, ndp_health
```

**MLD group churn monitoring:**
```spl
index=network sourcetype="cisco:ios" ("MLD" ("GROUP_JOIN" OR "GROUP_LEAVE")) earliest=-24h
| rex field=_raw "group\s+(?<mcast_group>[0-9a-fA-F:]+)"
| rex field=_raw "(?:vlan|VLAN)\s*(?<vlan>\d+)"
| timechart span=1h count by mcast_group
```

### Step 3 — Validate
(a) **MLD Snooping status verification.** Cross-reference Splunk data with `show ipv6 mld snooping` on each switch. All VLANs should show `Enabled`.

(b) **NDP group presence.** On a VLAN with an active router and hosts, ff02::1 must be present. ff02::2 must be present if the router's SVI is on that VLAN. Solicited-Node groups (ff02::1:ffXX:XXXX) should match the number of active IPv6 hosts.

(c) **Intentional disable test.** On a lab VLAN, disable MLD Snooping: `no ipv6 mld snooping vlan 100`. Verify the health check flags the VLAN as unhealthy. Re-enable and verify the flag clears.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — MLD Snooping Health"):
- Row 1 — Single-value: VLANs with MLD Snooping disabled, VLANs missing NDP-critical groups.
- Row 2 — Table: per-VLAN MLD Snooping status and NDP group health.
- Row 3 — Timechart: MLD group join/leave churn over 24 hours.

**Scheduling:** MLD Snooping status poll every hour. NDP group check every hour. Group churn trending daily.

**Runbook:**
1. MLD Snooping disabled on a VLAN: enable with `ipv6 mld snooping vlan <id>`. Verify NDP recovers.
2. ff02::1 missing: check if MLD Querier is configured on the VLAN's router SVI. Without a querier, MLD group membership times out after 260 seconds.
3. High group churn: check if hosts are rapidly joining/leaving — may indicate network instability or a rogue device.

### Step 5 — Troubleshooting

- **MLD Snooping shows 'Enabled' but groups are empty** — No MLD Querier is active on the VLAN. The switch needs to receive MLD Queries (from a router) to maintain group membership. Configure the router SVI as MLD Querier: `ipv6 mld snooping querier` on Cisco.

- **NDP works despite MLD Snooping showing issues** — Some switches have a 'static multicast group' or 'flood unknown multicast' setting that forwards NDP multicast regardless of MLD Snooping state. While NDP works, this wastes bandwidth.

- **MLDv1 vs MLDv2 mismatch** — Hosts using MLDv1 and switches expecting MLDv2 (or vice versa) may cause group membership issues. Most modern switches handle both versions, but verify compatibility.

## SPL

```spl
index=network sourcetype="cisco:ios" ("MLD" AND ("GROUP_JOIN" OR "GROUP_LEAVE" OR "SNOOPING"))
| rex field=_raw "group\s+(?<mcast_group>[0-9a-fA-F:]+)"
| rex field=_raw "(?:vlan|VLAN)\s*(?<vlan>\d+)"
| stats count as events dc(mcast_group) as unique_groups values(mcast_group) as groups by host, vlan
| eval has_ndp_groups=if(match(mvjoin(groups, ","), "ff02::1|ff02::2|ff02::1:ff"), "YES", "NO")
| table host, vlan, events, unique_groups, has_ndp_groups
```

## Visualization

(1) Table: per-VLAN MLD Snooping status with NDP group presence. (2) Single-value: VLANs without NDP-critical multicast groups. (3) Timechart: MLD group join/leave events over time — high churn may indicate instability. (4) Dashboard: MLD Snooping coverage across the switch fleet.

## Known False Positives

**MLD Snooping intentionally disabled.** Some networks disable MLD Snooping on specific VLANs for simplicity or compatibility. In this case, all IPv6 multicast is flooded to all ports — NDP works (because the multicast reaches everyone) but bandwidth is wasted. This is a design decision, not a failure.

**Solicited-Node Multicast groups are transient.** Each IPv6 address generates a corresponding Solicited-Node Multicast group (ff02::1:ffXX:XXXX). Groups appear and disappear as hosts join and leave the VLAN. The NDP-critical check should focus on ff02::1 (always present) and ff02::2 (present when routers are on the VLAN).

**MLD Querier election.** MLD requires a querier (typically the router) to periodically send MLD Queries. If the router fails, MLD membership may time out and groups disappear. This is a real problem (not a false positive) but may be transient during router failovers.

## References

- [RFC 3810 — Multicast Listener Discovery Version 2 (MLDv2) for IPv6](https://www.rfc-editor.org/rfc/rfc3810)
- [RFC 4861 — Neighbor Discovery for IP version 6 (§7 — Multicast address requirements for NDP)](https://www.rfc-editor.org/rfc/rfc4861)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.5 — MLD and multicast security)](https://www.rfc-editor.org/rfc/rfc9099)
