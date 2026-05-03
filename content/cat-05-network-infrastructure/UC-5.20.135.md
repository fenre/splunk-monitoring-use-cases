<!-- AUTO-GENERATED from UC-5.20.135.json — DO NOT EDIT -->

---
id: "5.20.135"
title: "IPv6 Duplicate Address Detection (DAD) DoS Attack Detection"
status: "verified"
criticality: "high"
splunkPillar: "ES"
---

# UC-5.20.135 · IPv6 Duplicate Address Detection (DAD) DoS Attack Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** ES &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*Before a device can use its new IPv6 address, it checks if anyone else already has the same address. An attacker can pretend to have EVERY address, so no new device can ever get an address — like someone at a hotel reception saying 'that room is taken' for every room, leaving all guests locked out. We watch for this trick and catch the impostor.*

---

## Description

Detects DAD (Duplicate Address Detection) denial-of-service attacks where an attacker responds to every DAD probe, preventing hosts from configuring IPv6 addresses. Multiple DAD failures across different addresses on the same segment indicates an active DAD DoS attack rather than genuine address conflicts.

## Value

A DAD DoS attack is trivially easy to execute (a single script on one host) and devastating in impact — every host on the segment is denied IPv6 service. Because DAD failures are often logged as informational events, they're easily missed without dedicated monitoring. Detecting the pattern of multiple DAD failures across different addresses quickly identifies the attack.

## Implementation

Monitor DAD failure events. Alert when multiple unique addresses fail DAD on the same segment (pattern of attack vs genuine duplicate).

## Detailed Implementation

### Prerequisites
- Switch/router NDP logging enabled.
- Zeek sensor for passive NDP monitoring.

### Step 1 — Enable DAD event logging.

### Step 2 — Create monitoring searches for DAD failure patterns.

### Step 3 — Validate: Simulate DAD DoS with `ndsend` tool. Verify detection fires.

### Step 4 — Operationalize
**Dashboard:** DAD health. **Alert:** >5 unique addresses failing DAD on same segment — critical.

### Step 5 — Troubleshooting
- Identify attacker: The NA response to DAD probes contains the attacker's source MAC. Use switch port security to identify and isolate.
- Mitigation: Enable SISF (Switch Integrated Security Features) with DAD Guard.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe" OR sourcetype="zeek:conn") earliest=-24h
  ("DAD" AND ("fail" OR "duplicate" OR "conflict" OR "defend"))
| rex field=_raw "(?:address|target)\s*(?<dad_address>[0-9a-fA-F:]+)"
| rex field=_raw "(?:src|source|from)\s*(?<responder>[0-9a-fA-F:]+)"
| stats count as dad_failures dc(dad_address) as unique_addresses by host
| eval severity=case(
    unique_addresses > 10 AND dad_failures > 20, "CRITICAL — DAD DoS attack: " . unique_addresses . " unique addresses failed DAD (" . dad_failures . " failures)",
    unique_addresses > 5, "HIGH — multiple DAD failures — possible targeted attack",
    dad_failures > 5, "MEDIUM — repeated DAD failures for same address — investigate",
    1=1, null())
| where isnotnull(severity)
| sort -dad_failures
```

## Visualization

(1) Single-value: DAD failures (red if >5). (2) Table: failed addresses. (3) Timechart: DAD failure rate. (4) Correlation: responder address (attacker).

## Known False Positives

**Genuine duplicates.** Legitimate address conflicts occur when two devices are statically assigned the same address. Single DAD failures are usually genuine; multiple failures across many addresses indicate an attack.

**VM cloning.** Cloned VMs with identical configurations may trigger DAD failures. This is a configuration issue, not an attack.

## References

- [RFC 3756 — IPv6 Neighbor Discovery (ND) Trust Models and Threats (§4.1.3 — DAD DoS)](https://www.rfc-editor.org/rfc/rfc3756#section-4.1.3)
- [RFC 4862 — IPv6 Stateless Address Autoconfiguration (§5.4 — DAD)](https://www.rfc-editor.org/rfc/rfc4862#section-5.4)
