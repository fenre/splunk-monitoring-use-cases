<!-- AUTO-GENERATED from UC-5.20.122.json — DO NOT EDIT -->

---
id: "5.20.122"
title: "DS-Lite (Dual-Stack Lite) Tunnel and AFTR Health Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.122 · DS-Lite (Dual-Stack Lite) Tunnel and AFTR Health Monitoring

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*DS-Lite is like a postal service that puts old-format letters (IPv4) inside new-format envelopes (IPv6) for delivery, then opens them at the destination post office (AFTR). If that post office gets overwhelmed, nobody's old-format letters get through. We watch the post office to make sure it doesn't get too busy.*

---

## Description

Monitors DS-Lite (RFC 6333) tunnel health and AFTR concentrator performance. DS-Lite enables IPv4 service over IPv6-only networks by tunneling IPv4 in IPv6 and performing centralized NAT44 at the AFTR. Tracks AFTR session table utilization, per-subscriber port exhaustion, tunnel failures, and MTU/fragmentation issues.

## Value

DS-Lite is widely deployed by ISPs to conserve IPv4 addresses while running IPv6-only core networks. The AFTR is a critical shared resource — when it fails or exhausts its session table, all customers behind it lose IPv4 connectivity. Monitoring AFTR health and per-subscriber port allocation ensures reliable IPv4 service during the IPv6 transition.

## Implementation

Monitor AFTR concentrator events, session table utilization, and tunnel health. Track per-subscriber port allocation.

## Detailed Implementation

### Prerequisites
- DS-Lite AFTR deployed.
- AFTR logging enabled.

### Step 1 — Configure AFTR monitoring
Enable session logging and port allocation logging on the AFTR.

### Step 2 — Create monitoring searches
```spl
index=network "AFTR" earliest=-1h
| stats count by host, dslite_event
```

### Step 3 — Validate
Verify IPv4 connectivity through DS-Lite from a test B4. Check AFTR session count.

### Step 4 — Operationalize
**Dashboard:** AFTR health. **Alert:** Session table >90% — critical. Port exhaustion — high.

### Step 5 — Troubleshooting
- Session table full: Reduce TCP/UDP timeouts. Add AFTR capacity.
- Port exhaustion: Increase per-subscriber port allocation or add more shared IPv4 addresses.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="juniper:junos") earliest=-4h
  ("%DSLITE" OR "ds-lite" OR "AFTR" OR "softwire")
| eval dslite_event=case(
    match(_raw, "(?i)AFTR.*session.*full|NAT.*pool.*exhaust"), "AFTR_EXHAUSTION",
    match(_raw, "(?i)tunnel.*down|softwire.*fail"), "TUNNEL_DOWN",
    match(_raw, "(?i)port.*exhaust|port.*alloc.*fail"), "PORT_EXHAUSTION",
    match(_raw, "(?i)fragment|MTU"), "MTU_ISSUE",
    1=1, "OTHER")
| stats count as events by host, dslite_event
| eval severity=case(
    dslite_event="AFTR_EXHAUSTION", "CRITICAL — AFTR session table/pool exhausted",
    dslite_event="TUNNEL_DOWN", "HIGH — DS-Lite tunnel failure",
    dslite_event="PORT_EXHAUSTION", "HIGH — per-subscriber port exhaustion",
    dslite_event="MTU_ISSUE", "MEDIUM — fragmentation in DS-Lite tunnel",
    1=1, null())
| where isnotnull(severity)
| sort -events
```

## Visualization

(1) Gauge: AFTR session table utilization. (2) Table: tunnel events. (3) Single-value: port exhaustion events. (4) Timechart: AFTR load.

## Known False Positives

**Subscriber churn.** High volumes of tunnel up/down during peak hours as customers connect/disconnect is normal for ISP environments.

**Planned maintenance.** AFTR failover during maintenance causes brief session table migrations.

## References

- [RFC 6333 — Dual-Stack Lite Broadband Deployments Following IPv4 Exhaustion](https://www.rfc-editor.org/rfc/rfc6333)
- [RFC 6908 — Deployment Considerations for Dual-Stack Lite](https://www.rfc-editor.org/rfc/rfc6908)
