<!-- AUTO-GENERATED from UC-5.18.9.json — DO NOT EDIT -->

---
id: "5.18.9"
title: "Pseudowire (L2VPN) Status Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.18.9 · Pseudowire (L2VPN) Status Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We babysit the pretend Ethernet cords stretched across the country inside our pipes. When those cords fray or lose their pairing tags, we ring the bell before wholesale buyers lose phone or cloud links.*

---

## Description

Splunk watches pseudowire attachment circuits and VC signaling so Ethernet wholesale handoffs, mobile backhaul emulations, and VPWS extensions raise alarms when VC IDs drift, MTUs mismatch, or remote labels disappear.

## Value

Business wholesale revenue stays defendable because operations correlates customer-visible Carrier Ethernet outages with precise pseudowire identifiers instead of guessing among dozens of VPN attachment interfaces.

## Implementation

Land PW syslog plus fifteen-minute SNMP polls for `pwOperStatus.down`, join on `vc_id`, enrich with customer circuit IDs via lookup, alert when VC stays non-forwarding > three polling intervals.

## Detailed Implementation

### Prerequisites
- Circuit inventory CSV tying `vc_id`, endpoints, customer VLAN, and handoff port.
- Known-good MTU template list.

### Step 1 — Logging coverage
Cisco ME/ASR families: ensure pseudowire status transitions emit syslog not solely SNMP traps if traps filtered upstream.

### Step 2 — SNMP augmentation
Poll `pwOperStatus`, `pwRemotePwID`, `pwAttachedPwIndex` via SC4SNMP profiles.

### Step 3 — SPL correlation
Join syslog events within ±300s of SNMP down transitions using `vc_id` key.

### Step 4 — CLI validation
`show l2vpn xconnect`, Junos `show l2circuit connections`, Nokia `show service sdp-using` commands confirm Splunk narrative.

### Step 5 — Lifecycle
Quarterly audit stale VC IDs still alerting—retire suppress entries after migrations.

## SPL

```spl
index=network earliest=-24h@h latest=now
| eval msg=lower(_raw)
| eval pw=match(msg,"(?:pseudowire|pw.?id|l2circuit|l2vpn|(?:ethernet|virtual.?circuit)|(?:vpws|vpls).*?(?:vc|pseudo|routed.?pseudo)|(?:mpls.?)?(?:xc|cross.?connect).*pw)")
| eval bad=match(msg,"(?:down|standby|(?:not.?)?(?:operational|active)|(?:detach|withdraw)|(?:signal.?)?(?:fail|mismatch)|(?:mtu).*(?:mismatch)|(?:remote.?)?(?:label).*(?:(?:mis)?match)|(?:oam)?(?:alarm)|(?:bd.?status).*?(?:down))")
| where pw=1 AND bad=1
| rex field=_raw max_match=0 "(?i)(?:vc.?id|vcid|pseudo.?wire.?id)\s*[:=]?\s*(?<vc_id>[0-9]+)"
| rex field=_raw max_match=0 "(?i)(?:neighbor|peer)\s*[:=]?\s*(?<neighbor>[0-9.]+|[0-9a-f:]+)"
| rex field=_raw max_match=0 "(?i)(?:interface|ac)\s*[:=]?\s*(?<ac_if>[^\s,]+)"
| stats count earliest(_time) as first_seen latest(_time) as last_seen values(neighbor) as peers values(ac_if) as ac_ports values(vc_id) as vc_ids by host sourcetype
| sort - count
```

## Visualization

Dashboard Studio: KPI for down pseudowires; Sankey optional via stats prep; table (`host`, `vc_ids`, `peers`, `ac_ports`, `count`).

## Known False Positives

**Protective standby:** VC purposely standby during ISSU—suppress via change tag.**SNMP stale indices:** renumber after reboot mis-joins until baseline refresh.**Keyword bleed:** generic "circuit" matches unrelated SONET logs—tighten regex.**MTU tuning windows:** planned edits spike alarms—calendar linkage.**Dual-homed PW:** single attachment messages appear alarming though service intact.

## References

- [Cisco Layer 2 VPNs Configuration Guide — Pseudowire](https://www.cisco.com/c/en/us/)
- [Juniper Layer 2 Circuits and VPNs User Guide](https://www.juniper.net/documentation/)
- [IETF RFC 4762 — VPLS Using LDP Signaling](https://www.rfc-editor.org/rfc/rfc4762)
