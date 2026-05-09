<!-- AUTO-GENERATED from UC-5.1.68.json — DO NOT EDIT -->

---
id: "5.1.68"
title: "BFD Session State for IGP Fast Failure Detection"
status: "community"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.68 · BFD Session State for IGP Fast Failure Detection

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Wave:** Walk &middot; **Status:** Community

*We watch the heartbeat that runs between routers — if either side stops hearing the heartbeat, traffic immediately reroutes through a different path. When the heartbeat itself fails, the rerouting becomes much slower and users lose voice calls or stalled web pages. We alert when a heartbeat drops so the team can fix the underlying cable or transceiver before traffic actually breaks.*

---

## Description

Surfaces Bidirectional Forwarding Detection (BFD) session-down events across the routed network. BFD is the sub-second failure-detection mechanism that runs alongside IGP (OSPF / IS-IS / EIGRP) and BGP — when a BFD session drops, the routing protocol gets to react faster than its own hello timers can.

## Value

BFD is invisible until it fails — that is its job. The whole point of BFD is to detect a forwarding-path failure in 50–300 ms, faster than any routing-protocol hello timer can. When BFD itself is the thing failing, the IGP and BGP fall back to their own hello timers and convergence slows from sub-second to tens of seconds, which is plenty of time for VoIP calls to drop and TCP sessions to time out. Catching BFD session drops in Splunk is therefore the canonical monitoring pattern for fast-converging networks: BFD flapping more than three times in five minutes warrants immediate investigation of optics or cabling because the path that BFD is supposed to be keeping fast is in fact the slow path right now.

## Implementation

Enable BFD for every IGP / BGP peer on core and distribution routers. Forward BFD syslog at severity 6 or lower to Splunk. Alert on BFD session DOWN events; correlate with IGP adjacency changes and interface status to distinguish BFD-only failures from underlying link failures. BFD flapping (more than three transitions in five minutes) warrants immediate optics / cabling investigation — see UC-5.1.6 (interface error counters).

## SPL

```spl
index=network (sourcetype="cisco:ios" "%BFD-6-BFD_SESS_DOWN") OR (sourcetype="junos:syslog" "BFD_STATE_CHANGE")
| rex "neighbor (?<bfd_peer>\S+).*(?<bfd_state>UP|DOWN|ADMINDOWN)"
| stats count by host, bfd_peer, bfd_state
| where bfd_state="DOWN"
| sort - count
```

## Visualization

Status grid (BFD session state per peer pair, coloured by latest state), Table (down sessions sorted by event count), Timeline (state changes over time, useful for spotting concurrent flap events).

## Known False Positives

**Optics replacement window.** When an SFP / QSFP is being swapped, BFD will flap during the cable / module insertion. Suppress alerts during announced optics-swap windows.

**ECMP load-balancing across asymmetric paths.** Some platforms run BFD per-path on ECMP bundles; one path failing while the other stays UP looks like a BFD flap but the data plane continues to forward fine. Treat repeated single-path drops as a transport-layer alarm rather than a network-wide one.

**BFD-over-LAG state machine quirks.** A few platforms had software bugs where the BFD-over-LAG state machine would mis-report DOWN on rapid LACP renegotiation. Where this is known, suppress for known-buggy code and prioritise the upgrade.

## References

- [RFC 5880 — Bidirectional Forwarding Detection](https://www.rfc-editor.org/rfc/rfc5880)
- [Cisco BFD Configuration Guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/iproute_bfd/configuration/15-mt/irb-15-mt-book.html)
