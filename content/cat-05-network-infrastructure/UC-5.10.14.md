<!-- AUTO-GENERATED from UC-5.10.14.json — DO NOT EDIT -->

---
id: "5.10.14"
title: "Internet Exchange Point (IXP) Peering Health"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.10.14 · Internet Exchange Point (IXP) Peering Health

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*We keep an eye on the special club connections where internet providers swap traffic cheaply, so when those handshake lines flicker we know which shared meeting room broke instead of blaming the whole world.*

---

## Description

Monitors only BGP neighbors classified as Internet Exchange peers—surfacing session instability, notification storms, or route-server-specific flap patterns distinct from upstream transit links sitting on different interfaces.

## Value

Peering teams isolate IX-specific regressions (fabric partitions, MAC-learning errors, RS policy edits) faster than generic BGP dashboards that bury IX peers among dozens of carrier sessions.

## Implementation

Maintain gold-standard CSV whenever peers move ports; annotate route-server vs bilateral peers to tune thresholds; integrate IX participant portal outage RSS optional enrichment.

## Detailed Implementation

### Prerequisites
- Accurate neighbor-to-IX mapping refreshed after every IX migration.
- Understanding bilateral versus route-server operational expectations (RS peers tolerate controlled resets).
- Clock sync across route reflectors logging duplicates.
- Optional NetFlow validation proving traffic collapse aligns with control-plane logs.

### Step 1 — Import `ix_peering_neighbors.csv` via automation consuming IRR/peering DB exports plus manual overrides.

### Step 2 — Tune rex statements per Junos `RPD_BGP_NEIGHBOR_STATE_CHANGED` vs Cisco `%BGP-5-ADJCHANGE` formats.

### Step 3 — Severity matrix flags RS peers differently—idle/connect churn may indicate LAN duplex mismatch.

### Step 4 — Dashboard overlays IX LAN SNMP errors (from UC-5.1.x physical monitors) when BGP alerts fire.

### Step 5 — Troubleshooting: duplicate syslog paths inflate counts—dedup via `dedup` on signature hash; private interconnect VLAN tagging mistakes misassociate peers—verify CMDB.

## SPL

```spl
index=network earliest=-4h (sourcetype="cisco:ios" OR sourcetype="juniper:junos")
    ("%BGP-5-ADJCHANGE" OR "%BGP-3-NOTIFICATION" OR "BGP_PEER_UP" OR "BGP_PEER_DOWN" OR "Notification sent")
| rex field=_raw "neighbor (?<peer>[0-9a-fA-F:\.:\]]+)"
| lookup ix_peering_neighbors.csv neighbor_ip as peer OUTPUT ix_name asn_peer route_server_flag
| where isnotnull(ix_name)
| rex field=_raw "(?i)(?<transition>(?:Established|Idle|Active|Connect|OpenSent|Down)[^\n]*)"
| eval unhealthy=if(match(transition,"(?i)Idle|Active|Connect|Down|Notification"),1,0)
| bin _time span=30m
| stats sum(unhealthy) as bad_samples count as msgs dc(transition) as state_entropy values(transition) as last_states by _time ix_name peer asn_peer route_server_flag host
| where bad_samples>0 OR state_entropy>3
| stats latest(bad_samples) as alerts latest(msgs) as chatter latest(last_states) as transitions latest(route_server_flag) as rs_mode by ix_name peer asn_peer host
| sort -alerts
```

## Visualization

Per-IX bubble chart (peer ASN vs flap score); timeline bands colored by IX fabric outage hypotheses; table linking peer IPs to MAC addresses when ARP logs exist.

## Known False Positives

RS soft resets during IRR refresh windows resemble outages; bilateral peers negotiating ADD-PATH toggle sessions briefly; metro Ethernet protective switching duplicates BGP logs.

## References

- [Euro-IX — Internet Exchange Points resources](https://www.euro-ix.net/)
- [RFC 4271 — BGP-4](https://www.rfc-editor.org/rfc/rfc4271)
