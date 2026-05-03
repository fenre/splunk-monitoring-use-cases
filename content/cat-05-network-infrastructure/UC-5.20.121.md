<!-- AUTO-GENERATED from UC-5.20.121.json — DO NOT EDIT -->

---
id: "5.20.121"
title: "IPv6 MAP-T / MAP-E Transition Mechanism Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.121 · IPv6 MAP-T / MAP-E Transition Mechanism Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*MAP is a clever system where many households share a single old-format address (IPv4) by each using different 'apartment numbers' (ports). If the system breaks, all those households lose access to old-format websites. We monitor it to make sure the sharing works correctly.*

---

## Description

Monitors MAP-T (RFC 7599) and MAP-E (RFC 7597) stateless IPv4/IPv6 transition mechanisms for translation/encapsulation failures, drops, and configuration issues. MAP-T/MAP-E are deployed by ISPs as scalable alternatives to stateful NAT64 and DS-Lite.

## Value

MAP-T and MAP-E enable ISPs to serve IPv4 traffic over IPv6-only infrastructure without per-session state. When MAP fails, customers lose IPv4 internet access. Because the mapping is algorithmic (stateless), failures typically affect entire customer ranges rather than individual sessions, making rapid detection critical.

## Implementation

Monitor MAP-T/MAP-E border relay (BR) and customer edge (CE) events. Track translation failures, drops, and configuration changes.

## Detailed Implementation

### Prerequisites
- MAP-T or MAP-E deployed on border relay and customer edge routers.
- MAP event logging enabled.

### Step 1 — Configure MAP monitoring
Enable logging on the MAP border relay. Monitor for translation failures and drops.

### Step 2 — Create monitoring searches
```spl
index=network "MAP" earliest=-24h
| stats count by host, map_event
```

### Step 3 — Validate
Verify IPv4 connectivity through MAP from a test CE. Generate traffic to an IPv4-only destination.

### Step 4 — Operationalize
**Dashboard:** MAP health. **Alert:** MAP failures >10/hour — high.

### Step 5 — Troubleshooting
- MAP rule mismatch: Verify MAP rule parameters (prefix, suffix length, PSID) match between BR and CE.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  ("%MAP" OR "map-t" OR "map-e" OR "mapping.*address.*port")
| eval map_event=case(
    match(_raw, "(?i)MAP.*error|MAP.*fail|translation.*fail"), "MAP_FAILURE",
    match(_raw, "(?i)MAP.*drop|out.?of.?range"), "MAP_DROP",
    match(_raw, "(?i)MAP.*config|rule.*update"), "MAP_CONFIG",
    1=1, "MAP_OTHER")
| stats count as events by host, map_event
| eval severity=case(
    map_event="MAP_FAILURE", "HIGH — MAP translation/encapsulation failures on " . host,
    map_event="MAP_DROP" AND events > 100, "MEDIUM — significant MAP drops (" . events . ")",
    1=1, null())
| where isnotnull(severity)
| sort -events
```

## Visualization

(1) Table: MAP events by device. (2) Single-value: MAP failures. (3) Timechart: MAP drop rate.

## Known False Positives

**Out-of-range addresses.** Traffic from IPv4 addresses not in the MAP rule set is expected to be dropped. This is not a MAP failure.

**CE reboots.** During CE router reboots, MAP service is briefly unavailable. This is expected.

## References

- [RFC 7597 — Mapping of Address and Port with Encapsulation (MAP-E)](https://www.rfc-editor.org/rfc/rfc7597)
- [RFC 7599 — Mapping of Address and Port using Translation (MAP-T)](https://www.rfc-editor.org/rfc/rfc7599)
