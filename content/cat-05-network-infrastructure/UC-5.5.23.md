<!-- AUTO-GENERATED from UC-5.5.23.json — DO NOT EDIT -->

---
id: "5.5.23"
title: "Versa Networks SD-WAN Path Quality and Routing Decisions"
status: "community"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.23 · Versa Networks SD-WAN Path Quality and Routing Decisions

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Community

*We track whether the company's branch offices are getting the network performance they were promised. When the link gets too slow or unreliable for an important application, the SD-WAN switches the traffic to a different path. We watch both the problem and the fix so the network team knows the system is doing its job.*

---

## Description

Tracks SLA violations and path-switch events across the Versa Networks SD-WAN fabric, aggregated per branch / circuit / SLA-policy triplet. The same query surfaces both the symptom (SLA violation) and the response (path switch) so the NOC can verify that the fabric is healing itself rather than just emitting alarms.

## Value

Versa Networks delivers an integrated SD-WAN, security, and routing platform that competes head-to-head with Cisco SD-WAN and Fortinet Secure SD-WAN. Versa Analytics is its native dashboard, but for organisations that have standardised on Splunk as the single pane of glass, hand-built dashboards in Versa Analytics never get the same traction. Forwarding Versa's path-quality and SLA telemetry into Splunk unlocks cross-vendor comparison: how often does the Versa-managed circuit miss SLA versus the Cisco-managed circuit on the same metro? This UC is the foundation for that comparison.

## Implementation

Forward Versa FlexVNF syslog to Splunk over UDP / TCP 514. Poll the Versa Director API on a 5-minute schedule for structured SLA violation and path-steering data. Alert when SLA violations exceed a per-site, per-circuit threshold over a rolling 1-hour window — the noise floor varies dramatically by transport and by SLA policy.

## SPL

```spl
index=sdwan sourcetype="versa:sdwan"
| search event_type="sla_violation" OR event_type="path_switch"
| stats count by branch_name, circuit_name, event_type, sla_policy
| sort - count
```

## Visualization

Table (SLA violations by branch / circuit), Timeline (path-switch events over time), Line chart (circuit quality scores per circuit, multi-circuit overlay).

## Known False Positives

**Brown-out periods on residential broadband.** Branches whose secondary transport is residential broadband will see SLA violations clustered around 18:00–22:00 local time. This is normal congestion; aggregate over a 7-day baseline before paging.

**Path-switch hysteresis loops.** Aggressive SLA policies can cause Versa to ping-pong between two transports when both are marginal. The alert that 'a path switch happened' is correct in each case, but waking ops at 02:00 is not the right response. Threshold the alert on count > 5 in 15 minutes for the same circuit.

**Director-side polling lag.** Director API polling can lag the underlying telemetry by 1–2 minutes during config-push windows. Tolerate a slip in the alert evaluation rather than declaring an alert false-fire.

## References

- [Versa Networks documentation](https://docs.versa-networks.com/)
- [Versa Director API guide](https://docs.versa-networks.com/Solutions/)
