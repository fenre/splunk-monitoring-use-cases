<!-- AUTO-GENERATED from UC-5.20.125.json — DO NOT EDIT -->

---
id: "5.20.125"
title: "IPv6 SEND (Secure Neighbor Discovery) Deployment Status Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.125 · IPv6 SEND (Secure Neighbor Discovery) Deployment Status Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Expert &middot; **Pillar:** Platform &middot; **Type:** Security, Compliance &middot; **Wave:** Run &middot; **Status:** Verified

*SEND is like putting a wax seal on important network messages so the recipient can verify they really came from the right sender. Most networks use simpler methods (like checking an ID badge at the door instead), but SEND is the gold standard for proving a message is genuine.*

---

## Description

Monitors Secure Neighbor Discovery (SEND, RFC 3971) deployment and Cryptographically Generated Addresses (CGA, RFC 3972) usage. SEND cryptographically signs NDP messages, providing definitive protection against RA spoofing and NDP poisoning. Tracks deployment status, verification failures, and CGA usage.

## Value

SEND is the strongest NDP security mechanism — it provides cryptographic proof that NDP messages are authentic. While RA Guard and DHCP Guard provide practical first-hop security, SEND is the only mechanism that works in all topologies (including where L2 security features aren't available). Monitoring SEND deployment and verification failures ensures the cryptographic NDP protection layer is functioning.

## Implementation

Monitor SEND configuration status and verification events. Track CGA usage. Alert on verification failures.

## Detailed Implementation

### Prerequisites
- SEND-capable routers and switches.
- RSA key pairs for SEND signing.

### Step 1 — SEND is complex to deploy and rarely used in practice. RA Guard (UC-5.20.28) provides equivalent protection at L2. Monitor SEND status where deployed.

### Step 2 — Create monitoring searches
```spl
index=network "SEND" earliest=-7d | stats count by host, send_event
```

### Step 3 — Validate SEND verification on a test device.

### Step 4 — Operationalize
**Dashboard:** SEND status. **Alert:** SEND verification failure — high.

### Step 5 — Troubleshooting
- SEND verification failures: Check RSA key validity and CGA parameters.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-7d
  ("SEND" OR "CGA" OR "RSA.*signature" OR "certification.*path")
| eval send_event=case(
    match(_raw, "(?i)SEND.*verify.*fail|CGA.*invalid|signature.*fail"), "SEND_VERIFICATION_FAILURE",
    match(_raw, "(?i)SEND.*enabled|CGA.*configured"), "SEND_CONFIGURED",
    match(_raw, "(?i)SEND.*disabled|no.*SEND"), "SEND_NOT_CONFIGURED",
    1=1, "OTHER")
| stats count as events by host, send_event
| eval status=case(
    send_event="SEND_VERIFICATION_FAILURE", "HIGH — SEND signature verification failed — possible NDP attack",
    send_event="SEND_NOT_CONFIGURED", "INFO — SEND not configured (RA Guard recommended as alternative)",
    send_event="SEND_CONFIGURED", "OK — SEND enabled and operational",
    1=1, null())
| where isnotnull(status)
| sort -events
```

## Visualization

(1) Table: SEND deployment status by device. (2) Single-value: SEND verification failures. (3) Pie chart: SEND-enabled vs not-enabled.

## Known False Positives

**SEND not widely deployed.** Most networks use RA Guard instead of SEND. The absence of SEND is informational, not a vulnerability, when RA Guard is deployed.

**CGA computation overhead.** CGA generation requires RSA key pair generation, which can take several seconds on low-powered devices.

## References

- [RFC 3971 — SEcure Neighbor Discovery (SEND)](https://www.rfc-editor.org/rfc/rfc3971)
- [RFC 3972 — Cryptographically Generated Addresses (CGA)](https://www.rfc-editor.org/rfc/rfc3972)
