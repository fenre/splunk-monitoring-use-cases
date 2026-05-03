<!-- AUTO-GENERATED from UC-5.18.2.json — DO NOT EDIT -->

---
id: "5.18.2"
title: "LDP Neighbor Adjacency Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.18.2 · LDP Neighbor Adjacency Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault, Operations &middot; **Wave:** Crawl &middot; **Status:** Verified

*We keep an eye on the handshake lines between our big routers that share sticker labels for packets. When those friendships drop, we shout early so nobody ships mail down a hallway that suddenly lost its name tags.*

---

## Description

Splunk tracks LDP hello and TCP session churn across PE and P nodes so partial mesh loss or GR timeouts appear as structured neighbor-down bursts rather than buried lines inside verbose routing daemon logs.

## Value

Label distribution continuity protects VPN and Internet prefixes alike because ops teams detect dying TCP adjacencies before liberal label retention masks blackholes and before PIC edge cases strand stale LFIB entries on upstream hops.

## Implementation

Ensure LDP session change syslog reaches the network index, normalize IPv4/IPv6 router IDs into `neighbor`, alert when distinct peer loss exceeds threshold per PE within ten minutes, and enrich with NetBox CMDB roles.

## Detailed Implementation

### Prerequisites
- Accurate CMDB linking management IPs on loopbacks to device names forwarded as syslog `host`.
- Baseline of expected LDP peers per platform (full mesh vs targeted).

### Step 1 — Logging posture
Cisco IOS-XE: confirm `%LDP-5-NBRCHG` or equivalent informational messages export to collectors; IOS-XR validate `mpls ldp neighbor` events via `logging discriminator`. Junos: ensure `system syslog user * any notice` captures `rpd` LDP messages without drowning in BGP noise—optionally filter facility in relay. Nokia SR OS: mirror router-id and peer events at `major` or higher per operations policy.

### Step 2 — Parsing
Augment TA extractions with `rex` for neighbor router-id and optional GR reason codes; map interface names for targeted sessions.

### Step 3 — Saved search
`ldp_neighbor_down_surge`: alert if `dc(peers)`≥2 per host in five minutes or single peer matches critical tier lookup `tier1_ldp_peers.csv`.

### Step 4 — CLI validation
On alarm: Cisco `show mpls ldp neighbor`; XR `show ldp neighbor`; Junos `show ldp neighbor`; Nokia `show router ldp session`; compare states and uptime to Splunk event timestamps.

### Step 5 — Runbook tie-in
Dashboard drilldown shows raw messages and suggested bounce/recovery steps; post-mortems attach Splunk search URLs as incident evidence when GR timers masked flap bursts.

## SPL

```spl
index=network earliest=-24h@h latest=now
| eval st=lower(coalesce(sourcetype,_sourcetype,""))
| where match(st,"cisco:ios|cisco:ios_xr|cisco:ios_xe|juniper:junos|nokia")
| eval msg=lower(_raw)
| eval is_ldp=if(match(msg,"\\bldp\\b") OR match(msg,"label.?distribution") OR match(_raw,"LDP-"),1,0)
| where is_ldp=1 AND match(msg,"(?:neighbor|adjacency|session|peer).*(?:down|up|reset|closed|timeout|hold.?time|fd|tcp)|(?:down|lost).*ldp|ldp.*(?:fail|error)|graceful.?restart.*(?:fail|complete)")
| rex field=_raw max_match=0 "(?i)(?:neighbor|peer)[=: \t]+(?<neighbor>[0-9.]+|[0-9a-f:]+)"
| rex field=_raw max_match=0 "(?i)(?:interface|if)\s*[:=]?\s*(?<ifname>[^\s,]+)"
| stats count earliest(_time) as first_seen latest(_time) as last_seen values(neighbor) as peers values(ifname) as ifaces by host st
| sort - count
```

## Visualization

Dashboard Studio: KPI for PEs with LDP downs in 24h; stacked bar of sessions by `host`; drilldown table (`host`, `peers`, `ifaces`, `count`) linked to raw events.

## Known False Positives

**Graceful restart:** neighbors flap informational during NSR switch—suppress via maintenance playbook.**Targeted LDP on pseudowires:** teardown mimics core outage—join with SAP/PW context.**IPv6 vs IPv4 RID mismatch:** duplicate-looking peers differ only by address family.**TCP RST storms:** transient SYN backlog spikes trigger noise until firewall rules clarified.**Log sampling:** if sampled inputs drop hello churn, counts under-report—disable sampling for LDP facilities.

## References

- [Cisco IOS Configuration Guides — MPLS Layer 3 VPNs (LDP fundamentals)](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/mp_l3_vpns/configuration/xe-16/mplsd-ios-xe-book.pdf)
- [Juniper Junos MPLS User Guide — LDP Overview](https://www.juniper.net/documentation/us/en/software/junos/mpls/topics/concept/mpls-ldp-overview.html)
- [IETF RFC 5036 — LDP Specification](https://www.rfc-editor.org/rfc/rfc5036)
