<!-- AUTO-GENERATED from UC-5.1.71.json — DO NOT EDIT -->

---
id: "5.1.71"
title: "QoS DSCP Marking and Classification Visibility"
status: "community"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.71 · QoS DSCP Marking and Classification Visibility

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Compliance &middot; **Wave:** Walk &middot; **Status:** Community

*We watch how the network labels each piece of data so important traffic — like voice calls and video meetings — gets priority over downloads. When the labels go missing or get changed, voice quality drops. We can see which router on the path stripped the labels and tell the team where to fix it.*

---

## Description

Aggregates NetFlow / IPFIX traffic by DSCP class to reveal how QoS marking is actually being applied across the network. Surfaces unexpected DSCP values at trust boundaries (a sign of upstream re-marking or attack) and gives the QoS operator a per-source view of the priority profile each subnet is receiving.

## Value

QoS marking is the contract between the application and the network: voice gets EF (DSCP 46), business video gets AF41, scavenger traffic gets CS1, default gets DF. The contract only works if every router along the path honours the marking. In practice, ISP-side untagging at the WAN edge, mismatched class maps between distribution and core, and re-marking on inter-zone trunk ports all silently demote critical traffic to best-effort. Without this UC the breakage is invisible until users complain about choppy voice; with this UC the QoS operator can see a sudden drop in EF-marked traffic from a subnet within minutes of the cause and pin the route blame on the right hop.

## Implementation

Export NetFlow / IPFIX with the ToS / DSCP field from WAN-edge and campus distribution routers. Optionally poll CISCO-CLASS-BASED-QOS-MIB for per-class-map match and drop counters — these counters expose drops in the priority queue that NetFlow alone cannot show. Create a `dscp_names` lookup table mapping DSCP values to their RFC names. Alert when unexpected DSCP values appear at trust boundaries or when priority-queue drop rates exceed the per-interface baseline.

## SPL

```spl
index=network sourcetype="netflow"
| eval dscp=floor(tos/4)
| stats count bytes as total_bytes by dscp src_ip dest_ip
| lookup dscp_names dscp OUTPUT dscp_name
| chart sum(total_bytes) over dscp_name by src_ip
```

## Visualization

Pie chart (traffic by DSCP class for the search window), Table (DSCP distribution per interface, useful for QoS-policy debugging), Line chart (priority-queue drops over time per interface).

## Known False Positives

**Cloud SaaS providers re-marking inbound.** Many SaaS providers re-mark all traffic to DF on egress because their fabric does not respect customer DSCP. The drop in EF / AF41 from those origins is normal — exclude known SaaS source-IP ranges from the alert.

**MPLS L3VPN service-class translation.** Some carrier MPLS clouds compress the customer's 8-class DSCP marking into a 3-class internal marking, then expand back at the egress PE. The DSCP value on each side is correct; the apparent re-marking inside the cloud is by design.

**WAN optimisation appliances re-marking compressed flows.** Aruba EdgeConnect, Riverbed Steelhead, and Cisco WAAS will re-mark optimised flows to a different DSCP for their own flow-pinning logic. Suppress alerts for traffic egressing a known WAN-optimisation appliance.

## References

- [RFC 4594 — Configuration Guidelines for DiffServ Service Classes](https://www.rfc-editor.org/rfc/rfc4594)
- [Cisco DSCP and IP Precedence Values](https://www.cisco.com/c/en/us/support/docs/quality-of-service-qos/qos-packet-marking/10103-dscpvalues.html)
