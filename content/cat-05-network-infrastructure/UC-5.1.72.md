<!-- AUTO-GENERATED from UC-5.1.72.json — DO NOT EDIT -->

---
id: "5.1.72"
title: "PIM Neighbor and Multicast Group State Monitoring"
status: "community"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.72 · PIM Neighbor and Multicast Group State Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Wave:** Walk &middot; **Status:** Community

*We watch how routers share live video and other one-to-many traffic — like a TV channel that many people are tuned in to. When the routers stop talking to each other, viewers lose the channel without warning. We catch the silent break and tell the team before the trading desk or the security cameras lose their feed.*

---

## Description

Tracks PIM (Protocol Independent Multicast) neighbour state and Rendezvous Point (RP) mapping events across multicast-enabled routers. Surfaces neighbour-DOWN events and invalid RP-join attempts — both early indicators of multicast-distribution-tree failure that silently breaks IPTV, financial market data, and surveillance video feeds.

## Value

Multicast distribution underpins three high-value workloads that almost every enterprise has somewhere: financial market-data feeds (the trading floor will literally lose money in seconds), IPTV / video distribution (executives will notice within minutes), and physical-security surveillance video (it is broken until somebody walks past a camera). PIM is the protocol that builds the distribution tree, and its failure modes are uniquely hard to debug from a multicast receiver's perspective — the receiver simply sees no traffic, with no indication of where on the tree the break is. Centralising PIM neighbour state and RP-mapping events in Splunk gives the multicast operator the directed-graph view that show-commands cannot.

## Implementation

Enable PIM syslog on every multicast-enabled router at severity 3 or lower so RP-join failures (severity 3) and neighbour changes (severity 5) both reach Splunk. Alert on PIM neighbour DOWN events and on unexpected RP changes. Optionally poll PIM-STD-MIB for (S,G) and (*,G) counts; sustained drops across the fleet typically indicate that source registration to the RP has failed.

## SPL

```spl
index=network (sourcetype="cisco:ios" "%PIM-5-NBRCHG" OR "%PIM-3-INVALID_RP_JOIN")
  OR (sourcetype="junos:syslog" "PIM_NEIGHBOR" OR "PIM_RP_MAPPING")
| rex "neighbor (?<pim_neighbor>\S+).*(?<state>UP|DOWN)"
| stats count by host, pim_neighbor, state
| where state="DOWN"
| sort - count
```

## Visualization

Status grid (PIM neighbour state per router, coloured by latest state), Table (down neighbours sorted by event count), Timeline (multicast control-plane events over time, useful for spotting concurrent failures across the tree).

## Known False Positives

**Auto-RP elections during steady state.** PIM-SM with Auto-RP runs periodic RP-discovery messages; one election failing during a candidate-router reboot is benign. Threshold the alert on count > 3 in 15 minutes for the same neighbour pair.

**Bidirectional PIM (Bidir-PIM) state-machine ticks.** Some platforms emit `PIM_NEIGHBOR` events more frequently in Bidir-PIM mode than in Sparse mode. Tune the per-host noise floor with a 7-day baseline.

**Multicast lab segments.** PIM testing in lab environments will alarm constantly. Filter alerts to production loopback ranges only.

## References

- [RFC 7761 — Protocol Independent Multicast - Sparse Mode (PIM-SM)](https://www.rfc-editor.org/rfc/rfc7761)
- [Cisco PIM Configuration Guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/ipmulti_pim/configuration/15-mt/imc-pim-15-mt-book.html)
